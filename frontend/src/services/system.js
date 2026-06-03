import api from './api'

export async function getSystemVersion() {
  const { data } = await api.get('/system/version')
  return data
}

export async function checkForUpdates(force = false) {
  const { data } = await api.get('/system/update-check', { params: { force } })
  return data
}
