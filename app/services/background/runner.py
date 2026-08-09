import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from app.services.background.alert_monitor import AlertMonitor
from app.services.background.news_aggregator import NewsAggregator
from app.services.background.scheduler import scheduler
from app.core.di.container import ServiceContainer
from app.domain.services import (
    MarketService,
    StockService,
    TelegramBotService,
)

logger = logging.getLogger(__name__)


class BackgroundTaskRunner:
    """
    Runs background tasks for:
    - Price alert monitoring
    - News aggregation
    - Market status updates
    - User profile updates
    - Watchlist monitoring
    - Earnings reminders
    - Evening summaries
    """

    def __init__(self, container: ServiceContainer):
        self._container = container
        self.alert_monitor = AlertMonitor(container)
        self.news_aggregator = NewsAggregator(container)
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._watchlist_alert_cooldown: Dict[str, datetime] = {}

        self.market_service = container.resolve(MarketService)
        self.stock_service = container.resolve(StockService)

    async def start(self):
        """Start all background tasks."""
        if self._running:
            return

        self._running = True
        logger.info("Starting background task runner")

        scheduler.start()
        await scheduler.load_all_schedules()

        self._tasks.append(asyncio.create_task(self._alert_monitor_loop()))
        self._tasks.append(asyncio.create_task(self._news_aggregation_loop()))
        self._tasks.append(asyncio.create_task(self._market_status_loop()))
        self._tasks.append(asyncio.create_task(self._user_profile_update_loop()))
        self._tasks.append(asyncio.create_task(self._watchlist_monitor_loop()))
        self._tasks.append(asyncio.create_task(self._earnings_reminder_loop()))
        self._tasks.append(asyncio.create_task(self._evening_summary_loop()))

        logger.info("Background task runner started with 7 tasks")

    async def stop(self):
        """Stop all background tasks."""
        self._running = False
        scheduler.stop()

        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("Background task runner stopped")

    async def _alert_monitor_loop(self):
        """Monitor price alerts every minute during market hours."""
        while self._running:
            try:
                market_status = await self.market_service.get_market_status()

                if market_status["is_open"]:
                    triggered = await self.alert_monitor.check_alerts()
                    for alert_data in triggered:
                        try:
                            await self.alert_monitor.send_alert_notification(alert_data)
                            logger.info(f"Alert triggered: {alert_data['symbol']} for user {alert_data['user_id']}")
                        except Exception as e:
                            logger.error(f"Failed to send alert notification: {e}")

                await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Alert monitor error: {e}")
                await asyncio.sleep(60)

    async def _news_aggregation_loop(self):
        """Aggregate news every 15 minutes."""
        while self._running:
            try:
                await self.news_aggregator.aggregate_news()
                await asyncio.sleep(900)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"News aggregation error: {e}")
                await asyncio.sleep(900)

    async def _market_status_loop(self):
        """Update market status every 5 minutes."""
        while self._running:
            try:
                status = await self.market_service.get_market_status()
                logger.debug(f"Market status: {status['status']}")
                await asyncio.sleep(300)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Market status error: {e}")
                await asyncio.sleep(300)

    async def _user_profile_update_loop(self):
        """Generate conversation summaries for active users every hour."""
        while self._running:
            try:
                from app.database import async_session_factory
                from app.models.user import User
                from app.models.conversation import Conversation, Message
                from sqlalchemy import select, func
                from app.domain.services import AIService

                ai_service = self._container.resolve(AIService)

                async with async_session_factory() as db:
                    result = await db.execute(
                        select(User).where(User.onboarding_completed == True)
                    )
                    users = result.scalars().all()

                    for user in users[:20]:
                        try:
                            conv_result = await db.execute(
                                select(Conversation)
                                .where(Conversation.user_id == user.id)
                                .where(Conversation.summary.is_(None))
                                .order_by(Conversation.updated_at.desc())
                                .limit(3)
                            )
                            unsummarized = conv_result.scalars().all()

                            for conv in unsummarized:
                                msg_result = await db.execute(
                                    select(Message)
                                    .where(Message.conversation_id == conv.id)
                                    .order_by(Message.created_at.asc())
                                )
                                messages = msg_result.scalars().all()
                                if len(messages) >= 4:
                                    text = "\n".join([f"{m.role}: {m.content[:150]}" for m in messages[-8:]])
                                    res = await ai_service.generate(
                                        prompt=f"Summarize in 1 sentence:\n{text}",
                                        system_message="Be concise.",
                                        temperature=0.2,
                                        max_tokens=100,
                                    )
                                    if res["success"] and res["content"]:
                                        conv.summary = res["content"].strip()
                                        conv.title = messages[0].content[:80] if messages else None

                            await db.commit()
                        except Exception as e:
                            logger.debug(f"Profile update for user {user.telegram_id}: {e}")

                    logger.debug(f"Processed profiles for {len(users)} users")

                await asyncio.sleep(3600)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"User profile update error: {e}")
                await asyncio.sleep(3600)

    async def _watchlist_monitor_loop(self):
        """Monitor watchlist stocks for significant price movements."""
        while self._running:
            try:
                from app.database import async_session_factory
                from app.models.user import User
                from sqlalchemy import select

                telegram_bot_service = self._container.resolve(TelegramBotService)

                async with async_session_factory() as db:
                    result = await db.execute(
                        select(User).where(User.onboarding_completed == True)
                    )
                    users = result.scalars().all()

                    for user in users[:20]:
                        try:
                            watchlist = user.watchlist or []
                            if not watchlist:
                                continue

                            for symbol in watchlist[:5]:
                                quote = await self.stock_service.get_stock_data(symbol)
                                if quote and quote.get("change_percent") is not None:
                                    change = quote["change_percent"]
                                    if abs(change) >= 5.0:
                                        cooldown_key = f"{user.telegram_id}:{symbol}"
                                        now = datetime.now()
                                        last_alert = self._watchlist_alert_cooldown.get(cooldown_key)
                                        if last_alert and (now - last_alert).total_seconds() < 3600:
                                            continue

                                        if telegram_bot_service:
                                            direction = "up" if change > 0 else "down"
                                            emoji = "📈" if change > 0 else "📉"
                                            await telegram_bot_service.send_message(
                                                chat_id=user.telegram_id,
                                                text=(
                                                    f"{emoji} *{symbol}* moved *{abs(change):.1f}%* {direction}!\n\n"
                                                    f"Current price: *${quote.get('price', 'N/A')}*"
                                                ),
                                            )
                                            self._watchlist_alert_cooldown[cooldown_key] = now
                        except Exception as e:
                            logger.debug(f"Watchlist monitor for {user.telegram_id}: {e}")

                await asyncio.sleep(900)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Watchlist monitor error: {e}")
                await asyncio.sleep(900)

    async def _earnings_reminder_loop(self):
        """Remind users about upcoming earnings for watchlist stocks."""
        while self._running:
            try:
                from app.database import async_session_factory
                from app.models.user import User
                from sqlalchemy import select
                from app.domain.services import EarningsCalendarService

                earnings_calendar = self._container.resolve(EarningsCalendarService)
                telegram_bot_service = self._container.resolve(TelegramBotService)

                async with async_session_factory() as db:
                    result = await db.execute(
                        select(User).where(User.onboarding_completed == True)
                    )
                    users = result.scalars().all()

                    for user in users[:20]:
                        try:
                            watchlist = user.watchlist or []
                            if not watchlist:
                                continue

                            calendar = await earnings_calendar.get_upcoming_earnings(watchlist[:10])
                            if not calendar:
                                continue

                            for earning in calendar[:3]:
                                if telegram_bot_service:
                                    await telegram_bot_service.send_message(
                                        chat_id=user.telegram_id,
                                        text=(
                                            f"📅 *Earnings Reminder*\n\n"
                                            f"*{earning.get('symbol', 'N/A')}* reports "
                                            f"*{earning.get('date', 'N/A')}*\n\n"
                                            f"Want me to analyze their previous earnings before they report?"
                                        ),
                                    )
                        except Exception as e:
                            logger.debug(f"Earnings reminder for {user.telegram_id}: {e}")

                await asyncio.sleep(86400)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Earnings reminder error: {e}")
                await asyncio.sleep(86400)

    async def _evening_summary_loop(self):
        """Send evening summary at market close (4 PM ET) on weekdays."""
        while self._running:
            try:
                from zoneinfo import ZoneInfo

                now = datetime.now(ZoneInfo("America/New_York"))
                market_close = now.replace(hour=16, minute=5, second=0, microsecond=0)

                if now < market_close:
                    wait_seconds = (market_close - now).total_seconds()
                    await asyncio.sleep(wait_seconds)
                else:
                    await asyncio.sleep(86400)
                    continue

                now = datetime.now(ZoneInfo("America/New_York"))
                if now.weekday() >= 5:
                    await asyncio.sleep(86400)
                    continue

                from app.database import async_session_factory
                from app.models.user import User
                from sqlalchemy import select
                from app.services.background.briefing_compiler import BriefingCompiler

                compiler = BriefingCompiler(self._container)
                telegram_bot_service = self._container.resolve(TelegramBotService)

                async with async_session_factory() as db:
                    result = await db.execute(
                        select(User).where(User.onboarding_completed == True, User.briefing_enabled == True)
                    )
                    users = result.scalars().all()

                for user in users[:20]:
                    try:
                        summary = await compiler.generate_briefing(user.telegram_id, summary_type="evening")
                        if summary and telegram_bot_service:
                            await telegram_bot_service.send_message(
                                chat_id=user.telegram_id,
                                text=f"📊 *Evening Market Summary*\n\n{summary}",
                            )
                    except Exception as e:
                        logger.debug(f"Evening summary for {user.telegram_id}: {e}")

                await asyncio.sleep(86400)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Evening summary error: {e}")
                await asyncio.sleep(86400)

    def get_status(self) -> Dict:
        """Get background task runner status."""
        return {
            "running": self._running,
            "tasks": len(self._tasks),
            "scheduled_jobs": len(scheduler.get_scheduled_jobs()),
        }