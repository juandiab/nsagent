import api from './api'

export async function generateSslCsr(payload) {
  const { data } = await api.post('/ssl/generate-csr', payload)
  return data
}
