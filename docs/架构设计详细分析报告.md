# 项目架构设计详细分析报告

## 一、项目概述

**daily_stock_analysis** 是一个基于 AI 的智能股票分析系统，专为 A 股（上海/深圳）和 H 股（香港）市场设计。系统每日自动分析用户自选股票，并通过多种渠道（企业微信、飞书、Telegram、邮件等）推送「决策仪表盘」。

### 核心特性

- AI 驱动的决策建议（Google Gemini + OpenAI 兼容 API）
- 多数据源容灾（AkShare、Tushare、Baostock、YFinance、EFinance）
- 多渠道通知推送
- 零成本 GitHub Actions 部署

---

## 二、整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              main.py (入口层)                                 │
│                    StockAnalysisPipeline (流程调度器)                          │
│  - 线程池并发控制 (ThreadPoolExecutor, max_workers=3)                         │
│  - 全局异常处理 (单股失败不影响整体)                                            │
│  - 断点续传 (has_today_data 检查)                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         ▼                            ▼                            ▼
┌─────────────────┐     ┌─────────────────────┐      ┌─────────────────────┐
│   data_provider │     │     analyzer.py     │      │ search_service.py   │
│   (策略模式)     │     │   (AI 分析层)       │      │   (新闻搜索)         │
│                 │     │                     │      │                     │
│ BaseFetcher     │     │ GeminiAnalyzer      │      │ Tavily              │
│   ├─ Efinance   │     │ OpenAI 兼容 API     │      │ SerpAPI             │
│   ├─ Akshare    │     │ Gemini Grounding    │      │ Bocha               │
│   ├─ Tushare    │     │                     │      │                     │
│   ├─ Baostock   │     │ AnalysisResult      │      │ 多 Key 负载均衡      │
│   └─ YFinance   │     │ (决策仪表盘结构)     │      │                     │
└─────────────────┘     └─────────────────────┘      └─────────────────────┘
         │                            │                            │
         └────────────────────────────┼────────────────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          storage.py (持久化层)                                │
│                    DatabaseManager (SQLAlchemy ORM)                          │
│  - StockDaily 模型 (行情数据)                                                 │
│  - SQLite 单例连接                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       notification.py (通知层)                                │
│                     NotificationService                                      │
│  - 企业微信 Webhook │ 飞书 Webhook │ Telegram │ 邮件 SMTP │ Pushover │ 自定义  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          config.py (配置层)                                   │
│                    Config (单例模式)                                          │
│  - .env 文件加载                                                              │
│  - 40+ 配置项管理                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 三、核心设计模式

### 3.1 策略模式 (Strategy Pattern) - 数据源管理

**位置**: `data_provider/base.py`

```python
# 抽象基类定义统一接口
class BaseFetcher(ABC):
    name: str
    priority: int

    @abstractmethod
    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str): ...
    @abstractmethod
    def _normalize_data(self, df: pd.DataFrame, stock_code: str): ...

# 策略管理器实现自动故障切换
class DataFetcherManager:
    def get_daily_data(self, stock_code: str, ...) -> Tuple[pd.DataFrame, str]:
        for fetcher in self._fetchers:  # 按优先级排序
            try:
                df = fetcher.get_daily_data(...)
                return df, fetcher.name  # 成功返回
            except Exception as e:
                continue  # 切换到下一个
        raise DataFetchError("所有数据源失败")
```

**优先级顺序**: Efinance(0) > Akshare(1) > Tushare(2) > Baostock(3) > YFinance(4)

### 3.2 单例模式 (Singleton Pattern) - 配置管理

**位置**: `config.py`

```python
class Config:
    _instance: Optional['Config'] = None

    @classmethod
    def get_instance(cls) -> 'Config':
        if cls._instance is None:
            cls._instance = cls._load_from_env()
        return cls._instance
```

### 3.3 工厂模式 - 通知渠道

**位置**: `notification.py`

```python
class NotificationChannel(Enum):
    WECHAT = "wechat"
    FEISHU = "feishu"
    TELEGRAM = "telegram"
    EMAIL = "email"
    PUSHOVER = "pushover"
    CUSTOM = "custom"

# SMTP 自动识别
SMTP_CONFIGS = {
    "qq.com": {"server": "smtp.qq.com", "port": 465, "ssl": True},
    "163.com": {"server": "smtp.163.com", "port": 465, "ssl": True},
    # ... 自动根据邮箱域名配置
}
```

---

## 四、数据流分析

### 4.1 主流程数据流

