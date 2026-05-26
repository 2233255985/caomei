<template>
  <div class="dashboard-page">
    <div class="page-header">
      <h1>数据仪表盘</h1>
      <p>草莓检测数据统计与分析</p>
    </div>
    <StatsCards :data="summary" />
    <div class="chart-grid">
      <TrendChart :data="trend" :days="30" />
      <div class="chart-container">
        <h3 class="chart-title">成熟度分布</h3>
        <div ref="pieRef" class="chart">
          <div v-if="maturityPlaceholder" class="chart-placeholder">
            <p>📊 功能预留</p>
            <p class="placeholder-hint">后续可扩展成熟度分类（青涩/半熟/成熟）</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import StatsCards from '../components/StatsCards.vue'
import TrendChart from '../components/TrendChart.vue'
import { getStatsSummary, getStatsTrend, getStatsMaturity } from '../api'

const summary = ref({ total_detections: 0, today_detections: 0, avg_confidence: 0, total_strawberries: 0 })
const trend = ref([])
const maturityPlaceholder = ref(true)
const pieRef = ref(null)
let pieChart = null

onMounted(async () => {
  try {
    const [s, t, m] = await Promise.all([getStatsSummary(), getStatsTrend(30), getStatsMaturity()])
    summary.value = s
    trend.value = t
    if (m.placeholder) {
      maturityPlaceholder.value = true
    } else if (pieRef.value && m.labels.length > 0) {
      maturityPlaceholder.value = false
      pieChart = echarts.init(pieRef.value)
      pieChart.setOption({
        tooltip: { trigger: 'item' },
        series: [{
          type: 'pie', radius: ['40%', '70%'],
          data: m.labels.map((l, i) => ({ name: l, value: m.values[i] })),
          itemStyle: { borderRadius: 6 },
          label: { show: true, formatter: '{b}: {c}' },
        }],
      })
    }
  } catch (e) { console.error('加载仪表盘数据失败', e) }
})
onUnmounted(() => pieChart?.dispose())
</script>

<style scoped>
.page-header { margin-bottom: 20px; }
.page-header h1 { font-size: 24px; color: #333; }
.page-header p { color: #888; margin-top: 4px; }
.chart-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; }
@media (max-width: 768px) { .chart-grid { grid-template-columns: 1fr; } }
.chart-container { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.chart-title { font-size: 16px; margin-bottom: 12px; color: #555; }
.chart { height: 350px; display: flex; align-items: center; justify-content: center; }
.chart-placeholder { text-align: center; color: #aaa; }
.chart-placeholder p { font-size: 16px; margin-bottom: 8px; }
.placeholder-hint { font-size: 13px; color: #ccc; }
</style>
