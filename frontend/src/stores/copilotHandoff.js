import { reactive } from 'vue'

export const ARCHITECT_SESSION_ID = 'pane-1'
export const OPERATOR_SESSION_ID = 'pane-2'

export const DESIGN_HANDOFF_MESSAGE =
  'Implement this design on the connected appliance. Start with the **Handoff for Operator** section. Use jpilot-form for any TBD values before running write tools.'

/** @typedef {{ targetSessionId: string, content: string, sourceLabel: string, queuedAt: number }} DesignHandoff */

export const handoffState = reactive({
  /** @type {DesignHandoff | null} */
  pending: null
})

/**
 * @param {{ content: string, sourceLabel?: string, targetSessionId?: string }} payload
 */
export function queueDesignHandoff(payload) {
  handoffState.pending = {
    targetSessionId: payload.targetSessionId || OPERATOR_SESSION_ID,
    content: payload.content,
    sourceLabel: payload.sourceLabel || '',
    queuedAt: Date.now()
  }
}

/**
 * @param {string} sessionId
 * @returns {DesignHandoff | null}
 */
export function consumeDesignHandoff(sessionId) {
  if (!handoffState.pending || handoffState.pending.targetSessionId !== sessionId) {
    return null
  }
  const handoff = { ...handoffState.pending }
  handoffState.pending = null
  return handoff
}
