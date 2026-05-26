<template>
  <div class="detect-page">
    <div class="page-header">
      <h1>草莓检测</h1>
      <p>上传草莓图片或视频，AI 自动识别并标记检测结果</p>
    </div>

    <!-- 模式切换 Tabs -->
    <div class="mode-tabs">
      <button :class="['tab', { active: mode === 'image' }]" @click="mode = 'image'">单图检测</button>
      <button :class="['tab', { active: mode === 'video' }]" @click="mode = 'video'">视频检测</button>
      <button :class="['tab', { active: mode === 'batch' }]" @click="mode = 'batch'">批量检测</button>
    </div>

    <!-- 单图模式 -->
    <template v-if="mode === 'image'">
      <ImageUploader @file-selected="onFileSelected" @file-removed="reset" />
      <div v-if="selectedFile" class="detect-actions">
        <button class="btn btn-primary" @click="runDetect" :disabled="loading">
          {{ loading ? '检测中...' : '开始检测' }}
        </button>
      </div>
      <ResultViewer :result="result" :loading="loading" :error="error" :image-url="imageUrl" />
    </template>

    <!-- 视频模式 -->
    <template v-if="mode === 'video'">
      <div class="uploader" @click="$refs.videoInput.click()">
        <input type="file" ref="videoInput" accept="video/*" @change="onVideoSelected" hidden />
        <div v-if="!selectedVideo" class="uploader-placeholder">
          <div class="upload-icon">🎬</div>
          <p>点击选择视频文件</p>
          <p class="upload-hint">支持 MP4 / AVI / MKV</p>
        </div>
        <div v-else class="uploader-preview">
          <video :src="videoPreviewUrl" controls style="max-width:100%;max-height:400px;border-radius:8px;" />
          <div class="uploader-actions">
            <button class="btn btn-secondary" @click="resetVideo">重新选择</button>
          </div>
        </div>
      </div>
      <div v-if="selectedVideo" class="detect-actions">
        <button class="btn btn-primary" @click="runVideoDetect" :disabled="videoLoading">
          {{ videoLoading ? `处理中 ${videoProgress}%` : '开始检测' }}
        </button>
      </div>
      <div v-if="videoLoading" class="video-progress-bar">
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: videoProgress + '%' }"></div>
        </div>
        <span class="progress-text">{{ videoProgress }}%</span>
      </div>
      <div v-if="videoResult" class="video-result-card">
        <div v-if="videoResult.error" class="error">{{ videoResult.error }}</div>
        <template v-else>
          <h3>检测完成</h3>
          <p>总帧数: {{ videoResult.total_frames }} | 处理帧: {{ videoResult.processed_frames }}</p>
          <p>处理耗时: {{ videoResult.elapsed_seconds }}s ({{ videoResult.fps_processed }} fps)</p>
          <video :src="videoResult.video_url" controls style="width:100%;border-radius:8px;margin-top:12px;" />
          <a :href="videoResult.video_url" download class="btn btn-primary" style="display:inline-block;margin-top:12px;text-decoration:none;">下载标注视频</a>
        </template>
      </div>
    </template>

    <!-- 批量模式 -->
    <template v-if="mode === 'batch'">
      <div class="uploader" @click="$refs.folderInput.click()">
        <input type="file" ref="folderInput" webkitdirectory @change="onFolderSelected" hidden />
        <div v-if="!selectedFiles.length" class="uploader-placeholder">
          <div class="upload-icon">📁</div>
          <p>点击选择文件夹</p>
          <p class="upload-hint">处理文件夹内所有图片</p>
        </div>
        <div v-else class="uploader-preview">
          <p>已选择 {{ selectedFiles.length }} 张图片</p>
          <div class="uploader-actions">
            <button class="btn btn-secondary" @click="resetBatch">重新选择</button>
          </div>
        </div>
      </div>
      <div v-if="selectedFiles.length" class="detect-actions">
        <button class="btn btn-primary" @click="runBatchDetect" :disabled="batchLoading">
          {{ batchLoading ? `处理中 ${batchProgress}/${selectedFiles.length}...` : '开始批量检测' }}
        </button>
      </div>
      <div v-if="batchResults.length" class="batch-results">
        <div v-for="(item, i) in batchResults" :key="i" class="batch-item">
          <img :src="item.annotated_url || item.image_url" class="batch-thumb" @click="showBatchDetail(item)" />
          <div class="batch-info">
            <div class="batch-filename">{{ item.filename }}</div>
            <div v-if="item.error" class="batch-error">{{ item.error }}</div>
            <div v-else>{{ item.count }} 个草莓, 平均 {{ (item.avg_confidence * 100).toFixed(1) }}%</div>
          </div>
        </div>
      </div>
    </template>

    <!-- 批量详情弹窗 -->
    <div v-if="batchDetail" class="modal-overlay" @click.self="batchDetail = null">
      <div class="modal">
        <h3>{{ batchDetail.filename }}</h3>
        <div class="img-tabs">
          <button :class="['img-tab', { active: showBatchAnnotated }]" @click="showBatchAnnotated = true">标注图</button>
          <button :class="['img-tab', { active: !showBatchAnnotated }]" @click="showBatchAnnotated = false">原图</button>
        </div>
        <img :src="showBatchAnnotated && batchDetail.annotated_url ? batchDetail.annotated_url : batchDetail.image_url"
             class="detail-img" />
        <div v-if="batchDetail.count" class="detail-info">
          <p>{{ batchDetail.count }} 个草莓, 平均置信度 {{ (batchDetail.avg_confidence * 100).toFixed(1) }}%</p>
          <div v-for="(d, j) in batchDetail.detections" :key="j" class="detail-item">
            #{{ j + 1 }} 置信度 {{ (d.score * 100).toFixed(0) }}% 框: [{{ d.bbox.join(', ') }}]
          </div>
        </div>
        <button class="btn btn-secondary" @click="batchDetail = null">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import ImageUploader from '../components/ImageUploader.vue'
