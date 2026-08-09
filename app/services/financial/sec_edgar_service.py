import httpx
import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

_last_request_time = 0.0
_rate_lock = asyncio.Lock()
_min_interval = 0.25


async def _rate_limit():
    global _last_request_time
    async with _rate_lock:
        now = asyncio.get_running_loop().time()
        elapsed = now - _last_request_time
        if elapsed < _min_interval:
            await asyncio.sleep(_min_interval - elapsed)
        _last_request_time = asyncio.get_running_loop().time()


class SECEdgarService:
    """
    Service for fetching SEC EDGAR filings.
    Uses the SEC EDGAR API (efts.sec.gov).
    """

    BASE_URL = "https://efts.sec.gov/LATEST"
    SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
    HEADERS = {
        "User-Agent": "AtlasAI/1.0 (financial-assistant@example.com)",
        "Accept": "application/json",
    }

    FILING_TYPES = {
        "10-K": "Annual Report",
        "10-Q": "Quarterly Report",
        "8-K": "Current Report",
        "DEF 14A": "Proxy Statement",
        "S-1": "IPO Registration",
        "13-F": "Institutional Holdings",
    }

    async def search_filings(
        self,
        company_name: str = None,
        ticker: str = None,
        filing_type: str = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Search for SEC filings."""
        try:
            params = {"dateRange": "custom", "startdt": "2024-01-01"}
            if company_name:
                params["company"] = company_name
            if ticker:
                params["ticker"] = ticker
            if filing_type:
                params["form_type"] = filing_type

            async with httpx.AsyncClient() as client:
                await _rate_limit()
                response = await client.get(
                    f"{self.BASE_URL}/search-index",
                    params=params,
                    headers=self.HEADERS,
                    timeout=30,
                )

                if response.status_code == 200:
                    data = response.json()
                    return self._parse_filings(data.get("hits", [])[:limit])
                else:
                    logger.error(f"SEC EDGAR search failed: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"SEC EDGAR search error: {e}")
            return []

    async def get_company_filings(
        self,
        cik: str,
        filing_type: str = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Get filings for a specific company by CIK."""
        try:
            url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"

            async with httpx.AsyncClient() as client:
                await _rate_limit()
                response = await client.get(url, headers=self.HEADERS, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    filings = data.get("filings", {}).get("recent", [])
                    return self._parse_company_filings(filings, filing_type, limit)
                else:
                    logger.error(f"SEC EDGAR company filings failed: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"SEC EDGAR company filings error: {e}")
            return []

    async def get_filing_content(self, filing_url: str) -> Optional[str]:
        """Fetch and extract text content from a filing."""
        try:
            async with httpx.AsyncClient() as client:
                await _rate_limit()
                response = await client.get(filing_url, headers=self.HEADERS, timeout=30)

                if response.status_code == 200:
                    return response.text[:50000]
                return None

        except Exception as e:
            logger.error(f"SEC EDGAR content fetch error: {e}")
            return None

    async def analyze_filing(self, filing_url: str, filing_type: str) -> Dict:
        """Analyze a SEC filing using AI."""
        from app.services.ai.service import ai_service

        content = await self.get_filing_content(filing_url)

        if not content:
            return {"error": "Could not fetch filing content"}

        prompt = f"""Analyze this SEC {filing_type} filing and provide:
1. Executive Summary (2-3 sentences)
2. Key Financial Highlights
3. Risk Factors
4. Notable Changes from Previous Filings
5. Management Outlook

Filing Content (excerpt):
{content[:8000]}

Provide a structured analysis."""

        result = await ai_service.generate(
            prompt=prompt,
            system_message="You are a SEC filing analyst. Be precise and cite specific sections.",
            temperature=0.3,
        )

        return {
            "analysis": result["content"] if result["success"] else "Analysis unavailable",
            "filing_type": filing_type,
            "url": filing_url,
        }

    def _parse_filings(self, hits: List[Dict]) -> List[Dict]:
        """Parse search results into structured filing data."""
        filings = []
        for hit in hits:
            source = hit.get("_source", {})
            filings.append({
                "file_num": source.get("file_num"),
                "form_type": source.get("form_type"),
                "display_names": source.get("display_names", []),
                "period_of_report": source.get("period_of_report"),
                "file_date": source.get("file_date"),
                "description": self.FILING_TYPES.get(source.get("form_type"), "Other Filing"),
            })
        return filings

    def _parse_company_filings(
        self, filings: Dict, filing_type: str, limit: int
    ) -> List[Dict]:
        """Parse company filings response."""
        results = []
        forms = filings.get("form", [])
        dates = filings.get("filingDate", [])
        urls = filings.get("primaryDocument", [])

        for i in range(min(len(forms), limit)):
            form = forms[i]
            if filing_type and form != filing_type:
                continue

            results.append({
                "form_type": form,
                "filing_date": dates[i] if i < len(dates) else None,
                "document": urls[i] if i < len(urls) else None,
                "description": self.FILING_TYPES.get(form, "Other Filing"),
            })

        return results

    async def get_cik_from_ticker(self, ticker: str) -> Optional[str]:
        """Get CIK number from stock ticker."""
        try:
            url = f"https://efts.sec.gov/LATEST/search-index?q={ticker}"
            async with httpx.AsyncClient() as client:
                await _rate_limit()
                response = await client.get(url, headers=self.HEADERS, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    hits = data.get("hits", [])
                    if hits:
                        return hits[0].get("_source", {}).get("cik")
            return None
        except Exception:
            return None


sec_edgar_service = SECEdgarService()
