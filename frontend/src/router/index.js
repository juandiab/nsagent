import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import { getToken } from '../services/auth'
import CopilotView from '../views/CopilotView.vue'
import DashboardView from '../views/DashboardView.vue'
import LoginView from '../views/LoginView.vue'
import NetScalersView from '../views/NetScalersView.vue'
import AIProvidersView from '../views/AIProvidersView.vue'
import NextGenApiView from '../views/NextGenApiView.vue'
import SettingsView from '../views/SettingsView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { public: true }
    },
    {
      path: '/',
      component: MainLayout,
      meta: { requiresAuth: true },
      children: [
        { path: '', name: 'dashboard', component: DashboardView },
        { path: 'copilot', name: 'copilot', component: CopilotView },
        { path: 'netscalers', name: 'netscalers', component: NetScalersView },
        { path: 'ai-providers', name: 'ai-providers', component: AIProvidersView },
        { path: 'next-gen-api', name: 'next-gen-api', component: NextGenApiView },
        { path: 'settings', name: 'settings', component: SettingsView }
      ]
    }
  ]
})

router.beforeEach((to) => {
  const authenticated = Boolean(getToken())

  if (to.meta.public && authenticated) {
    return { path: '/' }
  }

  if (to.meta.requiresAuth && !authenticated) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  return true
})

export default router
