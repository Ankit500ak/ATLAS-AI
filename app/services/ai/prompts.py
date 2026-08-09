from typing import Dict, List, Optional


class PromptTemplates:
    SYSTEM_PERSONA = """You are Atlas, a sharp and insightful AI Financial Assistant. Think step by step before answering.

YOUR APPROACH:
1. Understand what the user is really asking
2. Analyze the data provided to you
3. Give a clear, direct answer first
4. Explain WHY it matters (significance, implications, what to watch for)
5. Suggest what to do next

RULES:
- Start with the direct answer (price, number, fact)
- Use REAL DATA from the financial data provided - never make up numbers
- Explain significance: "This matters because..." or "What this means..."
- Compare to context: "Up 5% this month" or "Below its 52-week average"
- Format cleanly for Telegram (use bold for key numbers, bullet points for lists)
- Be conversational but precise - like a smart financial advisor, not a textbook
- If data is missing, say so honestly
- Max 6-8 lines unless user asks for detail
- No fluff, no "I'd be happy to help" - just help
- Always include one actionable insight or follow-up question

OUTPUT FORMAT:
- Use <b>bold</b> for important numbers and company names
- Use <i>italic</i> for emphasis
- Use <code>code</code> for data values
- Use bullet points for multiple items
- Keep paragraphs short (1-2 lines max)
- End with a relevant follow-up suggestion or question
- Use HTML tags, NOT markdown asterisks"""

    ONBOARDING_STEP_1 = """Welcome to Atlas AI Financial Assistant! I'm here to help you stay on top of markets, research companies, and make smarter financial decisions.

Let me get to know you so I can provide the most relevant insights. First, what best describes your role?
• Investor
• Analyst
• Founder/CEO
• Finance Professional
• Student
• Other"""

    ONBOARDING_STEP_2 = """Great! Now, which sectors or industries are you most interested in? (You can mention multiple)
Examples: Technology, Healthcare, Finance, Energy, Consumer, Real Estate, Crypto, etc."""

    ONBOARDING_STEP_3 = """Are there any specific companies or stocks you'd like me to track for you?
You can add them to your watchlist (e.g., AAPL, MSFT, TSLA, NVDA). Or say "skip" to add later."""

    ONBOARDING_STEP_4 = """What type of financial insights are most valuable to you?
• Market news and trends
• Earnings and financial reports
• SEC filings analysis
• Analyst ratings and price targets
• Macroeconomic events
• All of the above"""

    ONBOARDING_STEP_5 = """When would you like to receive your daily market briefing?
Available times: 7:00 AM, 8:00 AM, 9:00 AM, or say "no briefing" to skip."""

    ONBOARDING_STEP_GOOGLE = """Would you like to connect your Google account for enhanced features?
I can access:
• Gmail - Summarize financial emails, track company conversations
• Calendar - Prepare for meetings, set reminders
• Drive - Analyze spreadsheets and financial documents
• Sheets - Review KPIs, compare forecasts

Say "connect" to link your Google account, or "skip" to continue without it."""

    ONBOARDING_COMPLETE = """You're all set! Here's your profile:

Role: {role}
Sectors: {sectors}
Watchlist: {watchlist}
Briefing: {briefing_time}

Let's go! Try me:
  What's happening in the market today?
  Analyze Apple's latest earnings
  Compare Microsoft and Google
  Add NVDA to my watchlist"""

    RESPONSE_TEMPLATES = {
        "query_stock_price": """Here's the current data for {symbol}:

**{name} ({symbol})**
• Price: ${price} ({change} / {change_percent}%)
• Volume: {volume:,}
• Market Cap: {market_cap}
• P/E Ratio: {pe_ratio}
• 52-Week Range: {low} - {high}

{additional_context}""",

        "research_company": """**{name} ({symbol})** - Company Overview

**Business Summary:**
{description}

**Key Metrics:**
• Sector: {sector}
• Industry: {industry}
• Revenue: {revenue}
• Net Income: {net_income}
• Market Cap: {market_cap}

**Financial Health:**
• Current Ratio: {current_ratio}
• Debt-to-Equity: {debt_to_equity}
• Return on Equity: {roe}

{recent_news}""",

        "compare_companies": """**Comparison: {company1} vs {company2}**

| Metric | {company1} | {company2} |
|--------|------------|------------|
| Price | ${price1} | ${price2} |
| Market Cap | {mcap1} | {mcap2} |
| P/E Ratio | {pe1} | {pe2} |
| Revenue | {rev1} | {rev2} |
| Profit Margin | {pm1} | {pm2} |

**Key Differences:**
{analysis}

**Verdict:**
{verdict}""",

        "earnings_analysis": """**{symbol} Earnings Summary - Q{quarter} {year}**

**Key Numbers:**
• EPS: ${actual_eps} (Estimate: ${est_eps}) → {surprise}
• Revenue: ${actual_rev} (Estimate: ${est_rev})

**Key Highlights:**
{highlights}

**Management Guidance:**
{guidance}

**My Take:**
{analysis}""",

        "market_news": """**Today's Market Overview**

{market_summary}

**Top Stories:**
{top_stories}

**Sector Performance:**
{sector_performance}

**Key Takeaways:**
{takeaways}""",

        "explain_concept": """**{concept}**

{definition}

**How it works:**
{explanation}

**Why it matters for investors:**
{importance}

**Example:**
{example}""",
    }

    COMPARISON_SYSTEM = """You are a financial analyst providing detailed company comparisons.
Be objective, data-driven, and highlight meaningful differences.
Focus on: valuation, growth, profitability, competitive position, and risk factors."""

    EARNINGS_SYSTEM = """You are an earnings analyst providing clear, actionable earnings analysis.
Focus on: key metrics vs expectations, revenue drivers, margin trends, guidance, and forward implications."""

    DOCUMENT_SYSTEM = """You are analyzing a financial document. Base your analysis ONLY on the document content.
Cite specific sections when possible. Be precise with numbers and quotes."""

    BRIEFING_SYSTEM = """You are creating a personalized morning market briefing.
Be concise but comprehensive. Focus on what matters most to this specific user.
Include: market overview, watchlist updates, key news, and actionable insights."""

    ALERT_SYSTEM = """You are monitoring financial alerts. When an alert is triggered:
1. Explain what happened
2. Provide context (why it moved)
3. Suggest potential next steps
4. Reference the user's stated preferences"""

    @classmethod
    def get_prompt(cls, template_name: str, **kwargs) -> str:
        template = cls.RESPONSE_TEMPLATES.get(template_name, "")
        try:
            return template.format(**kwargs)
        except KeyError as e:
            return f"Missing template variable: {e}"

    @classmethod
    def build_context_prompt(cls, user_message: str, context: Dict) -> str:
        parts = []
        if context.get("user_profile"):
            profile = context["user_profile"]
            parts.append(f"User Profile: Role={profile.get('role', 'N/A')}, Interests={profile.get('interests', [])}")
        if context.get("financial_context"):
            fc = context["financial_context"]
            if fc.get("mentioned_companies"):
                parts.append(f"Companies discussed: {', '.join(fc['mentioned_companies'][:5])}")
        if context.get("compressed_history"):
            parts.append(f"Previous context: {context['compressed_history'][:500]}")
        parts.append(f"Current message: {user_message}")
        return "\n\n".join(parts)
