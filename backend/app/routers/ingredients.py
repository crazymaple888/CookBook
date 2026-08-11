from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.models.base import get_db
from app.schemas.common import Page
from app.schemas.ingredient import IngredientCategoryOut, IngredientOut
from app.services import ingredient_service

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("/search", response_model=Page[IngredientOut])
def search(
    q: str = Query(default="", max_length=64),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return ingredient_service.search_ingredients(db, q, page, page_size)


@router.get("/categories", response_model=list[IngredientCategoryOut])
def categories(db: Session = Depends(get_db)):
    return ingredient_service.category_tree(db)
