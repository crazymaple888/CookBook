from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_optional_current_user
from app.models import Recipe, User
from app.models.base import get_db
from app.schemas.common import Page
from app.schemas.recipe import (
    RecipeCard,
    RecipeCategoryOut,
    RecipeCreate,
    RecipeDetail,
    RecipeUpdate,
)
from app.services import recipe_service

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("/random", response_model=list[RecipeCard])
def random(
    count: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return recipe_service.random_recipes(db, count)


@router.get("/categories", response_model=list[RecipeCategoryOut])
def categories(db: Session = Depends(get_db)):
    return recipe_service.list_categories(db)


@router.get("", response_model=Page[RecipeCard])
def list_recipes(
    query: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
    sort: str = Query(default="new", pattern="^(new|hot)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return recipe_service.list_recipes(db, query, category_id, sort, page, page_size)


@router.get("/users/me/recipes", response_model=Page[RecipeCard])
def my_recipes(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return recipe_service.my_recipes(db, user.id, page, page_size)


@router.get("/{recipe_id}", response_model=RecipeDetail)
def detail(
    recipe_id: int,
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    return recipe_service.get_recipe_detail(db, recipe_id, user.id if user else None)


@router.post("", response_model=RecipeDetail, status_code=201)
def create_recipe(
    payload: RecipeCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    recipe = recipe_service.create_recipe(db, payload, user.id)
    return recipe_service.get_recipe_detail(db, recipe.id, user.id)


@router.put("/{recipe_id}", response_model=RecipeDetail)
def update_recipe(
    recipe_id: int,
    payload: RecipeUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_author(db, recipe_id, user)
    recipe = recipe_service.update_recipe(db, recipe_id, payload, user.id)
    return recipe_service.get_recipe_detail(db, recipe.id, user.id)


@router.delete("/{recipe_id}", status_code=204)
def delete_recipe(
    recipe_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_author(db, recipe_id, user)
    recipe_service.delete_recipe(db, recipe_id)


def _check_author(db: Session, recipe_id: int, user: User) -> None:
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    if not (
        user.is_admin
        or (recipe.source == "user" and recipe.source_id.startswith(f"user-{user.id}-"))
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only author or admin can modify",
        )
