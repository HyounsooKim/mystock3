<template>
  <div class="page-header">
    <div class="container-xl">
      <div class="row align-items-center">
        <div class="col">
          <h1 class="page-title">포트폴리오</h1>
          <div class="text-muted mt-1">
            보유 종목의 수익률을 추적하세요
          </div>
        </div>
        <div class="col-auto">
          <div class="btn-list">
            <button class="btn btn-primary" @click="showAddModal = true">
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
  </div>

  <div class="page-body">
    <div class="container-xl">
      <!-- Error Alert -->
      <div v-if="portfolioStore.error" class="alert alert-danger alert-dismissible mb-3" role="alert">
          <div class="d-flex">
            <div>
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon alert-icon">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
            </div>
            <div>{{ portfolioStore.error }}</div>
          </div>
          <button type="button" class="btn-close" @click="portfolioStore.clearError()"></button>
      </div>

      <!-- Summary Cards -->
      <h3 class="mb-3">수익률</h3>
      <div class="row row-cards mb-3">
        <div class="col-12">
          <div class="card">
            <div class="card-body p-0">
              <div class="row g-0" style="min-height: 300px;">
                <div class="col-lg-3 p-3 border-end d-flex flex-column">
                  <div class="card mb-2" style="flex: 1;">
                    <div class="card-body py-2">
                      <div class="text-muted mb-1 small">총 평가금액</div>
                      <div class="h3 mb-0">${{ formatPrice(portfolioStore.totalMarketValue) }}</div>
                    </div>
                  </div>
                  <div class="card mb-2" style="flex: 1;">
                    <div class="card-body py-2">
                      <div class="text-muted mb-1 small">총 손익</div>
                      <div class="d-flex align-items-center">
                        <div class="h3 mb-0 me-2" :class="totalProfitLossClass">
                          {{ formatProfitLoss(portfolioStore.totalProfitLoss) }}
                        </div>
                        <div class="h4 mb-0" :class="totalProfitLossPercentClass">
                          {{ formatPercent(portfolioStore.totalProfitLossPercent) }}
                        </div>
                        <svg v-if="portfolioStore.totalProfitLoss > 0" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon ms-1 text-success">
                          <path d="M3 17l6 -6l4 4l8 -8"></path>
                          <path d="M14 7l7 0l0 7"></path>
                        </svg>
                        <svg v-else-if="portfolioStore.totalProfitLoss < 0" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="icon ms-1 text-danger">
                          <path d="M3 7l6 6l4 -4l8 8"></path>
                          <path d="M21 10l0 7l-7 0"></path>
                        </svg>
                      </div>
                    </div>
                  </div>
                  <div class="card mb-0" style="flex: 2;">
                    <div class="card-body py-2">
                      <div class="text-muted mb-1 small">종목 분석 요약</div>
                      <div class="text-muted small">준비중...</div>
                    </div>
                  </div>
                </div>
                <div class="col-lg-9 p-3">
                  <div class="card mb-0 h-100">
                    <div class="card-body">
                      <div v-if="portfolioStore.filteredEntries.length > 0">
                        <PortfolioHeatmap :entries="portfolioStore.filteredEntries" />
                      </div>
                      <div v-else class="text-muted text-center py-5">
                        등록된 종목이 없습니다
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Portfolio Table with Tabs -->
      <h3 class="mb-3">보유 종목</h3>
      <div class="card">
        <div class="card-header">
          <ul class="nav nav-tabs card-header-tabs" data-bs-toggle="tabs" role="tablist">
            <li class="nav-item" role="presentation">
              <a 
                href="#tabs-all" 
                class="nav-link" 
                :class="{ active: portfolioStore.selectedCategory === 'all' }"
                @click.prevent="selectCategory('all')"
                data-bs-toggle="tab"
                :aria-selected="portfolioStore.selectedCategory === 'all'"
                role="tab"
              >
                전체
              </a>
            </li>
            <li class="nav-item" role="presentation">
              <a 
                href="#tabs-long" 
                class="nav-link" 
                :class="{ active: portfolioStore.selectedCategory === '장기' }"
                @click.prevent="selectCategory('장기')"
                data-bs-toggle="tab"
                :aria-selected="portfolioStore.selectedCategory === '장기'"
                role="tab"
              >
                장기
              </a>
            </li>
            <li class="nav-item" role="presentation">
              <a 
                href="#tabs-short" 
                class="nav-link" 
                :class="{ active: portfolioStore.selectedCategory === '단기' }"
                @click.prevent="selectCategory('단기')"
                data-bs-toggle="tab"
                :aria-selected="portfolioStore.selectedCategory === '단기'"
                role="tab"
              >
                단기
              </a>
            </li>
            <li class="nav-item" role="presentation">
              <a 
                href="#tabs-scout" 
                class="nav-link" 
                :class="{ active: portfolioStore.selectedCategory === '정찰병' }"
                @click.prevent="selectCategory('정찰병')"
                data-bs-toggle="tab"
                :aria-selected="portfolioStore.selectedCategory === '정찰병'"
                role="tab"
              >
                정찰병
              </a>
            </li>
            <li class="nav-item ms-auto" role="presentation">
              <a 
                href="#" 
                class="nav-link" 
                @click.prevent="refreshPrices"
                :disabled="portfolioStore.loading"
                title="실시간 가격 새로고침"
                role="tab"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" :class="{ 'spinning': portfolioStore.loading }">
                  <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
                </svg>
              </a>
            </li>
          </ul>
        </div>
        <div class="card-body">
          <div class="tab-content">
            <div class="tab-pane" :class="{ active: portfolioStore.selectedCategory === 'all', show: portfolioStore.selectedCategory === 'all' }" id="tabs-all" role="tabpanel">
              <PortfolioTable
                v-if="portfolioStore.selectedCategory === 'all'"
                :entries="portfolioStore.filteredEntries"
                @edit="handleEdit"
                @delete="handleDelete"
              />
            </div>
            <div class="tab-pane" :class="{ active: portfolioStore.selectedCategory === '장기', show: portfolioStore.selectedCategory === '장기' }" id="tabs-long" role="tabpanel">
              <PortfolioTable
                v-if="portfolioStore.selectedCategory === '장기'"
                :entries="portfolioStore.filteredEntries"
                @edit="handleEdit"
                @delete="handleDelete"
              />
            </div>
            <div class="tab-pane" :class="{ active: portfolioStore.selectedCategory === '단기', show: portfolioStore.selectedCategory === '단기' }" id="tabs-short" role="tabpanel">
              <PortfolioTable
                v-if="portfolioStore.selectedCategory === '단기'"
                :entries="portfolioStore.filteredEntries"
                @edit="handleEdit"
                @delete="handleDelete"
              />
            </div>
            <div class="tab-pane" :class="{ active: portfolioStore.selectedCategory === '정찰병', show: portfolioStore.selectedCategory === '정찰병' }" id="tabs-scout" role="tabpanel">
              <PortfolioTable
                v-if="portfolioStore.selectedCategory === '정찰병'"
                :entries="portfolioStore.filteredEntries"
                @edit="handleEdit"
                @delete="handleDelete"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>  <!-- Add Stock Modal -->
  <AddStockModal
      :is-open="showAddModal"
      @close="showAddModal = false"
      @submit="handleAdd"
    />

    <!-- Edit Entry Modal -->
    <EditEntryModal
      :is-open="showEditModal"
      :entry="selectedEntry"
      @close="showEditModal = false"
      @submit="handleUpdate"
    />

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="modal-backdrop" @click.self="showDeleteModal = false">
      <div class="modal-dialog modal-sm">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">삭제 확인</h5>
            <button type="button" class="btn-close" @click="showDeleteModal = false"></button>
          </div>
          <div class="modal-body">
            <p>정말 삭제하시겠습니까?</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showDeleteModal = false">
              취소
            </button>
            <button type="button" class="btn btn-danger" @click="confirmDelete">
              삭제
            </button>
          </div>
        </div>
      </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onActivated } from 'vue'
