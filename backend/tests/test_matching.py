from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.models import Base, Ingredient, Recipe, RecipeIngredient
from app.services.matching_service import match_recipes
from app.schemas.matching import MatchRequest

# Make JSONB columns compile on SQLite so in-memory tests can create tables.
from sqlalchemy.dialects.postgresql import JSONB as PGJSONB
from sqlalchemy.ext.compiler import compiles


@compiles(PGJSONB, "sqlite")
def _compile_pgjsonb_sqlite(type_, compiler, **kw):
    return "JSON"


def _make_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine), engine


def _ingredient(db: Session, name: str) -> Ingredient:
    ing = Ingredient(name=name)
    db.add(ing)
    db.flush()
    return ing


def _recipe(db: Session, title: str, ingredients: list[Ingredient]) -> Recipe:
    r = Recipe(
        title=title,
        steps=[],
        source="test",
        source_id=title,
        content_hash="x" * 64,
    )
    db.add(r)
    db.flush()
    for ing in ingredients:
        db.add(RecipeIngredient(recipe_id=r.id, ingredient_id=ing.id, raw_text=ing.name))
    return r


def test_coverage_ordering_and_missing():
    db, engine = _make_db()
    tomato = _ingredient(db, "西红柿")
    egg = _ingredient(db, "鸡蛋")
    pork = _ingredient(db, "猪肉")
    onion = _ingredient(db, "葱")

    # 番茄炒蛋: 西红柿+鸡蛋+葱 (3 ingredients)
    r1 = _recipe(db, "番茄炒蛋", [tomato, egg, onion])
    # 西红柿蛋汤: 西红柿+鸡蛋 (2 ingredients)
    r2 = _recipe(db, "西红柿蛋汤", [tomato, egg])
    # 猪肉炖葱: 猪肉+葱 (2 ingredients)
    r3 = _recipe(db, "猪肉炖葱", [pork, onion])
    db.commit()

    # User has: 西红柿 + 鸡蛋
    resp = match_recipes(
        db,
        MatchRequest(
            ingredient_ids=[tomato.id, egg.id],
            page=1,
            page_size=20,
        ),
    )
    assert resp.total == 2  # r1 and r2 match, r3 has no overlap
    # r2 coverage=1.0, r1 coverage=2/3 -> r2 first
    assert [item.recipe.id for item in resp.items] == [r2.id, r1.id]
    assert resp.items[0].is_complete is True
    assert resp.items[0].missing_ingredients == []
    assert resp.items[1].is_complete is False
    missing_names = {m.name for m in resp.items[1].missing_ingredients}
    assert missing_names == {"葱"}
    assert resp.items[1].missing_ingredients[0].label == "需购买"
    engine.dispose()


def test_text_name_resolution_and_unresolved():
    db, engine = _make_db()
    tomato = _ingredient(db, "西红柿")
    egg = _ingredient(db, "鸡蛋")
    _recipe(db, "西红柿炒鸡蛋", [tomato, egg])
    db.commit()

    resp = match_recipes(
        db,
        MatchRequest(
            ingredient_names=["番茄", "鸡蛋"],
            page=1,
            page_size=20,
        ),
    )
    # "番茄" not in synonyms -> unresolved; "鸡蛋" resolves and matches the recipe at 50%.
    assert "番茄" in resp.unresolved_names
    assert resp.total == 1
    item = resp.items[0]
    assert item.coverage == 0.5
    assert {m.name for m in item.missing_ingredients} == {"西红柿"}
    engine.dispose()


def test_synonym_resolution():
    db, engine = _make_db()
    tomato = _ingredient(db, "西红柿")
    from app.models import IngredientSynonym

    db.add(IngredientSynonym(ingredient_id=tomato.id, synonym="番茄"))
    egg = _ingredient(db, "鸡蛋")
    _recipe(db, "西红柿炒鸡蛋", [tomato, egg])
    db.commit()

    resp = match_recipes(
        db,
        MatchRequest(
            ingredient_names=["番茄", "鸡蛋"],
            page=1,
            page_size=20,
        ),
    )
    assert resp.unresolved_names == []
    assert resp.total == 1
    assert resp.items[0].coverage == 1.0
    assert resp.items[0].is_complete is True
    engine.dispose()
