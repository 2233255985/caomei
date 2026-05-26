<template>
  <div class="settings-page">
    <div class="page-header">
      <h1>系统设置</h1>
      <p>配置推理后端和模型文件路径</p>
    </div>

    <div class="setting-card">
      <h3>推理后端</h3>
      <p class="setting-desc">选择草莓检测的推理引擎运行位置</p>
      <div class="radio-group">
        <label class="radio" :class="{ active: backend === 'local' }">
          <input type="radio" value="local" v-model="backend" @change="saveBackend" />
          <span class="radio-label">本地推理 (ONNX Runtime)</span>
          <span class="radio-desc">在 PC 上使用 ONNX Runtime 运行模型</span>
        </label>
        <label class="radio" :class="{ active: backend === 'atlas' }">
          <input type="radio" value="atlas" v-model="backend" @change="saveBackend" />
          <span class="radio-label">Atlas 200 DK 远程推理</span>
          <span class="radio-desc">通过 HTTP 连接开发板进行推理</span>
        </label>
      </div>
    </div>

    <div class="setting-card">
      <h3>模型文件</h3>
      <p class="setting-desc">指定本地 ONNX 模型文件路径</p>
      <div class="model-path-row">
        <input type="text" v-model="modelPath" class="path-input" placeholder="例如: D:\models\best_strawberry.onnx" />
        <button class="btn btn-secondary" @click="browseFile">选择文件</button>
        <button class="btn btn-primary" @click="saveModelPath" :disabled="!modelPath">保存</button>
      </div>
      <input type="file" ref="fileInput" accept=".onnx" @change="onFileSelected" hidden />
      <div v-if="modelExists === true" class="status status-ok">✓ 模型文件存在</div>
      <div v-if="modelExists === false" class="status status-err">✗ 文件不存在</div>
      <div v-if="modelMessage" class="setting-message">{{ modelMessage }}</div>
    </div>

    <div v-if="message" class="setting-message">{{ message }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getBackend, setBackend, getModelPath, setModelPath } from '../api'

const backend = ref('local')
const message = ref('')
const modelPath = ref('')
const modelExists = ref(null)
const modelMessage = ref('')
const fileInput = ref(null)

onMounted(async () => {
  try {
    const [b, m] = await Promise.all([getBackend(), getModelPath()])
    backend.value = b.backend
    modelPath.value = m.model_path || ''
    modelExists.value = m.exists
  } catch (e) { console.error(e) }
})

async function saveBackend() {
  try {
    const data = await setBackend(backend.value)
    message.value = data.message
    setTimeout(() => { message.value = '' }, 3000)
  } catch (e) { message.value = '保存失败'; console.error(e) }
}

function browseFile() {
  fileInput.value?.click()
}

async function onFileSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return
  // 浏览器安全限制无法获取完整路径，使用文件名提示用户手动输入
  modelMessage.value = `已选择: ${file.name}，请确认文件在服务器上的完整路径`
  setTimeout(() => { modelMessage.value = '' }, 5000)
}

async function saveModelPath() {
  if (!modelPath.value) return
  try {
    const data = await setModelPath(modelPath.value)
    modelExists.value = data.exists ?? null
    modelMessage.value = data.message
    setTimeout(() => { modelMessage.value = '' }, 3000)
  } catch (e) {
    const msg = e.response?.data?.error || '保存失败'
    modelMessage.value = msg
    modelExists.value = false
  }
}
</script>

<style scoped>
.page-header { margin-bottom: 20px; }
.page-header h1 { font-size: 24px; color: #333; }
.page-header p { color: #888; margin-top: 4px; }
.setting-card { background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 16px; }
.setting-card h3 { margin-bottom: 4px; }
.setting-desc { color: #888; font-size: 14px; margin-bottom: 16px; }
.radio-group { display: flex; flex-direction: column; gap: 12px; }
.radio {
  display: flex; flex-direction: column; padding: 16px; border: 2px solid #e0e0e0;
  border-radius: 8px; cursor: pointer; transition: all 0.2s;
}
.radio.active { border-color: #e53935; background: #fff8f8; }
.radio input { display: none; }
.radio-label { font-weight: 600; font-size: 15px; color: #333; }
.radio-desc { font-size: 13px; color: #888; margin-top: 2px; }
.setting-message { margin-top: 12px; padding: 8px 16px; background: #e8f5e9; border-radius: 6px; color: #2e7d32; font-size: 14px; }
.model-path-row { display: flex; gap: 8px; align-items: center; }
.path-input {
  flex: 1; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px;
  font-size: 14px; font-family: monospace; outline: none;
}
.path-input:focus { border-color: #e53935; }
.status { margin-top: 8px; font-size: 13px; }
.status-ok { color: #2e7d32; }
.status-err { color: #e53935; }
.btn {
  padding: 8px 16px; border: none; border-radius: 6px; font-size: 14px; cursor: pointer;
  transition: all 0.2s; white-space: nowrap;
}
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary { background: #e53935; color: #fff; }
.btn-primary:hover:not(:disabled) { background: #c62828; }
.btn-secondary { background: #e0e0e0; color: #333; }
.btn-secondary:hover { background: #bdbdbd; }
</style>
