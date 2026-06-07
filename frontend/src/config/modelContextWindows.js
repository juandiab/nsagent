/** Context budgeting tiers — keep in sync with backend context_limits.py */
export const MAX_HISTORY_MESSAGES = 20

/** @deprecated Use resolveMaxHistoryMessages(contextTokenLimit) for model-aware limits. */
export const LEGACY_MAX_HISTORY_MESSAGES = MAX_HISTORY_MESSAGES

/** Rough system prompt + tool schema overhead sent each turn (128k+ models). */
export const SYSTEM_PROMPT_TOKEN_OVERHEAD = 4000

const MODEL_CONTEXT_PATTERNS = [
  { pattern: /gpt-4\.1/i, tokens: 1_047_576 },
  { pattern: /gpt-4o-mini/i, tokens: 128_000 },
  { pattern: /gpt-4o/i, tokens: 128_000 },
  { pattern: /gpt-4-turbo/i, tokens: 128_000 },
  { pattern: /gpt-4/i, tokens: 8192 },
  { pattern: /gpt-3\.5/i, tokens: 16_385 },
  { pattern: /o1-mini/i, tokens: 128_000 },
  { pattern: /o1-preview|o1\b/i, tokens: 128_000 },
  { pattern: /o3-mini/i, tokens: 200_000 },
  { pattern: /claude-opus-4|claude-sonnet-4|claude-3-7/i, tokens: 200_000 },
  { pattern: /claude-3-5-sonnet|claude-3-5-haiku/i, tokens: 200_000 },
  { pattern: /claude-3-opus|claude-3-sonnet|claude-3-haiku/i, tokens: 200_000 },
  { pattern: /claude/i, tokens: 200_000 },
  { pattern: /gemini-2\.5|gemini-2\.0|gemini-1\.5-pro|gemini-1\.5-flash/i, tokens: 1_048_576 },
  { pattern: /gemini/i, tokens: 128_000 },
  { pattern: /grok-3|grok-2/i, tokens: 131_072 },
  { pattern: /grok/i, tokens: 131_072 },
  { pattern: /deepseek-reasoner|deepseek-r1/i, tokens: 64_000 },
  { pattern: /deepseek/i, tokens: 64_000 },
  { pattern: /llama-3\.3|llama-3\.2|llama-3\.1|llama3/i, tokens: 128_000 },
  { pattern: /qwen2\.5|qwen/i, tokens: 128_000 },
  { pattern: /mistral-large|mixtral|mistral/i, tokens: 128_000 },
  { pattern: /phi-3|phi-4/i, tokens: 128_000 }
]

const PROVIDER_DEFAULT_CONTEXT = {
  OpenAI: 128_000,
  Anthropic: 200_000,
  Gemini: 1_048_576,
  Grok: 131_072,
  DeepSeek: 64_000,
  OpenRouter: 128_000,
  'Azure OpenAI': 128_000,
  'AWS Bedrock': 200_000,
  'LM Studio': 32_768,
  'OpenAI-Compatible': 32_768
}

export function resolveContextTokenLimit(model, providerType) {
  const name = String(model || '').trim()
  if (name) {
    for (const entry of MODEL_CONTEXT_PATTERNS) {
      if (entry.pattern.test(name)) return entry.tokens
    }
  }
  return PROVIDER_DEFAULT_CONTEXT[providerType] || 128_000
}

export function resolveMaxHistoryMessages(contextTokenLimit) {
  const limit = Number(contextTokenLimit) || 128_000
  if (limit >= 1_000_000) return 48
  if (limit >= 512_000) return 36
  if (limit >= 200_000) return 28
  if (limit >= 128_000) return 20
  if (limit >= 64_000) return 14
  if (limit >= 32_768) return 10
  if (limit >= 16_000) return 8
  return 6
}

export function resolveMaxToolResultChars(contextTokenLimit) {
  const limit = Number(contextTokenLimit) || 128_000
  if (limit >= 512_000) return 16_000
  if (limit >= 128_000) return 12_000
  if (limit >= 64_000) return 8_000
  if (limit >= 32_768) return 5_000
  return 3_000
}

export function resolveSystemPromptTokenOverhead(contextTokenLimit) {
  const limit = Number(contextTokenLimit) || 128_000
  if (limit >= 128_000) return 4000
  if (limit >= 32_768) return 3500
  return 3000
}

export function resolveContextLimits(model, providerType) {
  const tokenLimit = resolveContextTokenLimit(model, providerType)
  return {
    tokenLimit,
    maxHistoryMessages: resolveMaxHistoryMessages(tokenLimit),
    maxToolResultChars: resolveMaxToolResultChars(tokenLimit),
    systemPromptOverhead: resolveSystemPromptTokenOverhead(tokenLimit)
  }
}
