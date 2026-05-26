import { createRouter, createWebHistory } from 'vue-router'
import DetectView from '../views/DetectView.vue'
import DashboardView from '../views/DashboardView.vue'
import HistoryView from '../views/HistoryView.vue'
import SettingsView from '../views/SettingsView.vue'

const routes = [
  { path: '/', name: 'detect', component: DetectView },
  { path: '/dashboard', name: 'dashboard', component: DashboardView },
  { path: '/history', name: 'history', component: HistoryView },
  { path: '/settings', name: 'settings', component: SettingsView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
