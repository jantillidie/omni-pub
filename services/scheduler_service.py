import logging
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.jobstores.base import JobLookupError

import sys
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from services.bluesky_service import post_with_image as post_to_bluesky
from services.mastodon_service import post_with_image as post_to_mastodon

logger = logging.getLogger(__name__)

_project_root = Path(__file__).resolve().parent.parent
_queue_dir = _project_root / "queue"
_queue_dir.mkdir(parents=True, exist_ok=True)

_scheduler: BackgroundScheduler | None = None


def _publish_to_social(text: str, image_path: str, day_name: str, platform: str) -> None:
    """
    Job-Funktion: wird vom Scheduler zur geplanten Zeit aufgerufen.
    Muss auf Modulebene sein, damit APScheduler sie beim App-Neustart
    über ihren func_ref wiederherstellen kann.
    """
    logger.info("Poste %s-Post für %s …", platform, day_name)
    try:
        if platform == "bluesky":
            uri = post_to_bluesky(text, image_path, alt_text=f"Tagesmenü {day_name}")
            logger.info("Bluesky-Post veröffentlicht: %s", uri)
        elif platform == "mastodon":
            url = post_to_mastodon(text, image_path)
            logger.info("Mastodon-Post veröffentlicht: %s", url)
    except Exception:
        logger.exception("Fehler beim Posten auf %s für %s", platform, day_name)


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(
            jobstores={
                "default": SQLAlchemyJobStore(
                    url=f"sqlite:///{_queue_dir / 'scheduler.sqlite'}"
                )
            },
            timezone="Europe/Berlin",
            job_defaults={"coalesce": True, "max_instances": 1},
        )
        _scheduler.start()
    return _scheduler


def schedule_post(
    day_name: str,
    text: str,
    image_path: str,
    post_datetime: datetime,
) -> list[str]:
    """
    Plant je einen Job für Bluesky und Mastodon.
    Gibt die Job-IDs zurück.
    """
    scheduler = get_scheduler()
    job_ids = []
    for platform in ("bluesky", "mastodon"):
        job = scheduler.add_job(
            _publish_to_social,
            "date",
            run_date=post_datetime,
            args=[text, image_path, day_name, platform],
            id=f"{day_name}_{platform}_{post_datetime.isoformat()}",
            misfire_grace_time=3600,
            replace_existing=True,
        )
        job_ids.append(job.id)
    return job_ids


def list_scheduled_posts() -> list[dict]:
    """Gibt alle geplanten Jobs zurück (id + nächste Ausführungszeit)."""
    scheduler = get_scheduler()
    return [
        {"id": job.id, "next_run": job.next_run_time}
        for job in scheduler.get_jobs()
    ]



def cancel_post(job_id: str) -> bool:
    """
    Entfernt einen geplanten Job. Gibt True zurück, wenn der Job
    existierte und entfernt wurde, sonst False wenn schon gelaufen.
    """
    scheduler = get_scheduler()
    try:
        scheduler.remove_job(job_id)
        return True
    except JobLookupError:
        return False
