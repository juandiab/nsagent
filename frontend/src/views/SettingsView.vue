<template>
  <div class="page">
    <PageHeader
      title="Settings"
      subtitle="Platform configuration and preferences"
    />

    <div class="grid">
      <div class="col-12 lg:col-8">
        <div class="content-panel content-panel-padded mb-4">
          <div class="flex align-items-start justify-content-between gap-3 flex-wrap">
            <div>
              <h2 class="section-title">MCP Server</h2>
              <p class="section-copy">Configure the Model Context Protocol server connection.</p>
            </div>
            <Tag
              :value="mcpStatus.online ? 'Online' : 'Offline'"
              :severity="mcpStatus.online ? 'success' : 'danger'"
              :icon="mcpStatus.online ? 'pi pi-check-circle' : 'pi pi-times-circle'"
            />
          </div>

          <div v-if="mcpLoading" class="mt-4">
            <ProgressSpinner style="width: 2rem; height: 2rem" />
          </div>

          <div v-else class="flex flex-column gap-4 mt-4">
            <div class="flex flex-column gap-2 setting-row">
              <label for="serverUrl" class="setting-label">Server URL</label>
              <InputText
                id="serverUrl"
                v-model="mcpSettings.serverUrl"
                placeholder="http://mcp-server:8001"
              />
              <small class="setting-hint">Backend uses this URL to reach the MCP server. Use host.docker.internal for host-side services.</small>
            </div>

            <div class="flex flex-column gap-2 setting-row">
              <label for="serverName" class="setting-label">Server name</label>
              <InputText id="serverName" v-model="mcpSettings.serverName" />
            </div>

            <div class="flex align-items-center justify-content-between gap-3 setting-row">
              <div>
                <div class="setting-label">SSE transport</div>
                <div class="setting-hint">Server-Sent Events endpoint for MCP clients.</div>
              </div>
              <ToggleSwitch v-model="mcpSettings.sseEnabled" />
            </div>

            <div class="flex gap-2 pt-2">
              <Button
                label="Save MCP settings"
                icon="pi pi-save"
                size="small"
                :loading="mcpSaving"
                @click="saveMcpSettings"
              />
              <Button
                label="Test connection"
                icon="pi pi-bolt"
                size="small"
                severity="secondary"
                outlined
                :loading="mcpTesting"
                @click="testMcpConnection"
              />
            </div>

            <Message v-if="mcpMessage" :severity="mcpMessageSeverity" :closable="false">
              {{ mcpMessage }}
            </Message>
          </div>
        </div>

        <div class="content-panel content-panel-padded mb-4">
          <h2 class="section-title">Security</h2>
          <p class="section-copy">
            Sign in with your password first, then register a passkey for faster sign-in next time.
          </p>

          <div class="flex flex-column gap-3 mt-4">
            <div class="flex align-items-center justify-content-between gap-3 flex-wrap">
              <div>
                <div class="setting-label">Passkeys</div>
                <div class="setting-hint">
                  {{ passkeyStatus.hasPasskey
                    ? `${passkeyStatus.passkeyCount} passkey(s) registered for ${passkeyStatus.username}`
                    : 'No passkey registered yet for your account.' }}
                </div>
              </div>
              <Tag
                :value="passkeyStatus.hasPasskey ? 'Enabled' : 'Not set up'"
                :severity="passkeyStatus.hasPasskey ? 'success' : 'secondary'"
              />
            </div>

            <Button
              label="Register passkey"
              icon="pi pi-key"
              size="small"
              :loading="passkeyRegistering"
              @click="registerMyPasskey"
            />

            <Message v-if="passkeyMessage" :severity="passkeyMessageSeverity" :closable="false">
              {{ passkeyMessage }}
            </Message>
          </div>
        </div>

        <div class="content-panel content-panel-padded">
          <h2 class="section-title">Copilot</h2>
          <p class="section-copy">Control what can be attached to Copilot chat messages.</p>

          <div class="flex flex-column gap-4 mt-4">
            <div class="flex align-items-center justify-content-between gap-3 setting-row">
              <div>
                <div class="setting-label">Allow image attachments</div>
                <div class="setting-hint">PNG, JPEG, WebP, GIF — up to 5 MB each</div>
              </div>
              <ToggleSwitch v-model="copilotSettings.allowImages" @update:model-value="saveCopilotPrefs" />
            </div>

            <div class="flex align-items-center justify-content-between gap-3 setting-row">
              <div>
                <div class="setting-label">Allow configuration files</div>
                <div class="setting-hint">.conf, .cfg, .txt, .json, .yaml, .xml, .ns, .cs — up to 1 MB each</div>
              </div>
              <ToggleSwitch v-model="copilotSettings.allowConfigFiles" @update:model-value="saveCopilotPrefs" />
            </div>

            <div class="flex flex-column gap-2 setting-row">
              <label for="maxAttachments" class="setting-label">Max attachments per message</label>
              <Select
                id="maxAttachments"
                v-model="copilotSettings.maxAttachments"
                :options="maxAttachmentOptions"
                class="max-select"
                @update:model-value="saveCopilotPrefs"
              />
            </div>
          </div>
        </div>

        <div class="content-panel content-panel-padded mt-4">
          <h2 class="section-title">Copilot web search</h2>
          <p class="section-copy">
            Copilot always searches the official Next-Gen API getting started guide. Optionally enable Brave Search for additional web results.
          </p>

          <div class="flex flex-column gap-4 mt-4">
            <div class="flex align-items-center justify-content-between gap-3 setting-row">
              <div>
                <div class="setting-label">Enable web search for Next-Gen API docs</div>
                <div class="setting-hint">Adds broader internet results alongside the official guide.</div>
              </div>
              <ToggleSwitch v-model="platformSettings.allowWebSearch" />
            </div>

            <div class="flex flex-column gap-2 setting-row">
              <label for="braveApiKey" class="setting-label">Brave Search API key</label>
              <Password
                id="braveApiKey"
                v-model="platformSettings.braveSearchApiKey"
                class="w-full"
                :feedback="false"
                toggle-mask
                input-class="w-full"
                :placeholder="platformSettings.hasBraveSearchApiKey ? 'Saved — enter a new key to replace' : 'BSA...'"
              />
              <small class="setting-hint">
                Get a key from <a href="https://brave.com/search/api/" target="_blank" rel="noopener">Brave Search API</a>.
                Stored encrypted on the backend.
              </small>
            </div>

            <div class="flex gap-2 pt-2">
              <Button
                label="Save web search settings"
                icon="pi pi-save"
                size="small"
                :loading="platformSaving"
                @click="savePlatformSettings"
              />
              <Button
                label="Test search"
                icon="pi pi-bolt"
                size="small"
                severity="secondary"
                outlined
                :loading="platformTesting"
                @click="testPlatformSearch"
              />
            </div>

            <Message v-if="platformMessage" :severity="platformMessageSeverity" :closable="false">
              {{ platformMessage }}
            </Message>
          </div>
        </div>
      </div>

      <div class="col-12 lg:col-4">
        <div class="content-panel content-panel-padded info-panel mb-4">
          <h3 class="info-title">MCP status</h3>
          <ul class="info-list m-0 pl-0 list-none">
            <li><strong>URL:</strong> {{ mcpStatus.serverUrl || '—' }}</li>
            <li><strong>Enabled tools:</strong> {{ mcpStatus.enabledToolCount }} / {{ mcpStatus.toolCount }}</li>
            <li><strong>Status:</strong> {{ mcpStatus.message }}</li>
          </ul>
        </div>

        <div class="content-panel content-panel-padded info-panel">
          <h3 class="info-title">Attachment tips</h3>
          <ul class="info-list m-0 pl-3">
            <li>Attach NetScaler configs for analysis or troubleshooting.</li>
            <li>Attach screenshots of errors, dashboards, or topology diagrams.</li>
            <li>Vision support depends on your default AI provider and model.</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'
