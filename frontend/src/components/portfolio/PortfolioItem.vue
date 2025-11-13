<template>
  <tr class="portfolio-item">
    <td>
      <div class="stock-info">
        <div class="symbol">{{ entry.symbol }}</div>
        <div class="company-name">{{ entry.company_name }}</div>
      </div>
    </td>

    <td>
      <span class="badge" :class="categoryBadgeClass">{{ entry.category }}</span>
    </td>

    <td>
      <span class="quantity">{{ entry.quantity }}주</span>
    </td>

    <td>
      <span class="price">${{ formatPrice(entry.purchase_price) }}</span>
    </td>

    <td>
      <span v-if="entry.current_price !== null" class="price">${{ formatPrice(entry.current_price) }}</span>
      <span v-else class="text-muted" title="현재가 정보를 가져올 수 없습니다">-</span>
    </td>

    <td>
      <span v-if="entry.market_value !== null" class="price">${{ formatPrice(entry.market_value) }}</span>
      <span v-else class="text-muted" title="평가금액을 계산할 수 없습니다">-</span>
    </td>

    <td>
      <div v-if="entry.profit_loss !== null" :class="['profit-loss', profitLossClass]">
        <div class="profit-loss-amount">{{ formatProfitLoss(entry.profit_loss) }}</div>
        <div class="profit-loss-percent">
          ({{ entry.profit_loss_percent !== null ? formatPercent(entry.profit_loss_percent) : '-' }})
        </div>
      </div>
      <span v-else class="text-muted" title="손익을 계산할 수 없습니다">-</span>
    </td>

    <td>
      <div class="action-buttons">
        <button
          class="btn btn-sm btn-ghost-secondary"
          @click="onEdit"
          title="수정"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
          </svg>
        </button>
        <button
          class="btn btn-sm btn-ghost-danger"
          @click="onDelete"
          title="삭제"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
      </div>
    </td>
  </tr>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PortfolioEntryWithMetrics } from '@/types'

interface Props {
  entry: PortfolioEntryWithMetrics
}

interface Emits {
  (e: 'edit', entry: PortfolioEntryWithMetrics): void
  (e: 'delete', entryId: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const categoryBadgeClass = computed(() => {
  switch (props.entry.category) {
    case '장기':
      return 'badge-success'
    case '단기':
      return 'badge-warning'
    case '정찰병':
      return 'badge-info'
    default:
      return 'badge-secondary'
  }
})

const profitLossClass = computed(() => {
  const profitLoss = props.entry.profit_loss
  if (profitLoss === null) return ''
  if (profitLoss > 0) return 'profit-positive'
  if (profitLoss < 0) return 'profit-negative'
  return 'profit-neutral'
})

function formatPrice(value: number): string {
  return value.toFixed(2)
}

function formatProfitLoss(value: number): string {
  const sign = value >= 0 ? '+' : ''
  return `${sign}$${value.toFixed(2)}`
}

function formatPercent(value: number): string {
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

function onEdit() {
  emit('edit', props.entry)
}

function onDelete() {
  emit('delete', props.entry.entry_id)
}
</script>

<style scoped>
.portfolio-item {
  cursor: default;
}

.stock-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.symbol {
  font-weight: 600;
  font-size: 1rem;
  color: var(--tblr-body-color);
}

.company-name {
  font-size: 0.875rem;
  color: var(--tblr-muted);
}

.badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
  display: inline-block;
}

.badge-success {
  background-color: var(--tblr-success-lt);
  color: var(--tblr-success);
}

.badge-warning {
  background-color: var(--tblr-warning-lt);
  color: var(--tblr-warning);
}

.badge-info {
  background-color: var(--tblr-info-lt);
  color: var(--tblr-info);
}

.badge-secondary {
  background-color: var(--tblr-secondary-lt);
  color: var(--tblr-secondary);
}

.quantity {
  color: var(--tblr-body-color);
}

.price {
  font-weight: 500;
  font-family: 'Courier New', monospace;
  color: var(--tblr-body-color);
}

.profit-loss {
  font-weight: 600;
  font-family: 'Courier New', monospace;
}

.profit-positive {
  color: var(--tblr-success);
}

.profit-negative {
  color: var(--tblr-danger);
}

.profit-neutral {
  color: var(--tblr-muted);
}

.profit-loss-percent {
  font-size: 0.875rem;
}

.action-buttons {
  display: flex;
  gap: 0.25rem;
  justify-content: flex-end;
}

.btn-ghost-secondary,
.btn-ghost-danger {
  padding: 0.25rem 0.5rem;
  border: none;
  background: transparent;
  transition: all 0.2s;
}

.btn-ghost-secondary:hover {
  background: var(--tblr-secondary-lt);
  color: var(--tblr-secondary);
}

.btn-ghost-danger:hover {
  background: var(--tblr-danger-lt);
  color: var(--tblr-danger);
}

.text-muted {
  color: var(--tblr-muted);
}
</style>
