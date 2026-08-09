from openai import AsyncOpenAI
from app.config import settings
from typing import Dict, List, Any, Optional
import json
import time
import logging

logger = logging.getLogger(__name__)


class ProviderConfig:
    """Configuration for a single AI provider."""
    def __init__(self, name: str, client: AsyncOpenAI, model: str, cost_per_1k: float = 0.0):
        self.name = name
        self.client = client
        self.model = model
        self.cost_per_1k = cost_per_1k
        self.token_count = 0


class AIService:
    """
    Core AI service with automatic fallback chain:
    1. OpenAI (if API key provided)
    2. OpenCode Zen / MiMo (if API key provided)
    3. Ollama (local, always available as last resort)
    """

    def __init__(self):
        self.providers: List[ProviderConfig] = []
        self._init_providers()

        if not self.providers:
            raise ValueError("No AI providers configured. Set at least one API key or ensure Ollama is running.")

        self.primary_model = self.providers[0].model
        self.secondary_model = self.providers[-1].model
        logger.info(f"AI providers initialized: {[p.name for p in self.providers]}")

    def _init_providers(self):
        """Initialize providers in fallback order: OpenAI -> OpenCode Zen -> Ollama."""
        # 1. OpenAI (highest priority)
        api_key = settings.openai_api_key or ""
        if api_key and not api_key.startswith("your_") and api_key != "sk-xxx":
            self.providers.append(ProviderConfig(
                name="OpenAI",
                client=AsyncOpenAI(api_key=api_key),
                model=settings.openai_model_primary,
                cost_per_1k=0.03,
            ))
            logger.info(f"OpenAI provider enabled: model={settings.openai_model_primary}")

        # 2. OpenCode Zen (second priority)
        zen_key = settings.opencode_zen_api_key or ""
        if zen_key and not zen_key.startswith("your_"):
            self.providers.append(ProviderConfig(
                name="OpenCode Zen",
                client=AsyncOpenAI(
                    api_key=zen_key,
                    base_url=settings.opencode_zen_base_url,
                ),
                model=settings.opencode_zen_model,
                cost_per_1k=0.0,
            ))
            logger.info(f"OpenCode Zen provider enabled: model={settings.opencode_zen_model}")

        # 3. Ollama (last resort - always added)
        ollama_client = AsyncOpenAI(
            api_key="ollama",
            base_url=f"{settings.ollama_base_url}/v1",
        )
        self.providers.append(ProviderConfig(
            name="Ollama",
            client=ollama_client,
            model=settings.ollama_model,
            cost_per_1k=0.0,
        ))
        logger.info(f"Ollama provider enabled: model={settings.ollama_model}")

    def count_tokens(self, text: str, model: str = None) -> int:
        if self.providers[0].name == "Ollama":
            return len(text) // 4
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(model or self.primary_model)
            return len(encoding.encode(text))
        except Exception:
            return len(text) // 4

    def estimate_cost(self, tokens: int, model: str) -> float:
        for provider in self.providers:
            if provider.model == model:
                return (tokens / 1000) * provider.cost_per_1k
        return (tokens / 1000) * 0.01

    async def generate(
        self,
        prompt: str,
        system_message: str = "",
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        last_error = None
        for provider in self.providers:
            start_time = time.time()
            try:
                use_model = model if model else provider.model
                kwargs = {
                    "model": use_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if response_format and provider.name in ("OpenAI", "OpenCode Zen"):
                    kwargs["response_format"] = response_format

                response = await provider.client.chat.completions.create(**kwargs)

                content = response.choices[0].message.content
                tokens_used = response.usage.total_tokens if response.usage else len(content) // 4
                prompt_tokens = response.usage.prompt_tokens if response.usage else tokens_used // 2
                completion_tokens = response.usage.completion_tokens if response.usage else tokens_used // 2

                provider.token_count += tokens_used
                cost = self.estimate_cost(tokens_used, use_model)
                duration = time.time() - start_time

                logger.info(f"AI generation completed ({provider.name}) in {duration:.2f}s, model={use_model}, tokens={tokens_used}")

                return {
                    "content": content,
                    "model": provider.model,
                    "provider": provider.name,
                    "tokens_used": tokens_used,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "cost_estimate": cost,
                    "duration": duration,
                    "success": True,
                }
            except Exception as e:
                duration = time.time() - start_time
                last_error = str(e)
                logger.warning(f"AI generation failed ({provider.name}): {e}, model={provider.model}, duration={duration:.2f}s")
                continue

        logger.error(f"All AI providers failed. Last error: {last_error}")
        return {
            "content": "",
            "model": self.primary_model,
            "provider": "none",
            "tokens_used": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "cost_estimate": 0,
            "duration": 0,
            "success": False,
            "error": f"All providers failed. Last error: {last_error}",
        }

    async def generate_structured(
        self,
        prompt: str,
        system_message: str = "",
        model: str = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        if self.providers[0].name != "Ollama":
            result = await self.generate(
                prompt=prompt,
                system_message=system_message,
                model=model,
                temperature=temperature,
                response_format={"type": "json_object"},
            )
        else:
            json_prompt = prompt + "\n\nIMPORTANT: Return ONLY valid JSON, no markdown or extra text."
            result = await self.generate(
                prompt=json_prompt,
                system_message=system_message,
                model=model,
                temperature=temperature,
            )

        if result["success"]:
            try:
                return {"data": json.loads(result["content"]), "metadata": result}
            except json.JSONDecodeError:
                return {"data": {"response": result["content"]}, "metadata": result}
        return {"data": {}, "metadata": result}

    async def summarize(self, text: str, max_length: int = 200) -> str:
        prompt = f"Summarize the following text in {max_length} words or less:\n\n{text}"
        result = await self.generate(
            prompt=prompt,
            model=self.secondary_model,
            temperature=0.3,
            max_tokens=500,
        )
        return result["content"] if result["success"] else ""

    async def analyze_sentiment(self, text: str) -> float:
        prompt = f"Analyze the sentiment of this financial text. Return a JSON object with 'score' (float from -1 to 1) and 'label' (negative/neutral/positive):\n\n{text}"
        result = await self.generate_structured(prompt=prompt, model=self.secondary_model)
        data = result.get("data", {})
        return data.get("score", 0.0)


ai_service = AIService()
