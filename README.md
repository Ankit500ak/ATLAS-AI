<div align="center">

<img src="https://img.shields.io/badge/-ATLAS%20AI-0A0E27?style=for-the-badge&labelColor=0A0E27" height="60" alt="Atlas AI"/>

# 🧠 ATLAS AI
### Your Financial Intelligence, Living Inside Telegram

*Bloomberg terminal. SEC filings. News wires. Spreadsheets. One chat.*

<br/>

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://telegram.org)
[![License](https://img.shields.io/badge/License-MIT-3FB950?style=for-the-badge)](LICENSE)

<br/>

**[✨ Features](#-features)** · **[🏗️ Architecture](#️-architecture)** · **[🔄 How It Works](#-how-a-message-travels)** · **[📱 Interface](#-what-it-looks-like)** · **[🚀 Quick Start](#-quick-start)** · **[📡 API](#-api-reference)** · **[🐳 Deployment](#-deployment)**

</div>

<br/>

> Finance professionals lose hours every day bouncing between terminals, filings, news tabs, and spreadsheets. **Atlas AI collapses all of it into one conversation** — the one you already have open, on the app you already use.

Atlas isn't a Q&A bot. It's a financial analyst that:

| | |
|---|---|
| 🧩 **Remembers** | your role, watchlist, and every past conversation |
| 📡 **Reaches out** | with market-moving intelligence before you ask |
| 🗣️ **Explains** | *why* something matters, not just *what* happened |
| 📈 **Adapts** | its workflow to how you actually work |

<br/>

---

## ✨ Features

<table>
<tr>
<td width="50%" valign="top">

### 💬 Natural Conversation
No commands. No syntax. Just talk to it.

```
You    → What's Apple's stock price?
Atlas  → AAPL is trading at $195.89,
         up 1.23% today...

You    → How does it compare to Microsoft?
Atlas  → Here's a side-by-side comparison...
```

</td>
<td width="50%" valign="top">

### 🔍 Deep Company Research
Real-time data fused with AI-generated insight.

- Live price, P/E, market cap, 52-wk range
- Earnings history + upcoming dates
- SEC filing search & summarization
- News sentiment, distilled

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 👁️ Intelligent Watchlist
```
You    → Add AAPL, NVDA, TSLA to my
         watchlist
Atlas  → Done! Tracking 3 stocks.
         I'll flag moves over 5%.
```

</td>
<td width="50%" valign="top">

### 🔔 Custom Price Alerts
```
You    → Alert me if TSLA drops
         5% in a day
Atlas  → Alert set for Tesla —
         5% daily move.
```

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 🌅 Daily Briefings
Morning & evening market recaps, delivered — not requested.

- Index snapshot (S&P · Dow · NASDAQ · VIX)
- Your watchlist, overnight
- Top financial headlines
- Earnings landing this week

</td>
<td width="50%" valign="top">

### 📄 Document Intelligence
```
You    → [uploads annual_report.pdf]
Atlas  → Processed! Ask me anything
         about this document.

You    → What were the key risks?
Atlas  → The main risk factors are...
```

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 🎙️ Voice & Image Input
Speak or screenshot — Atlas reads either.

- **Voice** → transcribed & answered naturally
- **Images** → charts, tables, screenshots parsed instantly

</td>
<td width="50%" valign="top">

### 📡 Proactive Intelligence
Atlas watches the market so you don't have to.

- Sharp moves on your watchlist
- Earnings-date reminders
- Breaking news that moves your names
- Smart follow-ups from past chats

</td>
</tr>
</table>

<br/>

---

## 🏗️ Architecture

Atlas is built on **Domain-Driven Design** — four clean layers, each with one job, talking only to the layer beside it.

```
╔══════════════════════════════════════════════════════════════════════════╗
║  📱  TELEGRAM BOT LAYER                                                   ║
║ ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐            ║
║ │   TEXT    │   │  VOICE 🎙️  │   │  PHOTO 📷  │   │ DOCUMENT 📄│            ║
║ │  Handler  │   │  Handler  │   │  Handler  │   │  Handler  │            ║
║ └─────┬─────┘   └─────┬─────┘   └─────┬─────┘   └─────┬─────┘            ║
║       └───────────────┴───────────────┴───────────────┘                 ║
╚══════════════════════════════════╤════════════════════════════════════════╝
                                    │  raw user input
╔═══════════════════════════════════▼═══════════════════════════════════════╗
║  ⚙️  APPLICATION LAYER                                                     ║
║ ┌─────────────────────────────────────────────────────────────────────┐ ║
║ │                        🧠 AI ORCHESTRATOR                            │ ║
║ │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐            │ ║
║ │  │   INTENT     │──▶│   CONTEXT    │──▶│   RESPONSE   │            │ ║
║ │  │  Classifier  │   │   Manager    │   │  Generator   │            │ ║
║ │  └──────────────┘   └──────────────┘   └──────────────┘            │ ║
║ └─────────────────────────────────────────────────────────────────────┘ ║
║      │                        │                        │                 ║
║      ▼                        ▼                        ▼                 ║
║ ┌───────────┐          ┌───────────┐           ┌───────────┐            ║
║ │Onboarding │          │ Watchlist │           │   Alert   │            ║
║ │ Use Case  │          │ Use Case  │           │ Use Case  │            ║
║ └───────────┘          └───────────┘           └───────────┘            ║
╚══════════════════════════════════╤════════════════════════════════════════╝
                                    │  domain calls
╔═══════════════════════════════════▼═══════════════════════════════════════╗
║  🧬  DOMAIN LAYER   (pure abstractions — no I/O, no frameworks)           ║
║ ┌────────────────┐   ┌────────────────┐   ┌────────────────┐            ║
║ │    Abstract     │   │    Abstract     │   │    Abstract     │            ║
║ │    Services      │   │  Repositories    │   │     Models       │            ║
║ └────────────────┘   └────────────────┘   └────────────────┘            ║
╚══════════════════════════════════╤════════════════════════════════════════╝
                                    │  implemented by
╔═══════════════════════════════════▼═══════════════════════════════════════╗
║  🔌  INFRASTRUCTURE LAYER                                                  ║
║ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  ║
║ │ Stock   │ │  News   │ │ Market  │ │   SEC   │ │  Cache  │ │   AI    │  ║
║ │Service │ │Service │ │Service │ │  EDGAR  │ │(Redis) │ │(MiMo) │  ║
║ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  ║
║ ┌─────────┐ ┌───────────────┐                                            ║
║ │Database │ │   Telegram    │                                            ║
║ │(SQLite)│ │      Bot        │                                            ║
║ └─────────┘ └───────────────┘                                            ║
╚═════════════════════════════════════════════════════════════════════════╝
```

**Rule of the layers:** dependencies point *inward*. Infrastructure knows about Domain; Domain knows nothing about Infrastructure. Swap Redis for Memcached, or MiMo for GPT-4, and the Application layer never notices.

<br/>

### 🧩 Key Components

| Component | Role |
|---|---|
| 🧠 **AI Orchestrator** | Coordinates intent classification, context assembly, and response generation end-to-end |
| 🎯 **Intent Classifier** | Hybrid pipeline — keywords → regex → AI fallback, cheapest check first |
| 🗂️ **Context Manager** | Maintains rolling working memory + compressed conversation history |
| ✍️ **Response Generator** | Role-adaptive prompting with grounded financial reasoning |
| 🌅 **Briefing Compiler** | Assembles the personalized morning / evening market brief |
| ⏱️ **Alert Monitor** | Background watcher polling live prices against user-set triggers |
| 📰 **News Aggregator** | Multi-source RSS ingestion enriched with sentiment scoring |

<br/>

---

## 🔄 How a Message Travels

What actually happens between you hitting *send* and Atlas replying:

```
 YOU (Telegram)                                                
    │  "Alert me if TSLA drops 5%"                             
    ▼                                                          
 ① TEXT HANDLER            captures the raw message              
    │                                                          
    ▼                                                          
 ② INTENT CLASSIFIER       keyword/regex hit → "create_alert"    
    │                      (AI fallback only if ambiguous)       
    ▼                                                          
 ③ CONTEXT MANAGER         pulls user profile + watchlist + history
    │                                                          
    ▼                                                          
 ④ ALERT USE CASE          validates ticker, threshold, direction 
    │                                                          
    ▼                                                          
 ⑤ INFRASTRUCTURE          Stock Service confirms TSLA is live     
    │                      Database persists the new alert rule    
    ▼                                                          
 ⑥ RESPONSE GENERATOR      drafts a natural-language confirmation  
    │                                                          
    ▼                                                          
 ATLAS (Telegram)          "Alert set for Tesla — 5% daily move." 
```

**Meanwhile, in the background — every 60 seconds:**

```
⏱️  Alert Monitor wakes up
      │
      ▼
📡  Fetches live prices for every active alert (Stock Service)
      │
      ▼
🔎  Compares price → threshold
      │
      ├── not triggered ──▶ sleep, check again in 60s
      │
      └── triggered ──▶ 🧠 Response Generator drafts the alert
                              │
                              ▼
                         📲 Pushed straight to your Telegram
```

<br/>

---

## 📱 What It Looks Like

Atlas has no separate app to download and no dashboard to learn — the **GUI is the chat you already have open**. No new UI to onboard onto, no context switch, no second window.

<div align="center">
<sub><b>Morning briefing → follow-up comparison, inside one thread</b></sub>
</div>

```
┌───────────────────────────────────────────┐
│  ‹   🧠  Atlas AI                🟢 online │
│      Financial Intelligence                │
├───────────────────────────────────────────┤
│                                             │
│  ╭───────────────────────────────────╮     │
│  │ ☀️  Good morning — here's your      │     │
│  │     brief for Mon, Aug 10           │     │
│  │  ─────────────────────────────      │     │
│  │  🟢 S&P 500    5,234.18   +0.45%    │     │
│  │  🟢 NASDAQ    16,428.82   +0.83%    │     │
│  │  🔴 VIX           14.20   −2.10%    │     │
│  │  ─────────────────────────────      │     │
│  │  📋 YOUR WATCHLIST                   │     │
│  │   AAPL   $195.89     ▲ +1.23%       │     │
│  │   NVDA   $875.28     ▲ +3.20%       │     │
│  │   TSLA   $241.10     ▼ −0.44%       │     │
│  │  ─────────────────────────────      │     │
│  │  📰 TOP STORY                        │     │
│  │   Fed signals potential rate cut    │     │
│  │  ─────────────────────────────      │     │
│  │  📅 THIS WEEK                        │     │
│  │   NVDA reports Thu, after close     │     │
│  ╰───────────────────────────────────╯ 8:00 │
│                                             │
│                    ╭─────────────────────╮ │
│                    │ How's that vs MSFT? │ │
│                    ╰─────────────────────╯ │
│                                       8:03  │
│                                             │
│  ╭───────────────────────────────────╮     │
│  │ 📊  NVDA  ⇄  MSFT                   │     │
│  │  ─────────────────────────────      │     │
│  │              NVDA         MSFT      │     │
│  │   Price     $875.28     $420.55     │     │
│  │   P/E         72.4         37.2     │     │
│  │   Mkt Cap   $2.15T       $3.10T     │     │
│  │  ─────────────────────────────      │     │
│  │  Microsoft leads on cloud scale     │     │
│  │  (Azure); NVIDIA leads on AI        │     │
│  │  demand growth...                   │     │
│  ╰───────────────────────────────────╯ 8:03 │
│                                             │
├───────────────────────────────────────────┤
│   🎙️     📎     Type a message…      ➤     │
└───────────────────────────────────────────┘
```

<div align="center">
<sub><b>A proactive alert firing mid-conversation — no prompt required</b></sub>
</div>

```
┌───────────────────────────────────────────┐
│  ‹   🧠  Atlas AI                🟢 online │
├───────────────────────────────────────────┤
│                                             │
│  ╭───────────────────────────────────╮     │
│  │ 🔔  ALERT TRIGGERED                  │     │
│  │  ─────────────────────────────      │     │
│  │  TSLA just dropped 5.1% today —     │     │
│  │  now trading at $228.90.            │     │
│  │                                       │     │
│  │  Move looks tied to a delivery      │     │
│  │  guidance cut announced this AM.    │     │
│  │                                       │     │
│  │  Want the full story, or should     │     │
│  │  I check your other positions?      │     │
│  ╰───────────────────────────────────╯ 11:42│
│                                             │
├───────────────────────────────────────────┤
│   🎙️     📎     Type a message…      ➤     │
└───────────────────────────────────────────┘
```

### 🎨 Visual language

Atlas keeps every message legible at a glance — color and iconography carry meaning consistently, so you can skim a busy morning brief in seconds.

| Signal | Meaning |
|---|---|
| 🟢 / ▲ | Price or index up |
| 🔴 / ▼ | Price or index down |
| 📋 | Watchlist block |
| 📰 | News / headline |
| 📅 | Earnings / calendar event |
| 🔔 | Proactive alert, unprompted |
| 📊 | Comparison / analysis block |
| ╭─╮ ╰─╯ | Atlas message bubble |

### 🧭 Onboarding, in six turns

```
①  "I'm an investor"          ─────▶  role selection
②  "Tech, Healthcare, Finance" ────▶  sector interests
③  "Add AAPL, NVDA, TSLA"      ────▶  watchlist seeded
④  "Earnings + market news"    ────▶  notification prefs
⑤  "8:00 AM daily"             ────▶  briefing schedule
⑥  "Connect Google"  (optional)────▶  Gmail · Calendar · Drive · Sheets
```

<br/>

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| 🐍 **Backend** | Python 3.13 + FastAPI |
| 🧠 **AI Models** | MiMo *(primary)* → OpenAI GPT-4 → Ollama *(local fallback)* |
| 🗄️ **Database** | SQLite + SQLAlchemy *(async)* |
| ⚡ **Cache** | In-memory L1 + Redis L2 |
| 📈 **Financial Data** | Yahoo Finance (`yfinance`) + SEC EDGAR |
| 📰 **News** | RSS — Yahoo Finance, MarketWatch, Investing.com |
| 💬 **Telegram** | `python-telegram-bot` v20 |
| ⏰ **Scheduling** | APScheduler *(cron-based)* |
| 🎙️ **Voice** | OpenAI Whisper + local fallback |
| 📄 **Documents** | PyPDF2 + pandas |

<br/>

---

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- OpenAI API key *(optional — MiMo is free)*

### Installation

```bash
# Clone the repository
git clone https://github.com/Ankit500ak/ATLAS-AI.git
cd ATLAS-AI

# Create a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# now edit .env with your keys
```

### Configuration

```env
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Optional — MiMo works out of the box without these
OPENAI_API_KEY=your_openai_key
OPENCODE_ZEN_API_KEY=your_zen_key

# Optional — Google Workspace integrations
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

### Run

```bash
python run.py
```

Atlas starts polling Telegram immediately. Open the app, find your bot, and say hello. 👋

<br/>

---

## 📡 API Reference

Atlas exposes a full REST surface for programmatic access.

| Endpoint | Method | Description |
|---|---|---|
| `/` | `GET` | Root endpoint |
| `/health` | `GET` | Health check + background task status |
| `/api/v1/status` | `GET` | Operational status |
| `/api/v1/users` | `POST` | Create user |
| `/api/v1/users/{id}` | `GET` | Get user profile |
| `/api/v1/watchlist/{user_id}` | `GET` | Get user watchlist |
| `/api/v1/alerts/{user_id}` | `GET` | Get active alerts |
| `/api/v1/market/status` | `GET` | Market status |
| `/api/v1/market/indices` | `GET` | Market indices |
| `/api/v1/stocks/{symbol}` | `GET` | Stock data |
| `/api/v1/news/market` | `GET` | Market news |
| `/api/v1/news/stock/{symbol}` | `GET` | Stock-specific news |
| `/api/v1/earnings/upcoming` | `GET` | Upcoming earnings |
| `/api/v1/sec/search/{ticker}` | `GET` | SEC filing search |
| `/api/v1/google/auth-url` | `GET` | Google OAuth URL |
| `/api/v1/google/gmail` | `GET` | Gmail messages |

**Authentication**

```bash
curl -H "Authorization: Bearer your_secret_key" \
     http://localhost:8000/api/v1/status
```

> In development mode, authentication is bypassed automatically.

<br/>

---

## ⏱️ Background Tasks

Seven loops keep Atlas proactive around the clock:

| Task | Interval | Purpose |
|---|---|---|
| 🔔 Alert Monitor | 60s | Check price alerts during market hours |
| 📰 News Aggregator | 15 min | Fetch & enrich news from RSS feeds |
| 📊 Market Status | 5 min | Refresh market open/closed state |
| 👤 Profile Updates | 1 hr | Update user interest profiles |
| 👁️ Watchlist Monitor | 15 min | Detect moves >5% on tracked tickers |
| 📅 Earnings Reminders | Daily | Notify on upcoming earnings |
| 🌆 Evening Summary | 4:05 PM ET | Send the evening market recap |

<br/>

---

## 🐳 Deployment

### Docker
```bash
docker-compose up -d
```

### Heroku
```bash
heroku create atlas-ai-bot
git push heroku main
```

### Production environment
```env
APP_ENV=production
DATABASE_URL=postgresql://user:pass@host/db
REDIS_URL=redis://host:6379/0
SECRET_KEY=your_production_secret
```

<br/>

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run a specific file
pytest tests/unit/test_core.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

<br/>

---

## 📁 Project Structure

```
ATLAS-AI/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Pydantic settings
│   ├── database.py                # Async SQLAlchemy setup
│   ├── models/                    # SQLAlchemy models
│   ├── schemas/                   # Pydantic schemas
│   │
│   ├── domain/                    # 🧬 Domain layer
│   │   ├── services/              #   abstract service interfaces
│   │   └── repositories/          #   abstract repository interfaces
│   │
│   ├── infrastructure/            # 🔌 Infrastructure layer
│   │   ├── ai/                    #   MiMo / OpenAI / Ollama
│   │   ├── database/              #   repository implementations
│   │   ├── financial/             #   Stock, News, Market, SEC services
│   │   └── messaging/             #   Telegram bot implementation
│   │
│   ├── services/                  # ⚙️ Business logic
│   │   ├── ai/                    #   intent classifier, orchestrator, prompts
│   │   ├── background/            #   task runner, scheduler
│   │   ├── conversation/          #   context manager, memory
│   │   ├── document/              #   PDF / text / CSV processor
│   │   ├── financial/             #   financial data services
│   │   ├── integrations/          #   Google Workspace integration
│   │   ├── personalization/       #   user profiler, watchlist, suggestions
│   │   └── telegram/              #   voice processor, alternative bot
│   │
│   ├── application/                # 🧩 Application layer
│   │   ├── use_cases/              #   message processor use case
│   │   └── dto/                    #   data transfer objects
│   │
│   ├── api/v1/                    # 📡 REST API endpoints
│   ├── core/                      # Cross-cutting concerns
│   │   ├── di/                    #   dependency injection container
│   │   ├── security.py            #   API key authentication
│   │   ├── rate_limiter.py        #   rate limiting middleware
│   │   └── exceptions.py          #   custom exceptions
│   └── utils/                     # Formatters, validators
│
├── tests/                         # Unit and integration tests
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container configuration
├── docker-compose.yml              # Docker Compose setup
├── pyproject.toml                  # Project configuration
└── run.py                          # Application launcher
```

<br/>

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch — `git checkout -b feature/amazing-feature`
3. Commit your changes — `git commit -m 'Add amazing feature'`
4. Push the branch — `git push origin feature/amazing-feature`
5. Open a Pull Request

<br/>

---

## 💛 Thank You

Atlas AI started as a hackathon idea and grew into something we're genuinely proud of. If you've read this far, tried the bot, filed an issue, or even just starred the repo — **thank you**. Projects like this move forward because people show up for them.

<div align="center">

```
   ┌─────────────────────────────────────────┐
   │                                           │
   │      🧠  Thanks for building with us      │
   │                                           │
   │   Every PR, issue, and idea makes         │
   │        Atlas a little smarter.            │
   │                                           │
   └─────────────────────────────────────────┘
```

</div>

<br/>

## 📬 Contact & Contributions

Want to contribute, report a bug, or just talk shop about financial AI? Reach out — we'd love to hear from you.

<div align="center">

[![GitHub Issues](https://img.shields.io/badge/Issues-Report%20a%20Bug-EA4335?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Ankit500ak/ATLAS-AI/issues)
[![GitHub Discussions](https://img.shields.io/badge/Discussions-Ask%20a%20Question-6E40C9?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Ankit500ak/ATLAS-AI/discussions)
[![Pull Requests](https://img.shields.io/badge/PRs-Welcome-3FB950?style=for-the-badge&logo=git&logoColor=white)](https://github.com/Ankit500ak/ATLAS-AI/pulls)

**Maintainer:** [@Ankit500ak](https://github.com/Ankit500ak)

</div>

Contribution paths that are always welcome:

| Type | Where to start |
|---|---|
| 🐛 **Bug reports** | Open an [issue](https://github.com/Ankit500ak/ATLAS-AI/issues) with steps to reproduce |
| 💡 **Feature ideas** | Start a [discussion](https://github.com/Ankit500ak/ATLAS-AI/discussions) before opening a PR |
| 🔧 **Code contributions** | Fork → branch → PR (see steps above) |
| 📖 **Docs & examples** | Typos, clarity fixes, and new usage examples always help |

<br/>

<div align="center">

**Built with passion for the Atlas AI Hackathon** 🚀

<sub>Atlas AI · Finance, at the speed of conversation</sub>

</div>
