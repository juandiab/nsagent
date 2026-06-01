<template>
  <div class="page">
    <PageHeader
      title="Next-Gen API"
      subtitle="NetScaler Next-Gen API options for Copilot and MCP"
    />

    <AiSectionNav />

    <div class="grid">
      <div class="col-12 lg:col-8">
        <div class="content-panel content-panel-padded">
          <div v-if="loading" class="py-4">
            <ProgressSpinner style="width: 2rem; height: 2rem" />
          </div>

          <div v-else class="flex flex-column gap-4">
            <div class="nextgen-meta">
              <div class="meta-item">
                <span class="meta-label">API base</span>
                <code>{{ nextGenApi.apiBase || '—' }}</code>
              </div>
              <div class="meta-item">
                <span class="meta-label">Transport</span>
                <span>{{ nextGenApi.transport || '—' }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">Authentication</span>
                <span>{{ nextGenApi.auth || '—' }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">Documentation</span>
                <a
                  v-if="nextGenApi.guideUrl"
                  :href="nextGenApi.guideUrl"
                  target="_blank"
                  rel="noopener"
                >
                  Getting started guide
                </a>
                <span v-else>—</span>
              </div>
            <div class="meta-item">
                <span class="meta-label">CLI reference</span>
                <a
                  v-if="nextGenApi.cliReferenceUrl"
                  :href="nextGenApi.cliReferenceUrl"
                  target="_blank"
                  rel="noopener"
                >
                  ADC command reference
                </a>
                <span v-else>—</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">API reference</span>
                <a
                  v-if="nextGenApi.apiDocsUrl"
                  :href="nextGenApi.apiDocsUrl"
                  target="_blank"
                  rel="noopener"
                >
                  OpenAPI catalog
                </a>
                <span v-else>—</span>
              </div>
            </div>

            <div class="flex flex-column gap-2 setting-row">
              <label for="nitroTimeout" class="setting-label">Next-Gen API timeout (seconds)</label>
              <InputNumber
                id="nitroTimeout"
                v-model="mcpSettings.nitroTimeoutSeconds"
                :min="5"
                :max="120"
                show-buttons
                class="timeout-input"
              />
            </div>

            <div class="flex align-items-center justify-content-between gap-3 setting-row">
              <div>
                <div class="setting-label">Verify SSL certificates</div>
                <div class="setting-hint">Disable for appliances with self-signed certificates (default off).</div>
              </div>
              <ToggleSwitch v-model="mcpSettings.verifySsl" />
            </div>

            <div class="flex align-items-center justify-content-between gap-3 setting-row">
              <div>
                <div class="setting-label">SSH fallback</div>
                <div class="setting-hint">
                  When Next-Gen API cannot answer, Copilot may run read-only show/stat/get commands via SSH.
                </div>
              </div>
              <ToggleSwitch v-model="mcpSettings.sshFallbackEnabled" />
            </div>

            <div class="flex flex-column gap-2 setting-row">
              <label for="sshPort" class="setting-label">SSH port</label>
              <InputNumber id="sshPort" v-model="mcpSettings.sshPort" :min="1" :max="65535" show-buttons class="timeout-input" />
            </div>

            <div class="flex flex-column gap-2 setting-row">
              <label for="sshTimeout" class="setting-label">SSH timeout (seconds)</label>
              <InputNumber
                id="sshTimeout"
                v-model="mcpSettings.sshTimeoutSeconds"
                :min="5"
                :max="120"
                show-buttons
                class="timeout-input"
              />
            </div>

            <div class="setting-row">
              <div class="setting-label mb-3">Available options</div>
              <DataTable :value="nextGenOptions" size="small" striped-rows class="options-table">
                <Column field="label" header="Option">
                  <template #body="{ data }">
                    <div class="option-label">{{ data.label }}</div>
                    <div class="setting-hint">{{ data.description }}</div>
                    <code class="tool-code">{{ data.name }}</code>
                  </template>
                </Column>
                <Column header="Next-Gen endpoints">
                  <template #body="{ data }">
                    <ul v-if="data.nextGenEndpoints?.length" class="endpoint-list m-0 pl-3">
                      <li v-for="endpoint in data.nextGenEndpoints" :key="endpoint">
                        <code>{{ endpoint }}</code>
                      </li>
                    </ul>
                    <span v-else class="setting-hint">Platform / docs</span>
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

            <div class="setting-row">
              <div class="setting-label mb-1">Next-Gen API reference</div>
              <div class="setting-hint mb-3">
                Full endpoint catalog indexed for Copilot RAG ({{ apiOperations.length }} operations).
              </div>
              <DataTable
                :value="apiOperations"
                size="small"
                striped-rows
                paginator
                :rows="12"
                class="options-table"
              >
                <Column field="category" header="Category" sortable />
                <Column field="name" header="Operation" sortable />
                <Column field="method" header="Method" style="width: 5rem">
                  <template #body="{ data }">
                    <Tag :value="data.method" :severity="data.method === 'GET' ? 'info' : 'secondary'" />
                  </template>
                </Column>
                <Column field="path" header="Path">
                  <template #body="{ data }">
                    <code>{{ data.path }}</code>
                  </template>
                </Column>
              </DataTable>
            </div>

            <div class="flex gap-2 pt-2">
              <Button
                label="Save settings"
                icon="pi pi-save"
                size="small"
                :loading="saving"
                @click="saveSettings"
              />
            </div>

            <Message v-if="message" :severity="messageSeverity" :closable="false">
              {{ message }}
            </Message>
          </div>
        </div>
      </div>

      <div class="col-12 lg:col-4">
        <div class="content-panel content-panel-padded info-panel">
          <h3 class="info-title">Summary</h3>
          <ul class="info-list m-0 pl-0 list-none">
            <li><strong>Options:</strong> {{ nextGenOptions.length }}</li>
            <li><strong>API operations:</strong> {{ apiOperations.length }}</li>
            <li><strong>Enabled:</strong> {{ enabledToolCount }} / {{ configurableOptionCount }}</li>
            <li><strong>MCP status:</strong> {{ mcpStatus.online ? 'Online' : 'Offline' }}</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import Button from 'primevue/button'
import Column from 'primevue/column'
import DataTable from 'primevue/datatable'
import InputNumber from 'primevue/inputnumber'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import Tag from 'primevue/tag'
import ToggleSwitch from 'primevue/toggleswitch'
import AiSectionNav from '../components/AiSectionNav.vue'
import PageHeader from '../components/PageHeader.vue'
import { getMcpConfig, getMcpStatus, saveMcpConfig } from '../services/mcp'

const loading = ref(true)
const saving = ref(false)
const message = ref('')
const messageSeverity = ref('info')
const nextGenOptions = ref([])
const apiCategories = ref([])
const nextGenApi = reactive({
  apiBase: '',
  guideUrl: '',
  apiDocsUrl: '',
  transport: '',
  auth: ''
})

const apiOperations = computed(() =>
  apiCategories.value.flatMap((group) =>
    (group.operations || []).map((operation) => ({
      category: group.category,
      name: operation.name,
      method: operation.method,
      path: operation.path
    }))
  )
)

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
  online: false,
  enabledToolCount: 0
})

