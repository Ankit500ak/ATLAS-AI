import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


class TestIntentClassifier:
    """Tests for intent classification system."""

    def test_classify_stock_price(self):
        from app.services.ai.intent_classifier import IntentClassifier

        classifier = IntentClassifier()
        result = classifier.classify("What is Apple's stock price?")
        assert result["intent"] == "query_stock_price"
        assert result["confidence"] > 0.3

    def test_classify_research(self):
        from app.services.ai.intent_classifier import IntentClassifier

        classifier = IntentClassifier()
        result = classifier.classify("Research Microsoft")
        assert result["intent"] == "research_company"
        assert result["confidence"] > 0.3

    def test_classify_compare(self):
        from app.services.ai.intent_classifier import IntentClassifier

        classifier = IntentClassifier()
        result = classifier.classify("Compare Apple and Google")
        assert result["intent"] == "compare_companies"
        assert result["confidence"] > 0.3

    def test_classify_news(self):
        from app.services.ai.intent_classifier import IntentClassifier

        classifier = IntentClassifier()
        result = classifier.classify("What's happening in the market today?")
        assert result["intent"] == "market_news"
        assert result["confidence"] > 0.3

    def test_classify_alert(self):
        from app.services.ai.intent_classifier import IntentClassifier

        classifier = IntentClassifier()
        result = classifier.classify("Alert me when Apple hits $200")
        assert result["intent"] == "set_alert"
        assert result["confidence"] > 0.3

    def test_classify_general(self):
        from app.services.ai.intent_classifier import IntentClassifier

        classifier = IntentClassifier()
        result = classifier.classify("Hello")
        assert result["intent"] == "general_question"


class TestModelRouter:
    """Tests for model routing system."""

    def test_route_simple_task(self):
        from app.services.ai.model_router import ModelRouter

        router = ModelRouter()
        result = router.route("query_stock_price")
        assert result["model_name"] == "mimo-v2.5-free"

    def test_route_complex_task(self):
        from app.services.ai.model_router import ModelRouter

        router = ModelRouter()
        result = router.route("earnings_analysis")
        assert result["model_name"] == "mimo-v2.5-free"


class TestFormatters:
    """Tests for utility formatters."""

    def test_format_currency(self):
        from app.utils.formatters import format_currency

        assert format_currency(1500000000000) == "$1.50T"
        assert format_currency(2500000000) == "$2.50B"
        assert format_currency(1500000) == "$1.50M"
        assert format_currency(1500) == "$1.50K"
        assert format_currency(99.99) == "$99.99"

    def test_format_percentage(self):
        from app.utils.formatters import format_percentage

        assert format_percentage(5.25) == "+5.25%"
        assert format_percentage(-3.14) == "-3.14%"
        assert format_percentage(0) == "+0.00%"

    def test_get_emoji(self):
        from app.utils.formatters import get_emoji

        assert get_emoji(1.0) == "🟢"
        assert get_emoji(-1.0) == "🔴"
        assert get_emoji(0) == "⚪"


class TestValidators:
    """Tests for input validators."""

    def test_validate_stock_symbol(self):
        from app.utils.validators import validate_stock_symbol

        assert validate_stock_symbol("AAPL") is True
        assert validate_stock_symbol("MSFT") is True
        assert validate_stock_symbol("A") is True
        assert validate_stock_symbol("TOOLONG") is False
        assert validate_stock_symbol("lower") is False

    def test_validate_time(self):
        from app.utils.validators import validate_time

        assert validate_time("08:00") is True
        assert validate_time("23:59") is True
        assert validate_time("25:00") is False
        assert validate_time("abc") is False


class TestWatchlistManager:
    """Tests for watchlist management."""

    @pytest.mark.asyncio
    async def test_parse_add_command(self):
        from app.services.personalization.watchlist_manager import WatchlistManager

        manager = WatchlistManager()
        result = await manager.parse_watchlist_command("Add AAPL and MSFT to my watchlist")
        assert result["action"] == "add"
        assert "AAPL" in result["tickers"]
        assert "MSFT" in result["tickers"]

    @pytest.mark.asyncio
    async def test_parse_remove_command(self):
        from app.services.personalization.watchlist_manager import WatchlistManager

        manager = WatchlistManager()
        result = await manager.parse_watchlist_command("Remove TSLA from my watchlist")
        assert result["action"] == "remove"
        assert "TSLA" in result["tickers"]

    @pytest.mark.asyncio
    async def test_parse_list_command(self):
        from app.services.personalization.watchlist_manager import WatchlistManager

        manager = WatchlistManager()
        result = await manager.parse_watchlist_command("Show me my stocks")
        assert result["action"] == "list"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
