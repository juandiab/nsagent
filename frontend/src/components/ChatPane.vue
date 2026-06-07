<template>
  <div
    class="chat-pane flex flex-column flex-1"
    :class="{ 'pane-empty': !session.messages.length, 'pane-generating': isGenerating }"
    @mousedown="markPaneFocused"
    @focusin="markPaneFocused"
  >
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
      <SelectButton
        v-model="session.role"
        :options="roleOptions"
        option-value="id"
        data-key="id"
        :allow-empty="false"
        class="pane-role-toggle"
        :disabled="isGenerating"
        aria-label="JPilot role"
      >
        <template #option="slotProps">
          <i
            :class="slotProps.option.icon"
            v-tooltip.bottom="roleOptionTooltip(slotProps.option)"
            :aria-label="slotProps.option.label"
          />
        </template>
      </SelectButton>
      <Select
        v-model="session.applianceChoice"
        :options="roleApplianceOptions"
        option-value="name"
        :placeholder="roleNeedsAppliance ? 'Appliance' : 'Appliance (optional)'"
        class="pane-select pane-select-appliance"
        :disabled="isGenerating || connecting || !roleApplianceOptions.length"
        :option-disabled="(appliance) => isApplianceDisabledForRole(appliance, session.role)"
        @change="onApplianceChange"
      >
        <template #option="{ option }">
          <ApplianceNameLabel :appliance="option" />
        </template>
        <template #value="{ value, placeholder }">
          <ApplianceNameLabel v-if="selectedAppliance" :appliance="selectedAppliance" />
          <span v-else>{{ placeholder }}</span>
        </template>
      </Select>
      <div v-if="roleProviders.length" class="pane-llm">
        <Select
          v-if="roleProviders.length > 1"
          v-model="session.providerId"
          :options="providerOptions"
          option-label="label"
          option-value="value"
          placeholder="LLM"
          class="pane-select pane-select-llm"
          :disabled="isGenerating"
        />
        <span
          v-else
          v-tooltip.bottom="activeProviderTooltip"
          class="pane-llm-name"
        >
          <i class="pi pi-sparkles" aria-hidden="true" />
          {{ activeProviderName }}
        </span>
      </div>
      <ContextUsageRing
        v-if="activeProvider"
        :percent-used="contextUsage.percentUsed"
        :prompt-tokens="contextUsage.promptTokens"
        :context-token-limit="contextUsage.contextTokenLimit"
        :trimmed-count="contextUsage.trimmedCount"
        :max-history-messages="contextUsage.maxHistoryMessages"
        :model="activeProvider.model"
      />
      <span class="pane-spacer" />
      <span
        v-if="session.connectedAppliance && isApplianceConnected()"
        v-tooltip.bottom="connectedApplianceTooltip"
        class="pane-connected"
      >
        <i class="pi pi-check-circle" /> {{ session.connectedAppliance }}
      </span>
      <span
        v-else-if="session.applianceChoice && !roleNeedsAppliance"
        v-tooltip.bottom="'Planning reference — no live connection required'"
        class="pane-appliance-ref"
      >
        <i class="pi pi-compass" /> {{ session.applianceChoice }}
      </span>
      <span
        v-else-if="session.applianceChoice && roleNeedsAppliance"
        v-tooltip.bottom="'Selected appliance is not connected yet'"
        class="pane-disconnected"
      >
        <i class="pi pi-exclamation-circle" /> {{ session.applianceChoice }}
      </span>
      <Button
        v-if="isGenerating"
        v-tooltip.bottom="'Stop generating'"
        label="Stop"
        icon="pi pi-stop"
        size="small"
        severity="danger"
        outlined
        @click="stopChat"
      />
      <Button
        v-if="webSearchAvailable && !isGenerating"
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
        :disabled="isGenerating"
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
          <span>Ask JPilot — {{ activeRole.label }}</span>
        </div>
        <p class="glass-role-hint">{{ activeRole.description }}</p>
        <div class="glass-input" @click="focusAskInput">
          <i class="pi pi-search glass-input-icon" />
          <input
            ref="askInputRef"
            v-model="session.input"
            type="text"
            class="glass-input-field"
            :placeholder="rolePlaceholder"
            :disabled="isGenerating || !ready"
            @keydown.enter.prevent="sendMessage()"
          />
          <button
            class="glass-attach"
            type="button"
            :disabled="isGenerating || !ready"
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

        <AskJpilotCommandMenu
          ref="commandMenuRef"
          :active-role="session.role"
          :appliance-vendor="commandMenuVendor"
          :disabled="isGenerating || !ready"
          @pick="onCommandPick"
        />

        <p v-if="!ready" class="glass-hint">
          No LLM assigned to {{ activeRole.label }} — configure one in Settings → AI Providers.
        </p>
        <p v-else-if="activeProviderName" class="glass-hint glass-llm-hint">
          <i class="pi pi-sparkles" aria-hidden="true" />
          Using <strong>{{ activeProviderName }}</strong> for {{ activeRole.label }}
        </p>
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
              <div
                v-if="session.role === 'architect' && canDownloadDesignDoc(assistantView(msg).content)"
                class="design-doc-download"
              >
                <Button
                  label="Send to Operator"
                  icon="pi pi-arrow-right"
                  size="small"
                  :disabled="isGenerating"
                  @click="sendDesignToOperator(assistantView(msg).content)"
                />
                <Button
                  label="Download design document"
                  icon="pi pi-download"
                  size="small"
                  outlined
                  :disabled="isGenerating"
                  @click="downloadDesignDocMessage(assistantView(msg).content)"
                />
              </div>
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
              :role="session.role"
              :loading="msg.pickerLoading"
              :connecting="connecting"
              @select="connectAppliance"
            />
            <ChatConfigForm
              v-if="assistantView(msg).inputForm && !assistantView(msg).formSubmitted"
              :form="assistantView(msg).inputForm"
              :submitting="isGenerating && submittingFormIndex === index"
              @submit="(values) => submitConfigForm(values, index)"
            />
            <ChatToolTrace v-if="msg.toolCalls?.length" :tools="msg.toolCalls" />
          </div>
        </div>

        <div v-if="isGenerating" class="chat-message chat-message-assistant">
          <div class="chat-bubble chat-bubble-loading">
            <ProgressSpinner style="width: 1.25rem; height: 1.25rem" stroke-width="4" />
            <div class="generation-status">
              <span class="generation-label">{{ generationStatus.label }}</span>
              <span class="generation-meta">{{ generationStatusMeta(generationStatus) }}</span>
            </div>
            <Button
              label="Stop"
              icon="pi pi-stop"
              size="small"
              severity="danger"
              text
              @click="stopChat"
            />
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
          :disabled="isGenerating || !ready"
          @click="toggleAttachMenu"
        />
        <Textarea
          v-model="session.input"
          rows="2"
          auto-resize
          class="chat-input flex-1"
          :placeholder="rolePlaceholder"
          :disabled="isGenerating || !ready"
          @keydown.enter.exact.prevent="sendMessage()"
        />
        <Button
          v-if="isGenerating"
          v-tooltip.top="'Stop generating'"
          icon="pi pi-stop"
          severity="danger"
          @click="stopChat"
        />
        <Button
          v-else
          icon="pi pi-send"
          :disabled="(!session.input.trim() && !pendingAttachments.length) || !ready"
          @click="sendMessage()"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import Menu from 'primevue/menu'
