<template>
  <div
    class="uploader"
    :class="{ 'is-dragover': dragging }"
    @dragover.prevent="dragging = true"
    @dragleave.prevent="dragging = false"
    @drop.prevent="handleDrop"
  >
    <input type="file" accept="image/*" ref="fileInput" @change="handleChange" hidden />
    <div v-if="!preview" class="uploader-placeholder" @click="$refs.fileInput.click()">
      <div class="upload-icon">📷</div>
      <p>拖拽图片到此处，或点击选择</p>
      <p class="upload-hint">支持 JPG / PNG / BMP</p>
    </div>
    <div v-else class="uploader-preview">
      <img :src="preview" alt="preview" />
      <div class="uploader-actions">
        <button class="btn btn-secondary" @click="remove">重新选择</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['file-selected', 'file-removed'])
const dragging = ref(false)
const preview = ref(null)
const fileInput = ref(null)
const currentFile = ref(null)

function handleDrop(e) {
  dragging.value = false
  const file = e.dataTransfer.files[0]
  if (file && file.type.startsWith('image/')) selectFile(file)
}

function handleChange(e) {
  const file = e.target.files[0]
  if (file) selectFile(file)
}

function selectFile(file) {
  currentFile.value = file
  const reader = new FileReader()
  reader.onload = (e) => { preview.value = e.target.result; emit('file-selected', file) }
  reader.readAsDataURL(file)
}

function remove() {
  preview.value = null
  currentFile.value = null
  emit('file-removed')
}
</script>

<style scoped>
.uploader {
  border: 2px dashed #ccc; border-radius: 12px; padding: 40px;
  text-align: center; cursor: pointer; transition: all 0.2s;
  background: #fafafa; min-height: 200px; display: flex;
  align-items: center; justify-content: center;
}
.uploader.is-dragover { border-color: #e53935; background: #fff0f0; }
.uploader-placeholder { color: #888; }
.upload-icon { font-size: 48px; margin-bottom: 12px; }
.upload-hint { font-size: 13px; color: #aaa; margin-top: 8px; }
.uploader-preview { width: 100%; }
.uploader-preview img { max-width: 100%; max-height: 400px; border-radius: 8px; }
.uploader-actions { margin-top: 12px; }
</style>
