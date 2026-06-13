/** Stack Calibration Studio public base URL (informational; API calls go through JPilot backend). */
export const CALIBRATION_STUDIO_BASE_URL = 'https://scstudio.nexxus-tech.com'

export const CALIBRATION_FEEDBACK_CATEGORIES = [
  { value: 'too_slow', label: 'Too slow / too many steps' },
  { value: 'tool_limit', label: 'Hit tool call limit' },
  { value: 'skill_not_triggered', label: 'Wrong workflow / skill did not apply' },
  { value: 'wrong_tool', label: 'Used the wrong tools' },
  { value: 'missing_step', label: 'Missing steps or sections' },
  { value: 'wrong_answer', label: 'Incorrect or incomplete answer' },
  { value: 'other', label: 'Other' }
]

export const CALIBRATION_SUGGESTED_SKILLS = {
  'nexxus-netscaler-firmware-ha-upgrade': 'NetScaler firmware HA upgrade (change control)'
}
