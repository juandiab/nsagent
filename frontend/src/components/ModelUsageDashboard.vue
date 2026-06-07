<template>
  <div class="usage-dashboard">
    <div class="usage-header">
      <div>
        <h3 class="info-title m-0">Model usage</h3>
        <p class="usage-period">{{ dashboard?.periodLabel || 'This month' }}</p>
      </div>
      <Button
        icon="pi pi-refresh"
        severity="secondary"
        text
        rounded
        :loading="loading"
        aria-label="Refresh usage"
        @click="load"
      />
    </div>

    <div v-if="loading && !dashboard" class="usage-loading">
      <ProgressSpinner style="width: 2rem; height: 2rem" />
    </div>

    <template v-else-if="dashboard">
      <div class="usage-card usage-card-brave">
        <div class="usage-card-top">
          <div class="usage-icon brave">
            <i class="pi pi-search" />
          </div>
          <div class="usage-meta">
            <span class="usage-name">Brave Search API</span>
            <span class="usage-sub">
              {{ dashboard.braveSearch.configured ? 'Key configured' : 'No API key' }}
              <span v-if="dashboard.braveSearch.enabled"> · Web search on</span>
            </span>
          </div>
          <Tag
            v-if="dashboard.braveSearch.configured"
            :value="braveStatusLabel"
            :severity="braveSeverity"
          />
        </div>

        <div v-if="dashboard.braveSearch.configured" class="usage-bars">
          <UsageMeter
            label="Search queries"
            :used="dashboard.braveSearch.queriesUsed"
            :limit="dashboard.braveSearch.monthlyQueryLimit"
            :percent="dashboard.braveSearch.percent"
            :remaining="dashboard.braveSearch.remainingQueries"
            :unlimited="dashboard.braveSearch.unlimited"
            unit="queries"
          />
        </div>
        <p v-else class="usage-empty">Add a Brave Search API key under Settings → AI Providers to track query usage.</p>
      </div>

      <div v-if="!dashboard.providers.length" class="usage-empty-block">
        No AI providers configured. Add LLM providers under Settings → AI Providers.
      </div>

      <div
        v-for="provider in dashboard.providers"
        :key="provider.id"
        class="usage-card"
        :class="{ 'usage-card-muted': !provider.enabled }"
      >
        <div class="usage-card-top">
          <div class="usage-icon" :class="providerIconClass(provider.providerType)">
            <i :class="providerIcon(provider.providerType)" />
          </div>
          <div class="usage-meta">
            <span class="usage-name">{{ provider.providerName }}</span>
            <span class="usage-sub">{{ provider.providerType }} · {{ provider.model }}</span>
          </div>
          <div class="usage-tags">
            <Tag v-if="provider.isDefault" value="Default" severity="info" />
            <Tag v-if="!provider.enabled" value="Disabled" severity="secondary" />
          </div>
        </div>

        <div class="usage-bars">
          <UsageMeter
            label="API requests"
            :used="provider.requestsUsed"
            :limit="provider.monthlyRequestLimit"
            :percent="provider.requestPercent"
            :remaining="provider.remainingRequests"
            :unlimited="provider.unlimited && !provider.monthlyRequestLimit"
            unit="requests"
          />
          <UsageMeter
            label="Tokens"
            :used="provider.tokensUsed"
            :limit="provider.monthlyTokenLimit"
            :percent="provider.tokenPercent"
            :remaining="provider.remainingTokens"
            :unlimited="provider.unlimited && !provider.monthlyTokenLimit"
            unit="tokens"
          />
        </div>
      </div>

      <p class="usage-footnote">
        Counts update after each JPilot chat and Brave web search this calendar month. Past activity before tracking was enabled is not included. Limits are planning caps — verify billing in each provider’s console.
      </p>
    </template>

    <Message v-else-if="error" severity="error" :closable="false">{{ error }}</Message>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import Button from 'primevue/button'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import Tag from 'primevue/tag'
