<template>
  <BaseLayout>
    <div class="page-header">
      <div class="container-xl">
        <div class="row align-items-center">
          <div class="col">
            <h1 class="page-title">관심종목</h1>
            <div class="text-muted mt-1">
              관심 있는 종목을 조회하세요.
            </div>
          </div>
          <div class="col-auto">
            <button class="btn btn-primary" @click="openAddModal">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon">
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
              종목 추가
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="page-body">
      <div class="container-xl">
        <!-- Error alert -->
        <div v-if="error" class="alert alert-danger alert-dismissible mb-3" role="alert">
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
          <button type="button" class="btn-close" @click="watchlistStore.clearError()"></button>
        </div>

        <!-- Watchlist card -->
        <div class="card">
          <div class="card-body">
            <WatchlistTable @edit="openEditModal" @delete="handleDelete" />
          </div>
        </div>
      </div>
    </div>

    <!-- Add Stock Modal -->
    <AddStockModal
      :is-open="showAddModal"
      @close="closeAddModal"
      @success="handleAddSuccess"
    />

    <!-- Edit Memo Modal -->
    <EditMemoModal
      v-if="editingItem"
      :is-open="showEditModal"
      :item="editingItem"
      @close="closeEditModal"
      @success="handleEditSuccess"
    />

    <!-- Delete Confirmation Modal -->
    <DeleteConfirmModal
      :is-open="showDeleteModal"
      :item-symbol="deletingItemSymbol"
      :loading="deleting"
      @confirm="confirmDelete"
      @cancel="cancelDelete"
    />
  </BaseLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useWatchlistStore } from '@/stores/watchlist'
import BaseLayout from '@/layouts/BaseLayout.vue'
import WatchlistTable from '@/components/WatchlistTable.vue'
import AddStockModal from '@/components/AddStockModal.vue'
import EditMemoModal from '../components/EditMemoModal.vue'
import DeleteConfirmModal from '../components/DeleteConfirmModal.vue'
import type { WatchlistItemWithQuote } from '@/types'

const watchlistStore = useWatchlistStore()
const { error } = storeToRefs(watchlistStore)

// Add modal
const showAddModal = ref(false)

function openAddModal() {
  showAddModal.value = true
}

function closeAddModal() {
  showAddModal.value = false
}

function handleAddSuccess() {
  showAddModal.value = false
  // Table will auto-refresh via store
}

// Edit modal
const showEditModal = ref(false)
const editingItem = ref<WatchlistItemWithQuote | null>(null)

function openEditModal(item: WatchlistItemWithQuote) {
  editingItem.value = item
  showEditModal.value = true
}

function closeEditModal() {
  showEditModal.value = false
  editingItem.value = null
}

function handleEditSuccess() {
  showEditModal.value = false
  editingItem.value = null
  // Table will auto-refresh via store
}

// Delete modal
const showDeleteModal = ref(false)
const deletingItemId = ref<string | null>(null)
const deletingItemSymbol = ref<string>('')
const deleting = ref(false)

function handleDelete(itemId: string) {
  const item = watchlistStore.items.find(i => i.id === itemId)
  if (!item) return

  deletingItemId.value = itemId
  deletingItemSymbol.value = item.symbol
  showDeleteModal.value = true
}

async function confirmDelete() {
  if (!deletingItemId.value) return

  deleting.value = true
  try {
    await watchlistStore.deleteWatchlistItem(deletingItemId.value)
    showDeleteModal.value = false
    deletingItemId.value = null
    deletingItemSymbol.value = ''
  } catch (err) {
    // Error handled by store
  } finally {
    deleting.value = false
  }
}

function cancelDelete() {
  showDeleteModal.value = false
  deletingItemId.value = null
  deletingItemSymbol.value = ''
}
</script>

<style scoped>
.page-header {
  margin-bottom: 2rem;
}

.alert-icon {
  margin-right: 0.5rem;
}
</style>
