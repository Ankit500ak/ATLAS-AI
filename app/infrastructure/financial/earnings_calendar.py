from app.domain.services import EarningsCalendarService
from typing import List, Dict, Any, Optional
import logging
import asyncio
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=4)


class EarningsCalendarImpl(EarningsCalendarService):
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 3600

    async def get_upcoming_earnings(self, symbols: Optional[List[str]] = None, limit: int = 50) -> List[Dict[str, Any]]:
        cache_key = f"earnings_{','.join(symbols or ['all'])}_{limit}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if (datetime.now() - cached["timestamp"]).total_seconds() < self._cache_ttl:
                return cached["data"]

        try:
            if symbols:
                earnings = []
                for symbol in symbols[:20]:
                    data = await self._get_symbol_earnings(symbol)
                    if data:
                        earnings.append(data)
                earnings.sort(key=lambda x: x.get("date", ""))
                result = earnings[:limit]
            else:
                major_symbols = [
                    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
                    "JPM", "V", "JNJ", "WMT", "PG", "MA", "UNH", "HD",
                    "DIS", "PYPL", "NFLX", "ADBE", "CRM"
                ]
                earnings = []
                for symbol in major_symbols:
                    data = await self._get_symbol_earnings(symbol)
                    if data:
                        earnings.append(data)
                earnings.sort(key=lambda x: x.get("date", ""))
                result = earnings[:limit]

            self._cache[cache_key] = {"data": result, "timestamp": datetime.now()}
            return result

        except Exception as e:
            logger.error(f"Failed to get upcoming earnings: {e}")
            return []

    async def _get_symbol_earnings(self, symbol: str) -> Optional[Dict[str, Any]]:
        try:
            loop = asyncio.get_running_loop()
            ticker = await loop.run_in_executor(executor, lambda: yf.Ticker(symbol))
            earnings_dates = await loop.run_in_executor(executor, lambda: ticker.earnings_dates)

            if earnings_dates is None or earnings_dates.empty:
                return None

            latest_date = earnings_dates.index[0]
            if isinstance(latest_date, str):
                latest_date = datetime.strptime(latest_date, "%Y-%m-%d")

            if latest_date < datetime.now():
                if len(earnings_dates) > 1:
                    latest_date = earnings_dates.index[1]
                else:
                    return None

            row = earnings_dates.loc[earnings_dates.index[0]]
            eps_estimate = row.get("EPS Estimate")
            eps_actual = row.get("Reported EPS")

            return {
                "symbol": symbol,
                "date": latest_date.strftime("%Y-%m-%d"),
                "time": row.get("Time", "TBD"),
                "eps_estimate": float(eps_estimate) if eps_estimate else None,
                "eps_actual": float(eps_actual) if eps_actual else None,
            }
        except Exception as e:
            logger.debug(f"Failed to get earnings for {symbol}: {e}")
            return None