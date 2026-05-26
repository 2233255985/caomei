<template>
  <div class="chart-container">
    <h3 class="chart-title">检测趋势（近 {{ days }} 天）</h3>
    <div ref="chartRef" class="chart"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({ data: { type: Array, default: () => [] }, days: { type: Number, default: 30 } })
const chartRef = ref(null)
let chart = null

function render() {
  if (!chartRef.value || !props.data.length) return
  if (!chart) chart = echarts.init(chartRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['检测次数', '草莓数量', '平均置信度'] },
    grid: { left: 50, right: 20, bottom: 30, top: 40 },
    xAxis: { type: 'category', data: props.data.map(d => d.date.slice(5)), axisLabel: { rotate: 45 } },
    yAxis: [
      { type: 'value', name: '数量' },
      { type: 'value', name: '置信度', min: 0, max: 1, axisLabel: { formatter: v => (v * 100).toFixed(0) + '%' } },
    ],
    series: [
      { name: '检测次数', type: 'line', data: props.data.map(d => d.detections), smooth: true, itemStyle: { color: '#e53935' } },
      { name: '草莓数量', type: 'line', data: props.data.map(d => d.strawberries), smooth: true, itemStyle: { color: '#43a047' } },
      { name: '平均置信度', type: 'line', data: props.data.map(d => d.avg_confidence), yAxisIndex: 1, smooth: true, itemStyle: { color: '#1e88e5' }, lineStyle: { type: 'dashed' } },
    ],
  })
}

onMounted(render)
watch(() => props.data, render, { deep: true })
onUnmounted(() => chart?.dispose())
</script>

<style scoped>
.chart-container { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.chart-title { font-size: 16px; margin-bottom: 12px; color: #555; }
.chart { height: 350px; }
</style>
