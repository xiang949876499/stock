import { create } from 'zustand'
import type { NewsItem } from '../types'
import { newsApi } from '../services/api'

interface NewsState {
  news: NewsItem[]
  sentiment: any
  loading: boolean
  error: string | null

  fetchNews: (symbol?: string, market?: string, days?: number) => Promise<void>
  fetchSentiment: (symbol: string, market: string, days?: number) => Promise<void>
}

export const useNewsStore = create<NewsState>((set) => ({
  news: [],
  sentiment: null,
  loading: false,
  error: null,

  fetchNews: async (symbol?: string, market?: string, days: number = 7) => {
    set({ loading: true, error: null })
    try {
      const response = await newsApi.list(symbol, market, days)
      set({ news: response.data, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  fetchSentiment: async (symbol: string, market: string, days: number = 30) => {
    set({ loading: true, error: null })
    try {
      const response = await newsApi.getSentiment(symbol, market, days)
      set({ sentiment: response.data, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },
}))
