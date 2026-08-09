import yfinance as yf
from app.domain.services import StockService
from typing import Dict, Optional, List
from datetime import datetime
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=4)


class StockServiceImpl(StockService):
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 300
        self._max_cache_size = 500

    def _evict_cache(self):
        if len(self._cache) > self._max_cache_size:
            oldest_keys = sorted(
                self._cache.keys(),
                key=lambda k: self._cache[k]["timestamp"]
            )[:len(self._cache) - self._max_cache_size // 2]
            for key in oldest_keys:
                del self._cache[key]

    async def get_stock_data(self, symbol: str) -> Optional[Dict]:
        cache_key = f"stock_{symbol}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if (datetime.now() - cached["timestamp"]).total_seconds() < self._cache_ttl:
                return cached["data"]

        try:
            loop = asyncio.get_running_loop()
            ticker = await loop.run_in_executor(executor, lambda: yf.Ticker(symbol))
            info = await loop.run_in_executor(executor, lambda: ticker.info)

            if not info or info.get("regularMarketPrice") is None:
                self._cache[cache_key] = {"data": None, "timestamp": datetime.now()}
                return None

            stock_data = {
                "symbol": symbol,
                "name": info.get("longName", info.get("shortName", symbol)),
                "price": info.get("regularMarketPrice", 0),
                "change": info.get("regularMarketChange", 0),
                "change_percent": info.get("regularMarketChangePercent", 0),
                "volume": info.get("regularMarketVolume", 0),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE"),
                "eps": info.get("trailingEps"),
                "dividend_yield": info.get("dividendYield"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh", 0),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow", 0),
                "average_volume": info.get("averageVolume", 0),
                "beta": info.get("beta"),
                "timestamp": datetime.now(),
            }

            self._cache[cache_key] = {"data": stock_data, "timestamp": datetime.now()}
            self._evict_cache()
            return stock_data

        except Exception as e:
            logger.error(f"Failed to fetch stock data for {symbol}: {e}")
            self._cache[cache_key] = {"data": None, "timestamp": datetime.now()}
            return None

    async def get_company_info(self, symbol: str) -> Optional[Dict]:
        cache_key = f"company_{symbol}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if (datetime.now() - cached["timestamp"]).total_seconds() < self._cache_ttl:
                return cached["data"]

        try:
            loop = asyncio.get_running_loop()
            ticker = await loop.run_in_executor(executor, lambda: yf.Ticker(symbol))
            info = await loop.run_in_executor(executor, lambda: ticker.info)

            if not info:
                self._cache[cache_key] = {"data": None, "timestamp": datetime.now()}
                return None

            company_info = {
                "symbol": symbol,
                "name": info.get("longName", info.get("shortName", symbol)),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "description": info.get("longBusinessSummary", "N/A")[:500],
                "employees": info.get("fullTimeEmployees"),
                "headquarters": f"{info.get('city', '')}, {info.get('state', '')}, {info.get('country', '')}",
                "website": info.get("website"),
                "revenue": info.get("totalRevenue"),
                "net_income": info.get("netIncomeToCommon"),
                "total_assets": info.get("totalAssets"),
                "total_debt": info.get("totalDebt"),
                "current_ratio": info.get("currentRatio"),
                "debt_to_equity": info.get("debtToEquity"),
                "return_on_equity": info.get("returnOnEquity"),
                "profit_margin": info.get("profitMargins"),
                "revenue_growth_yoy": info.get("revenueGrowth"),
                "earnings_growth_yoy": info.get("earningsGrowth"),
                "timestamp": datetime.now(),
            }

            self._cache[cache_key] = {"data": company_info, "timestamp": datetime.now()}
            return company_info

        except Exception as e:
            logger.error(f"Failed to fetch company info for {symbol}: {e}")
            return None

    async def get_earnings_data(self, symbol: str) -> Optional[Dict]:
        try:
            loop = asyncio.get_running_loop()
            ticker = await loop.run_in_executor(executor, lambda: yf.Ticker(symbol))

            earnings_dates = await loop.run_in_executor(executor, lambda: ticker.earnings_dates)
            earnings = await loop.run_in_executor(executor, lambda: ticker.earnings)

            if earnings_dates is None or earnings_dates.empty:
                return None

            latest = earnings_dates.iloc[0] if len(earnings_dates) > 0 else None
            if latest is None:
                return None

            eps_actual = latest.get("Reported EPS", None)
            eps_estimate = latest.get("EPS Estimate", None)
            surprise = None
            if eps_actual is not None and eps_estimate is not None and eps_estimate != 0:
                surprise = ((eps_actual - eps_estimate) / abs(eps_estimate)) * 100

            earnings_data = {
                "symbol": symbol,
                "report_date": str(earnings_dates.index[0]) if len(earnings_dates) > 0 else "N/A",
                "eps_estimate": float(eps_estimate) if eps_estimate else None,
                "eps_actual": float(eps_actual) if eps_actual else None,
                "surprise_percent": round(surprise, 2) if surprise else None,
                "historical": earnings.to_dict() if earnings is not None else {},
            }

            return earnings_data

        except Exception as e:
            logger.error(f"Failed to fetch earnings data for {symbol}: {e}")
            return None

    async def get_historical_data(self, symbol: str, period: str = "1mo") -> Optional[List[Dict]]:
        try:
            loop = asyncio.get_running_loop()
            ticker = await loop.run_in_executor(executor, lambda: yf.Ticker(symbol))
            hist = await loop.run_in_executor(executor, lambda: ticker.history(period=period))

            if hist.empty:
                return None

            data = []
            for date, row in hist.iterrows():
                data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": round(row["Open"], 2),
                    "high": round(row["High"], 2),
                    "low": round(row["Low"], 2),
                    "close": round(row["Close"], 2),
                    "volume": int(row["Volume"]),
                })
            return data

        except Exception as e:
            logger.error(f"Failed to fetch historical data for {symbol}: {e}")
            return None

    async def get_sector_performance(self) -> Optional[Dict]:
        sectors = [
            "XLK", "XLF", "XLV", "XLE", "XLY", "XLP", "XLI", "XLU", "XLRE", "XLB", "XLC"
        ]
        sector_names = {
            "XLK": "Technology", "XLF": "Financials", "XLV": "Healthcare",
            "XLE": "Energy", "XLY": "Consumer Disc.", "XLP": "Consumer Staples",
            "XLI": "Industrials", "XLU": "Utilities", "XLRE": "Real Estate",
            "XLB": "Materials", "XLC": "Communication"
        }
        performance = {}
        for sector_symbol in sectors:
            data = await self.get_stock_data(sector_symbol)
            if data:
                performance[sector_names[sector_symbol]] = {
                    "change": data["change"],
                    "change_percent": data["change_percent"],
                }
        return performance