<template>
  <div class="page">
    <div class="welcome-panel mb-3">
      <div class="welcome-panel-inner flex flex-column lg:flex-row lg:align-items-center lg:justify-content-between gap-2">
        <div class="welcome-copy">
          <p class="welcome-eyebrow m-0">
            Developed by
            <a
              :href="NEXXUS_TECH.websiteUrl"
              target="_blank"
              rel="noopener noreferrer"
            >{{ NEXXUS_TECH.name }}</a>
          </p>
          <h2>Welcome to JPilot</h2>
          <p>
            Your intelligent ADC and infrastructure platform. Manage NetScalers with JPilot chat,
            register other vendors for what's ahead, and configure AI providers—all with guardrails
            built by Nexxus Tech.
          </p>
        </div>
        <div class="welcome-cta flex-shrink-0">
          <Button
            as="a"
            :href="NEXXUS_TECH.contactUrl"
            target="_blank"
            rel="noopener noreferrer"
            label="Contact us to customize this solution for you"
            icon="pi pi-envelope"
            icon-pos="right"
            size="small"
            class="contact-cta-btn"
          />
        </div>
      </div>
    </div>

    <div class="grid dashboard-main-grid">
      <div class="col-12 md:col-6 dashboard-column">
        <div class="stat-card">
          <div class="stat-label">Appliances</div>
          <div class="stat-value">{{ stats.netscalers + stats.otherAppliances }}</div>
          <p class="stat-detail">
            {{ stats.netscalers }} NetScaler · {{ stats.otherAppliances }} other vendors
          </p>
          <RouterLink to="/appliances" class="stat-link">Manage inventory →</RouterLink>
        </div>
        <div class="stat-card">
          <div class="stat-label">AI Providers</div>
          <div class="stat-value">{{ stats.providers }}</div>
          <RouterLink v-if="isAdmin" to="/settings?section=ai-providers" class="stat-link">Configure providers →</RouterLink>
          <span v-else class="empty-hint">Admin configuration</span>
        </div>
      </div>
      <div class="col-12 md:col-6 dashboard-column">
        <div class="content-panel content-panel-padded quick-panel">
          <h3 class="panel-heading">Quick actions</h3>
          <div class="flex flex-wrap gap-3 mt-3">
            <Button
              v-for="action in quickActions"
              :key="action.to"
              :label="action.label"
              :icon="action.icon"
              size="small"
              :severity="action.to === '/copilot' ? undefined : 'secondary'"
              :outlined="action.to !== '/copilot'"
              @click="router.push(action.to)"
            />
          </div>
        </div>
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

    <NexxusMarketingSection pinned />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import NexxusMarketingSection from '../components/NexxusMarketingSection.vue'
import { NEXXUS_TECH } from '../config/nexxusTech'
import { isNetScalerVendor } from '../config/applianceVendors'
import api from '../services/api'
import { getDashboardQuickActions } from '../config/jpilotRecommendedActions'
import { getMcpStatus } from '../services/mcp'
import { getStoredUser } from '../services/auth'

const router = useRouter()
const currentUser = ref(getStoredUser())
const isAdmin = computed(() => currentUser.value?.role === 'admin')
const quickActions = computed(() => getDashboardQuickActions(isAdmin.value))
const stats = reactive({
  netscalers: 0,
  providers: 0,
  otherAppliances: 0
})
const mcpStatus = reactive({
  online: false
})

onMounted(async () => {
  try {
    const meRes = await api.get('/auth/me')
    currentUser.value = meRes.data
  } catch {
    // Dashboard remains usable without role refresh.
  }
  try {
    const [appliancesRes, providersRes, status] = await Promise.all([
      api.get('/appliances'),
      api.get('/ai-providers'),
      getMcpStatus().catch(() => ({ online: false }))
    ])
    stats.netscalers = appliancesRes.data.filter((item) => isNetScalerVendor(item.vendor)).length
    stats.providers = providersRes.data.length
    stats.otherAppliances = appliancesRes.data.filter((item) => !isNetScalerVendor(item.vendor)).length
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

.dashboard-column {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.panel-heading {
  font-size: 0.9375rem;
  font-weight: 600;
  margin: 0;
  color: var(--p-text-color);
}

.stat-detail {
  margin: 0.35rem 0 0;
  font-size: 0.8125rem;
  color: var(--p-text-muted-color);
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

.welcome-eyebrow {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--p-text-muted-color);
  margin-bottom: 0.25rem !important;
}

.welcome-eyebrow a {
  color: var(--p-primary-color);
  text-decoration: none;
}

.welcome-eyebrow a:hover {
  text-decoration: underline;
}

.contact-cta-btn {
  white-space: nowrap;
}

@media (max-width: 991px) {
  .contact-cta-btn {
    white-space: normal;
    width: 100%;
  }
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

@media (max-height: 900px) {
  .dashboard-column {
    gap: 0.5rem;
  }
}
</style>
