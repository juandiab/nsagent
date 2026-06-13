const TOOL_LIMIT_RE = /maximum number of tool calls/i
const FORM_SUBMIT_RE = /planning inputs for:/gi

export function inferCalibrationCategory(session) {
  const messages = session?.messages || []
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    const msg = messages[i]
    const content = String(msg?.content || '')
    if (msg?.isError) return 'other'
    if (TOOL_LIMIT_RE.test(content)) return 'tool_limit'
    if (msg?.deploymentContinuation?.required) return 'too_slow'
  }
  const formCount = countPlanningFormSubmissions(messages)
  if (formCount >= 6) return 'too_slow'
  return 'other'
}

export function countPlanningFormSubmissions(messages) {
  const combined = (messages || []).map((m) => m.content || '').join('\n')
  return (combined.match(FORM_SUBMIT_RE) || []).length
}

export function inferUserGoal(messages) {
  const firstUser = (messages || []).find((m) => m.role === 'user' && String(m.content || '').trim())
  return firstUser ? String(firstUser.content).trim().slice(0, 500) : ''
}

export function inferSuggestedSkillId({ userGoal, role, vendor }) {
  if (vendor !== 'netscaler' || role !== 'architect') return null
  const lowered = (userGoal || '').toLowerCase()
  if (lowered.includes('firmware') && (lowered.includes('ha') || lowered.includes('upgrade'))) {
    return 'nexxus-netscaler-firmware-ha-upgrade'
  }
  if (lowered.includes('change control') || lowered.includes('maintenance window')) {
    return 'nexxus-netscaler-firmware-ha-upgrade'
  }
  return null
}

export function sessionStartedAt(messages) {
  const first = (messages || []).find((m) => m.createdAt)
  if (!first?.createdAt) return null
  return new Date(first.createdAt).toISOString()
}

export function buildCalibrationFeedbackPayload({
  session,
  sessionId,
  objectiveMet = false,
  userGoal = '',
  category = 'other',
  userComment = '',
  includeApplianceName = false
}) {
  const messages = (session?.messages || [])
    .filter((m) => !m.appliancePicker && !m.roleSwitchNotice)
    .map((m) => ({
      role: m.role,
      content: m.content || '',
      createdAt: m.createdAt ? new Date(m.createdAt).toISOString() : null,
      isError: Boolean(m.isError),
      toolCalls: (m.toolCalls || []).map((tc) => ({
        name: tc.name,
        arguments: tc.arguments || {},
        result: tc.result || ''
      }))
    }))

  const goal = userGoal.trim() || inferUserGoal(messages)
  const vendor = session?.applianceVendor || 'netscaler'

  return {
    objectiveMet,
    userGoal: goal,
    vendor,
    role: session?.role || 'architect',
    category,
    rating: objectiveMet ? 'positive' : 'negative',
    userComment: userComment.trim(),
    matchedSkills: [],
    suggestedSkillId: inferSuggestedSkillId({ userGoal: goal, role: session?.role, vendor }),
    includeApplianceName,
    applianceName: includeApplianceName ? session?.connectedAppliance || session?.applianceChoice || null : null,
    session: {
      sessionId: sessionId || null,
      startedAt: sessionStartedAt(messages),
      messages
    },
    diagnostics: {
      lastErrorType: category === 'tool_limit' ? 'tool_limit' : null,
      formSubmissionCount: countPlanningFormSubmissions(messages) || null
    },
    source: 'jpilot_in_app'
  }
}

export function shouldOfferCalibrationFeedback(session, { isGenerating = false } = {}) {
  if (isGenerating) return false
  const messages = session?.messages || []
  if (messages.length < 2) return false
  const hasAssistant = messages.some((m) => m.role === 'assistant' && String(m.content || '').trim())
  return hasAssistant
}
