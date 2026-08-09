<div align="center">

# ATLAS AI

### AI-Powered Financial Intelligence for Telegram

[![Python](https://img.shields.io/badge/Python-3.13-blue?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=flat-square&logo=telegram&logoColor=white)](https://telegram.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**Atlas AI is an intelligent financial assistant that lives inside Telegram, designed to help finance professionals make faster, better-informed decisions through natural conversations.**

[Features](#features) • [Architecture](#architecture) • [Quick Start](#quick-start) • [Usage](#usage) • [API](#api-reference) • [Deployment](#deployment)

</div>

---

## Overview

Finance professionals waste hours daily switching between Bloomberg terminals, SEC filings, news platforms, and spreadsheet dashboards. **Atlas AI eliminates this context switching** by bringing all financial intelligence into a single conversational interface inside Telegram.

Unlike traditional chatbots that simply answer questions, Atlas AI:
- **Remembers** your preferences, watchlist, and past conversations
- **Proactively** sends you relevant market intelligence
- **Explains** why information matters, not just what happened
- **Learns** your workflow and becomes more helpful over time

---

## Features

### Natural Conversations
No commands to remember. Just type what you need in plain English.

```
You: What's Apple's stock price?
Atlas: AAPL is trading at $195.89, up 1.23% today...

You: How does it compare to Microsoft?
Atlas: Here's a side-by-side comparison...
```

### Company Research
Deep company analysis powered by AI with real-time financial data.

- Stock prices, P/E ratios, market cap, 52-week ranges
- Earnings history and upcoming earnings dates
- SEC filing search and analysis
- Company news and market sentiment

### Intelligent Watchlist
Track the stocks that matter to you with personalized monitoring.

```
You: Add AAPL, NVDA, TSLA to my watchlist
Atlas: Done! I'm now tracking 3 stocks for you.
       I'll notify you of significant movements (>5%).
```

### Price Alerts
Set custom alerts and get notified instantly.

```
You: Alert me when NVDA hits $500
Atlas: Done! I'll notify you when NVIDIA reaches $500.

You: Alert me if TSLA drops 5% in a day
Atlas: Alert set for Tesla 5% daily movement.
```

### Daily Briefings
Personalized morning and evening market summaries delivered to your Telegram.

**Morning Briefing includes:**
- Market overview (S&P 500, Dow, NASDAQ, VIX)
- Your watchlist performance
- Top financial news
- Upcoming earnings on your watchlist

### Document Intelligence
Upload financial documents and ask questions about them.

```
You: [Uploads annual report.pdf]
Atlas: Document processed! Here's the summary...
       You can now ask me questions about this document.

You: What were the key risk factors?
Atlas: Based on the document, the main risk factors are...
```

### Voice & Image Support
Interact using voice messages or share screenshots of financial charts.

- **Voice**: Speak naturally, Atlas transcribes and responds
- **Images**: Share charts, graphs, or tables for instant analysis

### Proactive Intelligence
Atlas doesn't wait for you to ask. It monitors and suggests.

- Significant price movements on your watchlist
- Upcoming earnings reminders
- Market-moving news alerts
- Follow-up questions based on your conversations

---

## Architecture

Atlas follows **Domain-Driven Design** with clean separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                     TELEGRAM BOT LAYER                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Text    │  │  Voice   │  │  Photo   │  │  Document│       │
│  │ Handler  │  │ Handler  │  │ Handler  │  │ Handler  │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       └──────────────┴──────────────┴──────────────┘            │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                   APPLICATION LAYER                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 AI ORCHESTRATOR                          │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │   Intent    │  │   Context    │  │   Response   │  │   │
│  │  │ Classifier  │  │   Manager    │  │  Generator   │  │   │
│  │  └─────────────┘  └──────────────┘  └──────────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Onboarding  │  │  Watchlist   │  │    Alert     │          │
│  │  Use Case   │  │  Use Case    │  │  Use Case    │          │
│  └─────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                   DOMAIN LAYER                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Abstract  │  │   Abstract   │  │   Abstract   │          │
│  │  Services   │  │ Repositories │  │    Models    │          │
│  └─────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Stock   │  │   News   │  │  Market  │  │   SEC    │       │
│  │ Service  │  │ Service  │  │ Service  │  │  EDGAR   │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Cache   │  │   AI     │  │ Database │  │ Telegram │       │
│  │ (Redis)  │  │ (MiMo)   │  │ (SQLite) │  │   Bot    │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Purpose |
|-----------|---------|
| **AI Orchestrator** | Coordinates intent classification, context assembly, and response generation |
| **Intent Classifier** | Hybrid classification using keywords, regex, and AI fallback |
| **Context Manager** | Maintains working memory and compressed conversation history |
| **Response Generator** | Role-adaptive prompts with financial reasoning |
| **Briefing Compiler** | Generates personalized market summaries |
| **Alert Monitor** | Background monitoring for price alerts |
| **News Aggregator** | Multi-source news with sentiment enrichment |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.13 + FastAPI |
| **AI Models** | MiMo (primary) → OpenAI GPT-4 → Ollama (fallback) |
| **Database** | SQLite + SQLAlchemy (async) |
| **Cache** | In-memory L1 + Redis L2 |
| **Financial Data** | Yahoo Finance (yfinance) + SEC EDGAR |
| **News** | RSS feeds (Yahoo Finance, MarketWatch, Investing.com) |
| **Telegram** | python-telegram-bot v20 |
| **Scheduling** | APScheduler (cron-based) |
| **Voice** | OpenAI Whisper + local fallback |
| **Documents** | PyPDF2 + pandas |

---

## Quick Start

### Prerequisites

- Python 3.13+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- OpenAI API key (optional - MiMo is free)

### Installation

```bash
# Clone the repository
git clone https://github.com/Ankit500ak/ATLAS-AI.git
cd ATLAS-AI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Create a `.env` file with your credentials:

```env
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Optional (MiMo is free and works without these)
OPENAI_API_KEY=your_openai_key
OPENCODE_ZEN_API_KEY=your_zen_key

# Optional - Google Integrations
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

### Run

```bash
python run.py
```

The bot will start polling Telegram for messages. Open Telegram, find your bot, and say hello!

---

## Usage

### Onboarding

When a user first interacts with Atlas, it guides them through a conversational onboarding:

1. **Role Selection** - "I'm an investor" / "I'm an analyst" / etc.
2. **Sector Interests** - "Technology, Healthcare, Finance"
3. **Watchlist Setup** - "Add AAPL, NVDA, TSLA"
4. **Notification Preferences** - "Earnings alerts, market news"
5. **Briefing Schedule** - "8:00 AM daily"
6. **Google Connect** - Optional Gmail/Calendar/Drive/Sheets

### Example Conversations

**Market Research:**
```
You: What's happening in the market today?
Atlas: Market is open! Here's your overview:

🟢 S&P 500: 5,234.18 (+0.45%)
🟢 NASDAQ: 16,428.82 (+0.83%)
🔴 VIX: 14.2 (-2.1%)

Top news: Fed signals potential rate cut...
```

**Company Analysis:**
```
You: Research NVIDIA
Atlas: Here's NVIDIA (NVDA) at a glance:

Price: $875.28 (+3.2%)
Market Cap: $2.15T
P/E Ratio: 72.4
EPS: $12.09

Key highlights:
• AI demand continues to drive growth
• Data center revenue up 409% YoY...
```

**Competitor Comparison:**
```
You: Compare Microsoft and Google
Atlas: Here's a side-by-side comparison:

| Metric | MSFT | GOOGL |
|--------|------|-------|
| Price | $420.55 | $175.98 |
| P/E | 37.2 | 25.8 |
| Market Cap | $3.1T | $2.2T |

Key Differences:
• Microsoft leads in cloud (Azure)...
```

**Price Alerts:**
```
You: Alert me if Apple drops below $180
Atlas: Done! Alert set for AAPL < $180.
       I'll notify you immediately when triggered.
```

**Document Analysis:**
```
You: [Uploads 10-K filing]
Atlas: Document processed: Apple Inc. 10-K

Summary: Apple's fiscal year showed...
Key insights:
• Revenue: $383B (+2% YoY)
• Services growth: 16%
• iPhone revenue: $200B

Ask me anything about this document!
```

---

## API Reference

Atlas exposes a REST API for programmatic access:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint |
| `/health` | GET | Health check with background task status |
| `/api/v1/status` | GET | Operational status |
| `/api/v1/users` | POST | Create user |
| `/api/v1/users/{id}` | GET | Get user profile |
| `/api/v1/watchlist/{user_id}` | GET | Get user watchlist |
| `/api/v1/alerts/{user_id}` | GET | Get active alerts |
| `/api/v1/market/status` | GET | Market status |
| `/api/v1/market/indices` | GET | Market indices |
| `/api/v1/stocks/{symbol}` | GET | Stock data |
| `/api/v1/news/market` | GET | Market news |
| `/api/v1/news/stock/{symbol}` | GET | Stock-specific news |
| `/api/v1/earnings/upcoming` | GET | Upcoming earnings |
| `/api/v1/sec/search/{ticker}` | GET | SEC filing search |
| `/api/v1/google/auth-url` | GET | Google OAuth URL |
| `/api/v1/google/gmail` | GET | Gmail messages |

### Authentication

API requests require a Bearer token:

```bash
curl -H "Authorization: Bearer your_secret_key" http://localhost:8000/api/v1/status
```

In development mode, authentication is bypassed automatically.

---

## Deployment

### Docker

```bash
docker-compose up -d
```

### Heroku

```bash
heroku create atlas-ai-bot
git push heroku main
```

### Environment Variables for Production

```env
APP_ENV=production
DATABASE_URL=postgresql://user:pass@host/db
REDIS_URL=redis://host:6379/0
SECRET_KEY=your_production_secret
```

---

## Background Tasks

Atlas runs 7 background loops for proactive intelligence:

| Task | Interval | Purpose |
|------|----------|---------|
| Alert Monitor | 60s | Check price alerts during market hours |
| News Aggregator | 15min | Fetch and enrich news from RSS feeds |
| Market Status | 5min | Update market open/closed status |
| Profile Updates | 1hr | Update user interest profiles |
| Watchlist Monitor | 15min | Detect significant price movements (>5%) |
| Earnings Reminders | Daily | Send upcoming earnings notifications |
| Evening Summary | 4:05 PM ET | Send evening market recap |

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_core.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

---

## Project Structure

```
ATLAS-AI/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Pydantic settings
│   ├── database.py                # Async SQLAlchemy setup
│   ├── models/                    # SQLAlchemy models
│   ├── schemas/                   # Pydantic schemas
│   ├── domain/                    # Domain layer
│   │   ├── services/              # Abstract service interfaces
│   │   └── repositories/          # Abstract repository interfaces
│   ├── infrastructure/            # Infrastructure implementations
│   │   ├── ai/                    # AI service (MiMo/OpenAI/Ollama)
│   │   ├── database/              # Repository implementations
│   │   ├── financial/             # Stock, News, Market, SEC services
│   │   └── messaging/             # Telegram bot implementation
│   ├── services/                  # Business logic
│   │   ├── ai/                    # Intent classifier, orchestrator, prompts
│   │   ├── background/            # Background task runner, scheduler
│   │   ├── conversation/          # Context manager, memory
│   │   ├── document/              # PDF/text/CSV processor
│   │   ├── financial/             # Financial data services
│   │   ├── integrations/          # Google Workspace integration
│   │   ├── personalization/       # User profiler, watchlist, suggestions
│   │   └── telegram/              # Voice processor, alternative bot
│   ├── application/               # Application layer
│   │   ├── use_cases/             # Message processor use case
│   │   └── dto/                   # Data transfer objects
│   ├── api/v1/                    # REST API endpoints
│   ├── core/                      # Cross-cutting concerns
│   │   ├── di/                    # Dependency injection container
│   │   ├── security.py            # API key authentication
│   │   ├── rate_limiter.py        # Rate limiting middleware
│   │   └── exceptions.py          # Custom exceptions
│   └── utils/                     # Formatters, validators
├── tests/                         # Unit and integration tests
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Container configuration
├── docker-compose.yml             # Docker Compose setup
├── pyproject.toml                 # Project configuration
└── run.py                         # Application launcher
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with passion for the Atlas AI Hackathon**

</div>
