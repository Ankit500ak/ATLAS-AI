import pytest
from unittest.mock import AsyncMock, MagicMock, patch, AsyncMock
from datetime import datetime


class TestDatabaseModels:
    """Tests for database models."""

    def test_user_model_fields(self):
        from app.models.user import User
        columns = {c.name for c in User.__table__.columns}
        assert "telegram_id" in columns
        assert "username" in columns
        assert "first_name" in columns
        assert "role" in columns
        assert "watchlist" in columns
        assert "onboarding_completed" in columns
        assert "briefing_time" in columns

    def test_conversation_model_fields(self):
        from app.models.conversation import Conversation
        columns = {c.name for c in Conversation.__table__.columns}
        assert "user_id" in columns
        assert "title" in columns
        assert "summary" in columns
        assert "is_active" in columns

    def test_message_model_fields(self):
        from app.models.conversation import Message
        columns = {c.name for c in Message.__table__.columns}
        assert "conversation_id" in columns
        assert "role" in columns
        assert "content" in columns
        assert "intent" in columns

    def test_alert_model_fields(self):
        from app.models.document import Alert
        columns = {c.name for c in Alert.__table__.columns}
        assert "user_id" in columns
        assert "symbol" in columns
        assert "alert_type" in columns
        assert "target_value" in columns
        assert "is_active" in columns
        assert "triggered" in columns

    def test_briefing_model_fields(self):
        from app.models.document import Briefing
        columns = {c.name for c in Briefing.__table__.columns}
        assert "user_id" in columns
        assert "date" in columns
        assert "content" in columns
        assert "sent" in columns

    def test_document_model_fields(self):
        from app.models.document import Document
        columns = {c.name for c in Document.__table__.columns}
        assert "user_id" in columns
        assert "filename" in columns
        assert "file_path" in columns
        assert "status" in columns


class TestPromptTemplates:
    """Tests for prompt templates."""

    def test_system_persona_exists(self):
        from app.services.ai.prompts import PromptTemplates
        assert len(PromptTemplates.SYSTEM_PERSONA) > 0

    def test_onboarding_steps_exist(self):
        from app.services.ai.prompts import PromptTemplates
        assert len(PromptTemplates.ONBOARDING_STEP_1) > 0
        assert len(PromptTemplates.ONBOARDING_STEP_2) > 0
        assert len(PromptTemplates.ONBOARDING_STEP_3) > 0
        assert len(PromptTemplates.ONBOARDING_STEP_4) > 0
        assert len(PromptTemplates.ONBOARDING_STEP_5) > 0

    def test_onboarding_complete_format(self):
        from app.services.ai.prompts import PromptTemplates
        result = PromptTemplates.ONBOARDING_COMPLETE.format(
            role="Investor",
            sectors="Technology",
            watchlist="AAPL, MSFT",
            briefing_time="08:00",
        )
        assert "Investor" in result
        assert "Technology" in result
        assert "AAPL" in result

    def test_response_templates_exist(self):
        from app.services.ai.prompts import PromptTemplates
        assert "query_stock_price" in PromptTemplates.RESPONSE_TEMPLATES
        assert "research_company" in PromptTemplates.RESPONSE_TEMPLATES
        assert "compare_companies" in PromptTemplates.RESPONSE_TEMPLATES
        assert "earnings_analysis" in PromptTemplates.RESPONSE_TEMPLATES
        assert "market_news" in PromptTemplates.RESPONSE_TEMPLATES

    def test_build_context_prompt(self):
        from app.services.ai.prompts import PromptTemplates
        context = {
            "user_profile": {"role": "Investor", "interests": ["Tech"]},
            "financial_context": {"mentioned_companies": ["AAPL"]},
            "compressed_history": "Previous discussion about Apple",
        }
        result = PromptTemplates.build_context_prompt("What's Apple's price?", context)
        assert "Investor" in result
        assert "AAPL" in result
        assert "Apple" in result


