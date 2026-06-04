# F5 BIG-IP — JPilot memory (TMSH / SSH reference)

Use this file with `search_f5_tmsh_reference` before running write commands on a BIG-IP.

## 1. Platform overview

- **Access**: SSH to the management IP (port 22). Prefer **TMSH** (`tmsh`) for configuration; avoid dropping to bash.
- **Modes**: Read-only discovery uses `tmsh show` and `tmsh list`. Changes use `tmsh create`, `tmsh modify`, then `tmsh save sys config`.
- **Official docs**: [F5 Cloud Docs](https://clouddocs.f5.com/), [F5 TechDocs](https://techdocs.f5.com/), [DevCentral](https://devcentral.f5.com/).

## 2. Read-only discovery (Operator/Analyst)

```
tmsh show sys version
tmsh show sys hardware
tmsh show sys provision
tmsh list sys management-ip
tmsh show sys performance system
tmsh show sys connection
tmsh show ltm virtual
tmsh list ltm virtual
tmsh show ltm pool
tmsh list ltm pool
tmsh show ltm node
tmsh list ltm node
tmsh show ltm profile
tmsh show net self
tmsh show net vlan
tmsh show net route
tmsh show cm device
tmsh show cm sync-status
```

Diagnostics:

```
ping <ip>
traceroute <ip>
```

## 3. Basic troubleshooting

```
tmsh show sys log ltm
tmsh show ltm virtual <name> detail
tmsh show ltm pool <name> members
tmsh show ltm pool <name> detail
tmsh show sys connection ss-server-addr <ip>
tmsh show sys connection ss-clientside-server-port <port>
```

## 4. Basic load balancing (HTTP example)

**Pool and members**

```
tmsh create ltm pool web_pool members add { 10.0.0.10:80 10.0.0.11:80 } monitor tcp
tmsh modify ltm pool web_pool monitor http
```

**Virtual server**

```
tmsh create ltm virtual web_vs destination 10.0.1.50:80 pool web_pool profiles add { http }
tmsh modify ltm virtual web_vs profiles add { http }
```

**Persist and save**

```
tmsh save sys config
```

## 5. Behavioral rules for JPilot

1. Call `search_f5_tmsh_reference` before any `f5_run_tmsh_command` or `f5_run_tmsh_commands`.
2. Use `f5_ssh_run_command` for read-only `tmsh show` / `tmsh list` / `ping` / `traceroute` only.
3. Discover object names with `tmsh list ltm virtual` / `tmsh list ltm pool` before modifying.
4. After configuration changes, include `tmsh save sys config` unless the user asked for a temporary test.
5. Destructive operations (`delete`, `restart`, `reboot`, `load sys config`) require explicit user confirmation.
6. Do not run bash/shell escape commands via SSH tools.

## 6. Command quick reference

| Task | Example command |
|------|-----------------|
| Version / platform | `tmsh show sys version` |
| Virtual servers | `tmsh list ltm virtual` |
| Pools | `tmsh list ltm pool` |
| Pool members | `tmsh show ltm pool <name> members` |
| Self IPs / VLANs | `tmsh show net self` |
| Save config | `tmsh save sys config` |
