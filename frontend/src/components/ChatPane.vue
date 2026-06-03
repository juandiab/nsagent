<template>
  <div class="chat-pane flex flex-column flex-1" :class="{ 'pane-empty': !session.messages.length }">
    <!-- shared hidden file inputs + attach menu -->
    <input
      ref="imageInputRef"
      type="file"
      accept="image/png,image/jpeg,image/webp,image/gif"
      multiple
      hidden
      @change="onImageSelected"
    />
    <input ref="configInputRef" type="file" :accept="configAccept" multiple hidden @change="onConfigSelected" />
    <Menu ref="attachMenu" :model="attachMenuItems" popup />

    <div class="pane-toolbar">
      <Select
        v-model="session.applianceChoice"
        :options="appliances"
        option-label="name"
        option-value="name"
        placeholder="Appliance"
        class="pane-select"
        :disabled="loading || connecting"
        @change="onApplianceChange"
      />
      <Select
        v-model="session.providerId"
        :options="providerOptions"
        option-label="label"
        option-value="value"
        placeholder="Model"
        class="pane-select pane-select-model"
        :disabled="loading || !providerOptions.length"
      />
      <span class="pane-spacer" />
      <span
        v-if="session.connectedAppliance"
        v-tooltip.bottom="'Connected via Next-Gen API'"
        class="pane-connected"
      >
        <i class="pi pi-check-circle" /> {{ session.connectedAppliance }}
      </span>
      <Button
        v-if="webSearchAvailable"
        v-tooltip.bottom="session.webSearch ? 'Web search: on (official domains, only when docs fall short). Click to disable.' : 'Web search: off for this chat. Click to enable.'"
        :icon="session.webSearch ? 'pi pi-globe' : 'pi pi-ban'"
        text
        rounded
        size="small"
        :class="{ 'websearch-off': !session.webSearch }"
        @click="session.webSearch = !session.webSearch"
      />
      <Button
        v-if="session.messages.length"
        v-tooltip.bottom="'Clear conversation'"
        icon="pi pi-eraser"
        text
        rounded
        size="small"
        :disabled="loading"
        @click="clearConversation"
      />
      <Button
        v-if="canClose"
        v-tooltip.bottom="'Close chat'"
        icon="pi pi-times"
        text
        rounded
        size="small"
        @click="$emit('close')"
      />
    </div>

    <!-- EMPTY STATE: glass command-menu "ask" panel -->
    <div v-if="!session.messages.length" class="ask-hero">
      <div class="glass-card">
        <div class="glass-head">
          <i class="pi pi-sparkles" />
          <span>Ask JPilot</span>
        </div>
        <div class="glass-input">
          <i class="pi pi-search glass-input-icon" />
          <input
            v-model="session.input"
            type="text"
            class="glass-input-field"
            placeholder="Ask about your NetScalers, run a check, request a change..."
            :disabled="loading || !ready"
            @keydown.enter.prevent="sendMessage()"
          />
          <button
            class="glass-attach"
            type="button"
            :disabled="loading || !ready"
            @click="toggleAttachMenu"
          >
            <i class="pi pi-paperclip" />
          </button>
          <span class="kbd">⏎</span>
        </div>

        <div v-if="pendingAttachments.length" class="pending-attachments glass-pending">
          <div v-for="(a, i) in pendingAttachments" :key="i" class="pending-attachment">
            <img v-if="a.kind === 'image'" :src="attachmentPreviewUrl(a)" :alt="a.name" class="pending-thumb" />
            <i v-else class="pi pi-file" />
            <span class="pending-name">{{ a.name }}</span>
            <Button icon="pi pi-times" text rounded size="small" @click="removeAttachment(i)" />
          </div>
        </div>

        <div class="glass-recommended">
          <p class="glass-recommended-intro">Recommended actions</p>
          <div
            v-for="group in recommendedGroups"
            :key="group.id"
            class="glass-prompt-group"
          >
            <div class="glass-prompt-group-title">{{ group.title }}</div>
            <div class="glass-prompts">
              <button
                v-for="action in group.actions"
                :key="action.id"
                class="glass-prompt"
                :disabled="!ready && action.type === 'prompt'"
                @click="runRecommendedAction(action)"
              >
                <i :class="action.icon" />
                <span>{{ action.label }}</span>
                <i v-if="action.type === 'link'" class="pi pi-arrow-right glass-prompt-link" />
              </button>
            </div>
          </div>
        </div>

        <p v-if="!ready" class="glass-hint">No enabled language model — configure one in Settings → AI Providers.</p>
      </div>
    </div>

    <!-- ACTIVE CONVERSATION -->
    <template v-else>
      <div ref="messagesEl" class="chat-messages flex-1">
        <div
          v-for="(msg, index) in session.messages"
          :key="index"
          class="chat-message"
          :class="msg.role === 'user' ? 'chat-message-user' : 'chat-message-assistant'"
        >
          <div class="chat-bubble">
            <div class="chat-role">{{ msg.role === 'user' ? 'You' : 'JPilot' }}</div>
            <div v-if="msg.attachments?.length" class="chat-attachments mb-2">
              <div v-for="(a, ai) in msg.attachments" :key="ai" class="attachment-chip">
                <img v-if="a.kind === 'image' && a.data" :src="attachmentPreviewUrl(a)" :alt="a.name" class="attachment-thumb" />
                <i v-else class="pi pi-file" />
                <span>{{ a.name }}</span>
              </div>
            </div>
            <div v-if="assistantView(msg).content && msg.role === 'assistant'" :class="{ 'chat-error-block': msg.isError }">
              <ChatMarkdown :content="assistantView(msg).content" />
            </div>
            <div v-else-if="msg.content" class="chat-content">{{ msg.content }}</div>
            <div v-if="msg.webSources?.length" class="web-sources">
              <span class="web-badge" v-tooltip.top="'This reply used live web results from allowed domains'">
                <i class="pi pi-globe" /> Web
              </span>
              <a
                v-for="src in msg.webSources"
                :key="src.url"
                :href="src.url"
                target="_blank"
                rel="noopener noreferrer"
                class="web-source-link"
                :title="src.title"
              >
                {{ hostOf(src.url) }}
              </a>
            </div>
            <ChatAppliancePicker
              v-if="msg.appliancePicker"
              :appliances="msg.appliances || []"
              :loading="msg.pickerLoading"
              :connecting="connecting"
              @select="connectAppliance"
            />
            <ChatConfigForm
              v-if="assistantView(msg).inputForm && !assistantView(msg).formSubmitted"
              :form="assistantView(msg).inputForm"
              :submitting="loading && submittingFormIndex === index"
              @submit="(values) => submitConfigForm(values, index)"
            />
            <ChatToolTrace v-if="msg.toolCalls?.length" :tools="msg.toolCalls" />
          </div>
        </div>

        <div v-if="loading" class="chat-message chat-message-assistant">
          <div class="chat-bubble chat-bubble-loading">
            <ProgressSpinner style="width: 1.25rem; height: 1.25rem" stroke-width="4" />
            <span>Thinking...</span>
          </div>
        </div>
      </div>

      <div v-if="pendingAttachments.length" class="pending-attachments">
        <div v-for="(a, i) in pendingAttachments" :key="i" class="pending-attachment">
          <img v-if="a.kind === 'image'" :src="attachmentPreviewUrl(a)" :alt="a.name" class="pending-thumb" />
          <i v-else class="pi pi-file" />
          <span class="pending-name">{{ a.name }}</span>
          <Button icon="pi pi-times" text rounded size="small" @click="removeAttachment(i)" />
        </div>
      </div>

      <div class="chat-input-bar">
        <Button
          v-tooltip.top="'Attach file'"
          icon="pi pi-paperclip"
          text
          rounded
          :disabled="loading || !ready"
          @click="toggleAttachMenu"
        />
        <Textarea
          v-model="session.input"
          rows="2"
          auto-resize
          class="chat-input flex-1"
          placeholder="Ask about your NetScalers, attach configs or images..."
          :disabled="loading || !ready"
          @keydown.enter.exact.prevent="sendMessage()"
        />
        <Button
          icon="pi pi-send"
          :loading="loading"
          :disabled="(!session.input.trim() && !pendingAttachments.length) || !ready"
          @click="sendMessage()"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import Menu from 'primevue/menu'
