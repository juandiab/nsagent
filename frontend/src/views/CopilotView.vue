<template>
  <div class="page copilot-page flex flex-column">
    <PageHeader title="Copilot" :subtitle="statusSubtitle">
      <template #actions>
        <Button
          v-tooltip.top="'Copilot settings'"
          icon="pi pi-cog"
          text
          rounded
          @click="router.push('/settings')"
        />
      </template>
    </PageHeader>

    <Message v-if="!status.ready" severity="warn" :closable="false" class="mb-3">
      {{ status.message }}
      <RouterLink to="/ai-providers" class="ml-2">Configure AI Providers →</RouterLink>
    </Message>

    <div v-if="connectedAppliance" class="connected-banner mb-3">
      <div class="connected-info">
        <i class="pi pi-check-circle" />
        <span>Connected to <strong>{{ connectedAppliance }}</strong> via Next-Gen API</span>
      </div>
      <Button label="Change" size="small" text @click="disconnectAppliance" />
    </div>

    <div class="chat-panel flex flex-column flex-1">
      <div ref="messagesEl" class="chat-messages flex-1">
        <div v-if="!messages.length" class="chat-empty">
          <i class="pi pi-sparkles chat-empty-icon" />
          <h2>NetScaler Copilot</h2>
          <p>Ask about appliances, attach configs, or upload screenshots for analysis.</p>
          <div class="flex flex-wrap gap-2 justify-content-center mt-4">
            <Button
              v-for="prompt in starterPrompts"
              :key="prompt"
              :label="prompt"
              size="small"
              outlined
              @click="sendMessage(prompt)"
            />
          </div>
        </div>

        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="chat-message"
          :class="msg.role === 'user' ? 'chat-message-user' : 'chat-message-assistant'"
        >
          <div class="chat-bubble">
            <div class="chat-role">{{ msg.role === 'user' ? 'You' : 'Copilot' }}</div>
            <div v-if="msg.attachments?.length" class="chat-attachments mb-2">
              <div
                v-for="(attachment, attachmentIndex) in msg.attachments"
                :key="attachmentIndex"
                class="attachment-chip"
              >
                <img
                  v-if="attachment.kind === 'image'"
                  :src="attachmentPreviewUrl(attachment)"
                  :alt="attachment.name"
                  class="attachment-thumb"
                />
                <i v-else class="pi pi-file" />
                <span>{{ attachment.name }}</span>
              </div>
            </div>
            <ChatMarkdown v-if="msg.content && msg.role === 'assistant'" :content="msg.content" />
            <div v-else-if="msg.content" class="chat-content">{{ msg.content }}</div>
            <ChatAppliancePicker
              v-if="msg.appliancePicker"
              :appliances="msg.appliances || []"
              :loading="msg.pickerLoading"
              :connecting="connectingAppliance"
              @select="connectAppliance"
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
        <div
          v-for="(attachment, index) in pendingAttachments"
          :key="index"
          class="pending-attachment"
        >
          <img
            v-if="attachment.kind === 'image'"
            :src="attachmentPreviewUrl(attachment)"
            :alt="attachment.name"
            class="pending-thumb"
          />
          <i v-else class="pi pi-file" />
          <span class="pending-name">{{ attachment.name }}</span>
          <Button icon="pi pi-times" text rounded size="small" @click="removeAttachment(index)" />
        </div>
      </div>

      <div class="chat-input-bar">
        <input
          ref="imageInputRef"
          type="file"
          accept="image/png,image/jpeg,image/webp,image/gif"
          multiple
          hidden
          @change="onImageSelected"
        />
        <input
          ref="configInputRef"
          type="file"
          :accept="configAccept"
          multiple
          hidden
          @change="onConfigSelected"
        />

        <Button
          v-tooltip.top="'Attach file'"
          icon="pi pi-paperclip"
          text
          rounded
          :disabled="loading || !status.ready"
          @click="toggleAttachMenu"
        />
        <Menu ref="attachMenu" :model="attachMenuItems" popup />

        <Textarea
          v-model="input"
          rows="2"
          auto-resize
          class="chat-input flex-1"
          placeholder="Ask about your NetScalers, attach configs or images..."
          :disabled="loading || !status.ready"
          @keydown.enter.exact.prevent="sendMessage()"
        />
        <Button
          icon="pi pi-send"
          :loading="loading"
          :disabled="(!input.trim() && !pendingAttachments.length) || !status.ready"
          @click="sendMessage()"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import Menu from 'primevue/menu'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import Textarea from 'primevue/textarea'
