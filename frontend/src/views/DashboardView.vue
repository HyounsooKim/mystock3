<template>
  <BaseLayout>
    <div class="container-xl py-4">
      <div class="page-header d-print-none mb-4">
        <div class="row align-items-center">
          <div class="col">
            <h2 class="page-title">대시보드</h2>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="text-center py-5">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">로딩 중...</span>
        </div>
      </div>

      <!-- Dashboard Cards -->
      <div v-else class="row row-deck row-cards">
        <!-- Total Portfolio Value Card -->
        <div class="col-sm-6 col-lg-3">
          <div class="card">
            <div class="card-body">
              <div class="d-flex align-items-center">
                <div class="subheader">총 자산</div>
              </div>
              <div class="h1 mb-0">{{ formatCurrency(totalAssets) }}</div>
            </div>
          </div>
        </div>

        <!-- Today's Profit/Loss Card -->
        <div class="col-sm-6 col-lg-3">
          <div class="card">
            <div class="card-body">
              <div class="d-flex align-items-center">
                <div class="subheader">총 손익률</div>
              </div>
              <div class="d-flex align-items-baseline">
                <div class="h1 mb-0 me-2" :class="profitLossColor">
                  {{ formatPercent(totalProfitLossPercent) }}
                </div>
              </div>
              <div class="text-muted" :class="profitLossColor">
                {{ formatCurrency(totalProfitLoss) }}
              </div>
            </div>
          </div>
        </div>

        <!-- Watchlist Count Card -->
        <div class="col-sm-6 col-lg-3">
          <div class="card card-link" @click="navigateTo('/watchlist')">
            <div class="card-body">
              <div class="d-flex align-items-center">
                <div class="subheader">관심종목</div>
              </div>
              <div class="d-flex align-items-baseline">
                <div class="h1 mb-0 me-2">{{ watchlistCount }}</div>
                <div class="me-auto">
                  <span class="text-muted">종목</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Portfolio Holdings Count Card -->
        <div class="col-sm-6 col-lg-3">
          <div class="card card-link" @click="navigateTo('/portfolio')">
            <div class="card-body">
              <div class="d-flex align-items-center">
                <div class="subheader">보유종목</div>
              </div>
              <div class="d-flex align-items-baseline">
                <div class="h1 mb-0 me-2">{{ portfolioCount }}</div>
                <div class="me-auto">
                  <span class="text-muted">종목</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Links -->
      <div class="row mt-4">
        <div class="col-12">
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">빠른 이동</h3>
            </div>
            <div class="list-group list-group-flush">
              <a href="/watchlist" class="list-group-item list-group-item-action" @click.prevent="navigateTo('/watchlist')">
                <div class="row align-items-center">
                  <div class="col-auto">
                    <span class="status-dot status-dot-animated bg-primary"></span>
                  </div>
                  <div class="col text-truncate">
                    <div class="text-reset d-block">관심종목 관리</div>
                    <div class="d-block text-muted text-truncate mt-n1">
                      관심 있는 종목을 추가하고 실시간 시세를 모니터링하세요
                    </div>
                  </div>
                </div>
              </a>
              <a href="/portfolio" class="list-group-item list-group-item-action" @click.prevent="navigateTo('/portfolio')">
                <div class="row align-items-center">
                  <div class="col-auto">
                    <span class="status-dot status-dot-animated bg-success"></span>
                  </div>
                  <div class="col text-truncate">
                    <div class="text-reset d-block">포트폴리오 관리</div>
                    <div class="d-block text-muted text-truncate mt-n1">
                      보유 종목의 수익률을 추적하고 분석하세요
                    </div>
                  </div>
                </div>
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </BaseLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import BaseLayout from '../layouts/BaseLayout.vue'
import { usePortfolioStore } from '../stores/portfolio'
import { useWatchlistStore } from '../stores/watchlist'

const router = useRouter()
const portfolioStore = usePortfolioStore()
const watchlistStore = useWatchlistStore()

const isLoading = ref(true)

// Computed properties
const totalAssets = computed(() => {
  return portfolioStore.totalMarketValue
})

const totalProfitLoss = computed(() => {
  return portfolioStore.totalProfitLoss
})

const totalProfitLossPercent = computed(() => {
  return portfolioStore.totalProfitLossPercent
})

const profitLossColor = computed(() => {
  if (totalProfitLoss.value > 0) return 'text-success'
  if (totalProfitLoss.value < 0) return 'text-danger'
  return 'text-muted'
})

const watchlistCount = computed(() => {
  return watchlistStore.itemCount
})

const portfolioCount = computed(() => {
  return portfolioStore.entries.length
})

// Format currency
function formatCurrency(value: number): string {
  if (value === 0) return '$0'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

// Format percentage
function formatPercent(value: number): string {
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

// Navigation
function navigateTo(path: string) {
  router.push(path)
}

// Fetch data on mount
onMounted(async () => {
  try {
    await Promise.all([
      portfolioStore.fetchPortfolio(),
      watchlistStore.fetchWatchlist()
    ])
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  } finally {
    isLoading.value = false
  }
})
</script>

<style scoped>
.card-link {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.card-link:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.status-dot {
  width: 0.5rem;
  height: 0.5rem;
}
</style>
