/**
 * Recommended starter actions for JPilot empty state, command menu, and dashboard shortcuts.
 * `prompt` actions send a chat message; `link` actions navigate to a tool page.
 */

export const jpilotCommandTabs = [
  { id: 'all', label: 'All' },
  { id: 'architect', label: 'Architect' },
  { id: 'operator', label: 'Operator' },
  { id: 'analyst', label: 'Analyst' }
]

/** Sidebar filter tags — click sets active filter in the command menu. */
export const jpilotCommandSidebar = [
  {
    title: 'Architect',
    items: [
      { id: 'citrix-delivery', label: 'StoreFront, DDC & Gateway' },
      { id: 'ha-dr', label: 'HA & disaster recovery' },
      { id: 'gslb', label: 'GSLB & multi-site' },
      { id: 'aws-cloud', label: 'Cloud (AWS & Azure)' },
      { id: 'network', label: 'Network & VLANs' },
      { id: 'security', label: 'Security & SSL/WAF' },
      { id: 'common', label: 'Common deployments' }
    ]
  },
  {
    title: 'Operator — Networking',
    items: [
      { id: 'networking', label: 'Channels, VLANs, routes' },
      { id: 'discover', label: 'Discover & inventory' }
    ]
  },
  {
    title: 'Operator — Traffic & apps',
    items: [
      { id: 'traffic-mgmt', label: 'Load balancing & GSLB' },
      { id: 'citrix-delivery', label: 'StoreFront, DDC & Gateway' },
      { id: 'guided', label: 'Guided forms' }
    ]
  },
  {
    title: 'Operator — Security',
    items: [
      { id: 'security', label: 'SSL, WAF & policies' },
      { id: 'ssl', label: 'Certificates & tools' }
    ]
  },
  {
    title: 'Analyst',
    items: [
      { id: 'diagnostics', label: 'Health & performance' },
      { id: 'networking', label: 'Network & connectivity' },
      { id: 'traffic-mgmt', label: 'LB, GSLB & sessions' },
      { id: 'security', label: 'SSL & WAF checks' },
      { id: 'citrix-delivery', label: 'Citrix workload checks' }
    ]
  },
  {
    title: 'Quick filters',
    items: [
      { id: 'link', label: 'Open tools' }
    ]
  }
]

/** Section layout per role tab — drives grouped results in the command menu. */
export const jpilotCommandSectionLayout = {
  architect: [{ title: 'Architect', sidebarTitle: 'Architect' }],
  operator: [
    { title: 'Operator — Networking', sidebarTitle: 'Operator — Networking' },
    { title: 'Operator — Traffic & apps', sidebarTitle: 'Operator — Traffic & apps' },
    { title: 'Operator — Security', sidebarTitle: 'Operator — Security' }
  ],
  analyst: [{ title: 'Analyst', sidebarTitle: 'Analyst' }],
  all: [
    { title: 'Architect', sidebarTitle: 'Architect' },
    { title: 'Operator — Networking', sidebarTitle: 'Operator — Networking' },
    { title: 'Operator — Traffic & apps', sidebarTitle: 'Operator — Traffic & apps' },
    { title: 'Operator — Security', sidebarTitle: 'Operator — Security' },
    { title: 'Analyst', sidebarTitle: 'Analyst' }
  ]
}

function sidebarItemsForTitle(title) {
  const block = jpilotCommandSidebar.find((s) => s.title === title)
  return block?.items || []
}

/** @type {Record<string, string[]>} */
const COMMAND_VENDOR_OVERRIDES = {
  'arch-sdx-multi-tenant': ['sdx']
}

const DEFAULT_COMMAND_VENDORS = ['netscaler']

/**
 * Vendor id used to filter recommended actions (`netscaler`, `sdx`, `cisco`, `f5`).
 * @param {import('./jpilotRecommendedActions').JpilotCommand} cmd
 * @returns {string[]}
 */
export function getCommandVendors(cmd) {
  if (Array.isArray(cmd.vendors) && cmd.vendors.length) return cmd.vendors
  if (COMMAND_VENDOR_OVERRIDES[cmd.id]) return COMMAND_VENDOR_OVERRIDES[cmd.id]
  return DEFAULT_COMMAND_VENDORS
}

/**
 * @param {import('./jpilotRecommendedActions').JpilotCommand} cmd
 * @param {string} vendor
 */
export function commandMatchesVendor(cmd, vendor) {
  return getCommandVendors(cmd).includes(vendor)
}

/**
 * When an appliance is selected, filter actions to its vendor; otherwise show all.
 * @param {{ vendor?: string|null } | null | undefined} appliance
 * @returns {string|null}
 */
export function resolveCommandFilterVendor(appliance) {
  if (!appliance) return null
  const raw = String(appliance.vendor || 'netscaler').trim().toLowerCase()
  return raw || 'netscaler'
}

/**
 * Sidebar filters that still have at least one command for the active vendor/tab.
 * @param {{ tab?: string, vendor?: string|null }} opts
 */
export function getJpilotCommandSidebar(opts = {}) {
  const availableTags = new Set(
    filterJpilotCommands({ tab: opts.tab || 'all', vendor: opts.vendor ?? null }).flatMap(
      (cmd) => cmd.tags
    )
  )
  return jpilotCommandSidebar
    .map((section) => ({
      ...section,
      items: section.items.filter((item) => availableTags.has(item.id))
    }))
    .filter((section) => section.items.length)
}

/**
 * @param {{ tab?: string, filterTag?: string|null, query?: string, vendor?: string|null }} opts
 * @returns {{ id: string, title: string, commands: import('./jpilotRecommendedActions').JpilotCommand[] }[]}
 */
export function getGroupedCommandResults(opts = {}) {
  const tab = opts.tab || 'all'
  const filterTag = opts.filterTag || null
  const matched = filterJpilotCommands(opts)

  if (filterTag) {
    const label =
      jpilotCommandSidebar.flatMap((s) => s.items).find((i) => i.id === filterTag)?.label || filterTag
    return [{ id: filterTag, title: label, commands: matched }]
  }

  const layout = jpilotCommandSectionLayout[tab] || jpilotCommandSectionLayout.all
  const groups = []
  const assigned = new Set()

  for (const block of layout) {
    const sections = sidebarItemsForTitle(block.sidebarTitle)
    for (const section of sections) {
      const commands = matched.filter(
        (cmd) => !assigned.has(cmd.id) && cmd.tags.includes(section.id)
      )
      for (const cmd of commands) {
        assigned.add(cmd.id)
      }
      if (commands.length) {
        groups.push({ id: section.id, title: section.label, commands })
      }
    }
  }

  const unassigned = matched.filter((cmd) => !assigned.has(cmd.id))
  if (unassigned.length) {
    groups.push({ id: 'other', title: 'More actions', commands: unassigned })
  }

  return groups
}

/** @typedef {'prompt'|'link'} JpilotCommandType */

/**
 * @typedef {Object} JpilotCommand
 * @property {string} id
 * @property {string} label
 * @property {string} [subtitle]
 * @property {string} icon
 * @property {JpilotCommandType} type
 * @property {string} [text]
 * @property {string} [to]
 * @property {'architect'|'operator'|'analyst'} role
 * @property {string[]} tags
 * @property {string[]} [vendors] — defaults to NetScaler ADC when omitted
 */

