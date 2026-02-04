# Full-Stack 目录重构实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 按 `docs/系统设计/架构设计文档.md` 的第 6 节目录结构，将根目录相关文件迁移到 `backend/` 与 `frontend/`，形成标准全栈仓库布局。  

**Architecture:** 以 `backend/app/` 为后端核心包，`frontend/` 为 Next.js App Router 项目；根目录仅保留文档、脚本、容器与顶层配置。  

**Tech Stack:** Python, FastAPI, SQLite, Next.js 16.1.6, Tailwind CSS, Docker Compose

---

### Task 1: 建立迁移基线与失败测试

**Files:**
- Create: `tests/backend/test_imports.py`
- Modify: `README.md`

**Step 1: 写一个会失败的导入测试**

```python
def test_backend_imports():
    import backend.app.config  # noqa: F401
    import backend.app.data_providers  # noqa: F401
    import backend.app.ml.stock_analyzer  # noqa: F401
```

**Step 2: 运行测试，验证失败**

Run: `pytest tests/backend/test_imports.py -v`  
Expected: FAIL（模块路径尚未存在）

**Step 3: 记录迁移说明（README 简短备注）**

在 `README.md` 增加“目录重构进行中”的一行提示，避免误导。

**Step 4: 提交**

```bash
git add tests/backend/test_imports.py README.md
git commit -m "chore: add import smoke test for repo restructure"
```

---

### Task 2: 创建后端目录骨架

