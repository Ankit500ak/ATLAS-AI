import logging
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from app.config import settings
from app.database import init_db, close_db
from app.core.di.container import configure_container, get_container
from app.core.rate_limiter import RateLimitMiddleware
from app.domain.services import TelegramBotService, CacheService

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    import os
    os.makedirs("data/cache", exist_ok=True)
    os.makedirs("data/documents", exist_ok=True)

    logger.info("Starting Atlas AI Financial Assistant...")

    configure_container()
    logger.info("DI container configured")

    await init_db()
    logger.info("Database initialized")

    container = get_container()
    from app.services.background.runner import BackgroundTaskRunner
    background_runner = BackgroundTaskRunner(container)
    await background_runner.start()
    app.state.background_runner = background_runner
    logger.info("Background tasks started")

    telegram_bot_service = container.resolve(TelegramBotService)
    if settings.telegram_bot_token:
        bot_app = telegram_bot_service.build_app()
        await bot_app.initialize()
        await bot_app.start()
        if settings.telegram_webhook_url:
            await bot_app.bot.set_webhook(url=f"{settings.telegram_webhook_url}/webhook/telegram")
            logger.info(f"Webhook set to {settings.telegram_webhook_url}")
        else:
            await bot_app.updater.start_polling(drop_pending_updates=True)
            logger.info("Bot started with polling")
        app.state.telegram_bot_app = bot_app
    else:
        logger.warning("No Telegram bot token configured")

    yield

    logger.info("Shutting down...")
    await background_runner.stop()
    if hasattr(app.state, 'telegram_bot_app') and app.state.telegram_bot_app:
        await app.state.telegram_bot_app.stop()
    await close_db()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Atlas AI Financial Assistant",
    description="AI-powered Financial Assistant for Telegram",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(RateLimitMiddleware)

from app.api.v1.router import router as api_router
app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "name": "Atlas AI Financial Assistant",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check(request: Request):
    background_runner = request.app.state.background_runner
    cache_service = get_container().resolve(CacheService)
    return {
        "status": "healthy",
        "background_tasks": background_runner.get_status(),
        "cache": cache_service.get_stats(),
    }


@app.get("/api/v1/status")
async def api_status(request: Request):
    background_runner = request.app.state.background_runner
    from app.services.background.scheduler import scheduler
    return {
        "status": "operational",
        "background_tasks": background_runner.get_status(),
        "scheduled_briefings": len(scheduler.get_scheduled_jobs()),
    }


@app.post("/webhook/telegram")
async def telegram_webhook(update: dict, request: Request):
    from telegram import Update
    import hmac

    if settings.telegram_webhook_secret:
        secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not hmac.compare_digest(secret_token, settings.telegram_webhook_secret):
            logger.warning("Invalid webhook secret token")
            return {"status": "error", "message": "Unauthorized"}

    try:
        telegram_bot_service = get_container().resolve(TelegramBotService)
        result = await telegram_bot_service.process_update(update)
        return result
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}