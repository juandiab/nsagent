<template>
  <nav class="landing-nav">
    <RouterLink to="/home" class="landing-nav-brand" aria-label="JPilot home">
      <img :src="logoSrc" alt="JPilot" class="landing-nav-logo" />
      <span class="landing-nav-name">JPilot</span>
    </RouterLink>

    <ul class="landing-nav-links">
      <li v-for="item in navItems" :key="item.label">
        <a v-if="item.href" :href="item.href" class="landing-nav-link">{{ item.label }}</a>
        <RouterLink v-else :to="item.to" class="landing-nav-link">{{ item.label }}</RouterLink>
      </li>
    </ul>

    <div class="landing-nav-actions">
      <button
        type="button"
        class="landing-nav-icon-btn"
        :aria-label="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'"
        @click="onToggleTheme"
      >
        <i :class="theme === 'dark' ? 'pi pi-sun' : 'pi pi-moon'" />
      </button>
      <RouterLink to="/login" class="landing-btn landing-btn-primary landing-nav-cta">
        Access
      </RouterLink>
      <button
        type="button"
        class="landing-nav-menu-btn"
        aria-label="Open menu"
        @click="mobileOpen = !mobileOpen"
      >
        <i class="pi pi-bars" />
      </button>
    </div>

    <div v-if="mobileOpen" class="landing-nav-mobile">
      <template v-for="item in navItems" :key="`mobile-${item.label}`">
        <a
          v-if="item.href"
          :href="item.href"
          class="landing-nav-mobile-link"
          @click="mobileOpen = false"
        >
          {{ item.label }}
        </a>
        <RouterLink
          v-else
          :to="item.to"
          class="landing-nav-mobile-link"
          @click="mobileOpen = false"
        >
          {{ item.label }}
        </RouterLink>
      </template>
      <RouterLink to="/login" class="landing-btn landing-btn-accent w-full" @click="mobileOpen = false">
        Access
      </RouterLink>
    </div>
  </nav>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { getTheme, toggleTheme } from '../../services/theme'

const logoSrc = '/jpilot-favicon.png'

const navItems = [
  { label: 'Features', href: '#features' },
  { label: 'Solutions', href: '#solutions' },
  { label: 'Install', href: '#install' }
]

const theme = ref(getTheme())
const mobileOpen = ref(false)

function onThemeChange(event) {
  theme.value = event.detail
}

function onToggleTheme() {
  theme.value = toggleTheme()
}

onMounted(() => {
  window.addEventListener('jpilot-theme-change', onThemeChange)
})

onUnmounted(() => {
  window.removeEventListener('jpilot-theme-change', onThemeChange)
})
</script>

<style scoped>
.landing-nav {
  position: relative;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.25rem 0;
  border-bottom: 1px dashed rgba(255, 255, 255, 0.12);
}

.landing-nav-brand {
  display: inline-flex;
  align-items: center;
  gap: 0.625rem;
  text-decoration: none;
  color: #fff;
}

.landing-nav-logo {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 50%;
  object-fit: cover;
}

.landing-nav-name {
  font-size: 1.0625rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.landing-nav-links {
  display: none;
  align-items: center;
  gap: 0.25rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.landing-nav-link {
  display: inline-flex;
  align-items: center;
  padding: 0.5rem 0.875rem;
  border-radius: 999px;
  color: rgba(255, 255, 255, 0.72);
  text-decoration: none;
  font-size: 0.9375rem;
  font-weight: 500;
  transition: background 0.2s ease, color 0.2s ease;
}

.landing-nav-link:hover,
.landing-nav-link.router-link-active {
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
}

.landing-nav-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.landing-nav-icon-btn,
.landing-nav-menu-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  cursor: pointer;
  transition: background 0.2s ease;
}

.landing-nav-icon-btn:hover,
.landing-nav-menu-btn:hover {
  background: rgba(255, 255, 255, 0.14);
}

.landing-nav-cta {
  display: none;
  min-width: 8.5rem;
}

.landing-nav-menu-btn {
  display: inline-flex;
}

.landing-nav-mobile {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  width: min(16rem, calc(100vw - 2rem));
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  padding: 0.75rem;
  border-radius: 1rem;
  background: var(--p-surface-0);
  border: 1px solid var(--p-surface-200);
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.18);
}

html.app-dark .landing-nav-mobile {
  background: var(--p-surface-900);
  border-color: var(--p-surface-700);
}

.landing-nav-mobile-link {
  display: block;
  padding: 0.625rem 0.75rem;
  border-radius: 0.625rem;
  color: var(--p-text-color);
  text-decoration: none;
  font-weight: 500;
}

.landing-nav-mobile-link:hover {
  background: var(--p-surface-100);
}

html.app-dark .landing-nav-mobile-link:hover {
  background: var(--p-surface-800);
}

@media (min-width: 960px) {
  .landing-nav-links {
    display: flex;
  }

  .landing-nav-cta {
    display: inline-flex;
  }

  .landing-nav-menu-btn {
    display: none;
  }

  .landing-nav-mobile {
    display: none;
  }
}
</style>