**Files:**
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/ml/__init__.py`
- Create: `backend/app/notification/__init__.py`
- Create: `backend/app/utils/__init__.py`
- Create: `backend/app/prompts/__init__.py`
- Create: `backend/app/prompts/default/__init__.py`

**Step 1: 创建目录**

Run:  
`mkdir -p backend/app/core backend/app/ml backend/app/notification backend/app/utils backend/app/prompts/default`

**Step 2: 添加空的包初始化文件**

Run:  
`touch backend/app/core/__init__.py backend/app/ml/__init__.py backend/app/notification/__init__.py backend/app/utils/__init__.py backend/app/prompts/__init__.py backend/app/prompts/default/__init__.py`

**Step 3: 运行测试，仍应失败**

Run: `pytest tests/backend/test_imports.py -v`  
Expected: FAIL（模块尚未移动）

**Step 4: 提交**

```bash
git add backend/app/core backend/app/ml backend/app/notification backend/app/utils backend/app/prompts
git commit -m "chore: add backend app skeleton"
```

---

### Task 3: 迁移后端核心代码并修正导入

**Files:**
- Move: `config.py` → `backend/app/config.py`
- Move: `data_provider/` → `backend/app/data_providers/`
- Move: `analyzer.py` → `backend/app/ml/analyzer.py`
- Move: `stock_analyzer.py` → `backend/app/ml/stock_analyzer.py`
- Move: `market_analyzer.py` → `backend/app/ml/market_analyzer.py`
- Move: `search_service.py` → `backend/app/ml/search_service.py`
- Move: `storage.py` → `backend/app/db/connection.py`
- Move: `notification.py` → `backend/app/notification/notification_service.py`
- Move: `enums.py` → `backend/app/utils/enums.py`
- Move: `scheduler.py` → `backend/app/core/scheduler.py`
- Move: `main.py` → `backend/app/core/pipeline.py`
- Move: `test_env.py` → `backend/app/core/test_env.py`
- Move: `feishu_doc.py` → `backend/app/services/feishu_doc.py`

**Step 1: 使用 git mv 执行迁移**

（逐条执行）  
`git mv config.py backend/app/config.py`  
`git mv data_provider backend/app/data_providers`  
`git mv analyzer.py backend/app/ml/analyzer.py`  
`git mv stock_analyzer.py backend/app/ml/stock_analyzer.py`  
`git mv market_analyzer.py backend/app/ml/market_analyzer.py`  
`git mv search_service.py backend/app/ml/search_service.py`  
`git mv storage.py backend/app/db/connection.py`  
`git mv notification.py backend/app/notification/notification_service.py`  
`git mv enums.py backend/app/utils/enums.py`  
`git mv scheduler.py backend/app/core/scheduler.py`  
`git mv main.py backend/app/core/pipeline.py`  
`git mv test_env.py backend/app/core/test_env.py`  
`git mv feishu_doc.py backend/app/services/feishu_doc.py`

**Step 2: 修正导入路径（最小改动）**

逐文件将 `from config import ...` 这类顶层导入改为 `from backend.app.config import ...` 或包内相对导入。

**Step 3: 运行测试，验证通过**

Run: `pytest tests/backend/test_imports.py -v`  
Expected: PASS

**Step 4: 提交**

```bash
git add backend/app
git commit -m "refactor: move core backend modules into app package"
```

---

### Task 4: 迁移运行期目录并更新路径配置

**Files:**
- Move: `data/` → `backend/data/`
- Move: `logs/` → `backend/logs/`
- Move: `reports/` → `backend/reports/`
- Move: `sources/` → `backend/sources/`
- Modify: `backend/app/config.py`

**Step 1: 迁移目录**

Run:  
`git mv data backend/data`  
`git mv logs backend/logs`  
`git mv reports backend/reports`  
`git mv sources backend/sources`

**Step 2: 更新配置中的默认路径**

将默认路径改为 `backend/...` 相对路径或基于项目根的绝对路径拼接。

**Step 3: 运行轻量检查**

Run: `python -m py_compile backend/app/config.py`  
Expected: PASS

**Step 4: 提交**

```bash
git add backend/data backend/logs backend/reports backend/sources backend/app/config.py
git commit -m "refactor: relocate runtime directories under backend"
```

---

### Task 5: 处理旧 Web 资源与前端目录对齐

**Files:**
- Move: `web/` → `frontend/legacy/web/`
- Move: `webui.py` → `backend/legacy/webui.py`
- Create: `frontend/README.md`

**Step 1: 创建 legacy 目录并迁移**

Run:  
`mkdir -p frontend/legacy backend/legacy`  
`git mv web frontend/legacy/web`  
`git mv webui.py backend/legacy/webui.py`

**Step 2: 补充前端说明**

在 `frontend/README.md` 说明 Next.js 项目将以此目录为根。

**Step 3: 提交**

```bash
git add frontend/legacy backend/legacy frontend/README.md
git commit -m "chore: move legacy web assets into frontend/backend"
```

---

### Task 6: 根目录配置整理（Docker/依赖）

**Files:**
- Move: `requirements.txt` → `backend/requirements.txt`（如需合并则先对比）
- Move: `pyproject.toml` → `backend/pyproject.toml`
- Move: `setup.cfg` → `backend/setup.cfg`
- Move: `Dockerfile` → `Dockerfile.backend`
- Create: `Dockerfile.frontend`
- Modify: `docker-compose.yml`

**Step 1: 迁移/合并依赖文件**

如 `backend/requirements.txt` 已存在，先合并后再移除根目录文件。

**Step 2: 统一 Docker 文件命名**

`git mv Dockerfile Dockerfile.backend`，并新增 `Dockerfile.frontend`（Next.js 构建/运行）。

**Step 3: 更新 docker-compose 引用路径**

调整 build context 与 Dockerfile 路径，指向 `backend/` 与 `frontend/`。

**Step 4: 提交**

```bash
git add backend/requirements.txt backend/pyproject.toml backend/setup.cfg Dockerfile.backend Dockerfile.frontend docker-compose.yml
git commit -m "chore: align root configs to full-stack layout"
```

---

### Task 7: 文档与运行指引更新

**Files:**
- Modify: `README.md`
- Modify: `docs/plans/2026-02-04-mvp-restart-design.md`

**Step 1: 更新运行说明**

说明后端 `backend/` 与前端 `frontend/` 的安装/启动命令。

**Step 2: 记录目录迁移变更**

在设计文档中补充目录结构变更的引用。

**Step 3: 提交**

```bash
git add README.md docs/plans/2026-02-04-mvp-restart-design.md
git commit -m "docs: update structure and run instructions"
```

