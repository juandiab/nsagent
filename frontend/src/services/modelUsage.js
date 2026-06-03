import api from './api'

export async function getModelUsageDashboard() {
  const { data } = await api.get('/copilot/usage-dashboard')
  return data
}

export async function saveModelUsageLimits(payload) {
  const { data } = await api.put('/copilot/usage-limits', payload)
  return data
}

export function formatCount(value) {
  const n = Number(value) || 0
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return String(n)
}
