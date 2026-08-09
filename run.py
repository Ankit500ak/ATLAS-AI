#!/usr/bin/env python3
"""
Atlas AI Financial Assistant - Main Entry Point
Run this script to start the application.
"""

import uvicorn
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    print("=" * 60)
    print("  Atlas AI Financial Assistant")
    print("  AI-Powered Financial Intelligence for Telegram")
    print("=" * 60)
    print()

    from app.config import settings

    if not settings.telegram_bot_token:
        print("WARNING: TELEGRAM_BOT_TOKEN not set!")
        print("Set it in .env file or environment variable.")
        print()

    if not settings.openai_api_key:
        print("WARNING: OPENAI_API_KEY not set!")
        print("Set it in .env file or environment variable.")
        print()

    print(f"Starting server on port 8000...")
    print(f"Environment: {settings.app_env}")
    print()

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
