/**
 * Portfolio Store
 * 
 * Manages portfolio state with category filtering and P/L calculations.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { 
  PortfolioEntryWithMetrics, 
  PortfolioEntryCreate, 
  PortfolioEntryUpdate,
  PortfolioCategory 
} from '@/types'
import apiClient from '@/api/client'

export const usePortfolioStore = defineStore('portfolio', () => {
  // State
  const entries = ref<PortfolioEntryWithMetrics[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const selectedCategory = ref<PortfolioCategory | 'all'>('all')

  // Computed
  const filteredEntries = computed(() => {
    if (selectedCategory.value === 'all') {
      return entries.value
    }
    return entries.value.filter(entry => entry.category === selectedCategory.value)
  })

  const totalMarketValue = computed(() => {
    return filteredEntries.value.reduce((sum, entry) => {
      return sum + (entry.market_value ?? 0)
    }, 0)
  })

  const totalProfitLoss = computed(() => {
    return filteredEntries.value.reduce((sum, entry) => {
      return sum + (entry.profit_loss ?? 0)
    }, 0)
  })

  const totalProfitLossPercent = computed(() => {
    const totalInvestment = filteredEntries.value.reduce((sum, entry) => {
      return sum + (entry.purchase_price * entry.quantity)
    }, 0)
    
    if (totalInvestment === 0) return 0
    return (totalProfitLoss.value / totalInvestment) * 100
  })

  const entriesByCategory = computed(() => {
    return {
      '장기': entries.value.filter(e => e.category === '장기'),
      '단기': entries.value.filter(e => e.category === '단기'),
      '정찰병': entries.value.filter(e => e.category === '정찰병'),
    }
  })

  // Actions
  async function fetchPortfolio(category?: PortfolioCategory) {
    loading.value = true
    error.value = null

    try {
      const params = category ? { category } : {}
      const response = await apiClient.get<PortfolioEntryWithMetrics[]>('/portfolio', { params })
      entries.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || '포트폴리오 조회에 실패했습니다'
      console.error('Failed to fetch portfolio:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function addEntry(entryData: PortfolioEntryCreate) {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.post<PortfolioEntryWithMetrics>('/portfolio', entryData)
      
      // Add the new entry to local state (backend returns with calculated P/L)
      entries.value.push(response.data)
      
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || '포트폴리오 추가에 실패했습니다'
      console.error('Failed to add portfolio entry:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getEntry(entryId: string) {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.get<PortfolioEntryWithMetrics>(`/portfolio/${entryId}`)
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || '포트폴리오 조회에 실패했습니다'
      console.error('Failed to get portfolio entry:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateEntry(entryId: string, updateData: PortfolioEntryUpdate) {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.patch<PortfolioEntryWithMetrics>(
        `/portfolio/${entryId}`,
        updateData
      )
      
      // Update the modified entry in local state
      const index = entries.value.findIndex(e => e.entry_id === entryId)
      if (index !== -1) {
        entries.value[index] = response.data
      }
      
      // If backend returned null prices, fetch the entry again to get updated prices
      if (response.data.current_price === null || response.data.current_price === undefined) {
        try {
          const refreshedEntry = await apiClient.get<PortfolioEntryWithMetrics>(`/portfolio/${entryId}`)
          if (index !== -1) {
            entries.value[index] = refreshedEntry.data
          }
        } catch (refreshErr) {
          console.error('Failed to refresh entry prices:', refreshErr)
          // Keep the original response data even if refresh fails
        }
      }
      
      return entries.value[index]
    } catch (err: any) {
      error.value = err.response?.data?.detail || '포트폴리오 수정에 실패했습니다'
      console.error('Failed to update portfolio entry:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteEntry(entryId: string) {
    loading.value = true
    error.value = null

    try {
      await apiClient.delete(`/portfolio/${entryId}`)
      
      // Remove from local state
      entries.value = entries.value.filter(e => e.entry_id !== entryId)
    } catch (err: any) {
      error.value = err.response?.data?.detail || '포트폴리오 삭제에 실패했습니다'
      console.error('Failed to delete portfolio entry:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  function setCategory(category: PortfolioCategory | 'all') {
    selectedCategory.value = category
  }

  function clearError() {
    error.value = null
  }

  function resetStore() {
    entries.value = []
    loading.value = false
    error.value = null
    selectedCategory.value = 'all'
  }

  return {
    // State
    entries,
    loading,
    error,
    selectedCategory,

    // Computed
    filteredEntries,
    totalMarketValue,
    totalProfitLoss,
    totalProfitLossPercent,
    entriesByCategory,

    // Actions
    fetchPortfolio,
    addEntry,
    getEntry,
    updateEntry,
    deleteEntry,
    setCategory,
    clearError,
    resetStore,
  }
})