import UsageMeter from './UsageMeter.vue'
import { formatCount, getModelUsageDashboard } from '../services/modelUsage'

const loading = ref(false)
const error = ref('')
const dashboard = ref(null)

const braveSeverity = computed(() => {
  const p = dashboard.value?.braveSearch?.percent
  if (p == null) return 'secondary'
  if (p >= 90) return 'danger'
  if (p >= 75) return 'warn'
  return 'success'
})

const braveStatusLabel = computed(() => {
  const brave = dashboard.value?.braveSearch
  if (!brave?.configured) return 'Not set'
  if (brave.unlimited) return `${formatCount(brave.queriesUsed)} used`
  const left = brave.remainingQueries ?? 0
  return `${formatCount(left)} left`
})

function providerIcon(type) {
  const map = {
    OpenAI: 'pi pi-sparkles',
    Anthropic: 'pi pi-comments',
    Gemini: 'pi pi-google',
    Grok: 'pi pi-bolt',
    DeepSeek: 'pi pi-code',
    OpenRouter: 'pi pi-share-alt',
    'Azure OpenAI': 'pi pi-microsoft',
    'AWS Bedrock': 'pi pi-cloud',
    'LM Studio': 'pi pi-desktop',
    'OpenAI-Compatible': 'pi pi-server'
  }
  return map[type] || 'pi pi-microchip-ai'
}

function providerIconClass(type) {
  return (type || 'default').replace(/\s+/g, '-').toLowerCase()
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    dashboard.value = await getModelUsageDashboard()
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Failed to load usage'
    dashboard.value = null
  } finally {
    loading.value = false
  }
}

onMounted(load)

defineExpose({ refresh: load })
</script>

<style scoped>
.usage-dashboard {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.usage-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
}

.usage-period {
  margin: 0.2rem 0 0;
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
}

.usage-loading {
  display: flex;
  justify-content: center;
  padding: 1.5rem 0;
}

.usage-card {
  padding: 0.85rem 0.9rem;
  border-radius: 12px;
  background: linear-gradient(145deg, var(--app-nested-surface), var(--app-nested-surface-strong));
  border: 1px solid var(--p-content-border-color);
  box-shadow: 0 1px 8px rgba(15, 23, 42, 0.04);
}

.usage-card-brave {
  background: linear-gradient(
    145deg,
    color-mix(in srgb, #3b82f6 12%, var(--app-nested-surface)),
    var(--app-nested-surface-strong)
  );
}

.usage-card-muted {
  opacity: 0.72;
}

.usage-card-top {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  margin-bottom: 0.65rem;
}

.usage-icon {
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  background: var(--p-primary-100);
  color: var(--p-primary-700);
  flex-shrink: 0;
}

.usage-icon.brave {
  background: rgba(59, 130, 246, 0.15);
  color: #2563eb;
}

.usage-icon.openai {
  background: rgba(16, 163, 127, 0.12);
  color: #0d9488;
}

.usage-icon.anthropic {
  background: rgba(217, 119, 6, 0.12);
  color: #b45309;
}

.usage-icon.gemini {
  background: rgba(37, 99, 235, 0.12);
  color: #1d4ed8;
}

.usage-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.usage-name {
  font-size: 0.875rem;
  font-weight: 600;
  line-height: 1.2;
}

.usage-sub {
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.usage-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.usage-bars {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.usage-empty,
.usage-empty-block,
.usage-footnote {
  margin: 0;
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
  line-height: 1.45;
}

.usage-empty-block {
  padding: 0.75rem;
  border-radius: 8px;
  background: var(--app-nested-surface-strong);
}

:global(html.app-dark) .usage-card {
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.22);
}

:global(html.app-dark) .usage-icon {
  background: color-mix(in srgb, var(--p-primary-400) 18%, var(--app-nested-surface-strong));
  color: var(--p-primary-200);
}

:global(html.app-dark) .usage-icon.brave {
  background: color-mix(in srgb, #3b82f6 22%, var(--app-nested-surface-strong));
  color: #93c5fd;
}
</style>