import ProgressSpinner from 'primevue/progressspinner'
import Select from 'primevue/select'
import Tag from 'primevue/tag'
import ToggleSwitch from 'primevue/toggleswitch'
import PageHeader from '../components/PageHeader.vue'
import { getCopilotSettings, saveCopilotSettings } from '../services/copilot'
import {
  getCopilotPlatformSettings,
  saveCopilotPlatformSettings,
  testCopilotPlatformSearch
} from '../services/copilotPlatform'
import { getMcpConfig, getMcpStatus, saveMcpConfig } from '../services/mcp'
import api from '../services/api'
import { getStoredUser } from '../services/auth'
import { fetchPasskeyStatus, passkeyErrorMessage, registerPasskey } from '../services/webauthn'

const maxAttachmentOptions = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
const copilotSettings = reactive(getCopilotSettings())

const platformSaving = ref(false)
const platformTesting = ref(false)
const platformMessage = ref('')
const platformMessageSeverity = ref('info')
const platformSettings = reactive({
  allowWebSearch: false,
  hasBraveSearchApiKey: false,
  braveSearchApiKey: ''
})

const mcpLoading = ref(true)
const mcpSaving = ref(false)
const mcpTesting = ref(false)
const mcpMessage = ref('')
const mcpMessageSeverity = ref('info')

const mcpSettings = reactive({
  serverUrl: '',
  serverName: 'netscaler-copilot',
  nitroTimeoutSeconds: 30,
  verifySsl: false,
  enabledTools: [],
  sseEnabled: true
})

const mcpStatus = reactive({
  online: false,
  serverUrl: '',
  message: 'Checking…',
  toolCount: 0,
  enabledToolCount: 0
})

const passkeyRegistering = ref(false)
const passkeyMessage = ref('')
const passkeyMessageSeverity = ref('info')
const passkeyStatus = reactive({
  username: '',
  hasPasskey: false,
  passkeyCount: 0
})

async function loadPasskeyStatus() {
  const user = getStoredUser()
  if (!user?.username) return
  passkeyStatus.username = user.username
  try {
    const status = await fetchPasskeyStatus(user.username)
    passkeyStatus.hasPasskey = status.hasPasskey
    passkeyStatus.passkeyCount = status.hasPasskey ? 1 : 0
    const { data } = await api.get(`/users/${user.id}`)
    passkeyStatus.passkeyCount = data.passkeyCount || 0
    passkeyStatus.hasPasskey = passkeyStatus.passkeyCount > 0
  } catch {
    passkeyStatus.hasPasskey = false
    passkeyStatus.passkeyCount = 0
  }
}