import ProgressSpinner from 'primevue/progressspinner'
import Select from 'primevue/select'
import Textarea from 'primevue/textarea'
import ChatAppliancePicker from './ChatAppliancePicker.vue'
import ChatConfigForm from './ChatConfigForm.vue'
import ChatMarkdown from './ChatMarkdown.vue'
import ChatToolTrace from './ChatToolTrace.vue'
import api from '../services/api'
import { formatCopilotError, isProviderQuotaError } from '../utils/chatErrors'
import {
  CONFIG_ACCEPT,
  attachmentPreviewUrl,
  connectCopilotAppliance,
  fileToAttachment,
  getCopilotSettings,
  listCopilotAppliances
} from '../services/copilot'
import { parseInputFormFromContent, resolveAssistantMessage } from '../utils/copilotForm'
import { clearSession, getSession } from '../stores/copilotSessions'
import { jpilotRecommendedGroups } from '../config/jpilotRecommendedActions'

const props = defineProps({
  sessionId: { type: String, required: true },
  providers: { type: Array, default: () => [] },
  appliances: { type: Array, default: () => [] },
  defaultProviderId: { type: String, default: '' },
  webSearchAvailable: { type: Boolean, default: false },
  canClose: { type: Boolean, default: false }
})

defineEmits(['close'])

