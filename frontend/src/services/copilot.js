import api from './api'

const STORAGE_KEY = 'copilot_settings'

const DEFAULT_SETTINGS = {
  allowImages: true,
  allowConfigFiles: true,
  maxAttachments: 5,
  notifyWhenReplyComplete: true,
  playReplySound: true
}

export function getCopilotSettings() {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return { ...DEFAULT_SETTINGS }
  try {
    return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) }
  } catch {
    return { ...DEFAULT_SETTINGS }
  }
}

export function saveCopilotSettings(settings) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...DEFAULT_SETTINGS, ...settings }))
}

export const IMAGE_ACCEPT = 'image/png,image/jpeg,image/webp,image/gif'
export const CONFIG_ACCEPT =
  '.conf,.cfg,.txt,.json,.yaml,.yml,.xml,.properties,.ini,.ns,.cs,.csv,.md,.markdown'

export const MAX_IMAGE_BYTES = 5 * 1024 * 1024
export const MAX_CONFIG_BYTES = 1024 * 1024

export function isImageFile(file) {
  return file.type.startsWith('image/')
}

export function isConfigFile(file) {
  const name = file.name.toLowerCase()
  return CONFIG_ACCEPT.split(',').some((ext) => name.endsWith(ext))
}

export async function fileToAttachment(file) {
  if (isImageFile(file)) {
    if (file.size > MAX_IMAGE_BYTES) {
      throw new Error(`Image '${file.name}' exceeds 5 MB`)
    }
    const data = await readAsBase64(file)
    return {
      name: file.name,
      kind: 'image',
      mimeType: file.type,
      data
    }
  }

  if (isConfigFile(file)) {
    if (file.size > MAX_CONFIG_BYTES) {
      throw new Error(`Config file '${file.name}' exceeds 1 MB`)
    }
    const text = await readAsText(file)
    return {
      name: file.name,
      kind: 'config',
      mimeType: file.type || 'text/plain',
      data: text
    }
  }

  throw new Error(`Unsupported file type: ${file.name}`)
}

function readAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result
      const base64 = result.split(',')[1]
      resolve(base64)
    }
    reader.onerror = () => reject(new Error(`Failed to read ${file.name}`))
    reader.readAsDataURL(file)
  })
}

function readAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => reject(new Error(`Failed to read ${file.name}`))
    reader.readAsText(file)
  })
}

export function attachmentPreviewUrl(attachment) {
  if (attachment.kind !== 'image') return null
  return `data:${attachment.mimeType};base64,${attachment.data}`
}

const SESSION_APPLIANCE_KEY = 'copilot_connected_appliance'

export function getConnectedAppliance() {
  return sessionStorage.getItem(SESSION_APPLIANCE_KEY) || ''
}

export function setConnectedAppliance(name) {
  if (name) {
    sessionStorage.setItem(SESSION_APPLIANCE_KEY, name)
  } else {
    sessionStorage.removeItem(SESSION_APPLIANCE_KEY)
  }
}

export async function listCopilotAppliances() {
  const { data } = await api.get('/copilot/appliances')
  return data
}

export async function connectCopilotAppliance(applianceName) {
  const { data } = await api.post('/copilot/connect', { applianceName })
  return data
}

// Enabled AI providers, for the per-pane model picker. The default provider first.
export async function listChatProviders() {
  const { data } = await api.get('/ai-providers')
  const enabled = (data || []).filter((p) => p.enabled)
  enabled.sort((a, b) => (b.isDefault ? 1 : 0) - (a.isDefault ? 1 : 0))
  return enabled
}

// Background images bundled in frontend/public/backgrounds.
export const CHAT_BACKGROUNDS = [
  { id: '01', url: '/backgrounds/01.jpg' },
  { id: '02', url: '/backgrounds/02.jpg' },
  { id: '03', url: '/backgrounds/03.jpg' },
  { id: '04', url: '/backgrounds/04.jpg' }
]

const BG_KEY = 'jpilot_background'

export function getChatBackground() {
  const saved = localStorage.getItem(BG_KEY)
  if (saved === 'none') return 'none'
  return saved || CHAT_BACKGROUNDS[0].url
}

export function setChatBackground(url) {
  localStorage.setItem(BG_KEY, url || 'none')
}

/** Animated backgrounds for JPilot Beta chat only. */
export const BETA_CHAT_BACKGROUNDS = [
  { id: 'constellation', label: 'Constellation', base: 'white' },
  { id: 'waves', label: 'Waves', base: 'white' },
  { id: 'drift', label: 'Drift', base: 'black' },
  { id: 'orbit', label: 'Orbit', base: 'black' }
]

const BETA_BG_KEY = 'jpilot_beta_background'
const BETA_BG_IDS = new Set([...BETA_CHAT_BACKGROUNDS.map((bg) => bg.id), 'none'])

export function getBetaChatBackground() {
  const saved = localStorage.getItem(BETA_BG_KEY)
  if (saved && BETA_BG_IDS.has(saved)) return saved
  return BETA_CHAT_BACKGROUNDS[0].id
}

export function setBetaChatBackground(id) {
  localStorage.setItem(BETA_BG_KEY, BETA_BG_IDS.has(id) ? id : 'constellation')
}
