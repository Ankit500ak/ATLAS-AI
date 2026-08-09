from datetime import datetime, time as dt_time, date, timedelta
from typing import Dict, Optional, Set
import logging

logger = logging.getLogger(__name__)


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    first_weekday = first.weekday()
    days_until = (weekday - first_weekday) % 7
    return first + timedelta(days=days_until + 7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> date:
    if month == 12:
        last_day = date(year, 12, 31)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    days_back = (last_day.weekday() - weekday) % 7
    return last_day - timedelta(days=days_back)


def _get_us_market_holidays(year: int) -> Set[date]:
    holidays = set()
    holidays.add(date(year, 1, 1))

    mlk = _nth_weekday(year, 1, 0, 3)
    holidays.add(mlk)

    presidents = _nth_weekday(year, 2, 0, 3)
    holidays.add(presidents)

    jan1 = date(year, 1, 1)
    a = jan1.year % 19
    b, c = divmod(jan1.year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month_easter = (h + l - 7 * m + 114) // 31
    day_easter = ((h + l - 7 * m + 114) % 31) + 1
    easter = date(year, month_easter, day_easter)
    good_friday = easter - timedelta(days=2)
    holidays.add(good_friday)

    memorial = _last_weekday(year, 5, 0)
    holidays.add(memorial)

    juneteenth = date(year, 6, 19)
    holidays.add(juneteenth)

    july4 = date(year, 7, 4)
    if july4.weekday() == 5:
        holidays.add(july4 - timedelta(days=1))
    elif july4.weekday() == 6:
        holidays.add(july4 + timedelta(days=1))
    else:
        holidays.add(july4)

    labor = _nth_weekday(year, 9, 0, 1)
    holidays.add(labor)

    thanksgiving = _nth_weekday(year, 11, 3, 4)
    holidays.add(thanksgiving)

    christmas = date(year, 12, 25)
    if christmas.weekday() == 5:
        holidays.add(christmas - timedelta(days=1))
    elif christmas.weekday() == 6:
        holidays.add(christmas + timedelta(days=1))
    else:
        holidays.add(christmas)

    return holidays


class MarketService:
    """
    Service for market status and market hours information.
    Uses US/Eastern timezone for accurate market hours.
    """

    MARKET_OPEN = dt_time(9, 30)
    MARKET_CLOSE = dt_time(16, 0)
    PRE_MARKET_START = dt_time(4, 0)
    AFTER_HOURS_END = dt_time(20, 0)

    def _get_eastern_time(self):
        """Get current US/Eastern time."""
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/New_York"))

    async def get_market_status(self) -> Dict:
        now = self._get_eastern_time()
        current_time = now.time()
        is_weekday = now.weekday() < 5
        today = now.date()
        holidays = _get_us_market_holidays(now.year)
        is_holiday = today in holidays

        if not is_weekday or is_holiday:
            status = "closed"
            session = "weekend" if not is_weekday else "holiday"
        elif current_time < self.PRE_MARKET_START:
            status = "closed"
            session = "closed"
        elif current_time < self.MARKET_OPEN:
            status = "pre-market"
            session = "pre-market"
        elif current_time <= self.MARKET_CLOSE:
            status = "open"
            session = "regular"
        elif current_time <= self.AFTER_HOURS_END:
            status = "after-hours"
            session = "after-hours"
        else:
            status = "closed"
            session = "closed"

        return {
            "status": status,
            "session": session,
            "is_open": status == "open",
            "current_time": now.isoformat(),
            "market_open": self.MARKET_OPEN.strftime("%H:%M"),
            "market_close": self.MARKET_CLOSE.strftime("%H:%M"),
        }

    async def get_market_indices(self) -> Dict:
        from app.services.financial.stock_service import StockService

        indices = {
            "^GSPC": "S&P 500",
            "^DJI": "Dow Jones",
            "^IXIC": "NASDAQ",
            "^RUT": "Russell 2000",
            "^VIX": "VIX",
        }

        stock_service = StockService()
        results = {}
        for symbol, name in indices.items():
            data = await stock_service.get_stock_data(symbol)
            if data:
                results[name] = {
                    "price": data["price"],
                    "change": data["change"],
                    "change_percent": data["change_percent"],
                }
        return results
