<template>
  <div class="portfolio-table">
    <!-- Empty State -->
    <div v-if="entries.length === 0" class="empty-state">
      <div class="empty-icon">💼</div>
      <h3>포트폴리오가 비어 있습니다</h3>
      <p>종목을 추가하여 수익률을 추적하세요</p>
    </div>

    <!-- Table with items -->
    <div v-else>
      <div class="table-responsive">
        <table class="table table-hover">
          <thead>
            <tr>
              <th>종목</th>
              <th>카테고리</th>
              <th>수량</th>
              <th>매수가</th>
              <th>현재가</th>
              <th>평가금액</th>
              <th>손익</th>
              <th style="width: 100px">관리</th>
            </tr>
          </thead>
          <tbody>
            <PortfolioItem
              v-for="entry in entries"
              :key="entry.entry_id"
              :entry="entry"
              @edit="onEdit"
              @delete="onDelete"
            />
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PortfolioEntryWithMetrics } from '@/types'
import PortfolioItem from './PortfolioItem.vue'

interface Props {
  entries: PortfolioEntryWithMetrics[]
}

interface Emits {
  (e: 'edit', entry: PortfolioEntryWithMetrics): void
  (e: 'delete', entryId: string): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

function onEdit(entry: PortfolioEntryWithMetrics) {
  emit('edit', entry)
}

function onDelete(entryId: string) {
  emit('delete', entryId)
}
</script>

<style scoped>
.portfolio-table {
  min-height: 400px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  text-align: center;
  color: var(--tblr-muted);
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  color: var(--tblr-body-color);
}

.empty-state p {
  font-size: 1rem;
}

.table {
  margin-bottom: 0;
}

.table thead th {
  border-bottom: 2px solid var(--tblr-border-color);
  font-weight: 600;
  color: var(--tblr-secondary);
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.05em;
}
</style>
