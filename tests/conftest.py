import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    user.telegram_id = 12345
    user.username = "testuser"
    user.first_name = "Test"
    user.last_name = "User"
    user.role = "Investor"
    user.sectors = ["Technology"]
    user.watchlist = ["AAPL", "MSFT"]
    user.onboarding_completed = True
    user.onboarding_step = 5
    user.briefing_time = "08:00"
    user.briefing_enabled = True
    user.interests = {}
    user.usage_patterns = {}
    user.notification_preferences = {}
    return user


@pytest.fixture
def mock_update():
    update = MagicMock()
    update.effective_user.id = 12345
    update.effective_user.first_name = "Test"
    update.effective_user.username = "testuser"
    update.message = AsyncMock()
    update.message.reply_text = AsyncMock()
    update.message.chat.send_action = AsyncMock()
    update.message.text = "test message"
    return update


@pytest.fixture
def mock_context():
    context = MagicMock()
    context.args = []
    return context


@pytest.fixture
def sample_stock_data():
    return {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "price": 178.50,
        "change": 2.30,
        "change_percent": 1.30,
        "volume": 50000000,
        "market_cap": "2.80T",
        "pe_ratio": 28.5,
        "low_52": 124.17,
        "high_52": 199.62,
        "sector": "Technology",
        "industry": "Consumer Electronics",
    }


@pytest.fixture
def sample_news():
    return [
        {"title": "Apple Reports Record Earnings", "source": "Reuters", "url": "https://example.com"},
        {"title": "Tech Stocks Rally", "source": "Bloomberg", "url": "https://example.com"},
    ]


@pytest.fixture
def sample_company_info():
    return {
        "name": "Apple Inc.",
        "symbol": "AAPL",
        "description": "Apple Inc. designs, manufactures, and markets smartphones.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "revenue": "394.3B",
        "net_income": "99.8B",
        "market_cap": "2.80T",
    }
