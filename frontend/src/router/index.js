import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import { getToken, getStoredUser } from '../services/auth'
import CopilotView from '../views/CopilotView.vue'
import DashboardView from '../views/DashboardView.vue'
import LoginView from '../views/LoginView.vue'
import LegalView from '../views/LegalView.vue'
import AccountRecoveryView from '../views/AccountRecoveryView.vue'
import OtherAppliancesView from '../views/OtherAppliancesView.vue'
import SettingsView from '../views/SettingsView.vue'
import PricingView from '../views/PricingView.vue'

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
      path: '/account-recovery',
      name: 'account-recovery',
      component: AccountRecoveryView,
      meta: { public: true }
    },
    {
      path: '/reset-password',
      redirect: (to) => ({ path: '/account-recovery', query: to.query })
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
        { path: 'appliances', name: 'appliances', component: OtherAppliancesView },
        { path: 'netscalers', redirect: (to) => ({ path: '/appliances', query: { ...to.query, tab: to.query.tab || 'inventory' } }) },
        { path: 'other-appliances', redirect: '/appliances' },
        { path: 'ssl-csr', redirect: { path: '/appliances', query: { tab: 'ssl' } } },
        { path: 'ai-providers', redirect: { path: '/settings', query: { section: 'ai-providers' } } },
        { path: 'next-gen-api', redirect: { path: '/settings', query: { section: 'nextgen' } } },
        { path: 'users', redirect: { path: '/settings', query: { section: 'users' } } },
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
