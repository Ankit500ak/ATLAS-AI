from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class StockData(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int
    market_cap: float
    pe_ratio: Optional[float]
    eps: Optional[float]
    dividend_yield: Optional[float]
    fifty_two_week_high: float
    fifty_two_week_low: float
    timestamp: datetime


class CompanyInfo(BaseModel):
    symbol: str
    name: str
    sector: str
    industry: str
    description: str
    employees: Optional[int]
    headquarters: Optional[str]
    website: Optional[str]
    revenue: Optional[float]
    net_income: Optional[float]
    total_assets: Optional[float]
    total_debt: Optional[float]
    current_ratio: Optional[float]
    debt_to_equity: Optional[float]
    return_on_equity: Optional[float]
    profit_margin: Optional[float]
    revenue_growth_yoy: Optional[float]


class EarningsData(BaseModel):
    symbol: str
    quarter: str
    year: int
    report_date: datetime
    eps_estimate: Optional[float]
    eps_actual: Optional[float]
    revenue_estimate: Optional[float]
    revenue_actual: Optional[float]
    surprise_percent: Optional[float]
    guidance: Optional[str]
    key_highlights: List[str]


class NewsArticle(BaseModel):
    title: str
    summary: str
    source: str
    url: str
    published_at: datetime
    sentiment: Optional[float]
    relevance_score: float
    symbols: List[str]
    category: str


class MarketStatus(BaseModel):
    is_open: bool
    next_open: Optional[datetime]
    next_close: Optional[datetime]
    current_session: str  # pre-market, regular, after-hours, closed


class AlertCreate(BaseModel):
    symbol: str
    alert_type: str  # price_above, price_below, percent_change
    target_value: float
    message: Optional[str] = None


class AlertResponse(BaseModel):
    id: int
    symbol: str
    alert_type: str
    target_value: float
    is_active: bool
    triggered: bool
    created_at: datetime

    class Config:
        from_attributes = True
