# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**daily_stock_analysis** - An AI-powered stock analysis system for A-shares (China) and H-shares (Hong Kong). It automatically analyzes user-selected stocks daily and pushes a "Decision Dashboard" to various notification channels (WeChat Work, Feishu, Telegram, Email).

## Commands

```bash
# Setup
pip install -r requirements.txt
cp .env.example .env

# Code formatting (120 line length)
black .
isort .

# Linting
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Security scanning
bandit -r . -x ./test_*.py

# Running
python main.py              # Normal run
python main.py --debug      # Debug mode
python main.py --dry-run    # Dry run (data only, no AI analysis)
python main.py --webui      # Run with WebUI
python main.py --webui-only # WebUI only

# Docker
docker build -t stock-analysis:test .
```

## Architecture

```
main.py (Entry Point)
    │
    ├── analyzer.py ── AI Analysis (Gemini primary, OpenAI-compatible fallback)
    ├── market_analyzer.py ── Market Review
    ├── search_service.py ── News Search (Tavily/Bocha/SerpAPI)
    ├── stock_analyzer.py ── Trend Analysis (MA5/10/20, bias, volume)
    ├── scheduler.py ── Scheduled Tasks
    ├── storage.py ── SQLite Database
    ├── notification.py ── Multi-channel delivery
    ├── feishu_doc.py ── Feishu Cloud Docs
    │
    ├── data_provider/ ── Strategy Pattern for data sources
    │   └── Auto-failover: Efinance > Akshare > Tushare > Baostock > YFinance
    │       (Tushare priority 0 if token configured)
    │
    ├── web/ ── WebUI Server
    │   ├── server.py ── HTTP Server (FastAPI)
    │   ├── handlers.py ── Request Handlers
    │   └── services.py ── Business Services
    │
    └── config.py ── Singleton Config from .env
```

## Key Conventions

- **Commit messages**: Conventional Commits (`feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `perf:`, `test:`, `chore:`)
- **Python**: 3.10+, PEP 8, Black formatting (120 char line limit)
- **Functions/classes**: Must have docstrings

## Key Patterns & Gotchas

- **Stock Code Format**: A-share codes are 6 digits. Windows command line may strip leading zeros (e.g., `000001` becomes `1`), so use `code.strip().zfill(6)` for normalization (main.py:922).
- **Config Singleton**: Use `get_config()` or `Config.get_instance()` to access config. Config is loaded once from `.env`.
- **Data Fetching**: Use `DataFetcherManager` for automatic failover. Each fetcher has `priority` attribute - lower = higher priority.
- **Rate Limiting**: Built-in jitter and delays to avoid API bans. `BaseFetcher.random_sleep()` provides random delays.
- **Thread Safety**: Stock processing uses `ThreadPoolExecutor` with low `max_workers` (default 3) to avoid rate limits.
- **Breakpoint Resume**: `db.has_today_data()` checks cached data before fetching to avoid redundant requests.
