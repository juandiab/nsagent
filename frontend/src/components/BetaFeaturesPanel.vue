<template>
  <div class="beta-features-panel">
    <div v-if="loading" class="content-panel content-panel-padded py-4">
      <ProgressSpinner style="width: 2rem; height: 2rem" />
    </div>

    <div v-else class="flex flex-column gap-4">
      <Message severity="info" :closable="false">
        {{ betaFeatures.sshSettingsNote }}
        <RouterLink class="beta-nextgen-link" :to="{ path: '/settings', query: { section: 'nextgen' } }">
          Open Next-Gen API settings
        </RouterLink>
      </Message>

      <div class="grid">
        <div class="col-12 lg:col-8">
          <div class="content-panel content-panel-padded">
            <div class="flex align-items-start justify-content-between gap-3 flex-wrap">
              <div>
                <h2 class="section-title">Beta platforms</h2>
                <p class="section-copy">
                  Enable JPilot MCP tools for SDX, Cisco IOS/XE, and F5 BIG-IP. These integrations are in beta testing.
                </p>
              </div>
              <Tag :value="betaFeatures.statusLabel || 'Beta Available'" severity="warn" icon="pi pi-flag" />
            </div>

            <div class="flex gap-2 pt-3 flex-wrap">
              <Button
                label="Save beta settings"
                icon="pi pi-save"
                size="small"
                :loading="saving"
                @click="saveSettings"
              />
              <Button
                label="Enable all beta tools"
                icon="pi pi-check-square"
                size="small"
                severity="secondary"
                outlined
                @click="setAllBetaTools(true)"
              />
              <Button
                label="Disable all beta tools"
                icon="pi pi-times"
                size="small"
                severity="secondary"
                outlined
                @click="setAllBetaTools(false)"
              />
            </div>

            <Message v-if="message" class="mt-3" :severity="messageSeverity" :closable="false">
              {{ message }}
            </Message>
          </div>
        </div>

        <div class="col-12 lg:col-4">
          <div class="content-panel content-panel-padded info-panel h-full">
            <h3 class="info-title">Summary</h3>
            <ul class="info-list m-0 pl-0 list-none">
              <li><strong>Platforms:</strong> {{ betaFeatures.productCount ?? betaProducts.length }}</li>
              <li><strong>Beta tools enabled:</strong> {{ enabledBetaToolCount }} / {{ configurableBetaToolCount }}</li>
              <li><strong>MCP status:</strong> {{ mcpStatus.online ? 'Online' : 'Offline' }}</li>
              <li><strong>Transport:</strong> {{ betaFeatures.transport || 'SSH' }}</li>
            </ul>
          </div>
        </div>
      </div>

      <div
        v-for="product in betaProducts"
        :key="product.id"
        class="content-panel content-panel-padded product-section"
      >
        <div class="product-head">
          <div>
            <h2 class="section-title">{{ product.label }}</h2>
            <p class="section-copy">{{ product.description }}</p>
            <div class="product-meta">
              <Tag :value="product.vendorGroup" severity="secondary" />
              <Tag :value="product.transport" severity="info" />
            </div>
          </div>
          <div class="product-actions">
            <Button
              label="Enable all"
              size="small"
              text
              @click="setProductTools(product.id, true)"
            />
            <Button
              label="Disable all"
              size="small"
              text
              severity="secondary"
              @click="setProductTools(product.id, false)"
            />
          </div>
        </div>

        <div v-if="product.docUrls?.length" class="doc-links mt-3">
          <span class="meta-label">Official documentation</span>
          <ul class="m-0 pl-0 list-none doc-link-list">
            <li v-for="doc in product.docUrls" :key="doc.url">
              <a :href="doc.url" target="_blank" rel="noopener">{{ doc.label }}</a>
            </li>
          </ul>
        </div>

        <p class="setting-hint mt-2 mb-0">{{ product.accessHint }}</p>

        <DataTable :value="product.options" size="small" striped-rows class="options-table mt-4">
          <Column field="label" header="Option">
            <template #body="{ data }">
              <div class="option-label">{{ data.label }}</div>
              <div class="setting-hint">{{ data.description }}</div>
              <code class="tool-code">{{ data.name }}</code>
            </template>
          </Column>
          <Column header="Available in">
            <template #body="{ data }">
              <div class="surface-tags">
                <Tag v-for="surface in data.surfaces" :key="surface" :value="surface" severity="secondary" />
              </div>
            </template>
          </Column>
          <Column header="Enabled" style="width: 6rem">
            <template #body="{ data }">
              <ToggleSwitch
                v-if="data.configurable"
                :model-value="isToolEnabled(data.name)"
                @update:model-value="toggleTool(data.name, $event)"
              />
              <Tag v-else value="Always on" severity="info" />
            </template>
          </Column>
        </DataTable>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import Tag from 'primevue/tag'
