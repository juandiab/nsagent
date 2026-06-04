# NetScaler SDX CLI / NITRO Command Reference for JPilot

## Scope

NetScaler SDX Management Service (SVM) only.

Excludes ADC/VPX configuration (LB, CS, WAF, AAA, Gateway, GSLB, etc.)

## Access Methods

| Method | Description |
|----------|-------------|
| SSH | Connect to SDX Management Service CLI |
| SSH + Shell | Enter underlying Linux shell on SVM |
| NITRO API | REST API exposed by SDX Management Service (not used by JPilot v1) |
| Hypervisor Shell | XenServer / Citrix Hypervisor layer (out of scope) |

## Safety Levels

| Level | Meaning |
|---------|---------|
| SAFE | Read-only |
| CAUTION | Changes configuration |
| DESTRUCTIVE | Can impact VPX instances or platform |
| CRITICAL | Can cause outage |

## SSH CLI Commands

### Platform Information

| Command | Purpose | Risk |
|-----------|---------|------|
| show system | Display SDX system information | SAFE |
| show version | Display firmware version | SAFE |
| show hostname | Display hostname | SAFE |
| show interface | Display interfaces | SAFE |
| show hardware | Display hardware inventory | SAFE |
| show disk | Disk utilization | SAFE |
| show memory | Memory usage | SAFE |
| show cpu | CPU utilization | SAFE |

### VPX Inventory and Lifecycle

| Command | Purpose | Risk |
|-----------|---------|------|
| show virtualserver | List VPX instances | SAFE |
| start virtualserver \<name\> | Start VPX | CAUTION |
| shutdown virtualserver \<name\> | Graceful shutdown | DESTRUCTIVE |
| restart virtualserver \<name\> | Reboot VPX | DESTRUCTIVE |
| force-stop virtualserver \<name\> | Hard power off | CRITICAL |
| delete virtualserver \<name\> | Delete VPX | CRITICAL |

### Network Operations

| Command | Purpose | Risk |
|-----------|---------|------|
| show vlan | Display VLAN assignments | SAFE |
| show channel | Display LACP channels | SAFE |
| add vlan | Create VLAN | CAUTION |
| delete vlan | Remove VLAN | DESTRUCTIVE |

### Firmware Management

| Command | Purpose | Risk |
|-----------|---------|------|
| show firmware | List firmware packages | SAFE |
| install firmware | Install firmware | DESTRUCTIVE |
| upgrade virtualserver | Upgrade VPX image | DESTRUCTIVE |

## SSH Shell Commands

Read-only shell checks (require entering SVM shell — use with care):

| Command | Purpose | Risk |
|-----------|---------|------|
| df -h | Disk utilization | SAFE |
| free -m | Memory | SAFE |
| top | CPU processes | SAFE |
| uptime | System load | SAFE |
| service svm restart | Restart SVM service | CRITICAL |
| reboot | Reboot SVM | CRITICAL |

## Confirmation Required (Operator)

Before executing, obtain explicit user confirmation:

- force-stop virtualserver
- delete virtualserver
- shutdown virtualserver / restart virtualserver
- delete vlan
- install firmware / upgrade virtualserver
- service svm restart / reboot

## Official References

1. https://docs.netscaler.com/en-us/sdx/current-release/
2. https://docs.netscaler.com/en-us/sdx/current-release/provision-netscaler-instances.html
3. https://docs.netscaler.com/en-us/sdx/current-release/configuring-management-service.html
4. https://support.citrix.com/external/article/CTX219781
