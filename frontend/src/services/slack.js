import api from './api'

export async function getSlackConfig() {
  const { data } = await api.get('/integrations/slack')
  return data
}

export async function saveSlackConfig(payload) {
  const { data } = await api.put('/integrations/slack', payload)
  return data
}

export async function testSlackConfig(payload) {
  const { data } = await api.post('/integrations/slack/test', payload)
  return data
}
