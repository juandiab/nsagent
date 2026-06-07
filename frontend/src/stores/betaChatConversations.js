import { reactive, watch } from 'vue'
import { getRoleById } from '../config/jpilotRoles'
import { migrateStorageJson, readStorageJson, writeStorageJson } from '../utils/chatStorage'
import { deleteSession, getSession } from './copilotSessions'
import { isSessionLoading } from './copilotChatRuns'

const STORAGE_KEY = 'jpilot_beta_conversations_v1'

/** Bounded list size — user must delete a thread to add beyond this cap. */
export const MAX_BETA_CONVERSATIONS = 12

function defaultConversation(sessionId, initialRole, label) {
  return {
    id: sessionId.replace(/^beta-(?:chat-|pane-)/, '') || 'default',
    sessionId,
    label,
    initialRole,
    createdAt: Date.now()
  }
}

function loadState() {
  const migrated = migrateStorageJson(STORAGE_KEY, sessionStorage, localStorage)
  if (migrated?.conversations?.length) {
    return {
      activeId: migrated.activeId || migrated.conversations[0].sessionId,
      conversations: migrated.conversations
    }
  }

  const stored = readStorageJson(localStorage, STORAGE_KEY)
  if (stored?.conversations?.length) {
    return {
      activeId: stored.activeId || stored.conversations[0].sessionId,
      conversations: stored.conversations
    }
  }

  const legacy = readStorageJson(sessionStorage, STORAGE_KEY)
  if (legacy?.conversations?.length) {
    return {
      activeId: legacy.activeId || legacy.conversations[0].sessionId,
      conversations: legacy.conversations
    }
  }

  return {
    activeId: 'beta-pane-1',
    conversations: [defaultConversation('beta-pane-1', 'architect', 'Architect')]
  }
}

export const betaChatState = reactive(loadState())

function persist() {
  writeStorageJson(localStorage, STORAGE_KEY, {
    activeId: betaChatState.activeId,
    conversations: betaChatState.conversations
  })
}

watch(() => betaChatState, persist, { deep: true })

function newSessionId() {
  const id =
    typeof crypto !== 'undefined' && crypto.randomUUID
      ? crypto.randomUUID().slice(0, 8)
      : String(Date.now()).slice(-8)
  return `beta-chat-${id}`
}

/**
 * @param {string} [initialRole]
 * @param {string} [label]
 */
export function createBetaConversation(initialRole = 'operator', label = '') {
  if (betaChatState.conversations.length >= MAX_BETA_CONVERSATIONS) {
    return null
  }
  const role = getRoleById(initialRole)
  const sessionId = newSessionId()
  const conversation = {
    id: sessionId.replace('beta-chat-', ''),
    sessionId,
    label: label || role.label,
    initialRole: role.id,
    createdAt: Date.now()
  }
  betaChatState.conversations.unshift(conversation)
  betaChatState.activeId = sessionId
  getSession(sessionId, role.id)
  return conversation
}

export function setActiveBetaConversation(sessionId) {
  if (betaChatState.conversations.some((c) => c.sessionId === sessionId)) {
    betaChatState.activeId = sessionId
  }
}

/**
 * @param {string} sessionId
 * @returns {{ ok: boolean, reason?: string }}
 */
export function removeBetaConversation(sessionId) {
  if (betaChatState.conversations.length <= 1) {
    return { ok: false, reason: 'Keep at least one conversation.' }
  }
  if (isSessionLoading(sessionId)) {
    return { ok: false, reason: 'Stop the in-flight reply before deleting this chat.' }
  }

  const index = betaChatState.conversations.findIndex((c) => c.sessionId === sessionId)
  if (index < 0) {
    return { ok: false, reason: 'Conversation not found.' }
  }

  betaChatState.conversations.splice(index, 1)
  deleteSession(sessionId)

  if (betaChatState.activeId === sessionId) {
    betaChatState.activeId = betaChatState.conversations[0]?.sessionId || ''
  }

  return { ok: true }
}

/** Find an Operator thread for Architect handoff, or create one. */
export function resolveBetaHandoffTargetSessionId() {
  const existing = betaChatState.conversations.find((conversation) => {
    const session = getSession(conversation.sessionId, conversation.initialRole)
    return session.role === 'operator'
  })
  if (existing) {
    return existing.sessionId
  }
  const created = createBetaConversation('operator', 'Operator handoff')
  return created?.sessionId || betaChatState.activeId
}

export function conversationDisplayTitle(conversation) {
  const session = getSession(conversation.sessionId, conversation.initialRole)
  const role = getRoleById(session.role)
  const firstUser = (session.messages || []).find(
    (msg) => msg.role === 'user' && msg.content && String(msg.content).trim()
  )
  if (firstUser?.content) {
    const text = String(firstUser.content).replace(/\s+/g, ' ').trim()
    return text.length > 48 ? `${text.slice(0, 48)}…` : text
  }
  if (conversation.label && conversation.label !== role.label) {
    return conversation.label
  }
  return `${role.label} chat`
}

export function canAddBetaConversation() {
  return betaChatState.conversations.length < MAX_BETA_CONVERSATIONS
}
