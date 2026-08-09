import json
import os
from typing import List, Dict, Any

_follow_ups_cache: Dict[str, Any] = None


def _load_follow_ups() -> Dict[str, Any]:
    global _follow_ups_cache
    if _follow_ups_cache is None:
        json_path = os.path.join(os.path.dirname(__file__), "follow_up_questions.json")
        with open(json_path, "r") as f:
            _follow_ups_cache = json.load(f)
    return _follow_ups_cache


def get_follow_ups(
    intent: str,
    context: str = "default",
    **kwargs,
) -> List[str]:
    """
    Get follow-up questions for an intent and context.

    Args:
        intent: The classified intent (e.g. "view_watchlist", "set_alert")
        context: The specific scenario (e.g. "has_stocks", "empty", "success")
        **kwargs: Template variables for string interpolation (e.g. symbol="AAPL")

    Returns:
        List of follow-up question strings, with templates filled in.
    """
    data = _load_follow_ups()
    intent_config = data.get(intent, {})
    questions = intent_config.get(context, intent_config.get("default", []))

    result = []
    for q in questions:
        try:
            filled = q.format(**kwargs) if kwargs else q
            result.append(filled)
        except KeyError:
            result.append(q)
    return result


def get_all_intents() -> List[str]:
    data = _load_follow_ups()
    return list(data.keys())
