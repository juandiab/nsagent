import api from './api'

export async function listInstalledCalibrations() {
  const { data } = await api.get('/copilot/calibrations')
  return data
}

export async function syncCalibrationsFromStudio() {
  const { data } = await api.post('/copilot/calibrations/sync')
  return data
}
