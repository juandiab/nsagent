<template>
  <div class="page">
    <PageHeader
      title="Settings"
      subtitle="Platform configuration and preferences"
    />

    <div class="settings-layout">
      <!-- Section navigation -->
      <nav class="settings-nav" aria-label="Settings sections">
        <div class="settings-nav-list">
          <div
            v-for="group in navGroups"
            :key="group.id"
            class="settings-nav-cluster"
          >
            <span class="settings-nav-cluster-label">{{ group.label }}</span>
            <ul class="settings-nav-group-tabs">
              <li
                v-for="section in group.sections"
                :key="section.key"
                class="settings-nav-item"
                :class="{ 'is-active': activeSection === section.key }"
              >
                <a class="settings-nav-link" @click="selectSection(section.key)">
                  <i :class="[section.icon, 'settings-nav-icon']" />
                  <span>{{ section.label }}</span>
                </a>
              </li>
            </ul>
          </div>
        </div>
      </nav>

      <!-- Section content (KeepAlive avoids remounting panels and refetching APIs when switching tabs) -->
      <div class="settings-content">
        <KeepAlive>
          <div :key="activeSection" class="settings-section-panel">
          <section v-if="activeSection === 'mcp'" class="grid">
            <div class="col-12 lg:col-8 flex flex-column gap-4">
              <div class="content-panel content-panel-padded">
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
  
              <div class="content-panel content-panel-padded">
                <div class="flex align-items-start justify-content-between gap-3 flex-wrap">
                  <div>
                    <h2 class="section-title">SMTP / Email</h2>
                    <p class="section-copy">Outbound email server used for password resets and notifications.</p>
                  </div>
                  <Tag
                    :value="smtpSettings.hasPassword || smtpSettings.host ? 'Configured' : 'Not set up'"
                    :severity="smtpSettings.hasPassword || smtpSettings.host ? 'success' : 'secondary'"
                  />
                </div>
  
                <div v-if="smtpLoading" class="mt-4">
                  <ProgressSpinner style="width: 2rem; height: 2rem" />
                </div>
  
                <div v-else class="flex flex-column gap-4 mt-4">
                  <div class="flex flex-column gap-2 setting-row">
                    <label for="smtpProvider" class="setting-label">Provider</label>
                    <Select
                      id="smtpProvider"
                      v-model="smtpSettings.provider"
                      :options="smtpProviders"
                      option-label="label"
                      option-value="value"
                      @update:model-value="applySmtpProvider"
                    />
                    <small class="setting-hint">Pick a preset to fill the server details, or choose Custom to enter your own.</small>
                  </div>
  
                  <div class="flex flex-column gap-2 setting-row">
                    <label for="smtpHost" class="setting-label">SMTP host</label>
                    <InputText
                      id="smtpHost"
                      v-model="smtpSettings.host"
                      placeholder="smtp.example.com"
                      :disabled="isSmtpPreset"
                    />
                  </div>
  
                  <div class="flex flex-column gap-2 setting-row">
                    <label for="smtpPort" class="setting-label">Port</label>
                    <InputNumber
                      id="smtpPort"
                      v-model="smtpSettings.port"
                      :use-grouping="false"
                      :min="1"
                      :max="65535"
                      class="max-select"
                      :disabled="isSmtpPreset"
                    />
                  </div>
  
                  <div class="flex flex-column gap-2 setting-row">
                    <label for="smtpUsername" class="setting-label">Username</label>
                    <InputText
                      id="smtpUsername"
                      v-model="smtpSettings.username"
                      placeholder="you@example.com"
                    />
                  </div>
  
                  <div class="flex flex-column gap-2 setting-row">
                    <label for="smtpPassword" class="setting-label">Password</label>
                    <Password
                      id="smtpPassword"
                      v-model="smtpSettings.password"
                      class="w-full"
                      :feedback="false"
                      toggle-mask
                      input-class="w-full"
                      :placeholder="smtpSettings.hasPassword ? 'Saved — enter a new password to replace' : 'App password or SMTP password'"
                    />
                    <small class="setting-hint">
                      For Gmail/Outlook with 2FA, generate an app password. Stored encrypted on the backend.
                    </small>
                  </div>
  
                  <div class="flex flex-column gap-2 setting-row">
                    <label for="smtpFrom" class="setting-label">From address</label>
                    <InputText
                      id="smtpFrom"
                      v-model="smtpSettings.fromAddress"
                      placeholder="no-reply@example.com"
                    />
                    <small class="setting-hint">Leave blank to use the username as the sender.</small>
                  </div>
  
                  <div class="flex align-items-center justify-content-between gap-3 setting-row">
                    <div>
                      <div class="setting-label">Encryption</div>
                      <div class="setting-hint">STARTTLS (587) or implicit SSL/TLS (465).</div>
                    </div>
                    <SelectButton
                      v-model="smtpEncryption"
                      :options="smtpEncryptionOptions"
                      option-label="label"
                      option-value="value"
                      :allow-empty="false"
                      :disabled="isSmtpPreset"
                    />
                  </div>
  
                  <div class="flex flex-column gap-2 setting-row">
                    <label for="smtpTestRecipient" class="setting-label">Send test email to</label>
                    <InputText
                      id="smtpTestRecipient"
                      v-model="smtpTestRecipient"
                      placeholder="you@example.com"
                    />
                    <small class="setting-hint">A test message is sent here to confirm the settings work.</small>
                  </div>
  
                  <div class="flex gap-2 pt-2">
                    <Button
                      label="Save SMTP settings"
                      icon="pi pi-save"
                      size="small"
                      :loading="smtpSaving"
                      @click="saveSmtpSettings"
                    />
                    <Button
                      label="Send test email"
                      icon="pi pi-send"
                      size="small"
                      severity="secondary"
                      outlined
                      :loading="smtpTesting"
                      @click="testSmtpSettings"
                    />
                  </div>
  
                  <Message v-if="smtpMessage" :severity="smtpMessageSeverity" :closable="false">
                    {{ smtpMessage }}
                  </Message>
                </div>
              </div>
            </div>
  
            <div class="col-12 lg:col-4">
              <div class="content-panel content-panel-padded info-panel">
                <h3 class="info-title">MCP status</h3>
                <ul class="info-list m-0 pl-0 list-none">
                  <li><strong>URL:</strong> {{ mcpStatus.serverUrl || '—' }}</li>
                  <li><strong>Enabled tools:</strong> {{ mcpStatus.enabledToolCount }} / {{ mcpStatus.toolCount }}</li>
                  <li><strong>Status:</strong> {{ mcpStatus.message }}</li>
                </ul>
              </div>
            </div>
          </section>
  
          <!-- JPilot (attachments) -->
          <section v-if="activeSection === 'jpilot'" class="grid">
            <div class="col-12 lg:col-8 flex flex-column gap-4">
              <div class="content-panel content-panel-padded">
                <h2 class="section-title">Attachments</h2>
                <p class="section-copy">Control what can be attached to JPilot chat messages.</p>
  
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
            </div>
  
            <div class="col-12 lg:col-4">
              <div class="content-panel content-panel-padded info-panel">
                <h3 class="info-title">Attachment tips</h3>
                <ul class="info-list m-0 pl-3">
                  <li>Attach NetScaler configs for analysis or troubleshooting.</li>
                  <li>Attach screenshots of errors, dashboards, or topology diagrams.</li>
                  <li>Vision support depends on your default language model.</li>
                </ul>
              </div>
            </div>
          </section>
  
          <!-- AI Providers -->
          <section v-if="activeSection === 'ai-providers'" class="flex flex-column gap-4">
            <AIProvidersPanel />
            <BraveSearchPanel @usage-changed="refreshUsageDashboard" />
            <div class="content-panel content-panel-padded">
              <ModelUsageDashboard ref="usageDashboardRef" />
            </div>
          </section>
  
          <!-- Next-Gen API -->
          <section v-if="activeSection === 'nextgen'">
            <NextGenApiPanel />
          </section>
  
          <!-- Security -->
          <section v-if="activeSection === 'security'" class="grid">
            <div class="col-12 lg:col-8">
              <div class="content-panel content-panel-padded">
                <h2 class="section-title">Security</h2>
                <p class="section-copy">
                  Register a passkey for passwordless sign-in. Once a passkey is active, password sign-in is
                  disabled for your account. Use account recovery (email code) if you lose your device.
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
            </div>
          </section>
  
          <!-- Users (admin) -->
          <section v-if="activeSection === 'users'">
            <UsersPanel />
          </section>
  
          <!-- About / updates -->
          <section v-if="activeSection === 'about'">
            <UpdatesPanel @update-status="onUpdateStatus" />
          </section>
  
          <!-- Legal -->
          <section v-if="activeSection === 'legal'" class="grid">
            <div class="col-12 lg:col-8">
              <div class="content-panel content-panel-padded">
                <h2 class="section-title">Legal</h2>
                <p class="section-copy">Policies and agreements that govern your use of JPilot.</p>
  
                <ul class="legal-links mt-4">
                  <li>
                    <RouterLink to="/legal/privacy">
                      <i class="pi pi-shield" /> <span>Privacy Policy</span> <i class="pi pi-external-link" />
                    </RouterLink>
                  </li>
                  <li>
                    <RouterLink to="/legal/terms">
                      <i class="pi pi-file" /> <span>Terms of Service</span> <i class="pi pi-external-link" />
                    </RouterLink>
                  </li>
                  <li>
                    <RouterLink to="/legal/eula">
                      <i class="pi pi-key" /> <span>End-User License Agreement</span> <i class="pi pi-external-link" />
                    </RouterLink>
                  </li>
                  <li>
                    <RouterLink to="/legal/acceptable-use">
                      <i class="pi pi-check-circle" /> <span>Acceptable Use Policy</span> <i class="pi pi-external-link" />
                    </RouterLink>
                  </li>
                </ul>
  
                <p class="section-copy mt-4">© {{ new Date().getFullYear() }} Nexxus-Tech SAS · Bogotá D.C., Colombia · contact@nexxus-tech.com</p>
              </div>
            </div>
          </section>
          </div>
        </KeepAlive>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'
