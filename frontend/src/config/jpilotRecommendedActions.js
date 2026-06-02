/**
 * Recommended starter actions for JPilot empty state and dashboard shortcuts.
 * `prompt` actions send a chat message; `link` actions navigate to a tool page.
 */
export const jpilotRecommendedGroups = [
  {
    id: 'discover',
    title: 'Discover',
    actions: [
      {
        id: 'system-info',
        label: 'Firmware, hostname, and serial',
        icon: 'pi pi-info-circle',
        type: 'prompt',
        text: 'Show system info for the connected appliance — firmware version, hostname, management IP, and serial number.'
      },
      {
        id: 'list-ips',
        label: 'List all IP addresses (NSIP, SNIP, VIP)',
        icon: 'pi pi-map-marker',
        type: 'prompt',
        text: 'List all IP addresses on the connected appliance with their types (NSIP, SNIP, VIP, etc.).'
      },
      {
        id: 'list-vservers',
        label: 'List load balancing virtual servers',
        icon: 'pi pi-sitemap',
        type: 'prompt',
        text: 'List all load balancing virtual servers on the connected appliance, including VIP, port, and state.'
      },
      {
        id: 'list-apps',
        label: 'List Next-Gen applications',
        icon: 'pi pi-box',
        type: 'prompt',
        text: 'List all Next-Gen API applications configured on the connected appliance.'
      }
    ]
  },
  {
    id: 'network',
    title: 'Network checks',
    actions: [
      {
        id: 'ping-google',
        label: 'Can the appliance reach 8.8.8.8?',
        icon: 'pi pi-wifi',
        type: 'prompt',
        text: 'Can the connected NetScaler appliance ping 8.8.8.8? Run a ping diagnostic and report the result.'
      },
      {
        id: 'ping-host',
        label: 'Test reachability to a host',
        icon: 'pi pi-share-alt',
        type: 'prompt',
        text: 'Can the connected appliance reach google.com? Use ping or traceroute and summarize reachability.'
      },
      {
        id: 'port-check',
        label: 'Check if port 443 is open on a host',
        icon: 'pi pi-link',
        type: 'prompt',
        text: 'From the connected appliance, check whether TCP port 443 is open on google.com and report open, refused, or no response.'
      }
    ]
  },
  {
    id: 'configure',
    title: 'Configure',
    actions: [
      {
        id: 'lb-vserver',
        label: 'Plan a new LB vserver (guided)',
        icon: 'pi pi-sliders-h',
        type: 'prompt',
        text: 'I want to create a new HTTP load balancing vserver. Ask me the required details with a form, then configure it on the appliance.'
      },
      {
        id: 'add-vip',
        label: 'Add a VIP or SNIP',
        icon: 'pi pi-plus-circle',
        type: 'prompt',
        text: 'I need to add a new VIP on the connected appliance. Ask what you need, then add the IP address.'
      },
      {
        id: 'storefront-lb',
        label: 'StoreFront / HTTPS LB checklist',
        icon: 'pi pi-list-check',
        type: 'prompt',
        text: 'Help me plan an HTTPS load balancer for Citrix StoreFront. Ask for missing details with a form before making any changes.'
      }
    ]
  },
  {
    id: 'ssl',
    title: 'SSL & certificates',
    actions: [
      {
        id: 'ssl-tool',
        label: 'Open SSL certificate tools',
        icon: 'pi pi-shield',
        type: 'link',
        to: '/ssl-csr'
      },
      {
        id: 'self-signed',
        label: 'Generate a self-signed cert for testing',
        icon: 'pi pi-key',
        type: 'link',
        to: '/ssl-csr'
      },
      {
        id: 'show-certkeys',
        label: 'Show installed certificate-key pairs',
        icon: 'pi pi-lock',
        type: 'prompt',
        text: 'Show all SSL certificate-key pairs on the connected appliance.'
      }
    ]
  },
  {
    id: 'diagnostics',
    title: 'Diagnostics',
    actions: [
      {
        id: 'cpu-mem',
        label: 'CPU and memory usage',
        icon: 'pi pi-chart-bar',
        type: 'prompt',
        text: 'Collect current CPU and memory statistics from the connected appliance.'
      },
      {
        id: 'lb-stats',
        label: 'LB vserver hit counts',
        icon: 'pi pi-chart-line',
        type: 'prompt',
        text: 'Show load balancing statistics and hit counts for virtual servers on the connected appliance.'
      },
      {
        id: 'health-summary',
        label: 'Quick health summary',
        icon: 'pi pi-heart',
        type: 'prompt',
        text: 'Give me a quick health summary of the connected appliance: version, IPs, LB vserver count, and any obvious issues.'
      }
    ]
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
  { label: 'Open JPilot', icon: 'pi pi-comments', to: '/copilot' },
  { label: 'SSL certificates', icon: 'pi pi-shield', to: '/ssl-csr' },
  { label: 'Add NetScaler', icon: 'pi pi-server', to: '/netscalers' },
  { label: 'AI providers', icon: 'pi pi-sparkles', to: '/ai-providers' },
  { label: 'Next-Gen API', icon: 'pi pi-code', to: '/next-gen-api' }
]
