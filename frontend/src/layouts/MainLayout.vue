<template>
  <div class="app-shell" :class="{ 'app-shell-beta-immersive': isImmersiveBetaChat }">
    <header v-if="!isImmersiveBetaChat" class="mobile-topbar">
      <div class="mobile-topbar-side mobile-topbar-start">
        <button
          type="button"
          class="mobile-topbar-btn mobile-topbar-menu"
          aria-label="Open menu"
          @click="mobileNavOpen = true"
        >
          <i class="pi pi-bars" />
        </button>
      </div>

      <RouterLink to="/" class="mobile-topbar-logo" @click="closeMobileNav">
        <JPilot :size="36" />
      </RouterLink>

      <div class="mobile-topbar-side mobile-topbar-end">
        <button
          type="button"
          class="mobile-topbar-btn mobile-topbar-avatar"
          :aria-label="currentUser?.username || 'Account'"
          @click="toggleUserMenu"
        >
          <Avatar :label="userInitials" shape="circle" class="user-avatar" />
        </button>
      </div>
    </header>

    <aside class="sidebar-panel desktop-sidebar flex flex-column">
      <JPilot />

      <nav class="sidebar-nav flex-1 flex flex-column align-items-center py-5">
        <template v-for="group in mainNavGroups" :key="group.id">
          <span v-if="group.label" class="sidebar-cluster-label">{{ group.label }}</span>
          <RouterLink
            v-for="item in group.items"
            :key="item.path"
            v-tooltip.right="navTooltip(item)"
            :to="item.path"
            class="nav-btn"
            :class="{
              'nav-btn-active': isActive(item),
              'nav-btn-busy': isCopilotNavItem(item) && hasActiveChatRuns,
              'nav-btn-beta': item.beta
            }"
          >
            <i :class="item.icon" />
            <span v-if="item.beta" class="nav-beta-tag">β</span>
          </RouterLink>
        </template>
      </nav>

      <div class="sidebar-footer flex flex-column align-items-center gap-3 pb-2">
        <RouterLink
          v-for="item in bottomNavItems"
          :key="item.path"
          v-tooltip.right="item.label"
          :to="item.path"
          class="nav-btn"
          :class="{ 'nav-btn-active': isActive(item.path) }"
        >
          <i :class="item.icon" />
        </RouterLink>

        <button
          v-tooltip.right="fullscreenTooltip"
          class="nav-btn"
          type="button"
          @click="onToggleFullscreen"
        >
          <i :class="fullscreenIcon" />
        </button>

        <button
          v-tooltip.right="theme === 'dark' ? 'Switch to light' : 'Switch to dark'"
          class="nav-btn"
          type="button"
          @click="onToggleTheme"
        >
          <i :class="theme === 'dark' ? 'pi pi-sun' : 'pi pi-moon'" />
        </button>

        <div class="sidebar-divider" />

        <button
          v-tooltip.right="currentUser?.username || 'Account'"
          class="user-avatar-btn"
          type="button"
          @click="toggleUserMenu"
        >
          <Avatar
            :label="userInitials"
            shape="circle"
            class="user-avatar"
          />
        </button>
      </div>
    </aside>

    <Menu ref="userMenu" :model="userMenuItems" popup />

    <Drawer
      v-model:visible="mobileNavOpen"
      position="left"
      :modal="true"
      :dismissable="true"
      :show-close-icon="false"
      class="mobile-nav-drawer"
    >
      <div class="mobile-nav">
        <div class="mobile-nav-header">
          <div class="mobile-nav-brand">
            <JPilot :size="40" />
            <span class="mobile-nav-title">JPilot</span>
          </div>
          <button
            type="button"
            class="mobile-nav-close"
            aria-label="Close menu"
            @click="closeMobileNav"
          >
            <i class="pi pi-times" />
          </button>
        </div>

        <template v-for="group in mainNavGroups" :key="`mobile-${group.id}`">
          <div v-if="group.label" class="mobile-nav-cluster-label">{{ group.label }}</div>
          <nav class="mobile-nav-section">
            <RouterLink
              v-for="item in group.items"
              :key="item.path"
              :to="item.path"
              class="mobile-nav-link"
              active-class=""
              exact-active-class=""
              :class="{
                'mobile-nav-link-active': isActive(item),
                'mobile-nav-link-busy': isCopilotNavItem(item) && hasActiveChatRuns
              }"
              @click="closeMobileNav"
            >
              <i :class="item.icon" />
              <span>{{ item.label }}</span>
              <Tag v-if="item.beta" value="Beta" severity="warn" class="mobile-nav-beta-tag" />
            </RouterLink>
          </nav>
        </template>

        <div class="mobile-nav-divider" />

        <nav class="mobile-nav-section">
          <RouterLink
            v-for="item in bottomNavItems"
            :key="item.path"
            :to="item.path"
            class="mobile-nav-link"
            active-class=""
            exact-active-class=""
            :class="{ 'mobile-nav-link-active': isActive(item.path) }"
            @click="closeMobileNav"
          >
            <i :class="item.icon" />
            <span>{{ item.label }}</span>
          </RouterLink>

          <button type="button" class="mobile-nav-link mobile-nav-action" @click="onToggleTheme">
            <i :class="theme === 'dark' ? 'pi pi-sun' : 'pi pi-moon'" />
            <span>{{ theme === 'dark' ? 'Switch to light' : 'Switch to dark' }}</span>
          </button>

          <button type="button" class="mobile-nav-link mobile-nav-action" @click="onToggleFullscreen">
            <i :class="fullscreenIcon" />
            <span>{{ fullscreenLabel }}</span>
          </button>
        </nav>
      </div>
    </Drawer>

    <main class="main-content flex-1 flex flex-column">
      <div v-if="updateBannerVisible" class="update-banner">
        <Message severity="warn" :closable="true" @close="dismissUpdateBanner">
          <span>
            JPilot <strong>{{ updateInfo.latest_display_version }}</strong> is available
            (installed {{ updateInfo.display_version }}).
            <RouterLink to="/settings?section=about" class="update-banner-link">
              View update instructions
            </RouterLink>
          </span>
        </Message>
      </div>

      <div class="main-view">
        <router-view v-slot="{ Component, route }">
          <Transition name="page-fade" mode="out-in">
            <component :is="Component" :key="route.path" class="route-page" />
          </Transition>
        </router-view>
      </div>

      <footer v-if="!isImmersiveBetaChat" class="app-legal">
        <span class="app-legal-copy app-legal-desktop">
          © {{ currentYear }}
          <a
            :href="NEXXUS_TECH.websiteUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="app-legal-brand-link"
          >Nexxus Tech</a>
        </span>
        <nav class="app-legal-links app-legal-desktop">
          <RouterLink to="/legal/privacy">Privacy Policy</RouterLink>
          <RouterLink to="/legal/terms">Terms of Service</RouterLink>
          <RouterLink to="/legal/eula">EULA</RouterLink>
          <RouterLink to="/legal/acceptable-use">Acceptable Use</RouterLink>
        </nav>
        <RouterLink to="/legal" class="app-legal-mobile">
          <span>© {{ currentYear }}</span>
          <span class="app-legal-mobile-brand">Nexxus Tech</span>
          <span class="app-legal-mobile-sep" aria-hidden="true">·</span>
          <span>Terms &amp; legal</span>
        </RouterLink>
      </footer>
    </main>

    <ConfirmDialog />
    <Toast position="top-right" />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, provide, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Avatar from 'primevue/avatar'
