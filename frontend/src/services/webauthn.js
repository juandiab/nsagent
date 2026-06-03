import { startAuthentication, startRegistration } from '@simplewebauthn/browser'
import api from './api'
import { setAuth } from './auth'

export async function fetchPasskeyStatus(username) {
  const { data } = await api.post('/auth/webauthn/status', { username: username.trim().toLowerCase() })
  return data
}

export async function registerPasskey(username, label = '', recoveryToken = null) {
  const cleaned = username.trim().toLowerCase()
  const body = { username: cleaned }
  if (recoveryToken) {
    body.recoveryToken = recoveryToken
  }
  const { data: options } = await api.post('/auth/webauthn/register/begin', body)
  const credential = await startRegistration({ optionsJSON: options })
  const finishBody = {
    username: cleaned,
    credential,
    label
  }
  if (recoveryToken) {
    finishBody.recoveryToken = recoveryToken
  }
  const { data } = await api.post('/auth/webauthn/register/finish', finishBody)
  if (data.accessToken) {
    setAuth(data.accessToken, data.user)
  }
  return data
}

export async function loginWithPasskey(username, { preferCrossDevice = false } = {}) {
  const cleaned = username.trim().toLowerCase()
  const { data: options } = await api.post('/auth/webauthn/login/begin', {
    username: cleaned,
    preferCrossDevice
  })
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
