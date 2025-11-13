<template>
  <div class="stock-quote">
    <!-- Loading state -->
    <div v-if="loading" class="quote-loading">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="text-muted mt-2">시세 정보를 불러오는 중...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="alert alert-danger" role="alert">
      <div class="d-flex">
        <div>
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon alert-icon">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
        </div>
        <div>{{ error }}</div>
      </div>
    </div>

    <!-- Quote display -->
    <div v-else-if="quote" class="quote-content">
      <!-- Header -->
      <div class="quote-header">
        <div class="quote-title">
          <h3 class="symbol">{{ quote.symbol }}</h3>
          <p class="company-name">{{ quote.company_name }}</p>
        </div>
        <button
          v-if="showRefreshButton"
          class="btn btn-sm btn-ghost-secondary"
          :disabled="refreshing"
          @click="handleRefresh"
          title="새로고침"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            :class="{ 'icon-spin': refreshing }"
          >
            <polyline points="23 4 23 10 17 10"></polyline>
            <polyline points="1 20 1 14 7 14"></polyline>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
          </svg>
        </button>
      </div>

      <!-- Price -->
      <div class="quote-price">
        <div class="current-price">{{ formatPrice(quote.current_price) }}</div>
        <div class="price-change" :class="getChangeClass(quote.change)">
          <span class="change-amount">{{ formatChange(quote.change) }}</span>
          <span class="change-percent">({{ formatChangePercent(quote.change_percent) }})</span>
        </div>
      </div>

      <!-- Details -->
      <div class="quote-details">
        <div class="detail-item">
          <span class="detail-label">시가</span>
          <span class="detail-value">{{ formatPrice(quote.open) }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">고가</span>
          <span class="detail-value text-success">{{ formatPrice(quote.high) }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">저가</span>
          <span class="detail-value text-danger">{{ formatPrice(quote.low) }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">거래량</span>
          <span class="detail-value">{{ formatVolume(quote.volume) }}</span>
        </div>
      </div>

      <!-- Last updated -->
      <div class="quote-footer">
        <small class="text-muted">
          마지막 업데이트: {{ formatLastUpdated(quote.last_updated) }}
        </small>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { getStockQuote } from '@/api/stocks'
import type { StockQuote } from '@/types'

interface Props {
  symbol: string
  autoRefresh?: boolean
  refreshInterval?: number // milliseconds
  showRefreshButton?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  autoRefresh: false,
  refreshInterval: 60000, // 1 minute
  showRefreshButton: true
})

const quote = ref<StockQuote | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const refreshing = ref(false)

let refreshTimer: NodeJS.Timeout | null = null

onMounted(() => {
  loadQuote()

  if (props.autoRefresh) {
    startAutoRefresh()
  }
})

watch(() => props.symbol, () => {
  loadQuote()
})

watch(() => props.autoRefresh, (enabled) => {
  if (enabled) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
})

async function loadQuote() {
  loading.value = true
  error.value = null

  try {
    quote.value = await getStockQuote(props.symbol)
  } catch (err: any) {
    error.value = err.response?.data?.detail || '시세 정보를 불러오는데 실패했습니다'
  } finally {
    loading.value = false
  }
}

async function handleRefresh() {
  refreshing.value = true
  error.value = null

  try {
    quote.value = await getStockQuote(props.symbol)
  } catch (err: any) {
    error.value = err.response?.data?.detail || '시세 정보를 불러오는데 실패했습니다'
  } finally {
    refreshing.value = false
  }
}

function startAutoRefresh() {
  stopAutoRefresh()
  refreshTimer = setInterval(() => {
    handleRefresh()
  }, props.refreshInterval)
}

function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

function formatPrice(price: number): string {
  return new Intl.NumberFormat('ko-KR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(price)
}

function formatChange(change: number): string {
  const sign = change >= 0 ? '+' : ''
  return `${sign}${formatPrice(change)}`
}

function formatChangePercent(percent: number): string {
  const sign = percent >= 0 ? '+' : ''
  return `${sign}${percent.toFixed(2)}%`
}

function getChangeClass(change: number): string {
  if (change > 0) return 'positive'
  if (change < 0) return 'negative'
  return 'neutral'
}

function formatVolume(volume: number): string {
  if (volume >= 1000000) {
    return `${(volume / 1000000).toFixed(2)}M`
  } else if (volume >= 1000) {
    return `${(volume / 1000).toFixed(2)}K`
  }
  return volume.toLocaleString('ko-KR')
}

function formatLastUpdated(timestamp: string): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return '방금 전'
  if (diffMins < 60) return `${diffMins}분 전`
  
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}시간 전`

  return date.toLocaleString('ko-KR')
}
</script>

<style scoped>
.stock-quote {
  min-height: 200px;
}

.quote-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.quote-content {
  padding: 1.5rem;
}

.quote-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.quote-title .symbol {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--tblr-body-color);
}

.quote-title .company-name {
  margin: 0.25rem 0 0 0;
  font-size: 0.875rem;
  color: var(--tblr-muted);
}

.btn-ghost-secondary {
  padding: 0.375rem 0.75rem;
  border: none;
  background: transparent;
}

.btn-ghost-secondary:hover:not(:disabled) {
  background: var(--tblr-secondary-lt);
  color: var(--tblr-secondary);
}

.icon-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.quote-price {
  margin-bottom: 1.5rem;
}

.current-price {
  font-size: 2rem;
  font-weight: 700;
  font-family: 'Courier New', monospace;
  color: var(--tblr-body-color);
  margin-bottom: 0.5rem;
}

.price-change {
  font-size: 1.125rem;
  font-weight: 600;
  font-family: 'Courier New', monospace;
}

.price-change.positive {
  color: var(--tblr-success);
}

.price-change.negative {
  color: var(--tblr-danger);
}

.price-change.neutral {
  color: var(--tblr-muted);
}

.change-percent {
  margin-left: 0.5rem;
}

.quote-details {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  padding: 1rem 0;
  border-top: 1px solid var(--tblr-border-color);
  border-bottom: 1px solid var(--tblr-border-color);
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-label {
  font-size: 0.875rem;
  color: var(--tblr-muted);
}

.detail-value {
  font-size: 0.875rem;
  font-weight: 600;
  font-family: 'Courier New', monospace;
  color: var(--tblr-body-color);
}

.quote-footer {
  margin-top: 1rem;
  text-align: right;
}

.alert-icon {
  margin-right: 0.5rem;
}
</style>
