import { create } from 'zustand'
import { tradingApi } from '../services/api'

export interface TradingAccount {
  account_id: string
  initial_capital: number
  cash: number
  total_assets: number
  total_pnl: number
  total_pnl_pct: number
  created_at: string
}

export interface TradingPosition {
  symbol: string
  market: string
  quantity: number
  avg_cost: number
  current_price: number
  pnl: number
  pnl_pct: number
}

export interface TradingTrade {
  trade_id: string
  signal_id: string
  symbol: string
  market: string
  direction: string
  quantity: number
  price: number
  amount: number
  status: string
  executed_at: string
}

export interface TradingReport {
  date: string
  total_assets: number
  cash: number
  position_value: number
  daily_pnl: number
  daily_pnl_pct: number
  total_pnl: number
  total_pnl_pct: number
  trade_count: number
  win_count: number
  win_rate: number
}

export interface AnalysisLog {
  log_id: string
  date: string
  symbol: string
  market: string
  content: string
  decision: string
  confidence: number
  created_at: string
}

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

export const useTradingStore = create<TradingState>((set) => ({
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
      const store = useTradingStore.getState()
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
      const response = await tradingApi.resetAccount(initialCapital)
      set({ account: response.data, positions: [], trades: [], loading: false })
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.message || '重置失败'
      set({ error: msg, loading: false })
      throw new Error(msg)
    }
  },

  fetchStatus: async () => {
    try {
      const response = await tradingApi.getStatus()
      set({ running: response.data.running })
    } catch (error: any) {
      console.error('获取状态失败:', error)
    }
  },
}))