```
1. 读取配置 (get_config)
   ↓
2. 获取自选股列表 (stock_list)
   ↓
3. 初始化各模块:
   - DataFetcherManager (数据源)
   - GeminiAnalyzer (AI)
   - NotificationService (通知)
   - SearchService (搜索)
   ↓
4. 并发执行 (ThreadPoolExecutor, max_workers=3):
   ┌─────────────────────────────────────┐
   │ for stock in stocks:                │
   │   future = executor.submit(process, stock) │
   └─────────────────────────────────────┘
   ↓
5. 单股处理流程:
   a) fetch_and_save_stock_data()
      ├─ 检查数据库是否有今日数据 (断点续传)
      ├─ DataFetcherManager.get_daily_data()
      │   └─ 遍历数据源，失败自动切换
      └─ 保存到 SQLite
   ↓
   b) search_service.search_stock_news()
      ├─ 多搜索引擎负载均衡
      └─ 返回新闻摘要
   ↓
   c) analyzer.analyze()
      ├─ 构建 Prompt (技术指标 + 新闻)
      ├─ 调用 Gemini API
      │   ├─ 重试机制 (5次)
      │   └─ 指数退避
      └─ 解析响应为 AnalysisResult
   ↓
6. 汇总分析结果
   ↓
7. 多渠道通知推送
   └─ 并行发送: 企业微信、飞书、Telegram、邮件...
```

### 4.2 数据标准化

**位置**: `data_provider/base.py`

```python
STANDARD_COLUMNS = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'pct_chg']

# 每个 Fetcher 实现 _normalize_data() 将原始数据转换为标准格式
class BaseFetcher:
    def get_daily_data(self, stock_code: str, ...) -> pd.DataFrame:
        raw_df = self._fetch_raw_data(...)       # Step 1: 获取原始
        df = self._normalize_data(raw_df, ...)   # Step 2: 标准化
        df = self._clean_data(df)                # Step 3: 清洗
        df = self._calculate_indicators(df)      # Step 4: 计算指标
        return df
```

---

## 五、防封禁与容错策略

### 5.1 流控配置

```python
# config.py
max_workers: int = 3              # 低并发限制
akshare_sleep_min: float = 2.0    # 请求间隔随机范围
akshare_sleep_max: float = 5.0
tushare_rate_limit_per_minute: int = 80  # Tushare 免费配额
```

### 5.2 重试机制

使用 `tenacity` 库实现指数退避重试：

```python
# Gemini API 调用
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=5, max=60),
    retry=retry_if_exception_type((RateLimitError, APIError))
)
def analyze_with_gemini(...): ...

# 数据获取
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=30)
)
def get_daily_data(...): ...
```

### 5.3 数据源故障切换

```
请求 → Efinance (Priority 0)
    ├─ 成功 → 返回数据
    └─ 失败 → 切换到 Akshare (Priority 1)
        ├─ 成功 → 返回数据
        └─ 失败 → 切换到 Tushare (Priority 2)
            ... 依次类推
            └─ 所有失败 → 抛出 DataFetchError
```

---

## 六、数据库设计

### 6.1 StockDaily 模型

```python
class StockDaily(Base):
    __tablename__ = 'stock_daily'

    id = Column(Integer, primary_key=True)
    code = Column(String(10), nullable=False, index=True)      # 股票代码
    date = Column(Date, nullable=False, index=True)            # 交易日期

    # OHLC 数据
    open, high, low, close = Column(Float), ...

    # 成交数据
    volume, amount, pct_chg = Column(Float), ...

    # 技术指标
    ma5, ma10, ma20, volume_ratio = Column(Float), ...

    # 数据来源
    data_source = Column(String(50))  # 记录来源

    # 唯一约束
    __table_args__ = (
        UniqueConstraint('code', 'date', name='uix_code_date'),
    )
```

### 6.2 断点续传逻辑

```python
def fetch_and_save_stock_data(self, code: str, force_refresh: bool = False):
    today = date.today()

    # 检查今日数据是否已存在
    if not force_refresh and self.db.has_today_data(code, today):
        logger.info(f"[{code}] 今日数据已存在，跳过获取（断点续传）")
        return True, None

    # 否则从数据源获取
    df, source = self.fetcher_manager.get_daily_data(code)
    self.db.save_stock_data(df, source)
```

---

## 七、模块依赖关系

```
main.py
├── config.py ─────────────┬─────────────────────┐
├── storage.py ────────────┤                     │
├── data_provider/ ────────┤  核心依赖            │
│   └── base.py ──────────┤                     │
├── analyzer.py ──────────┤                     │
├── notification.py ──────┤                     │
├── search_service.py ────┤                     │
└── enums.py ─────────────┘                     │
                                                │
data_provider/                                  │
├── base.py ────────────────────────────────────┤
├── akshare_fetcher.py ────┐                   │
├── tushare_fetcher.py ────┤  策略实现          │
├── baostock_fetcher.py ───┤                   │
├── efinance_fetcher.py ───┤                   │
└── yfinance_fetcher.py ───┘                   │
                                                │
notification.py                                 │
├── analyzer.py (AnalysisResult) ───────────────┤
└── config.py ──────────────────────────────────┘
```

---

## 八、关键配置项

