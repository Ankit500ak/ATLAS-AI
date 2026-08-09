import re
from typing import Optional


class TelegramFormatter:
    """Central formatter for all Telegram messages."""
    
    GREEN = "#00C853"
    RED = "#FF1744"
    GOLD = "#FFD700"
    BLUE = "#2196F3"
    GRAY = "#9E9E9E"
    
    @staticmethod
    def format(text: str) -> str:
        """Format any text for Telegram with proper HTML and colors."""
        if not text:
            return text
        
        # Step 1: Convert markdown to HTML
        text = TelegramFormatter._convert_markdown(text)
        
        # Step 2: Add colors for financial data
        text = TelegramFormatter._add_financial_colors(text)
        
        # Step 3: Clean up any nested/duplicate tags
        text = TelegramFormatter._cleanup(text)
        
        return text
    
    @staticmethod
    def _convert_markdown(text: str) -> str:
        """Convert markdown formatting to HTML."""
        # Convert **bold** to <b>bold</b>
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        # Convert *italic* to <i>italic</i> (but not inside <b> tags)
        text = re.sub(r'(?<!<b>)\*(?<!</b>)(.+?)(?<!<b>)\*(?!</b>)', r'<i>\1</i>', text)
        # Convert `code` to <code>code</code>
        text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
        return text
    
    @staticmethod
    def _add_financial_colors(text: str) -> str:
        """Add colors for financial data (green for profit, red for loss)."""
        
        # First, protect existing HTML tags by temporarily replacing them
        protected = []
        def protect(match):
            protected.append(match.group(0))
            return f"__PROTECTED_{len(protected)-1}__"
        
        # Protect all existing HTML tags
        text = re.sub(r'<[^>]+>', protect, text)
        
        # Color percentage changes: +2.5% (green), -1.3% (red)
        def color_percent(match):
            val = match.group(1)
            if val.startswith('+') or (val[0].isdigit()):
                return f'<font color="{TelegramFormatter.GREEN}">{val}</font>'
            else:
                return f'<font color="{TelegramFormatter.RED}">{val}</font>'
        
        text = re.sub(r'([+-]?\d+\.?\d*%)', color_percent, text)
        
        # Color ▲ arrows green and ▼ arrows red
        text = text.replace('▲', f'<font color="{TelegramFormatter.GREEN}">▲</font>')
        text = text.replace('▼', f'<font color="{TelegramFormatter.RED}">▼</font>')
        
        # Color BULLISH/BEARISH signals
        text = text.replace('BULLISH', f'<font color="{TelegramFormatter.GREEN}">BULLISH</font>')
        text = text.replace('BEARISH', f'<font color="{TelegramFormatter.RED}">BEARISH</font>')
        
        # Color UP/DOWN market status
        text = text.replace('[UP]', f'<font color="{TelegramFormatter.GREEN}">[UP]</font>')
        text = text.replace('[DOWN]', f'<font color="{TelegramFormatter.RED}">[DOWN]</font>')
        
        # Restore protected HTML tags
        def restore(match):
            idx = int(match.group(1))
            return protected[idx]
        
        text = re.sub(r'__PROTECTED_(\d+)__', restore, text)
        
        return text
    
    @staticmethod
    def _cleanup(text: str) -> str:
        """Clean up any nested/duplicate tags."""
        # Remove nested <font> tags: <font color="X"><font color="X">text</font></font> -> <font color="X">text</font>
        text = re.sub(r'<font color="([^"]+)"><font color="\1">(.*?)</font></font>', r'<font color="\1">\2</font>', text)
        
        # Remove nested <b> tags
        text = re.sub(r'<b><b>(.+?)</b></b>', r'<b>\1</b>', text)
        
        # Remove nested <i> tags
        text = re.sub(r'<i><i>(.+?)</i></i>', r'<i>\1</i>', text)
        
        # Remove empty tags
        text = re.sub(r'<b></b>', '', text)
        text = re.sub(r'<i></i>', '', text)
        text = re.sub(r'<code></code>', '', text)
        text = re.sub(r'<font[^>]*></font>', '', text)
        
        return text


def format_message(text: str) -> str:
    """Convenience function to format a message."""
    return TelegramFormatter.format(text)