import ProgressSpinner from 'primevue/progressspinner'
import Select from 'primevue/select'
import SelectButton from 'primevue/selectbutton'
import Tag from 'primevue/tag'
import ToggleSwitch from 'primevue/toggleswitch'
import PageHeader from '../components/PageHeader.vue'
import ModelUsageDashboard from '../components/ModelUsageDashboard.vue'
import NextGenApiPanel from '../components/NextGenApiPanel.vue'
import AIProvidersPanel from '../components/AIProvidersPanel.vue'
import BraveSearchPanel from '../components/BraveSearchPanel.vue'
import UsersPanel from '../components/UsersPanel.vue'
import UpdatesPanel from '../components/UpdatesPanel.vue'
import { getCopilotSettings, saveCopilotSettings } from '../services/copilot'
import { getMcpConfig, getMcpStatus, saveMcpConfig } from '../services/mcp'
import { getSmtpConfig, saveSmtpConfig, testSmtpConfig } from '../services/smtp'
import api from '../services/api'
import { getStoredUser } from '../services/auth'
import { fetchPasskeyStatus, passkeyErrorMessage, registerPasskey } from '../services/webauthn'

const route = useRoute()
const router = useRouter()

const currentUser = ref(getStoredUser())
const isAdmin = computed(() => currentUser.value?.role === 'admin')

