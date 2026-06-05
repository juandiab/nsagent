import { NEXXUS_TECH } from './nexxusTech'

export const PRICING_PLANS = [
  {
    id: 'free',
    name: 'Free Edition',
    tagline: 'Everything you need to start',
    priceLabel: 'Free',
    priceDetail: 'Forever · unlimited',
    highlighted: false,
    ctaLabel: 'You are here',
    ctaHref: null,
    ctaDisabled: true,
    features: [
      'Unlimited NetScaler appliances',
      'Password login and optional passkeys (WebAuthn)',
      'Any LLM provider — cloud or local (LM Studio, OpenAI-compatible)',
      'JPilot copilot with MCP — Next-Gen API and SSH CLI',
      'Diagnostics, SSL CSR tools, and admin user roles',
      'Encrypted appliance credentials — never sent to the LLM',
      'On-prem Docker — data stays in your network'
    ]
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    tagline: 'Identity, ADC depth, and guided rollout',
    priceLabel: null,
    priceDetail: 'Custom quote',
    highlighted: false,
    ctaLabel: 'Contact us',
    ctaHref: NEXXUS_TECH.contactUrl,
    ctaDisabled: false,
    features: [
      'Everything in Free Edition',
      'SSO for JPilot — LDAP, Entra ID, Okta, or Google',
      'Custom copilot prompts and org runbooks',
      'Engineer-led WAF, GSLB, SSL, and CS/LB workflows on NetScaler',
      'Custom MCP memory files for your change standards',
      'HA deployment, backup, and upgrade assistance',
      'Email and ticket support (business hours)'
    ]
  },
  {
    id: 'enterprise-pro',
    name: 'Enterprise Pro',
    tagline: 'Advanced programs with on-demand expert support',
    priceLabel: null,
    priceDetail: 'Support Credits included',
    highlighted: false,
    ctaLabel: 'Contact us',
    ctaHref: NEXXUS_TECH.contactUrl,
    ctaDisabled: false,
    features: [
      'Everything in Enterprise',
      'Advanced WAF programs — OWASP, bot management, tuning',
      'On-demand support via Support Credits — remote SME engineers when you need them',
      'Credits for migrations, production changes, and advanced implementations',
      'Dedicated architect and priority support channel',
      'F5-to-NetScaler and multicloud ADC migration playbooks',
      'Production runbooks and change-window execution support'
    ]
  }
]

export const PLATFORM_HIGHLIGHTS = [
  {
    icon: 'pi pi-gift',
    title: 'Free to use',
    description: 'No license fees. No appliance or user limits.'
  },
  {
    icon: 'pi pi-infinity',
    title: 'Unlimited',
    description: 'As many NetScalers and LLM providers as you need.'
  },
  {
    icon: 'pi pi-server',
    title: 'On-premises',
    description: 'Docker on your network. Your data never leaves.'
  },
  {
    icon: 'pi pi-lock',
    title: 'Secure',
    description: 'Encrypted secrets, JWT sessions, optional passkeys, TLS-ready.'
  },
  {
    icon: 'pi pi-chart-line',
    title: 'Monitorable',
    description: 'Standard containers — plug into your existing observability stack.'
  },
  {
    icon: 'pi pi-shield',
    title: 'Best practices',
    description: 'Authenticated API access and least-privilege user roles.'
  }
]
