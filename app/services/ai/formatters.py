from typing import Dict, List, Any


def format_stock_comparison(data: Dict[str, Any], tickers: List[str]) -> str:
    """Format stock comparison in clean, scannable structure."""
    
    if not data or not tickers:
        return "No data available for comparison."
    
    lines = []
    lines.append(f"**Stock Comparison: {' vs '.join(tickers)}**\n")
    
    # Price & Performance
    lines.append("**Price & Today:**")
    for ticker in tickers:
        stock = data.get(ticker, {})
        price = stock.get("price", "N/A")
        change = stock.get("change_percent", 0)
        arrow = "▲" if change >= 0 else "▼"
        lines.append(f"  {ticker}: ${price} {arrow} {change:+.2f}%")
    lines.append("")
    
    # Fundamentals
    lines.append("**Fundamentals:**")
    for ticker in tickers:
        stock = data.get(ticker, {})
        pe = stock.get("pe_ratio", "N/A")
        margin = stock.get("profit_margin", "N/A")
        market_cap = stock.get("market_cap", "N/A")
        lines.append(f"  {ticker}: P/E {pe} | Margin {margin} | Cap {market_cap}")
    lines.append("")
    
    # 52-Week Range
    lines.append("**52-Week Range:**")
    for ticker in tickers:
        stock = data.get(ticker, {})
        low_52 = stock.get("52_week_low", "N/A")
        high_52 = stock.get("52_week_high", "N/A")
        lines.append(f"  {ticker}: ${low_52} - ${high_52}")
    lines.append("")
    
    return "\n".join(lines)


def format_stock_analysis(ticker: str, data: Dict[str, Any]) -> str:
    """Format single stock analysis cleanly."""
    
    if not data:
        return f"No data available for {ticker}."
    
    price = data.get("price", "N/A")
    change = data.get("change_percent", 0)
    arrow = "▲" if change >= 0 else "▼"
    
    lines = []
    lines.append(f"**{ticker} Analysis**\n")
    lines.append(f"**Price:** ${price} {arrow} {change:+.2f}%")
    lines.append(f"**Open:** ${data.get('open', 'N/A')}")
    lines.append(f"**High/Low:** ${data.get('high', 'N/A')} / ${data.get('low', 'N/A')}")
    lines.append(f"**Volume:** {data.get('volume', 'N/A'):,}")
    lines.append("")
    
    # Fundamentals
    pe = data.get("pe_ratio", "N/A")
    market_cap = data.get("market_cap", "N/A")
    dividend = data.get("dividend_yield", "N/A")
    lines.append(f"**Fundamentals:**")
    lines.append(f"  P/E: {pe} | Market Cap: {market_cap}")
    lines.append(f"  Dividend Yield: {dividend}")
    
    return "\n".join(lines)


def format_watchlist_summary(stocks: List[Dict[str, Any]]) -> str:
    """Format watchlist with prices in compact view."""
    
    if not stocks:
        return "Your watchlist is empty."
    
    lines = []
    lines.append("**Your Watchlist:**\n")
    
    for stock in stocks:
        ticker = stock.get("ticker", "?")
        price = stock.get("price", "N/A")
        change = stock.get("change_percent", 0)
        arrow = "▲" if change >= 0 else "▼"
        lines.append(f"  {ticker}: ${price} {arrow} {change:+.2f}%")
    
    lines.append(f"\nTracking {len(stocks)} stocks")
    
    return "\n".join(lines)


def format_portfolio_analysis(portfolio: Dict[str, Any]) -> str:
    """Format portfolio analysis in structured way."""
    
    lines = []
    lines.append("**Portfolio Analysis**\n")
    
    total_value = portfolio.get("total_value", 0)
    total_change = portfolio.get("total_change_percent", 0)
    arrow = "▲" if total_change >= 0 else "▼"
    
    lines.append(f"**Total Value:** ${total_value:,.2f} {arrow} {total_change:+.2f}%\n")
    
    holdings = portfolio.get("holdings", [])
    if holdings:
        lines.append("**Holdings:**")
        for h in holdings:
            ticker = h.get("ticker", "?")
            shares = h.get("shares", 0)
            value = h.get("value", 0)
            gain_loss = h.get("gain_loss_percent", 0)
            gain_arrow = "▲" if gain_loss >= 0 else "▼"
            lines.append(f"  {ticker}: {shares} shares | ${value:,.2f} | {gain_arrow} {gain_loss:+.2f}%")
    
    return "\n".join(lines)


def format_market_overview(indices: Dict[str, Any]) -> str:
    """Format market overview compactly."""
    
    lines = []
    lines.append("**Market Overview**\n")
    
    for name, data in indices.items():
        value = data.get("value", "N/A")
        change = data.get("change_percent", 0)
        arrow = "▲" if change >= 0 else "▼"
        lines.append(f"  {name}: {value} {arrow} {change:+.2f}%")
    
    return "\n".join(lines)