/** @type {JpilotCommand[]} */
export const jpilotCommands = [
  // ═══════════════════════════════════════════════════════════════════════════
  // Architect — design & discovery (choice forms → design document)
  // ═══════════════════════════════════════════════════════════════════════════
  {
    id: 'arch-storefront-lb',
    label: 'Load balancing design — Citrix StoreFront',
    subtitle: 'Architect · StoreFront & CVAD',
    icon: 'pi pi-desktop',
    type: 'prompt',
    role: 'architect',
    tags: ['citrix-delivery', 'common', 'architect'],
    text:
      'Design HTTPS load balancing for Citrix StoreFront (SSL vserver, monitors, persistence, subnet routing). Use jpilot-form discovery, then a design document with LB/SSL tables and Handoff for Operator.'
  },
  {
    id: 'arch-ddc-lb',
    label: 'Load balancing design — Delivery Controllers',
    subtitle: 'Architect · StoreFront & CVAD',
    icon: 'pi pi-server',
    type: 'prompt',
    role: 'architect',
    tags: ['citrix-delivery', 'common', 'architect'],
    text:
      'Design load balancing for Citrix Delivery Controllers (XML/RDS/Citrix protocols, SSL, health monitors, least-connection vs round robin). Discovery via forms, then design tables and phased implementation steps.'
  },
  {
    id: 'arch-ha-config',
    label: 'High availability (HA pair) design',
    subtitle: 'Architect · HA & DR',
    icon: 'pi pi-clone',
    type: 'prompt',
    role: 'architect',
    tags: ['ha-dr', 'common', 'architect'],
    text:
      'Design NetScaler ADC in an active/passive HA pair: heartbeat interfaces, failover, config sync, NSAPI/RPC, and maintenance mode. Use choice forms, then document HA topology, monitoring, and verification.'
  },
  {
    id: 'arch-gslb-design',
    label: 'Configure GSLB (multi-site DNS)',
    subtitle: 'Architect · GSLB & multi-site',
    icon: 'pi pi-globe',
    type: 'prompt',
    role: 'architect',
    tags: ['gslb', 'common', 'architect'],
    text:
      'Design Global Server Load Balancing across two or more datacenters: GSLB sites, MEP, ADNS, GSLB vserver/services, and public DNS integration. Discovery with forms, then GSLB entity tables and rollout plan.'
  },
  {
    id: 'arch-gateway-cvad',
    label: 'Citrix Gateway for CVAD / DaaS',
    subtitle: 'Architect · StoreFront & CVAD',
    icon: 'pi pi-sign-in',
    type: 'prompt',
    role: 'architect',
    tags: ['citrix-delivery', 'security', 'common', 'architect'],
    text:
      'Design Citrix Gateway for Virtual Apps and Desktops: authentication (LDAP/SAML/MSAL), session policies, STA/StoreFront integration, SSL, and split tunneling. Use the Citrix Gateway & product integration discovery form (StoreFront, CVAD, user access patterns), then Gateway + AAA sections per docs.netscaler.com integrate-citrix-gateway-with-citrix-products.'
  },
  {
    id: 'arch-gateway-citrix-integrations',
    label: 'Gateway — Integrate with Citrix products',
    subtitle: 'Architect · StoreFront & CVAD',
    icon: 'pi pi-sign-in',
    type: 'prompt',
    role: 'architect',
    tags: ['citrix-delivery', 'security', 'common', 'architect'],
    text:
      'Design per Integrate NetScaler Gateway with Citrix products: user access to apps/desktops/ShareFile, StoreFront, CVAD, CEM settings, combined Gateway+CEM+CVAD deploy. Use jpilot-form booleans for each topic, then Gateway integration tables and supplemental links to docs.netscaler.com.'
  },
  {
    id: 'arch-gateway-intune-msal',
    label: 'Gateway — Intune, MSAL & Azure AD',
    subtitle: 'Architect · Security & Gateway',
    icon: 'pi pi-id-card',
    type: 'prompt',
    role: 'architect',
    tags: ['citrix-delivery', 'security', 'aws-cloud', 'architect'],
    text:
      'Design Gateway with Microsoft Intune MDM, micro VPN with Endpoint Manager, MSAL token authentication, Azure portal Gateway app, NAC device check, and Azure AD Graph notes. Discovery form booleans, then policy tables and official doc links.'
  },
  {
    id: 'arch-azure-adc-autoscale',
    label: 'NetScaler ADC Azure autoscale',
    subtitle: 'Architect · Azure & cloud',
    icon: 'pi pi-cloud',
    type: 'prompt',
    role: 'architect',
    tags: ['aws-cloud', 'ha-dr', 'common', 'architect'],
    text:
      'Design NetScaler ADC VPX autoscale in Azure per Citrix Tech Zone (community.citrix.com netscaler-adc-azure-autoscale): cloud credentials, autoscale profile, scale policies, HA, and networking. Include Azure deployment section and supplemental link.'
  },
  {
    id: 'arch-exchange-gateway-lb',
    label: 'Exchange LB with email security filtering',
    subtitle: 'Architect · Application delivery',
    icon: 'pi pi-envelope',
    type: 'prompt',
    role: 'architect',
    tags: ['common', 'citrix-delivery', 'architect'],
    text:
      'Design load balancing for Microsoft Exchange with email security filtering on NetScaler Gateway/ADC. Discovery form option for Exchange LB; document vserver, policies, and docs.netscaler.com exchange email security filtering guide.'
  },
  {
    id: 'arch-dual-dc-ha',
    label: 'Two-datacenter HA with GSLB',
    subtitle: 'Architect · HA & multi-site',
    icon: 'pi pi-compass',
    type: 'prompt',
    role: 'architect',
    tags: ['ha-dr', 'gslb', 'architect'],
    text:
      'Design two datacenters with Citrix ADC VPX in HA per site and GSLB between sites (on-prem, AWS per region, or mixed). Choice-form discovery, then VLAN/subnet/IP tables, GSLB sites, AWS deployment section if applicable, and Handoff for Operator.'
  },
  {
    id: 'arch-reverse-proxy-ssl',
    label: 'Internet reverse proxy + SSL offload',
    subtitle: 'Architect · Common deployment',
    icon: 'pi pi-lock',
    type: 'prompt',
    role: 'architect',
    tags: ['common', 'security', 'architect'],
    text:
      'Design a common internet-facing pattern: SSL termination on ADC, HTTP/HTTPS services, monitors, and cipher hardening. Document SSL profiles, vserver/service group tables, and Qualys-style verification steps.'
  },
  {
    id: 'arch-content-switching',
    label: 'Content switching (URL/path routing)',
    subtitle: 'Architect · Common deployment',
    icon: 'pi pi-directions',
    type: 'prompt',
    role: 'architect',
    tags: ['common', 'architect'],
    text:
      'Design content switching virtual servers to route traffic by hostname, URL path, or headers to different backend pools. Include CS policy tables and when to use CS vs separate LB vservers.'
  },
  {
    id: 'arch-waf-migration',
    label: 'Web App Firewall (WAF) design',
    subtitle: 'Architect · Security & WAF',
    icon: 'pi pi-shield',
    type: 'prompt',
    role: 'architect',
    tags: ['migration', 'security', 'architect'],
    text:
      'Design Citrix Web App Firewall deployment: profiles, signatures, learning vs lockdown, policy bindings on LB vservers. Choice forms for app compatibility, then WAF tables and phased rollout.'
  },
  {
    id: 'arch-vlan-ip-plan',
    label: 'VLAN and IP addressing plan',
    subtitle: 'Architect · Network & VLANs',
    icon: 'pi pi-map',
    type: 'prompt',
    role: 'architect',
    tags: ['network', 'architect'],
    text:
      'Design VLANs and IPs (NSIP, SNIP, VIP, management) for two-arm HA. One topic per form turn, then addressing tables in the design document.'
  },
  {
    id: 'arch-one-vs-two-arm',
    label: 'One-arm vs two-arm topology',
    subtitle: 'Architect · Network & VLANs',
    icon: 'pi pi-share-alt',
    type: 'prompt',
    role: 'architect',
    tags: ['network', 'architect'],
    text:
      'Compare one-arm vs two-arm ADC for my constraints. Forms for traffic and management needs, then topology recommendation and PBR for management isolation.'
  },
  {
    id: 'arch-ssl-hardening',
    label: 'SSL/TLS hardening (A+ target)',
    subtitle: 'Architect · Security',
    icon: 'pi pi-key',
    type: 'prompt',
    role: 'architect',
    tags: ['security', 'architect'],
    text:
      'Design SSL profiles and cipher groups for public vservers. Document cipher tables, TLS versions, and compatibility risks in a formal deliverable.'
  },
  {
    id: 'arch-adm-monitoring',
    label: 'Citrix ADM & monitoring design',
    subtitle: 'Architect · Operations',
    icon: 'pi pi-chart-line',
    type: 'prompt',
    role: 'architect',
    tags: ['architect', 'common'],
    text:
      'Design ADM (agent/cloud), syslog, analytics, licensing, and backup for multiple ADCs. Forms first, then monitoring and ADM configuration tables.'
  },
  {
    id: 'arch-firmware-roadmap',
    label: 'Firmware upgrade roadmap',
    subtitle: 'Architect · Platform',
    icon: 'pi pi-arrow-up',
    type: 'prompt',
    role: 'architect',
    tags: ['architect', 'migration'],
    text:
      'Create a phased firmware upgrade plan for HA pairs: prerequisites, risks, maintenance windows, rollback, and verification checklist.'
  },
  {
    id: 'arch-auth-ldap',
    label: 'Authentication design (LDAP + fallback)',
    subtitle: 'Architect · AAA',
    icon: 'pi pi-users',
    type: 'prompt',
    role: 'architect',
    tags: ['architect', 'security', 'citrix-delivery'],
    text:
      'Design ADC/Gateway authentication: LDAP primary, local fallback, group extraction, and session policies. Use Gateway authentication & authorization discovery booleans, then policy tables per docs.netscaler.com authentication hub.'
  },
  {
    id: 'arch-gateway-aaa-full',
    label: 'Gateway authentication & authorization',
    subtitle: 'Architect · AAA & Gateway',
    icon: 'pi pi-shield',
    type: 'prompt',
    role: 'architect',
    tags: ['security', 'citrix-delivery', 'common', 'architect'],
    text:
      'Design NetScaler Gateway AAA: global auth types, auth vs authorization, policy bind order, LDAP/RADIUS/SAML/TACACS+/cert, MFA, SSO, OTP, nFactor, Unified Gateway Visualizer, mobile RADIUS+LDAP, AD group restriction, device posture. Use jpilot-form booleans for each topic, then authentication policy tables and supplemental links.'
  },
  {
    id: 'arch-greenfield-sizing',
    label: 'Greenfield VPX sizing & platform',
    subtitle: 'Architect · Sizing',
    icon: 'pi pi-box',
    type: 'prompt',
    role: 'architect',
    tags: ['architect', 'ha-dr', 'common'],
    text:
      'Greenfield VPX planning: throughput, SSL TPS, edition, HA (on-prem or AWS EC2). Discovery forms, then sizing summary and platform tables.'
  },
  {
    id: 'arch-aws-vpx-ec2',
    label: 'Citrix ADC VPX on AWS (EC2)',
    subtitle: 'Architect · AWS & cloud',
    icon: 'pi pi-cloud',
    type: 'prompt',
    role: 'architect',
    tags: ['aws-cloud', 'network', 'ha-dr', 'common', 'architect'],
    text:
      'Design Citrix ADC VPX on AWS EC2: VPC/subnets, ENI mapping (mgmt/client/server), security groups, instance sizing, Marketplace/BYOL licensing, HA across AZs, optional cloud/autoscale integration, Route 53/DNS, and hybrid VPN/TGW/DX if needed. Use jpilot-form discovery, then full design document with AWS deployment tables and Handoff for Operator.'
  },
  {
    id: 'arch-aws-gslb-route53',
    label: 'GSLB on AWS with Route 53',
    subtitle: 'Architect · AWS & GSLB',
    icon: 'pi pi-globe',
    type: 'prompt',
    role: 'architect',
    tags: ['aws-cloud', 'gslb', 'architect'],
    text:
      'Design multi-site GSLB when ADC runs in AWS: GSLB sites/MEP, ADNS, public DNS delegation to Route 53 (or external DNS), health monitors, and VPC networking per region. Forms first, then GSLB + AWS sections in the design document.'
  },
  {
    id: 'arch-aws-gateway-cvad',
    label: 'Citrix Gateway on ADC in AWS',
    subtitle: 'Architect · AWS & Gateway',
    icon: 'pi pi-sign-in',
    type: 'prompt',
    role: 'architect',
    tags: ['aws-cloud', 'citrix-delivery', 'security', 'architect'],
    text:
      'Design Citrix Gateway on VPX in AWS for CVAD/DaaS: VPC ingress, SSL on NLB/ADC, authentication, STA/StoreFront paths over VPN/TGW, and security groups. Discovery forms, then Gateway + AWS deployment tables.'
  },
  {
    id: 'arch-nfactor-aaa',
    label: 'nFactor / multi-factor authentication',
    subtitle: 'Architect · Security & Gateway',
    icon: 'pi pi-id-card',
    type: 'prompt',
    role: 'architect',
    tags: ['security', 'citrix-delivery', 'architect'],
    text:
      'Design nFactor for Gateway Authentication: login schemas, cascading factors, EPA/posture, LDAP/RADIUS/SAML. Enable nFactor and related booleans in Gateway authentication discovery form, then policy tables and Unified Gateway Visualizer notes in the design document.'
  },
  {
    id: 'arch-rate-limit',
    label: 'Rate limiting & DDoS protection design',
    subtitle: 'Architect · Security',
    icon: 'pi pi-ban',
    type: 'prompt',
    role: 'architect',
    tags: ['security', 'common', 'architect'],
    text:
      'Design rate limiting, bot detection, and surge protection on internet-facing vservers. Document policies, thresholds, and monitoring in the deliverable.'
  },
  {
    id: 'arch-ip-reputation',
    label: 'IP reputation & bot management',
    subtitle: 'Architect · Security',
    icon: 'pi pi-eye',
    type: 'prompt',
    role: 'architect',
    tags: ['security', 'common', 'architect'],
    text:
      'Design IP reputation integration and bot management policies for public apps. Include enablement steps, false-positive handling, and WAF coordination.'
  },
  {
    id: 'arch-microservices-ingress',
    label: 'Kubernetes / microservices ingress',
    subtitle: 'Architect · Common deployment',
    icon: 'pi pi-cloud',
    type: 'prompt',
    role: 'architect',
    tags: ['common', 'architect'],
    text:
      'Design ADC as north-south ingress for microservices: content switching, path routing, mTLS options, and monitor strategy. Discovery forms then CS/LB tables.'
  },
  {
    id: 'arch-oauth-api',
    label: 'OAuth / API gateway pattern',
    subtitle: 'Architect · Common deployment',
    icon: 'pi pi-code',
    type: 'prompt',
    role: 'architect',
    tags: ['common', 'security', 'architect'],
    text:
      'Design API traffic management with authentication (OAuth/JWT introspection patterns), rate limits, and SSL. Document AAA and responder policies.'
  },
  {
    id: 'arch-global-server-persist',
    label: 'Persistence & session design',
    subtitle: 'Architect · Traffic design',
    icon: 'pi pi-sync',
    type: 'prompt',
    role: 'architect',
    tags: ['common', 'citrix-delivery', 'architect'],
    text:
      'Design LB persistence (cookie, source IP, SSL session) for stateful apps and Citrix workloads. Compare options with forms, then persistence profile tables.'
  },
  {
    id: 'arch-gslb-active-active',
    label: 'GSLB active/active & custom DNS',
    subtitle: 'Architect · GSLB',
    icon: 'pi pi-globe',
    type: 'prompt',
    role: 'architect',
    tags: ['gslb', 'architect'],
    text:
      'Design active/active GSLB with custom DNS responses, weights, and persistence across sites. Document MEP, site metrics, and failover behavior.'
  },
  {
    id: 'arch-gslb-cname',
    label: 'GSLB public CNAME delegation',
    subtitle: 'Architect · GSLB',
    icon: 'pi pi-link',
    type: 'prompt',
    role: 'architect',
    tags: ['gslb', 'architect'],
    text:
      'Design public DNS delegation to GSLB ADNS for application FQDNs. Forms for zones and records, then DNS/GSLB binding tables.'
  },
  {
    id: 'arch-mgmt-pbr',
    label: 'Management plane isolation (PBR)',
    subtitle: 'Architect · Network',
    icon: 'pi pi-shield',
    type: 'prompt',
    role: 'architect',
    tags: ['network', 'security', 'architect'],
    text:
      'Design out-of-band management and PBR so NSIP/management traffic never crosses production VLANs. VLAN and route tables in the design doc.'
  },
  {
    id: 'arch-sdx-multi-tenant',
    label: 'SDX multi-tenant VPX design',
    subtitle: 'Architect · Platform',
    icon: 'pi pi-table',
    type: 'prompt',
    role: 'architect',
    tags: ['network', 'ha-dr', 'architect'],
    vendors: ['sdx'],
    text:
      'Design Citrix ADC SDX with multiple VPX instances: channel allocation, management partitioning, and HA per tenant.'
  },
  {
    id: 'arch-mpx-capacity',
    label: 'MPX hardware capacity design',
    subtitle: 'Architect · Sizing',
    icon: 'pi pi-server',
    type: 'prompt',
    role: 'architect',
    tags: ['ha-dr', 'common', 'architect'],
    text:
      'Size NetScaler MPX for SSL TPS, throughput, and HA. Document hardware SKU, port plan, and growth headroom.'
  },
  {
    id: 'arch-citrix-director',
    label: 'Director / monitoring integration',
    subtitle: 'Architect · Citrix',
    icon: 'pi pi-chart-bar',
    type: 'prompt',
    role: 'architect',
    tags: ['citrix-delivery', 'common', 'architect'],
    text:
      'Design integration between ADC, Citrix Director/ADM, and syslog/SNMP for CVAD monitoring. Tables for collectors and alert thresholds.'
  },
  {
    id: 'arch-unified-gateway',
    label: 'Unified Gateway (VPN + AAA + SWG)',
    subtitle: 'Architect · Gateway',
    icon: 'pi pi-sign-in',
    type: 'prompt',
    role: 'architect',
    tags: ['citrix-delivery', 'security', 'architect'],
    text:
      'Design Unified Gateway combining VPN, ICA proxy, and secure web gateway policies. Discovery forms, then Gateway policy tables.'
  },
  {
    id: 'arch-appflow-analytics',
    label: 'AppFlow / analytics export',
    subtitle: 'Architect · Operations',
    icon: 'pi pi-chart-line',
    type: 'prompt',
    role: 'architect',
    tags: ['common', 'architect'],
    text:
      'Design AppFlow and analytics export to SIEM or observability stack. Document collectors, sampling, and retention.'
  },
  {
    id: 'arch-rewrite-canonical',
    label: 'Rewrite & responder (SEO/redirects)',
    subtitle: 'Architect · Traffic',
    icon: 'pi pi-arrow-right',
    type: 'prompt',
    role: 'architect',
    tags: ['common', 'architect'],
    text:
      'Design rewrite and responder policies for URL canonicalization, maintenance pages, and security headers on LB vservers.'
  },
  {
    id: 'arch-cache-compression',
    label: 'Compression & caching edge design',
    subtitle: 'Architect · Performance',
    icon: 'pi pi-bolt',
    type: 'prompt',
    role: 'architect',
    tags: ['common', 'architect'],
    text:
      'Design HTTP compression and content caching at the ADC for static workloads. Document policies, cache sizes, and invalidation approach.'
  },
  {
    id: 'arch-bcp-dr-tabletop',
    label: 'DR tabletop & failover test plan',
    subtitle: 'Architect · HA & DR',
    icon: 'pi pi-calendar',
    type: 'prompt',
    role: 'architect',
    tags: ['ha-dr', 'gslb', 'architect'],
    text:
      'Create a DR tabletop and failover test plan for ADC HA and GSLB: scenarios, success criteria, and rollback — as part of the design deliverable.'
  },
  {
    id: 'arch-ctx-hybrid-cloud',
    label: 'Hybrid cloud ADC placement',
    subtitle: 'Architect · Network',
    icon: 'pi pi-cloud',
    type: 'prompt',
    role: 'architect',
    tags: ['network', 'common', 'architect'],
    text:
      'Design ADC placement for hybrid cloud (on-prem + AWS VPC). Document VPN/TGW/DX connectivity, subnet/SNIP/VIP plan per site, and latency assumptions. Include AWS deployment tables when VPX runs in EC2.'
  },
  {
    id: 'arch-ipv6-dual-stack',
    label: 'Dual-stack IPv4/IPv6 design',
    subtitle: 'Architect · Network',
    icon: 'pi pi-globe',
    type: 'prompt',
    role: 'architect',
    tags: ['network', 'architect'],
    text: 'Design dual-stack IPv4/IPv6 on ADC: addressing, routing, and vserver considerations. Tables per site.'
  },
  {
    id: 'arch-private-link',
    label: 'Private link / dedicated interconnect',
    subtitle: 'Architect · Network',
    icon: 'pi pi-link',
    type: 'prompt',
    role: 'architect',
    tags: ['network', 'architect'],
    text: 'Design ADC connectivity over private link or Express Direct. Document routes, MTU, and failover.'
  },
  {
    id: 'arch-segmentation',
    label: 'Network segmentation (DMZ tiers)',
    subtitle: 'Architect · Network',
    icon: 'pi pi-table',
    type: 'prompt',
    role: 'architect',
    tags: ['network', 'security', 'architect'],
    text: 'Design DMZ segmentation with ADC between tiers. VLAN matrix, ACL assumptions, and SNIP per zone.'
  },
  {
    id: 'arch-gslb-health',
    label: 'GSLB custom health monitors',
    subtitle: 'Architect · GSLB',
    icon: 'pi pi-heart',
    type: 'prompt',
    role: 'architect',
    tags: ['gslb', 'architect'],
    text: 'Design GSLB site metrics and custom monitors for application health. Document MEP and metric exchange.'
  },
  {
    id: 'arch-gslb-persistence',
    label: 'GSLB site persistence design',
    subtitle: 'Architect · GSLB',
    icon: 'pi pi-sync',
    type: 'prompt',
    role: 'architect',
    tags: ['gslb', 'common', 'architect'],
    text: 'Design GSLB persistence across sites for stateful apps. Compare GSLB methods and DNS TTL strategy.'
  },
  {
    id: 'arch-gslb-cloud-dns',
    label: 'GSLB with external DNS provider',
    subtitle: 'Architect · GSLB',
    icon: 'pi pi-cloud',
    type: 'prompt',
    role: 'architect',
    tags: ['gslb', 'architect'],
    text: 'Design GSLB when public DNS stays at Route53/Azure DNS. Document delegation, glue records, and health checks.'
  },
  {
    id: 'arch-gslb-maintenance',
    label: 'GSLB maintenance / admin flags',
    subtitle: 'Architect · GSLB',
    icon: 'pi pi-wrench',
    type: 'prompt',
    role: 'architect',
    tags: ['gslb', 'ha-dr', 'architect'],
    text: 'Design GSLB maintenance mode and administrative flags for planned outages. Runbook section in design doc.'
  },
  {
    id: 'arch-gslb-latency',
    label: 'GSLB proximity & RTT policies',
    subtitle: 'Architect · GSLB',
    icon: 'pi pi-map',
    type: 'prompt',
    role: 'architect',
    tags: ['gslb', 'architect'],
    text: 'Design GSLB method selection using RTT/static proximity for global users. Forms for sites and thresholds.'
  },
  {
    id: 'arch-ha-stretch',
    label: 'Stretched VLAN / L2 stretch HA',
    subtitle: 'Architect · HA & DR',
    icon: 'pi pi-clone',
    type: 'prompt',
    role: 'architect',
    tags: ['ha-dr', 'network', 'architect'],
    text: 'Design HA across stretched L2 domains. Document risks, split-brain avoidance, and recommended alternatives.'
  },
  {
    id: 'arch-ha-license',
    label: 'HA licensing & pooled capacity',
    subtitle: 'Architect · HA & DR',
    icon: 'pi pi-ticket',
    type: 'prompt',
    role: 'architect',
    tags: ['ha-dr', 'architect'],
    text: 'Document HA pair licensing, pooled bandwidth, and ADM pooling in the platform design section.'
  },
  {
    id: 'arch-ha-incumbent',
    label: 'Migrate standalone to HA pair',
    subtitle: 'Architect · HA & DR',
    icon: 'pi pi-arrow-right',
    type: 'prompt',
    role: 'architect',
    tags: ['ha-dr', 'migration', 'architect'],
    text: 'Design migration from standalone ADC to HA pair with minimal outage. Phased steps and rollback.'
  },
  {
    id: 'arch-ha-third-site',
    label: 'Witness / third-site quorum',
    subtitle: 'Architect · HA & DR',
    icon: 'pi pi-compass',
    type: 'prompt',
    role: 'architect',
    tags: ['ha-dr', 'architect'],
    text: 'Design HA with witness or third-site considerations for split-brain prevention where applicable.'
  },
  {
    id: 'arch-ctx-vda-registration',
    label: 'VDA registration & XML design',
    subtitle: 'Architect · Citrix DDC',
    icon: 'pi pi-server',
    type: 'prompt',
    role: 'architect',
    tags: ['citrix-delivery', 'architect'],
    text: 'Design LB and firewall paths for VDA registration, XML, and broker traffic in CVAD.'
  },
  {
    id: 'arch-ctx-roaming',
    label: 'User roaming profiles & UPM paths',
    subtitle: 'Architect · Citrix',
    icon: 'pi pi-users',
    type: 'prompt',
    role: 'architect',
    tags: ['citrix-delivery', 'architect'],
    text: 'Design ADC paths for UPM/FSLogix and profile storage access via Citrix workloads.'
  },
  {
    id: 'arch-ctx-hdx-edge',
    label: 'HDX over WAN / EDT design',
    subtitle: 'Architect · Citrix',
    icon: 'pi pi-bolt',
    type: 'prompt',
    role: 'architect',
    tags: ['citrix-delivery', 'network', 'architect'],
    text: 'Design Gateway/ADC settings for HDX/EDT over high-latency links. Document ports and UDP policies.'
  },
  {
    id: 'arch-ctx-internal-gateway',
    label: 'Internal vs external Gateway zones',
    subtitle: 'Architect · Gateway',
    icon: 'pi pi-sign-in',
    type: 'prompt',
    role: 'architect',
    tags: ['citrix-delivery', 'security', 'architect'],
    text: 'Design separate internal and external Gateway vservers with different auth and split tunnel policies.'
  },
  {
    id: 'arch-ctx-saml-oidc',
    label: 'SAML/OIDC to StoreFront',
    subtitle: 'Architect · Citrix',
    icon: 'pi pi-id-card',
    type: 'prompt',
    role: 'architect',
    tags: ['citrix-delivery', 'security', 'architect'],
    text: 'Design SAML/OIDC integration for StoreFront/Gateway using AAA policies. Prerequisites and flow tables.'
  },
  {
    id: 'arch-ctx-multi-geo-users',
    label: 'Multi-geo user proximity (CVAD)',
    subtitle: 'Architect · Citrix & GSLB',
    icon: 'pi pi-globe',
    type: 'prompt',
    role: 'architect',
    tags: ['citrix-delivery', 'gslb', 'architect'],
    text: 'Design GSLB + Gateway proximity for global CVAD users. Site selection and STA/StoreFront mapping.'
  },
  {
    id: 'arch-sec-zero-trust',
    label: 'Zero trust access edge',
    subtitle: 'Architect · Security',
    icon: 'pi pi-shield',
    type: 'prompt',
    role: 'architect',
    tags: ['security', 'common', 'architect'],
    text: 'Design zero-trust style access with Gateway, MFA, device posture, and micro-segmentation at ADC.'
  },
  {
    id: 'arch-sec-tls-mtls',
    label: 'mTLS to backend design',
    subtitle: 'Architect · Security',
    icon: 'pi pi-lock',
    type: 'prompt',
    role: 'architect',
    tags: ['security', 'architect'],
    text: 'Design mutual TLS between ADC and backend services. Client cert profiles and CA chain tables.'
  },
  {
    id: 'arch-ctx-resource-locations',
    label: 'Resource locations & zones (CVAD)',
    subtitle: 'Architect · Citrix',
    icon: 'pi pi-map',
    type: 'prompt',
    role: 'architect',
    tags: ['citrix-delivery', 'architect'],
    text: 'Design ADC/GSLB mapping for CVAD resource locations and zones. Document FQDNs and site affinity.'
  },
  {
    id: 'arch-ha-sync-exclude',
    label: 'HA config sync exclusions',
    subtitle: 'Architect · HA',
    icon: 'pi pi-cog',
    type: 'prompt',
    role: 'architect',
    tags: ['ha-dr', 'architect'],
    text: 'Design HA sync groups and excluded objects (routes, SNMP) for safe failover behavior.'
  },
  {
    id: 'arch-ha-cfg-audit',
    label: 'HA config audit checklist',
    subtitle: 'Architect · HA',
    icon: 'pi pi-list-check',
    type: 'prompt',
    role: 'architect',
    tags: ['ha-dr', 'architect'],
    text: 'Produce HA configuration audit checklist: node IDs, heartbeats, routes on secondary, and validation steps.'
  },
  {
    id: 'arch-ha-graceful',
    label: 'Graceful HA switchover plan',
    subtitle: 'Architect · HA',
    icon: 'pi pi-refresh',
    type: 'prompt',
    role: 'architect',
    tags: ['ha-dr', 'architect'],
    text: 'Document graceful HA switchover procedure for code upgrades with user impact analysis.'
  },
  {
    id: 'arch-ha-incident',
    label: 'HA split-brain recovery',
    subtitle: 'Architect · HA',
    icon: 'pi pi-exclamation-triangle',
    type: 'prompt',
    role: 'architect',
    tags: ['ha-dr', 'architect'],
    text: 'Design split-brain detection and recovery runbook for ADC HA pairs.'
  },
  {
    id: 'arch-gslb-weight',
    label: 'GSLB weighted active/passive',
    subtitle: 'Architect · GSLB',
    icon: 'pi pi-sliders-h',
    type: 'prompt',
    role: 'architect',
    tags: ['gslb', 'architect'],
    text: 'Design weighted GSLB for active/passive DR with manual override weights per site.'
  },
  {
    id: 'arch-gslb-fqdn-plan',
    label: 'GSLB FQDN & zone delegation plan',
    subtitle: 'Architect · GSLB',
    icon: 'pi pi-link',
    type: 'prompt',
    role: 'architect',
    tags: ['gslb', 'architect'],
    text: 'Document all public FQDNs, zones, TTLs, and GSLB vserver mappings in design tables.'
  },
  {
    id: 'arch-gslb-capacity',
    label: 'GSLB capacity & QPS sizing',
    subtitle: 'Architect · GSLB',
    icon: 'pi pi-chart-bar',
    type: 'prompt',
    role: 'architect',
    tags: ['gslb', 'architect'],
    text: 'Size GSLB DNS QPS and ADNS capacity per site. Include headroom and monitoring thresholds.'
  },
  {
    id: 'arch-gslb-failover-test',
    label: 'GSLB failover test script',
    subtitle: 'Architect · GSLB',
    icon: 'pi pi-play',
    type: 'prompt',
    role: 'architect',
    tags: ['gslb', 'ha-dr', 'architect'],
    text: 'Write GSLB failover test script: stop site, verify DNS answers, restore — for design appendix.'
  },
  {
    id: 'arch-net-jumbo',
    label: 'Jumbo frames & MTU design',
    subtitle: 'Architect · Network',
    icon: 'pi pi-arrows-v',
    type: 'prompt',
    role: 'architect',
    tags: ['network', 'architect'],
    text: 'Design jumbo frame support end-to-end on ADC channels and VLANs. MTU tables and test plan.'
  },
  {
    id: 'arch-net-qos',
    label: 'QoS / CoS marking design',
    subtitle: 'Architect · Network',
    icon: 'pi pi-sliders-v',
    type: 'prompt',
    role: 'architect',
    tags: ['network', 'architect'],
    text: 'Design QoS marking for Citrix and business traffic traversing ADC interfaces.'
  },
  {
    id: 'arch-net-firewall',
    label: 'Firewall rule matrix (ADC)',
    subtitle: 'Architect · Network',
    icon: 'pi pi-shield',
    type: 'prompt',
    role: 'architect',
    tags: ['network', 'security', 'architect'],
    text: 'Produce firewall rule matrix: who talks to NSIP/SNIP/VIP on which ports between tiers.'
  },
  {
    id: 'arch-net-dns-forward',
    label: 'ADC DNS forwarder / ADNS design',
    subtitle: 'Architect · Network',
    icon: 'pi pi-globe',
    type: 'prompt',
    role: 'architect',
    tags: ['network', 'gslb', 'architect'],
    text: 'Design DNS forwarding and ADNS placement for internal vs external resolution.'
  },
  {
    id: 'arch-net-l3-out',
    label: 'L3-out / routed mode segments',
    subtitle: 'Architect · Network',
    icon: 'pi pi-share-alt',
    type: 'prompt',
    role: 'architect',
    tags: ['network', 'architect'],
    text: 'Design routed L3 segments to ADC SNIPs without L2 stretch. Routing and ARP considerations.'
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // Operator — implement on connected appliance
  // ═══════════════════════════════════════════════════════════════════════════
  // Discover
  {
    id: 'system-info',
    label: 'Firmware, hostname, and serial',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-info-circle',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator'],
    text: 'Show system info for the connected appliance — firmware version, hostname, management IP, and serial number.'
  },
  {
    id: 'list-ips',
    label: 'List all IP addresses (NSIP, SNIP, VIP)',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-map-marker',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator', 'networking'],
    text: 'List all IP addresses on the connected appliance with their types (NSIP, SNIP, VIP, etc.).'
  },
  {
    id: 'list-vservers',
    label: 'List load balancing virtual servers',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-sitemap',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator', 'traffic-mgmt'],
    text: 'List all load balancing virtual servers on the connected appliance, including VIP, port, state, and service bindings.'
  },
  {
    id: 'list-apps',
    label: 'List Next-Gen applications',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-th-large',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator'],
    text: 'List all Next-Gen API applications configured on the connected appliance.'
  },
  // Networking — channels, VLANs, routes, SNIP, PBR, HA
  {
    id: 'op-channel-lacp',
    label: 'Configure link channel (LACP)',
    subtitle: 'Operator · Networking',
    icon: 'pi pi-link',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'configure', 'operator'],
    text:
      'I need to configure an LACP link channel on the connected appliance for data interfaces. Ask missing details with a jpilot-form, search CLI reference, then apply and save ns config.'
  },
  {
    id: 'op-vlan-bind',
    label: 'Add VLAN and bind to interface',
    subtitle: 'Operator · Networking',
    icon: 'pi pi-share-alt',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'configure', 'operator'],
    text:
      'Add a VLAN and bind it to the correct interface/channel on the connected appliance. Use a form for VLAN ID, interface, and tagging, then configure via CLI.'
  },
  {
    id: 'op-route-pbr',
    label: 'Static route or policy-based route (PBR)',
    subtitle: 'Operator · Networking',
    icon: 'pi pi-directions-alt',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'configure', 'operator'],
    text:
      'Configure a static route or PBR on the connected appliance (e.g. management traffic isolation). Gather network/mask/gateway via jpilot-form, then apply routes and save config.'
  },
  {
    id: 'op-snip-vip',
    label: 'Add SNIP or VIP',
    subtitle: 'Operator · Networking',
    icon: 'pi pi-plus-circle',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'configure', 'operator'],
    text: 'Add a new SNIP or VIP on the connected appliance. Ask for IP, netmask, and VLAN/type with a form, then configure it.'
  },
  {
    id: 'op-ha-pair',
    label: 'Configure HA pair (nodes & heartbeat)',
    subtitle: 'Operator · Networking · HA',
    icon: 'pi pi-clone',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'configure', 'operator', 'guided'],
    text:
      'Configure high availability on the connected appliance: peer IP, heartbeat interfaces, and failover mode. Use jpilot-form for missing values, then apply HA settings and verify with show ha node.'
  },
  {
    id: 'ping-google',
    label: 'Ping test from appliance',
    subtitle: 'Operator · Networking · Diagnostics',
    icon: 'pi pi-wifi',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'discover', 'operator'],
    text: 'Can the connected NetScaler ping 8.8.8.8? Run netscaler_run_diagnostic and report the result.'
  },
  {
    id: 'port-check',
    label: 'TCP port check to a host',
    subtitle: 'Operator · Networking · Diagnostics',
    icon: 'pi pi-search',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'discover', 'operator'],
    text: 'From the connected appliance, check whether TCP port 443 is open on a target host I specify. Use telnet or tcp_port diagnostic.'
  },
  {
    id: 'op-enable-l2-l3',
    label: 'Enable L2/L3 mode as required',
    subtitle: 'Operator · Networking',
    icon: 'pi pi-cog',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'configure', 'operator'],
    text: 'Review and enable required L2/L3 modes on the connected appliance for my VLAN design. Use show mode, then set mode if needed and save config.'
  },
  {
    id: 'op-interface-speed',
    label: 'Set interface speed & duplex',
    subtitle: 'Operator · Networking',
    icon: 'pi pi-sliders-v',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'configure', 'operator'],
    text: 'Configure interface speed and duplex on a specified interface on the connected appliance. Form for interface ID and settings, then apply.'
  },
  {
    id: 'op-add-nsip',
    label: 'Add or change NSIP',
    subtitle: 'Operator · Networking',
    icon: 'pi pi-home',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'configure', 'operator', 'guided'],
    text: 'Add or update the NSIP on the connected appliance. Use jpilot-form for IP and netmask, confirm HA impact, then apply.'
  },
  {
    id: 'op-default-gateway',
    label: 'Configure default gateway',
    subtitle: 'Operator · Networking',
    icon: 'pi pi-directions',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'configure', 'operator'],
    text: 'Set or update the default gateway on the connected appliance for a given traffic domain. Form for gateway IP, then CLI.'
  },
  {
    id: 'op-arp-freeze',
    label: 'Gratuitous ARP / VIP movement',
    subtitle: 'Operator · Networking',
    icon: 'pi pi-refresh',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'configure', 'operator'],
    text: 'After VIP changes on the connected appliance, ensure ARP propagation (enable arp on VIP or run appropriate commands). Explain steps and execute.'
  },
  {
    id: 'op-traceroute',
    label: 'Traceroute from appliance',
    subtitle: 'Operator · Networking',
    icon: 'pi pi-share-alt',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'discover', 'operator'],
    text: 'Run traceroute from the connected appliance to a target I specify and summarize hops and latency.'
  },
  {
    id: 'op-show-vlan',
    label: 'Show VLAN and interface bindings',
    subtitle: 'Operator · Networking · Discover',
    icon: 'pi pi-list',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'discover', 'operator'],
    text: 'Show all VLANs, interfaces, and channel bindings on the connected appliance in a concise table.'
  },
  {
    id: 'op-show-route',
    label: 'Show routes and PBR policies',
    subtitle: 'Operator · Networking · Discover',
    icon: 'pi pi-map',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'discover', 'operator'],
    text: 'Show static routes and policy-based routes on the connected appliance.'
  },
  {
    id: 'op-ha-force-failover',
    label: 'Force HA failover (maintenance)',
    subtitle: 'Operator · Networking · HA',
    icon: 'pi pi-clone',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'configure', 'operator'],
    text: 'Guide forced HA failover on the connected HA pair for maintenance. Confirm with me, then run appropriate ha commands and verify state.'
  },
  {
    id: 'op-snmp-trap',
    label: 'Configure SNMP trap destination',
    subtitle: 'Operator · Networking · Monitoring',
    icon: 'pi pi-bell',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'configure', 'operator'],
    text: 'Configure SNMP trap or manager targets on the connected appliance. Form for manager IP/community, then apply.'
  },
  {
    id: 'op-syslog-export',
    label: 'Configure remote syslog',
    subtitle: 'Operator · Networking · Monitoring',
    icon: 'pi pi-file-export',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'configure', 'operator'],
    text: 'Add remote syslog server on the connected appliance for audit and event export. Form for server IP/port, then CLI.'
  },
  // Traffic management — LB, CS, GSLB, monitors, persistence
  {
    id: 'lb-vserver',
    label: 'Create LB vserver (guided)',
    subtitle: 'Operator · Traffic management',
    icon: 'pi pi-sliders-h',
    type: 'prompt',
    role: 'operator',
    tags: ['traffic-mgmt', 'configure', 'operator', 'guided'],
    text: 'Create a new HTTP/HTTPS load balancing vserver on the connected appliance. Use a jpilot-form for VIP, port, backends, and monitor, then configure and save.'
  },
  {
    id: 'op-cs-vserver',
    label: 'Content switching vserver & policy',
    subtitle: 'Operator · Traffic management',
    icon: 'pi pi-filter',
    type: 'prompt',
    role: 'operator',
    tags: ['traffic-mgmt', 'configure', 'operator', 'guided'],
    text:
      'Configure a content switching vserver and policy to route by hostname or URL path on the connected appliance. Form for rules and targets, then CLI/API execution.'
  },
  {
    id: 'op-gslb-site',
    label: 'GSLB site & service (basic)',
    subtitle: 'Operator · Traffic management',
    icon: 'pi pi-globe',
    type: 'prompt',
    role: 'operator',
    tags: ['traffic-mgmt', 'configure', 'operator', 'guided'],
    text:
      'Configure basic GSLB on the connected appliance: local site, GSLB service linked to an LB vserver, and ADNS. Use a form for site IPs and DNS names, then apply per official GSLB setup.'
  },
  {
    id: 'op-monitor-service',
    label: 'Bind health monitor to service',
    subtitle: 'Operator · Traffic management',
    icon: 'pi pi-heart',
    type: 'prompt',
    role: 'operator',
    tags: ['traffic-mgmt', 'configure', 'operator'],
    text:
      'Add or change a health monitor on a service or service group on the connected appliance. Ask for monitor type and bindings via form if needed, then apply.'
  },
  {
    id: 'op-responder-https',
    label: 'HTTP→HTTPS responder policy',
    subtitle: 'Operator · Traffic management',
    icon: 'pi pi-arrow-right',
    type: 'prompt',
    role: 'operator',
    tags: ['traffic-mgmt', 'configure', 'operator'],
    text:
      'Create a responder policy to redirect HTTP to HTTPS on a named LB vserver on the connected appliance. Confirm vserver name with a form if missing, then bind policy.'
  },
  {
    id: 'storefront-lb',
    label: 'Implement StoreFront HTTPS LB',
    subtitle: 'Operator · Citrix StoreFront',
    icon: 'pi pi-desktop',
    type: 'prompt',
    role: 'operator',
    tags: ['citrix-delivery', 'traffic-mgmt', 'configure', 'operator', 'guided'],
    text:
      'Configure HTTPS load balancing for Citrix StoreFront on the connected appliance (SSL vserver, backends, tcp-default/http monitors). Use jpilot-form for VIP, servers, and cert binding.'
  },
  {
    id: 'op-ddc-lb',
    label: 'Implement Delivery Controller LB',
    subtitle: 'Operator · Citrix DDC',
    icon: 'pi pi-server',
    type: 'prompt',
    role: 'operator',
    tags: ['citrix-delivery', 'traffic-mgmt', 'configure', 'operator', 'guided'],
    text:
      'Configure load balancing for Citrix Delivery Controllers on the connected appliance. Form for controller IPs, ports, SSL, and LB method, then create vserver and services.'
  },
  {
    id: 'op-gateway-cvad',
    label: 'Citrix Gateway VPN vserver (CVAD)',
    subtitle: 'Operator · Citrix Gateway',
    icon: 'pi pi-sign-in',
    type: 'prompt',
    role: 'operator',
    tags: ['citrix-delivery', 'configure', 'operator', 'guided', 'security'],
    text:
      'Configure a Citrix Gateway virtual server on the connected appliance for CVAD access (SSL VPN, authentication profile, session policies). Gather requirements via jpilot-form before changes.'
  },
  {
    id: 'op-service-group',
    label: 'Create service group & members',
    subtitle: 'Operator · Traffic management',
    icon: 'pi pi-users',
    type: 'prompt',
    role: 'operator',
    tags: ['traffic-mgmt', 'configure', 'operator', 'guided'],
    text: 'Create a service group and add backend servers on the connected appliance. Use jpilot-form for names, IPs, ports, then bind to vserver.'
  },
  {
    id: 'op-persistence-profile',
    label: 'Configure persistence profile',
    subtitle: 'Operator · Traffic management',
    icon: 'pi pi-sync',
    type: 'prompt',
    role: 'operator',
    tags: ['traffic-mgmt', 'configure', 'operator', 'guided'],
    text: 'Create and bind a persistence profile (cookie/sourceIP) to an LB vserver on the connected appliance. Form for type and timeout.'
  },
  {
    id: 'op-lb-method',
    label: 'Change LB method on vserver',
    subtitle: 'Operator · Traffic management',
    icon: 'pi pi-sliders-h',
    type: 'prompt',
    role: 'operator',
    tags: ['traffic-mgmt', 'configure', 'operator'],
    text: 'Change load balancing method on a named vserver on the connected appliance (e.g. LEASTCONNECTION, ROUNDROBIN). Confirm name via form if needed.'
  },
  {
    id: 'op-ssl-bridge',
    label: 'SSL_BRIDGE / SSL offload vserver',
    subtitle: 'Operator · Traffic management',
    icon: 'pi pi-lock',
    type: 'prompt',
    role: 'operator',
    tags: ['traffic-mgmt', 'configure', 'operator', 'guided'],
    text: 'Create SSL or SSL_BRIDGE LB vserver on the connected appliance. Form for VIP, port, backends, cert, then configure.'
  },
  {
    id: 'op-cs-action',
    label: 'Content switching action & policy',
    subtitle: 'Operator · Traffic management',
    icon: 'pi pi-filter',
    type: 'prompt',
    role: 'operator',
    tags: ['traffic-mgmt', 'configure', 'operator'],
    text: 'Create CS action and policy for host/path routing on the connected appliance. Form for match expression and target pool.'
  },
  {
    id: 'op-gslb-mep',
    label: 'Enable GSLB MEP to remote site',
    subtitle: 'Operator · Traffic management',
    icon: 'pi pi-globe',
    type: 'prompt',
    role: 'operator',
    tags: ['traffic-mgmt', 'configure', 'operator', 'guided'],
    text: 'Configure GSLB MEP communication to a remote site on the connected appliance. Form for remote site IP and credentials.'
  },
  {
    id: 'op-adns-bind',
    label: 'Bind ADNS service to IP',
    subtitle: 'Operator · Traffic management',
    icon: 'pi pi-server',
    type: 'prompt',
    role: 'operator',
    tags: ['traffic-mgmt', 'configure', 'operator'],
    text: 'Configure ADNS service on the connected appliance for GSLB DNS answers. Form for listen IP and bind to GSLB vserver.'
  },
  {
    id: 'op-rewrite-insert-header',
    label: 'Insert HTTP header (rewrite)',
    subtitle: 'Operator · Traffic management',
    icon: 'pi pi-pencil',
    type: 'prompt',
    role: 'operator',
    tags: ['traffic-mgmt', 'configure', 'operator'],
    text: 'Add rewrite policy to insert or remove HTTP headers on an LB vserver on the connected appliance.'
  },
  {
    id: 'op-rate-limit-policy',
    label: 'Rate limit policy on vserver',
    subtitle: 'Operator · Traffic management',
    icon: 'pi pi-ban',
    type: 'prompt',
    role: 'operator',
    tags: ['traffic-mgmt', 'configure', 'operator', 'security'],
    text: 'Configure stream selector and responder/rate-limit policy on a vserver on the connected appliance. Form for threshold.'
  },
  {
    id: 'op-disable-vserver',
    label: 'Disable or enable vserver',
    subtitle: 'Operator · Traffic management',
    icon: 'pi pi-power-off',
    type: 'prompt',
    role: 'operator',
    tags: ['traffic-mgmt', 'configure', 'operator'],
    text: 'Disable or enable a named LB vserver on the connected appliance for maintenance. Confirm name and desired state.'
  },
  {
    id: 'op-citrix-ica-monitor',
    label: 'Citrix ICA/custom monitor',
    subtitle: 'Operator · Citrix · Traffic',
    icon: 'pi pi-desktop',
    type: 'prompt',
    role: 'operator',
    tags: ['citrix-delivery', 'traffic-mgmt', 'configure', 'operator'],
    text: 'Configure a Citrix-specific or custom monitor for StoreFront/DDC services on the connected appliance.'
  },
  {
    id: 'op-sta-server',
    label: 'Configure STA server for Gateway',
    subtitle: 'Operator · Citrix Gateway',
    icon: 'pi pi-link',
    type: 'prompt',
    role: 'operator',
    tags: ['citrix-delivery', 'traffic-mgmt', 'configure', 'operator', 'guided'],
    text: 'Bind STA servers to Citrix Gateway on the connected appliance for CVAD. Form for STA URLs and priority.'
  },
  {
    id: 'op-session-profile',
    label: 'Gateway session profile & policy',
    subtitle: 'Operator · Citrix Gateway',
    icon: 'pi pi-sign-in',
    type: 'prompt',
    role: 'operator',
    tags: ['citrix-delivery', 'configure', 'operator', 'guided'],
    text: 'Create or update session profile and policy on Citrix Gateway vserver on the connected appliance.'
  },
  {
    id: 'op-aaa-vserver',
    label: 'Authentication vserver (LDAP)',
    subtitle: 'Operator · Citrix · Security',
    icon: 'pi pi-users',
    type: 'prompt',
    role: 'operator',
    tags: ['citrix-delivery', 'security', 'configure', 'operator', 'guided'],
    text: 'Configure authentication vserver with LDAP policy on the connected appliance for Gateway or AAA traffic.'
  },
  {
    id: 'op-list-cs',
    label: 'List content switching vservers',
    subtitle: 'Operator · Discover · Traffic',
    icon: 'pi pi-list',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'traffic-mgmt', 'operator'],
    text: 'List content switching vservers and policies on the connected appliance.'
  },
  {
    id: 'op-list-gslb',
    label: 'List GSLB configuration',
    subtitle: 'Operator · Discover · Traffic',
    icon: 'pi pi-globe',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'traffic-mgmt', 'operator'],
    text: 'List GSLB sites, services, and vservers on the connected appliance.'
  },
  // Security — SSL, WAF, certs
  {
    id: 'show-certkeys',
    label: 'Show certificate-key pairs',
    subtitle: 'Operator · Security',
    icon: 'pi pi-lock',
    type: 'prompt',
    role: 'operator',
    tags: ['security', 'ssl', 'operator', 'discover'],
    text: 'Show all SSL certificate-key pairs on the connected appliance and expiry dates if available.'
  },
  {
    id: 'op-ssl-bind',
    label: 'Bind SSL cert to vserver',
    subtitle: 'Operator · Security',
    icon: 'pi pi-shield',
    type: 'prompt',
    role: 'operator',
    tags: ['security', 'ssl', 'configure', 'operator', 'guided'],
    text:
      'Bind an existing certificate-key pair to an SSL LB vserver on the connected appliance. Form for cert name and vserver if not specified, then bind and verify.'
  },
  {
    id: 'op-waf-profile',
    label: 'Bind WAF profile to vserver',
    subtitle: 'Operator · Security',
    icon: 'pi pi-exclamation-triangle',
    type: 'prompt',
    role: 'operator',
    tags: ['security', 'configure', 'operator', 'guided'],
    text:
      'Attach or update a Web App Firewall profile on an LB vserver on the connected appliance. Use a form for profile name, vserver, and learning mode, then apply.'
  },
  {
    id: 'ssl-tool',
    label: 'Open SSL certificate tools',
    subtitle: 'Operator · Tools',
    icon: 'pi pi-cog',
    type: 'link',
    role: 'operator',
    tags: ['ssl', 'link', 'operator'],
    to: '/appliances?tab=ssl'
  },
  {
    id: 'self-signed',
    label: 'Generate self-signed cert (UI)',
    subtitle: 'Operator · Tools',
    icon: 'pi pi-key',
    type: 'link',
    role: 'operator',
    tags: ['ssl', 'link', 'operator'],
    to: '/appliances?tab=ssl'
  },
  {
    id: 'op-cipher-group',
    label: 'Create & bind cipher group',
    subtitle: 'Operator · Security',
    icon: 'pi pi-lock',
    type: 'prompt',
    role: 'operator',
    tags: ['security', 'ssl', 'configure', 'operator', 'guided'],
    text: 'Create a cipher group and SSL profile on the connected appliance, bind to an SSL vserver. Form for TLS versions and ciphers.'
  },
  {
    id: 'op-sni-cert',
    label: 'SNI certificate on SSL vserver',
    subtitle: 'Operator · Security',
    icon: 'pi pi-key',
    type: 'prompt',
    role: 'operator',
    tags: ['security', 'ssl', 'configure', 'operator'],
    text: 'Bind additional certificate for SNI hostname on an SSL vserver on the connected appliance.'
  },
  {
    id: 'op-hsts-header',
    label: 'HSTS / security headers (responder)',
    subtitle: 'Operator · Security',
    icon: 'pi pi-shield',
    type: 'prompt',
    role: 'operator',
    tags: ['security', 'configure', 'operator'],
    text: 'Add responder or rewrite policies for HSTS and security headers on a public vserver on the connected appliance.'
  },
  {
    id: 'op-ip-reputation-enable',
    label: 'Enable IP reputation filter',
    subtitle: 'Operator · Security',
    icon: 'pi pi-eye',
    type: 'prompt',
    role: 'operator',
    tags: ['security', 'configure', 'operator'],
    text: 'Enable IP reputation and bind to a vserver on the connected appliance. Confirm scope with a form first.'
  },
  {
    id: 'op-appfw-signatures',
    label: 'Update WAF signatures',
    subtitle: 'Operator · Security',
    icon: 'pi pi-download',
    type: 'prompt',
    role: 'operator',
    tags: ['security', 'configure', 'operator'],
    text: 'Check and update Web App Firewall signatures on the connected appliance; report current version.'
  },
  {
    id: 'op-aaa-policy',
    label: 'AAA traffic policy on vserver',
    subtitle: 'Operator · Security',
    icon: 'pi pi-user',
    type: 'prompt',
    role: 'operator',
    tags: ['security', 'configure', 'operator', 'guided'],
    text: 'Configure AAA policy on an LB vserver for form-based or SSO authentication on the connected appliance.'
  },
  {
    id: 'op-ssl-diag',
    label: 'Diagnose SSL handshake failures',
    subtitle: 'Operator · Security · Discover',
    icon: 'pi pi-search',
    type: 'prompt',
    role: 'operator',
    tags: ['security', 'ssl', 'discover', 'operator'],
    text: 'Troubleshoot SSL handshake or certificate errors on a named vserver on the connected appliance using show ssl and logs.'
  },
  {
    id: 'op-crl-ocsp',
    label: 'Configure CRL/OCSP stapling',
    subtitle: 'Operator · Security',
    icon: 'pi pi-verified',
    type: 'prompt',
    role: 'operator',
    tags: ['security', 'ssl', 'configure', 'operator'],
    text: 'Configure CRL or OCSP stapling for server certificates on the connected appliance.'
  },
  {
    id: 'op-bot-policy',
    label: 'Bot management policy',
    subtitle: 'Operator · Security',
    icon: 'pi pi-android',
    type: 'prompt',
    role: 'operator',
    tags: ['security', 'configure', 'operator'],
    text: 'Enable and bind bot management policy on an internet-facing vserver on the connected appliance.'
  },
  {
    id: 'op-import-cert',
    label: 'Import certificate-key (CLI)',
    subtitle: 'Operator · Security',
    icon: 'pi pi-upload',
    type: 'prompt',
    role: 'operator',
    tags: ['security', 'ssl', 'configure', 'operator'],
    text: 'Guide importing a certificate and private key on the connected appliance when I provide PEM paths or paste content in chat.'
  },
  {
    id: 'op-show-ssl-vserver',
    label: 'Show SSL settings per vserver',
    subtitle: 'Operator · Security · Discover',
    icon: 'pi pi-list',
    type: 'prompt',
    role: 'operator',
    tags: ['security', 'ssl', 'discover', 'operator'],
    text: 'Show SSL protocol, cipher, and cert bindings for a named vserver on the connected appliance.'
  },
  {
    id: 'op-discover-features',
    label: 'Show enabled features & modes',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-check-square',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator'],
    text: 'Show which features and modes are enabled on the connected appliance (LB, SSL, GSLB, WAF, etc.).'
  },
  {
    id: 'op-discover-hw',
    label: 'Show hardware & capacity',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-server',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator'],
    text: 'Show hardware platform, licensed capacity, and SSL chip utilization on the connected appliance.'
  },
  {
    id: 'op-discover-save-config',
    label: 'Show unsaved config diff',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-file',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator'],
    text: 'Show if there is unsaved configuration on the connected appliance and summarize changes since last save ns config.'
  },
  {
    id: 'op-discover-running-config',
    label: 'Export running config summary',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-download',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator'],
    text: 'Summarize key running config objects on the connected appliance: vservers, services, VIPs, and HA state.'
  },
  {
    id: 'op-discover-monitors',
    label: 'List all monitors',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-heart',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator'],
    text: 'List configured monitors and their bindings on the connected appliance.'
  },
  {
    id: 'op-discover-servers',
    label: 'List all servers & services',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-database',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator'],
    text: 'List all servers, services, and service groups on the connected appliance with state.'
  },
  {
    id: 'op-discover-audit-log',
    label: 'Recent audit log entries',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-history',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator'],
    text: 'Show recent audit log or command history on the connected appliance if available.'
  },
  {
    id: 'op-discover-nslog',
    label: 'Tail ns.log errors',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-exclamation-circle',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator'],
    text: 'Check recent errors in ns.log on the connected appliance and summarize critical lines.'
  },
  {
    id: 'op-discover-tech-support',
    label: 'Generate tech support bundle',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-file-export',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator'],
    text: 'Explain how to generate a tech support file on the connected appliance and what to collect before a change window.'
  },
  {
    id: 'op-discover-license',
    label: 'Show license status',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-ticket',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator'],
    text: 'Show license edition, expiration, and enabled features on the connected appliance.'
  },
  {
    id: 'op-discover-aaadb',
    label: 'Show AAA sessions summary',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-users',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator', 'citrix-delivery'],
    text: 'Show summary of AAA/Gateway authentication sessions on the connected appliance.'
  },
  {
    id: 'op-discover-appfw',
    label: 'List WAF profiles & policies',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-shield',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator', 'security'],
    text: 'List Web App Firewall profiles, policies, and bindings on the connected appliance.'
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // Analyst — read-first troubleshooting on connected appliance
  // ═══════════════════════════════════════════════════════════════════════════
  {
    id: 'health-summary',
    label: 'Quick health summary',
    subtitle: 'Analyst · Diagnostics',
    icon: 'pi pi-heart',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'discover'],
    text: 'Quick health summary of the connected appliance: version, HA state, IP summary, LB vserver count, and obvious issues.'
  },
  {
    id: 'cpu-mem',
    label: 'CPU and memory usage',
    subtitle: 'Analyst · Diagnostics',
    icon: 'pi pi-chart-bar',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst'],
    text: 'Collect current CPU and memory statistics from the connected appliance.'
  },
  {
    id: 'lb-stats',
    label: 'LB vserver statistics',
    subtitle: 'Analyst · Traffic management',
    icon: 'pi pi-chart-line',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'traffic-mgmt'],
    text: 'Show load balancing statistics and hit counts for virtual servers on the connected appliance; flag DOWN or zero-hit vservers.'
  },
  {
    id: 'an-ha-state',
    label: 'HA node and failover status',
    subtitle: 'Analyst · Networking',
    icon: 'pi pi-clone',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'networking'],
    text: 'Show HA node status, sync state, and last failover events on the connected appliance (read-only).'
  },
  {
    id: 'an-vlan-ip-audit',
    label: 'Audit VLANs, channels, and IPs',
    subtitle: 'Analyst · Networking',
    icon: 'pi pi-map',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'networking'],
    text: 'Audit VLAN bindings, link channels, NSIP/SNIP/VIP layout, and static routes on the connected appliance. Summarize misconfigurations or gaps.'
  },
  {
    id: 'an-connectivity',
    label: 'Connectivity test to backend',
    subtitle: 'Analyst · Networking',
    icon: 'pi pi-wifi',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'networking'],
    text: 'Run ping or TCP port diagnostics from the connected appliance to a backend host and port I provide. Report reachability only.'
  },
  {
    id: 'an-gslb-status',
    label: 'GSLB site and service status',
    subtitle: 'Analyst · Traffic management',
    icon: 'pi pi-globe',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'traffic-mgmt'],
    text: 'Show GSLB sites, services, and vserver state on the connected appliance. Note any DOWN or mismatch with DNS expectations.'
  },
  {
    id: 'an-service-down',
    label: 'Why is a service or vserver DOWN?',
    subtitle: 'Analyst · Traffic management',
    icon: 'pi pi-question-circle',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'traffic-mgmt', 'citrix-delivery'],
    text:
      'A load balancing vserver or service is DOWN on the connected appliance. Gather show/stat evidence, monitor results, and likely causes — read-only, no config changes.'
  },
  {
    id: 'an-ssl-expiry',
    label: 'SSL certificate expiry check',
    subtitle: 'Analyst · Security',
    icon: 'pi pi-lock',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'security'],
    text: 'List SSL certificate-key pairs on the connected appliance and highlight any nearing expiry or missing bindings on public vservers.'
  },
  {
    id: 'an-waf-hits',
    label: 'WAF / security check summary',
    subtitle: 'Analyst · Security',
    icon: 'pi pi-shield',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'security'],
    text: 'Summarize Web App Firewall profiles, bindings, and recent deny/learn stats on the connected appliance if available (read-only).'
  },
  {
    id: 'an-storefront-lb',
    label: 'StoreFront LB health check',
    subtitle: 'Analyst · Citrix StoreFront',
    icon: 'pi pi-desktop',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'citrix-delivery', 'traffic-mgmt'],
    text:
      'Review StoreFront-related LB vservers, monitors, and SSL bindings on the connected appliance. Report state and common misconfiguration patterns.'
  },
  {
    id: 'an-gateway-sessions',
    label: 'Citrix Gateway session overview',
    subtitle: 'Analyst · Citrix Gateway',
    icon: 'pi pi-sign-in',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'citrix-delivery'],
    text:
      'Show Citrix Gateway vserver status and active session summary on the connected appliance (read-only show/stat commands).'
  },
  {
    id: 'an-nsconmsg-events',
    label: 'Recent events and errors (nsconmsg)',
    subtitle: 'Analyst · Diagnostics',
    icon: 'pi pi-list',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst'],
    text: 'Collect recent console events and errors from the connected appliance using nsconmsg and summarize actionable findings.'
  },
  {
    id: 'an-disk-space',
    label: 'Disk and var partition usage',
    subtitle: 'Analyst · Diagnostics',
    icon: 'pi pi-database',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst'],
    text: 'Check disk usage under /var and flash on the connected appliance and flag if logs need rotation.'
  },
  {
    id: 'an-throughput',
    label: 'Throughput & connection rates',
    subtitle: 'Analyst · Diagnostics',
    icon: 'pi pi-chart-bar',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'traffic-mgmt'],
    text: 'Report current throughput and concurrent connection counts on the connected appliance.'
  },
  {
    id: 'an-monitor-failures',
    label: 'Failed monitors in last hour',
    subtitle: 'Analyst · Traffic management',
    icon: 'pi pi-heart',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'traffic-mgmt'],
    text: 'List monitors in FAILED state and affected services/vservers on the connected appliance.'
  },
  {
    id: 'an-persistence-table',
    label: 'Persistence session table',
    subtitle: 'Analyst · Traffic management',
    icon: 'pi pi-sync',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'traffic-mgmt'],
    text: 'Summarize persistence sessions and any overflow or misbinding on the connected appliance.'
  },
  {
    id: 'an-cs-hit',
    label: 'Content switching policy hits',
    subtitle: 'Analyst · Traffic management',
    icon: 'pi pi-filter',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'traffic-mgmt'],
    text: 'Show CS policy hit counts and default-action drops on the connected appliance.'
  },
  {
    id: 'an-gslb-dns',
    label: 'GSLB DNS resolution test',
    subtitle: 'Analyst · Traffic management',
    icon: 'pi pi-globe',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'traffic-mgmt'],
    text: 'Verify GSLB DNS answers from the connected appliance for a test FQDN I provide (read-only).'
  },
  {
    id: 'an-traceroute-backend',
    label: 'Traceroute to backend pool',
    subtitle: 'Analyst · Networking',
    icon: 'pi pi-share-alt',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'networking'],
    text: 'Traceroute from the connected appliance to backend servers and note asymmetric routing.'
  },
  {
    id: 'an-interface-errors',
    label: 'Interface error counters',
    subtitle: 'Analyst · Networking',
    icon: 'pi pi-wifi',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'networking'],
    text: 'Show interface error/drop counters on the connected appliance and flag anomalies.'
  },
  {
    id: 'an-ssl-vserver-bind',
    label: 'SSL binding audit per vserver',
    subtitle: 'Analyst · Security',
    icon: 'pi pi-lock',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'security'],
    text: 'Audit SSL cert bindings and protocol versions on all public vservers on the connected appliance.'
  },
  {
    id: 'an-cipher-mismatch',
    label: 'Cipher mismatch investigation',
    subtitle: 'Analyst · Security',
    icon: 'pi pi-search',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'security'],
    text: 'Investigate client cipher mismatch errors on a named SSL vserver on the connected appliance (read-only).'
  },
  {
    id: 'an-ddc-lb-health',
    label: 'Delivery Controller LB health',
    subtitle: 'Analyst · Citrix DDC',
    icon: 'pi pi-server',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'citrix-delivery', 'traffic-mgmt'],
    text: 'Check LB vservers and monitors for Delivery Controllers on the connected appliance.'
  },
  {
    id: 'an-ica-latency',
    label: 'ICA/HDX session quality clues',
    subtitle: 'Analyst · Citrix',
    icon: 'pi pi-desktop',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'citrix-delivery'],
    text: 'Gather stats and logs relevant to ICA/HDX user slowness on the connected Gateway or STA path (read-only).'
  },
  {
    id: 'an-config-diff',
    label: 'Compare running vs saved config',
    subtitle: 'Analyst · Diagnostics',
    icon: 'pi pi-file',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'discover'],
    text: 'Determine if unsaved changes exist on the connected appliance and summarize risk before reboot.'
  },
  {
    id: 'an-surge-queue',
    label: 'Surge queue & protection stats',
    subtitle: 'Analyst · Traffic management',
    icon: 'pi pi-chart-line',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'traffic-mgmt'],
    text: 'Report surge queue depth and rate-limit drops on vservers on the connected appliance.'
  },
  {
    id: 'an-appfw-blocks',
    label: 'Recent WAF blocks/denies',
    subtitle: 'Analyst · Security',
    icon: 'pi pi-ban',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'security'],
    text: 'Summarize recent Web App Firewall deny events on the connected appliance for a vserver I name.'
  },
  {
    id: 'an-route-table',
    label: 'Routing table review',
    subtitle: 'Analyst · Networking',
    icon: 'pi pi-map',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'networking'],
    text: 'Show routing table and point out missing or duplicate routes on the connected appliance.'
  },
  {
    id: 'an-pbr-hit',
    label: 'PBR policy hit counts',
    subtitle: 'Analyst · Networking',
    icon: 'pi pi-directions',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'networking'],
    text: 'Show PBR policy statistics and which traffic hits management isolation rules on the connected appliance.'
  },
  {
    id: 'an-channel-ha',
    label: 'Channel HA state',
    subtitle: 'Analyst · Networking',
    icon: 'pi pi-link',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'networking'],
    text: 'Verify LACP/channel HA state and member interface status on the connected appliance.'
  },
  {
    id: 'an-arp-table',
    label: 'ARP table anomalies',
    subtitle: 'Analyst · Networking',
    icon: 'pi pi-search',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'networking'],
    text: 'Inspect ARP table on the connected appliance for duplicate or stale VIP entries.'
  },
  {
    id: 'an-udp-443',
    label: 'UDP 443 / EDT port reachability',
    subtitle: 'Analyst · Networking · Citrix',
    icon: 'pi pi-wifi',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'networking', 'citrix-delivery'],
    text: 'Test UDP/TCP ports needed for EDT/ICA from the connected appliance to a target I specify.'
  },
  {
    id: 'an-snip-reach',
    label: 'SNIP-to-backend reachability',
    subtitle: 'Analyst · Networking',
    icon: 'pi pi-share-alt',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'networking'],
    text: 'Verify SNIP can reach backend subnets for a service on the connected appliance (ping/port checks).'
  },
  {
    id: 'an-vlan-mismatch',
    label: 'VLAN tagging mismatch check',
    subtitle: 'Analyst · Networking',
    icon: 'pi pi-exclamation-triangle',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'networking'],
    text: 'Check for VLAN/interface tagging mismatches that could cause asymmetric routing on the connected appliance.'
  },
  {
    id: 'an-dns-gslb',
    label: 'DNS resolution via ADNS',
    subtitle: 'Analyst · Networking',
    icon: 'pi pi-globe',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'networking', 'traffic-mgmt'],
    text: 'Test internal DNS resolution for GSLB ADNS on the connected appliance for a record I provide.'
  },
  {
    id: 'an-mgmt-access',
    label: 'Management path isolation check',
    subtitle: 'Analyst · Networking',
    icon: 'pi pi-shield',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'networking', 'security'],
    text: 'Verify management traffic uses expected PBR/path and not production default route on the connected appliance.'
  },
  {
    id: 'an-ssl-protocol',
    label: 'SSL protocol version audit',
    subtitle: 'Analyst · Security',
    icon: 'pi pi-lock',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'security'],
    text: 'Audit enabled SSL/TLS protocol versions on all SSL vservers on the connected appliance; flag weak versions.'
  },
  {
    id: 'an-cert-chain',
    label: 'Certificate chain validation',
    subtitle: 'Analyst · Security',
    icon: 'pi pi-verified',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'security'],
    text: 'Validate certificate chains and intermediate trust on the connected appliance for a named cert.'
  },
  {
    id: 'an-responder-policy',
    label: 'Responder/rewrite policy audit',
    subtitle: 'Analyst · Security',
    icon: 'pi pi-filter',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'security', 'traffic-mgmt'],
    text: 'List responder and rewrite policies bound to public vservers on the connected appliance.'
  },
  {
    id: 'an-ip-reputation-hits',
    label: 'IP reputation block summary',
    subtitle: 'Analyst · Security',
    icon: 'pi pi-ban',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'security'],
    text: 'Summarize IP reputation blocks on the connected appliance in the last interval if stats exist.'
  },
  {
    id: 'an-login-fail-aaa',
    label: 'AAA login failure analysis',
    subtitle: 'Analyst · Security',
    icon: 'pi pi-user',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'security', 'citrix-delivery'],
    text: 'Analyze recent AAA/Gateway login failures on the connected appliance from logs (read-only).'
  },
  {
    id: 'an-citrix-broker',
    label: 'Broker/XML connectivity check',
    subtitle: 'Analyst · Citrix DDC',
    icon: 'pi pi-server',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'citrix-delivery'],
    text: 'Check connectivity and monitor state for Delivery Controller/LB paths on the connected appliance.'
  },
  {
    id: 'an-citrix-sta',
    label: 'STA reachability from Gateway',
    subtitle: 'Analyst · Citrix Gateway',
    icon: 'pi pi-link',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'citrix-delivery'],
    text: 'Verify STA server reachability and bindings for Citrix Gateway on the connected appliance.'
  },
  {
    id: 'an-citrix-receiver',
    label: 'StoreFront / Receiver path check',
    subtitle: 'Analyst · StoreFront',
    icon: 'pi pi-desktop',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'citrix-delivery', 'traffic-mgmt'],
    text: 'Trace StoreFront base URL/LB path health: vserver, certs, monitors on the connected appliance.'
  },
  {
    id: 'an-citrix-gslb-storefront',
    label: 'GSLB for StoreFront FQDN',
    subtitle: 'Analyst · Citrix & GSLB',
    icon: 'pi pi-globe',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'citrix-delivery', 'traffic-mgmt'],
    text: 'Verify GSLB DNS and site selection for a StoreFront FQDN on the connected appliance.'
  },
  {
    id: 'an-citrix-profile',
    label: 'Session profile mismatch',
    subtitle: 'Analyst · Citrix Gateway',
    icon: 'pi pi-cog',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'citrix-delivery'],
    text: 'Review Gateway session profiles/policies for conflicts on the connected appliance (read-only).'
  },
  {
    id: 'an-net-mtu',
    label: 'Path MTU discovery issue',
    subtitle: 'Analyst · Networking',
    icon: 'pi pi-arrows-v',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'networking'],
    text: 'Investigate possible MTU/black-hole issues on a path from the connected appliance (ping with DF, trace).'
  },
  {
    id: 'an-sec-crl-expiry',
    label: 'CRL/OCSP responder health',
    subtitle: 'Analyst · Security',
    icon: 'pi pi-verified',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'security'],
    text: 'Check CRL/OCSP responder reachability and stapling status on the connected appliance.'
  },
  {
    id: 'an-sec-weak-cipher',
    label: 'Weak cipher detection',
    subtitle: 'Analyst · Security',
    icon: 'pi pi-ban',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'security'],
    text: 'List vservers still allowing legacy ciphers on the connected appliance.'
  },
  {
    id: 'an-sec-unbound-cert',
    label: 'VIP without SSL cert binding',
    subtitle: 'Analyst · Security',
    icon: 'pi pi-exclamation-circle',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'security'],
    text: 'Find SSL vservers missing certificate bindings on the connected appliance.'
  },
  {
    id: 'an-sec-sni-gap',
    label: 'SNI hostname coverage gaps',
    subtitle: 'Analyst · Security',
    icon: 'pi pi-key',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'security'],
    text: 'Audit SNI certificates vs required hostnames on the connected appliance.'
  },
  {
    id: 'an-ctx-failover-broker',
    label: 'Broker failover during outage',
    subtitle: 'Analyst · Citrix',
    icon: 'pi pi-server',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'citrix-delivery'],
    text: 'During DDC outage simulation planning, show which LB monitors would fail on the connected appliance.'
  },
  {
    id: 'an-ctx-license',
    label: 'Citrix licensing connectivity',
    subtitle: 'Analyst · Citrix',
    icon: 'pi pi-ticket',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'citrix-delivery'],
    text: 'Check network paths from ADC to Citrix licensing/cloud connectors relevant to Gateway/StoreFront (read-only).'
  },
  {
    id: 'an-ctx-duplicate-vip',
    label: 'Duplicate VIP / IP conflict',
    subtitle: 'Analyst · Citrix · Network',
    icon: 'pi pi-copy',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst', 'citrix-delivery', 'networking'],
    text: 'Detect duplicate VIPs or IP conflicts affecting Citrix workloads on the connected appliance.'
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // SDX — SVM platform (SSH) — 15 actions (+ arch-sdx-multi-tenant above)
  // ═══════════════════════════════════════════════════════════════════════════
  {
    id: 'sdx-arch-capacity-plan',
    label: 'SDX capacity & growth plan',
    subtitle: 'Architect · Platform',
    icon: 'pi pi-chart-bar',
    type: 'prompt',
    role: 'architect',
    tags: ['network', 'ha-dr', 'architect'],
    vendors: ['sdx'],
    text:
      'Plan SDX platform capacity for additional VPX tenants: channel bandwidth, CPU/memory/disk headroom, and management network. Discovery forms, then sizing tables and rollout phases.'
  },
  {
    id: 'sdx-arch-firmware-rollout',
    label: 'SVM & VPX firmware rollout plan',
    subtitle: 'Architect · Operations',
    icon: 'pi pi-upload',
    type: 'prompt',
    role: 'architect',
    tags: ['common', 'architect'],
    vendors: ['sdx'],
    text:
      'Design a controlled firmware upgrade plan for the SDX SVM and hosted VPX instances: prerequisites, maintenance windows, rollback, and verification checklist.'
  },
  {
    id: 'sdx-op-platform-summary',
    label: 'SDX platform summary',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-server',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator'],
    vendors: ['sdx'],
    text:
      'On the connected SDX, show platform summary: firmware, hostname, channel usage, and VPX instance count (read-only show commands).'
  },
  {
    id: 'sdx-op-list-vpx',
    label: 'List VPX instances',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-table',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator'],
    vendors: ['sdx'],
    text: 'List all VPX instances on the connected SDX with state, allocated resources, and management IPs.'
  },
  {
    id: 'sdx-op-firmware-inventory',
    label: 'Firmware package inventory',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-box',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator'],
    vendors: ['sdx'],
    text:
      'Show installed and available firmware packages on the connected SDX SVM (read-only). Note versions in use by each VPX.'
  },
  {
    id: 'sdx-op-channel-plan',
    label: 'Review channel allocation',
    subtitle: 'Operator · Networking',
    icon: 'pi pi-sitemap',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'operator'],
    vendors: ['sdx'],
    text:
      'Review 10G/40G channel allocation on the connected SDX: which interfaces are assigned to which VPX tenants and what capacity remains.'
  },
  {
    id: 'sdx-op-lacp-channels',
    label: 'LACP channels & interfaces',
    subtitle: 'Operator · Networking',
    icon: 'pi pi-link',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'operator'],
    vendors: ['sdx'],
    text:
      'Show LACP channels and physical interface bindings on the connected SDX. Summarize member state and any down links (read-only).'
  },
  {
    id: 'sdx-op-svm-vlans',
    label: 'SVM VLAN assignments',
    subtitle: 'Operator · Networking',
    icon: 'pi pi-map',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'operator'],
    vendors: ['sdx'],
    text:
      'List VLANs configured on the connected SDX management platform and which VPX instances use each segment (read-only show vlan).'
  },
  {
    id: 'sdx-op-capacity-headroom',
    label: 'Platform resource headroom',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-gauge',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator'],
    vendors: ['sdx'],
    text:
      'Report CPU, memory, and disk utilization on the connected SDX SVM and whether resources remain for another VPX (read-only show cpu/memory/disk).'
  },
  {
    id: 'sdx-op-vpx-maintenance-precheck',
    label: 'VPX maintenance pre-check',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-wrench',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator'],
    vendors: ['sdx'],
    text:
      'Before restarting a named VPX on the connected SDX, gather read-only state: HA role, sync, active sessions impact summary, and peer VPX status.'
  },
  {
    id: 'sdx-an-vpx-health',
    label: 'VPX instance health check',
    subtitle: 'Analyst · Diagnostics',
    icon: 'pi pi-heart',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst'],
    vendors: ['sdx'],
    text:
      'Check health of each VPX on the connected SDX: power state, HA sync indicators, and recent platform alarms (read-only).'
  },
  {
    id: 'sdx-an-mgmt-connectivity',
    label: 'SVM management connectivity',
    subtitle: 'Analyst · Networking',
    icon: 'pi pi-wifi',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'networking', 'analyst'],
    vendors: ['sdx'],
    text:
      'Verify management network reachability from the SDX SVM: routes, DNS, and NTP status without changing configuration.'
  },
  {
    id: 'sdx-an-alarm-audit',
    label: 'Platform alarm audit',
    subtitle: 'Analyst · Diagnostics',
    icon: 'pi pi-bell',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst'],
    vendors: ['sdx'],
    text:
      'Review recent SDX platform alarms and VPX lifecycle events on the connected appliance. Group by severity and recommend next steps (read-only).'
  },
  {
    id: 'sdx-an-vpx-resource-imbalance',
    label: 'VPX resource imbalance',
    subtitle: 'Analyst · Diagnostics',
    icon: 'pi pi-exclamation-triangle',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst'],
    vendors: ['sdx'],
    text:
      'Compare CPU/memory allocation across VPX instances on the connected SDX. Flag tenants over-provisioned or starved (read-only).'
  },
  // ═══════════════════════════════════════════════════════════════════════════
  // Cisco IOS/XE (SSH) — Architect + Operator + Analyst
  // ═══════════════════════════════════════════════════════════════════════════
  {
    id: 'cisco-arch-ios-upgrade',
    label: 'IOS / IOS-XE upgrade plan',
    subtitle: 'Architect · Lifecycle',
    icon: 'pi pi-upload',
    type: 'prompt',
    role: 'architect',
    tags: ['common', 'architect'],
    vendors: ['cisco'],
    text:
      'Design a safe Cisco IOS or IOS-XE upgrade for campus switches: image selection, pre-checks (boot variable, disk space, config backup), maintenance window, reload order, and rollback. Use jpilot-form discovery, then a step-by-step design document with verification commands.'
  },
  {
    id: 'cisco-arch-campus-design',
    label: 'Campus switching design (access / dist / core)',
    subtitle: 'Architect · Network',
    icon: 'pi pi-sitemap',
    type: 'prompt',
    role: 'architect',
    tags: ['network', 'common', 'architect'],
    vendors: ['cisco'],
    text:
      'Design a three-tier campus LAN: access, distribution, and core roles, uplink speeds, and where routing terminates. Discovery questions on site size and PoE needs, then topology diagram description and device placement table.'
  },
  {
    id: 'cisco-arch-vlan-design',
    label: 'VLAN & segmentation plan',
    subtitle: 'Architect · Network',
    icon: 'pi pi-table',
    type: 'prompt',
    role: 'architect',
    tags: ['network', 'security', 'architect'],
    vendors: ['cisco'],
    text:
      'Design VLAN IDs, names, and IP subnets for users, servers, management, and voice. Document which switches carry which VLANs, trunk allowed lists, and pruning strategy.'
  },
  {
    id: 'cisco-arch-l3-svi',
    label: 'L3 switching & SVI design',
    subtitle: 'Architect · Network',
    icon: 'pi pi-map',
    type: 'prompt',
    role: 'architect',
    tags: ['network', 'architect'],
    vendors: ['cisco'],
    text:
      'Design inter-VLAN routing on Cisco L3 switches: SVI IPs, default gateway placement, static routes or routing protocol choice, and DHCP helper addresses where needed.'
  },
  {
    id: 'cisco-arch-stp-design',
    label: 'Spanning tree (RSTP) design',
    subtitle: 'Architect · Network',
    icon: 'pi pi-share-alt',
    type: 'prompt',
    role: 'architect',
    tags: ['network', 'ha-dr', 'architect'],
    vendors: ['cisco'],
    text:
      'Design spanning-tree for a Cisco campus: root bridge placement, portfast/bpduguard on access ports, uplink port types, and MST vs RSTP choice. Include failure scenarios in the design doc.'
  },
  {
    id: 'cisco-arch-port-channel',
    label: 'Port-channel & LACP design',
    subtitle: 'Architect · Network',
    icon: 'pi pi-clone',
    type: 'prompt',
    role: 'architect',
    tags: ['network', 'ha-dr', 'architect'],
    vendors: ['cisco'],
    text:
      'Design port-channels between access and distribution switches: LACP mode, load-balancing, member interfaces, and misconfiguration safeguards. Tables per switch pair.'
  },
  {
    id: 'cisco-arch-access-standards',
    label: 'Access port standards',
    subtitle: 'Architect · Operations',
    icon: 'pi pi-cog',
    type: 'prompt',
    role: 'architect',
    tags: ['common', 'network', 'architect'],
    vendors: ['cisco'],
    text:
      'Define a standard Cisco access-port template: description convention, access VLAN, voice VLAN optional, portfast, storm control, and err-disable recovery. Deliver as a design appendix for Operator handoff.'
  },
  {
    id: 'cisco-arch-mgmt-security',
    label: 'Management plane hardening',
    subtitle: 'Architect · Security',
    icon: 'pi pi-shield',
    type: 'prompt',
    role: 'architect',
    tags: ['security', 'network', 'architect'],
    vendors: ['cisco'],
    text:
      'Design management security for Cisco switches: SSH version, VTY ACLs, dedicated management VLAN or VRF, SNMP read-only community restrictions, and AAA (TACACS+/RADIUS) integration outline.'
  },
  {
    id: 'cisco-arch-first-hop-redundancy',
    label: 'HSRP / VRRP gateway redundancy',
    subtitle: 'Architect · HA',
    icon: 'pi pi-clone',
    type: 'prompt',
    role: 'architect',
    tags: ['ha-dr', 'network', 'architect'],
    vendors: ['cisco'],
    text:
      'Design first-hop redundancy (HSRP or VRRP) on Cisco distribution switches: virtual IP, priority/preempt, tracking, and alignment with spanning-tree root. Document failover behavior.'
  },
  {
    id: 'cisco-arch-qos-basics',
    label: 'Basic QoS & trust boundary',
    subtitle: 'Architect · Network',
    icon: 'pi pi-sliders-h',
    type: 'prompt',
    role: 'architect',
    tags: ['network', 'common', 'architect'],
    vendors: ['cisco'],
    text:
      'Design basic QoS on Cisco IOS/XE for voice and business traffic: trust boundary on access ports, marking on uplinks, and queueing policy outline suitable for a small campus.'
  },
  {
    id: 'cisco-op-version',
    label: 'IOS version and uptime',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-info-circle',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator'],
    vendors: ['cisco'],
    text:
      'On the connected switch, run read-only show commands for IOS/XE version, hostname, uptime, and serial number. Summarize in a table.'
  },
  {
    id: 'cisco-op-interfaces',
    label: 'Interface status summary',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-link',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'networking', 'operator'],
    vendors: ['cisco'],
    text:
      'List interface status on the connected switch: admin/oper state, VLANs, and errors on uplinks and access ports (read-only).'
  },
  {
    id: 'cisco-op-vlan-audit',
    label: 'VLAN and trunk audit',
    subtitle: 'Operator · Networking',
    icon: 'pi pi-sitemap',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'operator'],
    vendors: ['cisco'],
    text:
      'Audit VLANs and trunk allowed lists on the connected switch. Highlight inconsistencies before any configuration change.'
  },
  {
    id: 'cisco-op-stp-root',
    label: 'STP root and topology',
    subtitle: 'Operator · Networking',
    icon: 'pi pi-share-alt',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'operator'],
    vendors: ['cisco'],
    text:
      'Show spanning-tree root bridge and port roles on the connected switch. Note any blocked ports affecting Citrix or server VLANs.'
  },
  {
    id: 'cisco-op-neighbors',
    label: 'CDP / LLDP neighbors',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-users',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'networking', 'operator'],
    vendors: ['cisco'],
    text:
      'Show CDP and LLDP neighbors on the connected switch. Map uplinks to distribution/core and downstream access devices (read-only).'
  },
  {
    id: 'cisco-op-mac-table',
    label: 'MAC address table review',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-table',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator'],
    vendors: ['cisco'],
    text:
      'Summarize MAC address table entries on the connected switch for a given VLAN or interface. Note flapping or unexpected hosts (read-only).'
  },
  {
    id: 'cisco-op-routing-table',
    label: 'IP routing table',
    subtitle: 'Operator · Networking',
    icon: 'pi pi-map',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'operator'],
    vendors: ['cisco'],
    text:
      'Show IP routing table and connected routes on the connected L3 switch (read-only show ip route). Highlight missing or overlapping prefixes.'
  },
  {
    id: 'cisco-op-config-snapshot',
    label: 'Running config overview',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-file',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator'],
    vendors: ['cisco'],
    text:
      'Produce a concise overview of the running configuration on the connected switch: SVIs, key ACLs, and port-channels (read-only, no secrets).'
  },
  {
    id: 'cisco-op-port-channel',
    label: 'Port-channel status',
    subtitle: 'Operator · Networking',
    icon: 'pi pi-clone',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'operator'],
    vendors: ['cisco'],
    text:
      'List port-channel groups on the connected switch: member interfaces, LACP state, and load-balancing (read-only).'
  },
  {
    id: 'cisco-op-access-port-template',
    label: 'Standard access port config',
    subtitle: 'Operator · Networking',
    icon: 'pi pi-cog',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'configure', 'operator'],
    vendors: ['cisco'],
    text:
      'After search_cisco_cli_reference, propose IOS commands to configure a new access port (VLAN, description, no shutdown) on the connected switch. Ask for interface ID and VLAN before applying.'
  },
  {
    id: 'cisco-an-cpu-mem',
    label: 'CPU and memory utilization',
    subtitle: 'Analyst · Diagnostics',
    icon: 'pi pi-chart-line',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst'],
    vendors: ['cisco'],
    text:
      'Collect CPU, memory, and buffer utilization on the connected switch (read-only). Flag sustained high utilization.'
  },
  {
    id: 'cisco-an-logs',
    label: 'Recent syslog highlights',
    subtitle: 'Analyst · Diagnostics',
    icon: 'pi pi-file',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'analyst'],
    vendors: ['cisco'],
    text:
      'Review recent syslog messages on the connected switch for interface flaps, STP changes, or auth failures (read-only).'
  },
  {
    id: 'cisco-an-interface-errors',
    label: 'Interface error counters',
    subtitle: 'Analyst · Diagnostics',
    icon: 'pi pi-exclamation-circle',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'networking', 'analyst'],
    vendors: ['cisco'],
    text:
      'Show interface counters and errors on the connected switch. Identify ports with CRC, giants, or input errors (read-only).'
  },
  {
    id: 'cisco-an-stp-instability',
    label: 'STP instability signals',
    subtitle: 'Analyst · Diagnostics',
    icon: 'pi pi-share-alt',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'networking', 'analyst'],
    vendors: ['cisco'],
    text:
      'Check spanning-tree topology changes, blocked ports, and inconsistent roles on the connected switch (read-only).'
  },
  {
    id: 'cisco-an-connectivity-test',
    label: 'Ping / traceroute from switch',
    subtitle: 'Analyst · Diagnostics',
    icon: 'pi pi-send',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'networking', 'analyst'],
    vendors: ['cisco'],
    text:
      'From the connected switch, run read-only ping or traceroute to a target IP I provide. Report reachability and path.'
  },
  // ═══════════════════════════════════════════════════════════════════════════
  // F5 BIG-IP (TMSH / SSH) — 15 actions
  // ═══════════════════════════════════════════════════════════════════════════
  {
    id: 'f5-arch-ha-design',
    label: 'BIG-IP HA pair design',
    subtitle: 'Architect · HA',
    icon: 'pi pi-clone',
    type: 'prompt',
    role: 'architect',
    tags: ['ha-dr', 'common', 'architect'],
    vendors: ['f5'],
    text:
      'Design an F5 BIG-IP active/standby or active/active HA pair: sync groups, floating self IPs, failover triggers, and maintenance windows. Use jpilot-form discovery (one topic per turn, choice/boolean fields — no markdown question tables), then a formal design document.'
  },
  {
    id: 'f5-arch-vs-pool',
    label: 'Virtual server & pool design',
    subtitle: 'Architect · Traffic',
    icon: 'pi pi-server',
    type: 'prompt',
    role: 'architect',
    tags: ['common', 'architect'],
    vendors: ['f5'],
    text:
      'Design BIG-IP virtual servers, pools, monitors, and persistence for an HTTP/HTTPS application. Use jpilot-form discovery for VIP, backends, SSL, and monitors, then a design document with Handoff for Operator.'
  },
  {
    id: 'f5-arch-irules-events',
    label: 'iRules & event-driven logic',
    subtitle: 'Architect · Traffic',
    icon: 'pi pi-code',
    type: 'prompt',
    role: 'architect',
    tags: ['traffic-mgmt', 'common', 'architect'],
    vendors: ['f5'],
    text:
      'Design when to use iRules, iApps, or LTM policies on BIG-IP for traffic steering, header injection, or maintenance pages. Use jpilot-form discovery, then document events, conditions, and testing approach.'
  },
  {
    id: 'f5-op-version',
    label: 'TMOS version and license',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-info-circle',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'operator'],
    vendors: ['f5'],
    text:
      'On the connected BIG-IP, show TMOS version, hostname, license state, and failover status (read-only tmsh show commands).'
  },
  {
    id: 'f5-op-list-virtuals',
    label: 'List virtual servers',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-list',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'traffic-mgmt', 'operator'],
    vendors: ['f5'],
    text: 'List virtual servers on the connected BIG-IP with destination, pool, and availability (read-only).'
  },
  {
    id: 'f5-op-pool-health',
    label: 'Pool member health',
    subtitle: 'Operator · Traffic',
    icon: 'pi pi-heart',
    type: 'prompt',
    role: 'operator',
    tags: ['traffic-mgmt', 'operator'],
    vendors: ['f5'],
    text:
      'For a named pool on the connected BIG-IP, show member state, monitor results, and connection counts (read-only).'
  },
  {
    id: 'f5-op-ssl-profile',
    label: 'Client SSL profile summary',
    subtitle: 'Operator · Security',
    icon: 'pi pi-lock',
    type: 'prompt',
    role: 'operator',
    tags: ['security', 'ssl', 'operator'],
    vendors: ['f5'],
    text:
      'Summarize client SSL profiles and certificate names bound to virtual servers on the connected BIG-IP (read-only).'
  },
  {
    id: 'f5-op-snat-inventory',
    label: 'SNAT / NAT inventory',
    subtitle: 'Operator · Networking',
    icon: 'pi pi-map',
    type: 'prompt',
    role: 'operator',
    tags: ['networking', 'operator'],
    vendors: ['f5'],
    text:
      'List SNAT pools, NAT rules, and self IPs used for outbound connections on the connected BIG-IP (read-only tmsh list/show).'
  },
  {
    id: 'f5-op-persistence-profiles',
    label: 'Persistence profiles',
    subtitle: 'Operator · Traffic',
    icon: 'pi pi-sync',
    type: 'prompt',
    role: 'operator',
    tags: ['traffic-mgmt', 'operator'],
    vendors: ['f5'],
    text:
      'Show persistence profiles and which virtual servers use them on the connected BIG-IP (read-only).'
  },
  {
    id: 'f5-op-monitors-catalog',
    label: 'Health monitor catalog',
    subtitle: 'Operator · Discover',
    icon: 'pi pi-heart-fill',
    type: 'prompt',
    role: 'operator',
    tags: ['discover', 'traffic-mgmt', 'operator'],
    vendors: ['f5'],
    text:
      'List custom and system health monitors on the connected BIG-IP and which pools reference each (read-only).'
  },
  {
    id: 'f5-op-new-pool-vs',
    label: 'Create pool + virtual server',
    subtitle: 'Operator · Traffic',
    icon: 'pi pi-plus',
    type: 'prompt',
    role: 'operator',
    tags: ['traffic-mgmt', 'configure', 'operator', 'guided'],
    vendors: ['f5'],
    text:
      'After search_f5_tmsh_reference, create a basic HTTP pool and virtual server on the connected BIG-IP. Ask for VIP, port, pool members, and monitor before applying TMSH commands.'
  },
  {
    id: 'f5-an-failover',
    label: 'HA failover readiness',
    subtitle: 'Analyst · Diagnostics',
    icon: 'pi pi-clone',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'ha-dr', 'analyst'],
    vendors: ['f5'],
    text:
      'Check BIG-IP HA sync, config sync status, and failover triggers on the connected device without making changes.'
  },
  {
    id: 'f5-an-traffic',
    label: 'Traffic and connection anomalies',
    subtitle: 'Analyst · Diagnostics',
    icon: 'pi pi-chart-bar',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'traffic-mgmt', 'analyst'],
    vendors: ['f5'],
    text:
      'Investigate elevated connections or slow virtual servers on the connected BIG-IP using read-only statistics and logs.'
  },
  {
    id: 'f5-an-pool-down',
    label: 'Why are pool members down?',
    subtitle: 'Analyst · Diagnostics',
    icon: 'pi pi-times-circle',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'traffic-mgmt', 'analyst'],
    vendors: ['f5'],
    text:
      'Troubleshoot unavailable pool members on the connected BIG-IP: monitor failures, network path, and port/service state (read-only).'
  },
  {
    id: 'f5-an-cert-expiry',
    label: 'Certificate expiry check',
    subtitle: 'Analyst · Security',
    icon: 'pi pi-calendar',
    type: 'prompt',
    role: 'analyst',
    tags: ['diagnostics', 'security', 'ssl', 'analyst'],
    vendors: ['f5'],
    text:
      'List SSL certificates on the connected BIG-IP with expiration dates and which client SSL profiles reference them (read-only).'
  }
]

