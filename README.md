# Atlas AI Financial Assistant

AI-powered Financial Assistant that lives inside Telegram and helps finance professionals stay informed, conduct research, and make better decisions through natural conversations.

## Features

- **Natural Conversations** - No commands, just chat naturally
- **Company Research** - Analyze stocks, earnings, and fundamentals
- **Market Intelligence** - Real-time market data and news
- **Document Analysis** - Upload and analyze financial documents
- **Price Alerts** - Set custom alerts for price movements
- **Daily Briefings** - Personalized morning market summaries
- **Watchlist Tracking** - Monitor your favorite stocks
- **Conversation Memory** - Remembers previous discussions

## Tech Stack

- **Backend**: Python + FastAPI
- **AI**: OpenAI GPT-4
- **Database**: SQLite + SQLAlchemy
- **Financial Data**: Yahoo Finance (yfinance)
- **Telegram**: python-telegram-bot

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Run the application:
```bash
python run.py
```

## Environment Variables

- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token from @BotFather
- `OPENAI_API_KEY` - Your OpenAI API key
- `DATABASE_URL` - Database connection string (default: SQLite)
- `SECRET_KEY` - Application secret key

## Project Structure

```
finance-ai-assistant/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration
│   ├── database.py             # Database setup
│   ├── models/                 # Database models
│   ├── schemas/                # Pydantic schemas
│   ├── services/
│   │   ├── ai/                 # AI pipeline (orchestrator, router, classifier)
│   │   ├── financial/          # Stock data, news, market
│   │   ├── conversation/       # Context management, memory
│   │   ├── document/           # Document processing
│   │   ├── personalization/    # User profiling
│   │   ├── telegram/           # Bot handlers
│   │   └── background/         # Scheduled jobs
│   ├── core/                   # Security, middleware
│   └── utils/                  # Helpers
├── data/                       # Local storage
├── tests/                      # Test suite
├── requirements.txt
├── .env.example
└── run.py
```

## Usage

Once the bot is running, open Telegram and search for your bot. Start a conversation:

1. Type `/start` to begin
2. Answer the onboarding questions
3. Start asking questions naturally!

Example queries:
- "What's Apple's stock price?"
- "Research NVIDIA"
- "Compare Microsoft and Google"
- "What's happening in the market today?"
- "Alert me when Tesla hits $250"
- "Give me my morning briefing"

## License

MIT