import ToggleSwitch from 'primevue/toggleswitch'
import { getMcpConfig, getMcpStatus, saveMcpConfig } from '../services/mcp'

const loading = ref(true)
const saving = ref(false)
const message = ref('')
const messageSeverity = ref('info')
const betaProducts = ref([])
const betaFeatures = reactive({
  productCount: 0,
  configurableToolCount: 0,
  transport: 'SSH',
  sshSettingsNote: '',
  statusLabel: 'Beta Available'
})

const mcpSettings = reactive({
  serverUrl: '',
  serverName: 'netscaler-copilot',
  nitroTimeoutSeconds: 30,
  verifySsl: false,
  enabledTools: [],
  sseEnabled: true,
  sshFallbackEnabled: true,
  sshPort: 22,
  sshTimeoutSeconds: 30
})

const mcpStatus = reactive({
  online: false
})

const configurableBetaToolNames = computed(() => {
  const names = []
  for (const product of betaProducts.value) {
    for (const option of product.options || []) {
      if (option.configurable) names.push(option.name)
    }
  }
  return names
})

const configurableBetaToolCount = computed(() => configurableBetaToolNames.value.length)

const enabledBetaToolCount = computed(
  () =>
    mcpSettings.enabledTools.filter((name) => configurableBetaToolNames.value.includes(name)).length
)

function isToolEnabled(name) {
  return mcpSettings.enabledTools.includes(name)
}

function toggleTool(name, enabled) {
  if (enabled && !mcpSettings.enabledTools.includes(name)) {
    mcpSettings.enabledTools.push(name)
  }
  if (!enabled) {
    mcpSettings.enabledTools = mcpSettings.enabledTools.filter((item) => item !== name)
  }
}

function setProductTools(productId, enabled) {
  const product = betaProducts.value.find((p) => p.id === productId)
  if (!product) return
  for (const option of product.options || []) {
    if (!option.configurable) continue
    toggleTool(option.name, enabled)
  }
}

function setAllBetaTools(enabled) {
  for (const name of configurableBetaToolNames.value) {
    toggleTool(name, enabled)
  }
}

async function refreshMcpStatus() {
  try {
    const status = await getMcpStatus()
    mcpStatus.online = status.online
  } catch {
    mcpStatus.online = false
  }
}

async function loadConfig() {
  loading.value = true
  try {
    const config = await getMcpConfig()
    betaProducts.value = config.betaProducts || []
    Object.assign(betaFeatures, config.betaFeatures || {})
    Object.assign(mcpSettings, {
      serverUrl: config.serverUrl,
      serverName: config.serverName,
      nitroTimeoutSeconds: config.nitroTimeoutSeconds,
      verifySsl: config.verifySsl,
      enabledTools: [...(config.enabledTools || [])],
      sseEnabled: config.sseEnabled,
      sshFallbackEnabled: config.sshFallbackEnabled ?? true,
      sshPort: config.sshPort ?? 22,
      sshTimeoutSeconds: config.sshTimeoutSeconds ?? 30
    })
    await refreshMcpStatus()
  } catch (error) {
    message.value = error.response?.data?.detail || 'Failed to load beta feature settings'
    messageSeverity.value = 'error'
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  message.value = ''
  try {
    await saveMcpConfig({ ...mcpSettings })
    message.value = 'Beta feature settings saved and synced to the MCP server.'
    messageSeverity.value = 'success'
    await refreshMcpStatus()
  } catch (error) {
    message.value = error.response?.data?.detail || 'Failed to save beta settings'
    messageSeverity.value = 'error'
  } finally {
    saving.value = false
  }
}

onMounted(loadConfig)
</script>

<style scoped>
.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
}

.section-copy {
  margin: 0.35rem 0 0;
  color: var(--p-text-muted-color);
  font-size: 0.875rem;
}

.setting-hint {
  font-size: 0.8125rem;
  color: var(--p-text-muted-color);
  margin-top: 0.2rem;
}

.tool-code {
  display: inline-block;
  margin-top: 0.35rem;
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
}

.info-title {
  font-size: 0.9375rem;
  font-weight: 600;
  margin: 0 0 0.75rem;
}

.info-list {
  color: var(--p-text-muted-color);
  line-height: 1.6;
  font-size: 0.875rem;
}

.info-list li + li {
  margin-top: 0.35rem;
}

.info-list strong {
  color: var(--p-text-color);
}

.product-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.product-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.product-actions {
  display: flex;
  gap: 0.25rem;
  flex-shrink: 0;
}

.meta-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--p-text-muted-color);
  margin-bottom: 0.35rem;
}

.doc-link-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.doc-link-list a {
  font-size: 0.875rem;
}

.surface-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.beta-nextgen-link {
  margin-left: 0.35rem;
  font-weight: 500;
}
</style>
