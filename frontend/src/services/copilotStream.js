import { getToken } from './auth'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function buildStreamError(event) {
  const error = new Error(
    typeof event.detail === 'string' ? event.detail : event.detail?.message || 'Copilot request failed'
  )
  error.response = {
    status: event.status || 502,
    data: { detail: event.detail }
  }
  return error
}

export async function streamCopilotChat(payload, { signal, onEvent } = {}) {
  const headers = { 'Content-Type': 'application/json', Accept: 'text/event-stream' }
  const token = getToken()
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(`${baseURL}/copilot/chat/stream`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
    signal
  })

  if (!response.ok) {
    let detail = `Copilot request failed (${response.status})`
    try {
      const body = await response.json()
      detail = body.detail || detail
    } catch {
      // ignore parse errors
    }
    const error = new Error(typeof detail === 'string' ? detail : detail?.message || 'Copilot request failed')
    error.response = { status: response.status, data: { detail } }
    throw error
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('Streaming response is not supported in this browser')
  }

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const chunks = buffer.split('\n\n')
    buffer = chunks.pop() || ''

    for (const chunk of chunks) {
      const line = chunk.split('\n').find((entry) => entry.startsWith('data: '))
      if (!line) continue

      const event = JSON.parse(line.slice(6))
      onEvent?.(event)

      if (event.type === 'done') {
        return event.response
      }
      if (event.type === 'error') {
        throw buildStreamError(event)
      }
    }
  }

  throw new Error('Stream ended before the reply was ready')
}
