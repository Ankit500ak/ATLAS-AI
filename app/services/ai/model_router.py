from typing import Dict
import logging

logger = logging.getLogger(__name__)


class ModelRouter:
    """
    Routes requests to appropriate AI models based on:
    - Task complexity
    - Cost optimization
    - Latency requirements
    """

    MODEL_CONFIGS = {
        "mimo": {
            "model": "mimo-v2.5-free",
            "cost_per_1k": 0.0,
            "max_tokens": 4096,
            "quality": "good",
        },
        "gpt4": {
            "model": "gpt-4",
            "cost_per_1k": 0.03,
            "max_tokens": 8192,
            "quality": "highest",
        },
        "gpt35": {
            "model": "gpt-3.5-turbo",
            "cost_per_1k": 0.002,
            "max_tokens": 4096,
            "quality": "good",
        },
    }

    INTENT_COMPLEXITY = {
        "query_stock_price": 0.2,
        "get_news": 0.2,
        "set_alert": 0.2,
        "explain_concept": 0.3,
        "market_news": 0.3,
        "research_company": 0.5,
        "compare_companies": 0.6,
        "macro_economic": 0.5,
        "earnings_analysis": 0.7,
        "portfolio_analysis": 0.7,
        "sec_filing": 0.8,
        "analyze_document": 0.8,
        "general_question": 0.3,
    }

    def route(self, intent: str, complexity_override: float = None) -> Dict:
        complexity = complexity_override or self.INTENT_COMPLEXITY.get(intent, 0.5)

        # Use MiMo for all tasks (free, good quality)
        selected = "mimo"
        reason = "MiMo primary model"

        config = self.MODEL_CONFIGS[selected]
        logger.info(f"Model routed: {selected} for intent={intent}, complexity={complexity}, reason={reason}")

        return {
            "model_name": config["model"],
            "complexity": complexity,
            "reason": reason,
            "max_tokens": config["max_tokens"],
        }

    def get_model_for_intent(self, intent: str) -> str:
        return self.MODEL_CONFIGS["mimo"]["model"]
