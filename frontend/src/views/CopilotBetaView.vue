<template>
  <div class="page copilot-page flex flex-column">
    <div class="copilot-toolbar flex justify-content-between align-items-center gap-2 flex-wrap mb-2">
      <div class="flex align-items-center gap-2">
        <Tag value="Beta" severity="warn" icon="pi pi-sparkles" />
        <span class="beta-view-label">Saved on this device until you delete them</span>
      </div>
      <div class="flex align-items-center gap-2 flex-wrap">
        <div class="bg-picker-wrap">
          <Button v-tooltip.bottom="'Background'" icon="pi pi-image" text rounded @click="bgPickerOpen = !bgPickerOpen" />
          <div v-if="bgPickerOpen" class="bg-picker">
            <button
              v-for="bg in backgrounds"
              :key="bg.id"
              class="bg-thumb"
              :class="{ 'bg-thumb-active': background === bg.url }"
              :style="{ backgroundImage: `url(${bg.url})` }"
              @click="chooseBackground(bg.url)"
            />
            <button
              class="bg-thumb bg-thumb-none"
              :class="{ 'bg-thumb-active': background === 'none' }"
              @click="chooseBackground('none')"
            >
              None
            </button>
          </div>
        </div>
        <Button v-tooltip.top="'JPilot settings'" icon="pi pi-cog" text rounded @click="router.push('/settings?section=jpilot')" />
      </div>
    </div>

    <Message v-if="!ready" severity="warn" :closable="false" class="mb-3">
      No enabled AI provider found.
      <RouterLink to="/settings?section=ai-providers" class="ml-2">Configure AI Providers →</RouterLink>
    </Message>

    <div class="stage flex-1" :style="stageStyle">
      <div class="stage-scrim" />
      <div class="beta-chat-layout">
        <div class="beta-sidebar-card content-panel">
          <BetaChatSidebar
            :panes="paneSummaries"
            :active-session-id="activeSessionId"
            :can-add="canAddConversation"
            :conversation-count="betaChatState.conversations.length"
            :max-conversations="MAX_BETA_CONVERSATIONS"
            @select="setActiveBetaConversation"
            @new-chat="onNewChat"
            @delete="onDeleteChat"
          />
        </div>
        <div class="beta-chat-card content-panel">
          <ChatPane
            v-if="activeConversation"
            :key="activeSessionId"
            class="beta-chat-pane"
            :session-id="activeSessionId"
            :initial-role="activeConversation.initialRole"
            ui-variant="beta"
            :providers="providers"
            :appliances="appliances"
            :default-provider-id="defaultProviderId"
            :web-search-available="webSearchAvailable"
            :can-close="false"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Tag from 'primevue/tag'
import BetaChatSidebar from '../components/BetaChatSidebar.vue'
import ChatPane from '../components/ChatPane.vue'
import { getRoleById } from '../config/jpilotRoles'
import {
  MAX_BETA_CONVERSATIONS,
  betaChatState,
  canAddBetaConversation,
  conversationDisplayTitle,
  createBetaConversation,
  removeBetaConversation,
  setActiveBetaConversation
} from '../stores/betaChatConversations'
import { handoffState } from '../stores/copilotHandoff'
import { isSessionLoading } from '../stores/copilotChatRuns'
import { getSession } from '../stores/copilotSessions'
import {
  CHAT_BACKGROUNDS,
  getChatBackground,
  listChatProviders,
  listCopilotAppliances,
  setChatBackground
} from '../services/copilot'
import { getCopilotPlatformSettings } from '../services/copilotPlatform'

const router = useRouter()
const toast = useToast()
const confirm = useConfirm()

const providers = ref([])
const appliances = ref([])
const backgrounds = CHAT_BACKGROUNDS
const background = ref(getChatBackground())
const bgPickerOpen = ref(false)
const webSearchAvailable = ref(false)

const ready = computed(() => providers.value.length > 0)
const canAddConversation = computed(() => canAddBetaConversation())
const activeSessionId = computed(() => betaChatState.activeId)

const activeConversation = computed(() =>
  betaChatState.conversations.find((c) => c.sessionId === activeSessionId.value) ||
  betaChatState.conversations[0] ||
  null
)

const defaultProviderId = computed(() => {
  const def = providers.value.find((p) => p.isDefault)
  return (def || providers.value[0])?.id || ''
})

const stageStyle = computed(() =>
  background.value === 'none' ? {} : { backgroundImage: `url(${background.value})` }
)

function lastMessagePreview(session) {
  const conversational = (session.messages || []).filter(
    (msg) => (msg.role === 'user' || msg.role === 'assistant') && msg.content && !msg.appliancePicker
  )
  const last = conversational[conversational.length - 1]
  if (!last?.content) return 'No messages yet'
  const text = String(last.content).replace(/\s+/g, ' ').trim()
  return text.length > 72 ? `${text.slice(0, 72)}…` : text
}

function paneStatus(session, sessionId) {
  if (isSessionLoading(sessionId)) return 'busy'
  if (session.connectedAppliance) return 'active'
  if (session.applianceChoice) return 'away'
  return 'away'
}

