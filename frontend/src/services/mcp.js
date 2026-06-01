import api from './api'

export async function getMcpConfig() {
  const { data } = await api.get('/mcp/config')
  return data
}

export async function saveMcpConfig(payload) {
  const { data } = await api.put('/mcp/config', payload)
  return data
}

export async function getMcpStatus() {
  const { data } = await api.get('/mcp/status')
  return data
}
