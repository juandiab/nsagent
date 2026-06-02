export const NEXXUS_TECH = {
  name: 'Nexxus Tech',
  websiteUrl: 'https://www.nexxus-tech.com',
  blogUrl: 'https://www.nexxus-tech.com/blog',
  contactUrl: 'https://www.nexxus-tech.com/contact'
}

/** Curated from https://www.nexxus-tech.com/api/blog — used when the proxy is unavailable. */
export const NEXXUS_BLOG_FALLBACK = [
  {
    slug: 'nsagent-open-source-netscaler-copilot',
    title: 'JPilot: NetScaler AI Copilot with Memory-Guided Tools',
    excerpt:
      "JPilot is Nexxus Tech's NetScaler AI copilot—built on Next-Gen API, memory-guided tools, and secure local or enterprise AI.",
    category: 'AI & Automation',
    date: '2026-06-02',
    read_time: 10,
    cover_color: '#4DB8E0'
  },
  {
    slug: 'netscaler-hybrid-post-quantum-cryptography',
    title: 'NetScaler Hybrid Post-Quantum Cryptography: Quantum-Ready TLS',
    excerpt:
      'NetScaler supports hybrid PQC (X25519_MLKEM768) on the TLS front end—mitigating harvest-now-decrypt-later risk while staying browser-compatible.',
    category: 'Security',
    date: '2026-06-02',
    read_time: 8,
    cover_color: '#6B5CE7'
  },
  {
    slug: 'netscaler-waf-top10-owasp-2024',
    title: 'Protecting Against the OWASP Top 10 with NetScaler Web App Firewall',
    excerpt:
      'Guide to NetScaler WAF and OWASP Top 10:2025—staged rollout, signatures, OpenAPI schema validation, and bot management.',
    category: 'WAF & Security',
    date: '2024-11-15',
    read_time: 10,
    cover_color: '#5B4FE8'
  },
  {
    slug: 'zero-trust-architecture-netscaler-okta-azure-ad',
    title: 'Building Zero Trust Access with NetScaler Gateway, Okta, and Microsoft Entra ID',
    excerpt:
      'Zero Trust with NetScaler Gateway as SAML SP, Entra ID or Okta as IdP, Conditional Access, nFactor, and EPA.',
    category: 'Zero-Trust',
    date: '2024-10-03',
    read_time: 11,
    cover_color: '#1DD4B4'
  },
]

export function nexxusBlogArticleUrl(slug) {
  return `${NEXXUS_TECH.blogUrl}/${slug}`
}
