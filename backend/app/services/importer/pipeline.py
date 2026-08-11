import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import RecipeImportLog
from app.models.base import SessionLocal
from app.services.importer.cleaner import parse_ingredient_line
from app.services.importer.fetcher import download_dataset, iter_records
from app.services.importer.importer import RecipeDraft, ImportStats, import_records

logger = logging.getLogger(__name__)

ADVISORY_LOCK_KEY = 7474001

_DATA_DIR = Path("data")


def _strip_control(text: str) -> str:
    """Remove NUL and other control bytes PostgreSQL text fields reject."""
    import re as _re

    return _re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)


def _record_to_draft(record: dict, source: str) -> RecipeDraft:
    title = _strip_control((record.get("name") or record.get("title") or "").strip())
    description = record.get("desc") or record.get("description")

    # 真实语料库字段名（下厨房语料库）：recipeIngredient / recipeInstructions
    raw_ingredients = record.get("recipeIngredient") or record.get("ingredients") or []
    raw_steps = record.get("recipeInstructions") or record.get("steps") or []

    steps = []
    if isinstance(raw_steps, list):
        for i, s in enumerate(raw_steps):
            if not s:
                continue
            text = _strip_control(s.get("text") if isinstance(s, dict) else str(s))
            if text:
                steps.append({"step": i + 1, "text": text})
    elif raw_steps:
        steps = [{"step": 1, "text": _strip_control(str(raw_steps))}]

    ingredients = []
    for raw in raw_ingredients:
        if isinstance(raw, str):
            ingredients.extend(parse_ingredient_line(raw))
        elif isinstance(raw, dict):
            ingredients.append(
                {
                    "name": _strip_control(raw.get("name") or ""),
                    "quantity": raw.get("quantity"),
                    "unit": raw.get("unit"),
                    "raw_text": _strip_control(raw.get("text") or raw.get("raw_text") or raw.get("name") or ""),
                }
            )

    source_id = str(record.get("id") or record.get("source_id") or f"idx-{abs(hash(title))}")
    return RecipeDraft(
        title=title,
        description=_strip_control(str(description)) if description else None,
        steps=steps,
        source_id=source_id,
        ingredients=ingredients,
        source=source,
    )


def run_import(db: Session, sample_limit: int | None = None) -> ImportStats:
    """Execute the full import pipeline within one advisory-locked session.

    Streams records in batches to bound memory usage (the full corpus is ~1.5M
    records; holding all drafts in memory would be very heavy).
    """
    log = RecipeImportLog(source=settings.import_source, status="running")
    db.add(log)
    db.commit()

    BATCH_SIZE = 2000
    stats = ImportStats()
    try:
        limit = sample_limit or settings.import_sample_limit
        path = download_dataset(sample_limit=limit)
        drafts: list[RecipeDraft] = []
        for i, record in enumerate(iter_records(path, sample_limit=limit)):
            drafts.append(_record_to_draft(record, settings.import_source))
            if len(drafts) >= BATCH_SIZE:
                batch_stats = import_records(db, drafts, settings.import_source)
                _merge_stats(stats, batch_stats)
                drafts = []
                db.commit()
        if drafts:
            batch_stats = import_records(db, drafts, settings.import_source)
            _merge_stats(stats, batch_stats)
        db.commit()

        log.status = "success"
        log.added_count = stats.added
        log.updated_count = stats.updated
        log.skipped_count = stats.skipped
        log.error_message = (
            f"created_ingredients={stats.created_ingredients}; failed={stats.failed}"
            if stats.created_ingredients or stats.failed
            else None
        )
        db.commit()
        logger.info(
            "Import done: added=%d updated=%d skipped=%d", stats.added, stats.updated, stats.skipped
        )
        return stats
    except Exception as exc:
        db.rollback()
        log = db.get(RecipeImportLog, log.id)
        if log is None:
            log = RecipeImportLog(source=settings.import_source, status="failed")
        log.status = "failed"
        log.error_message = str(exc)
        db.add(log)
        db.commit()
        logger.exception("Import failed: %s", exc)
        raise


def _merge_stats(target: ImportStats, batch: ImportStats) -> None:
    target.added += batch.added
    target.updated += batch.updated
    target.skipped += batch.skipped
    target.created_ingredients += batch.created_ingredients
    target.failed += batch.failed


def acquire_lock(db: Session) -> bool:
    row = db.execute(text("SELECT pg_try_advisory_lock(:key)"), {"key": ADVISORY_LOCK_KEY}).scalar()
    return bool(row)


def release_lock(db: Session) -> None:
    db.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": ADVISORY_LOCK_KEY})


def run_import_job() -> None:
    """Background job entry point; guards against concurrent runs via PG advisory lock."""
    db = SessionLocal()
    try:
        if not acquire_lock(db):
            logger.info("Another import is already running; skipping.")
            return
        try:
            run_import(db)
        finally:
            release_lock(db)
    finally:
        db.close()
