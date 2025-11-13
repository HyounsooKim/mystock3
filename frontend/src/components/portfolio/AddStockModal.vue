<template>
  <div v-if="isOpen" class="modal-backdrop" @click.self="close">
    <div class="modal-dialog">
      <div class="modal-content">
        <!-- Header -->
        <div class="modal-header">
          <h5 class="modal-title">포트폴리오에 추가</h5>
        </div>

        <!-- Body -->
        <div class="modal-body">
          <!-- Error Alert -->
          <div v-if="error" class="alert alert-danger" role="alert">
            {{ error }}
          </div>

          <form @submit.prevent="handleSubmit">
            <!-- Stock Search -->
            <div class="mb-3">
              <label class="form-label">종목 검색</label>
              <StockSearch
                v-model="searchQuery"
                @select="handleStockSelect"
              />
              <div v-if="selectedStock" class="selected-stock mt-2">
                <strong>{{ selectedStock.symbol }}</strong> - {{ selectedStock.name }}
              </div>
            </div>

            <!-- Category -->
            <div class="mb-3">
              <label class="form-label">투자 카테고리 *</label>
              <select
                v-model="form.category"
                class="form-select"
                :class="{ 'is-invalid': validationErrors.category }"
                required
              >
                <option value="">카테고리 선택</option>
                <option value="장기">장기</option>
                <option value="단기">단기</option>
                <option value="정찰병">정찰병</option>
              </select>
              <div v-if="validationErrors.category" class="invalid-feedback">
                {{ validationErrors.category }}
              </div>
            </div>

            <!-- Purchase Price -->
            <div class="mb-3">
              <label class="form-label">매수 단가 (USD) *</label>
              <input
                v-model.number="form.purchase_price"
                type="number"
                step="0.01"
                min="0.01"
                class="form-control"
                :class="{ 'is-invalid': validationErrors.purchase_price }"
                placeholder="예: 245.50"
                required
              />
              <div v-if="validationErrors.purchase_price" class="invalid-feedback">
                {{ validationErrors.purchase_price }}
              </div>
            </div>

            <!-- Quantity -->
            <div class="mb-3">
              <label class="form-label">수량 (주) *</label>
              <input
                v-model.number="form.quantity"
                type="number"
                step="1"
                min="1"
                class="form-control"
                :class="{ 'is-invalid': validationErrors.quantity }"
                placeholder="예: 10"
                required
              />
              <div v-if="validationErrors.quantity" class="invalid-feedback">
                {{ validationErrors.quantity }}
              </div>
            </div>

            <!-- Total Investment -->
            <div v-if="form.purchase_price && form.quantity" class="alert alert-info">
              <strong>총 투자금액:</strong> ${{ (form.purchase_price * form.quantity).toFixed(2) }}
            </div>
          </form>
        </div>

        <!-- Footer -->
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="close">
            닫기
          </button>
          <button
            type="button"
            class="btn btn-primary"
            :disabled="!isFormValid || loading"
            @click="handleSubmit"
          >
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
            추가
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { PortfolioCategory, PortfolioEntryCreate } from '@/types'
import type { StockSearchResult } from '@/api/stocks'
import StockSearch from '@/components/stocks/StockSearch.vue'

interface Props {
  isOpen: boolean
}

interface Emits {
  (e: 'close'): void
  (e: 'submit', data: PortfolioEntryCreate): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const searchQuery = ref('')
const selectedStock = ref<StockSearchResult | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const form = ref({
  symbol: '',
  company_name: '',
  category: '' as PortfolioCategory | '',
  purchase_price: null as number | null,
  quantity: null as number | null,
})

const validationErrors = ref({
  category: '',
  purchase_price: '',
  quantity: '',
})

const isFormValid = computed(() => {
  return (
    selectedStock.value !== null &&
    form.value.category !== '' &&
    form.value.purchase_price !== null &&
    form.value.purchase_price > 0 &&
    form.value.quantity !== null &&
    form.value.quantity > 0
  )
})

watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    resetForm()
  }
})

function handleStockSelect(stock: StockSearchResult) {
  selectedStock.value = stock
  form.value.symbol = stock.symbol
  form.value.company_name = stock.name
}

function validateForm(): boolean {
  validationErrors.value = {
    category: '',
    purchase_price: '',
    quantity: '',
  }

  let isValid = true

  if (!form.value.category) {
    validationErrors.value.category = '카테고리를 선택하세요'
    isValid = false
  }

  if (!form.value.purchase_price || form.value.purchase_price <= 0) {
    validationErrors.value.purchase_price = '매수 단가를 입력하세요 (0보다 커야 함)'
    isValid = false
  }

  if (!form.value.quantity || form.value.quantity <= 0) {
    validationErrors.value.quantity = '수량을 입력하세요 (0보다 커야 함)'
    isValid = false
  }

  return isValid
}

async function handleSubmit() {
  if (!isFormValid.value) {
    validateForm()
    return
  }

  if (!validateForm()) {
    return
  }

  const entryData: PortfolioEntryCreate = {
    symbol: form.value.symbol,
    company_name: form.value.company_name,
    category: form.value.category as PortfolioCategory,
    purchase_price: form.value.purchase_price!,
    quantity: form.value.quantity!,
  }

  emit('submit', entryData)
}

function resetForm() {
  searchQuery.value = ''
  selectedStock.value = null
  error.value = null
  form.value = {
    symbol: '',
    company_name: '',
    category: '',
    purchase_price: null,
    quantity: null,
  }
  validationErrors.value = {
    category: '',
    purchase_price: '',
    quantity: '',
  }
}

function close() {
  emit('close')
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
}

.modal-dialog {
  width: 100%;
  max-width: 600px;
  margin: 1.75rem auto;
}

.modal-content {
  background-color: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
}

.modal-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.btn-close {
  background: transparent;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  opacity: 0.5;
}

.btn-close:hover {
  opacity: 1;
}

.btn-close::before {
  content: '×';
}

.modal-body {
  padding: 1.5rem;
}

.modal-footer {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--color-border);
}

.selected-stock {
  padding: 0.5rem;
  background-color: var(--color-bg-alt);
  border-radius: 0.25rem;
  font-size: 0.875rem;
}

.form-label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-control,
.form-select {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  background-color: var(--color-bg);
  color: var(--color-text);
}

.form-control:focus,
.form-select:focus {
  outline: none;
  border-color: var(--tblr-primary);
  box-shadow: 0 0 0 0.2rem rgba(var(--tblr-primary-rgb), 0.25);
}

.is-invalid {
  border-color: var(--color-loss);
}

.invalid-feedback {
  display: block;
  margin-top: 0.25rem;
  font-size: 0.875rem;
  color: var(--color-loss);
}

.alert {
  padding: 0.75rem 1rem;
  border-radius: 0.25rem;
  margin-bottom: 1rem;
}

.alert-danger {
  background-color: rgba(220, 53, 69, 0.1);
  border: 1px solid var(--color-loss);
  color: var(--color-loss);
}

.alert-info {
  background-color: rgba(0, 123, 255, 0.1);
  border: 1px solid #0054a6;
  color: #0054a6;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  border: none;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background-color: var(--tblr-primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--tblr-primary-darken);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background-color: #5a6268;
}

.spinner-border-sm {
  width: 1rem;
  height: 1rem;
  border-width: 0.2rem;
}
</style>
