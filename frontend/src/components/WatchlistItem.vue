<template>
  <tr class="watchlist-item" :data-item-id="item.id">
    <td class="drag-handle">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="3" y1="12" x2="21" y2="12"></line>
        <line x1="3" y1="6" x2="21" y2="6"></line>
        <line x1="3" y1="18" x2="21" y2="18"></line>
      </svg>
    </td>
    <td>
      <div class="stock-info">
        <div class="symbol">{{ item.symbol }}</div>
        <div class="company-name">{{ item.company_name }}</div>
      </div>
    </td>
    <td>
      <span class="price">{{ formatPrice(item.current_price) }}</span>
    </td>
    <td>
      <span :class="['change-percent', getChangeClass(item.change_percent)]">
        {{ formatChangePercent(item.change_percent) }}
      </span>
    </td>
    <td>
      <span class="memo" :title="item.memo">{{ item.memo || '-' }}</span>
    </td>
    <td>
      <div class="action-buttons">
        <button
          class="btn btn-sm btn-ghost-secondary"
          @click="handleEdit"
          title="메모 수정"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
          </svg>
        </button>
        <button
          class="btn btn-sm btn-ghost-danger"
          @click="handleDelete"
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
import type { WatchlistItemWithQuote } from '@/types'

interface Props {
  item: WatchlistItemWithQuote
}

const props = defineProps<Props>()

const emit = defineEmits<{
  edit: [item: WatchlistItemWithQuote]
  delete: [itemId: string]
}>()

function formatPrice(price: number | string | null): string {
  if (price === null || price === undefined) return '-'
  // Convert string to number if needed
  const numPrice = typeof price === 'string' ? parseFloat(price) : price
  if (isNaN(numPrice)) return '-'
  return new Intl.NumberFormat('ko-KR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(numPrice)
}

function formatChangePercent(percent: number | string | null): string {
  if (percent === null || percent === undefined) return '-'
  // Convert string to number if needed
  const numPercent = typeof percent === 'string' ? parseFloat(percent) : percent
  if (isNaN(numPercent)) return '-'
  const sign = numPercent >= 0 ? '+' : ''
  return `${sign}${numPercent.toFixed(2)}%`
}

function getChangeClass(percent: number | string | null): string {
  if (percent === null || percent === undefined) return 'text-muted'
  // Convert string to number if needed
  const numPercent = typeof percent === 'string' ? parseFloat(percent) : percent
  if (isNaN(numPercent)) return 'text-muted'
  if (numPercent > 0) return 'text-success'
  if (numPercent < 0) return 'text-danger'
  return 'text-muted'
}

function handleEdit() {
  emit('edit', props.item)
}

function handleDelete() {
  emit('delete', props.item.id)
}
</script>

<style scoped>
.watchlist-item {
  cursor: default;
}

.drag-handle {
  cursor: grab;
  color: var(--tblr-muted);
  opacity: 0.5;
  transition: opacity 0.2s;
}

.drag-handle:hover {
  opacity: 1;
}

.drag-handle:active {
  cursor: grabbing;
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

.price {
  font-weight: 500;
  font-family: 'Courier New', monospace;
}

.change-percent {
  font-weight: 600;
  font-family: 'Courier New', monospace;
}

.memo {
  display: inline-block;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--tblr-muted);
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
</style>
