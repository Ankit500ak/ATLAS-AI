import re


def validate_stock_symbol(symbol: str) -> bool:
    return bool(re.match(r'^[A-Z]{1,5}$', symbol))


def validate_email(email: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))


def validate_time(time_str: str) -> bool:
    return bool(re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', time_str))


def sanitize_text(text: str) -> str:
    return text.strip().replace('<', '&lt;').replace('>', '&gt;')


def extract_tickers(text: str) -> list:
    return re.findall(r'\b([A-Z]{2,5})\b', text)