| 配置组 | 关键变量 | 说明 |
|--------|----------|------|
| **股票** | `STOCK_LIST` | 自选股代码，逗号分隔 |
| **AI** | `GEMINI_API_KEY` / `OPENAI_API_KEY` | 至少配置一个 |
| **数据** | `TUSHARE_TOKEN` | Tushare Pro Token |
| **搜索** | `BOCHA_API_KEYS`, `TAVILY_API_KEYS` | 多 Key 负载均衡 |
| **通知** | `WECHAT_WEBHOOK_URL`, `FEISHU_WEBHOOK_URL` | 可配置多个 |
| **并发** | `MAX_WORKERS` | 默认 3，防封禁 |
| **流控** | `GEMINI_REQUEST_DELAY` | Gemini 请求间隔 |

---

## 九、运行模式

| 模式 | 命令 | 用途 |
|------|------|------|
| 正常 | `python main.py` | 完整分析流程 |
| 调试 | `python main.py --debug` | 详细日志 |
| 干跑 | `python main.py --dry-run` | 仅获取数据，不 AI 分析 |
| WebUI | `python main.py --webui` | 启动本地管理界面 |
| 仅 WebUI | `python main.py --webui-only` | 只启动 WebUI |
| 指定股票 | `python main.py --stocks "600519,000001"` | 分析指定股票 |
| 大盘复盘 | `python main.py --market-review` | 仅大盘复盘 |

---

## 十、扩展指南

### 10.1 新增数据源

1. 继承 `BaseFetcher` 实现 `_fetch_raw_data()` 和 `_normalize_data()`
2. 设置 `priority` 优先级（数字越小越优先）
3. 在 `DataFetcherManager._init_default_fetchers()` 注册

**示例**:

```python
from data_provider.base import BaseFetcher

class MyFetcher(BaseFetcher):
    name = "MyFetcher"
    priority = 10  # 较低优先级

    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str):
        # 从数据源获取原始数据
        pass

    def _normalize_data(self, df: pd.DataFrame, stock_code: str):
        # 转换为标准格式: date, open, high, low, close, volume, amount, pct_chg
        pass
```

### 10.2 新增通知渠道

1. 在 `NotificationChannel` Enum 添加新类型
2. 在 `NotificationService` 实现发送逻辑
3. 配置项添加到 `Config` dataclass

### 10.3 新增 AI 模型

1. 在 `analyzer.py` 添加新的 Analyzer 类
2. 实现 `analyze()` 接口
3. 支持 OpenAI 兼容 API 格式即可

---

## 十一、技术栈总结

| 层级 | 技术选型 |
|------|----------|
| 语言 | Python 3.10+ |
| 数据库 | SQLite + SQLAlchemy |
| AI | Google Gemini / OpenAI 兼容 API |
| 数据源 | AkShare, Tushare, Baostock, YFinance, EFinance |
| 搜索 | Tavily, SerpAPI, Bocha |
| HTTP | requests, httpx |
| 重试 | tenacity |
| 部署 | GitHub Actions, Docker |

---

## 十二、文件结构

```
daily_stock_analysis/
├── main.py                    # 主入口，流程调度
├── analyzer.py                # AI 分析层
├── config.py                  # 配置管理（单例）
├── notification.py            # 通知服务
├── search_service.py          # 新闻搜索
├── storage.py                 # 数据存储
├── market_analyzer.py         # 大盘分析
├── stock_analyzer.py          # 股票趋势分析
├── enums.py                   # 枚举定义
├── requirements.txt           # 依赖列表
├── .env.example               # 配置示例
├── Dockerfile                 # Docker 构建
├── docker-compose.yml         # Docker Compose
├── CLAUDE.md                  # Claude Code 指南
├── CONTRIBUTING.md            # 贡献指南
├── README.md                  # 项目说明
│
├── data_provider/             # 数据源模块
│   ├── base.py                # 基类与管理器（策略模式）
│   ├── akshare_fetcher.py     # AkShare 实现
│   ├── tushare_fetcher.py     # Tushare 实现
│   ├── baostock_fetcher.py    # Baostock 实现
│   ├── efinance_fetcher.py    # EFinance 实现
│   └── yfinance_fetcher.py    # YFinance 实现
│
├── web/                       # WebUI 模块
│   ├── server.py              # 服务端
│   ├── router.py              # 路由
│   ├── handlers.py            # 处理器
│   ├── services.py            # 业务服务
│   └── templates/             # 模板文件
│
├── data/                      # 数据目录
│   └── stock_analysis.db      # SQLite 数据库
│
├── logs/                      # 日志目录
│
├── reports/                   # 报告目录
│
├── sources/                   # 静态资源
│
├── docs/                      # 文档
│   ├── full-guide.md          # 完整配置指南
│   └── architecture.md        # 架构设计文档（本文件）
│
└── .github/
    └── workflows/             # CI/CD 流程
        ├── ci.yml             # 持续集成
        ├── daily_analysis.yml # 每日分析
        └── pr-review.yml      # PR 评审
```

---

*文档版本: 1.0*
*最后更新: 2026-01-22*