const router = useRouter()
const toast = useToast()

// Persistent per-pane state (survives unmount / pane switches / reload).
const session = getSession(props.sessionId)

// Transient UI state — fine to reset on remount.
const loading = ref(false)
const connecting = ref(false)
const submittingFormIndex = ref(null)
const messagesEl = ref(null)
const pendingAttachments = ref([])
const imageInputRef = ref(null)
const configInputRef = ref(null)
const attachMenu = ref(null)

const configAccept = CONFIG_ACCEPT
const recommendedGroups = jpilotRecommendedGroups

const ready = computed(() => props.providers.length > 0)
const providerOptions = computed(() =>
  props.providers.map((p) => ({ label: `${p.providerName} · ${p.model}`, value: p.id }))
)

// Default the model once providers load, if this pane hasn't chosen one.
watch(
  () => props.defaultProviderId,
  (id) => {
    if (id && !session.providerId) session.providerId = id
  },
  { immediate: true }
)

const attachMenuItems = computed(() => {
  const settings = getCopilotSettings()
  const items = []
  if (settings.allowImages) {
    items.push({ label: 'Attach image', icon: 'pi pi-image', command: () => imageInputRef.value?.click() })
  }
  if (settings.allowConfigFiles) {
    items.push({ label: 'Attach config file', icon: 'pi pi-file', command: () => configInputRef.value?.click() })
  }
  if (!items.length) {
    items.push({ label: 'Attachments disabled — open Settings', icon: 'pi pi-cog', command: () => router.push('/settings') })
  }
  return items
})

function toggleAttachMenu(event) {
  attachMenu.value.toggle(event)
}

function runRecommendedAction(action) {
  if (action.type === 'link') {
    router.push(action.to)
    return
  }
  if (!ready.value) return
  sendMessage(action.text)
}

async function addFiles(fileList) {
  const settings = getCopilotSettings()
  const files = Array.from(fileList || [])
  if (!files.length) return
  if (pendingAttachments.value.length + files.length > settings.maxAttachments) {
    toast.add({ severity: 'warn', summary: 'Too many attachments', detail: `Maximum ${settings.maxAttachments} attachments per message`, life: 3000 })
    return
  }
  for (const file of files) {
    try {
      const attachment = await fileToAttachment(file)
      if (attachment.kind === 'image' && !settings.allowImages) throw new Error('Image attachments are disabled in Settings')
      if (attachment.kind === 'config' && !settings.allowConfigFiles) throw new Error('Config file attachments are disabled in Settings')
      pendingAttachments.value.push(attachment)
    } catch (error) {
      toast.add({ severity: 'error', summary: 'Attachment failed', detail: error.message, life: 4000 })
    }
  }
}

function onImageSelected(event) {
  addFiles(event.target.files)
  event.target.value = ''
}

function onConfigSelected(event) {
  addFiles(event.target.files)
  event.target.value = ''
}