import ProgressSpinner from 'primevue/progressspinner'
import Select from 'primevue/select'
import SelectButton from 'primevue/selectbutton'
import Textarea from 'primevue/textarea'
import ChatAppliancePicker from './ChatAppliancePicker.vue'
import ApplianceNameLabel from './ApplianceNameLabel.vue'
import ContextUsageRing from './ContextUsageRing.vue'
import ChatConfigForm from './ChatConfigForm.vue'
import AskJpilotCommandMenu from './AskJpilotCommandMenu.vue'
import ChatMarkdown from './ChatMarkdown.vue'
import ChatToolTrace from './ChatToolTrace.vue'
import { streamCopilotChat } from '../services/copilotStream'
import { formatCopilotError, isChatAbortError, isProviderQuotaError } from '../utils/chatErrors'
import { generationStatusMeta } from '../utils/generationStatus'
import {
  CONFIG_ACCEPT,
  attachmentPreviewUrl,
  connectCopilotAppliance,
  fileToAttachment,
  getCopilotSettings,
  listCopilotAppliances
} from '../services/copilot'
import { parseInputFormFromContent, resolveAssistantMessage } from '../utils/copilotForm'
import { estimateSessionContextUsage } from '../utils/contextUsage'
import { downloadDesignDocument, createDesignDocumentAttachment, isDesignDocumentMessage } from '../utils/designDocument'
import {
  ARCHITECT_SESSION_ID,
  DESIGN_HANDOFF_MESSAGE,
  OPERATOR_SESSION_ID,
  consumeDesignHandoff,
  handoffState,
  queueDesignHandoff
} from '../stores/copilotHandoff'
import { clearSession, getSession } from '../stores/copilotSessions'
import {
  beginChatRun,
  endChatRun,
  isSessionLoading,
  setFocusedChatSession,
  stopChatRun
} from '../stores/copilotChatRuns'
import { notifyReplyReady } from '../services/chatNotifications'
import {
  DEFAULT_JPILOT_ROLE,
  JPILOT_ROLES,
  getRoleById,
  roleRequiresAppliance
} from '../config/jpilotRoles'
import {
  appliancesForJpilotRole,
  isApplianceDisabledForRole
} from '../config/jpilotApplianceAccess'
import { isNetScalerVendor } from '../config/applianceVendors'
import { resolveCommandFilterVendor } from '../config/jpilotRecommendedActions'

