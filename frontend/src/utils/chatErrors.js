const QUOTA_HINTS = [
  'quota exceeded',
  'exceeded your current quota',
  'insufficient_quota',
  'resource_exhausted',
  'free_tier',
  'generativelanguage.googleapis.com'
]

const CONTEXT_LIMIT_HINTS = [
  'context length',
  'context window',
  'maximum context',
  'max_tokens',
  'token limit',
  'too many tokens',
  'prompt is too long',
  'input is too long',
  'request too large'
]

const GATEWAY_TIMEOUT_HINTS = [
  'status code 504',
  'gateway timeout',
  'gateway time-out',
  'timed out',
  'etimedout',
  'econnaborted',
  '504 gateway'
]

function tryParseJsonError(text) {
  const trimmed = String(text || '').trim()
  if (!trimmed.startsWith('{')) return null
  try {
    return JSON.parse(trimmed)
  } catch {
    return null
  }
}

function lowered(text) {
  return String(text || '').toLowerCase()
}

function isQuotaLike(text) {
  const haystack = lowered(text)
  return QUOTA_HINTS.some((hint) => haystack.includes(hint))
}

function isContextLimitLike(text) {
  const haystack = lowered(text)
  return CONTEXT_LIMIT_HINTS.some((hint) => haystack.includes(hint))
}

function isGatewayTimeoutLike(text) {
  const haystack = lowered(text)
  return GATEWAY_TIMEOUT_HINTS.some((hint) => haystack.includes(hint))
}

function gatewayTimeoutMessage() {
  return [
    'JPilot did not finish in time (gateway or upstream timeout).',
    '',
    'The proxy or AI provider stopped waiting while your request was running. Architect discovery with tools can take several minutes.',
    '',
    '**What you can do:**',
    '1. **Retry** — your planning inputs stay in this chat thread.',
    '2. Start a **new chat** if the thread is long (shorter context is faster).',
    '3. Use a faster **Model**, or turn off **Web** search for this turn.'
  ].join('\n')
}

function contextLimitMessage() {
  return [
    'The selected model ran out of context or token budget for this request.',
    '',
    '**What you can do:**',
    '1. Start a **new chat** and paste your latest planning inputs to continue discovery.',
    '2. Switch to a model with a larger context window under **AI Providers**.',
    '3. Open **Settings → Usage** to review monthly token limits and remaining quota.'
  ].join('\n')
}

function quotaExhaustedMessage(providerMessage) {
  const lines = [
    'The selected AI model cannot complete this request because the API quota or credits are exhausted.',
    '',
    '**What you can do:**',
    '1. Switch to another provider using the **Model** dropdown in JPilot.',
    '2. Open **AI Providers** to add credits or configure another API key.',
    '3. Open **Settings → Usage** to see monthly token and request limits.',
    '4. On free tiers, limits often reset daily — wait and retry, or use a paid key.'
  ]
  if (providerMessage) {
    lines.push('', `_Provider message: ${providerMessage}_`)
  }
  return lines.join('\n')
}

export function isChatAbortError(error) {
  return error?.code === 'ERR_CANCELED' || error?.name === 'CanceledError'
}

/**
 * Backend usually formats these already; this is a client-side fallback.
 */
export function formatCopilotError(error) {
  const status = error?.response?.status
  const detail = error?.response?.data?.detail

  if (typeof detail === 'string' && detail.includes('**What you can do:**')) {
    return detail
  }

  const raw = typeof detail === 'string' ? detail : error?.message || 'JPilot request failed.'
  const cleaned = raw.replace(/^Copilot request failed:\s*/i, '').trim()
  const combined = `${cleaned} ${error?.code || ''}`

  if (status === 504 || (status === 502 && isGatewayTimeoutLike(combined))) {
    return gatewayTimeoutMessage()
  }

  if (isGatewayTimeoutLike(combined) && !isQuotaLike(combined)) {
    return gatewayTimeoutMessage()
  }

  const parsed = tryParseJsonError(cleaned)
  if (parsed?.error?.message && isQuotaLike(JSON.stringify(parsed))) {
    return quotaExhaustedMessage(parsed.error.message)
  }

  if (status === 429 || isQuotaLike(cleaned)) {
    return quotaExhaustedMessage()
  }

  if (isContextLimitLike(cleaned)) {
    return contextLimitMessage()
  }

  if (status === 502 || status === 503) {
    return [
      'JPilot could not reach the AI provider or backend service.',
      '',
      '**What you can do:**',
      '1. Confirm the backend is running and your **Model** provider is enabled under **AI Providers**.',
      '2. Retry in a moment; if this persists, check server logs.',
      '',
      cleaned ? `_Detail: ${cleaned}_` : ''
    ]
      .filter(Boolean)
      .join('\n')
  }

  return `Sorry, something went wrong.\n\n${cleaned}`
}

export function isGatewayTimeoutError(error) {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string' && detail.includes('gateway or upstream timeout')) {
    return true
  }
  const status = error?.response?.status
  const combined = `${detail || ''} ${error?.message || ''} ${error?.code || ''}`
  return status === 504 || isGatewayTimeoutLike(combined)
}

export function isProviderQuotaError(error) {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') {
    if (detail.includes('quota or credits are exhausted')) {
      return true
    }
    if (detail.includes('**What you can do:**') && !detail.includes('gateway or upstream timeout')) {
      return true
    }
  }
  return (
    error?.response?.status === 429 ||
    isQuotaLike(detail) ||
    isQuotaLike(error?.message) ||
    isContextLimitLike(detail) ||
    isContextLimitLike(error?.message)
  )
}
