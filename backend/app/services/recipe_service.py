from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    Comment,
    Favorite,
    Ingredient,
    Like,
    Recipe,
    RecipeCategory,
    RecipeIngredient,
)
from app.schemas.common import Page
from app.schemas.recipe import (
    RecipeCard,
    RecipeCreate,
    RecipeDetail,
    RecipeIngredientOut,
    RecipeUpdate,
)
from app.services.canonicalizer import resolve_ingredient_id
from app.utils.pagination import paginate

RECIPE_CARD_COLS = (
    Recipe.id,
    Recipe.title,
    Recipe.description,
    Recipe.cover_url,
    Recipe.category_id,
    Recipe.likes_count,
    Recipe.favorites_count,
    Recipe.comments_count,
)


def random_recipes(db: Session, count: int = 10, user_id: int | None = None) -> list[RecipeCard]:
    count = min(max(count, 1), 50)
    rows = db.execute(
        select(*RECIPE_CARD_COLS)
        .where(Recipe.is_published.is_(True))
        .order_by(func.random())
        .limit(count)
    ).all()
    return [_card_from_row(r) for r in rows]


def list_recipes(
    db: Session,
    query: str | None,
    category_id: int | None,
    sort: str,
    page: int,
    page_size: int,
    user_id: int | None = None,
) -> Page[RecipeCard]:
    stmt = select(*RECIPE_CARD_COLS).where(Recipe.is_published.is_(True))
    count_stmt = (
        select(Recipe.id).where(Recipe.is_published.is_(True))
    )
    if query:
        like = f"%{query}%"
        stmt = stmt.where(or_(Recipe.title.ilike(like), Recipe.description.ilike(like)))
        count_stmt = count_stmt.where(
            or_(Recipe.title.ilike(like), Recipe.description.ilike(like))
        )
    if category_id:
        stmt = stmt.where(Recipe.category_id == category_id)
        count_stmt = count_stmt.where(Recipe.category_id == category_id)

    if sort == "new":
        stmt = stmt.order_by(Recipe.created_at.desc(), Recipe.id.desc())
    elif sort == "hot":
        stmt = stmt.order_by(Recipe.likes_count.desc(), Recipe.created_at.desc())
    else:
        stmt = stmt.order_by(Recipe.created_at.desc(), Recipe.id.desc())

    page_obj = paginate(db, stmt, page, page_size, count_source=count_stmt)
    return Page[RecipeCard](
        items=[_card_from_row(r) for r in page_obj.items],
        total=page_obj.total,
        page=page_obj.page,
        page_size=page_obj.page_size,
        has_more=page_obj.has_more,
    )


def get_recipe_detail(
    db: Session, recipe_id: int, user_id: int | None = None
) -> RecipeDetail:
    recipe = db.get(Recipe, recipe_id)
    if recipe is None or not recipe.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    ing_rows = db.execute(
        select(
            RecipeIngredient.id,
            Ingredient.name,
            RecipeIngredient.raw_text,
            RecipeIngredient.quantity,
            RecipeIngredient.unit,
            RecipeIngredient.is_main,
        )
        .join(Ingredient, Ingredient.id == RecipeIngredient.ingredient_id)
        .where(RecipeIngredient.recipe_id == recipe_id)
        .order_by(RecipeIngredient.id)
    ).all()
    ingredients = [
        RecipeIngredientOut(
            id=r.id, name=r.name, raw_text=r.raw_text,
            quantity=float(r.quantity) if r.quantity is not None else None,
            unit=r.unit, is_main=r.is_main,
        )
        for r in ing_rows
    ]

    is_favorited = is_liked = False
    if user_id is not None:
        is_favorited = (
            db.scalar(
                select(Favorite.id).where(
                    Favorite.user_id == user_id, Favorite.recipe_id == recipe_id
                )
            )
            is not None
        )
        is_liked = (
            db.scalar(
                select(Like.id).where(
                    Like.user_id == user_id, Like.recipe_id == recipe_id
                )
            )
            is not None
        )

    return RecipeDetail(
        id=recipe.id,
        title=recipe.title,
        description=recipe.description,
        cover_url=recipe.cover_url,
        category_id=recipe.category_id,
        likes_count=recipe.likes_count,
        favorites_count=recipe.favorites_count,
        comments_count=recipe.comments_count,
        steps=recipe.steps,
        prep_time=recipe.prep_time,
        cook_time=recipe.cook_time,
        servings=recipe.servings,
        difficulty=recipe.difficulty,
        created_at=recipe.created_at,
        is_favorited=is_favorited,
        is_liked=is_liked,
        ingredients=ingredients,
    )


