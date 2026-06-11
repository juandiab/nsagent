const CONTINUE_WORDS = new Set([
  'continue',
  'continuar',
  'continua',
  'continúa',
  'resume',
  'go on',
  'keep going',
  'proceed',
  'procede'
])

export function isDeploymentContinueMessage(text) {
  const normalized = String(text || '')
    .trim()
    .toLowerCase()
  if (!normalized) return false
  if (CONTINUE_WORDS.has(normalized)) return true
  return normalized.startsWith('continue ') || normalized.startsWith('continuar ')
}

export function messageNeedsDeploymentContinuation(message) {
  return Boolean(message?.deploymentContinuation?.required)
}
