import asyncio
from typing import List, Callable, Optional
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ..utils.logger import get_logger
from ..utils.config import get_config, get_settings


logger = get_logger("scheduler")


class NewsScheduler:
    """Manages scheduled news fetching and sending tasks."""

    def __init__(self):
        settings = get_settings()
        self.user_timezone = settings.user_timezone
        self.scheduler = AsyncIOScheduler(timezone=self.user_timezone)
        self.config = get_config()

    def add_daily_job(
        self,
        func: Callable,
        hour: int,
        minute: int = 0,
        job_id: str = None,
        **kwargs
    ):
        """Add a daily job at specified time."""
        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            timezone=self.user_timezone
        )

        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id or f"job_{hour}_{minute}",
            replace_existing=True,
            kwargs=kwargs
        )

        logger.info(f"Added daily job at {hour:02d}:{minute:02d}")

    def add_news_jobs(self, process_func: Callable):
        """Add news processing jobs based on configuration."""
        frequency = self.config["scheduler"]["frequency"]
        times = self.config["scheduler"]["delivery_times"][:frequency]

        for time_str in times:
            hour, minute = map(int, time_str.split(":"))
            self.add_daily_job(
                func=process_func,
                hour=hour,
                minute=minute,
                job_id=f"news_{time_str.replace(':', '')}"
            )

    def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")

    def get_jobs(self) -> list:
        """Get list of scheduled jobs."""
        return self.scheduler.get_jobs()

    def run_now(self, job_id: str):
        """Manually trigger a job."""
        job = self.scheduler.get_job(job_id)
        if job:
            job.modify(next_run_time=datetime.now())
            logger.info(f"Triggered job: {job_id}")


async def run_scheduled_task(func: Callable, *args, **kwargs):
    """Wrapper to run async functions as scheduled tasks."""
    try:
        if asyncio.iscoroutinefunction(func):
            await func(*args, **kwargs)
        else:
            func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error in scheduled task: {e}")