import ConfirmDialog from 'primevue/confirmdialog'
import Drawer from 'primevue/drawer'
import Menu from 'primevue/menu'
import Message from 'primevue/message'
import Tag from 'primevue/tag'
import Toast from 'primevue/toast'
import JPilot from '../components/JPilot.vue'
import { NEXXUS_TECH } from '../config/nexxusTech'
import api from '../services/api'
import { clearAuth, getStoredUser } from '../services/auth'
import { checkForUpdates } from '../services/system'
import { getTheme, toggleTheme } from '../services/theme'
import { hasActiveChatRuns } from '../stores/copilotChatRuns'

const DISMISS_KEY = 'jpilot_update_dismissed'
const MOBILE_NAV_BREAKPOINT = 992

const route = useRoute()
const router = useRouter()
const userMenu = ref()
const mobileNavOpen = ref(false)
const currentUser = ref(getStoredUser())
const theme = ref(getTheme())
const currentYear = new Date().getFullYear()
const updateInfo = ref(null)
const updateBannerDismissed = ref(false)
const isFullscreen = ref(false)

const fullscreenIcon = computed(() =>
  isFullscreen.value ? 'pi pi-window-minimize' : 'pi pi-window-maximize'
)

const fullscreenLabel = computed(() =>
  isFullscreen.value ? 'Exit full screen' : 'Full screen'
)

