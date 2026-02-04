// Stock types
export interface Quote {
  code: string
  name?: string
  price: number
  pct_chg: number
  volume?: number
  turnover_rate?: number
  open?: number
  high?: number
  low?: number
  close?: number
  pe_ratio?: number
  pb_ratio?: number
  updated_at: string
}

export interface OHLCV {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number
  pct_chg: number
}

export interface Indicators {
  moving_averages: Record<string, number>
  bias?: number
  volume_ratio?: number
  macd?: {
    dif: number
    dea: number
    macd: number
  }
  kdj?: {
    k: number
    d: number
    j: number
  }
}

export interface StockAnalysis {
  code: string
  name?: string
  current_price: number
  pct_chg: number
  analysis: {
    trend: string
    tech_score: number
    ai_recommendation: string
    risk_level: string
  }
  indicators: Indicators
  chip_distribution?: Record<string, any>
  recent_news: Array<{ title: string; url: string; sentiment: string }>
  updated_at: string
}

// Portfolio types
export interface Position {
  id: number
  code: string
  name?: string
  quantity: number
  avg_cost: number
  current_price: number
  profit_loss: number
  profit_pct: number
  position_ratio: number
  notes?: string
}

export interface PortfolioSummary {
  total_value: number
  total_profit: number
  total_profit_pct: number
  cash_balance: number
  position_count: number
}

export interface Portfolio {
  summary: PortfolioSummary
  positions: Position[]
  updated_at: string
}

// Alert types
export interface Alert {
  id: number
  code?: string
  alert_type: string
  threshold: number
  direction: string
  enabled: boolean
  notify_channels: string[]
  notes?: string
  last_triggered?: string
  trigger_count: number
}

// Knowledge types
export interface Document {
  id: number
  title: string
  slug?: string
  category_id?: number
  status: string
  content: string
  tags: string[]
  related_codes: string[]
  auto_generated: boolean
  version: number
  created_at: string
  updated_at?: string
}

export interface Category {
  id: number
  name: string
  slug: string
  parent_id?: number
  description?: string
}

// Review types
export interface DailyReviewResponse {
  id: number
  date: string
  market_overview?: string
  hot_sectors: Array<Record<string, any>>
  winning_trades: Array<Record<string, any>>
  losing_trades: Array<Record<string, any>>
  lessons_learned: string[]
  knowledge_gained: string[]
  tomorrow_focus: string[]
  created_by?: number
  created_at: string
  updated_at?: string
}

export interface WeeklyReviewResponse {
  id: number
  week_start: string
  week_end: string
  market_summary: string
  sector_performance: Array<Record<string, any>>
  key_lessons: string[]
  strategy_updates: Array<Record<string, any>>
  next_week_outlook?: string
  created_at: string
}

export interface ReviewCalendarResponse {
  year: number
  month: number
  days: Array<{
    date: string
    has_review: boolean
    review_id?: number
  }>
}

// Strategy types
export interface Strategy {
  id: number
  name: string
  category: string
  description?: string
  conditions: Record<string, any>
  actions: Record<string, any>
  risk_management: Record<string, any>
  source_doc_id?: number
  verification_count: number
  success_rate?: number
  status: string
  created_at: string
  updated_at?: string
}

export interface SignalResponse {
  id: number
  strategy_id: number
  strategy_name: string
  code: string
  signal_type: string
  confidence: number
  reasoning?: string
  price: number
  created_at: string
}

// Chat types
export interface ModelInfo {
  id: string
  name: string
  provider: string
  description?: string
  strengths?: string[]
  enabled: boolean
}
