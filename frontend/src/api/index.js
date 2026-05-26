import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export function detectImage(file) {
  const form = new FormData()
  form.append('image', file)
  return api.post('/detect', form).then(r => r.data)
}

export function getHistory(page = 1, perPage = 20) {
  return api.get('/detect/history', { params: { page, per_page: perPage } }).then(r => r.data)
}

export function getHistoryDetail(id) {
  return api.get(`/detect/history/${id}`).then(r => r.data)
}

export function deleteHistory(id) {
  return api.delete(`/detect/history/${id}`).then(r => r.data)
}

export function getStatsSummary() {
  return api.get('/stats/summary').then(r => r.data)
}

export function getStatsTrend(days = 30) {
  return api.get('/stats/trend', { params: { days } }).then(r => r.data)
}

export function getStatsMaturity() {
  return api.get('/stats/maturity').then(r => r.data)
}

export function getBackend() {
  return api.get('/settings/backend').then(r => r.data)
}

export function setBackend(backend) {
  return api.post('/settings/backend', { backend }).then(r => r.data)
}

export function getModelPath() {
  return api.get('/settings/model-path').then(r => r.data)
}

export function setModelPath(modelPath) {
  return api.post('/settings/model-path', { model_path: modelPath }).then(r => r.data)
}

export function detectVideo(file) {
  const form = new FormData()
  form.append('video', file)
  return api.post('/detect/video', form, { timeout: 60000 }).then(r => r.data)
}

export function getVideoProgress(taskId) {
  return api.get(`/detect/video/progress/${taskId}`).then(r => r.data)
}

export function detectBatch(files) {
  const form = new FormData()
  files.forEach(f => form.append('images', f))
  return api.post('/detect/batch', form, { timeout: 300000 }).then(r => r.data)
}
