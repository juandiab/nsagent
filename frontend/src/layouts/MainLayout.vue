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

const route = useRoute()
const router = useRouter()
const userMenu = ref()
const currentUser = ref(getStoredUser())

const mainNavItems = [
  { label: 'Dashboard', path: '/', icon: 'pi pi-home' },
  { label: 'Copilot', path: '/copilot', icon: 'pi pi-comments' },
  { label: 'NetScalers', path: '/netscalers', icon: 'pi pi-server' },
  { label: 'AI Providers', path: '/ai-providers', icon: 'pi pi-sparkles' },
  { label: 'Next-Gen API', path: '/next-gen-api', icon: 'pi pi-code' }
]

const bottomNavItems = [
  { label: 'Settings', path: '/settings', icon: 'pi pi-cog' }
]

const userInitials = computed(() => {
  const name = currentUser.value?.username || 'A'
  return name.slice(0, 2).toUpperCase()
})

const userMenuItems = computed(() => [
  {
    label: currentUser.value?.username || 'Account',
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
  background: var(--p-surface-0);
  color: var(--p-text-color);
  border-color: var(--p-content-border-color);
}

.nav-btn-active {
  background: var(--p-surface-0);
  color: var(--p-text-color);
  border-color: var(--p-content-border-color);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
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

.main-content {
  padding: 0 0.5rem 2rem;
  gap: 2rem;
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