const fullscreenTooltip = computed(() => fullscreenLabel.value)

const isImmersiveBetaChat = computed(() => route.name === 'jpilot-beta')

const updateBannerVisible = computed(() =>
  Boolean(updateInfo.value?.update_available) && !updateBannerDismissed.value
)

function closeMobileNav() {
  mobileNavOpen.value = false
}

function openMobileNav() {
  mobileNavOpen.value = true
}

provide('openMobileNav', openMobileNav)

function isUpdateDismissed(version) {
  try {
    return sessionStorage.getItem(DISMISS_KEY) === version
  } catch {
    return false
  }
}

function dismissUpdateBanner() {
  updateBannerDismissed.value = true
  try {
    sessionStorage.setItem(DISMISS_KEY, updateInfo.value?.latest_display_version || '1')
  } catch {
    // Ignore storage failures.
  }
}

async function loadUpdateStatus(force = false) {
  try {
    const info = await checkForUpdates(force)
    updateInfo.value = info
    updateBannerDismissed.value = isUpdateDismissed(info.latest_display_version)
  } catch {
    updateInfo.value = null
  }
}

function onUpdateAvailableEvent(event) {
  updateInfo.value = event.detail
  updateBannerDismissed.value = isUpdateDismissed(event.detail?.latest_display_version)
}

function onToggleTheme() {
  theme.value = toggleTheme()
}

function syncFullscreenState() {
  isFullscreen.value = Boolean(document.fullscreenElement)
}

async function onToggleFullscreen() {
  closeMobileNav()
  try {
    if (document.fullscreenElement) {
      await document.exitFullscreen()
    } else {
      await document.documentElement.requestFullscreen()
    }
  } catch {
    // Unsupported or denied (common on iOS Safari).
  } finally {
    syncFullscreenState()
  }
}

const mainNavGroups = [
  {
    id: 'main',
    label: '',
    items: [{ label: 'Dashboard', path: '/', icon: 'pi pi-home' }]
  },
  {
    id: 'jpilot-chat',
    label: 'JPilot Chat',
    items: [
      { label: 'Chat', path: '/jpilot', icon: 'pi pi-comments' },
      { label: 'Chat', path: '/jpilot/beta', icon: 'pi pi-sparkles', beta: true }
    ]
  },
  {
    id: 'inventory',
    label: '',
    items: [{ label: 'Appliances', path: '/appliances', icon: 'pi pi-server' }]
  }
]

const bottomNavItems = [
  { label: 'Plans', path: '/plans', icon: 'pi pi-tags' },
  { label: 'Settings', path: '/settings', icon: 'pi pi-cog' }
]

const userInitials = computed(() => {
  const name = currentUser.value?.username || 'A'
  return name.slice(0, 2).toUpperCase()
})

