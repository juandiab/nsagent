# JPilot change control record outline (reference)

Use this structure when `planning_intent` is **change_control** and discovery is complete (or the user asks to generate). Vendor-neutral ITIL / ServiceNow CAB style. Mark unknowns **TBD**.

## Front matter
- **Change record** — title, change ID (TBD if not assigned), requestor, change owner, created date
- **Classification** — standard / normal / emergency / expedited
- **State** — draft / scheduled / approved / implemented (default **draft** unless user specified)

## Change details
- **Summary** — one paragraph
- **Description** — detailed scope of work
- **Business justification** — why the change is needed
- **Category & type** — e.g. network, application delivery, security, maintenance (TBD if unknown)

## Impact & risk
- **Affected CIs / systems** — table: name, role, site, impact level
- **Services & users affected** — description and estimated user count (TBD if unknown)
- **Risk assessment** — risk level (low/medium/high), outage expected (yes/no), maximum outage duration
- **Risk mitigation** — controls during implementation

## Schedule
- **Planned maintenance window** — date, start time, end time, timezone
- **Blackout / freeze constraints** — TBD if none
- **Emergency/expedited rationale** — required when classification is emergency or expedited

## Pre-change checklist
| Item | Owner | Status | Notes |
|------|-------|--------|-------|
| Change approved (CAB / manager) | | TBD | |
| Stakeholder notification sent | | TBD | |
| Configuration backup / export | | TBD | |
| Support diagnostic bundle | | TBD | |
| Rollback validated / tested | | TBD | |
| Implementation runbook reviewed | | TBD | |

## Implementation plan
Numbered steps with owner and estimated duration per step. Include maintenance-mode or failover sequencing if applicable.

## Rollback plan
- **Rollback trigger** — conditions that initiate rollback
- **Rollback steps** — numbered, with max time to restore service
- **Rollback validation** — how to confirm rollback success

## Post-change validation
- **Success criteria** — measurable checks
- **Validation steps** — numbered tests (functional, monitoring, logs)
- **Monitoring period** — duration and owner
- **Post-implementation review** — date/owner (TBD)

## Communications
- **Notification audience** — teams, customers, NOC
- **Comms timeline** — before / during / after window
- **Status update method** — email, ticket, bridge (TBD)

## Approvals & stakeholders
| Role | Name | Approval (yes/no/TBD) | Date |
|------|------|------------------------|------|
| Change owner | | | |
| Implementer | | | |
| Approver / CAB | | | |
| Observer | | | |

## Vendor pre-change checklist — NetScaler ADC
Include this appendix when the change touches Citrix NetScaler ADC:
- Verify HA pair state and sync (`show ha node`, `show sync status`)
- Export or backup config (`show config`, `/flash/nsconfig`, ADM backup if used)
- Generate tech support if troubleshooting baseline needed
- Confirm `save config` / `save ns config` plan after change
- Document failover / secondary path during maintenance
- Validate license and capacity headroom if adding features

## Vendor pre-change checklist — F5 BIG-IP
Include when the change touches F5 BIG-IP:
- Verify config-sync / device trust status
- Save running config; UCS backup before change
- Confirm HA failover readiness and traffic-group ownership
- QKView baseline if support engagement likely
- Maintenance mode / force-offline sequencing documented

## Vendor pre-change checklist — Cisco IOS/XE
Include when the change touches Cisco switches:
- `show running-config` archive or export
- Verify boot variable, disk space, and target IOS image
- `copy running-config startup-config` plan
- Console/OOB access confirmed for rollback
- Reload order documented for stacked or redundant paths

## Optional — Handoff for Operator
Include **only** when the user confirmed on-appliance execution: goal, connected appliance/inventory name, numbered implementation commands or tasks, verification, rollback reference.
