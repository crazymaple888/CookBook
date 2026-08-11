"""Re-clean existing recipe ingredients with the improved cleaner.

The full import ran with an older cleaner that left English-unit noise in
ingredient names ('200g猪肉馅' -> '200猪肉馅'). This script walks every
recipe, re-parses each raw ingredient line with the fixed cleaner, and
updates recipe_ingredients to point at clean canonical ingredients.

Usage:
    DATABASE_URL=... python -m scripts.reclean_ingredients
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Ingredient, RecipeIngredient
from app.services.canonicalizer import resolve_ingredient_id
from app.services.importer.cleaner import parse_ingredient_line

BATCH_SIZE = 1000


def main() -> None:
    import os

    from sqlalchemy import create_engine

    engine = create_engine(os.environ["DATABASE_URL"])
    db = Session(engine)
    start = time.time()

    total_rows = 0
    updated_rows = 0
    deleted_rows = 0
    # RECLEAN_TEST_LIMIT caps rows processed for a quick smoke test.
    test_limit = int(os.environ.get("RECLEAN_TEST_LIMIT", "0"))
    # Id-based cursor: unlike OFFSET pagination, deleting rows mid-loop does not
    # cause the query to skip or revisit rows, so every original row is seen
    # exactly once.
    last_id = 0

    while True:
        rows = db.scalars(
            select(RecipeIngredient)
            .where(RecipeIngredient.id > last_id)
            .order_by(RecipeIngredient.id)
            .limit(BATCH_SIZE)
        ).all()
        if not rows:
            break
        last_id = rows[-1].id
        total_rows += len(rows)

        # Group by recipe so de-duplication across a recipe's ingredients works.
        by_recipe: dict[int, list] = {}
        for ri in rows:
            by_recipe.setdefault(ri.recipe_id, []).append(ri)

        for recipe_ris in by_recipe.values():
            used_ingredient_ids: set[int] = set()
            for ri in recipe_ris:
                raw = ri.raw_text or ""
                parsed = parse_ingredient_line(raw)
                if not parsed or not parsed[0]["name"]:
                    db.delete(ri)
                    deleted_rows += 1
                    continue
                clean_name = parsed[0]["name"]
                ing_id, canonical = resolve_ingredient_id(db, clean_name)
                if ing_id is None:
                    # Idempotent create (name may already exist with a variant
                    # that resolve_ingredient_id didn't match).
                    from sqlalchemy.dialects.postgresql import insert as pg_insert

                    ins = (
                        pg_insert(Ingredient)
                        .values(name=clean_name)
                        .on_conflict_do_nothing(index_elements=[Ingredient.name])
                        .returning(Ingredient.id)
                    )
                    ing_id = db.execute(ins).scalar()
                    if ing_id is None:
                        ing_id = db.scalar(
                            select(Ingredient.id).where(Ingredient.name == clean_name)
                        )
                if ing_id is None:
                    db.delete(ri)
                    deleted_rows += 1
                    continue
                if ing_id in used_ingredient_ids:
                    # Same recipe would now list the same ingredient twice.
                    db.delete(ri)
                    deleted_rows += 1
                    continue
                used_ingredient_ids.add(ing_id)
                # Guard against cross-batch duplicates: if a recipe's rows span
                # batches, the same (recipe, ingredient) pair may already exist
                # from an earlier batch — drop the later duplicate.
                try:
                    with db.begin_nested():
                        ri.ingredient_id = ing_id
                        ri.raw_text = raw
                        ri.quantity = parsed[0].get("quantity")
                        ri.unit = parsed[0].get("unit")
                except Exception:
                    db.delete(ri)
                    deleted_rows += 1
                    continue
                updated_rows += 1

        db.commit()
        if total_rows % 500000 == 0:
            print(f"[{total_rows}] {time.time()-start:.0f}s")
        if test_limit and total_rows >= test_limit:
            print(f"测试模式: 已达 {test_limit} 行, 停止")
            break

    elapsed = time.time() - start
    print(f"完成: 处理 {total_rows} 条关联, 更新 {updated_rows}, 删除噪音 {deleted_rows}, 耗时 {elapsed/60:.1f} 分钟")
    db.close()


if __name__ == "__main__":
    main()
