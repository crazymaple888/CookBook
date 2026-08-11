from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Comment, Favorite, Like, Recipe, User
from app.schemas.common import Page
from app.schemas.community import CommentList, CommentOut
from app.schemas.recipe import RecipeCard
from app.services.recipe_service import RECIPE_CARD_COLS, _card_from_row
from app.utils.pagination import paginate


def _get_recipe(db: Session, recipe_id: int) -> Recipe:
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return recipe


def add_favorite(db: Session, user_id: int, recipe_id: int) -> bool:
    _get_recipe(db, recipe_id)
    exists = db.scalar(
        select(Favorite.id).where(
            Favorite.user_id == user_id, Favorite.recipe_id == recipe_id
        )
    )
    if exists is None:
        db.add(Favorite(user_id=user_id, recipe_id=recipe_id))
        recipe = db.get(Recipe, recipe_id)
        recipe.favorites_count += 1
        db.commit()
        return True
    return False


def remove_favorite(db: Session, user_id: int, recipe_id: int) -> bool:
    fav = db.scalar(
        select(Favorite).where(
            Favorite.user_id == user_id, Favorite.recipe_id == recipe_id
        )
    )
    if fav is not None:
        db.delete(fav)
        recipe = db.get(Recipe, recipe_id)
        if recipe is not None:
            recipe.favorites_count = max(recipe.favorites_count - 1, 0)
        db.commit()
        return True
    return False


def my_favorites(db: Session, user_id: int, page: int, page_size: int) -> Page[RecipeCard]:
    stmt = (
        select(*RECIPE_CARD_COLS)
        .join(Favorite, Favorite.recipe_id == Recipe.id)
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.id.desc())
    )
    count_stmt = (
        select(Recipe.id)
        .join(Favorite, Favorite.recipe_id == Recipe.id)
        .where(Favorite.user_id == user_id)
    )
    page_obj = paginate(db, stmt, page, page_size, count_source=count_stmt)
    return Page[RecipeCard](
        items=[_card_from_row(r) for r in page_obj.items],
        total=page_obj.total,
        page=page_obj.page,
        page_size=page_obj.page_size,
        has_more=page_obj.has_more,
    )


def toggle_like(db: Session, user_id: int, recipe_id: int) -> dict:
    _get_recipe(db, recipe_id)
    like = db.scalar(
        select(Like).where(Like.user_id == user_id, Like.recipe_id == recipe_id)
    )
    recipe = db.get(Recipe, recipe_id)
    if like is None:
        db.add(Like(user_id=user_id, recipe_id=recipe_id))
        recipe.likes_count += 1
        liked = True
    else:
        db.delete(like)
        recipe.likes_count = max(recipe.likes_count - 1, 0)
        liked = False
    db.commit()
    db.refresh(recipe)
    return {"liked": liked, "likes_count": recipe.likes_count}


def add_comment(
    db: Session, user_id: int, recipe_id: int, content: str, parent_id: int | None
) -> Comment:
    _get_recipe(db, recipe_id)
    if parent_id is not None:
        parent = db.get(Comment, parent_id)
        if parent is None or parent.recipe_id != recipe_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid parent comment"
            )
    comment = Comment(
        recipe_id=recipe_id, user_id=user_id, parent_id=parent_id, content=content
    )
    db.add(comment)
    recipe = db.get(Recipe, recipe_id)
    recipe.comments_count += 1
    db.commit()
    db.refresh(comment)
    return comment


def list_comments(db: Session, recipe_id: int, page: int, page_size: int) -> CommentList:
    _get_recipe(db, recipe_id)
    total = db.scalar(
        select(func.count(Comment.id)).where(Comment.recipe_id == recipe_id)
    ) or 0

    root_rows = db.execute(
        select(Comment, User.nickname)
        .outerjoin(User, User.id == Comment.user_id)
        .where(Comment.recipe_id == recipe_id, Comment.parent_id.is_(None))
        .order_by(Comment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    root_ids = [r.Comment.id for r in root_rows]
    replies_by_parent: dict[int, list[CommentOut]] = {}
    if root_ids:
        reply_rows = db.execute(
            select(Comment, User.nickname)
            .outerjoin(User, User.id == Comment.user_id)
            .where(Comment.recipe_id == recipe_id, Comment.parent_id.in_(root_ids))
            .order_by(Comment.created_at.asc())
        ).all()
        for c, nickname in reply_rows:
            replies_by_parent.setdefault(c.parent_id, []).append(
                CommentOut(
                    id=c.id,
                    recipe_id=c.recipe_id,
                    user_id=c.user_id,
                    parent_id=c.parent_id,
                    content=c.content,
                    created_at=c.created_at,
                    author_name=nickname or f"user{c.user_id}",
                )
            )

    items = []
    for c, nickname in root_rows:
        items.append(
            CommentOut(
                id=c.id,
                recipe_id=c.recipe_id,
                user_id=c.user_id,
                parent_id=c.parent_id,
                content=c.content,
                created_at=c.created_at,
                author_name=nickname or f"user{c.user_id}",
                replies=replies_by_parent.get(c.id, []),
            )
        )
    return CommentList(items=items, total=total)


def delete_comment(db: Session, comment_id: int, user_id: int, is_admin: bool) -> None:
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if not (is_admin or comment.user_id == user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed"
        )
    recipe = db.get(Recipe, comment.recipe_id)
    db.delete(comment)
    if recipe is not None:
        recipe.comments_count = max(recipe.comments_count - 1, 0)
    db.commit()
