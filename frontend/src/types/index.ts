// 股票信息
export interface StockInfo {
  symbol: string
  name: string
  market: 'A' | 'HK' | 'US'
  industry: string
  list_date: string
  is_st: boolean
  is_active: boolean
}

// 日线数据
export interface StockDaily {
  symbol: string
  market: string
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number
  turnover: number
}

// 技术指标
export interface TechnicalIndicators {
  symbol: string
  market: string
  date: string
  ma5: number
  ma10: number
  ma20: number
  ma60: number
  macd: number
  macd_signal: number
  macd_hist: number
  kdj_k: number
  kdj_d: number
  kdj_j: number
  rsi_6: number
  rsi_12: number
  rsi_24: number
  boll_upper: number
  boll_middle: number
  boll_lower: number
}

// 信号
export interface Signal {
  schema_version: string
  signal_id: string
  as_of: string
  source: string
  status: 'draft' | 'approved' | 'published' | 'rejected' | 'consumed' | 'archived'
  targets: Record<string, number>
  cash_weight: number
  metadata?: Record<string, any>
}

// 新闻
export interface NewsItem {
  id: string
  symbol: string
  market: string
  title: string
  content: string
  source: string
  url: string
  publish_time: string
  sentiment: 'positive' | 'negative' | 'neutral'
  importance: 'P0' | 'P1' | 'P2'
}

// 持仓
export interface Position {
  symbol: string
  market: string
  quantity: number
  avg_price: number
  current_price: number
  pnl: number
}

// 分析请求
export interface AnalysisRequest {
  symbol: string
  market: string
  strategy: string
}

// 分析响应
export interface AnalysisResponse {
  symbol: string
  score: number
  signal: 'buy' | 'sell' | 'hold'
  trend: 'bullish' | 'bearish' | 'neutral'
  reason: string
}

// 聊天请求
export interface ChatRequest {
  session_id?: string
  message: string
}

// 聊天响应
export interface ChatResponse {
  session_id: string
  message: string
}
