from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Ingredient, Recipe, RecipeIngredient
from app.schemas.matching import (
    MatchIngredient,
    MatchRecipe,
    MatchRequest,
    MatchResponse,
    MatchResultItem,
)
from app.services.canonicalizer import resolve_ingredient_id


def match_recipes(db: Session, payload: MatchRequest) -> MatchResponse:
    # Resolve text ingredient names to canonical ids.
    unresolved: list[str] = []
    user_ids: list[int] = list(payload.ingredient_ids)
    seen_ids: set[int] = set(user_ids)

    for name in payload.ingredient_names:
        ing_id, _ = resolve_ingredient_id(db, name)
        if ing_id is None:
            unresolved.append(name)
        elif ing_id not in seen_ids:
            seen_ids.add(ing_id)
            user_ids.append(ing_id)

    page = max(payload.page, 1)
    limit = min(max(payload.page_size, 1), 100)
    offset = (page - 1) * limit

    if not user_ids:
        return MatchResponse(
            items=[], total=0, page=page, page_size=limit,
            has_more=False, unresolved_names=unresolved,
        )

    # Count all distinct candidate recipes that contain at least one user ingredient.
    total = (
        db.scalar(
            select(func.count(func.distinct(RecipeIngredient.recipe_id))).where(
                RecipeIngredient.ingredient_id.in_(user_ids)
            )
        )
        or 0
    )

    candidates = (
        select(RecipeIngredient.recipe_id)
        .where(RecipeIngredient.ingredient_id.in_(user_ids))
        .distinct()
        .subquery()
    )
    matched_in = RecipeIngredient.ingredient_id.in_(user_ids)
    # Aggregate over ALL rows of candidate recipes, not just the matched ones.
    # Filtering by recipe (via IN subquery) preserves every ingredient of the recipe.
    stats = (
        select(
            RecipeIngredient.recipe_id,
            func.count().filter(matched_in).label("matched_cnt"),
            func.count().label("total_cnt"),
        )
        .where(RecipeIngredient.recipe_id.in_(select(candidates.c.recipe_id)))
        .group_by(RecipeIngredient.recipe_id)
        .subquery()
    )

    query = (
        select(
            Recipe.id,
            Recipe.title,
            Recipe.cover_url,
            Recipe.description,
            Recipe.likes_count,
            stats.c.matched_cnt,
            stats.c.total_cnt,
        )
        .join(stats, stats.c.recipe_id == Recipe.id)
        .where(Recipe.is_published.is_(True))
    )
    rows = db.execute(query).all()

    # Sort by coverage DESC, then fewest required ingredients, then likes, then id.
    rows.sort(
        key=lambda r: (
            -(float(r.matched_cnt) / float(r.total_cnt)) if r.total_cnt else 0,
            r.total_cnt,
            -r.likes_count,
            -r.id,
        )
    )
    page_rows = rows[offset : offset + limit]

    # Build per-recipe matched/missing ingredient detail for the paginated slice.
    recipe_ids = [r.id for r in page_rows]
    details: dict[int, tuple[list[MatchIngredient], list[MatchIngredient]]] = {}
    user_id_set = set(user_ids)
    if recipe_ids:
        ri_rows = db.execute(
            select(
                RecipeIngredient.recipe_id,
                RecipeIngredient.ingredient_id,
                Ingredient.name,
                RecipeIngredient.raw_text,
                RecipeIngredient.quantity,
                RecipeIngredient.unit,
            )
            .join(Ingredient, Ingredient.id == RecipeIngredient.ingredient_id)
            .where(RecipeIngredient.recipe_id.in_(recipe_ids))
        ).all()
        for rid, ing_id, name, raw, qty, unit in ri_rows:
            matched, missing = details.setdefault(rid, ([], []))
            entry = MatchIngredient(
                name=name,
                raw_text=raw,
                quantity=float(qty) if qty is not None else None,
                unit=unit,
            )
            if ing_id in user_id_set:
                matched.append(entry)
            else:
                entry.label = "需购买"
                missing.append(entry)

    items: list[MatchResultItem] = []
    for r in page_rows:
        matched_names, missing_names = details.get(r.id, ([], []))
        coverage = float(r.matched_cnt) / float(r.total_cnt) if r.total_cnt else 0.0
        items.append(
            MatchResultItem(
                recipe=MatchRecipe(
                    id=r.id,
                    title=r.title,
                    cover_url=r.cover_url,
                    description=r.description,
                ),
                coverage=round(coverage, 4),
                is_complete=coverage >= 1.0,
                matched_ingredients=matched_names,
                missing_ingredients=missing_names,
            )
        )

    return MatchResponse(
        items=items,
        total=total,
        page=page,
        page_size=limit,
        has_more=offset + limit < total,
        unresolved_names=unresolved,
    )
