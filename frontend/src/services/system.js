import api from './api'

export async function getSystemVersion() {
  const { data } = await api.get('/system/version')
  return data
}

export async function checkForUpdates(force = false) {
  const { data } = await api.get('/system/update-check', { params: { force } })
  return data
}

export async function getLicenseFingerprint() {
  const { data } = await api.get('/system/license-fingerprint')
  return data
}

/** Loads license (creates record with fingerprint on first visit). */
export async function getLicense() {
  const { data } = await api.get('/system/license')
  return data
}

/** Saves license code and syncs with the Nexxus licensing server. */
export async function saveLicenseCode(licenseCode) {
  const { data } = await api.put('/system/license', { licenseCode })
  return data
}

/** Removes the current license; keeps installation fingerprint for a new activation. */
export async function removeLicense() {
  const { data } = await api.delete('/system/license')
  return data
}

/** Imports a Nexxus offline ``.lic`` file (parsed in memory; stored in the local DB). */
export async function importOfflineLicense(file) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/system/license/import-offline', form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return data
}
