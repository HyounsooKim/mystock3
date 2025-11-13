<template>
  <div v-if="isOpen" class="modal fade show" style="display: block" @click="handleBackdropClick">
    <div class="modal-dialog modal-dialog-centered" @click.stop>
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">관심종목 추가</h5>
          <button type="button" class="btn-close" @click="close"></button>
        </div>
        <div class="modal-body">
          <!-- Error alert -->
          <div v-if="error" class="alert alert-danger alert-dismissible" role="alert">
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
            <button type="button" class="btn-close" @click="clearError"></button>
          </div>

          <form @submit.prevent="handleSubmit">
            <!-- Stock Search -->
            <div class="mb-3">
              <label class="form-label required">종목 검색</label>
              <StockSearch
                v-model="searchQuery"
                @select="handleStockSelect"
              />
              <div v-if="selectedStock" class="selected-stock mt-2">
                <strong>{{ selectedStock.symbol }}</strong> - {{ selectedStock.name }}
              </div>
              <div v-if="!selectedStock && form.symbol" class="form-text text-danger">
                종목을 검색하여 선택해주세요
              </div>
            </div>

            <!-- Company name (read-only) -->
            <div class="mb-3">
              <label class="form-label">회사명</label>
              <input
                v-model="form.company_name"
                type="text"
                class="form-control"
                placeholder="종목을 선택하면 자동으로 입력됩니다"
                readonly
                disabled
              />
              <div class="form-text">종목 검색 후 자동으로 입력됩니다</div>
            </div>

            <!-- Memo input -->
            <div class="mb-3">
              <label class="form-label">메모 <span class="text-muted">(선택)</span></label>
              <input
                v-model="form.memo"
                type="text"
                class="form-control"
                :class="{ 'is-invalid': memoError }"
                placeholder="메모를 입력하세요"
                maxlength="50"
              />
              <div v-if="memoError" class="invalid-feedback">{{ memoError }}</div>
              <div class="form-text">
                {{ form.memo.length }}/50자
              </div>
            </div>
          </form>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="close">
            취소
          </button>
          <button
            type="button"
            class="btn btn-primary"
            :disabled="!isValid || loading"
            @click="handleSubmit"
          >
            <span v-if="loading" class="spinner-border spinner-border-sm me-2" role="status"></span>
            추가
          </button>
        </div>
      </div>
    </div>
  </div>
  <div v-if="isOpen" class="modal-backdrop fade show"></div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useWatchlistStore } from '@/stores/watchlist'
import type { StockSearchResult } from '@/api/stocks'
import StockSearch from '@/components/stocks/StockSearch.vue'

interface Props {
  isOpen: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  success: []
}>()

const watchlistStore = useWatchlistStore()

const searchQuery = ref('')
const selectedStock = ref<StockSearchResult | null>(null)

const form = ref({
  symbol: '',
  company_name: '',
  memo: ''
})

const loading = ref(false)
const error = ref<string | null>(null)
const memoError = ref<string | null>(null)

const isValid = computed(() => {
  return selectedStock.value !== null &&
         form.value.symbol.length >= 1 &&
         form.value.company_name.length > 0 &&
         form.value.memo.length <= 50 &&
         !memoError.value
})

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    resetForm()
  }
})

function handleStockSelect(stock: StockSearchResult) {
  selectedStock.value = stock
  form.value.symbol = stock.symbol
  form.value.company_name = stock.name
}

async function handleSubmit() {
  if (!isValid.value || loading.value) return

  loading.value = true
  error.value = null

  try {
    await watchlistStore.addToWatchlist({
      symbol: form.value.symbol,
      company_name: form.value.company_name,
      memo: form.value.memo || undefined
    })
    emit('success')
    close()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '종목 추가에 실패했습니다'
  } finally {
    loading.value = false
  }
}

function close() {
  emit('close')
}

function handleBackdropClick() {
  close()
}

function clearError() {
  error.value = null
}

function resetForm() {
  searchQuery.value = ''
  selectedStock.value = null
  form.value = {
    symbol: '',
    company_name: '',
    memo: ''
  }
  error.value = null
  memoError.value = null
  loading.value = false
}
</script>

<style scoped>
.modal {
  background: rgba(0, 0, 0, 0.5);
}

.required::after {
  content: ' *';
  color: var(--tblr-danger);
}

.alert-icon {
  margin-right: 0.5rem;
}

.selected-stock {
  padding: 0.5rem;
  background-color: var(--color-bg-alt);
  border-radius: 0.25rem;
  font-size: 0.875rem;
}

.form-control:disabled {
  background-color: var(--tblr-bg-surface-secondary);
  opacity: 0.7;
  cursor: not-allowed;
}
</style>
