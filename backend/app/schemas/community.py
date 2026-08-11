from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    parent_id: int | None = None


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recipe_id: int
    user_id: int
    parent_id: int | None = None
    content: str
    created_at: datetime
    author_name: str | None = None
    replies: list["CommentOut"] = []


class CommentList(BaseModel):
    items: list[CommentOut]
    total: int
