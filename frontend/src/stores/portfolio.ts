import { create } from 'zustand'
import type { Position } from '../types'
import { executionApi } from '../services/api'

interface PortfolioState {
  positions: Position[]
  account: any
  loading: boolean
  error: string | null

  fetchPositions: () => Promise<void>
  fetchAccount: () => Promise<void>
}

export const usePortfolioStore = create<PortfolioState>((set) => ({
  positions: [],
  account: null,
  loading: false,
  error: null,

  fetchPositions: async () => {
    set({ loading: true, error: null })
    try {
      const response = await executionApi.getPositions()
      set({ positions: response.data, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  fetchAccount: async () => {
    set({ loading: true, error: null })
    try {
      const response = await executionApi.getAccount()
      set({ account: response.data, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },
}))
