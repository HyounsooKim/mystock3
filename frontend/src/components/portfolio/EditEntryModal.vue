<template>
  <div v-if="isOpen" class="modal-backdrop" @click.self="close">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">포트폴리오 수정</h5>
          <button type="button" class="btn-close" @click="close"></button>
        </div>

        <div class="modal-body">
          <div v-if="error" class="alert alert-danger">{{ error }}</div>

          <div class="mb-3">
            <div class="stock-info">
              <strong>{{ entry?.symbol }}</strong> - {{ entry?.company_name }}
              <span class="badge badge-secondary ms-2">{{ entry?.category }}</span>
            </div>
          </div>

          <div class="mb-3">
            <label class="form-label">매수 단가 (USD) *</label>
            <input
              v-model.number="form.purchase_price"
              type="number"
              step="0.01"
              min="0.01"
              class="form-control"
              required
            />
          </div>

          <div class="mb-3">
            <label class="form-label">수량 (주) *</label>
            <input
              v-model.number="form.quantity"
              type="number"
              step="1"
              min="1"
              class="form-control"
              required
            />
          </div>

          <div v-if="form.purchase_price && form.quantity" class="alert alert-info">
            <strong>총 투자금액:</strong> ${{ (form.purchase_price * form.quantity).toFixed(2) }}
          </div>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="close">취소</button>
          <button
            type="button"
            class="btn btn-primary"
            :disabled="!isFormValid || loading"
            @click="handleSubmit"
          >
            <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
            수정
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { PortfolioEntryWithMetrics, PortfolioEntryUpdate } from '@/types'

interface Props {
  isOpen: boolean
  entry: PortfolioEntryWithMetrics | null
}

interface Emits {
  (e: 'close'): void
  (e: 'submit', data: PortfolioEntryUpdate): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const loading = ref(false)
const error = ref<string | null>(null)

const form = ref({
  purchase_price: null as number | null,
  quantity: null as number | null,
})

const isFormValid = computed(() => {
  return (
    form.value.purchase_price !== null &&
    form.value.purchase_price > 0 &&
    form.value.quantity !== null &&
    form.value.quantity > 0
  )
})

watch(() => props.entry, (entry) => {
  if (entry) {
    form.value = {
      purchase_price: entry.purchase_price,
      quantity: entry.quantity,
    }
  }
})

function handleSubmit() {
  if (!isFormValid.value) return

  const updateData: PortfolioEntryUpdate = {
    purchase_price: form.value.purchase_price!,
    quantity: form.value.quantity!,
  }

  emit('submit', updateData)
}

function close() {
  emit('close')
}
</script>

<style scoped>
/* Reuse same styles as AddStockModal */
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
  max-width: 500px;
}

.modal-content {
  background-color: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
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
  cursor: pointer;
  opacity: 0.5;
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

.stock-info {
  padding: 0.75rem;
  background-color: var(--color-bg-alt);
  border-radius: 0.25rem;
}

.badge-secondary {
  background-color: #6c757d;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
}

.form-label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-control {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  background-color: var(--color-bg);
  color: var(--color-text);
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
}

.btn-primary {
  background-color: var(--tblr-primary);
  color: white;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}
</style>
