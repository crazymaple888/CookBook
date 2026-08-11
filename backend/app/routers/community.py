from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.models import User
from app.models.base import get_db
from app.schemas.common import Page
from app.schemas.community import CommentCreate, CommentList, CommentOut
from app.schemas.recipe import RecipeCard
from app.services import community_service

router = APIRouter(tags=["community"])


@router.post("/recipes/{recipe_id}/favorite", status_code=201)
def favorite(
    recipe_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    added = community_service.add_favorite(db, user.id, recipe_id)
    if not added:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already favorited")
    return {"status": "ok"}


@router.delete("/recipes/{recipe_id}/favorite", status_code=204)
def unfavorite(
    recipe_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    community_service.remove_favorite(db, user.id, recipe_id)


@router.get("/users/me/favorites", response_model=Page[RecipeCard])
def my_favorites(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return community_service.my_favorites(db, user.id, page, page_size)


@router.post("/recipes/{recipe_id}/like")
def like(
    recipe_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return community_service.toggle_like(db, user.id, recipe_id)


@router.post("/recipes/{recipe_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(
    recipe_id: int,
    payload: CommentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = community_service.add_comment(
        db, user.id, recipe_id, payload.content, payload.parent_id
    )
    return CommentOut(
        id=comment.id,
        recipe_id=comment.recipe_id,
        user_id=comment.user_id,
        parent_id=comment.parent_id,
        content=comment.content,
        created_at=comment.created_at,
        author_name=user.nickname or user.username,
    )


@router.get("/recipes/{recipe_id}/comments", response_model=CommentList)
def list_comments(
    recipe_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return community_service.list_comments(db, recipe_id, page, page_size)


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(
    comment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    community_service.delete_comment(db, comment_id, user.id, user.is_admin)