async function registerMyPasskey() {
  const user = getStoredUser()
  if (!user?.username) return
  passkeyRegistering.value = true
  passkeyMessage.value = ''
  try {
    await registerPasskey(user.username)
    passkeyMessage.value = 'Passkey registered. You can use it on the login screen next time.'
    passkeyMessageSeverity.value = 'success'
    await loadPasskeyStatus()
  } catch (error) {
    passkeyMessage.value = passkeyErrorMessage(error)
    passkeyMessageSeverity.value = 'error'
  } finally {
    passkeyRegistering.value = false
  }
}

function saveCopilotPrefs() {
  saveCopilotSettings({ ...copilotSettings })
}

async function loadPlatformSettings() {
  try {
    const settings = await getCopilotPlatformSettings()
    Object.assign(platformSettings, {
      allowWebSearch: settings.allowWebSearch,
      hasBraveSearchApiKey: settings.hasBraveSearchApiKey,
      braveSearchApiKey: ''
    })
  } catch (error) {
    platformMessage.value = error.response?.data?.detail || 'Failed to load web search settings'
    platformMessageSeverity.value = 'error'
  }
}

async function savePlatformSettings() {
  platformSaving.value = true
  platformMessage.value = ''
  try {
    const payload = {
      allowWebSearch: platformSettings.allowWebSearch,
      braveSearchApiKey: platformSettings.braveSearchApiKey || null
    }
    const saved = await saveCopilotPlatformSettings(payload)
    Object.assign(platformSettings, {
      allowWebSearch: saved.allowWebSearch,
      hasBraveSearchApiKey: saved.hasBraveSearchApiKey,
      braveSearchApiKey: ''
    })
    platformMessage.value = 'Web search settings saved.'
    platformMessageSeverity.value = 'success'
  } catch (error) {
    platformMessage.value = error.response?.data?.detail || 'Failed to save web search settings'
    platformMessageSeverity.value = 'error'
  } finally {
    platformSaving.value = false
  }
}

async function testPlatformSearch() {
  platformTesting.value = true
  platformMessage.value = ''
  try {
    const result = await testCopilotPlatformSearch({
      allowWebSearch: platformSettings.allowWebSearch,
      braveSearchApiKey: platformSettings.braveSearchApiKey || null
    })
    platformMessage.value = result.message
    platformMessageSeverity.value = result.success ? 'success' : 'error'
  } catch (error) {
    platformMessage.value = error.response?.data?.detail || 'Brave Search test failed'
    platformMessageSeverity.value = 'error'
  } finally {
    platformTesting.value = false
  }
}

async function refreshMcpStatus() {
  try {
    const status = await getMcpStatus()
    Object.assign(mcpStatus, status)
  } catch (error) {
    mcpStatus.online = false
    mcpStatus.message = error.response?.data?.detail || error.message
  }
}

async function loadMcpConfig() {
  mcpLoading.value = true
  try {
    const config = await getMcpConfig()
    Object.assign(mcpSettings, {
      serverUrl: config.serverUrl,
      serverName: config.serverName,
      nitroTimeoutSeconds: config.nitroTimeoutSeconds,
      verifySsl: config.verifySsl,
      enabledTools: [...(config.enabledTools || [])],
      sseEnabled: config.sseEnabled
    })
    await refreshMcpStatus()
  } catch (error) {
    mcpMessage.value = error.response?.data?.detail || 'Failed to load MCP settings'
    mcpMessageSeverity.value = 'error'
  } finally {
    mcpLoading.value = false
  }
}

async function saveMcpSettings() {
  mcpSaving.value = true
  mcpMessage.value = ''
  try {
    await saveMcpConfig({ ...mcpSettings })
    mcpMessage.value = 'Settings saved and synced to the MCP server.'
    mcpMessageSeverity.value = 'success'
    await refreshMcpStatus()
  } catch (error) {
    mcpMessage.value = error.response?.data?.detail || 'Failed to save MCP settings'
    mcpMessageSeverity.value = 'error'
  } finally {
    mcpSaving.value = false
  }
}

async function testMcpConnection() {
  mcpTesting.value = true
  mcpMessage.value = ''
  try {
    await refreshMcpStatus()
    if (mcpStatus.online) {
      mcpMessage.value = `Connected — ${mcpStatus.enabledToolCount} tool(s) enabled.`
      mcpMessageSeverity.value = 'success'
    } else {
      mcpMessage.value = mcpStatus.message
      mcpMessageSeverity.value = 'error'
    }
  } finally {
    mcpTesting.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadMcpConfig(), loadPlatformSettings(), loadPasskeyStatus()])
})
</script>

<style scoped>
.page {
  animation: page-in 0.35s ease;
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
}

.section-copy {
  margin: 0.35rem 0 0;
  color: var(--p-text-muted-color);
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

.max-select {
  max-width: 8rem;
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
