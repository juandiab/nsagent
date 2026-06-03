<template>
  <div class="legal-page">
    <header class="legal-header">
      <RouterLink to="/" class="legal-brand">
        <NetScalerLogo />
        <span class="legal-brand-name">JPilot</span>
      </RouterLink>
      <RouterLink to="/login" class="legal-back">
        <i class="pi pi-arrow-left" /> Back
      </RouterLink>
    </header>

    <main class="legal-body">
      <nav class="legal-nav">
        <ul class="legal-nav-list">
          <li
            v-for="doc in docs"
            :key="doc.key"
            class="legal-nav-item"
            :class="{ 'is-active': activeDoc === doc.key }"
          >
            <RouterLink :to="`/legal/${doc.key}`" class="legal-nav-link">
              <i :class="[doc.icon, 'legal-nav-icon']" />
              <span>{{ doc.label }}</span>
            </RouterLink>
          </li>
        </ul>
      </nav>

      <article class="legal-content content-panel content-panel-padded">
        <ChatMarkdown :content="activeContent" />
      </article>
    </main>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ChatMarkdown from '../components/ChatMarkdown.vue'
import NetScalerLogo from '../components/NetScalerLogo.vue'
import privacyPolicy from '../legal/privacy-policy.md?raw'
import termsOfService from '../legal/terms-of-service.md?raw'
import eula from '../legal/eula.md?raw'
import acceptableUsePolicy from '../legal/acceptable-use-policy.md?raw'

const docs = [
  { key: 'privacy', label: 'Privacy Policy', icon: 'pi pi-shield', content: privacyPolicy },
  { key: 'terms', label: 'Terms of Service', icon: 'pi pi-file', content: termsOfService },
  { key: 'eula', label: 'EULA', icon: 'pi pi-key', content: eula },
  { key: 'acceptable-use', label: 'Acceptable Use', icon: 'pi pi-check-circle', content: acceptableUsePolicy }
]

const route = useRoute()
const router = useRouter()

const activeDoc = computed(() => {
  const requested = route.params.doc
  return docs.some((d) => d.key === requested) ? requested : 'privacy'
})

const activeContent = computed(
  () => docs.find((d) => d.key === activeDoc.value)?.content || ''
)

// Normalize unknown/empty doc params to the default page.
watch(
  () => route.params.doc,
  (doc) => {
    if (!doc || !docs.some((d) => d.key === doc)) {
      router.replace('/legal/privacy')
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.legal-page {
  min-height: 100vh;
  background: var(--p-surface-50);
  color: var(--p-text-color);
  display: flex;
  flex-direction: column;
}

.legal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--p-content-border-color);
  background: var(--p-content-background);
}

.legal-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  text-decoration: none;
  color: var(--p-text-color);
}

.legal-brand-name {
  font-weight: 700;
  font-size: 1.05rem;
}

.legal-back {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  text-decoration: none;
  color: var(--p-text-muted-color);
  font-weight: 500;
  font-size: 0.9rem;
}

.legal-back:hover {
  color: var(--p-primary-color);
}

.legal-body {
  width: 100%;
  max-width: 70rem;
  margin: 0 auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  flex: 1;
}

.legal-nav {
  border-bottom: 1px solid var(--p-content-border-color);
  overflow-x: auto;
}

.legal-nav-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: row;
  white-space: nowrap;
}

.legal-nav-item {
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}

.legal-nav-item.is-active {
  border-bottom-color: var(--p-primary-color);
}

.legal-nav-icon {
  font-size: 1rem;
}

.legal-nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  cursor: pointer;
  font-weight: 500;
  color: var(--p-text-muted-color);
  text-decoration: none;
  transition: color 0.15s ease;
}

.legal-nav-item.is-active .legal-nav-link {
  color: var(--p-primary-color);
}

.legal-nav-link:hover {
  color: var(--p-text-color);
}

.legal-content {
  background: var(--p-content-background);
}
</style>
