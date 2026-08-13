import hashlib
import json
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models import Ingredient, Recipe, RecipeIngredient
from app.services.canonicalizer import resolve_many


@dataclass
class ImportStats:
    added: int = 0
    updated: int = 0
    skipped: int = 0
    created_ingredients: int = 0
    failed: int = 0


@dataclass
class RecipeDraft:
    title: str
    source_id: str
    description: str | None = None
    steps: list[dict] = field(default_factory=list)
    ingredients: list[dict] = field(default_factory=list)  # {name, quantity, unit, raw_text}
    source: str = "chinese-recipes-corpus"


def content_hash(record: RecipeDraft) -> str:
    canonical = {
        "title": record.title,
        "description": record.description,
        "steps": record.steps,
        "ingredients": [
            {k: ing.get(k) for k in ("name", "quantity", "unit")}
            for ing in sorted(record.ingredients, key=lambda i: i.get("name") or "")
        ],
    }
    return hashlib.sha256(
        json.dumps(canonical, ensure_ascii=False).encode()
    ).hexdigest()


# incremental name->id cache (lightweight, avoids loading full ingredients table)
_INGREDIENT_CACHE: dict[str, int] = {}


def import_records(db: Session, records: list[RecipeDraft], source: str) -> ImportStats:
    stats = ImportStats()

    # Gather all ingredient raw names once for bulk resolution.
    all_names = []
    for rec in records:
        all_names.extend(ing.get("raw_text") or ing.get("name") or "" for ing in rec.ingredients)
    resolved = resolve_many(db, all_names)

    # Map canonical names -> existing ingredients to avoid repeated lookups.
    existing = _INGREDIENT_CACHE  # name -> id, built incrementally

    for rec in records:
        if not rec.title:
            stats.skipped += 1
            continue
        # Use a savepoint per recipe so one bad record cannot roll back the
        # whole batch (a full rollback would invalidate earlier flushes).
        try:
            with db.begin_nested():
                _upsert_recipe(db, rec, source, resolved, existing, stats)
        except Exception:
            stats.failed += 1
            continue
    db.commit()
    return stats


def _upsert_recipe(
    db: Session,
    rec: RecipeDraft,
    source: str,
    resolved: dict[str, tuple[int | None, str | None]],
    existing: dict[str, Ingredient],
    stats: ImportStats,
) -> None:
    new_hash = content_hash(rec)
    recipe = db.scalar(
        select(Recipe).where(Recipe.source == source, Recipe.source_id == rec.source_id)
    )
    if recipe is not None and recipe.content_hash == new_hash:
        stats.skipped += 1
        return

    # Resolve ingredient ids, de-duplicating by canonical name so a recipe never
    # lists the same ingredient twice (violates uq_recipe_ingredients).
    seen_names: set[str] = set()
    ingredient_ids: list[int] = []
    for ing in rec.ingredients:
        raw = ing.get("raw_text") or ing.get("name") or ""
        ing_id, canonical_name = resolved.get(raw, (None, None))
        name = (canonical_name or ing.get("name") or "").strip()
        if not name:
            continue
        if name in seen_names:
            continue
        seen_names.add(name)
        if ing_id is None:
            ing_id = _get_or_create_ingredient(db, name, existing, stats)
        ingredient_ids.append(ing_id)

    if recipe is None:
        recipe = Recipe(
            title=rec.title,
            description=rec.description,
            steps=rec.steps,
            source=source,
            source_id=rec.source_id,
            content_hash=new_hash,
        )
        db.add(recipe)
        db.flush()
        stats.added += 1
    else:
        recipe.title = rec.title
        recipe.description = rec.description
        recipe.steps = rec.steps
        recipe.content_hash = new_hash
        stats.updated += 1

    # Rebuild recipe_ingredients (delete + insert in same transaction).
    db.execute(
        RecipeIngredient.__table__.delete().where(RecipeIngredient.recipe_id == recipe.id)
    )
    for i, ing in enumerate(rec.ingredients):
        if i >= len(ingredient_ids):
            break
        db.add(
            RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ingredient_ids[i],
                raw_text=ing.get("raw_text") or ing.get("name"),
                quantity=ing.get("quantity"),
                unit=ing.get("unit"),
            )
        )


def _get_or_create_ingredient(
    db: Session, name: str, existing: dict[str, Ingredient], stats: ImportStats
) -> int:
    """Return the id for an ingredient name, creating it idempotently.

    Uses INSERT ... ON CONFLICT DO NOTHING so a savepoint rollback elsewhere
    never leaves a phantom id (the ingredient is committed with the batch).
    """
    ing_id = existing.get(name)
    if ing_id is not None:
        return ing_id

    stmt = (
        pg_insert(Ingredient)
        .values(name=name)
        .on_conflict_do_nothing(index_elements=[Ingredient.name])
        .returning(Ingredient.id)
    )
    ing_id = db.execute(stmt).scalar()
    if ing_id is None:
        ing_id = db.scalar(select(Ingredient.id).where(Ingredient.name == name))
    else:
        stats.created_ingredients += 1
    existing[name] = ing_id
    return ing_id
