from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class UserDTO:
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    sectors: List[str] = field(default_factory=list)
    watchlist: List[str] = field(default_factory=list)
    onboarding_completed: bool = False
    onboarding_step: int = 0
    briefing_enabled: bool = False
    briefing_time: Optional[str] = None
    google_connected: bool = False


@dataclass
class ConversationDTO:
    id: int
    user_id: int
    title: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class MessageDTO:
    id: int
    conversation_id: int
    role: str
    content: str
    intent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class StockDataDTO:
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int
    market_cap: int
    pe_ratio: Optional[float] = None
    eps: Optional[float] = None
    dividend_yield: Optional[float] = None
    fifty_two_week_high: float = 0
    fifty_two_week_low: float = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CompanyInfoDTO:
    symbol: str
    name: str
    sector: str
    industry: str
    description: str
    employees: Optional[int] = None
    headquarters: str = ""
    website: Optional[str] = None
    revenue: Optional[int] = None
    net_income: Optional[int] = None
    total_assets: Optional[int] = None
    total_debt: Optional[int] = None
    current_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    return_on_equity: Optional[float] = None
    profit_margin: Optional[float] = None
    revenue_growth_yoy: Optional[float] = None
    earnings_growth_yoy: Optional[float] = None


@dataclass
class NewsDTO:
    title: str
    link: str
    summary: str
    published: str
    source: str


@dataclass
class MarketStatusDTO:
    status: str
    is_open: bool
    spy_price: float
    spy_change: float
    spy_change_percent: float
    timestamp: datetime
    timezone: str


@dataclass
class AlertDTO:
    id: int
    symbol: str
    alert_type: str
    target_value: float
    triggered: bool = False
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class BriefingDTO:
    user_id: int
    summary_type: str
    content: str
    generated_at: datetime = field(default_factory=datetime.now)