const props = defineProps({
  sessionId: { type: String, required: true },
  initialRole: { type: String, default: DEFAULT_JPILOT_ROLE },
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
const session = getSession(props.sessionId, props.initialRole)

// Transient UI state — fine to reset on remount.
const connecting = ref(false)
const isGenerating = computed(() => isSessionLoading(props.sessionId))

function markPaneFocused() {
  setFocusedChatSession(props.sessionId)
}
const submittingFormIndex = ref(null)
const messagesEl = ref(null)
const pendingAttachments = ref([])
const imageInputRef = ref(null)
const configInputRef = ref(null)
const attachMenu = ref(null)
const askInputRef = ref(null)
const commandMenuRef = ref(null)
const generationStatus = ref({
  phase: 'thinking',
  label: 'Thinking…',
  elapsedMs: 0,
  tokensPerSec: null,
  round: 0
})
let generationStartedAt = 0
let generationElapsedTimer = null
let lastGenerationStats = null

function resetGenerationStatus() {
  generationStatus.value = {
    phase: 'thinking',
    label: 'Thinking…',
    elapsedMs: 0,
    tokensPerSec: null,
    round: 0
  }
  lastGenerationStats = null
}

function startGenerationTimer() {
  generationStartedAt = Date.now()
  stopGenerationTimer()
  generationElapsedTimer = setInterval(() => {
    generationStatus.value = {
      ...generationStatus.value,
      elapsedMs: Date.now() - generationStartedAt
    }
  }, 250)
}

function stopGenerationTimer() {
  if (generationElapsedTimer) {
    clearInterval(generationElapsedTimer)
    generationElapsedTimer = null
  }
}

function onGenerationEvent(event) {
  if (event.type === 'llm_stats') {
    lastGenerationStats = {
      tokensPerSec: event.tokensPerSec,
      outputTokens: event.outputTokens,
      durationMs: event.durationMs,
      totalTokens: event.totalTokens
    }
  }
  if (event.type === 'status' || event.type === 'llm_stats') {
    generationStatus.value = {
      phase: event.phase || generationStatus.value.phase,
      label: event.label || generationStatus.value.label,
      elapsedMs: event.elapsedMs ?? generationStatus.value.elapsedMs,
      tokensPerSec: event.tokensPerSec ?? generationStatus.value.tokensPerSec,
      round: event.round ?? generationStatus.value.round
    }
  }
}

const configAccept = CONFIG_ACCEPT

const ready = computed(() => roleProviders.value.length > 0)
const roleOptions = JPILOT_ROLES
const activeRole = computed(() => getRoleById(session.role))
const roleNeedsAppliance = computed(() => roleRequiresAppliance(session.role))
const rolePlaceholder = computed(() => {
  if (activeRole.value.id === 'architect') {
    return 'Plan a deployment, HA design, migration, or ask NetScaler architecture questions…'
  }
  if (activeRole.value.id === 'analyst') {
    return 'Describe the issue; attach logs or screenshots; connect an appliance for live checks…'
  }
  return 'Ask about your NetScalers, attach configs or images…'
})
const providerOptions = computed(() =>
  roleProviders.value.map((provider) => ({
    label: provider.providerName,
    value: provider.id
  }))
)

const roleApplianceOptions = computed(() =>
  appliancesForJpilotRole(props.appliances, session.role)
)

const roleProviders = computed(() =>
  props.providers.filter((provider) => providerSupportsRole(provider, session.role))
)

const activeProvider = computed(() =>
  props.providers.find((provider) => provider.id === session.providerId) || roleProviders.value[0] || null
)

const contextUsage = computed(() =>
  estimateSessionContextUsage({
    messages: session.messages,
    draftInput: session.input,
    pendingAttachments: pendingAttachments.value,
    model: activeProvider.value?.model,
    providerType: activeProvider.value?.providerType
  })
)

const activeProviderName = computed(() => activeProvider.value?.providerName || '')

const activeProviderTooltip = computed(() =>
  activeProviderName.value
    ? `LLM for ${activeRole.value.label}: ${activeProviderName.value}`
    : ''
)

const selectedAppliance = computed(() =>
  roleApplianceOptions.value.find((appliance) => appliance.name === session.applianceChoice) ||
    props.appliances.find((appliance) => appliance.name === session.applianceChoice) ||
    null
)

/** Filter recommended actions once an appliance is chosen in this pane. */
const commandMenuVendor = computed(() =>
  session.applianceChoice ? resolveCommandFilterVendor(selectedAppliance.value) : null
)

const connectedApplianceTooltip = computed(() => {
  if (!selectedAppliance.value) return 'Connected'
  const vendor = selectedAppliance.value.vendor
  if (vendor === 'cisco' || vendor === 'f5' || vendor === 'sdx') return 'Connected via SSH'
  return 'Connected via Next-Gen API'
})

function chatApplianceName() {
  return session.applianceChoice || session.connectedAppliance || ''
}

function isApplianceConnected() {
  return Boolean(
    session.connectedAppliance &&
      session.applianceChoice &&
      session.connectedAppliance === session.applianceChoice
  )
}

function roleOptionTooltip(role) {
  const names = props.providers
    .filter((provider) => providerSupportsRole(provider, role.id))
    .map((provider) => provider.providerName)
  const llmLine = names.length
    ? `LLM: ${names.join(', ')}`
    : 'No LLM assigned for this role'
  return `${role.label} — ${llmLine}`
}

function providerSupportsRole(provider, roleId) {
  if (!provider) return false
  const roles = provider.roles
  if (!Array.isArray(roles) || !roles.length) return true
  return roles.includes(roleId)
}

function pickProviderForRole(force = false) {
  const options = providerOptions.value
  if (!options.length) {
    session.providerId = ''
    return
  }

  const currentValid = options.some((option) => option.value === session.providerId)
  if (!force && currentValid) return

  const roleDefault = options.find((option) => {
    const provider = props.providers.find((entry) => entry.id === option.value)
    return provider?.isDefault
  })
  session.providerId = roleDefault?.value || options[0]?.value || ''
}

function pickApplianceForRole(force = false) {
  const options = roleApplianceOptions.value
  if (!options.length) {
    session.applianceChoice = null
    session.connectedAppliance = ''
    return
  }

  const currentValid = options.some(
    (appliance) =>
      appliance.name === session.applianceChoice && !isApplianceDisabledForRole(appliance, session.role)
  )
  if (!force && currentValid) return

  const preferred =
    options.find((appliance) => isNetScalerVendor(appliance.vendor)) || options[0]
  session.applianceChoice = preferred.name
  if (roleNeedsAppliance.value) {
    session.connectedAppliance = ''
  }
}

function onRoleChange() {
  pickProviderForRole(true)
  pickApplianceForRole(true)
}

watch(
  () => session.role,
  () => {
    onRoleChange()
  }
)

watch(
  () => props.providers,
  () => {
    pickProviderForRole(false)
  },
  { immediate: true, deep: true }
)

watch(
  () => props.appliances,
  () => {
    pickApplianceForRole(false)
  },
  { immediate: true, deep: true }
)

const attachMenuItems = computed(() => {
  const settings = getCopilotSettings()
  const items = []
  if (settings.allowImages) {
    items.push({ label: 'Attach image', icon: 'pi pi-image', command: () => imageInputRef.value?.click() })
  }
  if (settings.allowConfigFiles) {
    items.push({
      label: 'Attach config or Markdown',
      icon: 'pi pi-file',
      command: () => configInputRef.value?.click()
    })
  }
  if (!items.length) {
    items.push({ label: 'Attachments disabled — open Settings', icon: 'pi pi-cog', command: () => router.push('/settings') })
  }
  return items
})

function toggleAttachMenu(event) {
  attachMenu.value.toggle(event)
}

function canDownloadDesignDoc(content) {
  return isDesignDocumentMessage(content)
}

function downloadDesignDocMessage(content) {
  const filename = downloadDesignDocument(content)
  toast.add({
    severity: 'success',
    summary: 'Design document downloaded',
    detail: filename,
    life: 3000
  })
}

function sendDesignToOperator(content) {
  if (props.sessionId !== ARCHITECT_SESSION_ID || session.role !== 'architect') {
    toast.add({
      severity: 'warn',
      summary: 'Architect pane only',
      detail: 'Send designs to Operator from the Architect chat pane.',
      life: 4000
    })
    return
  }
  try {
    const attachment = createDesignDocumentAttachment(content)
    queueDesignHandoff({
      content,
      sourceLabel: attachment.name
    })
    toast.add({
      severity: 'info',
      summary: 'Sent to Operator',
      detail: 'Opening the Operator pane and starting implementation…',
      life: 3500
    })
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Handoff failed',
      detail: error.message || 'Could not send design to Operator.',
      life: 4000
    })
  }
}

