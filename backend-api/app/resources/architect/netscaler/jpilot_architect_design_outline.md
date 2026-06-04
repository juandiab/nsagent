# JPilot design deliverable outline (reference)

Use this structure when the user asks for a design document or discovery is complete. Use markdown tables for configuration settings. Mark unknowns as **TBD**.

## Front matter
- **Executive summary** — customer/context, engagement scope, Citrix areas covered (System, Networking, Security, Application delivery, Operations)
- **Project goals** — numbered goals and how this design addresses each
- **Design risks and recommendations** — risks/unknowns; short-term (2–4 weeks) and long-term (3+ months) actions

## Design narrative
- **Document purpose** — audience (architecture, engineering, operations)
- **Deliverable overview** — how requirements were gathered
- **Conceptual architecture** — sites, HA pairs, traffic flow (describe diagram if no image); call out **on-premises**, **AWS**, or **hybrid** placement
- **Overall design decisions** — platform, firmware target, topology mode (one-arm/two-arm), auth (LDAP/local/RADIUS), enabled features (LB, WAF, GSLB, IP reputation, etc.)

## Domain sections (include tables where applicable)
- **Platform design** — hardware/VPX/MPX, edition, capacity, firmware/build; for cloud, note hosting (AWS EC2, Azure, etc.)
- **AWS deployment (when VPX/ADC runs in AWS)** — include this section whenever the design uses Citrix ADC **VPX on EC2**, AWS-only sites, or hybrid with AWS VPCs:
  - **AWS scope table** — account(s), region(s), VPC IDs, Availability Zones, tenancy (shared/dedicated)
  - **EC2 & licensing** — instance type/family, vCPU/RAM vs ADC throughput targets, licensing model (AWS Marketplace hourly, BYOL, ADM pool), firmware/build
  - **Network in AWS** — subnet layout (management, client, server/SNIP, optional dedicated VIP subnet); **ENI mapping table** (ENI name/role, subnet, security group, source/dest check, private IP, optional Elastic IP); one-arm vs two-arm in VPC; NAT gateway vs public subnet for management
  - **Security** — security group rules (inbound/outbound) per tier; NACL notes; IAM instance profile / SSM if used; least-privilege for `cloud` credential integration
  - **ADC cloud integration** — `cloud parameter` / AWS credential profile if autoscale or AWS API integration is in scope; autoscale group design (scale-up/down triggers, min/max nodes) or **TBD**
  - **HA in AWS** — HA pair spread across AZs; secondary ENI / floating IP / EIP failover pattern; anti-affinity placement; sync and heartbeat subnet reachability
  - **Routing & DNS** — VPC route tables (0.0.0.0/0, on-prem via TGW/VPN/DX); internal ALB/NLB in front of or behind ADC if applicable; **Route 53** (or external DNS) for public names and GSLB delegation
  - **Hybrid connectivity** — Site-to-site VPN, Direct Connect, or Transit Gateway to on-prem; SNIP reachability to VDA/StoreFront subnets; latency and MTU assumptions
  - **Operations in AWS** — CloudWatch/syslog targets, backup (`/flash/nsconfig`, AMIs/snapshots if used), patching/maintenance windows, ADM agent reachability
- **Network design** — topology, interfaces, channels, **VLAN table**, **IP address table** (NSIP, SNIP, VIP, management), PBR for management isolation (on-prem VLANs; in AWS use subnets/ENIs instead of VLANs where applicable)
- **High availability** — mode (active/passive), peers, heartbeat/monitoring interfaces
- **Modes and features** — global modes enabled/disabled with rationale
- **TCP / HTTP parameters** — global tuning (table or bullet list)
- **HTTP profiles** — named profiles if app-specific
- **NetScaler Gateway — authentication & authorization** (when Gateway or AAA is in scope) — include subsections only for selected topics:
  - **Global auth model** — default global authentication types; auth without authorization; authorization policies; disabling authentication; authentication for specific times; how authentication policies work (priority/bind order)
  - **Users & groups** — local users; groups; AD group restriction on Gateway access
  - **Authentication methods** — LDAP, RADIUS, SAML, TACACS+, client certificate; RADIUS + LDAP with mobile devices
  - **Advanced** — multifactor authentication; single sign-on; one-time password; **nFactor** login schemas for Gateway; **Unified Gateway Visualizer** narrative (policy flow)
  - **Posture & access** — device posture checks on NetScaler Gateway; EPA integration with auth policies
  - **Tables** — authentication servers/profiles, policies (auth + session), bindings to Gateway vserver, prerequisites and certificates
- **NetScaler Gateway — Citrix product integration** (when Gateway or CEM is in scope) — include subsections only for selected integrations:
  - User access — how users reach apps, desktops, and ShareFile (client, URL, SSO)
  - **StoreFront** — FQDN, STA, beacons, authentication bridge, session policies
  - **Citrix Virtual Apps and Desktops** — Controllers, XML/ICA, HDX, resource access
  - **Citrix Endpoint Management** — CEM settings, LB to CEM, certificates, mobile paths
  - **Combined deploy** — Gateway + CEM + Virtual Apps and Desktops (single design narrative)
  - **SmartControl** — policies and prerequisites
  - **Microsoft Intune / Endpoint Manager** — integrated Intune MDM vs alternatives; micro VPN; NAC device check on Gateway vserver (single-factor)
  - **Azure AD** — Gateway app in Azure portal; MSAL token authentication; Azure AD Graph extended support notes
  - **Microsoft Exchange** — LB servers with email security filtering (if in scope)
  - **Policy tables** — Gateway vserver, session, authentication, EPA, and bind order
- **Azure deployment & ADC autoscale** (when VPX/autoscale runs in Azure) — mirror AWS-style tables where applicable; **autoscale profile**, cloud credentials, scale policies, min/max nodes; cite Citrix Tech Zone NetScaler ADC Azure autoscale guide in **Supplemental links**
- **Load balancing** — vserver/service group patterns; reference migration row per app where relevant
- **SSL / TLS** — profiles, cipher groups, Qualys-grade targets if required
- **Web App Firewall** — profile, security checks, learning, policies, signatures (if in scope)
- **GSLB** — sites, domains, persistence (if in scope)
- **Monitoring** — syslog, ADM/cloud agent, metrics retention
- **Citrix ADM** — deployment model, agents, licensing, backup
- **Backup and restore** — methods (`/flash/nsconfig`, ADM, etc.)

## Closing
- **Sizing summary** — capacity assumptions and scale notes
- **Supplemental links** — official doc pointers only
- **Handoff for Operator** — goal, constraints, numbered implementation steps, verification, target appliance/inventory name
