import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import { getToken, getStoredUser } from '../services/auth'
import CopilotView from '../views/CopilotView.vue'
import DashboardView from '../views/DashboardView.vue'
import LoginView from '../views/LoginView.vue'
import LegalView from '../views/LegalView.vue'
import ResetPasswordView from '../views/ResetPasswordView.vue'
import NetScalersView from '../views/NetScalersView.vue'
import SettingsView from '../views/SettingsView.vue'
import PricingView from '../views/PricingView.vue'
import UsersView from '../views/UsersView.vue'

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
      path: '/reset-password',
      name: 'reset-password',
      component: ResetPasswordView,
      meta: { public: true }
    },
    {
      path: '/legal/:doc?',
      name: 'legal',
      component: LegalView
    },
    {
      path: '/',
      component: MainLayout,
      meta: { requiresAuth: true },
      children: [
        { path: '', name: 'dashboard', component: DashboardView },
        { path: 'copilot', name: 'copilot', component: CopilotView },
        { path: 'netscalers', name: 'netscalers', component: NetScalersView },
        { path: 'ssl-csr', redirect: { path: '/netscalers', query: { tab: 'ssl' } } },
        { path: 'ai-providers', redirect: { path: '/settings', query: { section: 'ai-providers' } } },
        { path: 'next-gen-api', redirect: { path: '/settings', query: { section: 'nextgen' } } },
        { path: 'users', name: 'users', component: UsersView, meta: { requiresAdmin: true } },
        { path: 'plans', name: 'plans', component: PricingView },
        { path: 'settings', name: 'settings', component: SettingsView }
      ]
    }
  ]
})

router.beforeEach((to) => {
  const authenticated = Boolean(getToken())
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)
  const requiresAdmin = to.matched.some((record) => record.meta.requiresAdmin)

  if (to.meta.public && authenticated) {
    return { path: '/' }
  }

  if (requiresAuth && !authenticated) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  if (requiresAdmin && authenticated) {
    const user = getStoredUser()
    if (user?.role !== 'admin') {
      return { path: '/' }
    }
  }

  return true
})

export default router
