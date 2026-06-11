import { reactive, watch } from 'vue'
import { normalizeRoleId } from '../config/jpilotRoles'
import { migrateStorageJson, readStorageJson, writeStorageJson } from '../utils/chatStorage'

// JPilot chat sessions keyed by pane / conversation id (e.g. pane-1, beta-chat-abc).
// Mirrored to localStorage on this device until the user clears a chat or deletes a thread.
const STORAGE_KEY = 'jpilot_sessions_v1'

function blankSession() {
  return {
    messages: [],
    input: '',
    role: 'operator',
    connectedAppliance: '',
    applianceChoice: null,
    providerId: '',
    webSearch: true,
    pendingMessage: null,
    pendingAttachmentsSnapshot: [],
    pendingRoleSwitch: null
  }
}

function loadPersisted() {
  const migrated = migrateStorageJson(STORAGE_KEY, sessionStorage, localStorage)
  if (migrated && typeof migrated === 'object') return migrated

  const stored = readStorageJson(localStorage, STORAGE_KEY)
  if (stored && typeof stored === 'object') return stored

  const legacy = readStorageJson(sessionStorage, STORAGE_KEY)
  if (legacy && typeof legacy === 'object') return legacy

  return {}
}

function trimSessionsForStorage(sessions) {
  const trimmed = {}
  for (const [id, session] of Object.entries(sessions)) {
    trimmed[id] = {
      input: session.input || '',
      role: session.role || 'operator',
      connectedAppliance: session.connectedAppliance || '',
      applianceChoice: session.applianceChoice || null,
      providerId: session.providerId || '',
      webSearch: session.webSearch !== false,
      pendingMessage: null,
      pendingAttachmentsSnapshot: [],
      messages: (session.messages || []).map((m) => ({
        role: m.role,
        content: m.content,
        createdAt: m.createdAt || undefined,
        toolCalls: m.toolCalls || undefined,
        webSources: m.webSources || undefined,
        appliancePicker: m.appliancePicker || undefined,
        inputForm: m.inputForm || undefined,
        formSubmitted: m.formSubmitted || undefined,
        attachments: (m.attachments || []).map((a) => ({
          name: a.name,
          kind: a.kind,
          mimeType: a.mimeType
        }))
      }))
    }
  }
  return trimmed
}

const state = reactive({ sessions: loadPersisted() })

export function getSession(id, defaultRole = 'operator') {
  if (!state.sessions[id]) {
    const session = blankSession()
    session.role = normalizeRoleId(defaultRole || 'operator')
    state.sessions[id] = session
  } else {
    state.sessions[id].role = normalizeRoleId(state.sessions[id].role)
  }
  return state.sessions[id]
}

export function clearSession(id) {
  const session = getSession(id)
  session.messages = []
  session.input = ''
  session.pendingMessage = null
  session.pendingAttachmentsSnapshot = []
  session.pendingRoleSwitch = null
  // Intentionally keep connectedAppliance, applianceChoice, and providerId.
}

export function deleteSession(id) {
  if (id && state.sessions[id]) {
    delete state.sessions[id]
  }
}

// Persist a trimmed copy: drop heavy base64 attachment data to stay under localStorage quota.
watch(
  () => state.sessions,
  (sessions) => {
    writeStorageJson(localStorage, STORAGE_KEY, trimSessionsForStorage(sessions))
  },
  { deep: true }
)
