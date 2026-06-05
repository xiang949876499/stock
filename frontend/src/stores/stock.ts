import { create } from 'zustand'
import type { StockInfo, StockDaily, TechnicalIndicators } from '../types'
import { stockApi } from '../services/api'

interface StockState {
  stocks: StockInfo[]
  selectedStock: StockInfo | null
  klineData: StockDaily[]
  technical: TechnicalIndicators | null
  loading: boolean
  error: string | null

  fetchStocks: (market?: string) => Promise<void>
  selectStock: (symbol: string, market: string) => Promise<void>
  fetchKline: (symbol: string, market: string, period?: string) => Promise<void>
}

export const useStockStore = create<StockState>((set) => ({
  stocks: [],
  selectedStock: null,
  klineData: [],
  technical: null,
  loading: false,
  error: null,

  fetchStocks: async (market?: string) => {
    set({ loading: true, error: null })
    try {
      const response = await stockApi.list(market)
      set({ stocks: response.data, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  selectStock: async (symbol: string, market: string) => {
    set({ loading: true, error: null })
    try {
      const response = await stockApi.get(symbol, market)
      set({ selectedStock: response.data, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  fetchKline: async (symbol: string, market: string, period: string = 'daily') => {
    set({ loading: true, error: null })
    try {
      const response = await stockApi.getKline(symbol, market, period)
      set({ klineData: response.data, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },
}))
