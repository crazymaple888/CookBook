from pydantic import BaseModel, Field


class MatchRequest(BaseModel):
    ingredient_ids: list[int] = Field(default_factory=list)
    ingredient_names: list[str] = Field(default_factory=list)
    page: int = 1
    page_size: int = 20


class MatchIngredient(BaseModel):
    name: str
    raw_text: str | None = None
    quantity: float | None = None
    unit: str | None = None
    label: str | None = None


class MatchRecipe(BaseModel):
    id: int
    title: str
    cover_url: str | None = None
    description: str | None = None


class MatchResultItem(BaseModel):
    recipe: MatchRecipe
    coverage: float
    is_complete: bool
    matched_ingredients: list[MatchIngredient] = []
    missing_ingredients: list[MatchIngredient] = []


class MatchResponse(BaseModel):
    items: list[MatchResultItem]
    total: int
    page: int
    page_size: int
    has_more: bool
    unresolved_names: list[str] = []