const userMenuItems = computed(() => [
  {
    label: currentUser.value?.displayName || currentUser.value?.username || 'Account',
    items: [
      {
        label: 'Logout',
        icon: 'pi pi-sign-out',
        command: () => logout()
      }
    ]
  }
])

function toggleUserMenu(event) {
  userMenu.value.toggle(event)
}

async function logout() {
  try {
    await api.post('/auth/logout')
  } catch {
    // Clear local session even if the API call fails.
  } finally {
    clearAuth()
    router.push('/login')
  }
}

onMounted(async () => {
  try {
    const { data } = await api.get('/auth/me')
    currentUser.value = data
  } catch {
    clearAuth()
    router.push('/login')
    return
  }
  window.addEventListener('jpilot-update-available', onUpdateAvailableEvent)
  window.addEventListener('resize', onViewportChange)
  document.addEventListener('fullscreenchange', syncFullscreenState)
  syncFullscreenState()
  await loadUpdateStatus(false)
})

onUnmounted(() => {
  window.removeEventListener('jpilot-update-available', onUpdateAvailableEvent)
  window.removeEventListener('resize', onViewportChange)
  document.removeEventListener('fullscreenchange', syncFullscreenState)
})

function onViewportChange() {
  if (window.innerWidth >= MOBILE_NAV_BREAKPOINT) {
    closeMobileNav()
  }
}

watch(
  () => route.path,
  () => {
    closeMobileNav()
  }
)

function isCopilotNavItem(item) {
  return item.path === '/jpilot' || item.path === '/jpilot/beta'
}

function navTooltip(item) {
  return item.beta ? `${item.label} (Beta)` : item.label
}

function isActive(item) {
  const path = item.path
  if (path === '/') {
    return route.path === '/'
  }
  if (item.beta || path === '/jpilot') {
    return route.path === path
  }
  return route.path.startsWith(path)
}
</script>

<style scoped>
.app-shell {
  display: flex;
  gap: var(--app-shell-gap);
  padding: 1.5rem;
  min-height: 100vh;
  align-items: flex-start;
  background: var(--p-surface-0);
}

:global(.app-dark) .app-shell {
  background: var(--p-surface-950);
}

.mobile-topbar {
  display: none;
}

.sidebar-panel {
  width: var(--sidebar-width);
  flex-shrink: 0;
  padding: 1.25rem 0.75rem;
  background: var(--p-surface-50);
  border: 1px solid var(--p-content-border-color);
  border-radius: 1rem;
  position: sticky;
  top: 1.5rem;
  height: calc(100vh - 3rem);
}

:global(.app-dark) .sidebar-panel {
  background: var(--p-surface-900);
}

.sidebar-nav {
  gap: 0.75rem;
}

.sidebar-cluster-label {
  width: 100%;
  margin: 0.35rem 0 0.15rem;
  padding: 0 0.15rem;
  font-size: 0.5625rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  text-align: center;
  color: var(--p-text-muted-color);
  line-height: 1.2;
}

.nav-btn-beta {
  position: relative;
}

.nav-beta-tag {
  position: absolute;
  right: 0.1rem;
  bottom: 0.1rem;
  font-size: 0.5rem;
  font-weight: 800;
  line-height: 1;
  color: var(--p-orange-500);
}

.sidebar-footer {
  margin-top: auto;
}

.sidebar-divider {
  width: 100%;
  height: 1px;
  background: var(--p-content-border-color);
  margin: 0.5rem 0;
}

.nav-btn {
  width: 2.5rem;
  height: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.625rem;
  border: 1px solid transparent;
  background: transparent;
  color: var(--p-text-muted-color);
  text-decoration: none;
  transition: all 0.2s ease;
  cursor: pointer;
}

.nav-btn i {
  font-size: 1.125rem;
  line-height: 1;
}

.nav-btn:hover {
  background: var(--p-surface-100);
  color: var(--p-text-color);
  border-color: var(--p-content-border-color);
}

