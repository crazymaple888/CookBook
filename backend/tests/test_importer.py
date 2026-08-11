import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.models import Base, Ingredient, Recipe, RecipeIngredient
from app.services.importer.cleaner import parse_ingredient_line
from app.services.importer.importer import RecipeDraft, import_records

# Register JSONB compiler for SQLite.
from sqlalchemy.dialects.postgresql import JSONB as PGJSONB
from sqlalchemy.ext.compiler import compiles


@compiles(PGJSONB, "sqlite")
def _compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


def _make_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine), engine


def test_parse_ingredient_line():
    assert parse_ingredient_line("猪肉500克")[0]["name"] == "猪肉"
    assert parse_ingredient_line("猪肉500克")[0]["quantity"] == 500.0
    assert parse_ingredient_line("猪肉500克")[0]["unit"] == "克"
    assert parse_ingredient_line("鸡蛋2个")[0]["name"] == "鸡蛋"
    assert parse_ingredient_line("番茄切成丁")[0]["name"] == "番茄"
    # 逗号分隔多食材会拆成多个
    multi = parse_ingredient_line("适量橄榄油，盐，黑胡椒")
    assert len(multi) == 3
    # 装饰文本返回空 name
    assert parse_ingredient_line("【烫种】")[0]["name"] == ""


def test_import_idempotent():
    db, engine = _make_db()
    drafts = [
        RecipeDraft(
            title="番茄炒蛋",
            steps=[{"step": 1, "text": "打蛋"}],
            source_id="1001",
            ingredients=[
                {"name": "番茄", "quantity": 2, "unit": "个", "raw_text": "番茄2个"},
                {"name": "鸡蛋", "quantity": 3, "unit": "个", "raw_text": "鸡蛋3个"},
            ],
        )
    ]
    stats1 = import_records(db, drafts, "test-source")
    assert stats1.added == 1
    assert stats1.created_ingredients == 2  # 番茄 and 鸡蛋 auto-created

    # Idempotent: same content -> skipped.
    stats2 = import_records(db, drafts, "test-source")
    assert stats2.skipped == 1
    assert stats2.added == 0

    # Changed content -> updated.
    drafts[0].ingredients = [
        {"name": "番茄", "quantity": 3, "unit": "个", "raw_text": "番茄3个"},
        {"name": "鸡蛋", "quantity": 3, "unit": "个", "raw_text": "鸡蛋3个"},
    ]
    stats3 = import_records(db, drafts, "test-source")
    assert stats3.updated == 1
    assert stats3.skipped == 0

    # recipe_ingredients rebuilt correctly.
    recipe = db.query(Recipe).filter_by(source_id="1001").one()
    assert recipe.title == "番茄炒蛋"
    ri = db.query(RecipeIngredient).filter_by(recipe_id=recipe.id).all()
    assert len(ri) == 2
    assert {r.raw_text for r in ri} == {"番茄3个", "鸡蛋3个"}
    engine.dispose()


def test_ingredient_synonym_resolution_on_import():
    db, engine = _make_db()
    from app.models import IngredientSynonym

    db.add(IngredientSynonym(ingredient_id=1, synonym="tomato"))
    # ingredient_id=1 doesn't exist; ensure import still works and doesn't crash.
    drafts = [
        RecipeDraft(
            title="测试",
            steps=[],
            source_id="2001",
            ingredients=[{"name": "测试食材", "raw_text": "测试食材"}],
        )
    ]
    stats = import_records(db, drafts, "test-source")
    assert stats.added == 1
    engine.dispose()
