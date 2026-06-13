import api from './api'

export async function getCalibrationFeedbackStatus() {
  const { data } = await api.get('/copilot/calibration-feedback/status')
  return data
}

export async function sendCalibrationFeedback(payload) {
  const { data } = await api.post('/copilot/calibration-feedback', payload)
  return data
}
