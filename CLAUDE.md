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
    ├── analyzer.py ── AI Analysis (Gemini/OpenAI)
    ├── market_analyzer.py ── Market Review
    ├── search_service.py ── News Search (Tavily/Bocha/SerpAPI)
    │
    ├── data_provider/ ── Strategy Pattern for data sources
    │   └── Auto-failover: Efinance > Akshare > Tushare > Baostock > YFinance
    │
    ├── notification.py ── Multi-channel delivery
    │   └── WeChat, Feishu, Telegram, Email, Custom Webhook
    │
    └── config.py ── Singleton Config from .env
```

## Key Conventions

- **Commit messages**: Conventional Commits (`feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `perf:`, `test:`, `chore:`)
- **Python**: 3.10+, PEP 8, Black formatting (120 char line limit)
- **Functions/classes**: Must have docstrings
