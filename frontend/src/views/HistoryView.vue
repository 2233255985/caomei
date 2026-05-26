<template>
  <div class="history-page">
    <div class="page-header">
      <h1>历史记录</h1>
      <p>查看和管理所有草莓检测记录</p>
    </div>

    <!-- 详情弹窗 -->
    <div v-if="detailRecord" class="modal-overlay" @click.self="detailRecord = null">
      <div class="modal">
        <h3>检测详情 #{{ detailRecord.id }}</h3>
        <div class="img-tabs" v-if="detailRecord.annotated_url">
          <button :class="['img-tab', { active: showAnnotated === false }]" @click="showAnnotated = false">原图</button>
          <button :class="['img-tab', { active: showAnnotated === true }]" @click="showAnnotated = true">标注图</button>
        </div>
        <img :src="showAnnotated && detailRecord.annotated_url ? detailRecord.annotated_url : detailRecord.image_url"
             class="detail-img" @error="onImgError" />
        <div class="detail-info">
          <p>草莓数: {{ detailRecord.count }} | 平均置信度: {{ (detailRecord.avg_confidence * 100).toFixed(1) }}%
          | 后端: {{ detailRecord.backend === 'local' ? '本地' : 'Atlas' }}
          | 时间: {{ detailRecord.created_at?.slice(0, 19) }}</p>
          <div v-for="(d, i) in detailRecord.result_json" :key="i" class="detail-item">
            #{{ i + 1 }} 置信度 {{ (d.score * 100).toFixed(0) }}% 框: [{{ d.bbox.join(', ') }}]
          </div>
        </div>
        <button class="btn btn-secondary" @click="detailRecord = null">关闭</button>
      </div>
    </div>

    <!-- 表格 -->
    <HistoryTable :items="records" @view-detail="viewDetail" @delete="confirmDelete" />

    <!-- 分页 -->
    <div v-if="totalPages > 1" class="pagination">
      <button :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
      <span>第 {{ page }} / {{ totalPages }} 页</span>
      <button :disabled="page >= totalPages" @click="goPage(page + 1)">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import HistoryTable from '../components/HistoryTable.vue'
import { getHistory, getHistoryDetail, deleteHistory } from '../api'

const records = ref([])
const page = ref(1)
const totalPages = ref(1)
const detailRecord = ref(null)
const showAnnotated = ref(false)

async function load() {
  try {
    const data = await getHistory(page.value)
    records.value = data.items
    totalPages.value = data.pages
  } catch (e) { console.error(e) }
}

async function viewDetail(item) {
  showAnnotated.value = false
  try {
    detailRecord.value = await getHistoryDetail(item.id)
  } catch (e) { console.error(e) }
}

function onImgError(e) {
  if (showAnnotated.value) {
    showAnnotated.value = false
  }
}

async function confirmDelete(id) {
  if (!confirm('确认删除此记录？')) return
  try {
    await deleteHistory(id)
    await load()
  } catch (e) { console.error(e) }
}

function goPage(p) { page.value = p; load() }

onMounted(load)
</script>

<style scoped>
.page-header { margin-bottom: 20px; }
.page-header h1 { font-size: 24px; color: #333; }
.page-header p { color: #888; margin-top: 4px; }
.pagination { display: flex; align-items: center; justify-content: center; gap: 16px; margin-top: 20px; }
.pagination button { padding: 6px 16px; border: 1px solid #ddd; border-radius: 4px; background: #fff; cursor: pointer; }
.pagination button:disabled { opacity: 0.4; cursor: default; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #fff; border-radius: 12px; padding: 24px; max-width: 600px; width: 90%; max-height: 80vh; overflow-y: auto; }
.modal h3 { margin-bottom: 12px; }
.detail-img { width: 100%; border-radius: 8px; margin-bottom: 12px; }
.detail-info { margin-bottom: 12px; font-size: 14px; }
.detail-item { padding: 4px 0; }
.img-tabs { display: flex; gap: 8px; margin-bottom: 12px; }
.img-tab {
  padding: 4px 16px; border: 1px solid #ddd; border-radius: 4px;
  background: #fff; cursor: pointer; font-size: 13px; color: #666;
}
.img-tab.active { border-color: #e53935; background: #fff8f8; color: #e53935; font-weight: 600; }
</style>
