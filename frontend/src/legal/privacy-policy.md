# Privacy Policy

**Last updated: June 3, 2026**

This Privacy Policy explains how **Nexxus-Tech SAS** ("Nexxus Tech", "Nexxus", "we", "us", or "our") collects, uses, discloses, and protects information in connection with **JPilot**, our AI assistant for NetScaler / Citrix ADC administration (the "Service").

**Nexxus Tech SAS Colombia**. For any privacy question, contact us at **contact@nexxus-tech.com**.

---

## 1. Hosted vs. self-hosted deployments

JPilot is offered in two ways, and our role differs accordingly:

- **Hosted (SaaS).** When you use JPilot at `jpilot.nexxus-tech.com` or another environment operated by Nexxus, we act as the **data controller** for account data and as a **data processor** for the operational data you put into the Service.
- **Self-hosted.** When you (or your organization) install JPilot on your own infrastructure using our Docker installer, **you are the data controller**. Nexxus does not host, access, or receive your data, and this Policy applies only to the software itself and to any optional services you choose to contact (for example, an AI provider). Your administrator is responsible for how the deployment is configured and secured.

This Policy describes the maximum set of data the Service can process. Your actual experience depends on your deployment type and configuration.

JPilot is available **worldwide** for business and professional use (except where prohibited by law). Referral sources such as LinkedIn do not change this Policy.

## 2. Information we process

**Account and authentication data:** username, email address, role, a securely hashed password, and—if you enable it—passkey (WebAuthn) credentials and session tokens.

**Configuration and secrets you provide:** AI provider API keys, Brave Search API keys, SMTP/email credentials, MCP server settings, and NetScaler/Citrix ADC connection details (hostnames, usernames, and credentials). Secrets are **encrypted at rest**.

**Operational content:** messages, prompts, file attachments (e.g., configuration files, screenshots) you send to JPilot, and the AI responses generated for you.

**Usage and diagnostic data:** model usage metrics (such as token and request counts), feature settings, and technical logs needed to operate and secure the Service.

**Transactional email data:** when password reset or notification emails are enabled, we process the recipient address and message content needed to send them.

