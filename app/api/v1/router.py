from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.security import verify_api_key
from app.core.di.container import get_container
from app.domain.services import (
    StockService,
    NewsService,
    MarketService,
    SECFilingService,
    EarningsCalendarService,
    CacheService,
)
from app.domain.repositories import UserRepository, AlertRepository

router = APIRouter(prefix="/api/v1", tags=["api"])


def get_background_runner(request: Request):
    return request.app.state.background_runner


def get_telegram_bot_app(request: Request):
    return getattr(request.app.state, 'telegram_bot_app', None)


@router.get("/status")
async def status(request: Request, _key: str = Depends(verify_api_key)):
    background_runner = get_background_runner(request)
    from app.services.background.scheduler import scheduler
    cache_service = get_container().resolve(CacheService)

    return {
        "status": "operational",
        "version": "1.0.0",
        "background_tasks": background_runner.get_status(),
        "scheduled_briefings": len(scheduler.get_scheduled_jobs()),
        "cache": cache_service.get_stats(),
    }


@router.get("/health")
async def health(request: Request, _key: str = Depends(verify_api_key)):
    background_runner = get_background_runner(request)
    return {
        "status": "healthy",
        "tasks_running": background_runner.get_status()["running"],
    }


@router.get("/users/{telegram_id}")
async def get_user(telegram_id: int, _key: str = Depends(verify_api_key)):
    user_repo = get_container().resolve(UserRepository)
    user = await user_repo.get_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "role": user.role,
        "watchlist": user.watchlist,
        "onboarding_completed": user.onboarding_completed,
        "briefing_enabled": user.briefing_enabled,
        "briefing_time": user.briefing_time,
    }


@router.get("/users/{telegram_id}/watchlist")
async def get_watchlist(telegram_id: int, _key: str = Depends(verify_api_key)):
    user_repo = get_container().resolve(UserRepository)
    user = await user_repo.get_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"watchlist": user.watchlist or []}


@router.get("/users/{telegram_id}/alerts")
async def get_alerts(telegram_id: int, _key: str = Depends(verify_api_key)):
    user_repo = get_container().resolve(UserRepository)
    alert_repo = get_container().resolve(AlertRepository)

    user = await user_repo.get_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    alerts = await alert_repo.get_active_by_user(user.id)

    return {
        "alerts": [
            {
                "id": a.id,
                "symbol": a.symbol,
                "alert_type": a.alert_type,
                "target_value": a.target_value,
                "triggered": a.triggered,
            }
            for a in alerts
        ]
    }


@router.get("/market/status")
async def market_status(_key: str = Depends(verify_api_key)):
    service = get_container().resolve(MarketService)
    return await service.get_market_status()


@router.get("/market/indices")
async def market_indices(_key: str = Depends(verify_api_key)):
    service = get_container().resolve(MarketService)
    return await service.get_market_indices()


@router.get("/stock/{symbol}")
async def get_stock(symbol: str, _key: str = Depends(verify_api_key)):
    service = get_container().resolve(StockService)
    data = await service.get_stock_data(symbol.upper())
    if not data:
        raise HTTPException(status_code=404, detail=f"Stock data not found for {symbol}")
    return data


@router.get("/stock/{symbol}/info")
async def get_stock_info(symbol: str, _key: str = Depends(verify_api_key)):
    service = get_container().resolve(StockService)
    data = await service.get_company_info(symbol.upper())
    if not data:
        raise HTTPException(status_code=404, detail=f"Company info not found for {symbol}")
    return data


@router.get("/news")
async def get_news(limit: int = 10, _key: str = Depends(verify_api_key)):
    service = get_container().resolve(NewsService)
    return await service.get_market_news(limit=limit)


@router.get("/earnings/upcoming")
async def upcoming_earnings(_key: str = Depends(verify_api_key)):
    service = get_container().resolve(EarningsCalendarService)
    return await service.get_upcoming_earnings()


@router.get("/sec/{symbol}")
async def sec_filings(symbol: str, limit: int = 5, _key: str = Depends(verify_api_key)):
    service = get_container().resolve(SECFilingService)
    filings = await service.search_filings(ticker=symbol.upper(), limit=limit)
    return {"filings": filings or []}


@router.get("/auth/google")
async def google_auth(telegram_id: int, _key: str = Depends(verify_api_key)):
    from app.services.integrations.google_service import google_service
    auth_url = google_service.get_auth_url(telegram_id)
    if not auth_url:
        raise HTTPException(status_code=500, detail="Failed to generate auth URL")
    return {"auth_url": auth_url}


@router.get("/auth/google/callback")
async def google_callback(code: str, state: int, _key: str = Depends(verify_api_key)):
    from app.services.integrations.google_service import google_service
    success = await google_service.handle_callback(code, state)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to authenticate with Google")
    return {"status": "connected", "user_id": state}


@router.get("/users/{telegram_id}/gmail")
async def get_gmail(telegram_id: int, query: str = "", limit: int = 10, _key: str = Depends(verify_api_key)):
    from app.services.integrations.google_service import google_service
    messages = await google_service.get_gmail_messages(telegram_id, query, limit)
    return {"messages": messages}


@router.get("/users/{telegram_id}/calendar")
async def get_calendar(telegram_id: int, days_ahead: int = 7, _key: str = Depends(verify_api_key)):
    from app.services.integrations.google_service import google_service
    events = await google_service.get_calendar_events(telegram_id, days_ahead)
    return {"events": events}


@router.get("/users/{telegram_id}/drive")
async def get_drive(telegram_id: int, query: str = "", limit: int = 10, _key: str = Depends(verify_api_key)):
    from app.services.integrations.google_service import google_service
    files = await google_service.get_drive_files(telegram_id, query, limit)
    return {"files": files}


@router.get("/users/{telegram_id}/sheets/{spreadsheet_id}")
async def get_sheets(telegram_id: int, spreadsheet_id: str, range_name: str = "Sheet1", _key: str = Depends(verify_api_key)):
    from app.services.integrations.google_service import google_service
    data = await google_service.get_sheets_data(telegram_id, spreadsheet_id, range_name)
    return {"data": data}