import PageHeader from '../components/PageHeader.vue'
import ChatAppliancePicker from '../components/ChatAppliancePicker.vue'
import ChatMarkdown from '../components/ChatMarkdown.vue'
import ChatToolTrace from '../components/ChatToolTrace.vue'
import api from '../services/api'
import {
  CONFIG_ACCEPT,
  attachmentPreviewUrl,
  connectCopilotAppliance,
  fileToAttachment,
  getConnectedAppliance,
  getCopilotSettings,
  listCopilotAppliances,
  setConnectedAppliance
} from '../services/copilot'

const router = useRouter()
const toast = useToast()

const messages = ref([])
const input = ref('')
const loading = ref(false)
const messagesEl = ref(null)
const status = ref({ ready: false, message: 'Loading...' })
const pendingAttachments = ref([])
const imageInputRef = ref(null)
const configInputRef = ref(null)
const attachMenu = ref(null)
const connectedAppliance = ref(getConnectedAppliance())
const connectingAppliance = ref(false)
const pendingMessage = ref(null)
const pendingAttachmentsSnapshot = ref([])

const configAccept = CONFIG_ACCEPT

const starterPrompts = [
  'Show firmware version',
  'Show the IP address',
  'What applications are configured?'
]

const attachMenuItems = computed(() => {
  const settings = getCopilotSettings()
  const items = []
  if (settings.allowImages) {
    items.push({
      label: 'Attach image',
      icon: 'pi pi-image',
      command: () => imageInputRef.value?.click()
    })
  }
  if (settings.allowConfigFiles) {
    items.push({
      label: 'Attach config file',
      icon: 'pi pi-file',
      command: () => configInputRef.value?.click()
    })
  }
  if (!items.length) {
    items.push({
      label: 'Attachments disabled — open Settings',
      icon: 'pi pi-cog',
      command: () => router.push('/settings')
    })
  }
  return items
})

const statusSubtitle = computed(() => {
  if (!status.value.ready) return 'Configure a default AI provider to start'
  return `${status.value.providerName} · ${status.value.model}`
})

function toggleAttachMenu(event) {
  attachMenu.value.toggle(event)
}