import ResultViewer from '../components/ResultViewer.vue'
import { detectImage, detectVideo, getVideoProgress, detectBatch } from '../api'

const mode = ref('image')

// 单图状态
const selectedFile = ref(null)
const result = ref(null)
const loading = ref(false)
const error = ref(null)
const imageUrl = ref(null)

// 视频状态
const selectedVideo = ref(null)
const videoPreviewUrl = ref(null)
const videoLoading = ref(false)
const videoProgress = ref(0)
const videoResult = ref(null)
let videoPollTimer = null

// 批量状态
const selectedFiles = ref([])
const batchLoading = ref(false)
const batchProgress = ref(0)
const batchResults = ref([])
const batchDetail = ref(null)
const showBatchAnnotated = ref(true)

// 单图方法
function onFileSelected(file) {
  selectedFile.value = file
  result.value = null
  error.value = null
  imageUrl.value = URL.createObjectURL(file)
}

function reset() {
  selectedFile.value = null
  result.value = null
  error.value = null
  if (imageUrl.value) URL.revokeObjectURL(imageUrl.value)
  imageUrl.value = null
}

async function runDetect() {
  if (!selectedFile.value) return
  loading.value = true
  error.value = null
  try {
    const data = await detectImage(selectedFile.value)
    result.value = data
    imageUrl.value = data.image_url || imageUrl.value
  } catch (e) {
    error.value = e.response?.data?.error || '检测失败，请重试'
  } finally {
    loading.value = false
  }
}

// 视频方法
function onVideoSelected(e) {
  const file = e.target.files[0]
  if (!file) return
  selectedVideo.value = file
  videoPreviewUrl.value = URL.createObjectURL(file)
  videoResult.value = null
}

function resetVideo() {
  selectedVideo.value = null
  if (videoPreviewUrl.value) URL.revokeObjectURL(videoPreviewUrl.value)
  videoPreviewUrl.value = null
  videoResult.value = null
  videoProgress.value = 0
  if (videoPollTimer) { clearInterval(videoPollTimer); videoPollTimer = null }
}

