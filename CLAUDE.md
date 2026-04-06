# AI Hedge Fund - CLAUDE.md

## Project Overview

An AI-powered hedge fund proof-of-concept using LLM-based agents modeled after famous investors (Buffett, Munger, Wood, etc.) to analyze stocks and generate trading decisions. Paper-trading and backtesting only — **no real trades**.

## Architecture

### Multi-Agent DAG (LangGraph)

The core workflow is a directed acyclic graph:

```
start_node → [Analyst Agents (parallel)] → risk_management_agent → portfolio_manager → END
```

- `src/main.py` — CLI entry point, `create_workflow()` builds the `StateGraph` dynamically
- `src/backtester.py` — Historical backtesting entry point
- `src/graph/state.py` — `AgentState` TypedDict with `messages`, `data`, `metadata` fields

### Agent Categories

- **12 Investor Agents** (`src/agents/`): Warren Buffett, Charlie Munger, Ben Graham, Bill Ackman, Cathie Wood, Michael Burry, Mohnish Pabrai, Nassim Taleb, Peter Lynch, Phil Fisher, Rakesh Jhunjhunwala, Stanley Druckenmiller, Aswath Damodaran
- **6 Quantitative Agents**: fundamentals, technicals, valuation, sentiment, news_sentiment, growth_agent
- **2 Management Agents**: risk_manager, portfolio_manager

Each analyst agent follows the pattern: `AgentState → analyze → store in state["data"]["analyst_signals"][agent_id] → return {messages, data}`

### Key Modules

| Module | Path | Purpose |
|---|---|---|
| Agent config | `src/utils/analysts.py` | `ANALYST_CONFIG` registry — add new agents here |
| LLM abstraction | `src/llm/models.py` | `ModelProvider` enum, `LLMModel` dataclass, `get_model()` factory |
| LLM utilities | `src/utils/llm.py` | `call_llm()` with retry logic and structured output |
| Financial data API | `src/tools/api.py` | All market data via financialdatasets.ai |
| Data cache | `src/data/cache.py` | In-memory cache for price/metrics/news |
| Data models | `src/data/models.py` | Pydantic models for API responses |
| Backtesting | `src/backtesting/` | Engine, controller, trader, portfolio, metrics |
| Web app | `app/backend/` + `app/frontend/` | FastAPI + React/TypeScript UI |

### LLM Support

13+ providers via unified abstraction: OpenAI, Anthropic, DeepSeek, Groq, Gemini, Ollama, OpenRouter, xAI, GigaChat, Azure. Models listed in `src/llm/api_models.json` and `src/llm/ollama_models.json`.

## Design Principles

1. **Modular agent architecture**: Each analyst is self-contained, conforming to a common interface (`AgentState → dict`). New analysts are added by creating the agent file and registering in `ANALYST_CONFIG`.

2. **LangGraph DAG orchestration**: Workflow is a composable graph where parallel analyst nodes feed into risk management, then portfolio management.

3. **Multi-LLM provider agnostic**: Supports 13+ providers including local Ollama. Model selection is per-run and configurable per-agent.

4. **Progressive disclosure**: Rule-based scoring runs first, LLM reasoning applied on top for nuanced analysis. Keeps token costs reasonable.

5. **Caching**: In-memory cache prevents redundant API calls across agents and backtest iterations.

6. **Typed contracts**: Pydantic models define strict input/output schemas for API responses, agent outputs, and portfolio state.

7. **Paper trading only**: Never execute real trades. Educational and research purposes only.

## Development

- **Dependencies**: Poetry (`pyproject.toml`). Run `poetry install` to set up.
- **Environment**: Copy `.env.example` to `.env` and fill in API keys.
- **CLI**: `python src/main.py` or `python src/backtester.py`
- **Web app**: `app/backend/` (FastAPI) + `app/frontend/` (React/Vite)
- **Docker**: `docker/docker-compose.yml` with embedded Ollama support
- **Tests**: `tests/` directory
