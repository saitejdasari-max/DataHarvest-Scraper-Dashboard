from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.core.logging import app_logger

scheduler = BackgroundScheduler(timezone="UTC")


def _run_scheduled_job(job_id: int):
    """Callback executed by APScheduler."""
    from app.database.session import SessionLocal
    from app.services.scraper_service import ScraperService

    db = SessionLocal()
    try:
        service = ScraperService(db)
        job = service.get_job(job_id)
        if not job or not job.is_scheduled:
            return
        app_logger.info(f"[Scheduler] Running scheduled job id={job_id}")
        service.run_job(job_id)

        # Update next_run_at
        if job.schedule_interval_hours:
            from app.database.repository import ScrapeJobRepository
            from app.schemas.schemas import ScrapeJobUpdate
            repo = ScrapeJobRepository(db)
            next_run = datetime.utcnow() + timedelta(hours=job.schedule_interval_hours)
            repo.update(job_id, ScrapeJobUpdate())
            job.next_run_at = next_run
            db.commit()
    except Exception as e:
        app_logger.error(f"[Scheduler] Job {job_id} failed: {e}")
    finally:
        db.close()


def register_job(job_id: int, interval_hours: int):
    job_name = f"scrape_job_{job_id}"
    if scheduler.get_job(job_name):
        scheduler.remove_job(job_name)
    scheduler.add_job(
        _run_scheduled_job,
        trigger=IntervalTrigger(hours=interval_hours),
        args=[job_id],
        id=job_name,
        replace_existing=True,
        name=f"Scrape Job #{job_id}",
    )
    app_logger.info(f"[Scheduler] Registered job {job_id} every {interval_hours}h")


def unregister_job(job_id: int):
    job_name = f"scrape_job_{job_id}"
    if scheduler.get_job(job_name):
        scheduler.remove_job(job_name)
        app_logger.info(f"[Scheduler] Unregistered job {job_id}")


def start_scheduler():
    if settings.SCHEDULER_ENABLED and not scheduler.running:
        scheduler.start()
        app_logger.info("[Scheduler] Started")
        _register_existing_scheduled_jobs()


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        app_logger.info("[Scheduler] Stopped")


def _register_existing_scheduled_jobs():
    """On startup, re-register any persisted scheduled jobs."""
    from app.database.session import SessionLocal
    from app.database.repository import ScrapeJobRepository

    db = SessionLocal()
    try:
        repo = ScrapeJobRepository(db)
        for job in repo.get_scheduled_jobs():
            if job.schedule_interval_hours:
                register_job(job.id, job.schedule_interval_hours)
    finally:
        db.close()
