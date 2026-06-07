/** Cloud LLM providers — local / self-hosted endpoints are excluded from role picks. */
import { lookupModelCost, normalizeModelName } from './modelPricing'

export const PUBLIC_CLOUD_PROVIDER_TYPES = [
  'OpenAI',
  'Anthropic',
  'Gemini',
  'Grok',
  'DeepSeek',
  'OpenRouter',
  'Azure OpenAI',
  'AWS Bedrock'
]

export const ROLE_SUGGESTION_THEMES = {
  architect: {
    label: 'Architect',
    tagline: 'Planning & design',
    icon: 'pi pi-compass'
  },
  operator: {
    label: 'Operator',
    tagline: 'Build & configure',
    icon: 'pi pi-cog'
  },
  analyst: {
    label: 'Analyst',
    tagline: 'Triage & diagnostics',
    icon: 'pi pi-search'
  }
}

const ROLE_HEURISTICS = {
  architect: {
    prefer: [
      /\bo3\b(?!-mini)/i,
      /\bo1(?!-mini)/i,
      /reason/i,
      /opus/i,
      /pro/i,
      /sonnet/i,
      /think/i
    ],
    avoid: [/mini/i, /nano/i, /haiku/i, /flash(?!.*think)/i]
  },
  operator: {
    prefer: [/mini/i, /flash/i, /nano/i, /haiku/i, /3\.5-turbo/i, /chat/i],
    avoid: [/opus/i, /reasoner/i, /reason/i, /\bo1\b/i, /\bo3\b/i]
  },
  analyst: {
    prefer: [/sonnet/i, /pro/i, /think/i, /gpt-4o(?!-mini)/i, /flash.*think/i],
    avoid: [/nano/i, /haiku/i]
  }
}

/**
 * Ideal model picks per cloud provider and JPilot role.
 * `patterns` are tested in order against models returned by the provider API.
 * Costs are indicative list pricing for quick comparison — not billing quotes.
 */
