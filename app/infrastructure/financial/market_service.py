from app.domain.services import MarketService
from typing import Dict, Any, List
import logging
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=5)


class MarketServiceImpl(MarketService):
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 300

    async def get_market_status(self) -> Dict[str, Any]:
        cache_key = "market_status"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if (datetime.now() - cached["timestamp"]).total_seconds() < self._cache_ttl:
                return cached["data"]

        try:
            import yfinance as yf

            spy = await asyncio.get_event_loop().run_in_executor(_executor, lambda: yf.Ticker("SPY"))
            spy_info = await asyncio.get_event_loop().run_in_executor(_executor, lambda: spy.info)

            et_time = datetime.now(ZoneInfo("America/New_York"))
            market_open = et_time.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = et_time.replace(hour=16, minute=0, second=0, microsecond=0)
            is_weekday = et_time.weekday() < 5
            is_open = is_weekday and market_open <= et_time <= market_close

            status = "open" if is_open else "closed"
            if not is_weekday:
                status = "weekend"

            result = {
                "status": status,
                "is_open": is_open,
                "spy_price": spy_info.get("regularMarketPrice", 0),
                "spy_change": spy_info.get("regularMarketChange", 0),
                "spy_change_percent": spy_info.get("regularMarketChangePercent", 0),
                "timestamp": datetime.now(),
                "timezone": "America/New_York",
            }

            self._cache[cache_key] = {"data": result, "timestamp": datetime.now()}
            return result

        except Exception as e:
            logger.error(f"Failed to get market status: {e}")
            return {
                "status": "unknown",
                "is_open": False,
                "spy_price": 0,
                "spy_change": 0,
                "spy_change_percent": 0,
                "timestamp": datetime.now(),
                "timezone": "America/New_York",
            }

    async def get_market_indices(self) -> Dict[str, Any]:
        indices = ["SPY", "DIA", "QQQ", "IWM", "VTI"]
        index_names = {
            "SPY": "S&P 500",
            "DIA": "Dow Jones",
            "QQQ": "NASDAQ 100",
            "IWM": "Russell 2000",
            "VTI": "Total Market",
        }

        try:
            import yfinance as yf

            results = {}
            for symbol in indices:
                ticker = await asyncio.get_event_loop().run_in_executor(_executor, lambda s=symbol: yf.Ticker(s))
                info = await asyncio.get_event_loop().run_in_executor(_executor, lambda t=ticker: t.info)
                if info:
                    results[index_names.get(symbol, symbol)] = {
                        "symbol": symbol,
                        "name": index_names.get(symbol, symbol),
                        "price": info.get("regularMarketPrice", 0),
                        "change": info.get("regularMarketChange", 0),
                        "change_percent": info.get("regularMarketChangePercent", 0),
                    }
            return results
        except Exception as e:
            logger.error(f"Failed to get market indices: {e}")
            return {}