const GROUP_LABELS = {
  platform: 'Platform',
  people: 'People',
  personal: 'Personal',
  app: 'App'
}

const allSections = [
  { key: 'ai-providers', label: 'AI Providers', icon: 'pi pi-sparkles', adminOnly: true, group: 'platform' },
  { key: 'jpilot', label: 'JPilot', icon: 'pi pi-comments', adminOnly: true, group: 'platform' },
  { key: 'mcp', label: 'MCP Server', icon: 'pi pi-server', adminOnly: true, group: 'platform' },
  { key: 'nextgen', label: 'Next-Gen API', icon: 'pi pi-code', adminOnly: true, group: 'platform' },
  { key: 'users', label: 'Users', icon: 'pi pi-users', adminOnly: true, group: 'people' },
  { key: 'security', label: 'Security', icon: 'pi pi-shield', group: 'personal' },
  { key: 'about', label: 'About', icon: 'pi pi-info-circle', group: 'app' },
  { key: 'legal', label: 'Legal', icon: 'pi pi-book', group: 'app' }
]

const sections = computed(() =>
  allSections.filter((section) => !section.adminOnly || isAdmin.value)
)

const navGroups = computed(() => {
  const groups = []
  for (const section of sections.value) {
    const last = groups[groups.length - 1]
    if (last?.id === section.group) {
      last.sections.push(section)
    } else {
      groups.push({
        id: section.group,
        label: GROUP_LABELS[section.group] || section.group,
        sections: [section]
      })
    }
  }
  return groups
})