function removeAttachment(index) {
  pendingAttachments.value.splice(index, 1)
}

function clearConversation() {
  clearSession(props.sessionId)
  pendingAttachments.value = []
}

const WEB_SEARCH_TOOLS = ['search_netscaler_nextgen_api', 'search_netscaler_cli_reference']

// Extract the external URLs that actually informed a reply (auditable provenance).
function extractWebSources(toolCalls) {
  const sources = []
  const seen = new Set()
  for (const tc of toolCalls || []) {
    if (!WEB_SEARCH_TOOLS.includes(tc.name)) continue
    let data
    try {
      data = JSON.parse(tc.result)
    } catch {
      continue
    }
    for (const r of data?.webResults?.results || []) {
      if (r.url && !seen.has(r.url)) {
        seen.add(r.url)
        sources.push({ title: r.title || r.url, url: r.url })
      }
    }
  }
  return sources
}

function assistantView(msg) {
  if (msg.role !== 'assistant') {
    return { content: msg.content, inputForm: null, formSubmitted: false }
  }
  return resolveAssistantMessage(msg)
}

function hostOf(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}

async function scrollToBottom() {
  await nextTick()
  if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
}

function onApplianceChange() {
  if (session.applianceChoice) connectAppliance({ name: session.applianceChoice })
}

async function showAppliancePicker() {
  const pickerIndex = session.messages.length
  session.messages.push({ role: 'assistant', content: '', appliancePicker: true, appliances: [], pickerLoading: true })
  await scrollToBottom()
  try {
    const appliances = await listCopilotAppliances()
    if (session.messages[pickerIndex]) {
      session.messages[pickerIndex].appliances = appliances
      session.messages[pickerIndex].pickerLoading = false
      session.messages[pickerIndex].content = appliances.length
        ? 'Choose a NetScaler from your inventory:'
        : 'No NetScalers found. Add one in the inventory first.'
    }
  } catch (error) {
    if (session.messages[pickerIndex]) {
      session.messages[pickerIndex].pickerLoading = false
      session.messages[pickerIndex].content = error.response?.data?.detail || 'Failed to load NetScalers from inventory.'
    }
  }
  await scrollToBottom()
}

async function connectAppliance(appliance) {
  connecting.value = true
  try {
    const result = await connectCopilotAppliance(appliance.name)
    session.connectedAppliance = result.applianceName
    session.applianceChoice = result.applianceName
    session.messages.push({
      role: 'assistant',
      content: `${result.message}\n\nAuthenticated as **${result.authenticatedUser}** via \`${result.loginEndpoint}\`.`
    })
    const queued = session.pendingMessage
    const queuedAttachments = session.pendingAttachmentsSnapshot
    session.pendingMessage = null
    session.pendingAttachmentsSnapshot = []
    if (queued || queuedAttachments.length) await runChat(queued, queuedAttachments)
  } catch (error) {
    session.messages.push({
      role: 'assistant',
      content: `Next-Gen API login failed for **${appliance.name}**: ${error.response?.data?.detail || error.message}`
    })
  } finally {
    connecting.value = false
    await scrollToBottom()
  }
}

