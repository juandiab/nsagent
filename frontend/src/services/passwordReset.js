import api from './api'

export function confirmPasswordReset({ username, code, newPassword }) {
  return api.post('/auth/password-reset/confirm', {
    username,
    code,
    newPassword
  })
}