import { usePortfolioStore } from '@/stores/portfolio'
import type { PortfolioEntryWithMetrics, PortfolioEntryCreate, PortfolioEntryUpdate, PortfolioCategory } from '@/types'
import PortfolioTable from '@/components/portfolio/PortfolioTable.vue'
import PortfolioHeatmap from '@/components/portfolio/PortfolioHeatmap.vue'
import AddStockModal from '@/components/portfolio/AddStockModal.vue'
import EditEntryModal from '@/components/portfolio/EditEntryModal.vue'

const portfolioStore = usePortfolioStore()

const showAddModal = ref(false)
const showEditModal = ref(false)
const showDeleteModal = ref(false)
const selectedEntry = ref<PortfolioEntryWithMetrics | null>(null)
const entryToDelete = ref<string | null>(null)

const totalProfitLossClass = computed(() => {
  const profitLoss = portfolioStore.totalProfitLoss
  if (profitLoss > 0) return 'profit-positive'
  if (profitLoss < 0) return 'profit-negative'
  return 'profit-neutral'
})

const totalProfitLossPercentClass = computed(() => {
  const percent = portfolioStore.totalProfitLossPercent
  if (percent > 0) return 'profit-positive'
  if (percent < 0) return 'profit-negative'
  return 'profit-neutral'
})

