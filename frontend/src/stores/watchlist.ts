/**
 * Watchlist store - Pinia store for managing watchlist state
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { WatchlistItem, WatchlistItemWithQuote, WatchlistItemCreate, WatchlistItemUpdate } from '@/types'
import apiClient from '@/api/client'
import { getBatchQuotes } from '@/api/stocks'

export const useWatchlistStore = defineStore('watchlist', () => {
  // State
  const items = ref<WatchlistItemWithQuote[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const hasItems = computed(() => items.value.length > 0)
  const itemCount = computed(() => items.value.length)

  // Actions
  async function fetchWatchlist() {
    loading.value = true
    error.value = null
    try {
      console.log('[WatchlistStore] Fetching watchlist...')
      const response = await apiClient.get<WatchlistItem[]>('/watchlist')
      console.log('[WatchlistStore] Response:', response)
      console.log('[WatchlistStore] Response data:', response.data)
      const watchlistItems = response.data
      console.log('[WatchlistStore] Watchlist items:', watchlistItems)

      // Fetch stock quotes for all symbols
      if (watchlistItems.length > 0) {
        console.log('[WatchlistStore] Fetching quotes for symbols:', watchlistItems.map(item => item.symbol))
        const symbols = watchlistItems.map(item => item.symbol)
        const quotes = await getBatchQuotes(symbols)
        console.log('[WatchlistStore] Quotes received:', quotes)

        // Merge watchlist items with quotes
        items.value = watchlistItems.map(item => {
          const quote = quotes.find(q => q.symbol === item.symbol)
          return {
            ...item,
            current_price: quote?.current_price ?? null,
            change: quote?.change ?? null,
            change_percent: quote?.change_percent ?? null
          }
        })
        console.log('[WatchlistStore] Final items:', items.value)
      } else {
        console.log('[WatchlistStore] No watchlist items')
        items.value = []
      }
    } catch (err: any) {
      console.error('[WatchlistStore] Error fetching watchlist:', err)
      error.value = err.response?.data?.detail || '관심종목을 불러오는데 실패했습니다'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function addToWatchlist(item: WatchlistItemCreate): Promise<WatchlistItem> {
    loading.value = true
    error.value = null
    try {
      const response = await apiClient.post<WatchlistItem>('/watchlist', item)
      await fetchWatchlist() // Refresh list
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || '종목 추가에 실패했습니다'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateWatchlistItem(itemId: string, update: WatchlistItemUpdate): Promise<void> {
    loading.value = true
    error.value = null
    try {
      await apiClient.patch(`/watchlist/${itemId}`, update)
      await fetchWatchlist() // Refresh list
    } catch (err: any) {
      error.value = err.response?.data?.detail || '종목 수정에 실패했습니다'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteWatchlistItem(itemId: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      await apiClient.delete(`/watchlist/${itemId}`)
      // Remove from local state immediately for better UX
      items.value = items.value.filter((item: WatchlistItemWithQuote) => item.id !== itemId)
    } catch (err: any) {
      error.value = err.response?.data?.detail || '종목 삭제에 실패했습니다'
      // Revert on error
      await fetchWatchlist()
      throw err
    } finally {
      loading.value = false
    }
  }

  async function reorderWatchlist(itemIds: string[]): Promise<void> {
    loading.value = true
    error.value = null
    try {
      await apiClient.post('/watchlist/reorder', { item_ids: itemIds })
      await fetchWatchlist() // Refresh list
    } catch (err: any) {
      error.value = err.response?.data?.detail || '순서 변경에 실패했습니다'
      throw err
    } finally {
      loading.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  function $reset() {
    items.value = []
    loading.value = false
    error.value = null
  }

  return {
    // State
    items,
    loading,
    error,
    // Getters
    hasItems,
    itemCount,
    // Actions
    fetchWatchlist,
    addToWatchlist,
    updateWatchlistItem,
    deleteWatchlistItem,
    reorderWatchlist,
    clearError,
    $reset
  }
})
