<template>
  <div class="result-viewer">
    <div v-if="loading" class="loading">检测中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="result" class="result-container">
      <div class="result-stats">
        <span class="stat">检测到 <strong>{{ result.count }}</strong> 个草莓</span>
        <span class="stat">平均置信度 <strong>{{ (result.avg_confidence * 100).toFixed(1) }}%</strong></span>
        <span class="stat">推理后端 <strong>{{ result.backend === 'local' ? '本地' : 'Atlas 200 DK' }}</strong></span>
      </div>
      <div class="result-image-wrapper">
        <canvas ref="canvas" class="result-canvas"></canvas>
      </div>
      <div class="detection-list">
        <div v-for="(d, i) in result.detections" :key="i" class="detection-item">
          #{{ i + 1 }} — 置信度 {{ (d.score * 100).toFixed(0) }}%
          <span class="bbox">[{{ d.bbox[0] }}, {{ d.bbox[1] }}, {{ d.bbox[2] }}, {{ d.bbox[3] }}]</span>
        </div>
      </div>
    </div>
    <div v-else class="empty">等待上传图片进行检测</div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({ result: Object, loading: Boolean, error: String, imageUrl: String })
const canvas = ref(null)

watch(() => props.result, async (val) => {
  if (!val) return
  await nextTick()
  if (!canvas.value) return
  drawDetections(val.detections, props.imageUrl || val.image_url)
})

function drawDetections(detections, imageUrl) {
  const c = canvas.value
  if (!c) return
  const ctx = c.getContext('2d')
  const img = new Image()
  img.src = imageUrl || ''
  img.onload = () => {
    c.width = img.width; c.height = img.height
    ctx.drawImage(img, 0, 0)
    const colors = ['#e53935', '#43a047', '#1e88e5', '#fb8c00', '#8e24aa']
    detections.forEach((d, i) => {
      const [x1, y1, x2, y2] = d.bbox
      const color = colors[i % colors.length]
      ctx.strokeStyle = color; ctx.lineWidth = 3
      ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)
      const label = `Strawberry ${(d.score * 100).toFixed(0)}%`
      ctx.fillStyle = color; ctx.font = '14px sans-serif'
      const tw = ctx.measureText(label).width
      ctx.fillRect(x1, y1 - 22, tw + 10, 22)
      ctx.fillStyle = '#fff'; ctx.fillText(label, x1 + 5, y1 - 6)
    })
  }
  img.onerror = () => {
    console.error('结果图片加载失败:', imageUrl)
    ctx.fillStyle = '#f5f5f5'
    ctx.fillRect(0, 0, c.width || 640, c.height || 480)
    ctx.fillStyle = '#999'
    ctx.font = '16px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('图片加载失败', (c.width || 640) / 2, (c.height || 480) / 2)
  }
}
</script>

<style scoped>
.result-viewer { margin-top: 20px; }
.loading, .error, .empty { padding: 40px; text-align: center; color: #888; }
.error { color: #e53935; }
.result-stats { display: flex; gap: 20px; margin-bottom: 12px; flex-wrap: wrap; }
.stat { font-size: 15px; color: #555; }
.result-image-wrapper { border: 1px solid #ddd; border-radius: 8px; overflow: auto; background: #fafafa; }
.result-canvas { width: 100%; display: block; }
.detection-list { margin-top: 12px; display: flex; flex-wrap: wrap; gap: 8px; }
.detection-item {
  background: #fff3e0; padding: 4px 12px; border-radius: 16px; font-size: 13px; color: #e65100;
}
.bbox { font-family: monospace; font-size: 12px; color: #888; }
</style>
