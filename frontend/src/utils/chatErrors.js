const QUOTA_HINTS = [
  'quota exceeded',
  'exceeded your current quota',
  'insufficient_quota',
  'resource_exhausted',
  'free_tier',
  'generativelanguage.googleapis.com'
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

function isQuotaLike(text) {
  const lowered = String(text || '').toLowerCase()
  return QUOTA_HINTS.some((hint) => lowered.includes(hint))
}

/**
 * Turn API error payloads into readable chat content.
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

  const parsed = tryParseJsonError(cleaned)
  if (parsed?.error?.message && isQuotaLike(JSON.stringify(parsed))) {
    return [
      'The selected AI model cannot complete this request because the API quota or credits are exhausted.',
      '',
      '**What you can do:**',
      '1. Switch to another provider using the **Model** dropdown in JPilot.',
      '2. Open **AI Providers** to add credits or configure another API key.',
      '3. If you are on a free tier, wait for the limit to reset and try again.',
      '',
      `_Provider message: ${parsed.error.message}_`
    ].join('\n')
  }

  if (status === 429 || isQuotaLike(cleaned)) {
    return [
      'The selected AI model hit a quota or rate limit.',
      '',
      '**What you can do:**',
      '1. Switch to another provider using the **Model** dropdown.',
      '2. Add credits or billing with your current provider, then retry.',
      '3. Wait a minute if this is a temporary rate limit.'
    ].join('\n')
  }

  return `Sorry, something went wrong.\n\n${cleaned}`
}

export function isProviderQuotaError(error) {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string' && detail.includes('**What you can do:**')) {
    return true
  }
  return error?.response?.status === 429 || isQuotaLike(detail) || isQuotaLike(error?.message)
}
