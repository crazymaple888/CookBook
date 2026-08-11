from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Ingredient, IngredientSynonym
from app.utils.text import normalize_name, strip_unit_suffix


def resolve_ingredient_id(db: Session, raw_name: str) -> tuple[int | None, str | None]:
    """Map a user/import ingredient text to a canonical ingredient id.

    Returns (ingredient_id, canonical_name). ingredient_id is None when the
    ingredient is not recognized.
    """
    cleaned, _ = strip_unit_suffix(raw_name)
    name = normalize_name(cleaned)
    if not name:
        return None, None

    # Exact synonym match first.
    syn = db.scalar(
        select(IngredientSynonym).where(IngredientSynonym.synonym == name)
    )
    if syn is not None:
        ing = db.get(Ingredient, syn.ingredient_id)
        if ing is not None:
            return ing.id, ing.name

    # Canonical name fallback.
    ing = db.scalar(select(Ingredient).where(Ingredient.name == name))
    if ing is not None:
        return ing.id, ing.name

    return None, cleaned


def resolve_many(db: Session, names: list[str]) -> dict[str, tuple[int | None, str | None]]:
    """Bulk-resolve many names in a single query for import efficiency."""
    result: dict[str, tuple[int | None, str | None]] = {}
    cleaned_map: dict[str, str] = {}
    pending: set[str] = set()

    for raw in names:
        cleaned, _ = strip_unit_suffix(raw)
        name = normalize_name(cleaned)
        if not name:
            result[raw] = (None, None)
            continue
        cleaned_map[raw] = name
        pending.add(name)

    if pending:
        syns = db.scalars(
            select(IngredientSynonym).where(IngredientSynonym.synonym.in_(pending))
        ).all()
        syn_by_name = {s.synonym: s.ingredient_id for s in syns}
        resolved_ids = set(syn_by_name.values())
        ings_by_id = {
            ing.id: ing
            for ing in db.scalars(select(Ingredient).where(Ingredient.id.in_(resolved_ids))).all()
        } if resolved_ids else {}

        canonical_ings = {
            ing.name: ing
            for ing in db.scalars(select(Ingredient).where(Ingredient.name.in_(pending))).all()
        }

        for raw, name in cleaned_map.items():
            ing_id = syn_by_name.get(name)
            if ing_id is not None and ing_id in ings_by_id:
                result[raw] = (ing_id, ings_by_id[ing_id].name)
                continue
            ing = canonical_ings.get(name)
            if ing is not None:
                result[raw] = (ing.id, ing.name)
                continue
            result[raw] = (None, name)

    return result
