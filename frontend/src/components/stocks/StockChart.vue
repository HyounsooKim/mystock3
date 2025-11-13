<template>
  <div class="stock-chart">
    <!-- Period selector -->
    <div class="chart-header">
      <div class="period-selector">
        <button
          v-for="p in periods"
          :key="p.value"
          class="btn btn-sm"
          :class="{ 'btn-primary': period === p.value, 'btn-ghost-secondary': period !== p.value }"
          @click="changePeriod(p.value)"
        >
          {{ p.label }}
        </button>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="chart-loading">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="text-muted mt-2">차트 데이터를 불러오는 중...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="alert alert-danger" role="alert">
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
    </div>

    <!-- Chart canvas -->
    <div v-else ref="chartContainer" class="chart-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'
import { getStockHistory } from '@/api/stocks'
import type { StockHistoryResponse } from '@/api/stocks'

interface Props {
  symbol: string
  height?: number
}

const props = withDefaults(defineProps<Props>(), {
  height: 400
})

type Period = '1D' | '1W' | '1M' | '3M' | '1Y'

interface PeriodOption {
  value: Period
  label: string
}

const periods: PeriodOption[] = [
  { value: '1D', label: '1일' },
  { value: '1W', label: '1주' },
  { value: '1M', label: '1개월' },
  { value: '3M', label: '3개월' },
  { value: '1Y', label: '1년' }
]

const period = ref<Period>('1M')
const chartContainer = ref<HTMLElement | null>(null)
const chartInstance = ref<ECharts | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const historyData = ref<StockHistoryResponse | null>(null)

onMounted(async () => {
  await loadChartData()
  await nextTick()
  initChart()

  // Handle window resize
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (chartInstance.value) {
    chartInstance.value.dispose()
  }
  window.removeEventListener('resize', handleResize)
})

watch(() => props.symbol, async () => {
  await loadChartData()
  updateChart()
})

async function loadChartData() {
  loading.value = true
  error.value = null

  try {
    historyData.value = await getStockHistory(props.symbol, period.value)
  } catch (err: any) {
    error.value = err.response?.data?.detail || '차트 데이터를 불러오는데 실패했습니다'
  } finally {
    loading.value = false
  }
}

async function changePeriod(newPeriod: Period) {
  period.value = newPeriod
  await loadChartData()
  updateChart()
}

function initChart() {
  if (!chartContainer.value || !historyData.value) return

  chartInstance.value = echarts.init(chartContainer.value)
  updateChart()
}

function updateChart() {
  if (!chartInstance.value || !historyData.value) return

  const dates = historyData.value.data.map(d => d.date)
  const values = historyData.value.data.map(d => [d.open, d.close, d.low, d.high])
  const volumes = historyData.value.data.map(d => d.volume)

  const option: EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params: any) => {
        const data = params[0]
        if (!data) return ''
        
        const values = data.value as number[]
        return `
          <div style="font-weight: bold; margin-bottom: 4px;">${data.name}</div>
          <div>시가: ${formatPrice(values[0])}</div>
          <div>종가: ${formatPrice(values[1])}</div>
          <div>저가: ${formatPrice(values[2])}</div>
          <div>고가: ${formatPrice(values[3])}</div>
        `
      }
    },
    grid: [
      {
        left: '10%',
        right: '10%',
        top: '10%',
        height: '60%'
      },
      {
        left: '10%',
        right: '10%',
        top: '75%',
        height: '15%'
      }
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        boundaryGap: false,
        axisLine: { onZero: false },
        splitLine: { show: false },
        min: 'dataMin',
        max: 'dataMax'
      },
      {
        type: 'category',
        gridIndex: 1,
        data: dates,
        boundaryGap: false,
        axisLine: { onZero: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        min: 'dataMin',
        max: 'dataMax'
      }
    ],
    yAxis: [
      {
        scale: true,
        splitArea: {
          show: true
        }
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 0,
        end: 100
      },
      {
        show: true,
        xAxisIndex: [0, 1],
        type: 'slider',
        top: '92%',
        start: 0,
        end: 100
      }
    ],
    series: [
      {
        name: props.symbol,
        type: 'candlestick',
        data: values,
        itemStyle: {
          color: '#ef5350',
          color0: '#26a69a',
          borderColor: '#ef5350',
          borderColor0: '#26a69a'
        }
      },
      {
        name: '거래량',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes,
        itemStyle: {
          color: '#7cb5ec'
        }
      }
    ]
  }

  chartInstance.value.setOption(option)
}

function handleResize() {
  if (chartInstance.value) {
    chartInstance.value.resize()
  }
}

function formatPrice(price: number): string {
  return new Intl.NumberFormat('ko-KR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(price)
}
</script>

<style scoped>
.stock-chart {
  width: 100%;
}

.chart-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1rem;
}

.period-selector {
  display: flex;
  gap: 0.5rem;
}

.btn-ghost-secondary {
  background: transparent;
  border: 1px solid var(--tblr-border-color);
  color: var(--tblr-body-color);
}

.btn-ghost-secondary:hover {
  background: var(--tblr-secondary-lt);
  border-color: var(--tblr-secondary);
  color: var(--tblr-secondary);
}

.chart-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: v-bind('`${height}px`');
}

.chart-container {
  width: 100%;
  height: v-bind('`${height}px`');
}

.alert-icon {
  margin-right: 0.5rem;
}
</style>