.nav-btn-active {
  background: var(--p-surface-100);
  color: var(--p-text-color);
  border-color: var(--p-content-border-color);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.nav-btn-busy {
  position: relative;
}

.nav-btn-busy::after {
  content: '';
  position: absolute;
  top: 0.35rem;
  right: 0.35rem;
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 50%;
  background: var(--p-primary-color);
  box-shadow: 0 0 0 2px var(--p-surface-0);
  animation: nav-busy-pulse 1.4s ease-in-out infinite;
}

@keyframes nav-busy-pulse {
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.55;
    transform: scale(0.85);
  }
}

.user-avatar-btn {
  border: none;
  background: transparent;
  padding: 0;
  cursor: pointer;
}

.user-avatar {
  width: 2.5rem !important;
  height: 2.5rem !important;
  background: var(--p-primary-100) !important;
  color: var(--p-primary-700) !important;
  font-size: 0.75rem !important;
  font-weight: 700 !important;
}

:global(.app-dark) .user-avatar {
  background: var(--p-primary-900) !important;
  color: var(--p-primary-200) !important;
}

.main-content {
  height: calc(100vh - 3rem);
  min-height: calc(100vh - 3rem);
  max-height: calc(100vh - 3rem);
  padding: 0 0.5rem 0;
  gap: 0.75rem;
  overflow: hidden;
}

.main-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: auto;
}

.main-view :deep(.route-page) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.update-banner {
  padding-top: 0.25rem;
}

.update-banner-link {
  margin-left: 0.35rem;
  color: inherit;
  font-weight: 600;
  text-decoration: underline;
}

.app-legal {
  flex-shrink: 0;
  margin-top: auto;
  padding: 0.75rem 1rem 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  border-top: 1px solid var(--p-content-border-color);
  font-size: 0.8125rem;
  color: var(--p-text-muted-color);
}

.app-legal-links {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.app-legal-links a {
  color: var(--p-text-muted-color);
  text-decoration: none;
}

.app-legal-links a:hover {
  color: var(--p-primary-color);
}

.app-legal-brand-link {
  color: var(--p-text-muted-color);
  font-weight: 600;
  text-decoration: none;
}

.app-legal-brand-link:hover {
  color: var(--p-primary-color);
  text-decoration: underline;
}

.app-legal-mobile {
  display: none;
}

.app-legal-mobile-sep {
  opacity: 0.55;
}

.mobile-nav {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-height: 100%;
}

.mobile-nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.mobile-nav-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
}

.mobile-nav-title {
  font-size: 1.125rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--p-text-color);
}

.mobile-nav-close {
  width: 2.25rem;
  height: 2.25rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--p-content-border-color);
  border-radius: 999px;
  background: transparent;
  color: var(--p-text-muted-color);
  cursor: pointer;
}

.mobile-nav-close:hover {
  background: var(--p-surface-100);
  color: var(--p-text-color);
}

.mobile-nav-cluster-label {
  margin: 0.5rem 0.875rem 0.15rem;
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--p-text-muted-color);
}

.mobile-nav-section {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.mobile-nav-beta-tag {
  margin-left: auto;
}

.mobile-nav-divider {
  height: 1px;
  background: var(--p-content-border-color);
  margin: 0.35rem 0;
}

.mobile-nav-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 0.875rem;
  border-radius: 0.75rem;
  border: 1px solid transparent;
  background: transparent;
  color: var(--p-text-color);
  text-decoration: none;
  font-size: 0.9375rem;
  font-weight: 500;
  cursor: pointer;
  width: 100%;
  text-align: left;
}

.mobile-nav-link i {
  font-size: 1.125rem;
  color: var(--p-text-muted-color);
}

.mobile-nav-link:hover {
  background: var(--p-surface-100);
  border-color: var(--p-content-border-color);
}

