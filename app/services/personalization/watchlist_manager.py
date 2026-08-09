import logging
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User

logger = logging.getLogger(__name__)


class WatchlistManager:
    """
    Manages user watchlists with natural language support.
    Handles add, remove, and list operations via conversation.
    """

    async def parse_watchlist_command(self, message: str) -> Dict:
        """Parse natural language watchlist commands."""
        message_lower = message.lower()

        if any(word in message_lower for word in ["remove", "delete", "stop", "untrack"]):
            action = "remove"
        elif any(word in message_lower for word in ["add", "track", "follow", "watch"]):
            action = "add"
        elif any(word in message_lower for word in ["list", "show", "what are"]):
            action = "list"
        else:
            return {"action": None}

        import re
        skip_words = {
            "ADD", "DELETE", "STOP", "SHOW", "LIST", "WHAT", "THE", "AND", "FOR",
            "ARE", "BUT", "NOT", "YOU", "ALL", "CAN", "HER", "WAS", "ONE", "OUR",
            "OUT", "HAS", "HIS", "HOW", "ITS", "MAY", "NEW", "NOW", "OLD", "SEE",
            "WAY", "WHO", "DID", "GET", "LET", "SAY", "SHE", "TOO", "USE", "TOP",
            "REMOVE", "DELETE", "FOLLOW", "TRACK", "WATCH", "START", "HELLO",
            "THAT", "THIS", "WITH", "HAVE", "FROM", "THEY", "BEEN", "SAID",
            "EACH", "MAKE", "LIKE", "LONG", "LOOK", "MANY", "MOST", "OVER",
            "SUCH", "TAKE", "THAN", "THEM", "THEN", "WELL", "WERE", "YOUR",
            "TO", "MY", "MMY", "ME", "I", "AM", "IS", "IT", "BE", "DO", "SO",
            "IF", "OR", "AN", "AS", "AT", "BY", "IN", "OF", "ON", "UP", "GO",
            "NO", "OK", "OH", "HI", "HEY", "PLEASE", "THANK", "THANKS",
            "ALSO", "JUST", "ONLY", "WANT", "NEED", "LIKE", "LOVE", "HATE",
            "WHEN", "WHERE", "WHY", "HOW", "WHICH", "WHAT", "WHO", "WHOSE",
            "WILL", "WOULD", "COULD", "SHOULD", "MIGHT", "MUST", "SHALL",
            "CAN", "MAY", "MIGHT", "MUST", "SHALL", "WILL",
            "SOME", "ANY", "EVERY", "EACH", "BOTH", "FEW", "MORE", "MOST",
            "OTHER", "ANOTHER", "SUCH", "THAN", "THEN", "ALSO",
            "BECAUSE", "SINCE", "WHILE", "ALTHOUGH", "THOUGH", "EVEN",
            "BUT", "YET", "STILL", "ALREADY", "YET", "EVEN",
            "VERY", "TOO", "QUITE", "RATHER", "PRETTY", "REALLY",
            "INTO", "ONTO", "UPON", "THROUGH", "DURING", "BEFORE",
            "AFTER", "ABOVE", "BELOW", "BETWEEN", "UNDER", "OVER",
            "ABOUT", "AGAIN", "ALONG", "AROUND", "BEHIND", "BESIDE",
            "BEYOND", "INSIDE", "OUTSIDE", "NEAR", "TOWARD",
        }
        ticker_pattern = r'\b([A-Z]{2,5})\b'
        tickers = [t for t in re.findall(ticker_pattern, message.upper()) if t not in skip_words]

        known_names = {
            "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL", "alphabet": "GOOGL",
            "amazon": "AMZN", "tesla": "TSLA", "nvidia": "NVDA", "meta": "META",
            "netflix": "NFLX", "amd": "AMD", "intel": "INTC", "salesforce": "CRM",
            "berkshire": "BRK.B", "jpmorgan": "JPM", "goldman": "GS", "visa": "V",
            "mastercard": "MA", "walmart": "WMT", "costco": "COST", "coca": "KO",
            "pepsi": "PEP", "disney": "DIS", "boeing": "BA",
        }
        for name, ticker in known_names.items():
            if name in message_lower and ticker not in tickers:
                tickers.append(ticker)

        return {"action": action, "tickers": tickers}

    async def add_to_watchlist(
        self, user_id: int, symbols: List[str], db: AsyncSession
    ) -> Dict:
        """Add symbols to user's watchlist."""
        result = await db.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return {"success": False, "error": "User not found"}

        current_watchlist = list(user.watchlist or [])
        added = []
        already_exists = []

        for symbol in symbols:
            symbol = symbol.upper()
            if symbol in current_watchlist:
                already_exists.append(symbol)
            else:
                current_watchlist.append(symbol)
                added.append(symbol)

        user.watchlist = list(current_watchlist)
        await db.commit()
        await db.refresh(user)

        return {
            "success": True,
            "added": added,
            "already_exists": already_exists,
            "total": len(user.watchlist),
        }

    async def remove_from_watchlist(
        self, user_id: int, symbols: List[str], db: AsyncSession
    ) -> Dict:
        """Remove symbols from user's watchlist."""
        result = await db.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return {"success": False, "error": "User not found"}

        current_watchlist = list(user.watchlist or [])
        removed = []
        not_found = []

        for symbol in symbols:
            symbol = symbol.upper()
            if symbol in current_watchlist:
                current_watchlist.remove(symbol)
                removed.append(symbol)
            else:
                not_found.append(symbol)

        user.watchlist = list(current_watchlist)
        await db.commit()
        await db.refresh(user)

        return {
            "success": True,
            "removed": removed,
            "not_found": not_found,
            "total": len(user.watchlist),
        }

    async def get_watchlist(self, user_id: int, db: AsyncSession) -> List[str]:
        """Get user's current watchlist."""
        result = await db.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        return user.watchlist if user else []

    async def format_watchlist_response(self, result: Dict, action: str) -> str:
        """Format watchlist operation result as user-friendly message."""
        if not result.get("success"):
            return result.get("error", "Failed to update watchlist.")

        if action == "add":
            added = result.get("added", [])
            already_exists = result.get("already_exists", [])
            total = result.get("total", 0)
            if added:
                msg = f"Added to your watchlist: {', '.join(added)}"
                if already_exists:
                    msg += f"\nAlready tracking: {', '.join(already_exists)}"
                msg += f"\n\nTotal stocks tracked: {total}"
                return msg
            else:
                return f"These stocks are already on your watchlist: {', '.join(already_exists)}"

        elif action == "remove":
            removed = result.get("removed", [])
            not_found = result.get("not_found", [])
            total = result.get("total", 0)
            if removed:
                msg = f"Removed from your watchlist: {', '.join(removed)}"
                if not_found:
                    msg += f"\nNot found on watchlist: {', '.join(not_found)}"
                msg += f"\n\nTotal stocks tracked: {total}"
                return msg
            else:
                return f"These stocks weren't on your watchlist: {', '.join(not_found)}"

        return "Watchlist updated."


watchlist_manager = WatchlistManager()
