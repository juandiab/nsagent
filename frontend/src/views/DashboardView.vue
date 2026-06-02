<template>
  <div class="page">
    <PageHeader
      title="Dashboard"
      subtitle="Overview of your JPilot platform"
    />

    <div class="welcome-panel mb-5">
      <h2>Welcome to JPilot</h2>
      <p>Your intelligent NetScaler management platform. Manage appliances, configure AI providers, and prepare for automated operations.</p>
    </div>

    <div class="grid">
      <div class="col-12 md:col-4">
        <div class="stat-card">
          <div class="stat-label">NetScalers</div>
          <div class="stat-value">{{ stats.appliances }}</div>
          <RouterLink to="/netscalers" class="stat-link">Manage inventory →</RouterLink>
        </div>
      </div>
      <div class="col-12 md:col-4">
        <div class="stat-card">
          <div class="stat-label">AI Providers</div>
          <div class="stat-value">{{ stats.providers }}</div>
          <RouterLink to="/ai-providers" class="stat-link">Configure providers →</RouterLink>
        </div>
      </div>
      <div class="col-12 md:col-4">
        <div class="stat-card">
          <div class="stat-label">Enabled Appliances</div>
          <div class="stat-value">{{ stats.enabled }}</div>
          <span class="empty-hint">Active in inventory</span>
        </div>
      </div>
    </div>

    <div class="grid mt-4">
      <div class="col-12 md:col-8">
        <div class="content-panel content-panel-padded quick-panel">
          <h3 class="panel-heading">Quick actions</h3>
          <div class="flex flex-wrap gap-3 mt-3">
            <Button label="Open JPilot" icon="pi pi-comments" size="small" @click="router.push('/copilot')" />
            <Button label="Add NetScaler" icon="pi pi-plus" size="small" severity="secondary" outlined @click="router.push('/netscalers')" />
            <Button label="Add AI Provider" icon="pi pi-sparkles" size="small" severity="secondary" outlined @click="router.push('/ai-providers')" />
          </div>
        </div>
      </div>
      <div class="col-12 md:col-4">
        <div class="content-panel content-panel-padded status-panel">
          <h3 class="panel-heading">Platform status</h3>
          <ul class="status-list m-0 mt-3 p-0 list-none">
            <li><Tag value="API Online" severity="success" icon="pi pi-check-circle" /></li>
            <li>
              <Tag
                :value="mcpStatus.online ? 'MCP Online' : 'MCP Offline'"
                :severity="mcpStatus.online ? 'success' : 'danger'"
                :icon="mcpStatus.online ? 'pi pi-link' : 'pi pi-exclamation-triangle'"
              />
            </li>
            <li><Tag value="MongoDB Connected" severity="success" icon="pi pi-database" /></li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import PageHeader from '../components/PageHeader.vue'
import api from '../services/api'
import { getMcpStatus } from '../services/mcp'

const router = useRouter()
const stats = reactive({
  appliances: 0,
  providers: 0,
  enabled: 0
})
const mcpStatus = reactive({
  online: false
})

onMounted(async () => {
  try {
    const [appliancesRes, providersRes, status] = await Promise.all([
      api.get('/appliances'),
      api.get('/ai-providers'),
      getMcpStatus().catch(() => ({ online: false }))
    ])
    stats.appliances = appliancesRes.data.length
    stats.providers = providersRes.data.length
    stats.enabled = appliancesRes.data.filter((item) => item.enabled).length
    mcpStatus.online = status.online
  } catch {
    // Dashboard remains usable without stats
  }
})
</script>

<style scoped>
.page {
  animation: page-in 0.35s ease;
}

.panel-heading {
  font-size: 0.9375rem;
  font-weight: 600;
  margin: 0;
  color: var(--p-text-color);
}

.stat-link {
  display: inline-block;
  margin-top: 0.75rem;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--p-primary-color);
  text-decoration: none;
}

.stat-link:hover {
  text-decoration: underline;
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

@keyframes page-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
