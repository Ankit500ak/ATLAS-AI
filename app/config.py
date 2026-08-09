from pydantic_settings import BaseSettings
from typing import Optional
import os
import secrets


class Settings(BaseSettings):
    # Telegram
    telegram_bot_token: str = ""
    telegram_webhook_url: str = ""
    telegram_webhook_secret: str = ""

    # OpenAI
    openai_api_key: str = ""
    openai_model_primary: str = "gpt-4"
    openai_model_secondary: str = "gpt-3.5-turbo"

    # OpenCode Zen (fallback #1 - cloud, free tier available)
    opencode_zen_api_key: str = ""
    opencode_zen_base_url: str = "https://opencode.ai/zen/v1"
    opencode_zen_model: str = "mimo-v2.5-free"

    # Ollama (fallback #2 - local inference)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:1.5b"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/finance_assistant.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = ""
    allowed_users: str = ""

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""

    # Application
    app_env: str = "development"
    log_level: str = "INFO"
    max_conversation_history: int = 50
    token_budget: int = 4000
    max_working_memory: int = 20

    class Config:
        env_file = ".env"
        case_sensitive = False

    def model_post_init(self, __context) -> None:
        if not self.secret_key:
            self.secret_key = secrets.token_urlsafe(32)

    def is_allowed_user(self, user_id: int) -> bool:
        if not self.allowed_users:
            return True
        allowed = [int(uid.strip()) for uid in self.allowed_users.split(",") if uid.strip()]
        return user_id in allowed


settings = Settings()
