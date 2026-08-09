from app.domain.services import SECFilingService
from typing import List, Dict, Any, Optional
import logging
import asyncio
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)


class SECFilingServiceImpl(SECFilingService):
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 3600
        self._base_url = "https://data.sec.gov"
        self._headers = {"User-Agent": "Atlas AI Financial Assistant (contact@example.com)"}

    async def search_filings(self, ticker: str, limit: int = 10) -> List[Dict[str, Any]]:
        cache_key = f"sec_filings_{ticker}_{limit}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if (datetime.now() - cached["timestamp"]).total_seconds() < self._cache_ttl:
                return cached["data"]

        try:
            cik = await self._get_cik(ticker)
            if not cik:
                return []

            url = f"{self._base_url}/submissions/CIK{cik}.json"
            async with aiohttp.ClientSession(headers=self._headers) as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        logger.warning(f"SEC API returned {resp.status} for {ticker}")
                        return []
                    data = await resp.json()

            filings = data.get("filings", {}).get("recent", {})
            results = []

            forms = filings.get("form", [])
            dates = filings.get("filingDate", [])
            accessions = filings.get("accessionNumber", [])
            descriptions = filings.get("primaryDocument", [])

            for i in range(min(len(forms), limit)):
                form_type = forms[i]
                if form_type in ["10-K", "10-Q", "8-K", "13F", "4", "S-1", "S-3"]:
                    results.append({
                        "form_type": form_type,
                        "filing_date": dates[i] if i < len(dates) else "N/A",
                        "accession_number": accessions[i] if i < len(accessions) else "",
                        "description": self._get_form_description(form_type),
                        "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accessions[i].replace('-', '')}/{accessions[i]}.txt" if i < len(accessions) else "",
                    })

            self._cache[cache_key] = {"data": results, "timestamp": datetime.now()}
            return results

        except Exception as e:
            logger.error(f"Failed to search SEC filings for {ticker}: {e}")
            return []

    async def get_filing_content(self, accession_number: str) -> Optional[str]:
        try:
            clean_accession = accession_number.replace("-", "")
            url = f"{self._base_url}/Archives/edgar/data/{clean_accession[:10]}/{clean_accession}/{accession_number}.txt"
            async with aiohttp.ClientSession(headers=self._headers) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return await resp.text()
            return None
        except Exception as e:
            logger.error(f"Failed to get filing content: {e}")
            return None

    async def _get_cik(self, ticker: str) -> Optional[str]:
        cache_key = f"cik_{ticker}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if (datetime.now() - cached["timestamp"]).total_seconds() < 86400:
                return cached["data"]

        try:
            url = "https://www.sec.gov/files/company_tickers.json"
            async with aiohttp.ClientSession(headers=self._headers) as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()

            for item in data.values():
                if item.get("ticker", "").upper() == ticker.upper():
                    cik = str(item.get("cik_str", "")).zfill(10)
                    self._cache[cache_key] = {"data": cik, "timestamp": datetime.now()}
                    return cik
            return None
        except Exception as e:
            logger.error(f"Failed to get CIK for {ticker}: {e}")
            return None

    def _get_form_description(self, form_type: str) -> str:
        descriptions = {
            "10-K": "Annual Report",
            "10-Q": "Quarterly Report",
            "8-K": "Current Report",
            "13F": "Institutional Holdings",
            "4": "Insider Transaction",
            "S-1": "Registration Statement",
            "S-3": "Shelf Registration",
        }
        return descriptions.get(form_type, "SEC Filing")