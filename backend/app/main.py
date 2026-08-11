from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.redis import close_redis, init_redis
from app.models.base import engine, SessionLocal
from app.scheduler.jobs import schedule_import_job
from app.scheduler.scheduler import shutdown_scheduler, start_scheduler
from app.routers import auth, community, ingredients, matching, recipes, users, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_redis()
    start_scheduler()
    schedule_import_job()
    yield
    shutdown_scheduler()
    close_redis()
    engine.dispose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(recipes.router, prefix="/api")
app.include_router(ingredients.router, prefix="/api")
app.include_router(matching.router, prefix="/api")
app.include_router(community.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/api/health")
def health():
    db_ok = True
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False
    return {"status": "ok", "database": "ok" if db_ok else "error"}
