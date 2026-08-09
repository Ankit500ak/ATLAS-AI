from datetime import datetime
import re


def format_currency(value: float) -> str:
    if abs(value) >= 1e12:
        return f"${value/1e12:.2f}T"
    elif abs(value) >= 1e9:
        return f"${value/1e9:.2f}B"
    elif abs(value) >= 1e6:
        return f"${value/1e6:.2f}M"
    elif abs(value) >= 1e3:
        return f"${value/1e3:.2f}K"
    return f"${value:.2f}"


def format_percentage(value: float) -> str:
    return f"{value:+.2f}%"


def format_number(value: float) -> str:
    if abs(value) >= 1e9:
        return f"{value/1e9:.2f}B"
    elif abs(value) >= 1e6:
        return f"{value/1e6:.2f}M"
    elif abs(value) >= 1e3:
        return f"{value/1e3:.2f}K"
    return f"{value:,.0f}"


def get_emoji(value: float) -> str:
    if value > 0:
        return "🟢"
    elif value < 0:
        return "🔴"
    return "⚪"


def truncate(text: str, max_length: int = 100) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def format_timestamp(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def escape_markdown(text: str) -> str:
    """Escape special Markdown V1 characters for Telegram."""
    if not text:
        return text
    chars = ['*', '_', '`', '[']
    for char in chars:
        text = text.replace(char, f'\\{char}')
    return text


def chunk_message(text: str, max_length: int = 4000) -> list:
    """Split a long message into chunks, respecting word boundaries and Markdown blocks."""
    if len(text) <= max_length:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break

        split_pos = max_length
        last_newline = text.rfind('\n', 0, max_length)
        if last_newline > max_length // 2:
            split_pos = last_newline + 1
        else:
            last_space = text.rfind(' ', 0, max_length)
            if last_space > max_length // 2:
                split_pos = last_space + 1

        chunks.append(text[:split_pos])
        text = text[split_pos:]

    return chunks
