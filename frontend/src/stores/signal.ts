import { create } from 'zustand'
import type { Signal } from '../types'
import { signalApi } from '../services/api'

interface SignalState {
  signals: Signal[]
  loading: boolean
  error: string | null

  fetchSignals: (symbol?: string, status?: string) => Promise<void>
  createSignal: (targets: Record<string, number>, source?: string) => Promise<Signal>
  approveSignal: (signalId: string) => Promise<void>
  rejectSignal: (signalId: string, reason: string) => Promise<void>
}

export const useSignalStore = create<SignalState>((set) => ({
  signals: [],
  loading: false,
  error: null,

  fetchSignals: async (symbol?: string, status?: string) => {
    set({ loading: true, error: null })
    try {
      const response = await signalApi.list(symbol, status)
      set({ signals: response.data, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  createSignal: async (targets: Record<string, number>, source: string = 'manual') => {
    set({ loading: true, error: null })
    try {
      const response = await signalApi.create(targets, source)
      const newSignal = response.data
      set((state) => ({
        signals: [newSignal, ...state.signals],
        loading: false,
      }))
      return newSignal
    } catch (error: any) {
      set({ error: error.message, loading: false })
      throw error
    }
  },

  approveSignal: async (signalId: string) => {
    set({ loading: true, error: null })
    try {
      await signalApi.approve(signalId)
      set((state) => ({
        signals: state.signals.map((s) =>
          s.signal_id === signalId ? { ...s, status: 'approved' } : s
        ),
        loading: false,
      }))
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  rejectSignal: async (signalId: string, reason: string) => {
    set({ loading: true, error: null })
    try {
      await signalApi.reject(signalId, reason)
      set((state) => ({
        signals: state.signals.map((s) =>
          s.signal_id === signalId ? { ...s, status: 'rejected' } : s
        ),
        loading: false,
      }))
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },
}))