async function runVideoDetect() {
  if (!selectedVideo.value) return
  videoLoading.value = true
  videoProgress.value = 0
  videoResult.value = null
  try {
    const { task_id } = await detectVideo(selectedVideo.value)
    videoPollTimer = setInterval(async () => {
      try {
        const task = await getVideoProgress(task_id)
        if (!task) return
        videoProgress.value = task.progress || 0
        if (task.status === 'done') {
          clearInterval(videoPollTimer); videoPollTimer = null
          videoResult.value = task.result
          videoLoading.value = false
        } else if (task.status === 'error') {
          clearInterval(videoPollTimer); videoPollTimer = null
          videoResult.value = { error: task.error || '处理失败' }
          videoLoading.value = false
        }
      } catch (e) { console.error('轮询失败:', e) }
    }, 1000)
  } catch (e) {
    const msg = e.response?.data?.error || e.message || '视频检测失败'
    videoResult.value = { error: msg }
    videoLoading.value = false
  }
}

onUnmounted(() => {
  if (videoPollTimer) clearInterval(videoPollTimer)
})

// 批量方法
function onFolderSelected(e) {
  selectedFiles.value = Array.from(e.target.files || [])
  batchResults.value = []
}

function resetBatch() {
  selectedFiles.value = []
  batchResults.value = []
  batchProgress.value = 0
  batchDetail.value = null
}

async function runBatchDetect() {
  if (!selectedFiles.value.length) return
  batchLoading.value = true
  batchProgress.value = 0
  batchResults.value = []
  try {
    const data = await detectBatch(selectedFiles.value)
    batchResults.value = data.results || []
    batchProgress.value = data.total
  } catch (e) {
    batchResults.value = [{ error: e.response?.data?.error || '批量检测失败' }]
  } finally {
    batchLoading.value = false
  }
}

function showBatchDetail(item) {
  batchDetail.value = item
  showBatchAnnotated.value = !!item.annotated_url
}
</script>

<style scoped>
.page-header { margin-bottom: 20px; }
.page-header h1 { font-size: 24px; color: #333; }
.page-header p { color: #888; margin-top: 4px; }
.detect-actions { margin-top: 16px; text-align: center; }
.btn {
  padding: 10px 32px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer;
  transition: all 0.2s;
}
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary { background: #e53935; color: #fff; }
.btn-primary:hover:not(:disabled) { background: #c62828; }
.btn-secondary { background: #e0e0e0; color: #333; }
.btn-secondary:hover { background: #bdbdbd; }
.error { color: #e53935; margin-top: 12px; padding: 12px; background: #fff5f5; border-radius: 8px; }
.uploader {
  border: 2px dashed #ddd; border-radius: 12px; padding: 40px; text-align: center;
  cursor: pointer; transition: all 0.2s; background: #fafafa;
}
.uploader:hover { border-color: #e53935; background: #fff8f8; }
.uploader-placeholder { color: #888; }
.upload-icon { font-size: 48px; margin-bottom: 12px; }
.upload-hint { font-size: 13px; color: #aaa; margin-top: 8px; }
.uploader-preview { position: relative; }
.uploader-actions { margin-top: 12px; }
.mode-tabs { display: flex; gap: 8px; margin-bottom: 20px; }
.tab {
  padding: 8px 24px; border: 2px solid #e0e0e0; border-radius: 8px;
  background: #fff; cursor: pointer; font-size: 15px; color: #666;
  transition: all 0.2s;
}
.tab:hover { border-color: #e53935; color: #e53935; }
.tab.active { border-color: #e53935; background: #fff8f8; color: #e53935; font-weight: 600; }
.video-progress-bar { margin-top: 16px; display: flex; align-items: center; gap: 12px; }
.progress-track { flex: 1; height: 8px; background: #e0e0e0; border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: #e53935; border-radius: 4px; transition: width 0.3s; }
.progress-text { font-size: 14px; color: #888; min-width: 36px; }
.video-result-card {
  margin-top: 20px; padding: 20px; background: #fff; border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.video-result-card h3 { margin-bottom: 8px; }
.video-result-card p { color: #666; font-size: 14px; margin-bottom: 4px; }
.batch-results { margin-top: 20px; display: flex; flex-direction: column; gap: 8px; }
.batch-item {
  display: flex; gap: 12px; padding: 12px; background: #fff; border-radius: 8px;
  align-items: center; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.batch-thumb { width: 80px; height: 80px; object-fit: cover; border-radius: 6px; cursor: pointer; }
.batch-thumb:hover { opacity: 0.85; }
.batch-info { flex: 1; }
.batch-filename { font-weight: 600; font-size: 14px; margin-bottom: 2px; }
.batch-error { color: #e53935; font-size: 13px; }
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
