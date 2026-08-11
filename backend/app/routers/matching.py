from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.base import get_db
from app.schemas.matching import MatchRequest, MatchResponse
from app.services import matching_service

router = APIRouter(tags=["matching"])


@router.post("/match", response_model=MatchResponse)
def match(payload: MatchRequest, db: Session = Depends(get_db)):
    return matching_service.match_recipes(db, payload)
