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
  timeout: 300000, // 5 分钟（AI 分析需要较长时间）
})

// 股票相关
export const stockApi = {
  list: (market?: string) =>
    api.get<StockInfo[]>('/stocks', { params: { market } }),

  get: (symbol: string, market: string) =>
    api.get<StockInfo>(`/stocks/${symbol}`, { params: { market } }),

  getKline: (symbol: string, market: string, period: string = 'daily') =>
    api.get<StockDaily[]>(`/stocks/${symbol}/kline`, { params: { market, period } }),

  getTechnical: (symbol: string, market: string) =>
    api.get<TechnicalIndicators>(`/stocks/${symbol}/technical`, { params: { market } }),
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

// 推荐相关
export const recommendApi = {
  stocks: (market: string = 'A', topN: number = 10) =>
    api.get('/recommend/stocks', { params: { market, top_n: topN } }),

  analyze: (market: string = 'A', topN: number = 5) =>
    api.get('/recommend/stocks/analyze', { params: { market, top_n: topN } }),

  evaluate: (symbol: string, market: string = 'A') =>
    api.get(`/recommend/stocks/${symbol}/evaluate`, { params: { market } }),
}

// 模拟交易相关
export const tradingApi = {
  getAccount: () => api.get('/trading/account'),
  resetAccount: (initialCapital: number = 1000000) => api.post('/trading/account/reset', { initial_capital: initialCapital }),
  getPositions: () => api.get('/trading/positions'),
  getTrades: (date?: string) => api.get('/trading/trades', { params: { date } }),
  getReports: () => api.get('/trading/reports'),
  getReport: (date: string) => api.get(`/trading/reports/${date}`),
  getMistakes: (date: string) => api.get(`/trading/reports/${date}/mistakes`),
  getAnalysisLogs: (date?: string) => api.get('/trading/analysis-logs', { params: { date } }),
  start: () => api.post('/trading/start'),
  stop: () => api.post('/trading/stop'),
  getStatus: () => api.get('/trading/status'),
}

// 插件相关
export const pluginApi = {
  list: () =>
    api.get<Record<string, string>>('/plugins/'),

  getInfo: (pluginName: string) =>
    api.get(`/plugins/${pluginName}`),

  execute: (pluginName: string, request: { symbol: string; params: Record<string, any> }) =>
    api.post(`/plugins/${pluginName}/execute`, request),

  export: (pluginName: string, symbol: string, format: string = 'json') =>
    api.get(`/plugins/${pluginName}/export`, {
      params: { symbol, format },
      responseType: 'blob',
    }),
}

export default api
