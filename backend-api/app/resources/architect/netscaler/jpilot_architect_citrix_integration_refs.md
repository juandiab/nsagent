# Citrix Gateway, authentication, Endpoint Management, Azure — official reference index

JPilot Architect uses this index for discovery options, design sections, and **Supplemental links**. Prefer these URLs in deliverables; search tools may fetch current-release pages under the same paths.

## Hub — Integrate NetScaler Gateway with Citrix products

- **Integrate NetScaler Gateway with Citrix products (hub)**  
  https://docs.netscaler.com/en-us/netscaler-gateway/current-release/integrate-citrix-gateway-with-citrix-products

### Core integrations (Gateway + Citrix stack)

| Topic | Use in design when |
|-------|-------------------|
| How users connect to applications, desktops, and ShareFile | User access patterns, client types, SSO, and published resource paths |
| Integrate NetScaler Gateway with StoreFront | StoreFront FQDN, STA, beacon, authentication bridge, session policies |
| Integrate NetScaler Gateway with Citrix Virtual Apps and Desktops | CVAD/DaaS delivery groups, XML/ICA, Controller connectivity, HDX |
| Deploy NetScaler Gateway with Citrix Endpoint Management, Citrix Virtual Apps, and Citrix Virtual Desktops | Combined CEM + CVAD + Gateway rollout, shared auth and routing |
| Configure settings for your Citrix Endpoint Management Environment | CEM server integration, load balancing, certificates, mobile paths |

### Endpoint Management, mobility, and Microsoft

| Topic | Use in design when |
|-------|-------------------|
| Configure SmartControl | SmartControl policies for managed mobile/desktop access via Gateway |
| Microsoft Intune Integration | Intune as MDM/MAM partner for Gateway |
| When to Use the Integrated Intune MDM Solution | Architecture choice: integrated Intune MDM vs alternatives |
| Understanding the NetScaler Gateway Intune MDM Integration | Deep-dive design for Intune MDM enrollment and Gateway binding |
| Configuring Network Access Control device check for NetScaler Gateway virtual server for single factor authentication deployment | Pre-auth device posture / NAC checks on Gateway vserver |
| Configuring a NetScaler Gateway application on the Azure portal | Azure AD enterprise app / SSO from Azure portal to Gateway |
| Understanding MSAL Token Authentication | OAuth/OIDC MSAL flow requirements |
| Configuring NetScaler Gateway Virtual Server for MSAL Token Authentication | Azure AD MSAL on Gateway vserver (policies, claims, session) |
| Set up NetScaler Gateway for using micro VPN with Microsoft Endpoint Manager | Micro VPN tunnel for Endpoint Manager–managed devices |
| Extended support for Azure AD Graph | Legacy Graph dependencies; note Azure AD Graph retirement and supported alternatives |

### Application delivery (non-Citrix app patterns on ADC)

| Topic | Use in design when |
|-------|-------------------|
| Configure load balancing servers for Microsoft Exchange with email security filtering | Exchange published via Gateway/ADC with email security filter policies |

- **Exchange LB + email security filtering**  
  https://docs.netscaler.com/en-us/netscaler-gateway/current-release/integrate-citrix-gateway-with-citrix-products/configure-citrix-endpoint-management-settings-to-integrate-with-citrix-gateway/configure-load-balancing-servers-for-microsoft-exchange-with-email-security-filtering.html

## Hub — NetScaler Gateway authentication & authorization

- **Authentication and authorization (hub)**  
  https://docs.netscaler.com/en-us/netscaler-gateway/current-release/authentication/

### Global policy model

| Topic | Use in design when |
|-------|-------------------|
| Configuring Default Global Authentication Types | System-wide default auth type on Gateway/AAA |
| Configuring Authentication Without Authorization | Auth-only flows (no authz policy) |
| Configuring Authorization | Authorization policies and session/resource access |
| Disabling Authentication | Bypass or internal-only paths; document risk |
| Configuring Authentication for Specific Times | Time-based auth policies (maintenance, off-hours) |
| How Authentication Policies Work | Policy bind order, priority, Advanced vs Classic, visualizer inputs |

### Directory, certificates, and protocols

| Topic | Use in design when |
|-------|-------------------|
| Configuring Local Users | Local user accounts on ADC for lab or break-glass |
| Configuring Groups | Group extraction, policy assignment by group |
| Configuring LDAP Authentication | AD/LDAP primary auth, attribute maps, failover |
| Configuring Client Certificate Authentication | Smart card / cert auth, OCSP, CA chain |
| Configuring RADIUS Authentication | RADIUS for VPN/Gateway or MFA back-end |
| Configuring SAML Authentication | IdP federation, metadata, assertions for Gateway |
| Configuring TACACS+ Authentication | TACACS+ admin or user auth where required |

### Advanced auth, SSO, and access control

| Topic | Use in design when |
|-------|-------------------|
| Configuring Multifactor Authentication | MFA stacks before session establishment |
| Configuring single sign-on | SSO to StoreFront, web apps, or SAML domains |
| Configuring One-Time Password Use | OTP/Mobile application tokens |
| nFactor for Gateway Authentication | Multi-step login schemas, EPA, cascading factors |
| Unified Gateway Visualizer | End-to-end policy flow review (auth → session → resources) |
| Configure NetScaler Gateway to use RADIUS and LDAP Authentication with Mobile Devices | Mobile client auth chain (LDAP + RADIUS) |
| Restrict access to NetScaler Gateway for members of one Active Directory group | Group-based allow/deny on Gateway vserver |
| Device Posture checks on NetScaler Gateway | EPA/posture before or during auth (compliance, OS, antivirus) |

## Cloud — NetScaler ADC autoscale on Azure

| Topic | Use in design when |
|-------|-------------------|
| NetScaler ADC Azure autoscale (deployment guide) | VPX/autoscale groups in Azure, cloud parameter, scale policies, HA in Azure |

- **Citrix Tech Zone — NetScaler ADC Azure autoscale**  
  https://community.citrix.com/tech-zone/build/deployment-guides/netscaler-adc-azure-autoscale/

## Design document expectations

When the user selects any integration or authentication scope in discovery:

1. Add **NetScaler Gateway — authentication & authorization** with **policy tables** (authentication virtual server/policies, session policies, bind order, LDAP/RADIUS/SAML server profiles, groups, nFactor login schemas). Include only subsections for selected booleans. Mark **TBD** where discovery is incomplete.
2. Add **NetScaler Gateway — Citrix product integration** when product integration booleans are set (vservers, STA/StoreFront, session/profile bindings).
3. For **Azure ADC autoscale**, add **Azure deployment** subsection and cite the Tech Zone guide above.
4. List all applicable hub links under **Supplemental links** in the final deliverable.