async function runChat(content, attachments) {
  loading.value = true
  await scrollToBottom()
  try {
    const conversational = session.messages.filter(
      (msg) => (msg.role === 'user' || msg.role === 'assistant') && msg.content && !msg.appliancePicker
    )
    let history = conversational.map((msg) => ({ role: msg.role, content: msg.content }))
    if (history.length && history[history.length - 1].role === 'user' && history[history.length - 1].content === content) {
      history = history.slice(0, -1)
    }
    const { data } = await api.post('/copilot/chat', {
      message: content,
      history,
      attachments,
      settings: getCopilotSettings(),
      applianceName: session.connectedAppliance,
      providerId: session.providerId || undefined,
      webSearch: session.webSearch !== false
    })
    const parsed = parseInputFormFromContent(data.content || '')
    session.messages.push({
      role: 'assistant',
      content: parsed.content,
      toolCalls: data.toolCalls,
      webSources: extractWebSources(data.toolCalls),
      inputForm: data.inputForm || parsed.inputForm
    })
  } catch (error) {
    const content = formatCopilotError(error)
    session.messages.push({
      role: 'assistant',
      content,
      isError: true,
      providerQuotaError: isProviderQuotaError(error)
    })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

async function submitConfigForm(values, messageIndex) {
  const msg = session.messages[messageIndex]
  const view = resolveAssistantMessage(msg)
  if (!view.inputForm || view.formSubmitted || loading.value) return

  const lines = [`Configuration inputs for: ${view.inputForm.title}`]
  for (const field of view.inputForm.fields) {
    const value = values[field.id]
    const rendered =
      field.type === 'boolean' ? (value ? 'yes' : 'no') : String(value ?? '').trim() || '(not provided)'
    lines.push(`- ${field.label}: ${rendered}`)
  }
  lines.push('', 'Proceed with the configuration using these values.')

  msg.formSubmitted = true
  submittingFormIndex.value = messageIndex
  try {
    await sendMessage(lines.join('\n'))
  } finally {
    submittingFormIndex.value = null
  }
}

async function sendMessage(text) {
  const content = (text || session.input).trim()
  const attachments = pendingAttachments.value.map((item) => ({
    name: item.name,
    kind: item.kind,
    mimeType: item.mimeType,
    data: item.data
  }))
  if ((!content && !attachments.length) || loading.value || !ready.value) return

  session.messages.push({ role: 'user', content, attachments: attachments.map((item) => ({ ...item })) })
  session.input = ''
  pendingAttachments.value = []
  await scrollToBottom()

  if (!session.connectedAppliance) {
    session.pendingMessage = content
    session.pendingAttachmentsSnapshot = attachments
    await showAppliancePicker()
    return
  }
  await runChat(content, attachments)
}

onMounted(scrollToBottom)
</script>

<style scoped>
.chat-pane {
  --glass-bg: rgba(255, 255, 255, 0.66);
  --glass-strong: rgba(255, 255, 255, 0.8);
  --glass-border: rgba(15, 23, 42, 0.1);
  --glass-text: var(--p-text-color);
  --glass-muted: var(--p-text-muted-color);
  --glass-field: rgba(15, 23, 42, 0.04);
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: 1rem;
  overflow: hidden;
  min-height: 0;
  backdrop-filter: blur(18px) saturate(140%);
  -webkit-backdrop-filter: blur(18px) saturate(140%);
  box-shadow: 0 12px 40px rgba(2, 6, 23, 0.12);
}

:global(.app-dark) .chat-pane {
  --glass-bg: rgba(17, 21, 32, 0.55);
  --glass-strong: rgba(24, 29, 43, 0.78);
  --glass-border: rgba(255, 255, 255, 0.12);
  --glass-field: rgba(255, 255, 255, 0.06);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.45);
}

.pane-toolbar {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 0.75rem;
  border-bottom: 1px solid var(--glass-border);
}

.pane-select {
  min-width: 9rem;
}

.pane-select-model {
  min-width: 11rem;
}

.pane-spacer {
  flex: 1;
}

.pane-connected {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8125rem;
  color: var(--p-primary-color);
  white-space: nowrap;
}

.pane-connected i {
  color: var(--p-green-500);
}

/* ---------- Empty state: glass command menu ---------- */
.ask-hero {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  min-height: 0;
}

.glass-card {
  width: min(34rem, 100%);
  background: var(--glass-strong);
  border: 1px solid var(--glass-border);
  border-radius: 1rem;
  padding: 1.25rem;
  box-shadow: 0 18px 50px rgba(2, 6, 23, 0.18);
}

.glass-head {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: var(--glass-text);
  margin-bottom: 0.9rem;
}

.glass-head i {
  color: var(--p-primary-color);
}

.glass-input {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 0.75rem;
  border: 1px solid var(--glass-border);
  border-radius: 0.75rem;
  background: var(--glass-field);
}

.glass-input-icon {
  color: var(--glass-muted);
}

.glass-input-field {
  flex: 1;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--glass-text);
  font-size: 0.95rem;
}

.glass-input-field::placeholder {
  color: var(--glass-muted);
}

.glass-attach {
  border: 0;
  background: transparent;
  color: var(--glass-muted);
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 0.4rem;
}

