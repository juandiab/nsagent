import { isNetScalerVendor, resolveApplianceProduct } from './applianceVendors'

/** Non–NetScaler ADC devices, or NetScaler lines flagged beta in inventory. */
export function isJpilotBetaAppliance(appliance) {
  if (!appliance) return false
  const product = resolveApplianceProduct(appliance)
  if (product?.beta) return true
  return Boolean(appliance.copilotEligible && !isNetScalerVendor(appliance.vendor))
}

export function appliancesForJpilotRole(appliances, roleId) {
  const enabled = (appliances || []).filter((item) => item.enabled)
  if (roleId === 'architect') {
    return [...enabled].sort(compareApplianceOptions)
  }
  return enabled.filter((item) => isNetScalerVendor(item.vendor)).sort((a, b) => a.name.localeCompare(b.name))
}

function compareApplianceOptions(a, b) {
  const aNet = isNetScalerVendor(a.vendor) ? 0 : 1
  const bNet = isNetScalerVendor(b.vendor) ? 0 : 1
  if (aNet !== bNet) return aNet - bNet
  return a.name.localeCompare(b.name)
}

export function isApplianceDisabledForRole(appliance, roleId) {
  if (!appliance?.enabled) return true
  if (roleId === 'architect') return false
  return !isNetScalerVendor(appliance.vendor)
}
