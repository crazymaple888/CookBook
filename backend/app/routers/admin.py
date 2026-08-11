from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.models import Ingredient, IngredientSynonym, RecipeImportLog, User
from app.models.base import get_db
from app.schemas.ingredient import IngredientOut
from app.services.importer.pipeline import run_import_job

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/import/trigger")
def trigger_import(
    background_tasks: BackgroundTasks,
    _: User = Depends(get_current_admin),
):
    """Trigger the dataset import asynchronously in the background."""
    background_tasks.add_task(run_import_job)
    return {"status": "triggered"}


@router.get("/import/status")
def import_status(_: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    latest = db.scalar(
        select(RecipeImportLog).order_by(RecipeImportLog.id.desc()).limit(1)
    )
    if latest is None:
        return {"has_run": False}
    return {
        "has_run": True,
        "status": latest.status,
        "source": latest.source,
        "added_count": latest.added_count,
        "updated_count": latest.updated_count,
        "skipped_count": latest.skipped_count,
        "error_message": latest.error_message,
        "started_at": latest.started_at,
        "finished_at": latest.finished_at,
    }


class IngredientCreate(BaseModel):
    name: str
    category_id: int | None = None
    synonyms: list[str] = []


class SynonymAdd(BaseModel):
    synonyms: list[str]


@router.post("/ingredients", response_model=IngredientOut, status_code=201)
def create_ingredient(
    payload: IngredientCreate,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    exists = db.scalar(select(Ingredient).where(Ingredient.name == payload.name))
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Ingredient already exists"
        )
    ing = Ingredient(name=payload.name, category_id=payload.category_id)
    db.add(ing)
    db.flush()
    for s in payload.synonyms:
        db.add(IngredientSynonym(ingredient_id=ing.id, synonym=s))
    db.commit()
    db.refresh(ing)
    return IngredientOut.model_validate(ing)


@router.post("/ingredients/{ingredient_id}/synonyms", status_code=204)
def add_synonyms(
    ingredient_id: int,
    payload: SynonymAdd,
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    ing = db.get(Ingredient, ingredient_id)
    if ing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ingredient not found")
    for s in payload.synonyms:
        exists = db.scalar(
            select(IngredientSynonym).where(IngredientSynonym.synonym == s)
        )
        if exists is None:
            db.add(IngredientSynonym(ingredient_id=ing.id, synonym=s))
    db.commit()


@router.get("/ingredients", response_model=list[IngredientOut])
def list_ingredients(
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    ings = db.scalars(select(Ingredient).order_by(Ingredient.name)).all()
    return [IngredientOut.model_validate(i) for i in ings]
