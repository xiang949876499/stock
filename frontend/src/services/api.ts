import axios from 'axios'
import type {
  StockInfo,
  StockDaily,
  TechnicalIndicators,
  Signal,
  NewsItem,
  Position,
  AnalysisRequest,
  AnalysisResponse,
  ChatRequest,
  ChatResponse,
} from '../types'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

// 股票相关
export const stockApi = {
  list: (market?: string) =>
    api.get<StockInfo[]>('/stocks', { params: { market } }),

  get: (symbol: string, market: string) =>
    api.get<StockInfo>(`/stocks/${symbol}`, { params: { market } }),

  getKline: (symbol: string, market: string, period: string = 'daily') =>
    api.get<StockDaily[]>(`/stocks/${symbol}/kline`, { params: { market, period } }),
}

// 分析相关
export const analysisApi = {
  analyze: (request: AnalysisRequest) =>
    api.post<AnalysisResponse>('/analysis/analyze', request),

  listReports: (symbol?: string) =>
    api.get('/analysis/reports', { params: { symbol } }),
}

// 信号相关
export const signalApi = {
  list: (symbol?: string, status?: string) =>
    api.get<Signal[]>('/signals', { params: { symbol, status } }),

  approve: (signalId: string) =>
    api.post(`/signals/${signalId}/approve`),

  reject: (signalId: string, reason: string) =>
    api.post(`/signals/${signalId}/reject`, { reason }),
}

// 执行相关
export const executionApi = {
  getPositions: () =>
    api.get<Position[]>('/execution/positions'),

  getAccount: () =>
    api.get('/execution/account'),

  listOrders: (symbol?: string) =>
    api.get('/execution/orders', { params: { symbol } }),
}

// 新闻相关
export const newsApi = {
  list: (symbol?: string, market?: string, days: number = 7) =>
    api.get<NewsItem[]>('/news', { params: { symbol, market, days } }),

  getSentiment: (symbol: string, market: string, days: number = 30) =>
    api.get('/news/sentiment', { params: { symbol, market, days } }),
}

// Agent 相关
export const agentApi = {
  chat: (request: ChatRequest) =>
    api.post<ChatResponse>('/agent/chat', request),
}

export default api
