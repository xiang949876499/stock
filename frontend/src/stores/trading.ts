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
    set({ loading: true, error: null })
    try {
      const response = await tradingApi.getAccount()
      set({ account: response.data, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  fetchPositions: async () => {
    set({ loading: true, error: null })
    try {
      const response = await tradingApi.getPositions()
      set({ positions: response.data, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  fetchTrades: async (date?: string) => {
    set({ loading: true, error: null })
    try {
      const response = await tradingApi.getTrades(date)
      set({ trades: response.data, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  fetchReports: async () => {
    set({ loading: true, error: null })
    try {
      const response = await tradingApi.getReports()
      set({ reports: response.data, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  fetchReport: async (date: string) => {
    set({ loading: true, error: null })
    try {
      const response = await tradingApi.getReport(date)
      set({ loading: false })
      return response.data
    } catch (error: any) {
      set({ error: error.message, loading: false })
      return null
    }
  },

  fetchAnalysisLogs: async (date?: string) => {
    set({ loading: true, error: null })
    try {
      const response = await tradingApi.getAnalysisLogs(date)
      set({ analysisLogs: response.data, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  startTrading: async () => {
    set({ loading: true, error: null })
    try {
      await tradingApi.start()
      set({ running: true, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  stopTrading: async () => {
    set({ loading: true, error: null })
    try {
      await tradingApi.stop()
      set({ running: false, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  resetAccount: async (initialCapital: number = 1000000) => {
    set({ loading: true, error: null })
    try {
      const response = await tradingApi.resetAccount(initialCapital)
      set({ account: response.data, positions: [], trades: [], loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  fetchStatus: async () => {
    try {
      const response = await tradingApi.getStatus()
      set({ running: response.data.running })
    } catch (error: any) {
      set({ error: error.message })
    }
  },
}))
