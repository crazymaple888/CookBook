from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.scheduler.scheduler import start_scheduler
from app.services.importer.pipeline import run_import_job


def schedule_import_job() -> None:
    scheduler = start_scheduler()
    scheduler.add_job(
        run_import_job,
        CronTrigger(
            day_of_week="*",
            hour=settings.import_cron_hour,
            minute=settings.import_cron_minute,
            timezone="Asia/Shanghai",
        ),
        id="update_recipes_job",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
