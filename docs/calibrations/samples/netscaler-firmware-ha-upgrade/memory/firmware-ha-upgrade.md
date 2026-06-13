# NetScaler ADC — firmware HA upgrade checklist

Use when documenting or implementing firmware upgrades on HA pairs.

## Pre-change (both nodes)

- Verify HA state: `show ha node`, `show sync status` — nodes UP, sync enabled
- Backup config: `show config` export, `/flash/nsconfig`, ADM backup if used
- Confirm license and capacity headroom for target build
- Tech support baseline if needed: `show techsupport`
- Notify stakeholders; confirm maintenance window and rollback approver

## Phased implementation (per HA pair)

Recommended sequence when upgrading active/standby:

1. Confirm traffic on primary; secondary synced
2. Fail over to secondary (or use `Turn OFF HA sync` per runbook) — document which node is passive target
3. Upgrade **secondary (formerly passive)** first: upload image, install, reboot
4. Validate secondary at new build; re-enable sync
5. Fail over; upgrade former primary
6. Final failover test; `save config` / `save ns config` on both nodes
7. Stagger between HA pairs if multiple pairs (sequential unless user specifies parallel)

## Rollback triggers

- Node fails to join HA after reboot
- Sync fails persistently
- Critical VIP or service down > agreed outage window
- Authentication or cert breakage on management or data plane

## Rollback steps

- Boot previous firmware partition if dual-partition supported
- Restore config from pre-change backup
- Max time to restore: document per org (default **TBD**)

## Post-change validation

- `show version` on both nodes — target build
- HA state synced; all VIPs responding
- Sample application / monitor checks
- Monitor logs and CPU for agreed period (default 24h **TBD**)

## Communications

- Before: maintenance notification (Slack/email/ticket)
- During: status updates at failover boundaries
- After: completion + validation summary
