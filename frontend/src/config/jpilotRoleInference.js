import { getRoleById, normalizeRoleId } from './jpilotRoles'

const ROLE_REASONS = {
  architect: 'best for planning and design work',
  operator: 'best for configuration changes on your appliance',
  analyst: 'best for troubleshooting and read-only checks'
}

function containsAny(text, phrases) {
  return phrases.some((phrase) => text.includes(phrase))
}

function isFormSubmission(text) {
  const stripped = (text || '').trim()
  return (
    stripped.startsWith('Configuration inputs for:') ||
    stripped.startsWith('Planning inputs for:')
  )
}

function attachmentIsDesignDocument(name) {
  const lowered = (name || '').toLowerCase()
  return lowered.endsWith('.md') || lowered.endsWith('.markdown')
}

function requestsDesignImplementation(text, attachmentNames = []) {
  const lowered = (text || '').toLowerCase()
  const verbs = ['configure', 'implement', 'apply', 'deploy', 'provision', 'build', 'execute', 'roll out', 'rollout']
  if (!verbs.some((verb) => lowered.includes(verb))) return false
  if (
    containsAny(lowered, [
      'design document',
      'design doc',
      'attached design',
      'this design',
      'from the design',
      'per the design',
      'based on the design',
      'jpilot-design',
      'handoff for operator'
    ])
  ) {
    return true
  }
  return attachmentNames.some(attachmentIsDesignDocument)
}

/**
 * Guess which JPilot role should handle a free-text chat message.
 * Returns null when the current role should stay unchanged.
 *
 * @param {string} text
 * @param {{ attachmentNames?: string[], currentRole?: string }} [opts]
 * @returns {{ role: string, reason: string, confidence: number } | null}
 */
export function inferChatRoleFromMessage(text, opts = {}) {
  const lowered = (text || '').trim().toLowerCase()
  const attachmentNames = opts.attachmentNames || []
  if (lowered.length < 4) return null

  if (isFormSubmission(text)) {
    return { role: 'operator', reason: 'form submissions are handled by Operator', confidence: 20 }
  }

  if (requestsDesignImplementation(text, attachmentNames)) {
    return { role: 'operator', reason: 'design implementation runs on the connected appliance', confidence: 20 }
  }

  const scores = { architect: 0, operator: 0, analyst: 0 }

  if (containsAny(lowered, [' as architect', 'architect mode', 'architect role', 'using architect'])) {
    scores.architect += 20
  }
  if (containsAny(lowered, [' as operator', 'operator mode', 'operator role', 'using operator'])) {
    scores.operator += 20
  }
  if (containsAny(lowered, [' as analyst', 'analyst mode', 'analyst role', 'using analyst'])) {
    scores.analyst += 20
  }

  const mentionsDesign = /\bdesign\b/.test(lowered)
  const mentionsHa = containsAny(lowered, [
    ' ha ',
    ' ha,',
    ' ha.',
    'high availability',
    'ha pair',
    'ha for',
    'ha across',
    'datacenter',
    'data center',
    'multi-site',
    'multi site'
  ])

  if (mentionsDesign && mentionsHa) {
    scores.architect += 12
  }

  if (
    mentionsDesign &&
    containsAny(lowered, [
      "let's design",
      'lets design',
      'help me design',
      'need to design',
      'want to design',
      'design the',
      'design a',
      'design an',
      'design our',
      'design for'
    ])
  ) {
    scores.architect += 10
  }

  if (
    containsAny(lowered, [
      'design document',
      'design doc',
      'architecture',
      'architectural',
      'deployment plan',
      'discovery form',
      'jpilot-form',
      'high availability design',
      'ha design',
      'design ha',
      'design the ha',
      'ha pair design',
      'gslb design',
      'load balancing design',
      'outline a design',
      'migration plan',
      'capacity plan',
      'blueprint',
      'reference appliance',
      'without connecting'
    ])
  ) {
    scores.architect += 8
  }

  if (mentionsDesign && !requestsDesignImplementation(text, attachmentNames)) {
    scores.architect += 4
  }

  if (
    containsAny(lowered, ['plan a ', 'plan for ', 'plan the ', 'plan our ', "planning for", 'planning a '])
  ) {
    scores.architect += 6
  }

  if (
    containsAny(lowered, [
      'why is',
      'why are',
      'why does',
      'root cause',
      'troubleshoot',
      'diagnose',
      'investigate',
      'not working',
      'is down',
      'went down',
      'failing',
      'intermittent',
      'health check',
      'health summary',
      'performance issue',
      'latency',
      'packet loss',
      'connectivity test',
      'can you reach',
      'ping ',
      'traceroute',
      'telnet ',
      'nsconmsg',
      'audit ',
      'certificate expir',
      'ssl expir',
      'what is wrong',
      "what's wrong"
    ])
  ) {
    scores.analyst += 7
  }

  if (
    containsAny(lowered, [
      'show ',
      'list ',
      'get ',
      'how many',
      'what is the',
      'display ',
      'summarize ',
      'summary of',
      'inventory',
      'version',
      'firmware',
      'hostname',
      'serial number'
    ])
  ) {
    scores.analyst += 3
  }

  if (
    containsAny(lowered, [
      'add ',
      'create ',
      'configure ',
      'implement ',
      'apply ',
      'deploy ',
      'provision ',
      'bind ',
      'unbind ',
      'set ',
      'update ',
      'change ',
      'remove ',
      'delete ',
      'enable ',
      'disable ',
      'run cli',
      'cli command',
      'save ns config',
      'new lb',
      'new vip',
      'new vserver',
      'static route',
      'vlan ',
      'channel ',
      'certificate bind',
      'upload cert'
    ])
  ) {
    scores.operator += 8
  }

  if (containsAny(lowered, ['outline', 'gateway', 'storefront', 'gslb'])) {
    scores.architect += 2
  }

  const ranked = Object.entries(scores).sort((a, b) => b[1] - a[1])
  const [bestRole, bestScore] = ranked[0]
  const [, secondScore] = ranked[1]

  if (bestScore < 5) return null
  if (secondScore >= 5 && bestScore - secondScore < 3) return null

  const currentRole = normalizeRoleId(opts.currentRole)
  if (bestRole === currentRole) return null

  return {
    role: bestRole,
    reason: ROLE_REASONS[bestRole],
    confidence: bestScore
  }
}

export function buildRoleSwitchNotice(toRoleId, reason) {
  const role = getRoleById(toRoleId)
  const detail = reason || ROLE_REASONS[normalizeRoleId(toRoleId)]
  return {
    toRole: normalizeRoleId(toRoleId),
    label: role.label,
    icon: role.icon,
    reason: detail
  }
}
