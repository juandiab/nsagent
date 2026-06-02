import api from './api'

export async function getCopilotPlatformSettings() {
  const { data } = await api.get('/copilot/platform-settings')
  return data
}

export async function saveCopilotPlatformSettings(payload) {
  const { data } = await api.put('/copilot/platform-settings', payload)
  return data
}

export async function testCopilotPlatformSearch(payload) {
  const { data } = await api.post('/copilot/platform-settings/test', payload)
  return data
}
