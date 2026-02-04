# 前端 UI/UX 设计方案

**创建日期:** 2026-02-04
**项目:** daily_stock_analysis

---

## 1. 设计定位

### 1.1 产品类型
金融数据分析 Dashboard（股票分析系统）

### 1.2 风格定位
- **主题:** Dark Mode (OLED) 深色模式
- **布局:** Data-Dense Dashboard + 顶部导航
- **目标用户:** 投资者、分析师

---

## 2. 色彩系统

### 2.1 核心颜色

```css
:root {
  /* 背景层 */
  --bg-primary:    #0F172A;   /* 页面主背景 */
  --bg-secondary:  #1E293B;   /* 卡片/面板背景 */
  --bg-tertiary:   #334155;   /* 次级区域 */

  /* 文字层 */
  --text-primary:  #F8FAFC;   /* 主标题 */
  --text-secondary:#94A3B8;   /* 次要文字 */
  --text-muted:    #64748B;   /* 禁用文字 */

  /* 品牌色 */
  --primary:       #3B82F6;   /* 主要交互色 */
  --primary-hover: #2563EB;
  --accent:        #F59E0B;   /* CTA */

  /* 涨跌色 - A股习惯: 红涨绿跌 */
  --rise:          #EF4444;   /* 上涨 - 红色 */
  --rise-bg:       rgba(239, 68, 68, 0.15);
  --fall:          #22C55E;   /* 下跌 - 绿色 */
  --fall-bg:       rgba(34, 197, 94, 0.15);
  --neutral:       #64748B;

  /* 边框 */
  --border:        #334155;
  --border-light:  #475569;

  /* 状态 */
  --success:       #22C55E;
  --warning:       #F59E0B;
  --error:         #EF4444;
}
```

### 2.2 涨跌色应用

| 场景 | 上涨 | 下跌 | 平盘 |
|------|------|------|------|
| 价格数字 | `#EF4444` | `#22C55E` | `#64748B` |
| 背景 | `rgba(239,68,68,0.15)` | `rgba(34,197,94,0.15)` | `#334155` |
| 趋势箭头 | ↑ | ↓ | → |

---

## 3. 字体系统

- **字体:** IBM Plex Sans
- **Google Fonts:** https://fonts.google.com/share?selection.family=IBM+Plex+Sans
- **CSS Import:**
```css
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');
```

---

## 4. 布局结构

### 4.1 导航架构

```
┌─────────────────────────────────────────────────────────────────┐
│  Logo    搜索栏                               通知  设置  用户  │
├────────┬─────────┬──────────┬─────────┬─────────┬──────────────┤
│  市场  │  复盘   │  知识库   │  组合   │  监控   │    策略      │
│ Market │ Review  │ Knowledge │Portfolio│ Monitor │  Strategy   │
└────────┴─────────┴──────────┴─────────┴─────────┴──────────────┘
```

### 4.2 Dashboard 布局

```
┌────────────────────────────────────────────────────────────┐
│  KPI卡片1   │  KPI卡片2   │  KPI卡片3   │  KPI卡片4        │
├────────────────┴────────────────┴────────────────┴──────────┤
│  主图表区 (自适应宽度)                                      │
├────────────────────────────────────────────────────────────┤
│  数据表格区 (带筛选、分页、列配置)                           │
└────────────────────────────────────────────────────────────┘
```

### 4.3 内容型页面布局

```
┌──────────────────────┬────────────────────────────────────┐
│  左侧分类树/列表     │         主内容区                   │
└──────────────────────┴────────────────────────────────────┘
```

---

## 5. Ant Design 主题配置

