<template>
  <div class="stats-cards">
    <div class="card">
      <div class="card-label">总检测次数</div>
      <div class="card-value">{{ data.total_detections }}</div>
    </div>
    <div class="card">
      <div class="card-label">今日检测</div>
      <div class="card-value">{{ data.today_detections }}</div>
    </div>
    <div class="card">
      <div class="card-label">平均置信度</div>
      <div class="card-value">{{ (data.avg_confidence * 100).toFixed(1) }}%</div>
    </div>
    <div class="card">
      <div class="card-label">检测到草莓总数</div>
      <div class="card-value">{{ data.total_strawberries }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({ data: { type: Object, default: () => ({}) } })
</script>

<style scoped>
.stats-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }
.card { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.card-label { font-size: 14px; color: #888; margin-bottom: 8px; }
.card-value { font-size: 32px; font-weight: 700; color: #e53935; }
</style>