const defaultSection = computed(() => (isAdmin.value ? 'ai-providers' : 'security'))
const sectionKeys = computed(() => new Set(sections.value.map((section) => section.key)))
const activeSection = ref(defaultSection.value)

function applySectionFromQuery() {
  const section = route.query.section
  if (section === 'usage') {
    if (isAdmin.value) {
      activeSection.value = 'ai-providers'
    } else {
      activeSection.value = 'security'
      router.replace({ query: { section: 'security' } })
    }
    return
  }
  if (typeof section === 'string' && sectionKeys.value.has(section)) {
    activeSection.value = section
    return
  }
  if (typeof section === 'string' && section) {
    activeSection.value = defaultSection.value
    router.replace({ query: { section: defaultSection.value } })
    return
  }
  activeSection.value = defaultSection.value
}

function selectSection(key) {
  activeSection.value = key
  router.replace({ query: { ...route.query, section: key } })
}

watch(() => route.query.section, applySectionFromQuery)

const loadedSections = ref(new Set())

async function ensureSectionLoaded(section) {
  if (section === 'mcp' && !loadedSections.value.has('mcp')) {
    await Promise.all([loadMcpConfig(), loadSmtpSettings()])
    loadedSections.value.add('mcp')
  }
  if (section === 'security' && !loadedSections.value.has('security')) {
    await loadPasskeyStatus()
    loadedSections.value.add('security')
  }
}

function onUpdateStatus(info) {
  if (info?.update_available) {
    window.dispatchEvent(new CustomEvent('jpilot-update-available', { detail: info }))
  }
}

watch(activeSection, (section) => {
  ensureSectionLoaded(section)
})

applySectionFromQuery()

const maxAttachmentOptions = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
const copilotSettings = reactive(getCopilotSettings())

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

// ---- SMTP / email ----
const smtpProviders = [
  { label: 'Gmail', value: 'gmail' },
  { label: 'Outlook / Office 365', value: 'outlook' },
  { label: 'Custom', value: 'custom' }
]

const smtpPresets = {
  gmail: { host: 'smtp.gmail.com', port: 587, useTls: true, useSsl: false },
  outlook: { host: 'smtp.office365.com', port: 587, useTls: true, useSsl: false }
}

const smtpEncryptionOptions = [
  { label: 'STARTTLS', value: 'starttls' },
  { label: 'SSL/TLS', value: 'ssl' },
  { label: 'None', value: 'none' }
]

const smtpLoading = ref(true)
const smtpSaving = ref(false)
const smtpTesting = ref(false)
const smtpMessage = ref('')
const smtpMessageSeverity = ref('info')
const smtpTestRecipient = ref('')

const smtpSettings = reactive({
  provider: 'custom',
  host: '',
  port: 587,
  username: '',
  password: '',
  fromAddress: '',
  hasPassword: false,
  useTls: true,
  useSsl: false
})

const isSmtpPreset = computed(() => smtpSettings.provider !== 'custom')

const smtpEncryption = computed({
  get() {
    if (smtpSettings.useSsl) return 'ssl'
    if (smtpSettings.useTls) return 'starttls'
    return 'none'
  },
  set(value) {
    smtpSettings.useSsl = value === 'ssl'
    smtpSettings.useTls = value === 'starttls'
  }
})

function applySmtpProvider(provider) {
  const preset = smtpPresets[provider]
  if (preset) {
    smtpSettings.host = preset.host
    smtpSettings.port = preset.port
    smtpSettings.useTls = preset.useTls
    smtpSettings.useSsl = preset.useSsl
  }
}

const passkeyRegistering = ref(false)
const passkeyMessage = ref('')
const passkeyMessageSeverity = ref('info')
const usageDashboardRef = ref(null)

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

