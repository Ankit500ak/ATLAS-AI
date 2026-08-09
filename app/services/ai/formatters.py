from typing import Dict, List, Any


def _filter_tickers(data: Dict[str, Any], tickers: List[str]) -> List[str]:
    """Filter out _info suffix tickers and return clean list."""
    return [t for t in tickers if not t.endswith('_info')]


def format_stock_comparison(data: Dict[str, Any], tickers: List[str]) -> str:
    """Format stock comparison with Telegram-supported formatting."""
    
    if not data or not tickers:
        return "No data available for comparison."
    
    clean_tickers = _filter_tickers(data, tickers)
    if not clean_tickers:
        clean_tickers = tickers[:2]
    
    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("📊 <b>STOCK COMPARISON</b>")
    lines.append(f"{' vs '.join(clean_tickers)}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    lines.append("💰 <b>PRICE & TODAY</b>")
    lines.append("─────────────────────────────")
    for ticker in clean_tickers:
        stock = data.get(ticker, {})
        price = stock.get("price", "N/A")
        change = stock.get("change_percent", 0)
        if change >= 0:
            arrow = "🟢 ▲"
            signal = "BULLISH"
        else:
            arrow = "🔴 ▼"
            signal = "BEARISH"
        lines.append(f'  <b>{ticker}</b>')
        lines.append(f'  └─ ${price} {arrow} {change:+.2f}%')
        lines.append(f'    [{signal}]')
    lines.append("")
    
    lines.append("📈 <b>FUNDAMENTALS</b>")
    lines.append("─────────────────────────────")
    for ticker in clean_tickers:
        stock = data.get(ticker, {})
        pe = stock.get("pe_ratio", "N/A")
        margin = stock.get("profit_margin", "N/A")
        market_cap = stock.get("market_cap", "N/A")
        if pe and pe != "N/A":
            try:
                pe = f"{float(pe):.1f}"
            except:
                pass
        if margin and margin != "N/A":
            try:
                margin = f"{float(margin)*100:.1f}%"
            except:
                pass
        if market_cap and market_cap != "N/A":
            try:
                cap = float(market_cap)
                if cap >= 1e12:
                    market_cap = f"${cap/1e12:.1f}T"
                elif cap >= 1e9:
                    market_cap = f"${cap/1e9:.1f}B"
                elif cap >= 1e6:
                    market_cap = f"${cap/1e6:.1f}M"
            except:
                pass
        lines.append(f'  <b>{ticker}</b>')
        lines.append(f'  └─ P/E: <code>{pe}</code>')
        lines.append(f'    Margin: <code>{margin}</code>')
        lines.append(f'    Cap: <code>{market_cap}</code>')
    lines.append("")
    
    lines.append("📅 <b>52-WEEK RANGE</b>")
    lines.append("─────────────────────────────")
    for ticker in clean_tickers:
        stock = data.get(ticker, {})
        low_52 = stock.get("52_week_low", "N/A")
        high_52 = stock.get("52_week_high", "N/A")
        price = stock.get("price", 0)
        
        if low_52 and high_52 and price and low_52 != "N/A" and high_52 != "N/A":
            try:
                low_f = float(str(low_52).replace(",", ""))
                high_f = float(str(high_52).replace(",", ""))
                price_f = float(str(price).replace(",", ""))
                if high_f > low_f:
                    position = ((price_f - low_f) / (high_f - low_f)) * 100
                    bar_len = 15
                    filled = int(position / 100 * bar_len)
                    bar = "█" * filled + "░" * (bar_len - filled)
                    lines.append(f'  <b>{ticker}</b>')
                    lines.append(f'  └─ <code>${low_52}</code> ─ <code>${high_52}</code>')
                    lines.append(f'    [{bar}] {position:.0f}%')
                else:
                    lines.append(f'  <b>{ticker}</b>: <code>${low_52} - ${high_52}</code>')
            except:
                lines.append(f'  <b>{ticker}</b>: <code>${low_52} - ${high_52}</code>')
        else:
            lines.append(f'  <b>{ticker}</b>: <code>Data unavailable</code>')
    lines.append("")
    
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if len(clean_tickers) >= 2:
        s1 = data.get(clean_tickers[0], {})
        s2 = data.get(clean_tickers[1], {})
        pe1 = s1.get("pe_ratio", 0)
        pe2 = s2.get("pe_ratio", 0)
        if pe1 and pe2:
            try:
                pe1_f = float(str(pe1).replace(",", ""))
                pe2_f = float(str(pe2).replace(",", ""))
                if pe1_f < pe2_f:
                    lines.append(f'💡 <b>{clean_tickers[0]}</b> is more <b>value-oriented</b>')
                else:
                    lines.append(f'💡 <b>{clean_tickers[1]}</b> is more <b>value-oriented</b>')
            except:
                pass
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return "\n".join(lines)


def format_stock_analysis(ticker: str, data: Dict[str, Any]) -> str:
    """Format single stock analysis with Telegram-supported formatting."""
    
    if not data:
        return f"No data available for {ticker}."
    
    price = data.get("price", "N/A")
    change = data.get("change_percent", 0)
    if change >= 0:
        arrow = "🟢 ▲"
        signal = "BULLISH"
    else:
        arrow = "🔴 ▼"
        signal = "BEARISH"
    
    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"📊 <b>{ticker} ANALYSIS</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    lines.append("💰 <b>PRICE</b>")
    lines.append("─────────────────────────────")
    lines.append(f'  <b>Current:</b> <code>${price}</code>')
    lines.append(f'  <b>Change:</b> {arrow} {change:+.2f}%')
    lines.append(f'  <b>Signal:</b> [{signal}]')
    lines.append("")
    
    lines.append("📈 <b>TRADING RANGE</b>")
    lines.append("─────────────────────────────")
    lines.append(f'  <b>Open:</b> <code>${data.get("open", "N/A")}</code>')
    lines.append(f'  <b>High:</b> <code>${data.get("high", "N/A")}</code>')
    lines.append(f'  <b>Low:</b> <code>${data.get("low", "N/A")}</code>')
    lines.append(f'  <b>Volume:</b> <code>{data.get("volume", "N/A"):,}</code>')
    lines.append("")
    
    pe = data.get("pe_ratio", "N/A")
    market_cap = data.get("market_cap", "N/A")
    dividend = data.get("dividend_yield", "N/A")
    lines.append("📊 <b>FUNDAMENTALS</b>")
    lines.append("─────────────────────────────")
    lines.append(f'  <b>P/E Ratio:</b> <code>{pe}</code>')
    lines.append(f'  <b>Market Cap:</b> <code>{market_cap}</code>')
    lines.append(f'  <b>Dividend:</b> <code>{dividend}</code>')
    lines.append("")
    
    low_52 = data.get("52_week_low", "N/A")
    high_52 = data.get("52_week_high", "N/A")
    lines.append("📅 <b>52-WEEK RANGE</b>")
    lines.append("─────────────────────────────")
    lines.append(f'  <code>${low_52}</code> ─ <code>${high_52}</code>')
    lines.append("")
    
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return "\n".join(lines)


def format_watchlist_summary(stocks: List[Dict[str, Any]]) -> str:
    """Format watchlist with Telegram-supported formatting."""
    
    if not stocks:
        return "Your watchlist is empty."
    
    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("📋 <b>YOUR WATCHLIST</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    total_change = 0
    valid_stocks = 0
    for stock in stocks:
        ticker = stock.get("ticker", "?")
        if ticker.endswith('_info'):
            continue
        price = stock.get("price", "N/A")
        change = stock.get("change_percent", 0)
        total_change += change
        valid_stocks += 1
        if change >= 0:
            arrow = "🟢 ▲"
        else:
            arrow = "🔴 ▼"
        lines.append(f'  <b>{ticker}</b>')
        lines.append(f'  └─ <code>${price}</code> {arrow} {change:+.2f}%')
    
    lines.append("")
    lines.append("─────────────────────────────")
    avg_change = total_change / valid_stocks if valid_stocks > 0 else 0
    if avg_change >= 0:
        arrow = "🟢 ▲"
    else:
        arrow = "🔴 ▼"
    lines.append(f'📊 <b>Summary:</b> {valid_stocks} stocks')
    lines.append(f'📈 <b>Avg Change:</b> {arrow} {avg_change:+.2f}%')
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return "\n".join(lines)


def format_market_overview(indices: Dict[str, Any]) -> str:
    """Format market overview with Telegram-supported formatting."""
    
    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("🌍 <b>MARKET OVERVIEW</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    for name, data in indices.items():
        if name.endswith('_info'):
            continue
        value = data.get("value", "N/A")
        change = data.get("change_percent", 0)
        if change >= 0:
            arrow = "🟢 ▲"
            status = "UP"
        else:
            arrow = "🔴 ▼"
            status = "DOWN"
        lines.append(f'  <b>{name}</b>')
        lines.append(f'  └─ <code>{value}</code> {arrow} {change:+.2f}%')
        lines.append(f'    [{status}]')
    
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return "\n".join(lines)


def format_morning_briefing(briefing: Dict[str, Any]) -> str:
    """Format morning briefing with Telegram-supported formatting."""
    
    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("☀️ <b>GOOD MORNING!</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    market_status = briefing.get("market_status", {})
    if market_status:
        lines.append("📈 <b>MARKET STATUS</b>")
        lines.append("─────────────────────────────")
        lines.append(f'  Status: <b>{market_status.get("status", "N/A")}</b>')
        lines.append(f'  Session: <b>{market_status.get("session", "N/A")}</b>')
        lines.append("")
    
    indices = briefing.get("market_indices", {})
    if indices:
        lines.append("🌍 <b>MARKET INDICES</b>")
        lines.append("─────────────────────────────")
        for name, data in indices.items():
            if name.endswith('_info'):
                continue
            value = data.get("value", "N/A")
            change = data.get("change_percent", 0)
            if change >= 0:
                arrow = "🟢 ▲"
            else:
                arrow = "🔴 ▼"
            lines.append(f'  <b>{name}</b>: <code>{value}</code> {arrow} {change:+.2f}%')
        lines.append("")
    
    watchlist = briefing.get("watchlist_updates", [])
    if watchlist:
        lines.append("📋 <b>WATCHLIST UPDATES</b>")
        lines.append("─────────────────────────────")
        for stock in watchlist[:5]:
            ticker = stock.get("ticker", "?")
            if ticker.endswith('_info'):
                continue
            price = stock.get("price", "N/A")
            change = stock.get("change_percent", 0)
            if change >= 0:
                arrow = "🟢 ▲"
            else:
                arrow = "🔴 ▼"
            lines.append(f'  <b>{ticker}</b>: <code>${price}</code> {arrow} {change:+.2f}%')
        lines.append("")
    
    news = briefing.get("news_highlights", [])
    if news:
        lines.append("📰 <b>TOP NEWS</b>")
        lines.append("─────────────────────────────")
        for i, item in enumerate(news[:3], 1):
            title = item.get("title", "N/A")
            lines.append(f'  {i}. <b>{title}</b>')
        lines.append("")
    
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 <i>Have a productive day!</i>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return "\n".join(lines)


def format_evening_summary(summary: Dict[str, Any]) -> str:
    """Format evening summary with Telegram-supported formatting."""
    
    lines = []
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("🌆 <b>MARKET CLOSE SUMMARY</b>")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    market = summary.get("market_performance", {})
    if market:
        lines.append("📈 <b>MARKET PERFORMANCE</b>")
        lines.append("─────────────────────────────")
        for name, data in market.items():
            if name.endswith('_info'):
                continue
            value = data.get("value", "N/A")
            change = data.get("change_percent", 0)
            if change >= 0:
                arrow = "🟢 ▲"
            else:
                arrow = "🔴 ▼"
            lines.append(f'  <b>{name}</b>: <code>{value}</code> {arrow} {change:+.2f}%')
        lines.append("")
    
    watchlist = summary.get("watchlist_performance", [])
    if watchlist:
        lines.append("📋 <b>YOUR WATCHLIST</b>")
        lines.append("─────────────────────────────")
        for stock in watchlist[:5]:
            ticker = stock.get("ticker", "?")
            if ticker.endswith('_info'):
                continue
            price = stock.get("price", "N/A")
            change = stock.get("change_percent", 0)
            if change >= 0:
                arrow = "🟢 ▲"
            else:
                arrow = "🔴 ▼"
            lines.append(f'  <b>{ticker}</b>: <code>${price}</code> {arrow} {change:+.2f}%')
        lines.append("")
    
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
    """Format triggered alert with Telegram-supported formatting."""
    
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
        arrow = "🟢 ▲"
    else:
        arrow = "🔴 ▼"
    
    lines.append(f'📊 <b>{ticker}</b>')
    lines.append("─────────────────────────────")
    lines.append(f'  <b>Alert Type:</b> <code>{alert_type}</code>')
    lines.append(f'  <b>Target:</b> <code>${target}</code>')
    lines.append(f'  <b>Current:</b> <code>${current}</code>')
    lines.append(f'  <b>Change:</b> {arrow} {change:+.2f}%')
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    return "\n".join(lines)


def format_earnings_calendar(earnings: List[Dict[str, Any]]) -> str:
    """Format earnings calendar with Telegram-supported formatting."""
    
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
