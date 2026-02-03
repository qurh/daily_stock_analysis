# Repository Guidelines

## 项目结构与模块组织
`main.py` 负责每日分析流程编排。核心逻辑集中在 `analyzer.py`、`market_analyzer.py`、`stock_analyzer.py`、`search_service.py`、`notification.py`、`storage.py`、`config.py`。数据源适配器位于 `data_provider/`（AkShare、Tushare、Baostock、YFinance、EFinance，共用基础 fetcher）。Web UI 在 `web/`，服务入口与路由模板在 `webui.py`。运行数据与产物分别位于 `data/`（SQLite）、`logs/`、`reports/`、`sources/`。文档在 `docs/`，CI 在 `.github/workflows/`。

## 构建、测试与本地运行
创建虚拟环境并安装依赖：
```bash
python -m venv venv
pip install -r requirements.txt
```
配置环境：`copy .env.example .env` 并填写 API Key。运行分析：
```bash
python main.py
python main.py --dry-run
python main.py --market-review
python main.py --stocks "600519,000001"
```
Web UI：
```bash
python main.py --webui
python main.py --webui-only
```
环境检查：`python test_env.py`（可加 `--db`、`--fetch`、`--llm`、`--notify`）。可选 Docker：`docker compose up --build`。

## 编码风格与命名规范
遵循 PEP 8，行宽 120（Black/Flake8）。函数与变量用 `snake_case`，类用 `CapWords`。涉及核心代码时执行格式化与静态检查：
```bash
black .
isort .
flake8 .
bandit -r . -x ./test_*.py
```
公共函数与类需 docstring；复杂逻辑请加简短注释。

## 测试规范
测试框架为 Pytest（见 `setup.cfg`，`test_*.py`、`test_*`）。运行：`pytest`。集成式验证用 `test_env.py`，覆盖配置、数据库、数据抓取、LLM 与通知。

## 提交与 PR 规范
提交信息遵循 Conventional Commits：`feat:`、`fix:`、`docs:`、`refactor:`，可选 scope（如 `feat(workflow):`）。PR 需包含简要说明、测试步骤与关联问题；新增配置请同步更新 `.env.example` 与 `docs/`；Web UI 改动需提供截图。

## 安全与配置提示
敏感信息仅保存在 `.env`，禁止提交。日志中避免输出完整 API Key 或 webhook URL，必要时脱敏或截断。
