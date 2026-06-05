/** Plan theme ids aligned with /plans card styles (plus trial). */
export const LICENSE_PLAN_THEME_LABELS = {
  free: 'Free Edition',
  trial: 'Trial',
  enterprise: 'Enterprise',
  'enterprise-pro': 'Enterprise Pro'
}

/** Normalize Nexxus licenseType strings to a plan theme id. */
export function resolveLicensePlanTheme(licenseType) {
  const normalized = String(licenseType ?? '')
    .trim()
    .toLowerCase()
    .replace(/[\s_]+/g, '-')

  if (!normalized) return null
  if (normalized === 'trial') return 'trial'
  if (normalized === 'free') return 'free'
  if (normalized === 'enterprise') return 'enterprise'
  if (normalized === 'enterprise-pro' || normalized === 'enterprisepro') return 'enterprise-pro'
  return null
}

/** Maps a license type to a /plans card id (trial has no plan card). */
export function licenseTypeToPlanId(licenseType) {
  const theme = resolveLicensePlanTheme(licenseType)
  if (!theme || theme === 'trial') return null
  return theme
}
