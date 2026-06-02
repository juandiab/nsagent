import api from './api'

export function listUsers() {
  return api.get('/users')
}

export function createUser(payload) {
  return api.post('/users', payload)
}

export function updateUser(id, payload) {
  return api.put(`/users/${id}`, payload)
}

export function deleteUser(id) {
  return api.delete(`/users/${id}`)
}

export function getUser(id) {
  return api.get(`/users/${id}`)
}

export function deletePasskey(userId, passkeyId) {
  return api.delete(`/users/${userId}/passkeys/${passkeyId}`)
}
