from typing import Dict, List, Any


def format_stock_comparison(data: Dict[str, Any], tickers: List[str]) -> str:
    """Format stock comparison with HTML colors for Telegram."""
    
    if not data or not tickers:
        return "No data available for comparison."
    
    lines = []
    lines.append(f"📊 <b>Stock Comparison: {' vs '.join(tickers)}</b>\n")
    
    # Price & Performance
    lines.append("💰 <b>Price & Today:</b>")
    for ticker in tickers:
        stock = data.get(ticker, {})
        price = stock.get("price", "N/A")
        change = stock.get("change_percent", 0)
        if change >= 0:
            color = "#00C853"  # Green
            arrow = "▲"
        else:
            color = "#FF1744"  # Red
            arrow = "▼"
        lines.append(f'  {ticker}: ${price} <font color="{color}">{arrow} {change:+.2f}%</font>')
    lines.append("")
    
    # Fundamentals
    lines.append("📈 <b>Fundamentals:</b>")
    for ticker in tickers:
        stock = data.get(ticker, {})
        pe = stock.get("pe_ratio", "N/A")
        margin = stock.get("profit_margin", "N/A")
        market_cap = stock.get("market_cap", "N/A")
        lines.append(f"  {ticker}: P/E {pe} | Margin {margin} | Cap {market_cap}")
    lines.append("")
    
    # 52-Week Range
    lines.append("📅 <b>52-Week Range:</b>")
    for ticker in tickers:
        stock = data.get(ticker, {})
        low_52 = stock.get("52_week_low", "N/A")
        high_52 = stock.get("52_week_high", "N/A")
        lines.append(f"  {ticker}: ${low_52} - ${high_52}")
    lines.append("")
    
    # Verdict
    if len(tickers) >= 2:
        s1 = data.get(tickers[0], {})
        s2 = data.get(tickers[1], {})
        pe1 = s1.get("pe_ratio", 0)
        pe2 = s2.get("pe_ratio", 0)
        if pe1 and pe2:
            if pe1 < pe2:
                lines.append(f'💡 <font color="#00C853">{tickers[0]} is more value-oriented</font>')
            else:
                lines.append(f'💡 <font color="#00C853">{tickers[1]} is more value-oriented</font>')
    
    return "\n".join(lines)


def format_stock_analysis(ticker: str, data: Dict[str, Any]) -> str:
    """Format single stock analysis with HTML colors."""
    
    if not data:
        return f"No data available for {ticker}."
    
    price = data.get("price", "N/A")
    change = data.get("change_percent", 0)
    if change >= 0:
        color = "#00C853"
        arrow = "▲"
    else:
        color = "#FF1744"
        arrow = "▼"
    
    lines = []
    lines.append(f"📊 <b>{ticker} Analysis</b>\n")
    lines.append(f'💰 <b>Price:</b> ${price} <font color="{color}">{arrow} {change:+.2f}%</font>')
    lines.append(f"📈 <b>Open:</b> ${data.get('open', 'N/A')}")
    lines.append(f"📉 <b>High/Low:</b> ${data.get('high', 'N/A')} / ${data.get('low', 'N/A')}")
    lines.append(f"📦 <b>Volume:</b> {data.get('volume', 'N/A'):,}")
    lines.append("")
    
    # Fundamentals
    pe = data.get("pe_ratio", "N/A")
    market_cap = data.get("market_cap", "N/A")
    dividend = data.get("dividend_yield", "N/A")
    lines.append(f"📈 <b>Fundamentals:</b>")
    lines.append(f"  P/E: {pe} | Market Cap: {market_cap}")
    lines.append(f"  Dividend Yield: {dividend}")
    
    return "\n".join(lines)


def format_watchlist_summary(stocks: List[Dict[str, Any]]) -> str:
    """Format watchlist with HTML colors in compact view."""
    
    if not stocks:
        return "Your watchlist is empty."
    
    lines = []
    lines.append("📋 <b>Your Watchlist:</b>\n")
    
    for stock in stocks:
        ticker = stock.get("ticker", "?")
        price = stock.get("price", "N/A")
        change = stock.get("change_percent", 0)
        if change >= 0:
            color = "#00C853"
            arrow = "▲"
        else:
            color = "#FF1744"
            arrow = "▼"
        lines.append(f'  {ticker}: ${price} <font color="{color}">{arrow} {change:+.2f}%</font>')
    
    lines.append(f"\n📊 Tracking {len(stocks)} stocks")
    
    return "\n".join(lines)


def format_market_overview(indices: Dict[str, Any]) -> str:
    """Format market overview with HTML colors."""
    
    lines = []
    lines.append("🌍 <b>Market Overview</b>\n")
    
    for name, data in indices.items():
        value = data.get("value", "N/A")
        change = data.get("change_percent", 0)
        if change >= 0:
            color = "#00C853"
            arrow = "▲"
        else:
            color = "#FF1744"
            arrow = "▼"
        lines.append(f'  {name}: {value} <font color="{color}">{arrow} {change:+.2f}%</font>')
    
    return "\n".join(lines)


def format_portfolio_analysis(portfolio: Dict[str, Any]) -> str:
    """Format portfolio analysis with HTML colors."""
    
    lines = []
    lines.append("💼 <b>Portfolio Analysis</b>\n")
    
    total_value = portfolio.get("total_value", 0)
    total_change = portfolio.get("total_change_percent", 0)
    if total_change >= 0:
        color = "#00C853"
        arrow = "▲"
    else:
        color = "#FF1744"
        arrow = "▼"
    
    lines.append(f'💰 <b>Total Value:</b> ${total_value:,.2f} <font color="{color}">{arrow} {total_change:+.2f}%</font>\n')
    
    holdings = portfolio.get("holdings", [])
    if holdings:
        lines.append("📊 <b>Holdings:</b>")
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
            lines.append(f'  {ticker}: {shares} shares | ${value:,.2f} | <font color="{gcolor}">{gain_arrow} {gain_loss:+.2f}%</font>')
    
    return "\n".join(lines)