/**
 * @param {{ tab?: string, filterTag?: string|null, query?: string, vendor?: string|null }} opts
 */
export function filterJpilotCommands(opts = {}) {
  const tab = opts.tab || 'all'
  const filterTag = opts.filterTag || null
  const query = (opts.query || '').trim().toLowerCase()
  const vendor = opts.vendor ?? null

  return jpilotCommands.filter((cmd) => {
    if (vendor && !commandMatchesVendor(cmd, vendor)) return false
    if (tab !== 'all' && cmd.role !== tab) return false
    if (filterTag && !cmd.tags.includes(filterTag)) return false
    if (query) {
      const hay = `${cmd.label} ${cmd.subtitle || ''} ${cmd.text || ''} ${cmd.role}`.toLowerCase()
      if (!hay.includes(query)) return false
    }
    return true
  })
}

/** Default tab when opening the menu for a pane role. */
export function defaultCommandTabForRole(role) {
  if (role === 'architect' || role === 'analyst' || role === 'operator') return role
  if (role === 'investigator') return 'analyst'
  return 'all'
}

function toLegacyAction(cmd) {
  return {
    id: cmd.id,
    label: cmd.label,
    icon: cmd.icon,
    type: cmd.type,
    text: cmd.text,
    to: cmd.to
  }
}

