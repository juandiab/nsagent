import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import { getToken, getStoredUser } from '../services/auth'
import {
  getLicenseForGate,
  isLicenseActivationRoute,
  licenseActivationRequired
} from '../services/licenseGate'
import { getPortalConfig } from '../services/portal'
import CopilotView from '../views/CopilotView.vue'
import CopilotBetaView from '../views/CopilotBetaView.vue'
import DashboardView from '../views/DashboardView.vue'
import LoginView from '../views/LoginView.vue'
import LegalView from '../views/LegalView.vue'
import AccountRecoveryView from '../views/AccountRecoveryView.vue'
import OtherAppliancesView from '../views/OtherAppliancesView.vue'
import SettingsView from '../views/SettingsView.vue'
import PricingView from '../views/PricingView.vue'
import CalibrationStudioView from '../views/CalibrationStudioView.vue'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/home',
      name: 'home',
      component: HomeView,
      meta: { public: true, allowAuthenticated: true }
    },
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
        { path: 'jpilot', name: 'jpilot', component: CopilotView },
        { path: 'jpilot/beta', name: 'jpilot-beta', component: CopilotBetaView },
        { path: 'copilot', redirect: '/jpilot' },
        { path: 'copilot/beta', redirect: '/jpilot/beta' },
        { path: 'appliances', name: 'appliances', component: OtherAppliancesView },
        { path: 'netscalers', redirect: (to) => ({ path: '/appliances', query: { ...to.query, tab: to.query.tab || 'inventory' } }) },
        { path: 'other-appliances', redirect: '/appliances' },
        { path: 'ssl-csr', redirect: { path: '/appliances', query: { tab: 'ssl' } } },
        { path: 'ai-providers', redirect: { path: '/settings', query: { section: 'ai-providers' } } },
        { path: 'next-gen-api', redirect: { path: '/settings', query: { section: 'nextgen' } } },
        { path: 'users', redirect: { path: '/settings', query: { section: 'users' } } },
        { path: 'plans', name: 'plans', component: PricingView },
        { path: 'calibration-studio', name: 'calibration-studio', component: CalibrationStudioView },
        { path: 'settings', name: 'settings', component: SettingsView }
      ]
    }
  ]
})

router.beforeEach(async (to) => {
  const authenticated = Boolean(getToken())
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)
  const requiresAdmin = to.matched.some((record) => record.meta.requiresAdmin)

  if (!authenticated && (to.path === '/' || to.path === '/home')) {
    const portalConfig = await getPortalConfig()
    if (to.path === '/' && portalConfig.displayHomePage) {
      return { path: '/home' }
    }
    if (to.path === '/home' && !portalConfig.displayHomePage) {
      return { path: '/login' }
    }
  }

  if (to.meta.public && authenticated && !to.meta.allowAuthenticated) {
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

  if (requiresAuth && authenticated && !isLicenseActivationRoute(to)) {
    try {
      const license = await getLicenseForGate()
      if (licenseActivationRequired(license)) {
        return {
          path: '/settings',
          query: { section: 'license', redirect: to.fullPath }
        }
      }
    } catch {
      // If license status cannot be loaded, do not block navigation.
    }
  }

  return true
})

export default router
