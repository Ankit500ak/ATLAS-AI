from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.config import settings


class AIService(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_message: str = "",
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        system_message: str = "",
        model: str = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def summarize(self, text: str, max_length: int = 200) -> str:
        pass

    @abstractmethod
    async def analyze_sentiment(self, text: str) -> float:
        pass

    @abstractmethod
    def count_tokens(self, text: str, model: str = None) -> int:
        pass


class StockService(ABC):
    @abstractmethod
    async def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_earnings_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_historical_data(self, symbol: str, period: str = "1mo") -> Optional[List[Dict]]:
        pass

    @abstractmethod
    async def get_sector_performance(self) -> Optional[Dict]:
        pass


class NewsService(ABC):
    @abstractmethod
    async def get_market_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_company_news(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_trending_news(self) -> List[Dict[str, Any]]:
        pass


class MarketService(ABC):
    @abstractmethod
    async def get_market_status(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_market_indices(self) -> Dict[str, Any]:
        pass


class SECFilingService(ABC):
    @abstractmethod
    async def search_filings(self, ticker: str, limit: int = 10) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_filing_content(self, accession_number: str) -> Optional[str]:
        pass


class EarningsCalendarService(ABC):
    @abstractmethod
    async def get_upcoming_earnings(self, symbols: Optional[List[str]] = None, limit: int = 50) -> List[Dict[str, Any]]:
        pass


class CacheService(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    async def clear_pattern(self, pattern: str) -> int:
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        pass


class TelegramBotService(ABC):
    @abstractmethod
    def build_app(self):
        pass

    @abstractmethod
    async def send_message(self, chat_id: int, text: str, parse_mode: str = "Markdown") -> bool:
        pass

    @abstractmethod
    async def process_update(self, update: Dict) -> Dict[str, Any]:
        pass