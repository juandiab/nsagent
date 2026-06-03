import api from './api'

export function requestAccountRecovery(username) {
  return api.post('/auth/account-recovery/request', {
    username: username.trim().toLowerCase()
  })
}

export function confirmAccountRecovery({ username, code, newPassword }) {
  const payload = {
    username: username.trim().toLowerCase(),
    code: code.trim()
  }
  if (newPassword?.trim()) {
    payload.newPassword = newPassword
  }
  return api.post('/auth/password-reset/confirm', payload)
}
