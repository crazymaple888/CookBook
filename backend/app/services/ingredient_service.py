from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Ingredient, IngredientCategory, IngredientSynonym, RecipeIngredient
from app.schemas.common import Page
from app.schemas.ingredient import IngredientCategoryOut, IngredientOut
from app.utils.pagination import paginate

# 点选面板只展示高频食材，避免被导入噪音淹没。
# 基于食材在菜谱食材表中的出现次数排序。
TOP_INGREDIENTS_LIMIT = 300


def search_ingredients(db: Session, q: str, page: int = 1, page_size: int = 20) -> Page[IngredientOut]:
    """Search ingredients, ranked by how often they appear across recipes.

    The corpus produces many noisy rows ('#土豆泥', '100克糖'); ranking by
    usage frequency surfaces real, commonly-used ingredients first.
    """
    if not q.strip():
        return Page[IngredientOut](items=[], total=0, page=page, page_size=page_size, has_more=False)

    like = f"%{q}%"
    usage = (
        select(RecipeIngredient.ingredient_id, func.count(RecipeIngredient.recipe_id).label("cnt"))
        .group_by(RecipeIngredient.ingredient_id)
        .subquery()
    )
    query = (
        select(Ingredient)
        .outerjoin(usage, usage.c.ingredient_id == Ingredient.id)
        .where(
            or_(
                Ingredient.name.ilike(like),
                Ingredient.id.in_(
                    select(IngredientSynonym.ingredient_id).where(
                        IngredientSynonym.synonym.ilike(like)
                    )
                ),
            )
        )
        .order_by(
            # Highest usage first; never-used noise sinks to the bottom.
            func.coalesce(usage.c.cnt, 0).desc(),
            Ingredient.name,
        )
    )
    page_obj = paginate(db, query, page, page_size)
    return Page[IngredientOut](
        items=[IngredientOut.model_validate(r[0]) for r in page_obj.items],
        total=page_obj.total,
        page=page_obj.page,
        page_size=page_obj.page_size,
        has_more=page_obj.has_more,
    )


def category_tree(db: Session) -> list[IngredientCategoryOut]:
    """Return ingredient categories, filtered to frequently-used ingredients.

    The corpus import produces tens of thousands of noisy ingredient rows
    (long descriptions, stray quantities, section headers). For the picker we
    only surface ingredients that actually appear across many recipes.
    """
    # Count how many recipes reference each ingredient; keep the top N.
    usage = (
        select(RecipeIngredient.ingredient_id, func.count(RecipeIngredient.recipe_id))
        .group_by(RecipeIngredient.ingredient_id)
        .order_by(func.count(RecipeIngredient.recipe_id).desc())
        .limit(TOP_INGREDIENTS_LIMIT)
    )
    top_ids = {row[0] for row in db.execute(usage).all()}

    categories = db.scalars(
        select(IngredientCategory).order_by(IngredientCategory.sort_order, IngredientCategory.id)
    ).all()
    ingredients = db.scalars(
        select(Ingredient).where(Ingredient.id.in_(top_ids)).order_by(Ingredient.name)
    ).all()
    by_cat: dict[int | None, list[Ingredient]] = {}
    for ing in ingredients:
        by_cat.setdefault(ing.category_id, []).append(ing)

    result = []
    for cat in categories:
        ing_list = by_cat.get(cat.id, [])
        if not ing_list:
            continue
        result.append(
            IngredientCategoryOut(
                id=cat.id,
                name=cat.name,
                sort_order=cat.sort_order,
                ingredients=[IngredientOut.model_validate(i) for i in ing_list],
            )
        )
    uncategorized = by_cat.get(None, [])
    if uncategorized:
        result.append(
            IngredientCategoryOut(
                id=0,
                name="其他",
                sort_order=999,
                ingredients=[IngredientOut.model_validate(i) for i in uncategorized],
            )
        )
    return result
