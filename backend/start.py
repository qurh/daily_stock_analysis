#!/usr/bin/env python
"""
AI Stock Analysis System - Startup Script
快速启动开发环境
"""

import subprocess
import sys
import os

def check_python_version():
    """检查 Python 版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print(f"Error: Python 3.10+ required, found {version.major}.{version.minor}")
        sys.exit(1)
    print(f"[OK] Python {version.major}.{version.minor}.{version.micro}")

def check_dependencies():
    """检查依赖是否安装"""
    print("\n[1/3] Checking dependencies...")
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import pydantic
        import httpx
        print("[OK] All core dependencies installed")
    except ImportError as e:
        print(f"[MISSING] {e}")
        print("\nInstall dependencies with:")
        print("  pip install -r backend/requirements.txt")
        sys.exit(1)

def init_database():
    """初始化数据库"""
    print("\n[2/3] Initializing database...")
    try:
        from app.db.database import init_db, engine
        import asyncio

        async def setup():
            await init_db()
            print("[OK] Database initialized")

        asyncio.run(setup())
    except Exception as e:
        print(f"[WARN] Database initialization warning: {e}")
        print("[INFO] This is normal if using SQLite for first time")

def start_server():
    """启动服务器"""
    # 先读取配置
    from app.config import get_settings
    settings = get_settings()

    print("\n[3/3] Starting server...")
    print("\n" + "="*50)
    print("AI Stock Analysis System")
    print("="*50)
    print(f"\nBackend API: http://{settings.HOST}:{settings.PORT}")
    print(f"API Docs:    http://{settings.HOST}:{settings.PORT}/docs")
    print("\nPress Ctrl+C to stop\n")

    # 切换到 backend 目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # 启动 uvicorn
    try:
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=True,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\nServer stopped")

if __name__ == "__main__":
    print("="*50)
    print("AI Stock Analysis System - Startup")
    print("="*50)

    check_python_version()
    check_dependencies()
    init_database()
    start_server()