const configurableOptionCount = computed(
  () => nextGenOptions.value.filter((item) => item.configurable).length
)

const enabledToolCount = computed(
  () => mcpSettings.enabledTools.filter((name) =>
    nextGenOptions.value.some((item) => item.configurable && item.name === name)
  ).length
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

async function refreshMcpStatus() {
  try {
    const status = await getMcpStatus()
    mcpStatus.online = status.online
    mcpStatus.enabledToolCount = status.enabledToolCount
  } catch {
    mcpStatus.online = false
  }
}

async function loadConfig() {
  loading.value = true
  try {
    const config = await getMcpConfig()
    nextGenOptions.value = config.nextGenOptions || config.availableTools || []
    apiCategories.value = config.nextGenApiCategories || []
    Object.assign(nextGenApi, config.nextGenApi || {})
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
    message.value = error.response?.data?.detail || 'Failed to load Next-Gen API settings'
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
    message.value = 'Next-Gen API settings saved and synced to the MCP server.'
    messageSeverity.value = 'success'
    await refreshMcpStatus()
  } catch (error) {
    message.value = error.response?.data?.detail || 'Failed to save settings'
    messageSeverity.value = 'error'
  } finally {
    saving.value = false
  }
}

onMounted(loadConfig)
</script>

<style scoped>
.page {
  animation: page-in 0.35s ease;
}

.setting-row {
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--p-content-border-color);
}

.setting-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.setting-label {
  font-size: 0.9375rem;
  font-weight: 500;
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

.nextgen-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
  gap: 1rem;
  padding: 1rem;
  border: 1px solid var(--p-content-border-color);
  border-radius: var(--p-content-border-radius);
  background: var(--p-content-background);
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.meta-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--p-text-muted-color);
}

.option-label {
  font-size: 0.9375rem;
  font-weight: 500;
}

.endpoint-list {
  font-size: 0.8125rem;
  color: var(--p-text-muted-color);
}

.endpoint-list li + li {
  margin-top: 0.25rem;
}

.surface-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.options-table :deep(.p-datatable-tbody > tr > td) {
  vertical-align: top;
}

.timeout-input {
  max-width: 10rem;
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
