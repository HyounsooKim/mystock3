<template>
  <div class="watchlist-table">
    <!-- Empty state -->
    <div v-if="!hasItems && !loading" class="empty-state">
      <div class="empty-icon">📊</div>
      <h3>관심종목이 없습니다</h3>
      <p>관심있는 종목을 추가해보세요</p>
    </div>

    <!-- Loading state -->
    <div v-else-if="loading" class="loading-state">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>

    <!-- Table with items -->
    <div v-else class="table-responsive">
      <table class="table table-hover">
        <thead>
          <tr>
            <th style="width: 40px"></th>
            <th>종목명</th>
            <th>현재가</th>
            <th>등락률</th>
            <th>메모</th>
            <th style="width: 100px">액션</th>
          </tr>
        </thead>
        <tbody ref="tableBody">
          <WatchlistItem
            v-for="item in items"
            :key="item.id"
            :item="item"
            @edit="handleEdit"
            @delete="handleDelete"
          />
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch, onBeforeUnmount } from 'vue'
import { storeToRefs } from 'pinia'
import { useWatchlistStore } from '@/stores/watchlist'
import WatchlistItem from '@/components/WatchlistItem.vue'
import type { WatchlistItemWithQuote } from '@/types'
// @ts-ignore - sortablejs types have import issues
import Sortable from 'sortablejs'

const watchlistStore = useWatchlistStore()
const { items, loading, hasItems } = storeToRefs(watchlistStore)

const tableBody = ref<HTMLElement | null>(null)
let sortableInstance: Sortable | null = null

const emit = defineEmits<{
  edit: [item: WatchlistItemWithQuote]
  delete: [itemId: string]
}>()

onMounted(async () => {
  console.log('[WatchlistTable] Mounted, fetching watchlist...')
  await watchlistStore.fetchWatchlist()
  console.log('[WatchlistTable] Fetch complete. Items:', items.value)
  console.log('[WatchlistTable] hasItems:', hasItems.value)
  await nextTick()
  initSortable()
})

onBeforeUnmount(() => {
  destroySortable()
})

// Watch items and reinitialize sortable when they change
watch(items, async () => {
  await nextTick()
  destroySortable()
  initSortable()
}, { deep: true })

function destroySortable() {
  if (sortableInstance) {
    sortableInstance.destroy()
    sortableInstance = null
  }
}

function initSortable() {
  if (!tableBody.value || !hasItems.value) return
  
  // Destroy existing instance if any
  destroySortable()

  sortableInstance = new Sortable(tableBody.value, {
    animation: 150,
    handle: '.drag-handle',
    ghostClass: 'sortable-ghost',
    dragClass: 'sortable-drag',
    onEnd: async (evt: any) => {
      if (evt.oldIndex === undefined || evt.newIndex === undefined) return
      if (evt.oldIndex === evt.newIndex) return

      // Get reordered item IDs from DOM order
      const rows = tableBody.value?.querySelectorAll('tr[data-item-id]')
      if (!rows) return
      
      const reorderedIds = Array.from(rows).map(row => 
        (row as HTMLElement).getAttribute('data-item-id')!
      )

      try {
        await watchlistStore.reorderWatchlist(reorderedIds)
        // Note: fetchWatchlist will be called by the store, which triggers watch
      } catch (err) {
        // Error handled by store
        // Refresh to revert UI on failure
        await watchlistStore.fetchWatchlist()
      }
    }
  })
}

function handleEdit(item: WatchlistItemWithQuote) {
  emit('edit', item)
}

function handleDelete(itemId: string) {
  emit('delete', itemId)
}
</script>

<style scoped>
.watchlist-table {
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

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
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

.sortable-ghost {
  opacity: 0.4;
  background: var(--tblr-bg-surface-secondary);
}

.sortable-drag {
  opacity: 0.8;
}
</style>