async function acceptDesignHandoff(handoff) {
  if (isGenerating.value) {
    queueDesignHandoff(handoff)
    toast.add({
      severity: 'warn',
      summary: 'Operator is busy',
      detail: 'Stop the current reply, then send the design again from Architect.',
      life: 4000
    })
    return
  }

  setFocusedChatSession(props.sessionId)
  if (session.role !== 'operator') {
    session.role = 'operator'
  }

  let attachment
  try {
    attachment = createDesignDocumentAttachment(handoff.content, handoff.sourceLabel || undefined)
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: 'Handoff failed',
      detail: error.message || 'Design document is too large to attach.',
      life: 4000
    })
    return
  }

  await sendMessage(DESIGN_HANDOFF_MESSAGE, [attachment])
}

async function tryConsumeDesignHandoff() {
  if (props.sessionId !== OPERATOR_SESSION_ID) return
  const handoff = consumeDesignHandoff(props.sessionId)
  if (!handoff) return
  await acceptDesignHandoff(handoff)
}

function onCommandPick(cmd) {
  if (cmd.type === 'link') {
    router.push(cmd.to)
    return
  }
  if (!ready.value) return
  sendMessage(cmd.text)
}

function focusAskInput() {
  askInputRef.value?.focus()
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
  session.connectedAppliance = ''
  if (!session.applianceChoice || !roleNeedsAppliance.value) return
  connectAppliance({ name: session.applianceChoice })
}