async function addFiles(fileList) {
  const settings = getCopilotSettings()
  const files = Array.from(fileList || [])
  if (!files.length) return

  if (pendingAttachments.value.length + files.length > settings.maxAttachments) {
    toast.add({
      severity: 'warn',
      summary: 'Too many attachments',
      detail: `Maximum ${settings.maxAttachments} attachments per message`,
      life: 3000
    })
    return
  }

  for (const file of files) {
    try {
      const attachment = await fileToAttachment(file)
      if (attachment.kind === 'image' && !settings.allowImages) {
        throw new Error('Image attachments are disabled in Settings')
      }
      if (attachment.kind === 'config' && !settings.allowConfigFiles) {
        throw new Error('Config file attachments are disabled in Settings')
      }
      pendingAttachments.value.push(attachment)
    } catch (error) {
      toast.add({
        severity: 'error',
        summary: 'Attachment failed',
        detail: error.message,
        life: 4000
      })
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

async function scrollToBottom() {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

async function loadStatus() {
  try {
    const { data } = await api.get('/copilot/status')
    status.value = data
  } catch {
    status.value = { ready: false, message: 'Failed to load Copilot status' }
  }
}

function disconnectAppliance() {
  connectedAppliance.value = ''
  setConnectedAppliance('')
  pendingMessage.value = null
}

async function showAppliancePicker() {
  const pickerIndex = messages.value.length
  messages.value.push({
    role: 'assistant',
    content: '',
    appliancePicker: true,
    appliances: [],
    pickerLoading: true
  })
  await scrollToBottom()

  try {
    const appliances = await listCopilotAppliances()
    if (messages.value[pickerIndex]) {
      messages.value[pickerIndex].appliances = appliances
      messages.value[pickerIndex].pickerLoading = false
      messages.value[pickerIndex].content = appliances.length
        ? 'Choose a NetScaler from your inventory:'
        : 'No NetScalers found. Add one in the inventory first.'
    }
  } catch (error) {
    if (messages.value[pickerIndex]) {
      messages.value[pickerIndex].pickerLoading = false
      messages.value[pickerIndex].content =
        error.response?.data?.detail || 'Failed to load NetScalers from inventory.'
    }
  }
  await scrollToBottom()
}

async function connectAppliance(appliance) {
  connectingAppliance.value = true
  try {
    const result = await connectCopilotAppliance(appliance.name)
    connectedAppliance.value = result.applianceName
    setConnectedAppliance(result.applianceName)
    messages.value.push({
      role: 'assistant',
      content: `${result.message}\n\nAuthenticated as **${result.authenticatedUser}** via \`${result.loginEndpoint}\`.`
    })

    const queued = pendingMessage.value
    const queuedAttachments = pendingAttachmentsSnapshot.value
    pendingMessage.value = null
    pendingAttachmentsSnapshot.value = []

    if (queued || queuedAttachments.length) {
      await runChat(queued, queuedAttachments)
    }
  } catch (error) {
    messages.value.push({
      role: 'assistant',
      content: `Next-Gen API login failed for **${appliance.name}**: ${error.response?.data?.detail || error.message}`
    })
  } finally {
    connectingAppliance.value = false
    await scrollToBottom()
  }
}

async function runChat(content, attachments) {
  loading.value = true
  await scrollToBottom()

  try {
    const conversational = messages.value.filter(
      (msg) => (msg.role === 'user' || msg.role === 'assistant') && msg.content && !msg.appliancePicker
    )
    let history = conversational.map((msg) => ({ role: msg.role, content: msg.content }))
    if (
      history.length
      && history[history.length - 1].role === 'user'
      && history[history.length - 1].content === content
    ) {
      history = history.slice(0, -1)
    }

    const { data } = await api.post('/copilot/chat', {
      message: content,
      history,
      attachments,
      settings: getCopilotSettings(),
      applianceName: connectedAppliance.value
    })

    messages.value.push({
      role: 'assistant',
      content: data.content,
      toolCalls: data.toolCalls
    })
  } catch (error) {
    const detail = error.response?.data?.detail || 'Copilot request failed'
    messages.value.push({
      role: 'assistant',
      content: `Sorry, something went wrong: ${detail}`
    })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

async function sendMessage(text) {
  const content = (text || input.value).trim()
  const attachments = pendingAttachments.value.map((item) => ({
    name: item.name,
    kind: item.kind,
    mimeType: item.mimeType,
    data: item.data
  }))

  if ((!content && !attachments.length) || loading.value || !status.value.ready) return

  messages.value.push({
    role: 'user',
    content,
    attachments: attachments.map((item) => ({ ...item }))
  })
  input.value = ''
  pendingAttachments.value = []
  await scrollToBottom()

  if (!connectedAppliance.value) {
    pendingMessage.value = content
    pendingAttachmentsSnapshot.value = attachments
    await showAppliancePicker()
    return
  }

  await runChat(content, attachments)
}

onMounted(loadStatus)
</script>

<style scoped>
.copilot-page {
  height: calc(100vh - 3rem);
  min-height: 32rem;
}

.chat-panel {
  background: var(--p-content-background);
  border: 1px solid var(--p-content-border-color);
  border-radius: 1rem;
  overflow: hidden;
  min-height: 0;
}

.chat-messages {
  overflow-y: auto;
  padding: 1.25rem;
}

.chat-empty {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--p-text-muted-color);
}

.chat-empty-icon {
  font-size: 2rem;
  color: var(--p-primary-color);
  margin-bottom: 1rem;
}

.chat-empty h2 {
  margin: 0 0 0.5rem;
  color: var(--p-text-color);
}

.chat-empty p {
  margin: 0;
  max-width: 28rem;
  margin-inline: auto;
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
  max-width: min(44rem, 88%);
  padding: 0.875rem 1rem;
  border-radius: 0.875rem;
  border: 1px solid var(--p-content-border-color);
}

.chat-message-user .chat-bubble {
  background: color-mix(in srgb, var(--p-primary-100) 70%, var(--p-content-background));
}

.chat-message-assistant .chat-bubble {
  background: var(--p-surface-50);
}

.chat-bubble-loading {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--p-text-muted-color);
}

.chat-role {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--p-text-muted-color);
  margin-bottom: 0.35rem;
}

.chat-content {
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: 0.9375rem;
}

.chat-attachments,
.pending-attachments {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.pending-attachments {
  padding: 0.75rem 1rem 0;
  border-top: 1px solid var(--p-content-border-color);
  background: var(--p-surface-50);
}

.attachment-chip,
.pending-attachment {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.5rem;
  border-radius: 0.5rem;
  background: var(--p-content-background);
  border: 1px solid var(--p-content-border-color);
  font-size: 0.8125rem;
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
  border-top: 1px solid var(--p-content-border-color);
  background: var(--p-surface-0);
}

.chat-input {
  resize: none;
}

.connected-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 1rem;
  border: 1px solid var(--p-primary-200);
  border-radius: 0.75rem;
  background: var(--p-primary-50);
}

.connected-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--p-primary-800);
}

.connected-info i {
  color: var(--p-green-600);
}
</style>
