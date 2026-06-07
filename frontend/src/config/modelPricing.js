/** Indicative list pricing for cloud models — not billing quotes. Updated manually. */

const LOCAL_PROVIDER_TYPES = new Set(['LM Studio', 'OpenAI-Compatible'])

/** First matching pattern wins (most specific patterns first). */
const MODEL_PRICING_BY_PROVIDER = {
  OpenAI: [
    { pattern: /gpt-4\.1-nano/i, cost: '≈ $0.10 / 1M in' },
    { pattern: /gpt-4\.1-mini/i, cost: '≈ $0.40 / 1M in' },
    { pattern: /gpt-4\.1/i, cost: '≈ $2 / 1M in' },
    { pattern: /gpt-4o-mini/i, cost: '≈ $0.15 / 1M in' },
    { pattern: /gpt-4o/i, cost: '≈ $2.50 / 1M in' },
    { pattern: /o3-mini/i, cost: '≈ $1.10 / 1M in' },
    { pattern: /\bo3\b/i, cost: '≈ $10 / 1M in' },
    { pattern: /o1-mini/i, cost: '≈ $1.10 / 1M in' },
    { pattern: /\bo1\b/i, cost: '≈ $15 / 1M in' },
    { pattern: /gpt-4-turbo/i, cost: '≈ $10 / 1M in' },
    { pattern: /gpt-4/i, cost: '≈ $30 / 1M in' },
    { pattern: /gpt-3\.5/i, cost: '≈ $0.50 / 1M in' }
  ],
  Anthropic: [
    { pattern: /claude-opus-4|claude-4-opus|claude-3-opus/i, cost: '≈ $15 / 1M in' },
    { pattern: /claude-sonnet-4|claude-4-sonnet|claude-3-7-sonnet/i, cost: '≈ $3 / 1M in' },
    { pattern: /claude-3-5-sonnet/i, cost: '≈ $3 / 1M in' },
    { pattern: /claude-3-5-haiku|claude-haiku-3-5|claude-3-haiku/i, cost: '≈ $0.80 / 1M in' },
    { pattern: /claude-3-sonnet/i, cost: '≈ $3 / 1M in' }
  ],
  Gemini: [
    { pattern: /gemini-2\.5-pro/i, cost: '≈ $1.25 / 1M in' },
    { pattern: /gemini-2\.0-pro/i, cost: '≈ $1.25 / 1M in' },
    { pattern: /gemini-1\.5-pro/i, cost: '≈ $1.25 / 1M in' },
    { pattern: /gemini-.*-flash/i, cost: '≈ $0.10 / 1M in' },
    { pattern: /gemini-2\.0-flash-thinking/i, cost: '≈ $0.10 / 1M in' },
    { pattern: /gemini/i, cost: '≈ $0.10 / 1M in' }
  ],
  Grok: [
    { pattern: /grok-3-mini/i, cost: '≈ $0.20 / 1M in' },
    { pattern: /grok-3/i, cost: '≈ $3 / 1M in' },
    { pattern: /grok-2-mini/i, cost: '≈ $0.20 / 1M in' },
    { pattern: /grok-2/i, cost: '≈ $2 / 1M in' }
  ],
  DeepSeek: [
    { pattern: /deepseek-reasoner|deepseek-r1/i, cost: '≈ $0.55 / 1M in' },
    { pattern: /deepseek-chat|deepseek-v3/i, cost: '≈ $0.27 / 1M in' },
    { pattern: /deepseek/i, cost: '≈ $0.27 / 1M in' }
  ],
  OpenRouter: [
    { pattern: /\/claude.*opus/i, cost: '≈ $15 / 1M in' },
    { pattern: /\/claude.*sonnet/i, cost: '≈ $3 / 1M in' },
    { pattern: /\/claude.*haiku/i, cost: '≈ $0.80 / 1M in' },
    { pattern: /\/gpt-4o-mini/i, cost: '≈ $0.15 / 1M in' },
    { pattern: /\/gpt-4o/i, cost: '≈ $2.50 / 1M in' },
    { pattern: /\/gemini.*flash/i, cost: '≈ $0.10 / 1M in' },
    { pattern: /\/gemini.*pro/i, cost: '≈ $1.25 / 1M in' },
    { pattern: /\//, cost: '≈ varies / 1M in' }
  ],
  'Azure OpenAI': [
    { pattern: /gpt-4o-mini/i, cost: '≈ $0.15 / 1M in' },
    { pattern: /gpt-4o/i, cost: '≈ $2.50 / 1M in' },
    { pattern: /gpt-4/i, cost: '≈ $30 / 1M in' },
    { pattern: /o1-mini/i, cost: '≈ $1.10 / 1M in' },
    { pattern: /\bo1\b/i, cost: '≈ $15 / 1M in' }
  ],
  'AWS Bedrock': [
    { pattern: /anthropic\.claude.*opus/i, cost: '≈ $15 / 1M in' },
    { pattern: /anthropic\.claude.*sonnet/i, cost: '≈ $3 / 1M in' },
    { pattern: /anthropic\.claude.*haiku/i, cost: '≈ $0.80 / 1M in' },
    { pattern: /meta\.llama/i, cost: '≈ $0.50 / 1M in' },
    { pattern: /amazon\.nova-micro/i, cost: '≈ $0.04 / 1M in' },
    { pattern: /amazon\.nova/i, cost: '≈ $0.25 / 1M in' }
  ]
}

const GENERIC_PRICING_FALLBACKS = [
  { pattern: /reasoner|reason|r1\b/i, cost: '≈ $0.55 / 1M in' },
  { pattern: /opus/i, cost: '≈ $15 / 1M in' },
  { pattern: /mini|nano|haiku/i, cost: '≈ $0.15 / 1M in' },
  { pattern: /flash(?!.*think)/i, cost: '≈ $0.10 / 1M in' },
  { pattern: /pro|sonnet|gpt-4/i, cost: '≈ $3 / 1M in' }
]

export function normalizeModelName(name) {
  return String(name || '')
    .trim()
    .replace(/^models\//i, '')
}

export function isLocalModelProvider(providerType) {
  return LOCAL_PROVIDER_TYPES.has(providerType)
}

/**
 * @param {string} modelName
 * @param {string} [providerType]
 * @returns {string|null}
 */
export function lookupModelCost(modelName, providerType = '') {
  const name = normalizeModelName(modelName)
  if (!name) return null

  if (isLocalModelProvider(providerType)) {
    return 'Local'
  }

  const providerRules = MODEL_PRICING_BY_PROVIDER[providerType] || []
  for (const rule of providerRules) {
    if (rule.pattern.test(name)) {
      return rule.cost
    }
  }

  if (providerType === 'OpenRouter' && name.includes('/')) {
    const suffix = name.split('/').slice(1).join('/')
    for (const rules of Object.values(MODEL_PRICING_BY_PROVIDER)) {
      if (rules === providerRules) continue
      for (const rule of rules) {
        if (rule.pattern.test(suffix)) {
          return rule.cost
        }
      }
    }
  }

  if (providerType === 'AWS Bedrock') {
    const bedrockName = name.replace(/^[^.]+\./, '').replace(/:\d+$/, '')
    for (const rules of Object.values(MODEL_PRICING_BY_PROVIDER)) {
      for (const rule of rules) {
        if (rule.pattern.test(bedrockName) || rule.pattern.test(name)) {
          return rule.cost
        }
      }
    }
  }

  for (const rule of GENERIC_PRICING_FALLBACKS) {
    if (rule.pattern.test(name)) {
      return rule.cost
    }
  }

  return null
}

/**
 * @param {string[]} models
 * @param {string} providerType
 * @returns {{ label: string, value: string, cost: string|null }[]}
 */
export function buildModelSelectOptions(models, providerType) {
  const list = Array.isArray(models) ? models : []
  return list
    .map(normalizeModelName)
    .filter(Boolean)
    .map((name) => ({
      label: name,
      value: name,
      cost: lookupModelCost(name, providerType)
    }))
}
