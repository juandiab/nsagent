export const NETSCALER_VENDOR = 'netscaler'

/** Top-level vendor families in the Add appliance flow */
export const VENDOR_GROUPS = [
  { id: 'citrix', label: 'Citrix' },
  { id: 'cisco', label: 'Cisco' },
  { id: 'f5', label: 'F5' },
  { id: 'juniper', label: 'Juniper' },
  { id: 'palo_alto', label: 'Palo Alto Networks' },
  { id: 'fortinet', label: 'Fortinet' },
  { id: 'checkpoint', label: 'Check Point' },
  { id: 'a10', label: 'A10 Networks' },
  { id: 'radware', label: 'Radware' },
  { id: 'haproxy', label: 'HAProxy / Kemp' },
  { id: 'other', label: 'Other' }
]

/**
 * Product lines within each vendor group.
 * `value` is the backend appliance vendor id when supported.
 */
export const APPLIANCE_PRODUCTS = [
  {
    id: 'netscaler-mpx',
    vendorGroupId: 'citrix',
    value: NETSCALER_VENDOR,
    label: 'NetScaler MPX',
    description:
      'Physical ADC — full JPilot chat, Next-Gen API, SSH CLI, Citrix Gateway, diagnostics, and SSL tools.',
    status: 'supported',
    hostHint: 'HTTPS on port 443 (Next-Gen API).',
    supportsInspect: true,
    supportsConnectionTest: true
  },
  {
    id: 'netscaler-vpx',
    vendorGroupId: 'citrix',
    value: NETSCALER_VENDOR,
    label: 'NetScaler VPX',
    description:
      'Virtual ADC — full JPilot chat, Next-Gen API, SSH CLI, Citrix Gateway, diagnostics, and SSL tools.',
    status: 'supported',
    hostHint: 'HTTPS on port 443 (Next-Gen API).',
    supportsInspect: true,
    supportsConnectionTest: true
  },
  {
    id: 'netscaler-sdx',
    vendorGroupId: 'citrix',
    value: 'sdx',
    label: 'NetScaler SDX',
    description: 'JPilot Operator/Analyst over SSH for SVM platform and VPX lifecycle.',
    status: 'supported',
    hostHint: 'SSH to the SDX Management Service (SVM).',
    supportsInspect: false,
    supportsConnectionTest: false
  },
  {
    id: 'cisco-switches',
    vendorGroupId: 'cisco',
    value: 'cisco',
    label: 'Cisco IOS/XE Switches',
    description: 'JPilot Operator/Analyst over SSH (show/configure).',
    status: 'supported',
    hostHint: 'SSH on port 22.',
    supportsInspect: false,
    supportsConnectionTest: false
  },
  {
    id: 'cisco-asa',
    vendorGroupId: 'cisco',
    value: null,
    label: 'Cisco ASA',
    description: 'Adaptive Security Appliance firewalls.',
    status: 'coming_soon'
  },
  {
    id: 'cisco-ftd',
    vendorGroupId: 'cisco',
    value: null,
    label: 'Cisco FTD',
    description: 'Firepower Threat Defense platforms.',
    status: 'coming_soon'
  },
  {
    id: 'cisco-aci',
    vendorGroupId: 'cisco',
    value: null,
    label: 'Cisco ACI',
    description: 'Application Centric Infrastructure.',
    status: 'coming_soon'
  },
  {
    id: 'f5-bigip',
    vendorGroupId: 'f5',
    value: 'f5',
    label: 'F5 BIG-IP',
    description: 'iControl REST API and TMSH over SSH.',
    status: 'coming_soon',
    hostHint: 'Management IP for HTTPS API and/or SSH.'
  },
  {
    id: 'juniper-junos',
    vendorGroupId: 'juniper',
    value: 'juniper',
    label: 'Junos (SRX / EX / QFX)',
    description: 'Junos devices and SRX series.',
    status: 'coming_soon'
  },
  {
    id: 'palo-panos',
    vendorGroupId: 'palo_alto',
    value: 'palo_alto',
    label: 'PAN-OS / Panorama',
    description: 'Palo Alto Networks firewalls and Panorama.',
    status: 'coming_soon'
  },
  {
    id: 'fortinet-fortigate',
    vendorGroupId: 'fortinet',
    value: 'fortinet',
    label: 'FortiGate / FortiADC',
    description: 'Fortinet security and ADC platforms.',
    status: 'coming_soon'
  },
  {
    id: 'checkpoint-gw',
    vendorGroupId: 'checkpoint',
    value: 'checkpoint',
    label: 'Check Point Gateway',
    description: 'Security gateways and management.',
    status: 'coming_soon'
  },
  {
    id: 'a10-thunder',
    vendorGroupId: 'a10',
    value: 'a10',
    label: 'A10 Thunder ADC',
    description: 'Thunder ADC load balancers.',
    status: 'coming_soon'
  },
  {
    id: 'radware-alteon',
    vendorGroupId: 'radware',
    value: 'radware',
    label: 'Radware Alteon / AppWall',
    description: 'Alteon and AppWall ADC platforms.',
    status: 'coming_soon'
  },
  {
    id: 'haproxy-kemp',
    vendorGroupId: 'haproxy',
    value: 'haproxy',
    label: 'HAProxy / Kemp',
    description: 'Software and hardware load balancers.',
    status: 'coming_soon'
  },
  {
    id: 'other-generic',
    vendorGroupId: 'other',
    value: 'other',
    label: 'Other platform',
    description: 'Any vendor with SSH CLI and/or REST API access.',
    status: 'coming_soon'
  }
]

