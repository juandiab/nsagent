import {
  resolveContextLimits,
  resolveMaxHistoryMessages,
  resolveSystemPromptTokenOverhead
} from '../config/modelContextWindows'

function estimateTextTokens(text) {
  if (!text) return 0
  return Math.ceil(String(text).length / 4)
}

function estimateAttachmentTokens(attachment) {
  if (!attachment) return 0
  if (attachment.kind === 'image' && attachment.data) {
    return Math.ceil(String(attachment.data).length / 4)
  }
  if (attachment.data) {
    return estimateTextTokens(typeof attachment.data === 'string' ? attachment.data : '')
  }
  return estimateTextTokens(attachment.name)
}

function estimateToolCallTokens(toolCalls) {
  if (!Array.isArray(toolCalls) || !toolCalls.length) return 0
  let tokens = 0
  for (const tool of toolCalls) {
    tokens += estimateTextTokens(tool.name)
    tokens += estimateTextTokens(JSON.stringify(tool.arguments || {}))
    tokens += estimateTextTokens(tool.result)
  }
  return tokens
}

function estimateMessageTokens(message) {
  if (!message) return 0
  let tokens = estimateTextTokens(message.content) + 4
  tokens += estimateToolCallTokens(message.toolCalls)
  if (Array.isArray(message.attachments)) {
    for (const attachment of message.attachments) {
      tokens += estimateAttachmentTokens(attachment)
    }
  }
  return tokens
}

function conversationalMessages(messages) {
  return (messages || []).filter(
    (message) =>
      (message.role === 'user' || message.role === 'assistant') &&
      message.content &&
      !message.appliancePicker
  )
}

export function estimateSessionContextUsage({
  messages = [],
  draftInput = '',
  pendingAttachments = [],
  model = '',
  providerType = ''
}) {
  const limits = resolveContextLimits(model, providerType)
  const history = conversationalMessages(messages)
  const maxHistoryMessages = limits.maxHistoryMessages
  const trimmed = history.slice(-maxHistoryMessages)
  let promptTokens = limits.systemPromptOverhead

  for (const message of trimmed) {
    promptTokens += estimateMessageTokens(message)
  }

  if (draftInput.trim()) {
    promptTokens += estimateMessageTokens({ role: 'user', content: draftInput.trim() })
  }
  for (const attachment of pendingAttachments || []) {
    promptTokens += estimateAttachmentTokens(attachment)
  }

  const contextTokenLimit = limits.tokenLimit
  const usableLimit = Math.max(
    contextTokenLimit - Math.min(8192, Math.floor(contextTokenLimit * 0.08)),
    1
  )
  const percentUsed = Math.min(100, (promptTokens / usableLimit) * 100)

  return {
    promptTokens,
    contextTokenLimit,
    usableLimit,
    percentUsed,
    messageCount: trimmed.length,
    maxHistoryMessages,
    trimmedCount: Math.max(0, history.length - maxHistoryMessages)
  }
}

export function formatTokenCount(value) {
  const n = Number(value) || 0
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1000) return `${Math.round(n / 1000)}k`
  return String(Math.round(n))
}

export { resolveMaxHistoryMessages, resolveSystemPromptTokenOverhead }
