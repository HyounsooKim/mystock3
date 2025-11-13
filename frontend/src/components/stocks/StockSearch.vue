<template>
  <div class="stock-search">
    <div class="search-input-wrapper">
      <input
        v-model="searchQuery"
        type="text"
        class="form-control"
        :class="{ 'is-invalid': error }"
        placeholder="종목명 또는 심볼로 검색 (예: Apple, AAPL)"
        @input="handleSearch"
        @focus="showResults = true"
      />
      <div v-if="loading" class="search-spinner">
        <div class="spinner-border spinner-border-sm" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>
    </div>

    <!-- Error message -->
    <div v-if="error" class="invalid-feedback d-block">{{ error }}</div>

    <!-- Search results dropdown -->
    <div v-if="showResults && (results.length > 0 || searched)" class="search-results">
      <div v-if="results.length > 0" class="results-list">
        <button
          v-for="stock in results"
          :key="stock.symbol"
          class="result-item"
          @click="selectStock(stock)"
        >
          <div class="result-symbol">{{ stock.symbol }}</div>
          <div class="result-name">{{ stock.name }}</div>
          <div class="result-region">{{ stock.region }}</div>
        </button>
      </div>
      <div v-else-if="searched && !loading" class="no-results">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
        <p>검색 결과가 없습니다</p>
      </div>
    </div>

    <!-- Backdrop -->
    <div v-if="showResults" class="search-backdrop" @click="closeResults"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { searchStocks } from '@/api/stocks'
import type { StockSearchResult } from '@/api/stocks'

interface Props {
  modelValue?: string
  autofocus?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  select: [stock: StockSearchResult]
}>()

const searchQuery = ref(props.modelValue || '')
const results = ref<StockSearchResult[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const showResults = ref(false)
const searched = ref(false)

let searchTimeout: NodeJS.Timeout | null = null

watch(() => props.modelValue, (newValue) => {
  searchQuery.value = newValue || ''
})

function handleSearch() {
  emit('update:modelValue', searchQuery.value)

  // Clear previous timeout
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }

  // Reset state
  error.value = null
  searched.value = false

  // Require at least 1 character
  if (searchQuery.value.trim().length === 0) {
    results.value = []
    return
  }

  // Debounce search (500ms)
  searchTimeout = setTimeout(async () => {
    await performSearch()
  }, 500)
}

async function performSearch() {
  loading.value = true
  error.value = null

  try {
    results.value = await searchStocks(searchQuery.value.trim())
    searched.value = true
    showResults.value = true
  } catch (err: any) {
    error.value = err.response?.data?.detail || '검색 중 오류가 발생했습니다'
    results.value = []
  } finally {
    loading.value = false
  }
}

function selectStock(stock: StockSearchResult) {
  emit('select', stock)
  closeResults()
}

function closeResults() {
  showResults.value = false
}
</script>

<style scoped>
.stock-search {
  position: relative;
}

.search-input-wrapper {
  position: relative;
}

.search-spinner {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  background: var(--tblr-bg-surface);
  border: 1px solid var(--tblr-border-color);
  border-radius: var(--tblr-border-radius);
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
  z-index: 1000;
  max-height: 400px;
  overflow-y: auto;
}

.results-list {
  display: flex;
  flex-direction: column;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  border: none;
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.2s;
  border-bottom: 1px solid var(--tblr-border-color-translucent);
}

.result-item:last-child {
  border-bottom: none;
}

.result-item:hover {
  background: var(--tblr-bg-surface-secondary);
}

.result-symbol {
  font-weight: 600;
  font-size: 1rem;
  color: var(--tblr-body-color);
  min-width: 60px;
}

.result-name {
  flex: 1;
  font-size: 0.875rem;
  color: var(--tblr-muted);
}

.result-region {
  font-size: 0.75rem;
  color: var(--tblr-secondary);
  white-space: nowrap;
}

.no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  color: var(--tblr-muted);
  text-align: center;
}

.no-results svg {
  margin-bottom: 0.5rem;
  opacity: 0.5;
}

.no-results p {
  margin: 0;
  font-size: 0.875rem;
}

.search-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;
}
</style>
