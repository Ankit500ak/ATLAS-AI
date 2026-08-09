import logging
from typing import Dict, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import asyncio

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4)


class EarningsCalendar:
    """
    Tracks upcoming earnings releases and provides earnings-related intelligence.
    """

    async def get_upcoming_earnings(self, symbols: list = None) -> list:
        """Get upcoming earnings dates for specified symbols."""
        import yfinance as yf

        if not symbols:
            symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META"]

        earnings = []
        for symbol in symbols[:10]:
            try:
                loop = asyncio.get_running_loop()
                ticker = await loop.run_in_executor(_executor, lambda s=symbol: yf.Ticker(s))
                calendar = await loop.run_in_executor(_executor, lambda t=ticker: t.calendar)

                if calendar is not None and not calendar.empty:
                    next_date = calendar.index[0] if len(calendar) > 0 else None
                    if next_date:
                        earnings.append({
                            "symbol": symbol,
                            "date": next_date.strftime("%Y-%m-%d") if hasattr(next_date, 'strftime') else str(next_date),
                            "days_until": (next_date - datetime.now()).days if hasattr(next_date, 'strftime') else None,
                        })
            except Exception as e:
                logger.debug(f"Could not get earnings for {symbol}: {e}")

        return sorted(earnings, key=lambda x: x.get("date", "9999"))

    async def get_earnings_surprises(self, symbol: str) -> Dict:
        """Get recent earnings surprises for a stock."""
        import yfinance as yf

        try:
            loop = asyncio.get_running_loop()
            ticker = await loop.run_in_executor(_executor, lambda: yf.Ticker(symbol))
            earnings_dates = await loop.run_in_executor(_executor, lambda t=ticker: t.earnings_dates)

            if earnings_dates is None or earnings_dates.empty:
                return {"symbol": symbol, "surprises": []}

            surprises = []
            for idx, row in earnings_dates.iterrows():
                eps_est = row.get("EPS Estimate")
                eps_actual = row.get("Reported EPS")
                if eps_est and eps_actual:
                    surprise_pct = ((eps_actual - eps_est) / abs(eps_est)) * 100
                    surprises.append({
                        "date": idx.strftime("%Y-%m-%d") if hasattr(idx, 'strftime') else str(idx),
                        "eps_estimate": float(eps_est),
                        "eps_actual": float(eps_actual),
                        "surprise_percent": round(surprise_pct, 2),
                        "beat": eps_actual > eps_est,
                    })

            return {
                "symbol": symbol,
                "surprises": surprises[:8],
                "beat_rate": sum(1 for s in surprises if s["beat"]) / max(len(surprises), 1) * 100,
            }

        except Exception as e:
            logger.error(f"Failed to get earnings surprises for {symbol}: {e}")
            return {"symbol": symbol, "surprises": []}

    async def generate_earnings_preview(self, symbol: str) -> str:
        """Generate an AI-powered earnings preview."""
        from app.services.ai.service import ai_service
        from app.services.financial.stock_service import StockService

        stock_service = StockService()

        stock_data = await stock_service.get_stock_data(symbol)
        company_info = await stock_service.get_company_info(symbol)
        earnings = await self.get_earnings_surprises(symbol)

        prompt = f"""Generate a brief earnings preview for {symbol}.

Company: {company_info.get('name', symbol) if company_info else symbol}
Current Price: ${stock_data.get('price', 'N/A') if stock_data else 'N/A'}
Sector: {company_info.get('sector', 'N/A') if company_info else 'N/A'}

Recent Earnings History:
{earnings.get('surprises', [])[:3]}

Beat Rate: {earnings.get('beat_rate', 0):.0f}%

Provide:
1. Key metrics to watch
2. Historical trend analysis
3. Potential risks/opportunities
4. What analysts are expecting

Keep it concise (3-4 paragraphs)."""

        result = await ai_service.generate(
            prompt=prompt,
            system_message="You are an earnings analyst providing a pre-earnings preview.",
            temperature=0.5,
        )

        return result["content"] if result["success"] else f"Earnings preview unavailable for {symbol}"


earnings_calendar = EarningsCalendar()