async function showAppliancePicker() {
  const pickerIndex = session.messages.length
  session.messages.push({ role: 'assistant', content: '', appliancePicker: true, appliances: [], pickerLoading: true })
  await scrollToBottom()
  try {
    const appliances = appliancesForJpilotRole(await listCopilotAppliances(), session.role)
    if (session.messages[pickerIndex]) {
      session.messages[pickerIndex].appliances = appliances
      session.messages[pickerIndex].pickerLoading = false
      session.messages[pickerIndex].content = appliances.length
        ? roleNeedsAppliance.value
          ? 'Choose a NetScaler from your inventory:'
          : 'Choose an appliance from your inventory (optional reference):'
        : roleNeedsAppliance.value
          ? 'No NetScaler appliances found. Add one in the inventory first.'
          : 'No appliances found. Add one in the inventory first.'
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
    const authLine =
      result.api === 'SSH'
        ? `Authenticated as **${result.authenticatedUser}** via SSH.`
        : `Authenticated as **${result.authenticatedUser}** via \`${result.loginEndpoint}\`.`
    session.messages.push({
      role: 'assistant',
      content: `${result.message}\n\n${authLine}`
    })
    const queued = session.pendingMessage
    const queuedAttachments = session.pendingAttachmentsSnapshot
    session.pendingMessage = null
    session.pendingAttachmentsSnapshot = []
    if (queued || queuedAttachments.length) await runChat(queued, queuedAttachments)
  } catch (error) {
    session.connectedAppliance = ''
    session.messages.push({
      role: 'assistant',
      content: `Connection failed for **${appliance.name}**: ${error.response?.data?.detail || error.message}`
    })
  } finally {
    connecting.value = false
    await scrollToBottom()
  }
}

async function runChat(content, attachments) {
  stopChatRun(props.sessionId)
  const controller = new AbortController()
  beginChatRun(props.sessionId, controller)
  resetGenerationStatus()
  startGenerationTimer()
  let wasError = false
  let userStopped = false
  await scrollToBottom()
  try {
    const conversational = session.messages.filter(
      (msg) => (msg.role === 'user' || msg.role === 'assistant') && msg.content && !msg.appliancePicker
    )
    let history = conversational.map((msg) => ({ role: msg.role, content: msg.content }))
    if (history.length && history[history.length - 1].role === 'user' && history[history.length - 1].content === content) {
      history = history.slice(0, -1)
    }
    const data = await streamCopilotChat(
      {
        message: content,
        history,
        attachments,
        settings: getCopilotSettings(),
        role: session.role || DEFAULT_JPILOT_ROLE,
        applianceName: chatApplianceName() || undefined,
        providerId: session.providerId || undefined,
        webSearch: session.webSearch !== false
      },
      {
        signal: controller.signal,
        onEvent: onGenerationEvent
      }
    )
    const parsed = parseInputFormFromContent(data.content || '')
    session.messages.push({
      role: 'assistant',
      content: parsed.content,
      toolCalls: data.toolCalls,
      webSources: extractWebSources(data.toolCalls),
      inputForm: data.inputForm || parsed.inputForm,
      generationStats: lastGenerationStats
    })
  } catch (error) {
    if (isChatAbortError(error)) {
      userStopped = true
      session.messages.push({
        role: 'assistant',
        content: 'Stopped — generation was cancelled. No further tokens will be used for this reply.'
      })
      return
    }
    wasError = true
    const content = formatCopilotError(error)
    session.messages.push({
      role: 'assistant',
      content,
      isError: true,
      providerQuotaError: isProviderQuotaError(error)
    })
  } finally {
    stopGenerationTimer()
    endChatRun(props.sessionId)
    submittingFormIndex.value = null
    await scrollToBottom()
    if (!userStopped) {
      notifyReplyReady({
        toast,
        sessionId: props.sessionId,
        role: session.role,
        wasError
      })
    }
  }
}

function stopChat() {
  stopChatRun(props.sessionId)
}

async function submitConfigForm(values, messageIndex) {
  const msg = session.messages[messageIndex]
  const view = resolveAssistantMessage(msg)
  if (!view.inputForm || view.formSubmitted || isGenerating.value) return

  const isArchitect = session.role === 'architect'
  const prefix = isArchitect ? 'Planning inputs for:' : 'Configuration inputs for:'
  const lines = [`${prefix} ${view.inputForm.title}`]
  for (const field of view.inputForm.fields) {
    const value = values[field.id]
    const rendered =
      field.type === 'boolean' ? (value ? 'yes' : 'no') : String(value ?? '').trim() || '(not provided)'
    lines.push(`- ${field.label}: ${rendered}`)
  }
  lines.push(
    '',
    isArchitect
      ? 'Continue design discovery or move to the next question.'
      : 'Proceed with the configuration on the connected appliance using these values. Do not ask the same questions in prose again.'
  )

  msg.formSubmitted = true
  submittingFormIndex.value = messageIndex
  try {
    await sendMessage(lines.join('\n'))
  } finally {
    submittingFormIndex.value = null
  }
}

async function sendMessage(text, externalAttachments = null) {
  const content = (text || session.input).trim()
  const sourceAttachments = externalAttachments ?? pendingAttachments.value
  const attachments = sourceAttachments.map((item) => ({
    name: item.name,
    kind: item.kind,
    mimeType: item.mimeType,
    data: item.data
  }))
  if ((!content && !attachments.length) || isGenerating.value || !ready.value) return

  session.messages.push({ role: 'user', content, attachments: attachments.map((item) => ({ ...item })) })
  session.input = ''
  if (!externalAttachments) {
    pendingAttachments.value = []
  }
  await scrollToBottom()

  if (roleNeedsAppliance.value && !isApplianceConnected()) {
    session.pendingMessage = content
    session.pendingAttachmentsSnapshot = attachments
    await showAppliancePicker()
    return
  }
  await runChat(content, attachments)
}

watch(
  () => [session.applianceChoice, session.connectedAppliance],
  () => {
    if (
      session.applianceChoice &&
      session.connectedAppliance &&
      session.applianceChoice !== session.connectedAppliance
    ) {
      session.connectedAppliance = ''
    }
  },
  { immediate: true }
)

onMounted(() => {
  markPaneFocused()
  scrollToBottom()
  tryConsumeDesignHandoff()
})

watch(
  () => handoffState.pending?.queuedAt,
  () => {
    tryConsumeDesignHandoff()
  }
)

onUnmounted(() => {
  stopGenerationTimer()
})
</script>

<style scoped>
.chat-pane.pane-generating {
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--p-primary-color) 35%, transparent);
}

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

