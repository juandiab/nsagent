import router from '../router'
import { getCopilotSettings } from './copilot'
import { getFocusedChatSession } from '../stores/copilotChatRuns'
import { getRoleById } from '../config/jpilotRoles'

function sessionPaneLabel(sessionId) {
  const id = String(sessionId || '')
  const match = id.match(/(?:beta-)?pane-(\d+)/i)
  if (!match) return 'JPilot'
  const beta = id.startsWith('beta-') ? 'Beta ' : ''
  return `${beta}Pane ${match[1]}`
}

/**
 * Notify when the user is not actively watching this chat session.
 * @param {string} sessionId
 */
export function shouldNotifyReplyReady(sessionId) {
  const settings = getCopilotSettings()
  if (settings.notifyWhenReplyComplete === false) return false
  if (typeof document !== 'undefined' && document.hidden) return true
  const path = router.currentRoute.value.path
  if (path !== '/jpilot' && path !== '/jpilot/beta') return true
  if (getFocusedChatSession() !== sessionId) return true
  return false
}

export function playCompletionSound() {
  const settings = getCopilotSettings()
  if (settings.playReplySound === false) return
  try {
    const ctx = new AudioContext()
    const playTone = (freq, start, duration) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.type = 'sine'
      osc.frequency.value = freq
      gain.gain.setValueAtTime(0.0001, start)
      gain.gain.exponentialRampToValueAtTime(0.07, start + 0.02)
      gain.gain.exponentialRampToValueAtTime(0.0001, start + duration)
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.start(start)
      osc.stop(start + duration + 0.02)
    }
    const t = ctx.currentTime
    playTone(880, t, 0.1)
    playTone(1174.66, t + 0.12, 0.14)
    window.setTimeout(() => ctx.close().catch(() => {}), 400)
  } catch {
    // Autoplay or AudioContext blocked — ignore
  }
}

/**
 * @param {object} opts
 * @param {import('primevue/usetoast').ToastServiceMethods} opts.toast
 * @param {string} opts.sessionId
 * @param {string} opts.role
 * @param {boolean} opts.wasError
 */
export function notifyReplyReady({ toast, sessionId, role, wasError }) {
  if (!shouldNotifyReplyReady(sessionId)) return

  playCompletionSound()

  const roleLabel = getRoleById(role).label
  const pane = sessionPaneLabel(sessionId)
  toast.add({
    severity: wasError ? 'warn' : 'success',
    summary: wasError ? 'JPilot finished with an issue' : 'JPilot reply ready',
    detail: wasError
      ? `${roleLabel} · ${pane} — open JPilot to review.`
      : `${roleLabel} · ${pane} — your answer is ready.`,
    life: 7000
  })
}
