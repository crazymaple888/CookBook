from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class IngredientCategory(Base):
    __tablename__ = "ingredient_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Ingredient(Base, TimestampMixin):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("ingredient_categories.id"), nullable=True
    )
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)


class IngredientSynonym(Base):
    __tablename__ = "ingredient_synonyms"

    id: Mapped[int] = mapped_column(primary_key=True)
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id"), index=True
    )
    synonym: Mapped[str] = mapped_column(String(64), unique=True, index=True)
