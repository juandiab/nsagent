import { getLicense } from './system'

let cachedLicense = null
let inflight = null

export function invalidateLicenseGateCache() {
  cachedLicense = null
  inflight = null
}

export async function getLicenseForGate({ force = false } = {}) {
  if (!force && cachedLicense) return cachedLicense
  if (!force && inflight) return inflight

  inflight = getLicense()
    .then((license) => {
      cachedLicense = license
      return license
    })
    .finally(() => {
      inflight = null
    })

  return inflight
}

/** True when the user must activate or renew before using the app. */
export function licenseActivationRequired(license) {
  if (!license?.hasLicenseCode) return true
  return ['expired', 'deactivated', 'missing'].includes(license.status)
}

export function isLicenseActivationRoute(to) {
  return to.path === '/settings' && to.query.section === 'license'
}
