<template>
  <div class="app-shell flex min-h-screen">
    <aside class="sidebar-panel flex flex-column">
      <NetScalerLogo />

      <nav class="sidebar-nav flex-1 flex flex-column align-items-center py-5">
        <RouterLink
          v-for="item in mainNavItems"
          :key="item.path"
          v-tooltip.right="item.label"
          :to="item.path"
          class="nav-btn"
          :class="{ 'nav-btn-active': isActive(item.path) }"
        >
          <i :class="item.icon" />
        </RouterLink>
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
        <Menu ref="userMenu" :model="userMenuItems" popup />
      </div>
    </aside>

    <main class="main-content flex-1 flex flex-column min-h-screen overflow-auto">
      <router-view v-slot="{ Component, route }">
        <Transition name="page-fade" mode="out-in">
          <component :is="Component" :key="route.path" />
        </Transition>
      </router-view>

      <footer class="app-legal">
        <span class="app-legal-copy">© {{ currentYear }} Nexxus Tech</span>
        <nav class="app-legal-links">
          <RouterLink to="/legal/privacy">Privacy Policy</RouterLink>
          <RouterLink to="/legal/terms">Terms of Service</RouterLink>
          <RouterLink to="/legal/eula">EULA</RouterLink>
          <RouterLink to="/legal/acceptable-use">Acceptable Use</RouterLink>
        </nav>
      </footer>
    </main>

    <ConfirmDialog />
    <Toast position="top-right" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Avatar from 'primevue/avatar'
import ConfirmDialog from 'primevue/confirmdialog'
import Menu from 'primevue/menu'
import Toast from 'primevue/toast'
import NetScalerLogo from '../components/NetScalerLogo.vue'
import api from '../services/api'
import { clearAuth, getStoredUser } from '../services/auth'
import { getTheme, toggleTheme } from '../services/theme'

const route = useRoute()
const router = useRouter()
const userMenu = ref()
const currentUser = ref(getStoredUser())
const theme = ref(getTheme())
const currentYear = new Date().getFullYear()

function onToggleTheme() {
  theme.value = toggleTheme()
}

const mainNavItems = computed(() => {
  const items = [
    { label: 'Dashboard', path: '/', icon: 'pi pi-home' },
    { label: 'JPilot', path: '/copilot', icon: 'pi pi-comments' },
    { label: 'NetScalers', path: '/netscalers', icon: 'pi pi-server' },
    { label: 'SSL Certificates', path: '/ssl-csr', icon: 'pi pi-shield' },
    { label: 'AI Providers', path: '/ai-providers', icon: 'pi pi-sparkles' },
    { label: 'Next-Gen API', path: '/next-gen-api', icon: 'pi pi-code' }
  ]
  if (currentUser.value?.role === 'admin') {
    items.push({ label: 'Users', path: '/users', icon: 'pi pi-users' })
  }
  return items
})

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
  }
})

function isActive(path) {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}
</script>

<style scoped>
.app-shell {
  gap: var(--app-shell-gap);
  padding: 1.5rem;
  background: var(--p-surface-0);
}

:global(.app-dark) .app-shell {
  background: var(--p-surface-950);
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

:global(html.app-dark) .nav-btn:hover:not(.nav-btn-active) {
  background: var(--p-surface-700);
  color: var(--p-text-color);
  border-color: var(--p-content-border-color);
}

:global(html.app-dark) .nav-btn-active {
  background: #f1f5f9;
  color: #1e293b;
  border-color: var(--p-content-border-color);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
}

:global(html.app-dark) .nav-btn-active i {
  color: #1e293b;
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
  padding: 0 0.5rem 2rem;
  gap: 2rem;
}

.app-legal {
  margin-top: auto;
  padding: 1.25rem 1rem 0.25rem;
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

.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
