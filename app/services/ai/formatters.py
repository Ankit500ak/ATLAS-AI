from typing import Dict, List, Any


def format_stock_comparison(data: Dict[str, Any], tickers: List[str]) -> str:
    """Format stock comparison with professional Telegram styling."""
    
    if not data or not tickers:
        return "No data available for comparison."
    
    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"📊 <b>STOCK COMPARISON</b>")
    lines.append(f"{' vs '.join(tickers)}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    # Price & Performance
    lines.append("💰 <b>PRICE & TODAY</b>")
    lines.append("─────────────────────────────")
    for ticker in tickers:
        stock = data.get(ticker, {})
        price = stock.get("price", "N/A")
        change = stock.get("change_percent", 0)
        if change >= 0:
            color = "#00C853"
            arrow = "▲"
            signal = "BULLISH"
        else:
            color = "#FF1744"
            arrow = "▼"
            signal = "BEARISH"
        lines.append(f'  <b>{ticker}</b>')
        lines.append(f'  └─ ${price} <font color="{color}">{arrow} {change:+.2f}%</font>')
        lines.append(f'    <font color="{color}">[{signal}]</font>')
    lines.append("")
    
    # Fundamentals
    lines.append("📈 <b>FUNDAMENTALS</b>")
    lines.append("─────────────────────────────")
    for ticker in tickers:
        stock = data.get(ticker, {})
        pe = stock.get("pe_ratio", "N/A")
        margin = stock.get("profit_margin", "N/A")
        market_cap = stock.get("market_cap", "N/A")
        lines.append(f'  <b>{ticker}</b>')
        lines.append(f'  └─ P/E: <code>{pe}</code>')
        lines.append(f'    Margin: <code>{margin}</code>')
        lines.append(f'    Cap: <code>{market_cap}</code>')
    lines.append("")
    
    # 52-Week Range
    lines.append("📅 <b>52-WEEK RANGE</b>")
    lines.append("─────────────────────────────")
    for ticker in tickers:
        stock = data.get(ticker, {})
        low_52 = stock.get("52_week_low", "N/A")
        high_52 = stock.get("52_week_high", "N/A")
        price = stock.get("price", 0)
        
        # Calculate position in range
        if low_52 and high_52 and price:
            try:
                low_f = float(low_52.replace(",", ""))
                high_f = float(high_52.replace(",", ""))
                price_f = float(price.replace(",", ""))
                if high_f > low_f:
                    position = ((price_f - low_f) / (high_f - low_f)) * 100
                    bar_len = 20
                    filled = int(position / 100 * bar_len)
                    bar = "█" * filled + "░" * (bar_len - filled)
                    lines.append(f'  <b>{ticker}</b>')
                    lines.append(f'  └─ <code>${low_52}</code> ─ <code>${high_52}</code>')
                    lines.append(f'    [{bar}] <font color="#FFD700">{position:.0f}%</font>')
                else:
                    lines.append(f'  <b>{ticker}</b>: <code>${low_52} - ${high_52}</code>')
            except:
                lines.append(f'  <b>{ticker}</b>: <code>${low_52} - ${high_52}</code>')
        else:
            lines.append(f'  <b>{ticker}</b>: <code>${low_52} - ${high_52}</code>')
    lines.append("")
    
    # Verdict
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if len(tickers) >= 2:
        s1 = data.get(tickers[0], {})
        s2 = data.get(tickers[1], {})
        pe1 = s1.get("pe_ratio", 0)
        pe2 = s2.get("pe_ratio", 0)
        if pe1 and pe2:
            try:
                pe1_f = float(str(pe1).replace(",", ""))
                pe2_f = float(str(pe2).replace(",", ""))
                if pe1_f < pe2_f:
                    lines.append(f'💡 <font color="#00C853">{tickers[0]}</font> is more <b>value-oriented</b>')
                else:
                    lines.append(f'💡 <font color="#00C853">{tickers[1]}</font> is more <b>value-oriented</b>')
            except:
                pass
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return "\n".join(lines)


def format_stock_analysis(ticker: str, data: Dict[str, Any]) -> str:
    """Format single stock analysis with professional styling."""
    
    if not data:
        return f"No data available for {ticker}."
    
    price = data.get("price", "N/A")
    change = data.get("change_percent", 0)
    if change >= 0:
        color = "#00C853"
        arrow = "▲"
        signal = "BULLISH"
    else:
        color = "#FF1744"
        arrow = "▼"
        signal = "BEARISH"
    
    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"📊 <b>{ticker} ANALYSIS</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    # Price Section
    lines.append("💰 <b>PRICE</b>")
    lines.append("─────────────────────────────")
    lines.append(f'  <b>Current:</b> <code>${price}</code>')
    lines.append(f'  <b>Change:</b> <font color="{color}">{arrow} {change:+.2f}%</font>')
    lines.append(f'  <b>Signal:</b> <font color="{color}">[{signal}]</font>')
    lines.append("")
    
    # Trading Range
    lines.append("📈 <b>TRADING RANGE</b>")
    lines.append("─────────────────────────────")
    lines.append(f'  <b>Open:</b> <code>${data.get("open", "N/A")}</code>')
    lines.append(f'  <b>High:</b> <code>${data.get("high", "N/A")}</code>')
    lines.append(f'  <b>Low:</b> <code>${data.get("low", "N/A")}</code>')
    lines.append(f'  <b>Volume:</b> <code>{data.get("volume", "N/A"):,}</code>')
    lines.append("")
    
    # Fundamentals
    pe = data.get("pe_ratio", "N/A")
    market_cap = data.get("market_cap", "N/A")
    dividend = data.get("dividend_yield", "N/A")
    lines.append("📊 <b>FUNDAMENTALS</b>")
    lines.append("─────────────────────────────")
    lines.append(f'  <b>P/E Ratio:</b> <code>{pe}</code>')
    lines.append(f'  <b>Market Cap:</b> <code>{market_cap}</code>')
    lines.append(f'  <b>Dividend:</b> <code>{dividend}</code>')
    lines.append("")
    
    # 52-Week
    low_52 = data.get("52_week_low", "N/A")
    high_52 = data.get("52_week_high", "N/A")
    lines.append("📅 <b>52-WEEK RANGE</b>")
    lines.append("─────────────────────────────")
    lines.append(f'  <code>${low_52}</code> ─ <code>${high_52}</code>')
    lines.append("")
    
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return "\n".join(lines)


def format_watchlist_summary(stocks: List[Dict[str, Any]]) -> str:
    """Format watchlist with professional styling."""
    
    if not stocks:
        return "Your watchlist is empty."
    
    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("📋 <b>YOUR WATCHLIST</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    total_change = 0
    for stock in stocks:
        ticker = stock.get("ticker", "?")
        price = stock.get("price", "N/A")
        change = stock.get("change_percent", 0)
        total_change += change
        if change >= 0:
            color = "#00C853"
            arrow = "▲"
        else:
            color = "#FF1744"
            arrow = "▼"
        lines.append(f'  <b>{ticker}</b>')
        lines.append(f'  └─ <code>${price}</code> <font color="{color}">{arrow} {change:+.2f}%</font>')
    
    lines.append("")
    lines.append("─────────────────────────────")
    avg_change = total_change / len(stocks) if stocks else 0
    if avg_change >= 0:
        color = "#00C853"
        arrow = "▲"
    else:
        color = "#FF1744"
        arrow = "▼"
    lines.append(f'📊 <b>Summary:</b> {len(stocks)} stocks')
    lines.append(f'📈 <b>Avg Change:</b> <font color="{color}">{arrow} {avg_change:+.2f}%</font>')
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return "\n".join(lines)


def format_market_overview(indices: Dict[str, Any]) -> str:
    """Format market overview with professional styling."""
    
    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("🌍 <b>MARKET OVERVIEW</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    for name, data in indices.items():
        value = data.get("value", "N/A")
        change = data.get("change_percent", 0)
        if change >= 0:
            color = "#00C853"
            arrow = "▲"
            status = "UP"
        else:
            color = "#FF1744"
            arrow = "▼"
            status = "DOWN"
        lines.append(f'  <b>{name}</b>')
        lines.append(f'  └─ <code>{value}</code> <font color="{color}">{arrow} {change:+.2f}%</font>')
        lines.append(f'    <font color="{color}">[{status}]</font>')
    
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return "\n".join(lines)


def format_portfolio_analysis(portfolio: Dict[str, Any]) -> str:
    """Format portfolio analysis with professional styling."""
    
    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("💼 <b>PORTFOLIO ANALYSIS</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    total_value = portfolio.get("total_value", 0)
    total_change = portfolio.get("total_change_percent", 0)
    if total_change >= 0:
        color = "#00C853"
        arrow = "▲"
    else:
        color = "#FF1744"
        arrow = "▼"
    
    lines.append("💰 <b>TOTAL VALUE</b>")
    lines.append("─────────────────────────────")
    lines.append(f'  <code>${total_value:,.2f}</code> <font color="{color}">{arrow} {total_change:+.2f}%</font>')
    lines.append("")
    
    holdings = portfolio.get("holdings", [])
    if holdings:
        lines.append("📊 <b>HOLDINGS</b>")
        lines.append("─────────────────────────────")
        for h in holdings:
            ticker = h.get("ticker", "?")
            shares = h.get("shares", 0)
            value = h.get("value", 0)
            gain_loss = h.get("gain_loss_percent", 0)
            if gain_loss >= 0:
                gcolor = "#00C853"
                gain_arrow = "▲"
            else:
                gcolor = "#FF1744"
                gain_arrow = "▼"
            lines.append(f'  <b>{ticker}</b>')
            lines.append(f'  └─ {shares} shares | <code>${value:,.2f}</code>')
            lines.append(f'    <font color="{gcolor}">{gain_arrow} {gain_loss:+.2f}%</font>')
    
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return "\n".join(lines)


def format_morning_briefing(briefing: Dict[str, Any]) -> str:
    """Format morning briefing with professional styling."""
    
    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("☀️ <b>GOOD MORNING, {name}!</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    # Market Status
    market_status = briefing.get("market_status", {})
    if market_status:
        lines.append("📈 <b>MARKET STATUS</b>")
        lines.append("─────────────────────────────")
        lines.append(f'  Status: <b>{market_status.get("status", "N/A")}</b>')
        lines.append(f'  Session: <b>{market_status.get("session", "N/A")}</b>')
        lines.append("")
    
    # Market Indices
    indices = briefing.get("market_indices", {})
    if indices:
        lines.append("🌍 <b>MARKET INDICES</b>")
        lines.append("─────────────────────────────")
        for name, data in indices.items():
            value = data.get("value", "N/A")
            change = data.get("change_percent", 0)
            if change >= 0:
                color = "#00C853"
                arrow = "▲"
            else:
                color = "#FF1744"
                arrow = "▼"
            lines.append(f'  <b>{name}</b>: <code>{value}</code> <font color="{color}">{arrow} {change:+.2f}%</font>')
        lines.append("")
    
    # Watchlist Updates
    watchlist = briefing.get("watchlist_updates", [])
    if watchlist:
        lines.append("📋 <b>WATCHLIST UPDATES</b>")
        lines.append("─────────────────────────────")
        for stock in watchlist[:5]:
            ticker = stock.get("ticker", "?")
            price = stock.get("price", "N/A")
            change = stock.get("change_percent", 0)
            if change >= 0:
                color = "#00C853"
                arrow = "▲"
            else:
                color = "#FF1744"
                arrow = "▼"
            lines.append(f'  <b>{ticker}</b>: <code>${price}</code> <font color="{color}">{arrow} {change:+.2f}%</font>')
        lines.append("")
    
    # Top News
    news = briefing.get("news_highlights", [])
    if news:
        lines.append("📰 <b>TOP NEWS</b>")
        lines.append("─────────────────────────────")
        for i, item in enumerate(news[:3], 1):
            title = item.get("title", "N/A")
            lines.append(f'  {i}. <b>{title}</b>')
        lines.append("")
    
    # Key Events
    events = briefing.get("key_events", [])
    if events:
        lines.append("📅 <b>KEY EVENTS</b>")
        lines.append("─────────────────────────────")
        for event in events[:3]:
            lines.append(f'  • {event}')
        lines.append("")
    
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 <i>Have a productive day!</i>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return "\n".join(lines)


def format_evening_summary(summary: Dict[str, Any]) -> str:
    """Format evening summary with professional styling."""
    
    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("🌆 <b>MARKET CLOSE SUMMARY</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    # Market Performance
    market = summary.get("market_performance", {})
    if market:
        lines.append("📈 <b>MARKET PERFORMANCE</b>")
        lines.append("─────────────────────────────")
        for name, data in market.items():
            value = data.get("value", "N/A")
            change = data.get("change_percent", 0)
            if change >= 0:
                color = "#00C853"
                arrow = "▲"
            else:
                color = "#FF1744"
                arrow = "▼"
            lines.append(f'  <b>{name}</b>: <code>{value}</code> <font color="{color}">{arrow} {change:+.2f}%</font>')
        lines.append("")
    
    # Watchlist Performance
    watchlist = summary.get("watchlist_performance", [])
    if watchlist:
        lines.append("📋 <b>YOUR WATCHLIST</b>")
        lines.append("─────────────────────────────")
        for stock in watchlist[:5]:
            ticker = stock.get("ticker", "?")
            price = stock.get("price", "N/A")
            change = stock.get("change_percent", 0)
            if change >= 0:
                color = "#00C853"
                arrow = "▲"
            else:
                color = "#FF1744"
                arrow = "▼"
            lines.append(f'  <b>{ticker}</b>: <code>${price}</code> <font color="{color}">{arrow} {change:+.2f}%</font>')
        lines.append("")
    
    # Top News
    news = summary.get("top_news", [])
    if news:
        lines.append("📰 <b>TOP NEWS</b>")
        lines.append("─────────────────────────────")
        for i, item in enumerate(news[:3], 1):
            title = item.get("title", "N/A")
            lines.append(f'  {i}. <b>{title}</b>')
        lines.append("")
    
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 <i>See you tomorrow!</i>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return "\n".join(lines)


def format_alert_triggered(alert: Dict[str, Any]) -> str:
    """Format triggered alert with professional styling."""
    
    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("🚨 <b>PRICE ALERT TRIGGERED</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    ticker = alert.get("ticker", "?")
    alert_type = alert.get("alert_type", "N/A")
    target = alert.get("target_value", "N/A")
    current = alert.get("current_value", "N/A")
    change = alert.get("change_percent", 0)
    
    if change >= 0:
        color = "#00C853"
        arrow = "▲"
    else:
        color = "#FF1744"
        arrow = "▼"
    
    lines.append(f'📊 <b>{ticker}</b>')
    lines.append("─────────────────────────────")
    lines.append(f'  <b>Alert Type:</b> <code>{alert_type}</code>')
    lines.append(f'  <b>Target:</b> <code>${target}</code>')
    lines.append(f'  <b>Current:</b> <code>${current}</code>')
    lines.append(f'  <b>Change:</b> <font color="{color}">{arrow} {change:+.2f}%</font>')
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return "\n".join(lines)


def format_earnings_calendar(earnings: List[Dict[str, Any]]) -> str:
    """Format earnings calendar with professional styling."""
    
    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("📅 <b>UPCOMING EARNINGS</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    for item in earnings[:5]:
        ticker = item.get("ticker", "?")
        date = item.get("date", "N/A")
        time = item.get("time", "N/A")
        estimate = item.get("estimate", "N/A")
        
        lines.append(f'  <b>{ticker}</b>')
        lines.append(f'  └─ Date: <code>{date}</code>')
        lines.append(f'    Time: <code>{time}</code>')
        lines.append(f'    Estimate: <code>{estimate}</code>')
    
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return "\n".join(lines)