const PROVIDER_ROLE_SUGGESTIONS = {
  OpenAI: {
    architect: {
      patterns: [/gpt-4\.1(?!-nano)/i, /\bo3\b(?!-mini)/i, /\bo1(?!-mini)/i, /gpt-4o(?!-mini)/i],
      fallbackLabel: 'GPT-4.1 / o3',
      blurb: 'Strong reasoning for discovery flows and formal design documents.',
      cost: '≈ $2–15 / 1M in'
    },
    operator: {
      patterns: [/gpt-4o-mini/i, /gpt-4\.1-nano/i, /gpt-3\.5/i],
      fallbackLabel: 'GPT-4o mini',
      blurb: 'Fast, reliable tool calling for day-to-day CLI and API changes.',
      cost: '≈ $0.15 / 1M in'
    },
    analyst: {
      patterns: [/gpt-4o(?!-mini)/i, /gpt-4\.1-mini/i, /gpt-4-turbo/i],
      fallbackLabel: 'GPT-4o',
      blurb: 'Balanced depth for correlating logs, stats, and live diagnostics.',
      cost: '≈ $2.50 / 1M in'
    }
  },
  Anthropic: {
    architect: {
      patterns: [/claude-opus-4|claude-4-opus/i, /claude-sonnet-4|claude-4-sonnet/i, /claude-3-7-sonnet/i],
      fallbackLabel: 'Claude Sonnet 4 / Opus',
      blurb: 'Excellent at structured architecture narratives and trade-off analysis.',
      cost: '≈ $3–15 / 1M in'
    },
    operator: {
      patterns: [/claude-3-5-haiku|claude-haiku-3-5/i, /claude-3-haiku/i],
      fallbackLabel: 'Claude 3.5 Haiku',
      blurb: 'Low latency for repetitive operational tasks and form-driven builds.',
      cost: '≈ $0.80 / 1M in'
    },
    analyst: {
      patterns: [/claude-sonnet-4|claude-4-sonnet/i, /claude-3-7-sonnet/i, /claude-3-5-sonnet/i],
      fallbackLabel: 'Claude Sonnet 4',
      blurb: 'Clear incident write-ups with careful read-only evidence gathering.',
      cost: '≈ $3 / 1M in'
    }
  },
  Gemini: {
    architect: {
      patterns: [/gemini-2\.5-pro/i, /gemini-2\.0-pro/i, /gemini-1\.5-pro/i],
      fallbackLabel: 'Gemini 2.5 Pro',
      blurb: 'Large context for complex multi-site designs and attached diagrams.',
      cost: '≈ $1.25 / 1M in'
    },
    operator: {
      patterns: [/gemini-2\.5-flash/i, /gemini-2\.0-flash/i, /gemini-1\.5-flash/i, /gemini-.*-flash/i],
      fallbackLabel: 'Gemini Flash',
      blurb: 'Cost-efficient execution with solid function calling.',
      cost: '≈ $0.10 / 1M in'
    },
    analyst: {
      patterns: [/gemini-2\.5-pro/i, /gemini-2\.0-flash-thinking/i, /gemini-2\.5-flash/i],
      fallbackLabel: 'Gemini 2.5 Pro / Flash',
      blurb: 'Good at weaving attachments with appliance readouts.',
      cost: '≈ $0.10–1.25 / 1M in'
    }
  },
  Grok: {
    architect: {
      patterns: [/grok-3(?!-mini)/i, /grok-2/i],
      fallbackLabel: 'Grok 3',
      blurb: 'Capable reasoning for greenfield and migration designs.',
      cost: '≈ $3 / 1M in'
    },
    operator: {
      patterns: [/grok-3-mini/i, /grok-2-mini/i, /grok-2/i],
      fallbackLabel: 'Grok mini / Grok 2',
      blurb: 'Responsive model for operational changes and tool loops.',
      cost: '≈ $0.20 / 1M in'
    },
    analyst: {
      patterns: [/grok-3(?!-mini)/i, /grok-2/i],
      fallbackLabel: 'Grok 3',
      blurb: 'Structured troubleshooting narratives from symptoms to root cause.',
      cost: '≈ $3 / 1M in'
    }
  },
  DeepSeek: {
    architect: {
      patterns: [/deepseek-reasoner/i, /deepseek-r1/i],
      fallbackLabel: 'DeepSeek Reasoner',
      blurb: 'Deep thinking for HA, migration, and capacity planning.',
      cost: '≈ $0.55 / 1M in'
    },
    operator: {
      patterns: [/deepseek-chat/i, /deepseek-v3/i],
      fallbackLabel: 'DeepSeek Chat',
      blurb: 'Very affordable daily driver for config work.',
      cost: '≈ $0.27 / 1M in'
    },
    analyst: {
      patterns: [/deepseek-chat/i, /deepseek-reasoner/i],
      fallbackLabel: 'DeepSeek Chat / Reasoner',
      blurb: 'Cost-effective RCA when you need more than a flash model.',
      cost: '≈ $0.27–0.55 / 1M in'
    }
  },
  OpenRouter: {
    architect: {
      patterns: [
        /anthropic\/claude.*opus/i,
        /anthropic\/claude.*sonnet/i,
        /openai\/o3(?!-mini)/i,
        /openai\/o1(?!-mini)/i,
        /google\/gemini.*pro/i
      ],
      fallbackLabel: 'Claude / o-series / Gemini Pro',
      blurb: 'Strong reasoning via OpenRouter for design docs and discovery.',
      cost: '≈ $3–15 / 1M in'
    },
    operator: {
      patterns: [
        /openai\/gpt-4o-mini/i,
        /google\/gemini.*flash/i,
        /anthropic\/claude.*haiku/i,
        /meta-llama\/llama.*8b/i
      ],
      fallbackLabel: 'Flash / mini / Haiku',
      blurb: 'Fast, affordable tool calling through OpenRouter.',
      cost: '≈ $0.10–0.80 / 1M in'
    },
    analyst: {
      patterns: [
        /anthropic\/claude.*sonnet/i,
        /openai\/gpt-4o(?!-mini)/i,
        /google\/gemini.*pro/i
      ],
      fallbackLabel: 'Sonnet / GPT-4o / Gemini Pro',
      blurb: 'Balanced models for incident write-ups and evidence review.',
      cost: '≈ $1–3 / 1M in'
    }
  },
  'Azure OpenAI': {
    architect: {
      patterns: [/o1(?!-mini)/i, /o3(?!-mini)/i, /gpt-4/i, /gpt-4\.1(?!-nano)/i],
      fallbackLabel: 'GPT-4.1 / o-series deployment',
      blurb: 'Use your strongest Azure deployment for architecture work.',
      cost: '≈ $2–15 / 1M in'
    },
    operator: {
      patterns: [/mini/i, /nano/i, /gpt-35/i, /gpt-3\.5/i],
      fallbackLabel: 'Mini / GPT-3.5 deployment',
      blurb: 'Pick a low-cost Azure deployment for operational changes.',
      cost: '≈ $0.15 / 1M in'
    },
    analyst: {
      patterns: [/gpt-4o(?!-mini)/i, /gpt-4\.1-mini/i, /gpt-4-turbo/i],
      fallbackLabel: 'GPT-4o deployment',
      blurb: 'Mid-tier Azure deployment for diagnostics and RCA.',
      cost: '≈ $2.50 / 1M in'
    }
  },
  'AWS Bedrock': {
    architect: {
      patterns: [
        /anthropic\.claude.*opus/i,
        /anthropic\.claude-3-7/i,
        /anthropic\.claude.*sonnet/i
      ],
      fallbackLabel: 'Claude Opus / Sonnet on Bedrock',
      blurb: 'Enterprise-grade reasoning inside your AWS account boundary.',
      cost: '≈ $3–15 / 1M in'
    },
    operator: {
      patterns: [/anthropic\.claude.*haiku/i, /amazon\.nova-micro/i, /amazon\.nova-lite/i],
      fallbackLabel: 'Haiku / Nova Lite',
      blurb: 'Low-latency Bedrock models for config and tool loops.',
      cost: '≈ $0.04–0.80 / 1M in'
    },
    analyst: {
      patterns: [/anthropic\.claude.*sonnet/i, /amazon\.nova-pro/i],
      fallbackLabel: 'Claude Sonnet / Nova Pro',
      blurb: 'Solid Bedrock picks for structured troubleshooting.',
      cost: '≈ $1–3 / 1M in'
    }
  }
}

