import { reactive, watch } from 'vue'
import { normalizeRoleId } from '../config/jpilotRoles'

// Persistent JPilot chat sessions, keyed by pane slot id (e.g. 'pane-1', 'pane-2').
// Lives in-memory (survives pane add/remove, orientation flips, and route navigation)
// and is mirrored to sessionStorage (survives a page reload, clears when the tab closes).
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
    pendingAttachmentsSnapshot: []
  }
}

function loadPersisted() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw) || {}
  } catch {
    // ignore corrupt storage
  }
  return {}
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
  // Intentionally keep connectedAppliance, applianceChoice, and providerId.
}

// Persist a trimmed copy: drop heavy base64 attachment data so we stay well under
// the sessionStorage quota. In-memory keeps full fidelity for the live session.
watch(
  () => state.sessions,
  (sessions) => {
    try {
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
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed))
    } catch {
      // Over quota or unavailable — in-memory state still works for this tab.
    }
  },
  { deep: true }
)
