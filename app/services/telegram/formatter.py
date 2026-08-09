import re
from typing import Optional


class TelegramFormatter:
    """Central formatter for all Telegram messages. Uses only supported HTML tags."""
    
    @staticmethod
    def format(text: str) -> str:
        """Format any text for Telegram with proper HTML."""
        if not text:
            return text
        
        # Step 1: Convert markdown to HTML
        text = TelegramFormatter._convert_markdown(text)
        
        # Step 2: Clean up any unsupported tags
        text = TelegramFormatter._cleanup_unsupported(text)
        
        # Step 3: Clean up any nested/duplicate tags
        text = TelegramFormatter._cleanup(text)
        
        return text
    
    @staticmethod
    def _convert_markdown(text: str) -> str:
        """Convert markdown formatting to HTML."""
        # Convert **bold** to <b>bold</b>
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        # Convert *italic* to <i>italic</i>
        text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
        # Convert `code` to <code>code</code>
        text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
        return text
    
    @staticmethod
    def _cleanup_unsupported(text: str) -> str:
        """Remove unsupported HTML tags (Telegram only supports b, i, code, pre, a, u, s, spoiler, blockquote)."""
        # Remove <font> tags (not supported) - keep the content
        text = re.sub(r'<font[^>]*>(.*?)</font>', r'\1', text)
        # Remove <span> tags (not supported) - keep the content
        text = re.sub(r'<span[^>]*>(.*?)</span>', r'\1', text)
        # Remove <div> tags (not supported) - keep the content
        text = re.sub(r'<div[^>]*>(.*?)</div>', r'\1', text)
        # Remove <p> tags (not supported) - keep the content
        text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1', text)
        # Remove <br> tags (not supported) - convert to newline
        text = re.sub(r'<br\s*/?>', '\n', text)
        return text
    
    @staticmethod
    def _cleanup(text: str) -> str:
        """Clean up any nested/duplicate tags."""
        # Remove nested <b> tags
        text = re.sub(r'<b><b>(.+?)</b></b>', r'<b>\1</b>', text)
        # Remove nested <i> tags
        text = re.sub(r'<i><i>(.+?)</i></i>', r'<i>\1</i>', text)
        # Remove nested <code> tags
        text = re.sub(r'<code><code>(.+?)</code></code>', r'<code>\1</code>', text)
        # Remove empty tags
        text = re.sub(r'<b></b>', '', text)
        text = re.sub(r'<i></i>', '', text)
        text = re.sub(r'<code></code>', '', text)
        text = re.sub(r'<pre></pre>', '', text)
        return text


def format_message(text: str) -> str:
    """Convenience function to format a message."""
    return TelegramFormatter.format(text)