function refreshUsageDashboard() {
  usageDashboardRef.value?.refresh?.()
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

async function loadSmtpSettings() {
  smtpLoading.value = true
  try {
    const config = await getSmtpConfig()
    Object.assign(smtpSettings, {
      provider: config.provider || 'custom',
      host: config.host || '',
      port: config.port || 587,
      username: config.username || '',
      password: '',
      fromAddress: config.fromAddress || '',
      hasPassword: config.hasPassword || false,
      useTls: config.useTls,
      useSsl: config.useSsl
    })
  } catch (error) {
    smtpMessage.value = error.response?.data?.detail || 'Failed to load SMTP settings'
    smtpMessageSeverity.value = 'error'
  } finally {
    smtpLoading.value = false
  }
}

function smtpPayload() {
  return {
    provider: smtpSettings.provider,
    host: smtpSettings.host,
    port: smtpSettings.port,
    username: smtpSettings.username,
    password: smtpSettings.password || null,
    fromAddress: smtpSettings.fromAddress,
    useTls: smtpSettings.useTls,
    useSsl: smtpSettings.useSsl
  }
}

async function saveSmtpSettings() {
  smtpSaving.value = true
  smtpMessage.value = ''
  try {
    const saved = await saveSmtpConfig(smtpPayload())
    Object.assign(smtpSettings, {
      provider: saved.provider,
      host: saved.host,
      port: saved.port,
      username: saved.username,
      password: '',
      fromAddress: saved.fromAddress,
      hasPassword: saved.hasPassword,
      useTls: saved.useTls,
      useSsl: saved.useSsl
    })
    smtpMessage.value = 'SMTP settings saved.'
    smtpMessageSeverity.value = 'success'
  } catch (error) {
    smtpMessage.value = error.response?.data?.detail || 'Failed to save SMTP settings'
    smtpMessageSeverity.value = 'error'
  } finally {
    smtpSaving.value = false
  }
}

async function testSmtpSettings() {
  if (!smtpTestRecipient.value.trim()) {
    smtpMessage.value = 'Enter a recipient address to send the test email.'
    smtpMessageSeverity.value = 'warn'
    return
  }
  smtpTesting.value = true
  smtpMessage.value = ''
  try {
    const result = await testSmtpConfig({
      ...smtpPayload(),
      testRecipient: smtpTestRecipient.value.trim()
    })
    smtpMessage.value = result.message
    smtpMessageSeverity.value = result.success ? 'success' : 'error'
  } catch (error) {
    smtpMessage.value = error.response?.data?.detail || 'SMTP test failed'
    smtpMessageSeverity.value = 'error'
  } finally {
    smtpTesting.value = false
  }
}

onMounted(async () => {
  try {
    const { data } = await api.get('/auth/me')
    currentUser.value = data
  } catch {
    // Fall back to stored user from login.
  }
  applySectionFromQuery()
  await ensureSectionLoaded(activeSection.value)
})
</script>

<style scoped>
.page {
  animation: page-in 0.35s ease;
}

.settings-layout {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.settings-nav-icon {
  font-size: 1rem;
}

/* Horizontal scrollable tab bar */
.settings-nav {
  border-bottom: 1px solid var(--p-content-border-color);
  overflow-x: auto;
}

.settings-nav-list {
  display: flex;
  flex-direction: row;
  align-items: flex-end;
  gap: 0;
  min-width: min-content;
  padding-bottom: 0.15rem;
}

.settings-nav-cluster {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  flex-shrink: 0;
}

.settings-nav-cluster + .settings-nav-cluster {
  margin-left: 0.75rem;
  padding-left: 0.75rem;
  border-left: 1px solid var(--p-content-border-color);
}

.settings-nav-cluster-label {
  font-size: 0.625rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--p-text-muted-color);
  padding: 0 0.5rem;
  line-height: 1;
  opacity: 0.85;
}

.settings-nav-group-tabs {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: row;
  white-space: nowrap;
}

.settings-nav-item {
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}

.settings-nav-item.is-active {
  border-bottom-color: var(--p-primary-color);
}

.settings-nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  cursor: pointer;
  font-weight: 500;
  color: var(--p-text-muted-color);
  transition: color 0.15s ease;
}

.settings-nav-item.is-active .settings-nav-link {
  color: var(--p-primary-color);
}

.settings-nav-link:hover {
  color: var(--p-text-color);
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
}

.legal-links {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.legal-links a {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.65rem 0.75rem;
  border-radius: 0.5rem;
  text-decoration: none;
  color: var(--p-text-color);
  border: 1px solid transparent;
}

.legal-links a:hover {
  background: var(--app-nested-surface);
  border-color: var(--p-content-border-color);
}

.legal-links a span {
  flex: 1;
  font-weight: 500;
}

.legal-links a .pi-external-link {
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
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
