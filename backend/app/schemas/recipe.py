from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RecipeIngredientIn(BaseModel):
    name: str
    quantity: float | None = None
    unit: str | None = None
    is_main: bool = True


class RecipeCategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sort_order: int = 0


class RecipeIngredientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    raw_text: str | None = None
    quantity: float | None = None
    unit: str | None = None
    is_main: bool = True


class RecipeCard(BaseModel):
    id: int
    title: str
    description: str | None = None
    cover_url: str | None = None
    category_id: int | None = None
    likes_count: int = 0
    favorites_count: int = 0
    comments_count: int = 0


class RecipeDetail(RecipeCard):
    steps: list[dict] = []
    prep_time: int | None = None
    cook_time: int | None = None
    servings: int | None = None
    difficulty: str | None = None
    created_at: datetime
    is_favorited: bool = False
    is_liked: bool = False
    ingredients: list[RecipeIngredientOut] = []


class RecipeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=2000)
    cover_url: str | None = Field(default=None, max_length=512)
    category_id: int | None = None
    steps: list[dict] = Field(default_factory=list)
    prep_time: int | None = None
    cook_time: int | None = None
    servings: int | None = None
    difficulty: str | None = None
    ingredients: list[RecipeIngredientIn] = Field(default_factory=list)


class RecipeUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=128)
    description: str | None = Field(default=None, max_length=2000)
    cover_url: str | None = Field(default=None, max_length=512)
    category_id: int | None = None
    steps: list[dict] | None = None
    ingredients: list[RecipeIngredientIn] | None = None