/** Legacy grouped shape for compact consumers (e.g. dashboard). */
export const jpilotRecommendedGroups = [
  {
    id: 'architect',
    title: 'Architecture & design',
    actions: jpilotCommands.filter((c) => c.role === 'architect').map(toLegacyAction)
  },
  {
    id: 'operator-networking',
    title: 'Operator · Networking',
    actions: jpilotCommands
      .filter((c) => c.role === 'operator' && c.tags.includes('networking'))
      .map(toLegacyAction)
  },
  {
    id: 'operator-traffic',
    title: 'Operator · Traffic management',
    actions: jpilotCommands
      .filter((c) => c.role === 'operator' && c.tags.includes('traffic-mgmt'))
      .map(toLegacyAction)
  },
  {
    id: 'operator-security',
    title: 'Operator · Security',
    actions: jpilotCommands
      .filter((c) => c.role === 'operator' && (c.tags.includes('security') || c.tags.includes('ssl')))
      .map(toLegacyAction)
  },
  {
    id: 'operator-discover',
    title: 'Operator · Discover',
    actions: jpilotCommands
      .filter((c) => c.role === 'operator' && c.tags.includes('discover') && !c.tags.includes('networking'))
      .map(toLegacyAction)
  },
  {
    id: 'analyst',
    title: 'Analyst',
    actions: jpilotCommands.filter((c) => c.role === 'analyst').map(toLegacyAction)
  }
]

/** Flat list for compact UIs (e.g. dashboard chips). */
export function flattenRecommendedActions(groups = jpilotRecommendedGroups) {
  return groups.flatMap((group) =>
    group.actions.map((action) => ({
      ...action,
      group: group.title
    }))
  )
}

export const dashboardQuickActions = [
  { label: 'Open JPilot', icon: 'pi pi-comments', to: '/copilot', adminOnly: false },
  { label: 'Add appliance', icon: 'pi pi-plus', to: '/appliances', adminOnly: true },
  { label: 'SSL certificates', icon: 'pi pi-shield', to: '/appliances?tab=ssl', adminOnly: false },
  { label: 'Settings', icon: 'pi pi-cog', to: '/settings', adminOnly: false },
  { label: 'AI providers', icon: 'pi pi-sparkles', to: '/settings?section=ai-providers', adminOnly: true }
]

export function getDashboardQuickActions(isAdmin) {
  return dashboardQuickActions.filter((action) => isAdmin || !action.adminOnly)
}