We do **not** use third-party advertising or behavioral-tracking cookies, and **the Service does not send telemetry, usage analytics, or your operational content back to Nexxus.** The Service uses only the storage strictly necessary to keep you signed in (for example, a session token in your browser's local storage).

## 3. How we use information

We use information to: provide and operate the Service; authenticate users and secure accounts; execute the actions you request against your AI providers and NetScaler appliances; generate AI responses; meter usage and enforce plan limits; send transactional emails you have enabled; maintain security, prevent abuse, and debug issues; and comply with legal obligations.

We do **not** sell your personal information, and we do **not** use your operational content to train our own models.

## 4. AI providers and subprocessors

JPilot connects to the AI provider **you configure**. When you send a prompt, the relevant content is transmitted to that provider to generate a response. Supported providers include **OpenAI, Anthropic (Claude), Google Gemini, xAI (Grok), and DeepSeek**, or a **self-hosted model via LM Studio / OpenAI-compatible endpoint** that never leaves your infrastructure. Each third-party provider processes your data under its own terms and privacy policy.

**The platform does not share, sell, or expose your confidential information on its own.** Data is sent to an external provider only as a direct result of your actions (the prompts and attachments you submit). **You are responsible for the data you choose to expose to public/consumer SaaS LLMs** and for ensuring that doing so complies with your policies and applicable law. For sensitive workloads—and for Enterprise deployments in particular—we recommend an **Enterprise SaaS LLM** with data-protection and no-training commitments, a **dedicated cloud LLM**, or a **self-hosted LLM** so prompt content remains within your controlled environment.

**Web sources.** By default the Service enables only the **official vendor documentation sites**. Any additional URL or source you add is enabled at your own risk, including exposure to prompt-injection or similar attacks via retrieved content.

For hosted deployments, we may rely on the following **subprocessors** (categories and primary providers):

| Category | Provider (region) | Purpose |
|----------|-------------------|---------|
| Cloud hosting | Hetzner Online GmbH (EU/Germany) | Infrastructure |
| Database | MongoDB (deployment-dependent) | Data storage |
| AI (as configured by you) | OpenAI, Anthropic, Google, xAI, DeepSeek, or your endpoint | Inference |
| Web search (optional) | Brave Search | Search results |
| Email (optional) | Your SMTP provider (e.g., Google) | Transactional email |

We update this list as subprocessors change. Enterprise customers may request a **Data Processing Agreement (DPA)** that describes processing, subprocessors, and security measures in more detail.

## 5. Disclosure of information

We disclose information only: to subprocessors who help us run the Service under appropriate confidentiality and data-protection terms; to the AI/search/email providers you configure, to fulfill your requests; when required by law or to protect rights, safety, and security; and in connection with a merger, acquisition, or asset sale, subject to this Policy. In self-hosted deployments, disclosures are controlled entirely by your organization.

## 6. Data retention

We retain account data for as long as your account is active. Operational content and configuration are retained until you delete them or close the account. After deletion or account closure, data is removed from active systems within a commercially reasonable period and may persist in encrypted backups for a limited time before being overwritten. We retain limited records longer where required for legal, security, or accounting purposes.

## 7. Security

We use encryption of secrets at rest, hashed passwords, optional passkey (WebAuthn) and multi-factor sign-in, role-based access controls, and transport encryption (HTTPS). Sensitive information stored by the Service (such as API keys, appliance credentials, and SMTP credentials) is **encrypted at rest**; in self-hosted deployments, the data and the encryption key remain **solely under your control**. No system is perfectly secure; you are responsible for safeguarding your credentials and, in self-hosted deployments, for the **security of the host operating system and environment** and for deploying in a controlled environment with controlled, least-privilege access.

**No recovery / backups.** Nexxus is **not responsible for recovering any lost data, configurations, credentials, or content.** You are responsible for maintaining your own backups and for safeguarding your encryption keys and credentials.

## 8. International transfers

For hosted deployments, your information may be processed in countries other than your own, including **Colombia**, the **European Union** (via our hosting provider), and—when you configure them—**the United States** or other countries through your chosen AI, email, or search providers.

Where **UK GDPR** or **EU GDPR** requires safeguards for transfers outside the UK/EEA, we rely on appropriate mechanisms such as **Standard Contractual Clauses (SCCs)** and/or the UK **International Data Transfer Agreement (IDTA)** or **UK Addendum**, as applicable, together with supplementary measures where appropriate. Details are available on request for Enterprise customers under a DPA.

**Your responsibility for third-party transfers.** When you configure a US or other non-EEA AI or email provider, **you direct those transfers** by your configuration and prompts. You are responsible for ensuring that choice complies with your policies and law.

## 9. Legal bases (EEA, UK, and similar regimes)

For hosted deployments where GDPR or UK GDPR applies, we process personal data on these bases:

| Processing | Legal basis |
|------------|-------------|
| Account, authentication, operating the Service | **Contract** (necessary to provide the Service you request) |
| Security, abuse prevention, logs | **Legitimate interests** (protecting the Service and users) |
| Compliance with law | **Legal obligation** |
| Optional features you enable (e.g., certain emails, passkeys) | **Contract** and/or **consent** where required |

We do **not** use your operational content to train our own models. Marketing cookies and cross-site tracking are **not** used.

## 10. Your rights

Depending on your location and applicable law—including **EU/UK GDPR**, **Colombia's Ley 1581 de 2012 (Habeas Data)**, **UAE PDPL** (where applicable), and U.S. state privacy laws such as **CCPA/CPRA**—you may have rights to **access**, **correct**, **delete**, **restrict** or **object** to processing, **portability**, and to **withdraw consent** where processing is consent-based.

To exercise rights for hosted accounts, contact **contact@nexxus-tech.com**. We respond within the timeframes required by applicable law (for example, **one month** under GDPR, extendable where permitted). In self-hosted deployments, **your organization is the data controller**—direct requests to your administrator; Nexxus does not hold your operational data.

**Supervisory authorities.** You may lodge a complaint with a regulator, including:

- **Colombia:** Superintendencia de Industria y Comercio (SIC)
- **UK:** Information Commissioner's Office (ICO) — [ico.org.uk](https://ico.org.uk)
- **EU:** Your local data protection authority

## 11. Security incidents

If we become aware of a personal-data breach affecting hosted account data that we control, we will notify you and, where required by law, regulators **without undue delay** and in line with applicable breach-notification rules. Self-hosted deployments are **your responsibility** to monitor and notify.

## 12. Children's privacy

The Service is not directed to individuals under **18**, and we do not knowingly collect their personal data.

## 13. Changes to this Policy

We may update this Policy from time to time. Material changes will be indicated by updating the "Last updated" date and, where appropriate, by additional notice.

## 14. Contact

Questions or requests: **contact@nexxus-tech.com** — **Nexxus Tech SAS Colombia**.
