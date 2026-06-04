/** JPilot chat roles — keep ids in sync with backend ChatRole / copilot_roles.py */

export const JPILOT_ROLES = [
  {
    id: 'architect',
    label: 'Architect',
    description: 'Plan deployments and designs without a connected appliance.',
    requiresAppliance: false,
    suggestedPaneLabel: 'Plan',
    handoffTarget: 'operator',
    icon: 'pi pi-compass'
  },
  {
    id: 'operator',
    label: 'Operator',
    description: 'Build and change configuration on a connected NetScaler.',
    requiresAppliance: true,
    suggestedPaneLabel: 'Operate',
    handoffTarget: null,
    icon: 'pi pi-cog'
  },
  {
    id: 'analyst',
    label: 'Analyst',
    description: 'Troubleshoot incidents with read-first checks on a connected appliance.',
    requiresAppliance: true,
    suggestedPaneLabel: 'Analyze',
    handoffTarget: 'operator',
    icon: 'pi pi-search'
  }
]

export const DEFAULT_JPILOT_ROLE = 'operator'

/** @deprecated Renamed to analyst; kept for persisted sessions. */
const LEGACY_ROLE_ALIASES = { investigator: 'analyst' }

export function normalizeRoleId(roleId) {
  if (!roleId) return DEFAULT_JPILOT_ROLE
  return LEGACY_ROLE_ALIASES[roleId] || roleId
}

export function getRoleById(roleId) {
  const id = normalizeRoleId(roleId)
  return JPILOT_ROLES.find((r) => r.id === id) || JPILOT_ROLES.find((r) => r.id === DEFAULT_JPILOT_ROLE)
}

export function roleRequiresAppliance(roleId) {
  return getRoleById(roleId)?.requiresAppliance !== false
}
