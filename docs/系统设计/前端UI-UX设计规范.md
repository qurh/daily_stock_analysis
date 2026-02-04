# 前端 UI/UX 设计规范

**项目名称：** daily_stock_analysis
**文档版本：** v1.0
**创建日期：** 2026-02-04
**文档状态：** 设计方案

---

## 目录

1. [设计概述](#1-设计概述)
2. [设计定位](#2-设计定位)
3. [色彩系统](#3-色彩系统)
4. [字体系统](#4-字体系统)
5. [布局架构](#5-布局架构)
6. [组件规范](#6-组件规范)
7. [页面设计](#7-页面设计)
8. [交互规范](#8-交互规范)
9. [响应式设计](#9-响应式设计)
10. [无障碍规范](#10-无障碍规范)
11. [实施路线图](#11-实施路线图)

---

## 1. 设计概述

### 1.1 项目背景

daily_stock_analysis 是一款 AI 驱动的股票分析系统，主要服务于 A 股和港股市场的个人投资者及专业分析师。系统提供智能选股、行情分析、组合管理、复盘总结、知识库管理等功能，旨在帮助用户做出更科学的投资决策。

当前系统处于架构重构阶段，前端需要从零开始构建全新的用户界面，以匹配现代化的技术架构（Next.js 14 + React 18 + TypeScript）和用户期望。

### 1.2 设计目标

本设计规范旨在建立一套统一、专业、可维护的 UI/UX 标准，确保产品在视觉上具有金融行业的专业感，在交互上符合用户的使用习惯，在技术上便于团队协作和长期维护。具体设计目标包括以下几个方面。

首先是视觉专业性，金融产品需要传递可信赖、专业的感觉，界面设计应当简洁大气，避免过度装饰，让用户专注于数据和决策本身。色彩运用应当克制而有目的，通过色彩传达涨跌、状态等关键信息。

其次是数据可读性，股票分析涉及大量数据，界面设计必须确保数据的清晰呈现。数字格式化需要统一规范，千分位、小数点位数、单位换算都需要符合金融行业的阅读习惯。表格和图表的设计应当便于用户快速获取关键信息。

第三是操作效率，投资者通常需要快速做出决策，界面交互应当流畅高效。常看股票应当一键可达，常用操作应当减少点击步骤，数据更新应当及时反馈。系统应当支持用户自定义常用的视图和布局。

第四是多端适配，用户可能在不同设备上使用系统，界面需要响应式适配。从大屏显示器到手机屏幕，核心功能和数据展示应当保持一致性，同时根据屏幕尺寸进行合理调整。

### 1.3 设计原则

本设计遵循以下核心原则，这些原则贯穿于所有界面设计和交互设计决策中。

**数据优先原则**要求界面的核心功能是呈现数据和辅助决策，其他元素应当服务于这一目标。页面布局应当突出数据和图表，辅助信息退居次要位置。避免不必要的视觉装饰分散用户注意力。

**一致性原则**要求整个应用的视觉和交互保持统一。相同的功能使用相同的视觉表现，相同的交互模式应用于相似的场景。一致性降低用户的学习成本，提高使用效率。

**渐进披露原则**要求首先展示最核心的信息和功能，详细信息和高级功能在用户需要时再呈现。避免一开始就展示过多选项导致用户困惑，同时保证功能的完整性。

**即时反馈原则**要求所有用户操作都应当得到及时、明确的反馈。按钮点击需要视觉反馈，数据加载需要加载状态，操作结果需要成功或失败的提示。

---

## 2. 设计定位

### 2.1 产品类型

本产品属于金融数据分析 Dashboard 类别，核心价值在于帮助用户分析股票行情、管理投资组合、做出投资决策。这类产品通常具有数据密集、信息量大、操作频繁的特点。

### 2.2 目标用户

主要目标用户群体包括以下几类。第一类是个人投资者，他们需要查看行情、分析数据、管理持仓，对界面专业性有一定要求，但更注重易用性。第二类是专业分析师，他们需要更详细的数据、更强大的分析工具，对数据精度和呈现方式有更高要求。第三类是量化交易者，他们需要程序化的接口和自定义的分析视图。

不同用户群体的需求存在差异，设计时需要平衡各方需求，确保基础功能对所有用户友好，高级功能对专业用户可用。

### 2.3 风格定位

基于产品类型和目标用户分析，设计风格定位如下。

**整体风格**定位为专业、简洁、数据驱动。界面不追求花哨的视觉效果，而是通过精心的布局和细节处理，传达专业、可信赖的品牌形象。设计语言现代而不激进，符合金融行业的审美惯例。

**主题模式**以深色模式为主，辅以浅色模式可选。深色模式在金融应用中广泛使用，原因包括：减少长时间使用的眼睛疲劳、突出彩色数据图表、营造专业的交易氛围等。涨跌颜色采用 A 股习惯（红涨绿跌），符合中国用户认知。

**交互密度**采用数据密集型布局，在保证可读性的前提下最大化数据展示空间。页面不使用过大的留白，而是合理利用屏幕空间展示更多有价值的信息。

### 2.4 技术栈

前端技术栈为 Next.js 14 + React 18 + TypeScript + Ant Design。设计规范需要与这一技术栈紧密结合，充分利用 Ant Design 组件库的能力，同时通过主题定制实现设计目标。

---

## 3. 色彩系统

### 3.1 设计理念

金融应用的色彩系统需要在功能性和美观性之间取得平衡。色彩首先服务于信息传达，通过颜色用户可以快速识别涨跌、状态、风险等信息。在此基础上，色彩搭配应当营造专业、舒适的视觉体验。

深色主题是金融应用的主流选择，原因包括：深色背景可以更好地衬托彩色图表和数据、减少长时间使用的视觉疲劳、在弱光环境下更友好、营造专业的交易氛围。

### 3.2 核心色板

#### 3.2.1 背景层

背景色采用渐进式的深色层次，从主背景到卡片背景再到输入框背景，颜色逐渐变浅，形成清晰的层次关系。

| 角色 | CSS 变量 | 色值 | 用途说明 |
|------|----------|------|----------|
| 页面主背景 | `--bg-primary` | `#0F172A` | 最深的背景色，用于整个页面背景 |
| 卡片背景 | `--bg-secondary` | `#1E293B` | 用于卡片、面板等独立区域 |
| 次级背景 | `--bg-tertiary` | `#334155` | 用于输入框、选中状态、次级区域 |

#### 3.2.2 文字层

文字颜色同样采用层次设计，确保在不同背景上都有良好的可读性。文字颜色的选择需要满足 WCAG AA 标准（4.5:1 对比度）。

| 角色 | CSS 变量 | 色值 | 用途说明 |
|------|----------|------|----------|
| 主标题 | `--text-primary` | `#F8FAFC` | 最重要的文字，如标题、数字 |
| 次要文字 | `--text-secondary` | `#94A3B8` | 辅助说明、标签、单位 |
| 禁用文字 | `--text-muted` | `#64748B` | 占位符、禁用状态、提示 |

#### 3.2.3 品牌色

品牌色用于主要的交互元素和强调信息，需要在深色背景上有足够的可见度。

| 角色 | CSS 变量 | 色值 | 用途说明 |
|------|----------|------|----------|
| 主色 | `--primary` | `#3B82F6` | 主要交互色、链接、选中状态 |
| 主色悬停 | `--primary-hover` | `#2563EB` | 按钮、链接悬停状态 |
| 强调色 | `--accent` | `#F59E0B` | CTA 按钮、重要提示 |
| 成功色 | `--success` | `#22C55E` | 成功状态、确认操作 |
| 警告色 | `--warning` | `#F59E0B` | 警告状态、待处理事项 |
| 错误色 | `--error` | `#EF4444` | 错误状态、危险操作 |
| 信息色 | `--info` | `#3B82F6` | 信息提示 |

#### 3.2.4 涨跌色

涨跌色是金融应用最核心的功能色，需要特别注意颜色含义与用户认知的一致性。中国 A 股市场习惯使用红色表示上涨、绿色表示下跌，这与西方市场的习惯相反，本设计采用 A 股习惯。

| 角色 | CSS 变量 | 色值 | 用途说明 |
|------|----------|------|----------|
| 上涨 | `--rise` | `#EF4444` | 价格上涨、正收益 |
| 上涨背景 | `--rise-bg` | `rgba(239, 68, 68, 0.15)` | 上涨相关元素的浅色背景 |
| 下跌 | `--fall` | `#22C55E` | 价格下跌、负收益 |
| 下跌背景 | `--fall-bg` | `rgba(34, 197, 94, 0.15)` | 下跌相关元素的浅色背景 |
| 平盘 | `--neutral` | `#64748B` | 价格持平、无变化 |

#### 3.2.5 边框与分隔

| 角色 | CSS 变量 | 色值 | 用途说明 |
|------|----------|------|----------|
| 边框 | `--border` | `#334155` | 元素边框、分隔线 |
| 浅边框 | `--border-light` | `#475569` | 悬停状态、次级边框 |

### 3.3 完整 CSS 变量定义

```css
:root {
  /* 背景层 */
  --bg-primary: #0F172A;
  --bg-secondary: #1E293B;
  --bg-tertiary: #334155;

  /* 文字层 */
  --text-primary: #F8FAFC;
  --text-secondary: #94A3B8;
  --text-muted: #64748B;

  /* 品牌色 */
  --primary: #3B82F6;
  --primary-hover: #2563EB;
  --accent: #F59E0B;

  /* 状态色 */
  --success: #22C55E;
  --warning: #F59E0B;
  --error: #EF4444;
  --info: #3B82F6;

  /* 涨跌色 - A股习惯：红涨绿跌 */
  --rise: #EF4444;
  --rise-bg: rgba(239, 68, 68, 0.15);
  --fall: #22C55E;
  --fall-bg: rgba(34, 197, 94, 0.15);
  --neutral: #64748B;

  /* 边框 */
  --border: #334155;
  --border-light: #475569;

  /* 圆角 */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;

  /* 阴影 */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
}
```

### 3.4 Ant Design 主题配置

```typescript
// src/theme/darkTheme.ts
import type { ThemeConfig } from 'antd'

export const darkTheme: ThemeConfig = {
  token: {
    // 品牌色
    colorPrimary: '#3B82F6',
    colorPrimaryHover: '#2563EB',
    colorPrimaryActive: '#1D4ED8',
    colorAccent: '#F59E0B',

    // 状态色
    colorSuccess: '#22C55E',
    colorWarning: '#F59E0B',
    colorError: '#EF4444',
    colorInfo: '#3B82F6',

    // 背景色
    colorBgContainer: '#1E293B',
    colorBgElevated: '#334155',
    colorBgLayout: '#0F172A',
    colorBgSpotlight: '#334155',

    // 文字色
    colorText: '#F8FAFC',
    colorTextSecondary: '#94A3B8',
    colorTextTertiary: '#64748B',
    colorTextQuaternary: '#475569',

    // 边框色
    colorBorder: '#334155',
    colorBorderSecondary: '#475569',

    // 圆角
    borderRadius: 8,

    // 字体
    fontFamily: "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",

    // 字号
    fontSize: 14,
    fontSizeSM: 12,
    fontSizeLG: 16,
    fontSizeXL: 20,
    fontSizeHeading1: 38,
    fontSizeHeading2: 30,
    fontSizeHeading3: 24,
    fontSizeHeading4: 20,
    fontSizeHeading5: 16,
  },
  components: {
    Layout: {
      headerBg: '#0F172A',
      headerHeight: 56,
      siderBg: '#0F172A',
      bodyBg: '#0F172A',
    },
    Card: {
      colorBgContainer: '#1E293B',
      headerBg: 'transparent',
      headerBorderColor: '#334155',
      paddingLG: 20,
      borderRadiusLG: 12,
    },
    Table: {
      colorBgContainer: '#1E293B',
      headerBg: '#1E293B',
      headerColor: '#94A3B8',
      rowHoverBg: '#334155',
      rowSelectedBg: 'rgba(59, 130, 246, 0.15)',
      rowSelectedHoverBg: 'rgba(59, 130, 246, 0.2)',
      borderColor: '#334155',
      headerBorderColor: '#334155',
    },
    Button: {
      primaryShadow: 'none',
      defaultShadow: 'none',
    },
    Input: {
      colorBgContainer: '#1E293B',
      borderColor: '#334155',
      hoverBorderColor: '#475569',
      activeBorderColor: '#3B82F6',
    },
    Select: {
      colorBgContainer: '#1E293B',
      borderColor: '#334155',
    },
    Tag: {
      defaultBg: '#334155',
    },
    Menu: {
      darkItemBg: '#0F172A',
      darkSubMenuItemBg: '#1E293B',
    },
    Modal: {
      colorBgContainer: '#1E293B',
      headerBg: '#1E293B',
      contentBg: '#1E293B',
    },
    Tabs: {
      inkBarColor: '#3B82F6',
      itemColor: '#94A3B8',
      itemHoverColor: '#F8FAFC',
      itemActiveColor: '#3B82F6',
    },
    Tooltip: {
      colorBgSpotlight: '#1E293B',
    },
    Message: {
      contentBg: '#1E293B',
    },
    Notification: {
      contentBg: '#1E293B',
    },
  },
}
```

### 3.5 涨跌色应用规范

涨跌色的使用需要严格遵守以下规范，确保用户可以快速准确地获取信息。

**数字颜色**的使用规则是：上涨数字使用红色（`#EF4444`），下跌数字使用绿色（`#22C55E`），平盘数字使用灰色（`#64748B`）。正数前的正号（+）需要明确显示，以便用户区分上涨和持平。

**背景色的使用**规则是：在需要强调涨跌状态时，可以使用浅色背景作为辅助。上涨背景为 `rgba(239, 68, 68, 0.15)`，下跌背景为 `rgba(34, 197, 94, 0.15)`。背景色应当谨慎使用，避免页面过于花哨。

**箭头图标**的使用规则是：上涨使用向上箭头（↑），下跌使用向下箭头（↓），平盘使用横线（—）或不显示箭头。箭头颜色与文字颜色一致。

**K线图颜色**采用标准配色：阳线（上涨）使用红色（`#EF4444`），阴线（下跌）使用绿色（`#22C55E`）。这一配色与 A 股交易软件一致，符合用户习惯。

---

## 4. 字体系统

### 4.1 字体选择

金融应用对字体的要求较高，主要体现在以下几个方面。首先是数字的可读性，股票价格、涨跌幅等数字需要清晰易读，避免歧义。其次是中西文混排的协调性，界面中经常需要同时显示中文和英文、数字、符号等。第三是长时间阅读的舒适度，用户可能长时间盯着屏幕查看行情。

基于以上考虑，推荐使用 IBM Plex Sans 作为主要字体。这是一款专为屏幕阅读优化的无衬线字体，具有良好的数字呈现和跨语言协调性。

```css
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');
```

备用字体链为：`'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif`。

### 4.2 字号规范

字号设计遵循 4px 基础网格系统，确保视觉上的节奏感和一致性。

| 用途 | 字号 | 行高 | 字重 | CSS 类 |
|------|------|------|------|--------|
| 大标题 | 32px | 40px | 600 | `text-4xl` |
| 中标题 | 24px | 32px | 600 | `text-3xl` |
| 小标题 | 20px | 28px | 500 | `text-2xl` |
| 卡片标题 | 16px | 24px | 500 | `text-lg` |
| 正文 | 14px | 22px | 400 | `text-base` |
| 辅助文字 | 12px | 20px | 400 | `text-sm` |
| 标签文字 | 12px | 18px | 500 | `text-xs` |
| 数据大号 | 24px | 32px | 600 | `data-xl` |
| 数据中号 | 20px | 28px | 600 | `data-lg` |
| 数据小号 | 16px | 24px | 600 | `data-base` |

### 4.3 字重规范

字重的使用需要保持一致性，避免随意变化导致视觉混乱。

| 字重 | 数值 | 用途 |
|------|------|------|
| Light | 300 | 大段正文（可选） |
| Regular | 400 | 默认字重，用于正文、辅助说明 |
| Medium | 500 | 强调文字、标签、小标题 |
| Semibold | 600 | 标题、数字、需要突出的信息 |
| Bold | 700 | 极少使用，仅用于特殊强调 |

### 4.4 行高与字间距

适当的行高和字间距对可读性至关重要。

行高规范：标题行高为字号的 1.2-1.25 倍，正文行高为字号的 1.5-1.75 倍。金融数据表格行高为 40-48px，确保数据清晰可读。

字间距规范：中文默认字间距，数字使用默认或略微收紧（-0.02em），英文大写字母可略微增加字间距（0.02-0.05em）。

### 4.5 数字格式化

数字格式化是金融应用的关键功能，需要严格规范以确保信息准确传达。

```typescript
// src/utils/format.ts

/**
 * 格式化价格
 * @param value - 价格数值
 * @param decimals - 小数位数，默认2位
 * @returns 格式化后的价格字符串
 */
export function formatPrice(value: number, decimals: number = 2): string {
  if (value === null || value === undefined) return '-'
  return `¥${value.toFixed(decimals)}`
}

/**
 * 格式化涨跌幅
 * @param value - 涨跌幅数值
 * @returns 格式化后的涨跌幅字符串
 */
export function formatPct(value: number): string {
  if (value === null || value === undefined) return '-'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

/**
 * 格式化成交量
 * @param value - 成交量数值
 * @returns 格式化后的成交量字符串
 */
export function formatVolume(value: number): string {
  if (value === null || value === undefined) return '-'
  if (value >= 100000000) return `${(value / 100000000).toFixed(2)}万手`
  if (value >= 10000) return `${(value / 10000).toFixed(2)}万手`
  return `${value.toLocaleString()}手`
}

/**
 * 格式化成交额
 * @param value - 成交额数值
 * @returns 格式化后的成交额字符串
 */
export function formatAmount(value: number): string {
  if (value === null || value === undefined) return '-'
  if (value >= 100000000) return `¥${(value / 100000000).toFixed(2)}亿`
  if (value >= 10000) return `¥${(value / 10000).toFixed(2)}万`
  return `¥${value.toLocaleString()}`
}

/**
 * 格式化市值
 * @param value - 市值数值
 * @returns 格式化后的市值字符串
 */
export function formatMarketCap(value: number): string {
  if (value === null || value === undefined) return '-'
  if (value >= 1000000000000) return `${(value / 1000000000000).toFixed(2)}万亿`
  if (value >= 100000000) return `${(value / 100000000).toFixed(2)}亿`
  return value.toLocaleString()
}

/**
 * 格式化百分比
 * @param value - 百分比数值
 * @param decimals - 小数位数
 * @returns 格式化后的百分比字符串
 */
export function formatPercent(value: number, decimals: number = 2): string {
  if (value === null || value === undefined) return '-'
  return `${value.toFixed(decimals)}%`
}

/**
 * 格式化市盈率
 * @param value - 市盈率数值
 * @returns 格式化后的市盈率字符串
 */
export function formatPE(value: number): string {
  if (value === null || value === undefined) return '-'
  if (value < 0) return '亏损'
  return value.toFixed(2)
}

/**
 * 格式化换手率
 * @param value - 换手率数值
 * @returns 格式化后的换手率字符串
 */
export function formatTurnover(value: number): string {
  if (value === null || value === undefined) return '-'
  return `${value.toFixed(2)}%`
}

/**
 * 格式化数字（千分位）
 * @param value - 数值
 * @param decimals - 小数位数
 * @returns 格式化后的数字字符串
 */
export function formatNumber(value: number, 2 decimals: number =): string {
  if (value === null || value === undefined) return '-'
  return value.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

/**
 * 格式化金额（千分位+货币符号）
 * @param value - 金额数值
 * @param decimals - 小数位数
 * @returns 格式化后的金额字符串
 */
export function formatCurrency(value: number, currency: string = 'CNY', decimals: number = 2): string {
  if (value === null || value === undefined) return '-'
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}
```

### 4.6 涨跌样式工具函数

```typescript
// src/utils/price.ts

export type PriceTrend = 'up' | 'down' | 'neutral'

/**
 * 获取价格趋势类型
 * @param value - 价格或涨跌幅数值
 * @returns 趋势类型
 */
export function getPriceTrend(value: number): PriceTrend {
  if (value > 0) return 'up'
  if (value < 0) return 'down'
  return 'neutral'
}

/**
 * 涨跌颜色映射
 */
export const PRICE_COLORS = {
  up: {
    text: '#EF4444',
    bg: 'rgba(239, 68, 68, 0.15)',
    border: 'rgba(239, 68, 68, 0.3)',
  },
  down: {
    text: '#22C55E',
    bg: 'rgba(34, 197, 94, 0.15)',
    border: 'rgba(34, 197, 94, 0.3)',
  },
  neutral: {
    text: '#64748B',
    bg: 'rgba(100, 116, 139, 0.15)',
    border: 'rgba(100, 116, 139, 0.3)',
  },
}

/**
 * 涨跌箭头图标
 */
export const PRICE_ARROWS = {
  up: '↑',
  down: '↓',
  neutral: '—',
}
```

---

## 5. 布局架构

### 5.1 全局布局结构

系统采用顶部导航栏加页面内容的经典布局，这种布局在金融应用中广泛使用，原因是可以最大化数据展示区域，同时保持导航的清晰可见。

```
┌─────────────────────────────────────────────────────────────────────┐
│                         顶部导航栏 (56px)                            │
│  Logo    市场    复盘    知识库    组合    监控    策略      搜索   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│                         页面主要内容区域                            │
│                                                                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 导航架构

顶部导航包含以下核心模块，模块顺序按照用户使用频率和功能重要性排列。

| 模块 | 路由 | 功能说明 | 优先级 |
|------|------|----------|--------|
| 市场 | /market | 行情查看、股票筛选、图表分析 | P0 |
| 复盘 | /review | 日/周复盘、日历回顾 | P1 |
| 知识库 | /knowledge | 文档管理、搜索、RAG | P1 |
| 组合 | /portfolio | 持仓管理、收益分析、交易记录 | P0 |
| 监控 | /monitor | 告警设置、状态监控 | P2 |
| 策略 | /strategy | 策略管理、回测 | P2 |

导航栏右侧常驻以下功能：全局搜索、通知中心、设置、用户菜单。

### 5.3 页面布局类型

根据页面功能特点，定义两种主要布局类型。

**Dashboard 型布局**用于市场、组合、监控等数据密集型页面，布局特点如下：顶部为 KPI 卡片区域（4 列网格），中部为主图表区域（自适应宽度），底部为数据表格区域（带筛选和分页）。

```
┌────────────────────────────────────────────────────────────┐
│  KPI卡片1   │  KPI卡片2   │  KPI卡片3   │  KPI卡片4        │
├────────────────┴────────────────┴────────────────┴──────────┤
│                                                             │
│                      主图表区域                              │
│                    (自适应宽度/高度)                         │
│                                                             │
├────────────────────────────────────────────────────────────┤
│                                                             │
│                     数据表格区域                             │
│                  (筛选、分页、列配置)                        │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

**内容型布局**用于知识库、设置等以内容为主的页面，布局特点如下：左侧为导航树或列表（固定宽度），右侧为主内容区域（自适应剩余宽度）。

```
┌──────────────────────┬────────────────────────────────────┐
│                      │                                     │
│    左侧导航树        │         主内容区域                  │
│    (280px)          │                                     │
│                      │                                     │
│                      │                                     │
│                      │                                     │
└──────────────────────┴────────────────────────────────────┘
```

### 5.4 间距系统

间距设计遵循 4px 基础网格，确保视觉节奏的一致性。

| 间距级别 | px 值 | 使用场景 |
|----------|-------|----------|
| xs | 4px | 元素内部紧凑间距 |
| sm | 8px | 相关元素间距 |
| md | 16px | 区块间距 |
| lg | 24px | 主要区块间距 |
| xl | 32px | 大区块间距 |
| 2xl | 48px | 页面边距 |
| 3xl | 64px | 最大间距 |

### 5.5 容器宽度

不同内容区域使用不同的最大宽度限制，确保阅读舒适度。

| 容器类型 | 最大宽度 | 使用场景 |
|----------|----------|----------|
| 全宽 | 100% | 图表、数据表格 |
| 内容区 | 1400px | 页面主要内容 |
| 弹窗 | 600-900px | 表单弹窗 |
| 卡片 | 100% | 适应父容器 |

---

## 6. 组件规范

### 6.1 通用组件

#### 6.1.1 卡片组件

卡片是界面中最常用的容器组件，用于承载独立的信息区块。

```tsx
// 标准卡片
<Card className="data-card">
  <Card.Meta
    title="卡片标题"
    description="卡片描述"
  />
  {/* 卡片内容 */}
</Card>

// 加载状态
<Card loading={loading}>
  {/* 内容 */}
</Card>
```

卡片样式规范：背景色为 `--bg-secondary`（`#1E293B`），边框为 `--border`（`#334155`，1px），圆角为 `--radius-lg`（12px），内边距为 20px，悬停效果为轻微阴影或边框颜色变化。

#### 6.1.2 按钮组件

按钮是界面中最常用的交互组件，需要明确区分不同类型和层级。

```tsx
// 主按钮
<Button type="primary">主按钮</Button>

// 次按钮
<Button>次按钮</Button>

// 文字按钮
<Button type="text">文字按钮</Button>

// 危险按钮
<Button danger>危险操作</Button>

// 图标按钮
<Button icon={<SearchOutlined />}>搜索</Button>
```

按钮样式规范：主按钮背景色为 `--primary`（`#3B82F6`），主按钮悬停背景色为 `--primary-hover`（`#2563EB`），圆角为 `--radius-md`（8px），高度为 36px 或 40px，禁用状态下不透明度为 0.5。

#### 6.1.3 标签组件

标签用于简短信息的分类和标注。

```tsx
//涨跌标签
<Tag color={value > 0 ? 'rise' : value < 0 ? 'fall' : 'neutral'}>
  {formatPct(value)}
</Tag>

//状态标签
<Tag color="success">已启用</Tag>
<Tag color="warning">待处理</Tag>
```

标签样式规范：背景色为对应颜色的浅色背景（15% 透明度），文字色为对应颜色，圆角为 `--radius-sm`（4px），内边距为 2px 8px。

### 6.2 数据展示组件

#### 6.2.1 统计数值组件

用于展示核心 KPI 数据。

```tsx
<Statistic
  title="总资产"
  value={112233.44}
  precision={2}
  prefix={<DollarOutlined />}
  valueStyle={{ color: '#F8FAFC' }}
/>
```

#### 6.2.2 涨跌幅指示器

用于展示价格变化的趋势指示。

```tsx
<div className="price-indicator">
  <span className={`price-value ${trend}`}>
    {formatPrice(value)}
  </span>
  <Tag color={trend === 'up' ? 'rise' : trend === 'down' ? 'fall' : 'neutral'}>
    {PRICE_ARROWS[trend]} {formatPct(pct)}
  </Tag>
</div>
```

### 6.3 表格组件

表格是金融应用最核心的数据展示组件，需要特别重视其设计和交互。

#### 6.3.1 标准行情表格

```tsx
<Table
  columns={[
    {
      title: '股票',
      dataIndex: 'name',
      width: 140,
      render: (_, record) => (
        <div>
          <div style={{ fontWeight: 500 }}>{record.code}</div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
            {record.name}
          </div>
        </div>
      ),
    },
    {
      title: '价格',
      dataIndex: 'price',
      align: 'right',
      width: 100,
      render: (value) => (
        <span style={{ color: value >= 0 ? 'var(--rise)' : 'var(--fall)' }}>
          {formatPrice(value)}
        </span>
      ),
    },
    {
      title: '涨跌幅',
      dataIndex: 'pct_chg',
      align: 'right',
      width: 100,
      render: (value) => (
        <Tag color={value > 0 ? 'rise' : value < 0 ? 'fall' : 'neutral'}>
          {formatPct(value)}
        </Tag>
      ),
    },
    {
      title: '成交量',
      dataIndex: 'volume',
      align: 'right',
      width: 120,
      render: (value) => formatVolume(value),
    },
    {
      title: '成交额',
      dataIndex: 'amount',
      align: 'right',
      width: 120,
      render: (value) => formatAmount(value),
    },
    {
      title: '换手率',
      dataIndex: 'turnover',
      align: 'right',
      width: 100,
      render: (value) => formatTurnover(value),
    },
    {
      title: '操作',
      key: 'actions',
      width: 80,
      render: (_, record) => (
        <Space>
          <Button type="text" size="small" icon={<EyeOutlined />}>
            查看
          </Button>
        </Space>
      ),
    },
  ]}
  dataSource={data}
  rowKey="code"
  size="small"
  pagination={{ pageSize: 10 }}
  scroll={{ x: 900 }}
  loading={loading}
  rowClassName={(_, index) =>
    index % 2 === 0 ? 'table-row-even' : 'table-row-odd'
  }
/>
```

表格样式规范：表头背景色为 `--bg-tertiary`（`#334155`），表头文字色为 `--text-secondary`（`#94A3B8`），行高为 40px 或 48px，奇偶行交替背景（可选），悬停行背景为 `--bg-tertiary`（`#334155`），选中行背景为 `rgba(59, 130, 246, 0.15)`，固定列阴影为渐变透明遮罩。

#### 6.3.2 表格交互规范

行悬停效果为背景色变为 `--bg-tertiary`，行选中效果为背景色变为 `rgba(59, 130, 246, 0.15)`，列排序效果为点击列头显示排序图标，支持升序和降序，列配置功能为支持右键菜单或列配置按钮，可显隐列和调整列宽。

### 6.4 图表组件

#### 6.4.1 图表颜色规范

```typescript
// src/constants/chartColors.ts

export const CHART_COLORS = {
  // K线颜色 - A股习惯
  up: '#EF4444',      // 上涨（红）
  down: '#22C55E',    // 下跌（绿）
  neutral: '#64748B', // 平盘（灰）

  // 均线颜色
  ma5: '#F59E0B',   // MA5 橙色
  ma10: '#3B82F6',  // MA10 蓝色
  ma20: '#8B5CF6',  // MA20 紫色

  // MACD 指标颜色
  macd: {
    dif: '#3B82F6',  // DIF 线蓝色
    dea: '#F59E0B',  // DEA 线橙色
    hist: {
      positive: 'rgba(239, 68, 68, 0.6)',  // 红柱
      negative: 'rgba(34, 197, 94, 0.6)',  // 绿柱
    },
  },

  // KDJ 指标颜色
  kdj: {
    k: '#F59E0B',   // K 线橙色
    d: '#3B82F6',   // D 线蓝色
    j: '#EC4899',   // J 线粉色
  },

  // 背景与网格
  grid: '#334155',    // 网格线
  axisLine: '#475569', // 坐标轴线
  background: 'transparent',
  tooltipBg: '#1E293B',
  tooltipText: '#F8FAFC',

  // 主题色
  primary: '#3B82F6',
  secondary: '#64748B',
  success: '#22C55E',
  warning: '#F59E0B',
  error: '#EF4444',
}
```

#### 6.4.2 推荐图表库

**Recharts** 用于 K 线以外的所有图表，优点包括 React 原生集成、TypeScript 类型支持好、API 设计直观、包体较小。

**Lightweight Charts**（TradingView）用于专业 K 线图，优点包括专为金融设计、性能优秀、专业级 K 线渲染、支持多种图表类型。

### 6.5 表单组件

表单用于用户输入数据，需要保持一致性和易用性。

```tsx
<Form form={form} layout="vertical">
  <Form.Item
    name="code"
    label="股票代码"
    rules={[{ required: true, message: '请输入股票代码' }]}
  >
    <Input placeholder="如: 600519" />
  </Form.Item>

  <Form.Item
    name="quantity"
    label="持仓数量"
    rules={[{ required: true, message: '请输入持仓数量' }]}
  >
    <InputNumber style={{ width: '100%' }} min={1} placeholder="股数" />
  </Form.Item>
</Form>
```

表单样式规范：标签文字色为 `--text-secondary`，输入框背景色为 `--bg-tertiary`，输入框边框色为 `--border`，输入框圆角为 `--radius-md`，错误提示文字色为 `--error`。

---

## 7. 页面设计

### 7.1 市场页面（Market）

市场页面是用户最常用的页面，提供行情查看、股票筛选、图表分析等功能。

**页面结构如下。**

顶部区域包含搜索栏、日期选择、常用指数快捷入口。搜索栏支持股票代码和名称模糊搜索，日期选择用于历史数据查看，指数入口包括上证指数、深证成指、创业板指、科创50 等。

KPI 卡片区域包含四个核心指标：上涨家数、下跌家数、成交额、涨停数。这些指标帮助用户快速了解市场整体状况。

主图表区域展示大盘指数走势，支持日线、周线、月线切换，支持叠加均线、MACD、KDJ 等指标。

股票列表区域展示实时行情，支持多维度排序、条件筛选、自定义列配置。

**交互设计如下。**

点击股票行可查看详情弹窗，支持快捷添加自选、添加到组合等操作。双击股票行可进入股票详情页。点击列表头部可进行列排序，支持多列排序。右键菜单提供更多操作选项。

### 7.2 组合页面（Portfolio）

组合页面展示用户的持仓信息和收益情况。

**页面结构如下。**

KPI 卡片区域包含五个核心指标：总资产、浮动盈亏、收益率、持仓数量、可用资金。其中浮动盈亏使用涨跌色标识，收益率正负使用涨跌色标识。

收益图表区域展示资产净值走势，支持按日、周、月查看，支持与沪深 300 指数对比。

持仓列表区域展示当前持仓股票的详细信息，包括成本价、当前价、浮动盈亏、收益率、仓位占比等。支持编辑、删除操作。

交易记录区域展示近期买卖记录，支持筛选和搜索。

**交互设计如下。**

点击持仓行可查看持仓详情，支持修改持仓信息。点击添加持仓按钮弹出表单弹窗。点击删除按钮需要二次确认。持仓排序支持按收益率、涨跌幅、市值等多维度。

### 7.3 复盘页面（Review）

复盘页面提供日/周复盘报告的查看和编辑功能。

**页面结构如下。**

日历导航区域展示当前月份的复盘日期，支持月份切换。点击日期可查看当天的复盘报告。

复盘报告区域展示选中的复盘报告内容，包括市场概览、重点板块、交易回顾、经验总结等。

新建复盘区域提供创建新复盘的入口，可选择日期。

**交互设计如下。**

点击日历日期查看对应复盘，日期有复盘记录时显示标记。点击新建复盘按钮弹出表单弹窗。复盘内容支持 Markdown 编辑。保存后自动触发 AI 分析（可选）。

### 7.4 知识库页面（Knowledge）

知识库页面提供文档管理、搜索、RAG 问答等功能。

**页面结构如下。**

左侧导航树展示文档分类和文档列表，支持展开折叠、搜索过滤。右侧内容区展示选中文档的详细内容或搜索结果。

编辑器区域提供新建/编辑文档的功能，支持 Markdown 格式。

**交互设计如下。**

点击文档在右侧查看详情。点击编辑按钮进入编辑模式。点击删除按钮需要二次确认。搜索支持全文检索和关键词高亮。支持一键导入对话内容到知识库。

### 7.5 监控页面（Monitor）

监控页面提供告警设置和系统状态监控。

**页面结构如下。**

状态概览区域展示系统运行状态、数据更新状态、API 调用统计等。告警列表区域展示已设置的告警规则和触发记录。告警配置区域提供新增/编辑告警规则的表单。

**交互设计如下。**

点击告警规则可查看详情和修改。点击新增告警按钮弹出配置表单。告警触发时显示通知。支持设置告警接收渠道。

### 7.6 策略页面（Strategy）

策略页面提供量化策略的管理和回测功能。

**页面结构如下。**

策略列表区域展示已创建的策略，包括策略名称、类型、状态、收益等。策略详情区域展示选中策略的参数配置和回测结果。回测配置区域提供设置回测参数和运行的界面。

**交互设计如下。**

点击策略查看详情和回测结果。点击新建策略按钮进入策略创建向导。回测运行需要较长时间，显示进度条和取消选项。结果展示支持图表和数据表格。

---

## 8. 交互规范

### 8.1 动效规范

动效使用需要克制，服务于功能而非装饰。适当的动效可以提升用户体验，但过度使用会影响性能和可读性。

#### 8.1.1 动效时长

| 动效类型 | 时长 | 使用场景 |
|----------|------|----------|
| 微交互 | 150ms | 按钮 hover、图标切换、复选框 |
| 过渡 | 200ms | 卡片展开、菜单收起、弹窗 |
| 加载 | 800ms | 骨架屏动画周期 |
| 图表入场 | 500ms | 图表数据更新 |
| 列表更新 | 300ms | 列表项增删 |

#### 8.1.2 缓动函数

默认缓动函数为 `ease-in-out`，快速交互可使用 `ease-out`，入场动画可使用 `ease-in`。

```css
transition: all 200ms ease-in-out;
animation: fadeIn 200ms ease-out;
```

### 8.2 加载状态

加载状态的设计直接影响用户对系统响应速度的感知，需要根据加载时间选择合适的展示方式。

**骨架屏**适用于页面或区块的整体加载，等待时间超过 1 秒时使用。骨架屏应当模拟真实内容的布局，让用户对加载内容有预期。

```tsx
<Skeleton active paragraph={{ rows: 4 }} />

<Skeleton active>
  <div className="chart-placeholder" />
</Skeleton>
```

**Spinner**适用于小范围加载，等待时间较短（1 秒以内）时使用。Spinner 应当放置在加载区域的中心位置。

```tsx
<Spin size="small" />

<div className="loading-container">
  <Spin size="large" tip="加载中..." />
</div>
```

**进度条**适用于加载时间较长且有明确进度的场景，如文件上传、长时间数据请求等。

```tsx
<Progress percent={50} status="active" />
```

### 8.3 数据更新指示

实时数据需要清晰展示更新时间，让用户了解数据的时效性。

```tsx
<div className="update-indicator">
  <span className="pulse-dot" />
  <span className="update-time">
    更新于 {lastUpdateTime}
  </span>
  <Button type="text" size="small" onClick={refresh} loading={refreshing}>
    刷新
  </Button>
</div>

<style>
.pulse-dot {
  width: 8px;
  height: 8px;
  background: var(--success);
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.9); }
}
</style>
```

### 8.4 错误处理

错误信息的展示需要清晰、友好、有建设性。

**全局错误**使用全局通知组件展示，停留时间 3 秒。

```tsx
message.error('操作失败，请稍后重试')

notification.error({
  message: '请求失败',
  description: '网络连接异常，请检查网络设置',
})
```

**表单错误**在表单字段下方显示具体错误信息。

```tsx
<Form.Item
  name="code"
  label="股票代码"
  rules={[{ required: true, message: '请输入股票代码' }]}
>
  <Input />
</Form.Item>
```

**空状态**使用友好的提示和操作引导。

```tsx
<Empty
  description="暂无数据"
  image={Empty.PRESENTED_IMAGE_SIMPLE}
>
  <Button type="primary" onClick={handleAdd}>
    添加第一条数据
  </Button>
</Empty>
```

### 8.5 确认操作

危险操作需要二次确认，避免误操作造成损失。

```tsx
<Popconfirm
  title="确认删除"
  description="确定要删除这个持仓吗？此操作不可恢复。"
  onConfirm={handleDelete}
  okText="确认"
  cancelText="取消"
  okButtonProps={{ danger: true }}
>
  <Button danger>删除</Button>
</Popconfirm>

<Modal
  title="确认操作"
  open={confirmVisible}
  onOk={handleConfirm}
  onCancel={() => setConfirmVisible(false)}
>
  <p>确定要执行此操作吗？</p>
</Modal>
```

---

## 9. 响应式设计

### 9.1 断点定义

响应式断点采用业界通用标准，确保在主流设备上的良好体验。

| 断点 | 宽度 | 设备类型 |
|------|------|----------|
| sm | 640px | 手机横屏、小屏平板 |
| md | 768px | 平板竖屏 |
| lg | 1024px | 平板横屏、笔记本 |
| xl | 1280px | 桌面显示器 |
| 2xl | 1536px | 大屏显示器 |

Tailwind CSS 使用：`sm:、md:、lg:、xl:、2xl:` 前缀。

### 9.2 响应式布局策略

**Dashboard 型页面**在不同屏幕宽度下的布局变化如下。在 xl 以上屏幕（1280px+），使用 4 列 KPI 卡片，表格显示全部列。在 lg 屏幕（1024px-1280px），使用 3 列 KPI 卡片，表格可收起部分次要列。在 md 屏幕（768px-1024px），使用 2 列 KPI 卡片，表格横向滚动，主图表高度降低。在 sm 屏幕（640px-768px），使用单列 KPI 卡片，表格简化显示关键列，主图表单独占一行。在 sm 以下屏幕（<640px），KPI 卡片单列显示，表格卡片化展示，主图表高度进一步降低。

**内容型页面**在不同屏幕宽度下的布局变化如下。在 xl 以上屏幕，左侧导航 280px 固定，右侧内容自适应。在 lg 屏幕（1024px-1280px），左侧导航 240px。在 md 屏幕（768px-1024px），左侧导航可收起，变为抽屉式。在 sm 屏幕（<768px），左侧导航完全隐藏，改为底部标签栏或汉堡菜单。

### 9.3 响应式组件示例

```tsx
<div className="grid-container">
  {/* KPI 卡片 - 不同屏幕不同列数 */}
  <div className="col-span-1 sm:col-span-2 lg:col-span-1">
    <KpiCard />
  </div>

  {/* 图表卡片 - 不同屏幕不同高度 */}
  <div className="h-64 sm:h-80 lg:h-96">
    <ChartCard />
  </div>

  {/* 表格 - 不同屏幕不同列数 */}
  <div className="overflow-x-auto">
    <Table
      scroll={{ x: 640 }}
      size={window.innerWidth < 768 ? 'small' : 'default'}
    />
  </div>
</div>
```

### 9.4 移动端导航

移动端采用底部导航栏加顶部搜索栏的组合，节省屏幕空间。

```tsx
// 底部导航栏
const bottomNavItems = [
  { key: 'market', icon: <ChartOutlined />, label: '市场' },
  { key: 'portfolio', icon: <WalletOutlined />, label: '组合' },
  { key: 'review', icon: <CalendarOutlined />, label: '复盘' },
  { key: 'knowledge', icon: <BookOutlined />, label: '知识库' },
]

// 顶部可收起搜索栏
<SearchBar collapsed={searchCollapsed} onToggle={() => setSearchCollapsed(!searchCollapsed)} />
```

---

## 10. 无障碍规范

### 10.1 色彩对比度

所有文字与背景的对比度必须满足 WCAG AA 标准（4.5:1），大号文字（18px+ 或 14px 粗体）满足 3:1。

使用工具检查：Chrome DevTools → Elements → Styles → Contrast ratio。

### 10.2 键盘导航

所有交互元素必须可以通过键盘访问和操作。

```tsx
<Button
  tabIndex={0}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleClick()
    }
  }}
>
  确认
</Button>
```

焦点状态需要清晰可见：

```css
button:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}
```

### 10.3 ARIA 属性

为非文本交互元素添加 ARIA 标签：

```tsx
<Button
  aria-label="删除持仓"
  aria-describedby="delete-help"
  icon={<DeleteOutlined />}
  onClick={handleDelete}
/>
<span id="delete-help" className="sr-only">
  删除当前选中的持仓记录
</span>

<div
  role="region"
  aria-label="股票行情表格"
  aria-describedby="table-description"
>
  <Table aria-label="股票行情" />
</div>
<span id="table-description" className="sr-only">
  展示沪深两市主要股票的最新行情数据
</span>
```

### 10.4 屏幕阅读器支持

为动态内容更新添加 Live Region：

```tsx
<div
  role="status"
  aria-live="polite"
  aria-atomic="true"
  className="sr-only"
>
  {statusMessage}
</div>

// 价格更新时
<div
  role="status"
  aria-live="assertive"
  className="sr-only"
>
  {stock.code} 当前价格 {formatPrice(stock.price)}，涨跌 {formatPct(stock.pct_chg)}
</div>
```

### 10.5 减少动画

尊重用户的减少动画偏好：

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

在 React 中检测：

```tsx
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

useEffect(() => {
  if (prefersReducedMotion) {
    // 使用静态加载状态
  } else {
    // 使用动画加载状态
  }
}, [prefersReducedMotion])
```

### 10.6 表单无障碍

所有表单输入必须有标签：

```tsx
<Form.Item
  name="code"
  label={<span id="code-label">股票代码</span>}
  rules={[{ required: true, message: '请输入股票代码' }]}
>
  <Input aria-labelledby="code-label" placeholder="如: 600519" />
</Form.Item>

// 或使用 htmlFor
<label htmlFor="stock-code">股票代码</label>
<Input id="stock-code" />
```

错误提示需要关联到输入框：

```tsx
<Form.Item
  name="code"
  help={errors.code}
  validateStatus={errors.code ? 'error' : ''}
>
  <Input aria-invalid={!!errors.code} aria-describedby="code-error" />
</Form.Item>
<span id="code-error" className="sr-only">{errors.code}</span>
```

---

## 11. 实施路线图

### 11.1 实施阶段划分

本设计规范的实施分为三个阶段，每个阶段有明确的目标和交付物。

**第一阶段（P0）- 基础设施**的目标是建立设计系统的基础设施，为后续页面开发提供支持。包含的任务有：配置 Ant Design 深色主题、创建全局 CSS 变量和样式文件、创建数字格式化工具函数、创建涨跌样式工具函数、创建主题 Provider 和配置入口。产出物为 `src/theme/darkTheme.ts`、`src/utils/format.ts`、`src/utils/price.ts`、`src/app/globals.css`。

**第二阶段（P1）- 核心页面**的目标是完成用户最常用的核心页面，包含市场页面和组合页面。包含的任务有：重构市场页面（MarketPage）、重构组合页面（PortfolioPage）、创建统一的页面布局组件、创建数据表格组件、创建图表封装组件。产出物为 `src/features/market/MarketPage.tsx`、`src/features/portfolio/PortfolioPage.tsx`。

**第三阶段（P2）- 辅助页面**的目标是完成剩余的功能页面。包含的任务有：重构复盘页面（ReviewPage）、重构知识库页面（KnowledgePage）、重构监控页面（MonitorPage）、重构策略页面（StrategyPage）、优化全局导航和布局。产出物为 `src/features/review/ReviewPage.tsx`、`src/features/knowledge/KnowledgePage.tsx`、`src/features/monitor/MonitorPage.tsx`、`src/features/strategy/StrategyPage.tsx`。

**第四阶段（P3）- 体验优化**的目标是优化细节体验，提升整体品质。包含的任务有：添加页面过渡动效、优化加载状态和骨架屏、实现响应式细节适配、无障碍检查和修复、性能优化。交付物为优化后的整体体验。

### 11.2 实施优先级说明

P0 阶段为必须完成的基础设施，是后续所有工作的前提。P1 阶段为高频使用页面，用户每天都会访问，需要优先保证质量。P2 阶段为低频使用页面，在 P1 完成后进行。P3 阶段为优化项，根据时间和资源情况安排。

### 11.3 验收标准

每个阶段的验收标准包括以下方面。

视觉一致性方面：所有页面使用统一的色彩、字体、间距系统，符合本设计规范定义。

功能完整性方面：页面功能完整，操作流程顺畅，无阻断性 bug。

性能达标方面：页面加载时间小于 3 秒，交互响应时间小于 100ms。

无障碍合规方面：通过 basic 级别的无障碍测试。

### 11.4 维护建议

设计规范的维护需要注意以下方面。

组件库更新时需要检查主题配置是否兼容 Ant Design 新版本。

新增页面时需要参考本规范，确保与其他页面的一致性。

设计调整时需要更新本文档并通知相关开发人员。

---

## 附录

### 附录 A：设计资源

字体资源为 IBM Plex Sans，Google Fonts 链接：https://fonts.google.com/share?selection.family=IBM+Plex+Sans。

图标资源为 Ant Design Icons，GitHub 链接：https://github.com/ant-design/ant-design-icons。

设计工具为 Figma、Sketch、Adobe XD。

### 附录 B：参考项目

同类型优秀金融应用参考包括：东方财富、同花顺、Wind、TradingView、财联社。

设计规范参考包括：Ant Design、Material Design、Apple Human Interface Guidelines。

### 附录 C：术语表

| 术语 | 说明 |
|------|------|
| 深色模式 | Dark Mode，系统使用深色背景的显示模式 |
|涨跌色 | 用于标识价格涨跌的颜色，A 股习惯红涨绿跌 |
| KPI | Key Performance Indicator，关键绩效指标 |
| RAG | Retrieval-Augmented Generation，检索增强生成 |
| ARIA | Accessible Rich Internet Applications，无障碍富互联网应用 |
| WCAG | Web Content Accessibility Guidelines，网页内容无障碍指南 |

---

**文档维护信息**

| 版本 | 日期 | 修改内容 | 作者 |
|------|------|----------|------|
| v1.0 | 2026-02-04 | 初始版本 | Claude |
