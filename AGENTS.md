# Repository Guidelines

## Project Structure & Module Organization
- `main.py` orchestrates the daily analysis pipeline; core logic lives in `analyzer.py`, `market_analyzer.py`, `stock_analyzer.py`, `search_service.py`, `notification.py`, `storage.py`, and `config.py`.
- `data_provider/` contains data source adapters (AkShare, Tushare, Baostock, YFinance, EFinance) built on a shared base fetcher.
- `web/` and `webui.py` provide the local WebUI server, routing, handlers, and templates.
- `data/` stores the SQLite database, `logs/` holds runtime logs, `reports/` holds generated reports, and `sources/` contains static assets.
- `docs/` is the primary documentation hub; CI workflows live in `.github/workflows/`.

## Build, Test, and Development Commands
- Create a venv and install deps:
  - `python -m venv venv`
  - `pip install -r requirements.txt`
- Configure environment: `copy .env.example .env` and fill in API keys.
- Run analysis:
  - `python main.py` (full run)
  - `python main.py --dry-run` (data only)
  - `python main.py --market-review`
  - `python main.py --stocks "600519,000001"`
- WebUI:
  - `python main.py --webui`
  - `python main.py --webui-only`
- Environment checks: `python test_env.py` (or `--db`, `--fetch`, `--llm`, `--notify`).
- Optional Docker: `docker compose up --build`.

## Coding Style & Naming Conventions
- Follow PEP 8; line length is 120 (Black/Flake8). Use `snake_case` for functions/variables and `CapWords` for classes.
- Format and lint locally when touching core code:
  - `black .`
  - `isort .`
  - `flake8 .`
  - `bandit -r . -x ./test_*.py`
- Add docstrings for public functions/classes and short comments for non-obvious logic.

## Testing Guidelines
- Pytest is configured in `setup.cfg` (`test_*.py`, `test_*` functions). Run `pytest` for automated tests.
- `test_env.py` is the primary integration-style validation for config, database access, data fetch, LLM calls, and notifications.

## Commit & Pull Request Guidelines
- Use Conventional Commits as in history: `feat:`, `fix:`, `docs:`, `refactor:`, with optional scopes like `feat(workflow):`.
- PRs should include a concise summary, testing steps, and linked issues. If you add new config, update `.env.example` and the relevant docs in `docs/`. Include screenshots for WebUI changes.

## Security & Configuration Tips
- Keep secrets in `.env` (never commit). Use `.env.example` as the template for new variables.
- Avoid logging API keys or full webhook URLs; redact or truncate in logs.
