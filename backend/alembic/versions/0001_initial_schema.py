"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "recipe_categories",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
    )

    op.create_table(
        "ingredient_categories",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(64), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=True, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("nickname", sa.String(64), nullable=True),
        sa.Column("avatar_url", sa.String(512), nullable=True),
        sa.Column("bio", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_admin", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "ingredients",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("category_id", sa.BigInteger(), sa.ForeignKey("ingredient_categories.id"), nullable=True),
        sa.Column("image_url", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ingredients_name", "ingredients", ["name"])

    op.create_table(
        "ingredient_synonyms",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("ingredient_id", sa.BigInteger(), sa.ForeignKey("ingredients.id"), nullable=False),
        sa.Column("synonym", sa.String(64), nullable=False, unique=True),
    )
    op.create_index("ix_ingredient_synonyms_ingredient_id", "ingredient_synonyms", ["ingredient_id"])
    op.create_index("ix_ingredient_synonyms_synonym", "ingredient_synonyms", ["synonym"])

    op.create_table(
        "recipes",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cover_url", sa.String(512), nullable=True),
        sa.Column("category_id", sa.BigInteger(), sa.ForeignKey("recipe_categories.id"), nullable=True),
        sa.Column("steps", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("prep_time", sa.Integer(), nullable=True),
        sa.Column("cook_time", sa.Integer(), nullable=True),
        sa.Column("servings", sa.Integer(), nullable=True),
        sa.Column("difficulty", sa.String(32), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_id", sa.String(128), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("is_published", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("likes_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("favorites_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("comments_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("source", "source_id", name="uq_recipes_source_source_id"),
    )
    op.create_index("ix_recipes_title", "recipes", ["title"])
    op.create_index("ix_recipes_category_id", "recipes", ["category_id"])

    op.create_table(
        "recipe_ingredients",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("recipe_id", sa.BigInteger(), sa.ForeignKey("recipes.id"), nullable=False),
        sa.Column("ingredient_id", sa.BigInteger(), sa.ForeignKey("ingredients.id"), nullable=False),
        sa.Column("raw_text", sa.String(255), nullable=True),
        sa.Column("quantity", sa.Numeric(10, 3), nullable=True),
        sa.Column("unit", sa.String(32), nullable=True),
        sa.Column("is_main", sa.Boolean(), server_default="true", nullable=False),
        sa.UniqueConstraint("recipe_id", "ingredient_id", name="uq_recipe_ingredients_recipe_ingredient"),
    )
    op.create_index("ix_recipe_ingredients_recipe_id", "recipe_ingredients", ["recipe_id"])
    op.create_index("ix_recipe_ingredients_ingredient_id", "recipe_ingredients", ["ingredient_id"])

    op.create_table(
        "favorites",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("recipe_id", sa.BigInteger(), sa.ForeignKey("recipes.id"), nullable=False),
        sa.UniqueConstraint("user_id", "recipe_id", name="uq_favorites_user_recipe"),
    )
    op.create_index("ix_favorites_user_id", "favorites", ["user_id"])
    op.create_index("ix_favorites_recipe_id", "favorites", ["recipe_id"])

    op.create_table(
        "comments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("recipe_id", sa.BigInteger(), sa.ForeignKey("recipes.id"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("parent_id", sa.BigInteger(), sa.ForeignKey("comments.id"), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_comments_recipe_id", "comments", ["recipe_id"])
    op.create_index("ix_comments_user_id", "comments", ["user_id"])

    op.create_table(
        "likes",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("recipe_id", sa.BigInteger(), sa.ForeignKey("recipes.id"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.UniqueConstraint("user_id", "recipe_id", name="uq_likes_user_recipe"),
    )
    op.create_index("ix_likes_recipe_id", "likes", ["recipe_id"])
    op.create_index("ix_likes_user_id", "likes", ["user_id"])

    op.create_table(
        "recipe_import_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), server_default="running", nullable=False),
        sa.Column("added_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("updated_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("skipped_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.execute(
        "CREATE INDEX ix_recipes_search_trgm ON recipes USING gin (title gin_trgm_ops, description gin_trgm_ops)"
    )


def downgrade() -> None:
    op.drop_table("recipe_import_logs")
    op.drop_table("likes")
    op.drop_table("comments")
    op.drop_table("favorites")
    op.drop_table("recipe_ingredients")
    op.drop_table("recipes")
    op.drop_table("ingredient_synonyms")
    op.drop_table("ingredients")
    op.drop_table("users")
    op.drop_table("ingredient_categories")
    op.drop_table("recipe_categories")
