<template>
  <nav class="ai-section-nav">
    <RouterLink
      v-for="item in items"
      :key="item.path"
      :to="item.path"
      class="ai-section-link"
      :class="{ 'ai-section-link-active': isActive(item.path) }"
    >
      <i :class="item.icon" />
      {{ item.label }}
    </RouterLink>
  </nav>
</template>

<script setup>
import { useRoute } from 'vue-router'

const items = [
  { label: 'AI Providers', path: '/ai-providers', icon: 'pi pi-sparkles' },
  { label: 'Next-Gen API', path: '/next-gen-api', icon: 'pi pi-code' }
]

const route = useRoute()

function isActive(path) {
  return route.path === path
}
</script>

<style scoped>
.ai-section-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
}

.ai-section-link {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.5rem 0.875rem;
  border-radius: 999px;
  border: 1px solid var(--p-content-border-color);
  background: var(--p-content-background);
  color: var(--p-text-muted-color);
  font-size: 0.875rem;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s ease;
}

.ai-section-link:hover {
  color: var(--p-text-color);
  border-color: var(--p-primary-200);
}

.ai-section-link-active {
  color: var(--p-primary-700);
  border-color: var(--p-primary-200);
  background: var(--p-primary-50);
}
</style>
