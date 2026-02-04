# AI 股票分析系统 - 本地部署指南

## 环境要求

- Python 3.10+
- PostgreSQL 15+ (可选，默认使用 SQLite)
- Redis 7+ (可选，用于缓存)
- Node.js 18+ (前端开发)

## 快速开始

### 1. 克隆并进入目录

```bash
cd daily_stock_analysis
```

### 2. 安装 Python 依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r backend/requirements.txt
```

### 3. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置 (Windows)
notepad .env

# 编辑配置 (Linux/Mac)
nano .env
```

主要配置项说明：

```env
# AI 模型 (至少配置一个)
GEMINI_API_KEY=your_gemini_api_key      # 推荐: https://aistudio.google.com/
OPENAI_API_KEY=your_openai_key          # 备选: https://platform.openai.com/
DEEPSEEK_API_KEY=your_deepseek_key      # 便宜: https://platform.deepseek.com/

# 数据库 (可选，使用默认 SQLite)
# DATABASE_URL=postgresql://user:password@localhost:5432/stock_ai

# 股票数据
TUSHARE_TOKEN=your_tushare_token         # 可选: https://tushare.pro/
```

### 4. 初始化数据库

```bash
# 默认使用 SQLite，无需额外配置
python -c "from app.db.database import init_db; import asyncio; asyncio.run(init_db())"
```

### 5. 启动后端服务

```bash
# 开发模式 (自动重载)
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8888 --reload

# 或者使用 Python 直接运行
python -m app.main
```

后端启动后访问: http://localhost:8888/docs (API 文档)

### 6. 启动前端 (可选)

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build
npm start
```

前端访问: http://localhost:3001

## Docker 部署 (推荐)

### 使用 Docker Compose

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

### 仅启动数据库

```bash
docker-compose up -d postgres redis
```

## 验证部署

### 1. 检查后端健康

```bash
curl http://localhost:8888/health
```

预期输出:
```json
{"status": "healthy", "version": "1.0.0"}
```

### 2. 检查 API 文档

访问: http://localhost:8888/docs

### 3. 测试 AI 对话

```bash
curl -X POST "http://localhost:8888/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "分析一下贵州茅台的走势",
    "use_rag": true,
    "stream": false
  }'
```

### 4. 测试 WebSocket

```javascript
// 在浏览器控制台中
const ws = new WebSocket('ws://localhost:8888/ws');
ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Message:', e.data);
```

## 常见问题

### 1. 数据库连接错误

```
Error: could not connect to server
```

解决:
```bash
# 使用 Docker PostgreSQL
docker-compose up -d postgres

# 或使用 SQLite (默认)
# 确保 DATABASE_URL 未设置或设置为 sqlite://...
```

### 2. AI API 密钥错误

```
Error: API key not valid
```

解决:
- 确认 API Key 正确
- 检查是否需要设置代理
- 确认模型名称正确

### 3. 端口被占用

```
Error: Port 8000 is already in use
```

解决:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <pid> /F

# Linux
lsof -i :8000
kill -9 <pid>
```

### 4. 内存不足

解决: 编辑 `docker-compose.yml` 降低内存限制

### 5. 模块导入错误

```bash
# 重新安装依赖
pip install -r backend/requirements.txt --force-reinstall

# 或清理缓存
pip cache purge
```

## 开发模式

### 代码格式化

```bash
# Black 格式化
black backend/

# import 排序
isort backend/
```

### 运行测试

```bash
pytest backend/tests/ -v
```

### 类型检查

```bash
mypy backend/
```

## 生产部署

### 1. 设置生产环境变量

```env
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://user:pass@localhost:5432/stock_ai
```

### 2. 使用 Gunicorn

```bash
gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 3. Nginx 反向代理

```nginx
server {
    listen 80;
    server_name localhost;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 监控和维护

### 查看日志

```bash
# Docker 方式
docker-compose logs -f backend

# 直接运行
tail -f logs/app.log
```

### 数据库备份

```bash
# SQLite
cp data/stock_analysis.db data/backup_$(date +%Y%m%d).db

# PostgreSQL
pg_dump -U postgres stock_ai > backup.sql
```
