<div align="center">

<br/>

# ATLAS AI

<img src="https://img.shields.io/badge/finance%20%C3%97%20AI%20%C3%97%20telegram-000000?style=flat-square" alt="tags"/>

### The Bloomberg terminal, the SEC filings, the news wire, and the spreadsheet — collapsed into one Telegram thread.

<br/>

<p>
<img src="https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.13"/>
<img src="https://img.shields.io/badge/FastAPI-0.104-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"/>
<img src="https://img.shields.io/badge/Telegram-Bot%20API-26A5E4?style=flat-square&logo=telegram&logoColor=white" alt="Telegram"/>
<img src="https://img.shields.io/badge/PRs-welcome-3FB950?style=flat-square" alt="PRs welcome"/>
</p>

<sub>
<a href="#features">Features</a> ·
<a href="#architecture">Architecture</a> ·
<a href="#how-it-works">How it works</a> ·
<a href="#inside-the-conversation">Interface</a> ·
<a href="#quick-start">Quick start</a> ·
<a href="#api-reference">API</a> ·
<a href="#deployment">Deployment</a> ·
<a href="#contact--contributions">Contact</a>
</sub>

</div>

<br/>

> Finance professionals lose hours a day switching between terminals, filings, news tabs, and spreadsheets. Atlas AI removes the switching — it brings live market data, document intelligence, and proactive alerts into the chat app already open on your phone.

Atlas isn't a lookup bot. It's built to behave like an analyst who's paying attention:

<div align="center">

| | | |
|:---:|:---:|:---:|
| **Remembers** <br/> your role, watchlist, and history | **Reaches out** <br/> before you have to ask | **Explains** <br/> *why* it matters, not just *what* happened |

</div>

<br/>

## Features

<table>
<tr>
<td width="50%" valign="top">

**Natural conversation**
No commands or syntax — plain English in, plain English out.

</td>
<td width="50%" valign="top">

**Deep company research**
Live price, P/E, market cap, 52-week range, earnings history, and SEC filing search in one reply.

</td>
</tr>
<tr>
<td width="50%" valign="top">

**Intelligent watchlist**
Track what matters; Atlas flags any move over 5% without being asked.

</td>
<td width="50%" valign="top">

**Custom price alerts**
Threshold, direction, or percentage-move triggers — set once, notified instantly.

</td>
</tr>
<tr>
<td width="50%" valign="top">

**Daily briefings**
A personalized morning and evening market summary, delivered on schedule.

</td>
<td width="50%" valign="top">

**Document intelligence**
Upload a 10-K, earnings deck, or report — then ask it questions directly.

</td>
</tr>
<tr>
<td width="50%" valign="top">

**Voice & image input**
Speak naturally or drop a chart screenshot; Atlas reads either.

</td>
<td width="50%" valign="top">

**Proactive intelligence**
Watchlist swings, earnings reminders, and breaking news — surfaced, not requested.

</td>
</tr>
</table>

<br/>

## Architecture

Atlas follows **Domain-Driven Design**: four layers, each with one responsibility, dependencies pointing strictly inward.

