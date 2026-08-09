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
        
        # Step 3: Clean up any double tags
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
        
        # Color percentage changes: +2.5% (green), -1.3% (red)
        text = re.sub(
            r'([+-]?\d+\.?\d*%)',
            lambda m: f'<font color="{TelegramFormatter.GREEN}">{m.group(1)}</font>' if m.group(1).startswith('+') or (not m.group(1).startswith('-') and m.group(1)[0].isdigit())
            else f'<font color="{TelegramFormatter.RED}">{m.group(1)}</font>',
            text
        )
        
        # Color ▲ arrows green and ▼ arrows red
        text = text.replace('▲', f'<font color="{TelegramFormatter.GREEN}">▲</font>')
        text = text.replace('▼', f'<font color="{TelegramFormatter.RED}">▼</font>')
        
        # Color BULLISH/BEARISH signals
        text = text.replace('BULLISH', f'<font color="{TelegramFormatter.GREEN}">BULLISH</font>')
        text = text.replace('BEARISH', f'<font color="{TelegramFormatter.RED}">BEARISH</font>')
        text = text.replace('[BULLISH]', f'<font color="{TelegramFormatter.GREEN}">[BULLISH]</font>')
        text = text.replace('[BEARISH]', f'<font color="{TelegramFormatter.RED}">[BEARISH]</font>')
        
        # Color UP/DOWN market status
        text = text.replace('[UP]', f'<font color="{TelegramFormatter.GREEN}">[UP]</font>')
        text = text.replace('[DOWN]', f'<font color="{TelegramFormatter.RED}">[DOWN]</font>')
        
        # Color sentiment scores
        text = re.sub(
            r'Sentiment score: (<i>[+-]?\d+\.?\d*</i>)',
            lambda m: f'Sentiment score: {m.group(1)}'.replace(
                m.group(1),
                f'<font color="{TelegramFormatter.GREEN}">{m.group(1)}</font>' if '+' in m.group(1)
                else f'<font color="{TelegramFormatter.RED}">{m.group(1)}</font>'
            ),
            text
        )
        
        # Color sentiment mood
        text = text.replace('Market Sentiment: Bullish', f'Market Sentiment: <font color="{TelegramFormatter.GREEN}">Bullish</font>')
        text = text.replace('Market Sentiment: Bearish', f'Market Sentiment: <font color="{TelegramFormatter.RED}">Bearish</font>')
        text = text.replace('Market Sentiment: Neutral', f'Market Sentiment: <font color="{TelegramFormatter.GOLD}">Neutral</font>')
        
        return text
    
    @staticmethod
    def _cleanup(text: str) -> str:
        """Clean up any formatting issues."""
        # Remove double <b> tags
        text = re.sub(r'<b><b>(.+?)</b></b>', r'<b>\1</b>', text)
        # Remove double <i> tags
        text = re.sub(r'<i><i>(.+?)</i></i>', r'<i>\1</i>', text)
        # Remove empty tags
        text = re.sub(r'<b></b>', '', text)
        text = re.sub(r'<i></i>', '', text)
        text = re.sub(r'<code></code>', '', text)
        return text


def format_message(text: str) -> str:
    """Convenience function to format a message."""
    return TelegramFormatter.format(text)
