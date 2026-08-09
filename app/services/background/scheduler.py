import asyncio
import logging
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.database import async_session_factory
from app.models.user import User
from sqlalchemy import select

logger = logging.getLogger(__name__)


class BriefingScheduler:
    """
    Schedules and delivers daily briefings to users at their preferred times.
    Uses APScheduler for cron-based scheduling.
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._user_jobs: Dict[int, str] = {}

    def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Briefing scheduler started")

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Briefing scheduler stopped")

    async def schedule_user_briefing(self, user_id: int, time_str: str):
        """
        Schedule a daily briefing for a specific user.
        time_str format: "HH:MM" (e.g., "08:00")
        """
        try:
            hour, minute = map(int, time_str.split(":"))

            job_id = f"briefing_{user_id}"

            if job_id in self._user_jobs:
                self.scheduler.remove_job(job_id)

            self.scheduler.add_job(
                self._send_briefing_to_user,
                CronTrigger(hour=hour, minute=minute, day_of_week="mon-fri"),
                args=[user_id],
                id=job_id,
                replace_existing=True,
            )

            self._user_jobs[user_id] = job_id
            logger.info(f"Scheduled daily briefing for user {user_id} at {time_str}")

        except Exception as e:
            logger.error(f"Failed to schedule briefing for user {user_id}: {e}")

    async def unschedule_user_briefing(self, user_id: int):
        """Remove scheduled briefing for a user."""
        job_id = f"briefing_{user_id}"
        if job_id in self._user_jobs:
            try:
                self.scheduler.remove_job(job_id)
                del self._user_jobs[user_id]
                logger.info(f"Unscheduled briefing for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to unschedule briefing for user {user_id}: {e}")

    async def _send_briefing_to_user(self, user_id: int):
        """Send briefing to a specific user via Telegram."""
        try:
            from app.services.background.briefing_compiler import BriefingCompiler

            compiler = BriefingCompiler()
            briefing = await compiler.generate_briefing(user_id)

            async with async_session_factory() as db:
                result = await db.execute(
                    select(User).where(User.telegram_id == user_id)
                )
                user = result.scalar_one_or_none()

                if user and user.briefing_enabled and briefing:
                    from app.core.di.container import get_container
                    from app.domain.services import TelegramBotService
                    telegram_bot_service = get_container().resolve(TelegramBotService)
                    await telegram_bot_service.send_message(
                        chat_id=user_id,
                        text=briefing,
                        parse_mode="Markdown",
                    )
                    logger.info(f"Sent scheduled briefing to user {user_id}")

                    from app.models.document import Briefing
                    from datetime import datetime, timezone
                    briefing_record = Briefing(
                        user_id=user.id,
                        date=datetime.now(timezone.utc),
                        content=briefing,
                        sent=True,
                    )
                    db.add(briefing_record)
                    await db.commit()

        except Exception as e:
            logger.error(f"Failed to send briefing to user {user_id}: {e}")

    async def load_all_schedules(self):
        """Load all user briefing schedules from database."""
        try:
            async with async_session_factory() as db:
                result = await db.execute(
                    select(User).where(User.briefing_enabled == True)
                )
                users = result.scalars().all()

                for user in users:
                    if user.briefing_time:
                        await self.schedule_user_briefing(user.telegram_id, user.briefing_time)

                logger.info(f"Loaded {len(users)} briefing schedules")

        except Exception as e:
            logger.error(f"Failed to load briefing schedules: {e}")

    def get_scheduled_jobs(self) -> List[Dict]:
        """Get all scheduled briefing jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            if job.id.startswith("briefing_"):
                user_id = int(job.id.split("_")[1])
                next_run = job.next_run_time
                jobs.append({
                    "user_id": user_id,
                    "next_run": next_run.isoformat() if next_run else None,
                    "job_id": job.id,
                })
        return jobs


scheduler = BriefingScheduler()
