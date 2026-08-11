"""Rebuild recipe_ingredients with cleaned ingredient names.

Strategy: instead of row-by-row UPDATE (which keeps hitting the
(recipe_id, ingredient_id) unique constraint and aborting the batch), we:
  1. Stream all (recipe_id, raw_text) pairs, clean each name in Python (fast).
  2. Create any missing ingredients in bulk.
  3. Build the new association set in memory (dedup by recipe+ingredient).
  4. Write into a staging table, then swap atomically.

Usage:
    DATABASE_URL=... python -m scripts.rebuild_ingredients
"""

import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Ingredient, IngredientSynonym, RecipeIngredient
from app.services.importer.cleaner import parse_ingredient_line

FETCH_SIZE = 20000


def main() -> None:
    import os

    from sqlalchemy import create_engine, text

    engine = create_engine(os.environ["DATABASE_URL"])
    db = Session(engine)
    start = time.time()

    # ---- Load ingredient catalog into memory ----
    ing_rows = db.execute(select(Ingredient.id, Ingredient.name)).all()
    id_by_name = {name: ing_id for ing_id, name in ing_rows}
    syn_rows = db.execute(select(IngredientSynonym.synonym, IngredientSynonym.ingredient_id)).all()
    id_by_syn = {syn: ing_id for syn, ing_id in syn_rows}
    print(f"食材库 {len(id_by_name)} 条, 同义词 {len(id_by_syn)} 条", flush=True)

    # ---- Phase 1: stream rows, clean names in Python ----
    # new_rows: list of (recipe_id, ingredient_name, raw_text, quantity, unit)
    new_rows = []
    name_set: set[str] = set()
    recipe_ing_names: dict[int, set[str]] = defaultdict(set)  # for dedup
    last_id = 0
    total = 0

    # Stream with id so the cursor advances correctly.
    while True:
        rows = db.execute(
            select(
                RecipeIngredient.id,
                RecipeIngredient.recipe_id,
                RecipeIngredient.raw_text,
                RecipeIngredient.quantity,
                RecipeIngredient.unit,
            )
            .where(RecipeIngredient.id > last_id)
            .order_by(RecipeIngredient.id)
            .limit(FETCH_SIZE)
        ).all()
        if not rows:
            break
        last_id = rows[-1]._mapping["id"]
        total += len(rows)

        for r in rows:
            rid = r._mapping["recipe_id"]
            raw = r._mapping["raw_text"] or ""
            qty = r._mapping["quantity"]
            unit = r._mapping["unit"]
            parsed = parse_ingredient_line(raw)
            if not parsed or not parsed[0]["name"]:
                continue  # pure noise -> drop
            name = parsed[0]["name"]
            # Dedup per recipe in memory.
            if name in recipe_ing_names[rid]:
                continue
            recipe_ing_names[rid].add(name)
            new_rows.append((rid, name, raw, qty, unit))
            name_set.add(name)

        if total % 200000 == 0:
            print(f"[阶段1] 读取 {total} 行, 有效 {len(new_rows)} 行, 耗时 {time.time()-start:.0f}s", flush=True)

    print(f"[阶段1] 完成: 读取 {total} 行 -> 有效 {len(new_rows)} 行, {len(name_set)} 个不同食材名, 耗时 {time.time()-start:.0f}s", flush=True)

    # ---- Phase 2: create missing ingredients in bulk ----
    missing = [n for n in name_set if n not in id_by_name]
    if missing:
        # Batch insert with conflict-ignore.
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        for i in range(0, len(missing), 1000):
            chunk = missing[i : i + 1000]
            stmt = (
                pg_insert(Ingredient)
                .values([{"name": n} for n in chunk])
                .on_conflict_do_nothing(index_elements=[Ingredient.name])
            )
            db.execute(stmt)
        db.commit()
        # Re-query fresh ids for the created ingredients, in chunks to stay
        # under PostgreSQL's 65535 bound-parameter limit.
        for i in range(0, len(missing), 1000):
            chunk = missing[i : i + 1000]
            fresh = db.execute(
                select(Ingredient.id, Ingredient.name).where(Ingredient.name.in_(chunk))
            ).all()
            id_by_name.update({name: ing_id for ing_id, name in fresh})
    print(f"[阶段2] 新食材 {len(missing)} 个, 耗时 {time.time()-start:.0f}s", flush=True)

    # ---- Phase 3: write staging table and swap ----
    print(f"[阶段3] 写入临时表...", flush=True)
    db.execute(text("DROP TABLE IF EXISTS recipe_ingredients_new"))
    db.execute(
        text(
            "CREATE TABLE recipe_ingredients_new ("
            "id BIGSERIAL PRIMARY KEY, "
            "recipe_id BIGINT NOT NULL REFERENCES recipes(id), "
            "ingredient_id BIGINT NOT NULL REFERENCES ingredients(id), "
            "raw_text VARCHAR(255), "
            "quantity NUMERIC(10,3), "
            "unit VARCHAR(32), "
            "is_main BOOLEAN NOT NULL DEFAULT true, "
            "UNIQUE (recipe_id, ingredient_id)"
            ")"
        )
    )

    # Bulk insert in chunks. ON CONFLICT DO NOTHING skips any (recipe, ingredient)
    # pair that slipped through in-memory de-dup (e.g. two names mapping to the
    # same ingredient via synonyms), instead of failing the whole batch.
    batch = []
    for rid, name, raw, qty, unit in new_rows:
        ing_id = id_by_syn.get(name) or id_by_name.get(name)
        if ing_id is None:
            continue
        batch.append((rid, ing_id, raw, qty, unit))
        if len(batch) >= 10000:
            db.execute(
                text(
                    "INSERT INTO recipe_ingredients_new (recipe_id, ingredient_id, raw_text, quantity, unit) "
                    "VALUES (:rid, :iid, :raw, :qty, :unit) "
                    "ON CONFLICT (recipe_id, ingredient_id) DO NOTHING"
                ),
                [{"rid": r, "iid": i, "raw": raw, "qty": q, "unit": u} for r, i, raw, q, u in batch],
            )
            batch = []
            db.commit()
    if batch:
        db.execute(
            text(
                "INSERT INTO recipe_ingredients_new (recipe_id, ingredient_id, raw_text, quantity, unit) "
                "VALUES (:rid, :iid, :raw, :qty, :unit) "
                "ON CONFLICT (recipe_id, ingredient_id) DO NOTHING"
            ),
            [{"rid": r, "iid": i, "raw": raw, "qty": q, "unit": u} for r, i, raw, q, u in batch],
        )
        db.commit()

    print(f"[阶段3] 临时表写入完成, 耗时 {time.time()-start:.0f}s, 开始原子替换", flush=True)

    # Atomic swap.
    db.execute(text("DROP TABLE IF EXISTS recipe_ingredients_old"))
    db.execute(text("ALTER TABLE recipe_ingredients RENAME TO recipe_ingredients_old"))
    db.execute(text("ALTER TABLE recipe_ingredients_new RENAME TO recipe_ingredients"))
    # Recreate indexes on the new table.
    db.execute(text("CREATE INDEX ix_recipe_ingredients_recipe_id ON recipe_ingredients(recipe_id)"))
    db.execute(text("CREATE INDEX ix_recipe_ingredients_ingredient_id ON recipe_ingredients(ingredient_id)"))
    db.commit()

    print(f"完成! 新表 {len(new_rows)} 行, 总耗时 {time.time()-start:.1f} 秒", flush=True)
    db.close()


if __name__ == "__main__":
    main()
