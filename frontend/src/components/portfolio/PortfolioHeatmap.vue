<template>
  <div class="portfolio-heatmap">
    <div ref="chartContainer" class="chart-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import type { PortfolioEntryWithMetrics } from '@/types'

interface Props {
  entries: PortfolioEntryWithMetrics[]
}

const props = defineProps<Props>()

const chartContainer = ref<HTMLDivElement>()
let chartInstance: echarts.ECharts | null = null
let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  if (chartContainer.value) {
    chartInstance = echarts.init(chartContainer.value)
    updateChart()
    
    // Watch for container size changes
    resizeObserver = new ResizeObserver(() => {
      chartInstance?.resize()
    })
    resizeObserver.observe(chartContainer.value)
  }
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  chartInstance?.dispose()
})

watch(() => props.entries, () => {
  updateChart()
}, { deep: true })

function updateChart() {
  if (!chartInstance) return

  const data = props.entries
    .filter(entry => entry.profit_loss_percent !== null)
    .map(entry => ({
      name: entry.symbol,
      value: [
        entry.market_value ?? 0,
        entry.profit_loss_percent ?? 0,
        entry.profit_loss ?? 0,
      ],
      itemStyle: {
        color: getProfitLossColor(entry.profit_loss_percent ?? 0),
      },
    }))

  const option: echarts.EChartsOption = {
    tooltip: {
      formatter: (params: any) => {
        const entry = props.entries.find(e => e.symbol === params.name)
        if (!entry) return ''
        return `
          <strong>${entry.symbol}</strong><br/>
          평가금액: $${entry.market_value?.toFixed(2) ?? '-'}<br/>
          손익: $${entry.profit_loss?.toFixed(2) ?? '-'}<br/>
          수익률: ${entry.profit_loss_percent?.toFixed(2) ?? '-'}%
        `
      },
    },
    series: [
      {
        type: 'treemap',
        data,
        width: '100%',
        height: '100%',
        roam: false,
        label: {
          show: true,
          formatter: (params: any) => {
            const entry = props.entries.find(e => e.symbol === params.name)
            if (!entry) return ''
            const percent = entry.profit_loss_percent?.toFixed(2) ?? '0.00'
            const sign = (entry.profit_loss_percent ?? 0) >= 0 ? '+' : ''
            return `${params.name}\n${sign}${percent}%`
          },
          fontSize: 14,
          fontWeight: 'bold',
        },
        upperLabel: {
          show: false,
        },
        itemStyle: {
          borderColor: '#fff',
          borderWidth: 2,
          gapWidth: 2,
        },
        levels: [
          {
            itemStyle: {
              borderWidth: 0,
              gapWidth: 5,
            },
          },
          {
            itemStyle: {
              gapWidth: 1,
            },
          },
        ],
      },
    ],
  }

  chartInstance.setOption(option)
}

function getProfitLossColor(percent: number): string {
  // Strong profit/loss: saturated colors
  if (percent >= 10) return '#22c55e'   // Strong profit (dark green)
  if (percent <= -10) return '#dc2626'  // Large loss (dark red)
  
  // Near zero: darker colors (closer to black)
  if (percent >= -1 && percent <= 1) {
    // -1% to +1%: very dark gray to black gradient
    const intensity = Math.abs(percent)  // 0 to 1
    const grayValue = Math.round(31 + (48 - 31) * intensity)  // 31 (#1f) to 48 (#30)
    const hex = grayValue.toString(16).padStart(2, '0')
    return `#${hex}${hex}${hex}`
  }
  
  // Moderate profit: green gradient (1% to 10%)
  if (percent > 1) {
    // Interpolate from dark gray (#374151) to light green (#86efac)
    const ratio = (percent - 1) / 9  // 0 to 1
    if (ratio < 0.5) {
      // 1% to 5.5%: dark gray to medium green
      const t = ratio * 2
      return interpolateColor('#374151', '#4ade80', t)
    } else {
      // 5.5% to 10%: medium green to light green
      const t = (ratio - 0.5) * 2
      return interpolateColor('#4ade80', '#86efac', t)
    }
  }
  
  // Moderate loss: red gradient (-1% to -10%)
  if (percent < -1) {
    // Interpolate from dark gray (#374151) to light red (#fca5a5)
    const ratio = (Math.abs(percent) - 1) / 9  // 0 to 1
    if (ratio < 0.5) {
      // -1% to -5.5%: dark gray to medium red
      const t = ratio * 2
      return interpolateColor('#374151', '#f87171', t)
    } else {
      // -5.5% to -10%: medium red to light red
      const t = (ratio - 0.5) * 2
      return interpolateColor('#f87171', '#fca5a5', t)
    }
  }
  
  return '#1f2937'  // Fallback
}

function interpolateColor(color1: string, color2: string, ratio: number): string {
  const r1 = parseInt(color1.slice(1, 3), 16)
  const g1 = parseInt(color1.slice(3, 5), 16)
  const b1 = parseInt(color1.slice(5, 7), 16)
  
  const r2 = parseInt(color2.slice(1, 3), 16)
  const g2 = parseInt(color2.slice(3, 5), 16)
  const b2 = parseInt(color2.slice(5, 7), 16)
  
  const r = Math.round(r1 + (r2 - r1) * ratio)
  const g = Math.round(g1 + (g2 - g1) * ratio)
  const b = Math.round(b1 + (b2 - b1) * ratio)
  
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`
}
</script>

<style scoped>
.portfolio-heatmap {
  width: 100%;
  height: 100%;
  min-height: 230px;
}

.chart-container {
  width: 100%;
  height: 100%;
  min-height: 230px;
}
</style>
