import api from './api'

let cachedPortalConfig = null
let pendingPortalConfig = null

const DEFAULT_PORTAL_CONFIG = { displayHomePage: true }

export function clearPortalConfigCache() {
  cachedPortalConfig = null
  pendingPortalConfig = null
}

export async function getPortalConfig({ force = false } = {}) {
  if (!force && cachedPortalConfig) {
    return cachedPortalConfig
  }

  if (!force && pendingPortalConfig) {
    return pendingPortalConfig
  }

  pendingPortalConfig = api
    .get('/system/portal-config')
    .then(({ data }) => {
      cachedPortalConfig = {
        displayHomePage: Boolean(data?.displayHomePage ?? DEFAULT_PORTAL_CONFIG.displayHomePage)
      }
      return cachedPortalConfig
    })
    .catch(() => DEFAULT_PORTAL_CONFIG)
    .finally(() => {
      pendingPortalConfig = null
    })

  return pendingPortalConfig
}

export async function getJpilotSettings() {
  const { data } = await api.get('/system/jpilot-settings')
  return data
}

export async function saveJpilotSettings(payload) {
  const { data } = await api.put('/system/jpilot-settings', payload)
  clearPortalConfigCache()
  return data
}