```typescript
// theme/themeConfig.ts
import type { ThemeConfig } from 'antd'

export const darkTheme: ThemeConfig = {
  token: {
    colorPrimary: '#3B82F6',
    colorPrimaryHover: '#2563EB',
    colorAccent: '#F59E0B',
    colorSuccess: '#22C55E',
    colorWarning: '#F59E0B',
    colorError: '#EF4444',
    colorInfo: '#3B82F6',
    colorBgContainer: '#1E293B',
    colorBgElevated: '#334155',
    colorBgLayout: '#0F172A',
    colorText: '#F8FAFC',
    colorTextSecondary: '#94A3B8',
    colorTextTertiary: '#64748B',
    colorBorder: '#334155',
    colorBorderSecondary: '#475569',
    borderRadius: 8,
    fontFamily: "'IBM Plex Sans', -apple-system, sans-serif",
  },
  components: {
    Layout: {
      headerBg: '#0F172A',
      siderBg: '#0F172A',
      bodyBg: '#0F172A',
    },
    Card: {
      colorBgContainer: '#1E293B',
      headerBg: 'transparent',
    },
    Table: {
      colorBgContainer: '#1E293B',
      headerBg: '#1E293B',
      rowHoverBg: '#334155',
    },
  },
}
```

---

## 6. 图表规范

### 6.1 图表颜色

```typescript
export const CHART_COLORS = {
  up: '#EF4444',      // 上涨 (红)
  down: '#22C55E',    // 下跌 (绿)
  neutral: '#64748B',
  ma5: '#F59E0B',     // MA5
  ma10: '#3B82F6',    // MA10
  ma20: '#8B5CF6',    // MA20
  macd: {
    dif: '#3B82F6',
    dea: '#F59E0B',
    hist: { positive: 'rgba(239, 68, 68, 0.6)', negative: 'rgba(34, 197, 94, 0.6)' }
  },
  kdj: { k: '#F59E0B', d: '#3B82F6', j: '#EC4899' },
  grid: '#334155',
}
```

### 6.2 推荐图表库
- **Recharts** - K线以外的所有图表
- **Lightweight Charts** - 专业K线图

---

## 7. 数字格式化

```typescript
export function formatPrice(value: number): string {
  return `¥${value.toFixed(2)}`
}

export function formatPct(value: number): string {
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

export function formatVolume(value: number): string {
  if (value >= 100000000) return `${(value / 100000000).toFixed(2)}亿`
  if (value >= 10000) return `${(value / 10000).toFixed(2)}万`
  return value.toLocaleString()
}

export function formatAmount(value: number): string {
  if (value >= 100000000) return `¥${(value / 100000000).toFixed(2)}亿`
  if (value >= 10000) return `¥${(value / 10000).toFixed(2)}万`
  return `¥${value.toLocaleString()}`
}
```

---

## 8. 动效规范

```typescript
export const ANIMATION = {
  micro: 150,        // 微交互
  transition: 200,   // 过渡
  skeleton: 800,     // 骨架屏
  chartEnter: 500,   // 图表入场
  chartUpdate: 300,  // 数据更新
}
```

### 加载状态
- 页面加载: 骨架屏 Skeleton
- 表格加载: Skeleton Table
- 小范围: Spin Spinner

---

## 9. 响应式断点

```css
--breakpoint-sm: 640px;   // 手机横屏
--breakpoint-md: 768px;   // 平板
--breakpoint-lg: 1024px;  // 笔记本
--breakpoint-xl: 1280px;  // 桌面
--breakpoint-2xl: 1536px; // 大屏
```

---

## 10. 无障碍规范

- 颜色对比度 >= 4.5:1
- 键盘导航支持
- ARIA 标签
- Focus 管理
- `prefers-reduced-motion` 支持

---

## 11. 实施优先级

| 优先级 | 任务 | 文件 |
|--------|------|------|
| P0 | 全局主题配置 | `src/theme/themeConfig.ts` |
| P0 | 涨跌色系统与工具函数 | `src/utils/format.ts` |
| P0 | 全局样式变量 | `src/app/globals.css` |
| P1 | 重构 Market 页面 | `src/features/market/MarketPage.tsx` |
| P1 | 重构 Portfolio 页面 | `src/features/portfolio/PortfolioPage.tsx` |
| P2 | 复盘页面适配 | `src/features/review/ReviewPage.tsx` |
| P2 | 知识库页面适配 | `src/features/knowledge/KnowledgePage.tsx` |
| P3 | 动效与微交互优化 | 全局 |

---

## 12. 参考文献

- [UI/UX Pro Max Design System](https://claude.com/claude-code)
- A股涨跌习惯: 红涨绿跌