export function isPublicCloudProvider(providerType) {
  return PUBLIC_CLOUD_PROVIDER_TYPES.includes(providerType)
}

function findMatchingModel(patterns, models) {
  for (const pattern of patterns) {
    const hit = models.find((name) => pattern.test(normalizeModelName(name)))
    if (hit) return hit
  }
  return null
}

function scoreModelForRole(modelName, roleId) {
  const name = normalizeModelName(modelName)
  const rules = ROLE_HEURISTICS[roleId]
  if (!rules) return 0

  let score = 0
  for (const pattern of rules.prefer) {
    if (pattern.test(name)) score += 10
  }
  for (const pattern of rules.avoid) {
    if (pattern.test(name)) score -= 8
  }
  return score
}

function findNextBestModel(models, roleId, exclude = new Set()) {
  const candidates = models
    .filter((name) => !exclude.has(name))
    .map((name) => ({ name, score: scoreModelForRole(name, roleId) }))
    .filter((entry) => entry.score > 0)
    .sort((a, b) => b.score - a.score || a.name.localeCompare(b.name))

  return candidates[0]?.name || null
}

/**
 * Pick the best available model for a role: ideal pattern match first, then heuristic fallback.
 * @param {{ patterns: RegExp[], fallbackLabel: string }} pick
 * @param {string[]} models
 * @param {string} roleId
 * @param {Set<string>} usedModels
 */
function resolveRoleModel(pick, models, roleId, usedModels) {
  const available = models.filter((name) => !usedModels.has(name))
  const pool = available.length ? available : models

  const ideal = findMatchingModel(pick.patterns, pool)
  if (ideal) {
    return { model: ideal, isIdeal: true }
  }

  const heuristic = findNextBestModel(pool, roleId, usedModels)
  if (heuristic) {
    return { model: heuristic, isIdeal: false }
  }

  const anyLeft = pool.find((name) => !usedModels.has(name)) || pool[0] || null
  if (anyLeft) {
    return { model: anyLeft, isIdeal: false }
  }

  return { model: null, isIdeal: false }
}

/**
 * @param {string} providerType
 * @param {string[]} availableModels
 * @returns {{
 *   roleId: string,
 *   theme: object,
 *   model: string|null,
 *   modelLabel: string,
 *   blurb: string,
 *   cost: string,
 *   available: boolean,
 *   isIdeal: boolean
 * }[]}
 */
export function buildRoleSuggestions(providerType, availableModels = []) {
  if (!isPublicCloudProvider(providerType)) {
    return []
  }

  const providerConfig = PROVIDER_ROLE_SUGGESTIONS[providerType]
  if (!providerConfig) {
    return []
  }

  const models = (Array.isArray(availableModels) ? availableModels : [])
    .map(normalizeModelName)
    .filter(Boolean)

  if (!models.length) {
    return []
  }

  const usedModels = new Set()
  const roleIds = ['architect', 'operator', 'analyst']

  return roleIds.map((roleId) => {
    const pick = providerConfig[roleId]
    const theme = ROLE_SUGGESTION_THEMES[roleId]
    const { model, isIdeal } = resolveRoleModel(pick, models, roleId, usedModels)

    if (model) {
      usedModels.add(model)
    }

    const cost = model
      ? lookupModelCost(model, providerType) || pick.cost
      : pick.cost

    return {
      roleId,
      theme,
      model,
      modelLabel: model || pick.fallbackLabel,
      blurb: pick.blurb,
      cost,
      available: Boolean(model),
      isIdeal
    }
  })
}
