import { create } from 'zustand'
import { tradingApi } from '../services/api'

// ── 接口定义（匹配后端 API 返回） ─────────────────────────

export interface TradingAccount {
  account_id: string
  initial_capital: number
  balance: number
  frozen: number
  total_assets: number
  created_at: string
  updated_at: string
}

export interface TradingPosition {
  symbol: string
  name: string
  volume: number
  avg_cost: number
  current_price: number
  market_value: number
  pnl: number
  pnl_pct: number
  open_date: string
}

export interface TradingTrade {
  trade_id: string
  account_id: string
  symbol: string
  name: string
  side: string        // BUY / SELL
  price: number
  volume: number
  amount: number
  commission: number
  strategy: string
  signal_score: number
  signal_reason: string
  created_at: string
}

export interface TradingReport {
  report_id: string
  account_id: string
  report_date: string
  total_assets: number
  daily_pnl: number
  daily_pnl_pct: number
  total_pnl: number
  total_pnl_pct: number
  max_drawdown: number
  win_rate: number
  trade_count: number
  report_markdown: string
  mistakes: string
  strategy_adjustments: string
}

export interface AnalysisLog {
  log_id: string
  account_id: string
  symbol: string
  strategy: string
  score: number
  signal: string
  trend: string
  reason: string
  action_taken: string
  action_reason: string
  created_at: string
}

// ── Store 状态 ────────────────────────────────────────────

interface TradingState {
  account: TradingAccount | null
  positions: TradingPosition[]
  trades: TradingTrade[]
  reports: TradingReport[]
  analysisLogs: AnalysisLog[]
  running: boolean
  loading: boolean
  error: string | null

  fetchAccount: () => Promise<void>
  fetchPositions: () => Promise<void>
  fetchTrades: (date?: string) => Promise<void>
  fetchReports: () => Promise<void>
  fetchReport: (date: string) => Promise<TradingReport | null>
  fetchAnalysisLogs: (date?: string) => Promise<void>
  startTrading: () => Promise<void>
  stopTrading: () => Promise<void>
  runAnalysis: () => Promise<void>
  resetAccount: (initialCapital?: number) => Promise<void>
  fetchStatus: () => Promise<void>
}

// ── Store 实现 ────────────────────────────────────────────

export const useTradingStore = create<TradingState>((set, get) => ({
  account: null,
  positions: [],
  trades: [],
  reports: [],
  analysisLogs: [],
  running: false,
  loading: false,
  error: null,

  fetchAccount: async () => {
    try {
      const response = await tradingApi.getAccount()
      set({ account: response.data })
    } catch (error: any) {
      console.error('获取账户失败:', error)
    }
  },

  fetchPositions: async () => {
    try {
      const response = await tradingApi.getPositions()
      set({ positions: response.data })
    } catch (error: any) {
      console.error('获取持仓失败:', error)
    }
  },

  fetchTrades: async (date?: string) => {
    try {
      const response = await tradingApi.getTrades(date)
      set({ trades: response.data })
    } catch (error: any) {
      console.error('获取交易记录失败:', error)
    }
  },

  fetchReports: async () => {
    try {
      const response = await tradingApi.getReports()
      set({ reports: response.data })
    } catch (error: any) {
      console.error('获取报告失败:', error)
    }
  },

  fetchReport: async (date: string) => {
    try {
      const response = await tradingApi.getReport(date)
      return response.data
    } catch (error: any) {
      console.error('获取报告失败:', error)
      return null
    }
  },

  fetchAnalysisLogs: async (date?: string) => {
    try {
      const response = await tradingApi.getAnalysisLogs(date)
      set({ analysisLogs: response.data })
    } catch (error: any) {
      console.error('获取分析日志失败:', error)
    }
  },

  startTrading: async () => {
    set({ loading: true, error: null })
    try {
      await tradingApi.start()
      set({ running: true, loading: false })
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.message || '启动失败'
      set({ error: msg, loading: false })
      throw new Error(msg)
    }
  },

  stopTrading: async () => {
    set({ loading: true, error: null })
    try {
      await tradingApi.stop()
      set({ running: false, loading: false })
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.message || '停止失败'
      set({ error: msg, loading: false })
      throw new Error(msg)
    }
  },

  runAnalysis: async () => {
    set({ loading: true, error: null })
    try {
      await tradingApi.analyze()
      set({ loading: false })
      // 分析完成后刷新数据
      const store = get()
      await Promise.allSettled([
        store.fetchTrades(),
        store.fetchAnalysisLogs(),
        store.fetchAccount(),
        store.fetchPositions(),
      ])
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.message || '分析失败'
      set({ error: msg, loading: false })
      throw new Error(msg)
    }
  },

  resetAccount: async (initialCapital: number = 1000000) => {
    set({ loading: true, error: null })
    try {
      await tradingApi.resetAccount(initialCapital)
      set({ loading: false })
      // 重置后刷新数据
      const store = get()
      await Promise.allSettled([
        store.fetchAccount(),
        store.fetchPositions(),
        store.fetchTrades(),
        store.fetchAnalysisLogs(),
      ])
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.message || '重置失败'
      set({ error: msg, loading: false })
      throw new Error(msg)
    }
  },

  fetchStatus: async () => {
    try {
      const response = await tradingApi.getStatus()
      set({
        running: response.data.running,
        account: response.data.account,
        positions: response.data.positions,
      })
    } catch (error: any) {
      console.error('获取状态失败:', error)
    }
  },
}))