.pane-role-toggle :deep(.p-togglebutton) {
  padding: 0.45rem 0.65rem;
}

.pane-role-toggle :deep(.p-togglebutton i) {
  font-size: 1rem;
}

.pane-select {
  min-width: 9rem;
}

.pane-select-appliance {
  min-width: 11rem;
}

.pane-select-appliance :deep(.appliance-name-label) {
  overflow: hidden;
}

.pane-select-appliance :deep(.appliance-name) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pane-select-llm {
  min-width: 9rem;
}

.pane-llm {
  display: flex;
  align-items: center;
  min-width: 0;
}

.pane-llm-name {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  max-width: 12rem;
  padding: 0.35rem 0.55rem;
  border-radius: 0.5rem;
  background: color-mix(in srgb, var(--p-primary-color) 10%, transparent);
  color: var(--p-text-color);
  font-size: 0.8125rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pane-llm-name i {
  flex-shrink: 0;
  color: var(--p-primary-color);
  font-size: 0.75rem;
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

.pane-disconnected {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8125rem;
  color: var(--p-orange-500);
  white-space: nowrap;
}

.pane-disconnected i {
  color: var(--p-orange-500);
}

.pane-appliance-ref {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8125rem;
  color: var(--p-text-muted-color);
  white-space: nowrap;
}

.pane-appliance-ref i {
  color: var(--p-primary-color);
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

.glass-role-hint {
  margin: -0.35rem 0 0.85rem;
  font-size: 0.8125rem;
  color: var(--glass-muted);
  line-height: 1.45;
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

.glass-llm-hint {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.glass-llm-hint i {
  color: var(--p-primary-color);
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

.design-doc-download {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--glass-border);
}

.chat-bubble-loading {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  color: var(--glass-muted);
}

.generation-status {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.generation-label {
  font-size: 0.875rem;
  color: var(--glass-text);
}

.generation-meta {
  font-size: 0.75rem;
  color: var(--glass-muted);
  font-variant-numeric: tabular-nums;
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