.glass-attach:hover:not(:disabled) {
  color: var(--glass-text);
}

.kbd {
  font-size: 0.75rem;
  color: var(--glass-muted);
  border: 1px solid var(--glass-border);
  border-radius: 0.4rem;
  padding: 0.05rem 0.4rem;
}

.glass-recommended {
  margin-top: 1rem;
  max-height: min(24rem, 42vh);
  overflow-y: auto;
  padding-right: 0.25rem;
}

.glass-recommended-intro {
  margin: 0 0 0.75rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--glass-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.glass-prompt-group + .glass-prompt-group {
  margin-top: 0.85rem;
}

.glass-prompt-group-title {
  margin-bottom: 0.35rem;
  padding: 0 0.7rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--glass-muted);
}

.glass-prompts {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.glass-prompt {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.55rem 0.7rem;
  border: 0;
  border-radius: 0.6rem;
  background: transparent;
  color: var(--glass-text);
  font-size: 0.875rem;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s ease;
}

.glass-prompt span {
  flex: 1;
}

.glass-prompt-link {
  font-size: 0.75rem;
  color: var(--glass-muted);
  margin-left: auto;
}

.glass-prompt:hover:not(:disabled) {
  background: var(--glass-field);
}

.glass-prompt:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.glass-prompt > i:first-child {
  color: var(--p-primary-color);
  flex-shrink: 0;
}

.glass-pending {
  margin-top: 0.75rem;
}

.glass-hint {
  margin: 0.9rem 0 0;
  font-size: 0.8125rem;
  color: var(--glass-muted);
}

/* ---------- Active conversation ---------- */
.chat-messages {
  overflow-y: auto;
  padding: 1.25rem;
}

.chat-message {
  display: flex;
  margin-bottom: 1rem;
}

.chat-message-user {
  justify-content: flex-end;
}

.chat-message-assistant {
  justify-content: flex-start;
}

.chat-bubble {
  max-width: min(44rem, 92%);
  padding: 0.875rem 1rem;
  border-radius: 0.875rem;
  border: 1px solid var(--glass-border);
  background: var(--glass-strong);
  color: var(--glass-text);
}

.chat-message-user .chat-bubble {
  background: color-mix(in srgb, var(--p-primary-color) 16%, var(--glass-strong));
}

.chat-error-block {
  border-left: 3px solid var(--p-orange-500);
  padding-left: 0.75rem;
}

.chat-bubble-loading {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--glass-muted);
}

.chat-role {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--glass-muted);
  margin-bottom: 0.35rem;
}

.chat-content {
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: 0.9375rem;
}

.web-sources {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
  margin-top: 0.6rem;
  padding-top: 0.5rem;
  border-top: 1px dashed var(--glass-border);
}

.web-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--p-primary-color);
  background: color-mix(in srgb, var(--p-primary-color) 14%, transparent);
  border: 1px solid color-mix(in srgb, var(--p-primary-color) 30%, transparent);
  border-radius: 999px;
  padding: 0.1rem 0.45rem;
}

.web-source-link {
  font-size: 0.75rem;
  color: var(--glass-muted);
  text-decoration: none;
  border: 1px solid var(--glass-border);
  border-radius: 0.4rem;
  padding: 0.1rem 0.4rem;
}

.web-source-link:hover {
  color: var(--p-primary-color);
  border-color: var(--p-primary-color);
}

.chat-attachments,
.pending-attachments {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.pending-attachments {
  padding: 0.75rem 1rem 0;
  border-top: 1px solid var(--glass-border);
}

.attachment-chip,
.pending-attachment {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.5rem;
  border-radius: 0.5rem;
  background: var(--glass-field);
  border: 1px solid var(--glass-border);
  font-size: 0.8125rem;
  color: var(--glass-text);
}

.attachment-thumb,
.pending-thumb {
  width: 2rem;
  height: 2rem;
  object-fit: cover;
  border-radius: 0.25rem;
}

.pending-name {
  max-width: 12rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-input-bar {
  display: flex;
  gap: 0.75rem;
  align-items: flex-end;
  padding: 1rem;
  border-top: 1px solid var(--glass-border);
}

.chat-input {
  resize: none;
  background: var(--glass-field);
}
</style>