```mermaid
flowchart TB
    subgraph L1["TELEGRAM BOT LAYER"]
        direction LR
        T1["Text Handler"] ~~~ T2["Voice Handler"] ~~~ T3["Photo Handler"] ~~~ T4["Document Handler"]
    end

    subgraph L2["APPLICATION LAYER"]
        direction TB
        subgraph ORCH["AI Orchestrator"]
            direction LR
            IC["Intent Classifier"] --> CM["Context Manager"] --> RG["Response Generator"]
        end
        subgraph UC[" "]
            direction LR
            U1["Onboarding Use Case"] ~~~ U2["Watchlist Use Case"] ~~~ U3["Alert Use Case"]
        end
        ORCH --> UC
    end

    subgraph L3["DOMAIN LAYER — pure abstractions"]
        direction LR
        D1["Abstract Services"] ~~~ D2["Abstract Repositories"] ~~~ D3["Abstract Models"]
    end

    subgraph L4["INFRASTRUCTURE LAYER"]
        direction LR
        I1["Stock Service"] ~~~ I2["News Service"] ~~~ I3["Market Service"] ~~~ I4["SEC EDGAR"]
        I5["Cache · Redis"] ~~~ I6["AI · MiMo"] ~~~ I7["Database · SQLite"] ~~~ I8["Telegram Bot"]
    end

    L1 --> L2 --> L3 --> L4

    style L1 fill:#0A0E27,color:#fff,stroke:#26A5E4,stroke-width:2px
    style L2 fill:#12163a,color:#fff,stroke:#7c5cff,stroke-width:2px
    style L3 fill:#1a1f4b,color:#fff,stroke:#3FB950,stroke-width:2px
    style L4 fill:#0A0E27,color:#fff,stroke:#f0883e,stroke-width:2px
```

**The rule that keeps this maintainable:** infrastructure knows about the domain layer; the domain layer knows nothing about infrastructure. Swap Redis for Memcached, or MiMo for GPT-4, and the application layer never has to change.

### Key components

| Component | Role |
|---|---|
| **AI Orchestrator** | Coordinates intent classification, context assembly, and response generation end-to-end |
| **Intent Classifier** | Hybrid pipeline — keyword match → regex → AI fallback, cheapest check first |
| **Context Manager** | Maintains rolling working memory plus compressed conversation history |
| **Response Generator** | Role-adaptive prompting with grounded financial reasoning |
| **Briefing Compiler** | Assembles the personalized morning and evening market brief |
| **Alert Monitor** | Background watcher polling live prices against user-set triggers |
| **News Aggregator** | Multi-source RSS ingestion enriched with sentiment scoring |

<br/>

## How it works

**Foreground — a user request, end to end:**

```mermaid
sequenceDiagram
    participant U as User
    participant H as Text Handler
    participant IC as Intent Classifier
    participant CM as Context Manager
    participant UC as Alert Use Case
    participant DB as Database
    participant RG as Response Generator

    U->>H: "Alert me if TSLA drops 5%"
    H->>IC: classify intent
    IC-->>H: intent = create_alert
    H->>CM: load user profile + watchlist
    CM-->>H: context
    H->>UC: create alert(TSLA, -5%)
    UC->>DB: persist alert rule
    DB-->>UC: confirmed
    UC->>RG: draft confirmation
    RG-->>U: "Alert set for Tesla — 5% daily move."
```

**Background — every 60 seconds, unprompted:**

```mermaid
flowchart LR
    A["Alert Monitor wakes"] --> B["Fetch live prices\nfor active alerts"]
    B --> C{"Threshold\ncrossed?"}
    C -- no --> A
    C -- yes --> D["Response Generator\ndrafts the alert"]
    D --> E["Pushed to Telegram"]

    style A fill:#0A0E27,color:#fff,stroke:#26A5E4
    style B fill:#0A0E27,color:#fff,stroke:#26A5E4
    style C fill:#12163a,color:#fff,stroke:#7c5cff
    style D fill:#1a1f4b,color:#fff,stroke:#3FB950
    style E fill:#1a1f4b,color:#fff,stroke:#3FB950
```

<br/>

## Inside the conversation

Atlas has no separate dashboard — the interface is the chat itself.

**Morning briefing**

> **Atlas** · 8:00 AM
> Good morning. Here's your brief for Monday, August 10.
>
> **Markets** — S&P 500 5,234.18 (+0.45%) · NASDAQ 16,428.82 (+0.83%) · VIX 14.20 (−2.10%)
> **Watchlist** — AAPL $195.89 (+1.23%) · NVDA $875.28 (+3.20%) · TSLA $241.10 (−0.44%)
> **Top story** — Fed signals a potential rate cut
> **This week** — NVDA reports Thursday, after close

