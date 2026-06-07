import api from './api'

export async function getSecuritySettings() {
  const { data } = await api.get('/security/settings')
  return data
}

export async function saveSecuritySettings(payload) {
  const { data } = await api.put('/security/settings', payload)
  return data
}

export async function getTlsCertificateStatus() {
  const { data } = await api.get('/security/tls/status')
  return data
}

export async function validateTlsCertificate(payload) {
  const { data } = await api.post('/security/tls/validate', payload)
  return data
}

export async function applyTlsCertificate(payload) {
  const { data } = await api.post('/security/tls/apply', payload)
  return data
}

export const PASSKEY_POLICY_OPTIONS = [
  {
    value: 'disabled',
    label: 'Disable',
    description: 'Turn off passkey sign-in and registration for all users.'
  },
  {
    value: 'enabled',
    label: 'Enable',
    description: 'Recommended. Passkeys are optional; once registered, password sign-in is disabled for that account.'
  },
  {
    value: 'enforced',
    label: 'Enforce',
    description: 'Require every user to register a passkey. Password sign-in is only available until a passkey is set up.'
  }
]

export function passkeyPolicyLabel(value) {
  return PASSKEY_POLICY_OPTIONS.find((option) => option.value === value)?.label || 'Enable'
}

export function passkeyPolicyDescription(value) {
  return PASSKEY_POLICY_OPTIONS.find((option) => option.value === value)?.description || ''
}