const paneSummaries = computed(() =>
  betaChatState.conversations.map((conversation) => {
    const session = getSession(conversation.sessionId, conversation.initialRole)
    const role = getRoleById(session.role)
    return {
      sessionId: conversation.sessionId,
      title: conversationDisplayTitle(conversation),
      preview: lastMessagePreview(session),
      role,
      busy: isSessionLoading(conversation.sessionId),
      status: paneStatus(session, conversation.sessionId)
    }
  })
)

function onNewChat() {
  if (!canAddBetaConversation()) {
    toast.add({
      severity: 'warn',
      summary: 'Conversation limit',
      detail: `You can keep up to ${MAX_BETA_CONVERSATIONS} chats in this tab. Delete one to add another.`,
      life: 5000
    })
    return
  }
  createBetaConversation('operator', 'New chat')
}

function onDeleteChat(sessionId) {
  const pane = paneSummaries.value.find((p) => p.sessionId === sessionId)
  confirm.require({
    message: `Delete "${pane?.title || 'this chat'}"? This cannot be undone.`,
    header: 'Delete conversation',
    icon: 'pi pi-trash',
    rejectLabel: 'Cancel',
    acceptLabel: 'Delete',
    acceptClass: 'p-button-danger',
    accept: () => {
      const result = removeBetaConversation(sessionId)
      if (!result.ok) {
        toast.add({
          severity: 'warn',
          summary: 'Could not delete',
          detail: result.reason,
          life: 4000
        })
      }
    }
  })
}

function chooseBackground(url) {
  background.value = url
  setChatBackground(url)
  bgPickerOpen.value = false
}

async function loadProviders() {
  try {
    providers.value = await listChatProviders()
  } catch {
    providers.value = []
  }
}

async function loadAppliances() {
  try {
    appliances.value = await listCopilotAppliances()
  } catch {
    appliances.value = []
  }
}

async function loadWebSearchAvailability() {
  try {
    const settings = await getCopilotPlatformSettings()
    webSearchAvailable.value = !!(settings.allowWebSearch && settings.hasBraveSearchApiKey)
  } catch {
    webSearchAvailable.value = false
  }
}

onMounted(() => {
  if (!betaChatState.conversations.length) {
    createBetaConversation('architect', 'Architect')
  }
  loadProviders()
  loadAppliances()
  loadWebSearchAvailability()
})

watch(
  () => handoffState.pending,
  (pending) => {
    if (pending?.targetSessionId?.startsWith('beta-')) {
      setActiveBetaConversation(pending.targetSessionId)
    }
  }
)
</script>

<style scoped>
.copilot-page {
  height: calc(100vh - 5rem);
  min-height: 32rem;
  overflow: hidden;
}

.beta-view-label {
  font-size: 0.8125rem;
  color: var(--p-text-muted-color);
}

.stage {
  position: relative;
  border-radius: 1rem;
  overflow: hidden;
  background-color: var(--p-surface-100);
  background-size: cover;
  background-position: center;
  min-height: 0;
}

:global(.app-dark) .stage {
  background-color: var(--p-surface-950);
}

.stage-scrim {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.35);
  pointer-events: none;
}

:global(.app-dark) .stage-scrim {
  background: rgba(2, 6, 23, 0.55);
}

.beta-chat-layout {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  height: 100%;
  min-height: 0;
  padding: 0.75rem;
}

.beta-sidebar-card,
.beta-chat-card {
  min-height: 0;
  overflow: hidden;
  padding: 0;
}

.beta-chat-pane {
  height: 100%;
  border: 0;
  border-radius: inherit;
  box-shadow: none;
}

@media (min-width: 992px) {
  .beta-chat-layout {
    flex-direction: row;
    gap: 2rem;
    padding: 1rem;
  }

  .beta-sidebar-card {
    width: 25rem;
    flex-shrink: 0;
  }

  .beta-chat-card {
    flex: 1;
    min-width: 0;
  }
}

.bg-picker-wrap {
  position: relative;
}

.bg-picker {
  position: absolute;
  right: 0;
  top: 2.75rem;
  z-index: 20;
  display: grid;
  grid-template-columns: repeat(2, 4.5rem);
  gap: 0.5rem;
  padding: 0.6rem;
  background: var(--p-content-background);
  border: 1px solid var(--p-content-border-color);
  border-radius: 0.75rem;
  box-shadow: 0 12px 32px rgba(2, 6, 23, 0.2);
}

.bg-thumb {
  width: 4.5rem;
  height: 3rem;
  border-radius: 0.5rem;
  border: 2px solid transparent;
  background-size: cover;
  background-position: center;
  cursor: pointer;
  color: var(--p-text-muted-color);
  font-size: 0.75rem;
}

.bg-thumb-none {
  background: var(--p-surface-100);
  display: flex;
  align-items: center;
  justify-content: center;
}

.bg-thumb-active {
  border-color: var(--p-primary-color);
}
</style>
