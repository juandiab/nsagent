import api from './api'

export async function getSmtpConfig() {
  const { data } = await api.get('/mcp/smtp')
  return data
}

export async function saveSmtpConfig(payload) {
  const { data } = await api.put('/mcp/smtp', payload)
  return data
}

export async function testSmtpConfig(payload) {
  const { data } = await api.post('/mcp/smtp/test', payload)
  return data
}
