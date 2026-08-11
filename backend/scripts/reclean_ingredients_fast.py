"""Re-clean existing recipe ingredients with the improved cleaner.

Optimized batch version: loads all ingredients into an in-memory dict once,
parses each raw ingredient line with the improved cleaner, and writes changes
back in bulk instead of one query per row.

Usage:
    DATABASE_URL=... python -m scripts.reclean_ingredients_fast
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Ingredient, IngredientSynonym, RecipeIngredient
from app.services.importer.cleaner import parse_ingredient_line

BATCH_SIZE = 5000


def main() -> None:
    import os

    from sqlalchemy import create_engine, text

    engine = create_engine(os.environ["DATABASE_URL"])
    db = Session(engine)
    start = time.time()

    # Load full ingredient catalog into memory once.
    ing_rows = db.execute(select(Ingredient.id, Ingredient.name)).all()
    id_by_name = {name: ing_id for ing_id, name in ing_rows}
    syn_rows = db.execute(select(IngredientSynonym.synonym, IngredientSynonym.ingredient_id)).all()
    id_by_synonym = {syn: ing_id for syn, ing_id in syn_rows}
    print(f"加载食材库 {len(id_by_name)} 条, 同义词 {len(id_by_synonym)} 条")

    last_id = 0
    total_rows = 0
    updated_rows = 0
    deleted_rows = 0
    # recipe -> set of ingredient_ids already assigned, persisted ACROSS batches
    # so de-dup works even when a recipe's rows span multiple batches.
    recipe_seen: dict[int, set[int]] = {}

    # Bulk UPDATE via executemany-style raw SQL.
    def flush_updates(updates: list[tuple]) -> None:
        nonlocal updated_rows
        if not updates:
            return
        try:
            db.execute(
                text(
                    "UPDATE recipe_ingredients SET ingredient_id = :iid, "
                    "quantity = :qty, unit = :unit WHERE id = :id"
                ),
                [
                    {"iid": iid, "qty": qty, "unit": unit, "id": rid}
                    for rid, iid, qty, unit in updates
                ],
            )
            db.commit()
            updated_rows += len(updates)
        except Exception:
            # A (recipe, ingredient) duplicate slipped through (cross-batch edge
            # case). Roll back and apply row-by-row, dropping conflicts.
            db.rollback()
            for rid, iid, qty, unit in updates:
                try:
                    with db.begin_nested():
                        db.execute(
                            text(
                                "UPDATE recipe_ingredients SET ingredient_id = :iid, "
                                "quantity = :qty, unit = :unit WHERE id = :id"
                            ),
                            {"iid": iid, "qty": qty, "unit": unit, "id": rid},
                        )
                    updated_rows += 1
                except Exception:
                    db.rollback()
                    db.execute(text("DELETE FROM recipe_ingredients WHERE id = :id"), {"id": rid})
            db.commit()

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

        updates: list[tuple] = []
        delete_ids: list[int] = []
        new_ingredients: dict[str, int] = {}

        for ri in rows:
            raw = ri.raw_text or ""
            parsed = parse_ingredient_line(raw)
            if not parsed or not parsed[0]["name"]:
                delete_ids.append(ri.id)
                continue
            clean_name = parsed[0]["name"]
            ing_id = id_by_synonym.get(clean_name) or id_by_name.get(clean_name)
            if ing_id is None:
                # Create new ingredient rows; flush immediately to get the id.
                if clean_name in new_ingredients:
                    ing_id = new_ingredients[clean_name]
                else:
                    new_ing = Ingredient(name=clean_name)
                    db.add(new_ing)
                    db.flush()
                    ing_id = new_ing.id
                    new_ingredients[clean_name] = ing_id
                    id_by_name[clean_name] = ing_id
            # De-dup within a recipe (persisted across batches).
            seen = recipe_seen.setdefault(ri.recipe_id, set())
            if ing_id in seen:
                delete_ids.append(ri.id)
                continue
            seen.add(ing_id)
            updates.append((ri.id, ing_id, parsed[0].get("quantity"), parsed[0].get("unit")))

        if delete_ids:
            db.execute(
                text("DELETE FROM recipe_ingredients WHERE id = ANY(:ids)"),
                {"ids": delete_ids},
            )
            deleted_rows += len(delete_ids)
        flush_updates(updates)

        if total_rows % 100000 == 0:
            elapsed = time.time() - start
            print(f"[{total_rows}] {elapsed:.0f}s | 更新{updated_rows} 删除{deleted_rows}")

    elapsed = time.time() - start
    print(f"完成: 处理 {total_rows} 条关联, 更新 {updated_rows}, 删除噪音 {deleted_rows}, 耗时 {elapsed/60:.1f} 分钟")
    db.close()


if __name__ == "__main__":
    main()
