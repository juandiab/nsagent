# Cisco IOS/XE switch — JPilot memory (SSH CLI reference)

Use this file with `search_cisco_cli_reference` before running write commands on a Cisco switch.

## 1. Platform overview

- **Access**: SSH (port 22). User EXEC mode (`>`) and privileged EXEC (`#`) after `enable`.
- **Configuration**: Global configuration from `configure terminal` (abbrev. `conf t`). Exit with `end` or `Ctrl+Z`.
- **Persistence**: `copy running-config startup-config` or `write memory` saves the running config.
- **Show vs display**: IOS uses `show` for operational state; some platforms accept `display` — prefer `show` on classic IOS/XE.

## 2. Read-only discovery (Operator/Analyst)

Common read commands (always safe to run first):

```
show version
show running-config
show startup-config
show ip interface brief
show interfaces status
show vlan brief
show mac address-table
show cdp neighbors
show lldp neighbors
show spanning-tree summary
show ip route
show logging
show clock
```

Diagnostics:

```
ping <ip>
traceroute <ip>
```

## 3. Basic L2 configuration patterns

**Access VLAN on access port**

```
configure terminal
interface GigabitEthernet1/0/1
 description Workstation
 switchport mode access
 switchport access vlan 10
 no shutdown
end
copy running-config startup-config
```

**Trunk port**

```
interface GigabitEthernet1/0/48
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk allowed vlan 10,20,30
 no shutdown
```

## 4. Basic L3 / SVI

```
ip routing
interface Vlan10
 ip address 10.10.10.1 255.255.255.0
 no shutdown
```

## 5. Behavioral rules for JPilot

1. Call `search_cisco_cli_reference` before any `cisco_run_cli_command` or `cisco_run_cli_commands`.
2. Use `cisco_ssh_run_command` for read-only `show` / `ping` / `traceroute` only.
3. Never invent interface names — use `show ip interface brief` or `show interfaces status` first when unsure.
4. After configuration changes, include `copy running-config startup-config` in the command batch unless the user asked for a temporary test.
5. Destructive commands (`reload`, `erase`, `delete`, `write erase`) require explicit user confirmation before execution.
6. Do not drop to shell (`bash`, `guestshell`, `tclsh`) via SSH tools.

## 6. Command quick reference

| Task | Example command |
|------|-----------------|
| Identity / firmware | `show version` |
| Interface summary | `show ip interface brief` |
| Switchport status | `show interfaces status` |
| VLANs | `show vlan brief` |
| MAC table | `show mac address-table` |
| Routing table | `show ip route` |
| Save config | `copy running-config startup-config` |
