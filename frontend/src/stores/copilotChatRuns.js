import { computed, reactive } from 'vue'

/** In-flight JPilot chat requests (survive pane unmount / route changes). */
const state = reactive({
  runs: {},
  focusedSessionId: null
})

export function beginChatRun(sessionId, abortController) {
  state.runs[sessionId] = { abortController }
}

export function endChatRun(sessionId) {
  delete state.runs[sessionId]
}

export function isSessionLoading(sessionId) {
  return Boolean(state.runs[sessionId])
}

export function stopChatRun(sessionId) {
  state.runs[sessionId]?.abortController?.abort()
}

export function setFocusedChatSession(sessionId) {
  state.focusedSessionId = sessionId
}

export function getFocusedChatSession() {
  return state.focusedSessionId
}

export const hasActiveChatRuns = computed(() => Object.keys(state.runs).length > 0)
