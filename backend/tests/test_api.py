import pytest
from fastapi.testclient import TestClient

from app.core.deps import get_db
from app.main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.postgresql import JSONB as PGJSONB
from sqlalchemy.ext.compiler import compiles

from app.models import Base, User

from tests.test_matching import _compile_pgjsonb_sqlite  # noqa: F401  (registers compiler)

# 模块级 session 工厂，供测试注册后授予上传权限
_test_session: sessionmaker | None = None


@pytest.fixture()
def client():
    global _test_session
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    _test_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    TestSession = _test_session

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    _test_session = None


def _register(client, username="alice", password="secret123", email="alice@test.com"):
    resp = client.post(
        "/api/auth/register",
        json={"username": username, "password": password, "email": email},
    )
    # 授予上传权限，方便测试发布流程（生产环境需申请审核）
    if _test_session is not None and resp.status_code == 200:
        from sqlalchemy import update

        db = _test_session()
        try:
            db.execute(
                update(User).where(User.username == username).values(uploader_status="approved")
            )
            db.commit()
        finally:
            db.close()
    return resp


def _auth_headers(resp) -> dict:
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_auth_flow(client):
    r = _register(client)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["user"]["username"] == "alice"
    assert data["access_token"]

    me = client.get("/api/users/me", headers=_auth_headers(r))
    assert me.status_code == 200
    assert me.json()["username"] == "alice"

    login = client.post(
        "/api/auth/login", json={"account": "alice", "password": "secret123"}
    )
    assert login.status_code == 200

    dup = _register(client)
    assert dup.status_code == 409


def test_recipe_crud_and_community(client):
    # Create ingredient + recipe directly in DB via a session? Simpler: user publishes recipe.
    reg = _register(client)
    headers = _auth_headers(reg)

    # Publish a recipe (uses text ingredients, unresolved ones are skipped).
    create = client.post(
        "/api/recipes",
        json={
            "title": "番茄炒蛋",
            "description": "家常菜",
            "steps": [{"step": 1, "text": "打蛋"}],
            "ingredients": [{"name": "西红柿"}, {"name": "鸡蛋"}],
        },
        headers=headers,
    )
    assert create.status_code == 201, create.text
    recipe_id = create.json()["id"]
    assert create.json()["title"] == "番茄炒蛋"

    # Detail (logged out) - not favorited.
    detail = client.get(f"/api/recipes/{recipe_id}")
    assert detail.status_code == 200
    assert detail.json()["is_favorited"] is False

    # Random list should include it.
    rand = client.get("/api/recipes/random")
    assert rand.status_code == 200
    assert any(r["id"] == recipe_id for r in rand.json())

    # Favorite it.
    fav = client.post(f"/api/recipes/{recipe_id}/favorite", headers=headers)
    assert fav.status_code == 201
    favs = client.get("/api/users/me/favorites", headers=headers)
    assert favs.status_code == 200
    assert favs.json()["total"] == 1

    # Unfavorite.
    assert client.delete(f"/api/recipes/{recipe_id}/favorite", headers=headers).status_code == 204
    favs = client.get("/api/users/me/favorites", headers=headers)
    assert favs.json()["total"] == 0

    # Like toggle.
    like1 = client.post(f"/api/recipes/{recipe_id}/like", headers=headers)
    assert like1.json()["liked"] is True
    like2 = client.post(f"/api/recipes/{recipe_id}/like", headers=headers)
    assert like2.json()["liked"] is False

    # Comment.
    c = client.post(
        f"/api/recipes/{recipe_id}/comments",
        json={"content": "很好吃！"},
        headers=headers,
    )
    assert c.status_code == 201, c.text
    comment_id = c.json()["id"]
    comments = client.get(f"/api/recipes/{recipe_id}/comments")
    assert comments.json()["total"] == 1
    assert comments.json()["items"][0]["content"] == "很好吃！"

    # Delete comment.
    assert client.delete(f"/api/comments/{comment_id}", headers=headers).status_code == 204

    # Author delete recipe.
    assert client.delete(f"/api/recipes/{recipe_id}", headers=headers).status_code == 204
    assert client.get(f"/api/recipes/{recipe_id}").status_code == 404


def test_non_author_cannot_delete(client):
    reg = _register(client, username="bob", email="bob@test.com")
    bob_headers = _auth_headers(reg)

    reg2 = _register(client, username="carol", email="carol@test.com")
    carol_headers = _auth_headers(reg2)

    create = client.post(
        "/api/recipes",
        json={"title": "红烧肉", "ingredients": [{"name": "猪肉"}]},
        headers=bob_headers,
    )
    recipe_id = create.json()["id"]

    # Carol cannot delete Bob's recipe.
    assert (
        client.delete(f"/api/recipes/{recipe_id}", headers=carol_headers).status_code == 403
    )