/** Flat list for Vendor support panel under inventory */
export const VENDOR_SUPPORT = APPLIANCE_PRODUCTS.map((product) => ({
  id: product.id,
  label: product.label,
  description: product.description,
  status: product.status === 'supported' ? 'supported' : 'coming_soon',
  vendorGroupLabel: VENDOR_GROUPS.find((g) => g.id === product.vendorGroupId)?.label || product.vendorGroupId
}))

/** @deprecated Use APPLIANCE_PRODUCTS — kept for any legacy imports */
export const OTHER_APPLIANCE_VENDORS = APPLIANCE_PRODUCTS.filter((p) => p.value)
  .map((p) => ({
    value: p.value,
    label: p.label,
    description: p.description,
    access: p.status === 'supported' ? ['JPilot'] : []
  }))

export const COPILOT_SUPPORTED_VENDORS = ['netscaler', 'cisco', 'sdx']

export function getVendorGroupLabel(groupId) {
  return VENDOR_GROUPS.find((g) => g.id === groupId)?.label || groupId
}

export function getProductsForVendorGroup(groupId) {
  return APPLIANCE_PRODUCTS.filter((p) => p.vendorGroupId === groupId)
}

export function getProductById(productId) {
  return APPLIANCE_PRODUCTS.find((p) => p.id === productId) || null
}

export function getProductByVendorValue(vendorValue) {
  if (!vendorValue || vendorValue === NETSCALER_VENDOR) {
    return null
  }
  return APPLIANCE_PRODUCTS.find((p) => p.value === vendorValue) || null
}

export function resolveApplianceProduct(appliance) {
  if (appliance?.productId) {
    return getProductById(appliance.productId)
  }
  const byVendor = getProductByVendorValue(appliance?.vendor)
  if (byVendor) return byVendor
  if (!appliance?.vendor || appliance.vendor === NETSCALER_VENDOR) {
    return {
      id: 'netscaler-adc',
      label: 'NetScaler ADC',
      value: NETSCALER_VENDOR,
      supportsInspect: true,
      supportsConnectionTest: true
    }
  }
  return null
}

export function isProductSupported(product) {
  return Boolean(product && product.status === 'supported' && product.value)
}

export function vendorLabel(value, productId = null) {
  if (productId) {
    const byId = getProductById(productId)
    if (byId) return byId.label
  }
  const product = resolveApplianceProduct({ vendor: value, productId })
  if (product?.label) return product.label
  return value || 'Unknown'
}

export function isNetScalerVendor(vendor) {
  return !vendor || vendor === NETSCALER_VENDOR
}

export function isCopilotEligibleVendor(vendor) {
  return COPILOT_SUPPORTED_VENDORS.includes(vendor || NETSCALER_VENDOR)
}

export function productSelectOptions(groupId) {
  return getProductsForVendorGroup(groupId).map((product) => ({
    id: product.id,
    label: product.label,
    description: product.description,
    status: product.status,
    disabled: !isProductSupported(product),
    statusLabel: product.status === 'supported' ? 'Available' : 'Coming soon'
  }))
}
