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
    id: 'investigator',
    label: 'Investigator',
    description: 'Troubleshoot incidents with read-first checks on a connected appliance.',
    requiresAppliance: true,
    suggestedPaneLabel: 'Investigate',
    handoffTarget: 'operator',
    icon: 'pi pi-search'
  }
]

export const DEFAULT_JPILOT_ROLE = 'operator'

export function getRoleById(roleId) {
  return JPILOT_ROLES.find((r) => r.id === roleId) || JPILOT_ROLES.find((r) => r.id === DEFAULT_JPILOT_ROLE)
}

export function roleRequiresAppliance(roleId) {
  return getRoleById(roleId)?.requiresAppliance !== false
}