def list_categories(db: Session) -> list[RecipeCategory]:
    return list(
        db.scalars(
            select(RecipeCategory).order_by(RecipeCategory.sort_order, RecipeCategory.id)
        ).all()
    )


def create_recipe(db: Session, payload: RecipeCreate, user_id: int) -> Recipe:
    import hashlib
    import json

    recipe = Recipe(
        title=payload.title,
        description=payload.description,
        cover_url=payload.cover_url,
        category_id=payload.category_id,
        steps=payload.steps or [],
        prep_time=payload.prep_time,
        cook_time=payload.cook_time,
        servings=payload.servings,
        difficulty=payload.difficulty,
        source="user",
        source_id=f"user-{user_id}-{payload.title}",
        content_hash=hashlib.sha256(
            json.dumps(payload.model_dump(), ensure_ascii=False).encode()
        ).hexdigest(),
    )
    db.add(recipe)
    db.flush()
    _replace_ingredients(db, recipe.id, payload.ingredients)
    db.commit()
    db.refresh(recipe)
    return recipe


def update_recipe(
    db: Session, recipe_id: int, payload: RecipeUpdate, user_id: int
) -> Recipe:
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    if recipe.source == "user" and recipe.source_id.startswith(f"user-{user_id}"):
        pass
    else:
        # Only author (or admin) may edit; handled in router via author check.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    data = payload.model_dump(exclude_unset=True)
    ingredients_data = data.pop("ingredients", None)
    for key, value in data.items():
        setattr(recipe, key, value)
    if ingredients_data is not None:
        _replace_ingredients(db, recipe.id, ingredients_data)
    db.commit()
    db.refresh(recipe)
    return recipe


def delete_recipe(db: Session, recipe_id: int) -> None:
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    db.execute(RecipeIngredient.__table__.delete().where(RecipeIngredient.recipe_id == recipe_id))
    db.execute(Favorite.__table__.delete().where(Favorite.recipe_id == recipe_id))
    db.execute(Like.__table__.delete().where(Like.recipe_id == recipe_id))
    db.execute(Comment.__table__.delete().where(Comment.recipe_id == recipe_id))
    db.delete(recipe)
    db.commit()


def my_recipes(db: Session, user_id: int, page: int, page_size: int) -> Page[RecipeCard]:
    stmt = (
        select(*RECIPE_CARD_COLS)
        .where(Recipe.source == "user", Recipe.source_id.like(f"user-{user_id}-%"))
        .order_by(Recipe.created_at.desc())
    )
    count_stmt = select(Recipe.id).where(
        Recipe.source == "user", Recipe.source_id.like(f"user-{user_id}-%")
    )
    page_obj = paginate(db, stmt, page, page_size, count_source=count_stmt)
    return Page[RecipeCard](
        items=[_card_from_row(r) for r in page_obj.items],
        total=page_obj.total,
        page=page_obj.page,
        page_size=page_obj.page_size,
        has_more=page_obj.has_more,
    )


def _card_from_row(r) -> RecipeCard:
    return RecipeCard(
        id=r.id,
        title=r.title,
        description=r.description,
        cover_url=r.cover_url,
        category_id=r.category_id,
        likes_count=r.likes_count,
        favorites_count=r.favorites_count,
        comments_count=r.comments_count,
    )


def _replace_ingredients(db: Session, recipe_id: int, ingredients: list[RecipeIngredientIn]):
    db.execute(
        RecipeIngredient.__table__.delete().where(RecipeIngredient.recipe_id == recipe_id)
    )
    for item in ingredients:
        ing_id, _ = resolve_ingredient_id(db, item.name)
        if ing_id is None:
            continue
        db.add(
            RecipeIngredient(
                recipe_id=recipe_id,
                ingredient_id=ing_id,
                raw_text=item.name,
                quantity=item.quantity,
                unit=item.unit,
                is_main=item.is_main,
            )
        )
