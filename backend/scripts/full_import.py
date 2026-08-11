"""Full corpus import driver.

Runs the import pipeline over the whole corpus in batches, printing progress.
Usage:
    DATABASE_URL=... IMPORT_DATA_DIR=... python -m scripts.full_import
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

from app.models import Ingredient, Recipe, RecipeIngredient
from app.services.importer.fetcher import download_dataset, iter_records
from app.services.importer.importer import ImportStats, import_records
from app.services.importer.pipeline import _record_to_draft

BATCH_SIZE = 2000
PROGRESS_EVERY = 20000


def main() -> None:
    import os

    engine = create_engine(os.environ["DATABASE_URL"])
    db = Session(engine)

    # Optional: clean existing corpus imports (controlled by FULL_IMPORT_CLEAN=1).
    if os.environ.get("FULL_IMPORT_CLEAN") == "1":
        db.execute(
            text(
                "DELETE FROM recipe_ingredients WHERE recipe_id IN "
                "(SELECT id FROM recipes WHERE source = 'chinese-recipes-corpus')"
            )
        )
        db.execute(text("DELETE FROM recipes WHERE source = 'chinese-recipes-corpus'"))
        db.execute(
            text(
                "DELETE FROM ingredients WHERE name NOT IN "
                "('西红柿','鸡蛋','葱','猪肉','土豆','茄子','小葱','洋葱','大蒜','生姜',"
                "'白菜','菠菜','胡萝卜','鸡肉','豆腐','大米','面粉','生抽','老抽','蚝油',"
                "'白糖','盐','料酒','食用油','辣椒','黄瓜','青椒','香菇','金针菇','虾',"
                "'鱼','苹果','香蕉','牛奶')"
            )
        )
        db.commit()
        print("[clean] 已清空历史语料库数据")

    path = download_dataset(sample_limit=None)
    stats = ImportStats()
    start = time.time()

    drafts: list = []
    total_read = 0
    for record in iter_records(path, sample_limit=None):
        drafts.append(_record_to_draft(record, "chinese-recipes-corpus"))
        total_read += 1
        if len(drafts) >= BATCH_SIZE:
            batch_stats = import_records(db, drafts, "chinese-recipes-corpus")
            _merge(stats, batch_stats)
            drafts = []
            db.commit()
            if total_read % PROGRESS_EVERY == 0:
                _report(stats, total_read, start)

    if drafts:
        batch_stats = import_records(db, drafts, "chinese-recipes-corpus")
        _merge(stats, batch_stats)
        db.commit()

    elapsed = time.time() - start
    total = db.scalar(select(func.count()).select_from(Recipe))
    ri = db.scalar(select(func.count()).select_from(RecipeIngredient))
    ing = db.scalar(select(func.count()).select_from(Ingredient))
    print(f"\n=== 完成 ===")
    print(f"读取 {total_read} 条 | 耗时 {elapsed/60:.1f} 分钟")
    print(f"added={stats.added} updated={stats.updated} skipped={stats.skipped} failed={stats.failed}")
    print(f"菜谱总数={total} 关联={ri} 食材总数={ing}")
    db.close()


def _merge(target: ImportStats, batch: ImportStats) -> None:
    target.added += batch.added
    target.updated += batch.updated
    target.skipped += batch.skipped
    target.created_ingredients += batch.created_ingredients
    target.failed += batch.failed


def _report(stats: ImportStats, read: int, start: float) -> None:
    elapsed = time.time() - start
    speed = read / elapsed
    print(
        f"[{read}] {elapsed:.0f}s | {speed:.0f}条/s | "
        f"added={stats.added} failed={stats.failed} 食材={stats.created_ingredients}"
    )


if __name__ == "__main__":
    main()