> **You** · 8:03 AM
> How's that vs MSFT?

> **Atlas** · 8:03 AM
> **NVDA vs. MSFT**
>
> | | NVDA | MSFT |
> |---|---|---|
> | Price | $875.28 | $420.55 |
> | P/E | 72.4 | 37.2 |
> | Market cap | $2.15T | $3.10T |
>
> Microsoft leads on cloud scale via Azure; NVIDIA leads on AI-driven demand growth.

**An alert, arriving without being asked**

> **Atlas** · 11:42 AM
> **Alert triggered — TSLA**
> Down 5.1% today, now trading at $228.90. The move looks tied to a delivery-guidance cut announced this morning.
>
> Want the full story, or should I check your other positions?

### Onboarding in six turns

| Step | You say | Atlas sets up |
|:---:|---|---|
| 1 | *"I'm an investor"* | Role selection |
| 2 | *"Tech, Healthcare, Finance"* | Sector interests |
| 3 | *"Add AAPL, NVDA, TSLA"* | Watchlist seeded |
| 4 | *"Earnings + market news"* | Notification preferences |
| 5 | *"8:00 AM daily"* | Briefing schedule |
| 6 | *"Connect Google"* (optional) | Gmail · Calendar · Drive · Sheets |

<br/>

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13 + FastAPI |
| AI models | MiMo (primary) → OpenAI GPT-4 → Ollama (local fallback) |
| Database | SQLite + SQLAlchemy (async) |
| Cache | In-memory L1 + Redis L2 |
| Financial data | Yahoo Finance (`yfinance`) + SEC EDGAR |
| News | RSS — Yahoo Finance, MarketWatch, Investing.com |
| Telegram | `python-telegram-bot` v20 |
| Scheduling | APScheduler (cron-based) |
| Voice | OpenAI Whisper + local fallback |
| Documents | PyPDF2 + pandas |

<br/>

## Quick start