// Initial load
onMounted(async () => {
  await portfolioStore.fetchPortfolio()
})

// Reload when component is activated (navigating back from other pages)
onActivated(async () => {
  await portfolioStore.fetchPortfolio()
})

// Manual refresh function
async function refreshPrices() {
  await portfolioStore.fetchPortfolio()
}

function selectCategory(category: PortfolioCategory | 'all') {
  portfolioStore.setCategory(category)
}

async function handleAdd(data: PortfolioEntryCreate) {
  try {
    await portfolioStore.addEntry(data)
    showAddModal.value = false
    // Refresh entire portfolio to get updated calculations
    await portfolioStore.fetchPortfolio()
  } catch (err: any) {
    // Error already stored in portfolioStore.error
    // Check for specific Korean error messages
    const errorMsg = err.response?.data?.detail || ''
    if (errorMsg.includes('이미 해당 카테고리에 등록된 종목입니다')) {
      // Keep modal open to allow user to change category
    } else if (errorMsg.includes('최대 10개 종목까지 등록 가능')) {
      // Show error and close modal
      showAddModal.value = false
    }
  }
}

function handleEdit(entry: PortfolioEntryWithMetrics) {
  selectedEntry.value = entry
  showEditModal.value = true
}

async function handleUpdate(data: PortfolioEntryUpdate) {
  if (!selectedEntry.value) return

  try {
    await portfolioStore.updateEntry(selectedEntry.value.entry_id, data)
    showEditModal.value = false
    selectedEntry.value = null
  } catch (err) {
    // Error already stored in portfolioStore.error
  }
}

function handleDelete(entryId: string) {
  entryToDelete.value = entryId
  showDeleteModal.value = true
}

async function confirmDelete() {
  if (!entryToDelete.value) return

  try {
    await portfolioStore.deleteEntry(entryToDelete.value)
    showDeleteModal.value = false
    entryToDelete.value = null
  } catch (err) {
    // Error already stored in portfolioStore.error
  }
}

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
</script>

<style scoped>
.alert-icon {
  margin-right: 0.5rem;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.text-success {
  color: var(--tblr-success) !important;
}

.text-danger {
  color: var(--tblr-danger) !important;
}

.text-muted-custom {
  color: var(--tblr-muted) !important;
}

/* Delete modal styles */
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

.modal-sm {
  max-width: 400px;
}

.modal-content {
  background-color: var(--tblr-body-bg);
  border: 1px solid var(--tblr-border-color);
  border-radius: 0.5rem;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--tblr-border-color);
}

.modal-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.modal-body {
  padding: 1.5rem;
}

.modal-footer {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--tblr-border-color);
}

.btn-secondary {
  background-color: var(--tblr-secondary);
  color: white;
}

.btn-danger {
  background-color: var(--tblr-danger);
  color: white;
}

.btn-icon {
  border: none !important;
}

.btn-icon:hover {
  background-color: rgba(0, 0, 0, 0.05);
}
</style>