.mobile-nav-link-active,
.mobile-nav-link.router-link-active {
  background: var(--p-surface-100);
  border-color: var(--p-content-border-color);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.mobile-nav-link-busy {
  position: relative;
}

.mobile-nav-link-busy::after {
  content: '';
  position: absolute;
  top: 0.65rem;
  right: 0.75rem;
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 50%;
  background: var(--p-primary-color);
}

.mobile-nav-action {
  font-family: inherit;
}

:global(.p-drawer.mobile-nav-drawer) {
  width: min(18rem, 100vw);
}

:global(.p-drawer.mobile-nav-drawer .p-drawer-content) {
  padding: 1rem;
  padding-bottom: calc(1rem + env(safe-area-inset-bottom, 0px));
}

@media (max-width: 991px) {
  .app-shell {
    flex-direction: column;
    gap: 0;
    padding: 0;
    width: 100%;
    max-width: 100vw;
    min-height: 100dvh;
    height: 100dvh;
    max-height: 100dvh;
    overflow: hidden;
  }

  .mobile-topbar {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 0.75rem;
    flex-shrink: 0;
    width: 100%;
    box-sizing: border-box;
    min-height: calc(var(--mobile-topbar-height, 3.75rem) + env(safe-area-inset-top, 0px));
    padding:
      calc(env(safe-area-inset-top, 0px) + 0.5rem)
      max(0.875rem, env(safe-area-inset-right, 0px))
      0.5rem
      max(0.875rem, env(safe-area-inset-left, 0px));
    background: var(--p-surface-0);
    border-bottom: 1px solid var(--p-content-border-color);
    z-index: 30;
  }

  .mobile-topbar-side {
    display: flex;
    align-items: center;
    min-width: 2.5rem;
  }

  .mobile-topbar-start {
    justify-self: start;
  }

  .mobile-topbar-end {
    justify-self: end;
    justify-content: flex-end;
  }

  .mobile-topbar-btn {
    width: 2.5rem;
    height: 2.5rem;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border: none;
    border-radius: 0.625rem;
    background: transparent;
    color: var(--p-text-color);
    cursor: pointer;
    flex-shrink: 0;
  }

  .mobile-topbar-btn i {
    color: inherit;
    font-size: 1.125rem;
    line-height: 1;
  }

  .mobile-topbar-menu {
    border: 1px solid var(--p-content-border-color);
    background: var(--p-content-background);
  }

  .mobile-topbar-btn:hover {
    background: var(--p-surface-100);
  }

  .mobile-topbar-logo {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    text-decoration: none;
    justify-self: center;
  }

  .mobile-topbar-avatar {
    padding: 0;
  }

  .desktop-sidebar {
    display: none !important;
  }

  .main-content {
    flex: 1;
    width: 100%;
    min-width: 0;
    min-height: 0;
    height: auto;
    max-height: none;
    padding: 0.75rem;
    padding-bottom: calc(0.75rem + env(safe-area-inset-bottom, 0px));
    box-sizing: border-box;
  }

  .app-shell-beta-immersive {
    height: 100dvh;
    max-height: 100dvh;
  }

  .app-shell-beta-immersive .main-content {
    padding: 0;
    padding-bottom: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
  }

  .app-legal {
    justify-content: center;
    padding: 0.35rem 0.25rem;
    padding-bottom: calc(0.35rem + env(safe-area-inset-bottom, 0px));
    border-top: 0;
  }

  .app-legal-desktop {
    display: none;
  }

  .app-legal-mobile {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    color: var(--p-text-muted-color);
    font-size: 0.75rem;
    line-height: 1.3;
    text-decoration: none;
    white-space: nowrap;
  }

  .app-legal-mobile:hover {
    color: var(--p-primary-color);
  }

  .app-legal-mobile-brand {
    font-weight: 600;
  }

  :global(.p-drawer.mobile-nav-drawer) {
    width: 100vw !important;
    max-width: 100vw;
    height: 100%;
    border-radius: 0;
    padding-top: env(safe-area-inset-top, 0px);
  }
}
</style>
