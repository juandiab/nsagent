import { startAuthentication, startRegistration } from '@simplewebauthn/browser'
import api from './api'
import { setAuth } from './auth'

export async function fetchPasskeyStatus(username) {
  const { data } = await api.post('/auth/webauthn/status', { username: username.trim().toLowerCase() })
  return data
}

export async function registerPasskey(username, label = '') {
  const cleaned = username.trim().toLowerCase()
  const { data: options } = await api.post('/auth/webauthn/register/begin', { username: cleaned })
  const credential = await startRegistration({ optionsJSON: options })
  const { data } = await api.post('/auth/webauthn/register/finish', {
    username: cleaned,
    credential,
    label
  })
  return data
}

export async function loginWithPasskey(username) {
  const cleaned = username.trim().toLowerCase()
  const { data: options } = await api.post('/auth/webauthn/login/begin', { username: cleaned })
  const credential = await startAuthentication({ optionsJSON: options })
  const { data } = await api.post('/auth/webauthn/login/finish', {
    username: cleaned,
    credential
  })
  setAuth(data.accessToken, data.user)
  return data
}

export function passkeyErrorMessage(error) {
  if (error?.name === 'NotAllowedError') {
    return 'Passkey request was cancelled or timed out.'
  }
  if (error?.response?.data?.detail) {
    return typeof error.response.data.detail === 'string'
      ? error.response.data.detail
      : 'Passkey operation failed.'
  }
  return error?.message || 'Passkey operation failed.'
}