class TestIntentClassifierExtended:
    """Extended tests for intent classifier."""

    def test_classify_sec_filing(self):
        from app.services.ai.intent_classifier import IntentClassifier
        classifier = IntentClassifier()
        result = classifier.classify("Analyze Apple's latest SEC filing")
        assert result["intent"] == "sec_filing"
        assert result["confidence"] > 0.3

    def test_classify_earnings(self):
        from app.services.ai.intent_classifier import IntentClassifier
        classifier = IntentClassifier()
        result = classifier.classify("What were Tesla's quarterly earnings?")
        assert result["intent"] == "earnings_analysis"
        assert result["confidence"] > 0.3

    def test_classify_explain(self):
        from app.services.ai.intent_classifier import IntentClassifier
        classifier = IntentClassifier()
        result = classifier.classify("What is P/E ratio?")
        assert result["intent"] == "explain_concept"
        assert result["confidence"] > 0.3

    def test_classify_macro(self):
        from app.services.ai.intent_classifier import IntentClassifier
        classifier = IntentClassifier()
        result = classifier.classify("What is the Fed doing with interest rates?")
        assert result["intent"] == "macro_economic"
        assert result["confidence"] > 0.3

    def test_classify_portfolio(self):
        from app.services.ai.intent_classifier import IntentClassifier
        classifier = IntentClassifier()
        result = classifier.classify("Analyze my portfolio")
        assert result["intent"] == "portfolio_analysis"
        assert result["confidence"] > 0.3

    def test_classify_briefing(self):
        from app.services.ai.intent_classifier import IntentClassifier
        classifier = IntentClassifier()
        result = classifier.classify("Give me my morning briefing")
        assert result["intent"] == "daily_briefing"
        assert result["confidence"] > 0.3

    def test_keyword_scoring(self):
        from app.services.ai.intent_classifier import IntentClassifier
        classifier = IntentClassifier()
        scores = classifier.classify_keyword("What is Apple's stock price?")
        assert "query_stock_price" in scores
        assert scores["query_stock_price"] > 0

    def test_multiple_intents(self):
        from app.services.ai.intent_classifier import IntentClassifier
        classifier = IntentClassifier()
        result = classifier.classify("Compare Apple and Google earnings")
        assert result["intent"] in ["compare_companies", "earnings_analysis"]


class TestFormattersExtended:
    """Extended tests for formatters."""

    def test_format_large_currency(self):
        from app.utils.formatters import format_currency
        result = format_currency(1000000000000)
        assert "T" in result

    def test_format_small_currency(self):
        from app.utils.formatters import format_currency
        result = format_currency(50.25)
        assert "$50.25" in result

    def test_format_percentage_zero(self):
        from app.utils.formatters import format_percentage
        result = format_percentage(0)
        assert "0.00%" in result

    def test_truncate_text(self):
        from app.utils.formatters import truncate
        result = truncate("Hello World", 5)
        assert len(result) <= 8
        assert "..." in result

    def test_format_number(self):
        from app.utils.formatters import format_number
        result = format_number(1500000)
        assert "M" in result


class TestValidatorsExtended:
    """Extended tests for validators."""

    def test_validate_stock_symbol_valid(self):
        from app.utils.validators import validate_stock_symbol
        assert validate_stock_symbol("AAPL") is True
        assert validate_stock_symbol("MSFT") is True
        assert validate_stock_symbol("GOOGL") is True

    def test_validate_stock_symbol_invalid(self):
        from app.utils.validators import validate_stock_symbol
        assert validate_stock_symbol("") is False
        assert validate_stock_symbol("TOOLONG") is False

    def test_validate_email(self):
        from app.utils.validators import validate_email
        assert validate_email("test@example.com") is True
        assert validate_email("invalid") is False

    def test_extract_tickers(self):
        from app.utils.validators import extract_tickers
        result = extract_tickers("Compare AAPL and MSFT")
        assert "AAPL" in result
        assert "MSFT" in result


class TestConfig:
    """Tests for configuration."""

    def test_settings_defaults(self):
        from app.config import Settings
        settings = Settings()
        assert settings.app_env == "development"
        assert settings.log_level == "INFO"
        assert settings.max_conversation_history == 50

    def test_is_allowed_user_no_restriction(self):
        from app.config import Settings
        settings = Settings()
        assert settings.is_allowed_user(12345) is True


class TestCacheService:
    """Tests for cache service."""

    @pytest.mark.asyncio
    async def test_cache_set_get(self):
        from app.services.financial.cache_service import CacheService
        cache = CacheService()
        await cache.set("test_key", {"data": "test"}, ttl=60)
        result = await cache.get("test_key")
        assert result is not None
        assert result["data"] == "test"

    @pytest.mark.asyncio
    async def test_cache_miss(self):
        from app.services.financial.cache_service import CacheService
        cache = CacheService()
        result = await cache.get("nonexistent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_delete(self):
        from app.services.financial.cache_service import CacheService
        cache = CacheService()
        await cache.set("delete_me", {"data": "value"}, ttl=60)
        await cache.delete("delete_me")
        result = await cache.get("delete_me")
        assert result is None

    def test_cache_stats(self):
        from app.services.financial.cache_service import CacheService
        cache = CacheService()
        stats = cache.get_stats()
        assert "memory_entries" in stats
        assert "redis_connected" in stats