**Prerequisites** — Python 3.13+, a Telegram bot token from [@BotFather](https://t.me/BotFather), and optionally an OpenAI API key (MiMo runs free by default).

```bash
# Clone and enter the repository
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

```bash
python run.py
```

Atlas starts polling Telegram immediately — open the app, find your bot, and say hello.

<br/>

## API reference

| Endpoint | Method | Description |
|---|:---:|---|
| `/` | GET | Root endpoint |
| `/health` | GET | Health check + background task status |
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

```bash
curl -H "Authorization: Bearer your_secret_key" \
     http://localhost:8000/api/v1/status
```

> In development mode, authentication is bypassed automatically.

<br/>

## Background tasks

Seven loops keep Atlas proactive around the clock.

| Task | Interval | Purpose |
|---|:---:|---|
| Alert Monitor | 60s | Check price alerts during market hours |
| News Aggregator | 15 min | Fetch and enrich news from RSS feeds |
| Market Status | 5 min | Refresh market open/closed state |
| Profile Updates | 1 hr | Update user interest profiles |
| Watchlist Monitor | 15 min | Detect moves over 5% on tracked tickers |
| Earnings Reminders | Daily | Notify on upcoming earnings |
| Evening Summary | 4:05 PM ET | Send the evening market recap |

<br/>

## Deployment

<table>
<tr>
<td width="50%" valign="top">

**Docker**
```bash
docker-compose up -d
```

</td>
<td width="50%" valign="top">

**Heroku**
```bash
heroku create atlas-ai-bot
git push heroku main
```

</td>
</tr>
</table>

```env
# Production environment
APP_ENV=production
DATABASE_URL=postgresql://user:pass@host/db
REDIS_URL=redis://host:6379/0
SECRET_KEY=your_production_secret
```

<br/>

## Testing

```bash
pytest tests/ -v                                  # run everything
pytest tests/unit/test_core.py -v                  # run one file
pytest tests/ --cov=app --cov-report=html           # with coverage
```

<br/>

## Project structure

```
ATLAS-AI/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py                # Pydantic settings
│   ├── database.py              # Async SQLAlchemy setup
│   ├── models/                  # SQLAlchemy models
│   ├── schemas/                 # Pydantic schemas
│   │
│   ├── domain/                  # Domain layer
│   │   ├── services/             #   abstract service interfaces
│   │   └── repositories/         #   abstract repository interfaces
│   │
│   ├── infrastructure/          # Infrastructure layer
│   │   ├── ai/                   #   MiMo / OpenAI / Ollama
│   │   ├── database/             #   repository implementations
│   │   ├── financial/            #   Stock, News, Market, SEC services
│   │   └── messaging/            #   Telegram bot implementation
│   │
│   ├── services/                # Business logic
│   │   ├── ai/                   #   intent classifier, orchestrator, prompts
│   │   ├── background/           #   task runner, scheduler
│   │   ├── conversation/         #   context manager, memory
│   │   ├── document/             #   PDF / text / CSV processor
│   │   ├── financial/            #   financial data services
│   │   ├── integrations/         #   Google Workspace integration
│   │   ├── personalization/      #   user profiler, watchlist, suggestions
│   │   └── telegram/             #   voice processor, alternative bot
│   │
│   ├── application/             # Application layer
│   │   ├── use_cases/            #   message processor use case
│   │   └── dto/                  #   data transfer objects
│   │
│   ├── api/v1/                  # REST API endpoints
│   ├── core/                    # Cross-cutting concerns
│   │   ├── di/                   #   dependency injection container
│   │   ├── security.py           #   API key authentication
│   │   ├── rate_limiter.py        #   rate limiting middleware
│   │   └── exceptions.py         #   custom exceptions
│   └── utils/                   # Formatters, validators
│
├── tests/                       # Unit and integration tests
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container configuration
├── docker-compose.yml             # Docker Compose setup
├── pyproject.toml                # Project configuration
└── run.py                        # Application launcher
```

<br/>

## Contributing

```bash
git checkout -b feature/amazing-feature   # 1. branch
git commit -m "Add amazing feature"       # 2. commit
git push origin feature/amazing-feature   # 3. push
```
Then open a Pull Request against `main`.

<br/>

---

<br/>

## Thank you

Atlas AI started as a hackathon idea and grew into something worth maintaining properly. If you've read this far, run the bot, filed an issue, or starred the repo — thank you. Projects like this move because people show up for them.

## Contact & contributions

<div align="center">

<p>
<a href="https://github.com/Ankit500ak/ATLAS-AI/issues"><img src="https://img.shields.io/badge/Issues-Report%20a%20Bug-EA4335?style=flat-square&logo=github&logoColor=white" alt="Issues"/></a>
<a href="https://github.com/Ankit500ak/ATLAS-AI/discussions"><img src="https://img.shields.io/badge/Discussions-Ask%20a%20Question-6E40C9?style=flat-square&logo=github&logoColor=white" alt="Discussions"/></a>
<a href="https://github.com/Ankit500ak/ATLAS-AI/pulls"><img src="https://img.shields.io/badge/PRs-Welcome-3FB950?style=flat-square&logo=git&logoColor=white" alt="PRs Welcome"/></a>
</p>

**Maintainer** — [@Ankit500ak](https://github.com/Ankit500ak)

</div>

| Want to... | Start here |
|---|---|
| Report a bug | Open an [issue](https://github.com/Ankit500ak/ATLAS-AI/issues) with steps to reproduce |
| Propose a feature | Start a [discussion](https://github.com/Ankit500ak/ATLAS-AI/discussions) before opening a PR |
| Contribute code | Fork → branch → PR, as above |
| Improve the docs | Typos, clarity fixes, and new examples are always welcome |

<br/>

<div align="center">
<sub>Built with passion for the Atlas AI Hackathon · Finance, at the speed of conversation</sub>
</div>
