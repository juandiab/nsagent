export const NETSCALER_VENDOR = 'netscaler'

/** Product lines shown in Appliances → Vendor support */
export const VENDOR_SUPPORT = [
  {
    id: 'netscaler-mpx-vpx',
    label: 'NetScaler MPX / VPX',
    description: 'Full JPilot chat, Next-Gen API, SSH CLI, diagnostics, and SSL tools.',
    status: 'supported'
  },
  {
    id: 'netscaler-sdx',
    label: 'NetScaler SDX',
    description: 'Multi-tenant platform support is planned for a future release.',
    status: 'coming_soon'
  }
]

export const OTHER_APPLIANCE_VENDORS = [
  {
    value: 'f5',
    label: 'F5 BIG-IP',
    description: 'iControl REST API and TMSH over SSH',
    access: ['SSH CLI', 'REST API']
  },
  {
    value: 'cisco',
    label: 'Cisco',
    description: 'ASA, FTD, IOS, and ACI platforms',
    access: ['SSH CLI', 'REST API']
  },
  {
    value: 'juniper',
    label: 'Juniper',
    description: 'Junos devices and SRX series',
    access: ['SSH CLI', 'REST API']
  },
  {
    value: 'palo_alto',
    label: 'Palo Alto Networks',
    description: 'PAN-OS firewalls and Panorama',
    access: ['SSH CLI', 'REST API']
  },
  {
    value: 'fortinet',
    label: 'Fortinet',
    description: 'FortiGate and FortiADC appliances',
    access: ['SSH CLI', 'REST API']
  },
  {
    value: 'checkpoint',
    label: 'Check Point',
    description: 'Security gateways and management',
    access: ['SSH CLI', 'REST API']
  },
  {
    value: 'a10',
    label: 'A10 Networks',
    description: 'Thunder ADC load balancers',
    access: ['SSH CLI', 'REST API']
  },
  {
    value: 'radware',
    label: 'Radware',
    description: 'Alteon and AppWall ADC platforms',
    access: ['SSH CLI', 'REST API']
  },
  {
    value: 'haproxy',
    label: 'HAProxy / Kemp',
    description: 'Software and hardware load balancers',
    access: ['SSH CLI', 'REST API']
  },
  {
    value: 'other',
    label: 'Other',
    description: 'Any vendor with SSH CLI and/or REST API access',
    access: ['SSH CLI', 'REST API']
  }
]

export function vendorLabel(value) {
  return OTHER_APPLIANCE_VENDORS.find((item) => item.value === value)?.label || value || 'Unknown'
}

export function isNetScalerVendor(vendor) {
  return !vendor || vendor === NETSCALER_VENDOR
}
