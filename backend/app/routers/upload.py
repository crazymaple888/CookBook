from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin, get_current_user
from app.models import User
from app.models.base import get_db
from pydantic import BaseModel

router = APIRouter(tags=["upload"])


class UploadStatusOut(BaseModel):
    status: str
    username: str


@router.post("/upload/apply", response_model=UploadStatusOut)
def apply_upload(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """User applies for upload permission."""
    if user.is_admin:
        return UploadStatusOut(status="approved", username=user.username)
    # Any current status can re-apply (rejected -> pending, none -> pending).
    user.uploader_status = "pending"
    db.commit()
    return UploadStatusOut(status="pending", username=user.username)


@router.get("/upload/status", response_model=UploadStatusOut)
def upload_status(
    user: User = Depends(get_current_user),
):
    if user.is_admin:
        status_val = "approved"
    else:
        status_val = user.uploader_status or "none"
    return UploadStatusOut(status=status_val, username=user.username)
