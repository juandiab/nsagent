# Terms of Service

**Last updated: June 3, 2026**

These Terms of Service ("Terms") govern your access to and use of **JPilot**, an AI assistant for NetScaler / Citrix ADC administration (the "Service"), provided by **Nexxus-Tech SAS** ("Nexxus Tech", "Nexxus", "we", "us", or "our"). By creating an account, installing, or using the Service, you agree to these Terms. If you do not agree, do not use the Service.

If you use the Service on behalf of an organization, you represent that you are authorized to bind that organization, and "you" refers to that organization.

---

## 1. The Service and editions

JPilot is offered as a **hosted (SaaS)** service operated by Nexxus and as **self-hosted software** you may install on your own infrastructure.

- The **Free edition** is available to individuals, small businesses, and businesses generally for their **own internal operations**, subject to these Terms and any published usage limits.
- **Paid, Enterprise, and other licensed offerings** are governed by a **separate written Commercial Agreement**, not by these Terms alone (see below).

**Commercial and licensed offerings (separate agreement).** The Free edition is offered solely under these Terms (and the EULA for self-hosted Software). **Paid editions, Enterprise editions, custom deployments, professional services, migration or implementation support, and any use not expressly permitted under the Free edition** (including MSP and sublicensing use) are **not licensed by your acceptance of these Terms or the EULA alone**. Those offerings require a **separate written agreement** executed by authorized representatives of both parties—for example, an **Enterprise Agreement**, master services agreement, order form, or statement of work (each, a **"Commercial Agreement"**).

When a Commercial Agreement applies to your use of the Service, that agreement (together with any exhibits, data-processing addendum, and order documents) sets the **fees, subscription term, license scope, support, service levels, and other commercial terms** for your licensed offering. **If there is a conflict** between the Commercial Agreement and these Terms, the EULA, or the Acceptable Use Policy, **the Commercial Agreement prevails** with respect to that conflict; otherwise these documents continue to apply. Quotes, pricing pages, pilots, or sales communications do **not** create a binding Commercial Agreement unless set out in a written agreement signed by both parties.

**Any company may use JPilot for its own internal operations.** The Service and Software may **not be resold, sublicensed, rented, or otherwise made available to third parties as a service or product**, whether for a fee or not, except under a Commercial Agreement that expressly permits it.

**Managed Service Providers (MSPs).** If you use JPilot to deliver services to, or to manage infrastructure on behalf of, third parties (for example, as a managed-services or hosting provider), you must obtain an **Enterprise license per managed server** under a Commercial Agreement. The price of such a license is established by Nexxus Tech based on the **scope, functionalities, and time/effort** involved, as set out in the applicable Commercial Agreement.

For self-hosted use, the software is also subject to the **End-User License Agreement (EULA)**.

## 2. Purpose; assistive nature

JPilot is an **assistive tool** intended to help qualified personnel work more efficiently. **It does not replace System Administrators, network engineers, or other qualified professionals, and is not intended for that purpose** — it is designed to optimize their work. The Service does not provide professional, legal, security, or compliance advice. You remain fully responsible for the decisions you make and the actions you execute.

We recommend deploying and using the Service only in **controlled environments with controlled, least-privilege user access**, and only against systems you are authorized to administer.

**Not for safety-critical use.** The Service is **not designed or intended for use in life-safety, emergency, or other high-risk environments where failure could lead to death, personal injury, or severe physical, environmental, or property damage.** You must not use it for such purposes.

## 3. Accounts and eligibility

You must be at least **18 years old** and provide accurate registration information. You are responsible for your account, your credentials, and all activity under your account. Notify us promptly of any unauthorized use. We may provision, suspend, or remove accounts as needed to operate the Service or enforce these Terms.

**Business and professional use.** The Service is intended for **business and professional use** by individuals and organizations that administer infrastructure. If you use the Service as a consumer in a jurisdiction that grants non-waivable consumer rights, those rights remain unaffected by these Terms.

## 4. Acceptable use

Your use of the Service is subject to our **Acceptable Use Policy (AUP)**, which is incorporated into these Terms. You must not misuse the Service, interfere with its operation, attempt to access it without authorization, or use it to act against systems you are not authorized to administer.

## 5. Your responsibilities; high-impact operations

JPilot can execute configuration and operational actions against NetScaler / Citrix ADC appliances and other systems **you connect**. You are solely responsible for:

- the appliances, credentials, systems, and **host operating system and environment** on which you run or connect the Service, including their security, patching, hardening, network controls, and access management;
- reviewing and approving actions before they are applied, especially changes that can affect production traffic, security, or availability; and
- maintaining backups and change-control appropriate to your environment.

**AI output may be inaccurate or incomplete.** You must independently verify any commands, configurations, or recommendations before relying on them.

**Confirmation prompts are an assistive safety feature, not a guarantee.** The Service may prompt you for confirmation before certain actions (for example, potentially destructive commands). Because AI behavior is non-deterministic, such prompts may not appear for every risky action. You must independently review and approve **every** action, must not rely solely on these prompts, and **are responsible for any command you allow to execute** — you are informed before execution and accept the outcome.

## 6. Third-party services, AI providers, and sources

The Service integrates with third-party providers you configure—including AI providers (e.g., OpenAI, Anthropic, Google Gemini, xAI, DeepSeek), optional web search (Brave Search), and email/SMTP providers. Your use of those services is governed by their terms, and you are responsible for obtaining and complying with the necessary accounts, API keys, and licenses. Nexxus is not responsible for third-party services.

**Allowed sources and prompt injection.** By default, the Service enables only the **official documentation websites of the relevant vendors**. If you add any additional URL, domain, or source, **you do so at your own risk**, including the risk of prompt-injection or similar attacks delivered through retrieved web content, appliance output, configuration files, screenshots, or any other content the Service ingests. You are responsible for the sources you enable and the content you submit.

**Confidential data and AI providers.** JPilot does not, on its own, share, sell, or expose your confidential information. However, when you send a prompt or attachment, the relevant content is transmitted to the **AI provider you configure** in order to generate a response. **You are solely responsible for the data you choose to expose to public/consumer SaaS LLMs** and for ensuring that doing so is permitted by your policies and applicable law. Do not submit confidential, regulated, or personal data to a provider unless its terms and your obligations allow it.

**Recommended for Enterprise:** to keep sensitive data within controlled boundaries, we recommend using an **Enterprise SaaS LLM** (with data-protection/no-training commitments), a **dedicated cloud LLM**, or a **self-hosted LLM** (e.g., via LM Studio or an OpenAI-compatible endpoint) so that prompt content never leaves your infrastructure.

## 7. Fees, plans, and token usage

The Free edition is provided at no charge and may have functional or usage limits. Paid and Enterprise plans are billed as described in your Commercial Agreement or, for online purchases without a separate agreement, at checkout. Except where required by law or expressly stated, fees are non-refundable. We may change plans, limits, or pricing on reasonable notice; changes do not apply retroactively to a paid term already purchased.

**Token usage and costs.** AI features consume tokens that are billed to you by your AI provider. Some requests inherently consume more tokens than others. We make **commercially reasonable efforts to optimize token consumption and product efficiency**, and we may continue to improve the Service over time, but **we do not warrant any particular level of token usage, cost, or efficiency, are under no obligation to provide optimizations, and are not responsible for charges billed to you by your providers.**

## 8. Free service, availability, and no SLA

The Free edition is provided **without any service-level agreement, uptime guarantee, or support commitment**. We may modify, suspend, limit, or **discontinue the Service or any feature at any time, with or without notice, and without liability to you**. Service-level, support, or availability commitments, if any, apply **only under a Commercial Agreement**.

## 9. Intellectual property

The Service, including its software, design, and documentation, is owned by Nexxus and its licensors and is protected by law. Subject to these Terms (and the EULA for self-hosted use), we grant you a limited, non-exclusive, non-transferable, revocable right to use the Service. You retain all rights to the content and data you submit ("Your Content"); you grant us a limited license to host, process, and transmit Your Content solely to provide the Service.

## 10. Feedback

If you provide suggestions or feedback, you grant us a perpetual, royalty-free license to use it without restriction or obligation to you.

## 11. Data, encryption, and backups

Our handling of personal data is described in the **Privacy Policy**. **The Service does not send telemetry, usage analytics, or your operational content back to Nexxus.** Sensitive information stored by the Service (such as API keys, appliance credentials, and SMTP credentials) is **encrypted at rest**; in self-hosted deployments, the data and the encryption key remain **solely under your control**.

**Nexxus is not responsible for recovering any lost data, configurations, credentials, or content,** and you are responsible for maintaining your own backups and for safeguarding your encryption keys and credentials. For self-hosted deployments, you control your data and environment in full.

## 12. Trademarks and no affiliation

The following names are trademarks of their respective owners and are used only for identification and interoperability:

- **Cloud Software Group / Citrix:** NetScaler, NetScaler MPX, NetScaler VPX, NetScaler SDX, Citrix ADC, Citrix Gateway, Citrix Virtual Apps and Desktops (CVAD), StoreFront, Citrix, and related product names.
- **Cisco Systems:** Cisco, IOS, IOS-XE, ASA, Firepower, FTD, ACI, and related product names.
- **F5:** F5, BIG-IP, NGINX, and related product names.
- **Juniper Networks:** Juniper, Junos, SRX, EX, QFX, and related product names.
- **Palo Alto Networks:** PAN-OS, Panorama, and related product names.
- **Fortinet:** FortiGate, FortiADC, and related product names.
- **Check Point Software Technologies:** Check Point and related product names.
- **A10 Networks:** A10, Thunder ADC, and related product names.
- **Radware:** Radware, Alteon, AppWall, and related product names.
- **HAProxy / Kemp:** HAProxy, Kemp, and related product names.
- **AI, search, email, and deployment (as you configure):** OpenAI, Anthropic, Claude, Google, Gemini, xAI, Grok, DeepSeek, Brave, LM Studio, Docker, MongoDB, Hetzner, and related product names.

**Nexxus Tech and JPilot are independent and are not affiliated with, sponsored by, endorsed by, or certified by any of these companies.** All third-party names and marks are used solely for identification and interoperability purposes.

## 13. Disclaimers

THE SERVICE IS PROVIDED **"AS IS" AND "AS AVAILABLE," WITHOUT WARRANTIES OF ANY KIND**, EXPRESS OR IMPLIED, INCLUDING MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT, AND ANY WARRANTY THAT THE SERVICE OR AI OUTPUT WILL BE ACCURATE, SECURE, UNINTERRUPTED, OR ERROR-FREE, TO THE FULLEST EXTENT PERMITTED BY LAW. WE DO NOT WARRANT THAT THE SERVICE WILL PREVENT OUTAGES, MISCONFIGURATIONS, OR SECURITY INCIDENTS.

## 14. Limitation of liability

TO THE FULLEST EXTENT PERMITTED BY LAW, NEXXUS AND ITS SUPPLIERS WILL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR FOR LOSS OF PROFITS, DATA, GOODWILL, OR SERVICE INTERRUPTION, OR FOR ANY DAMAGE TO OR OUTAGE OF SYSTEMS YOU CONNECT, ARISING FROM OR RELATED TO THE SERVICE. OUR TOTAL AGGREGATE LIABILITY FOR ANY CLAIM WILL NOT EXCEED THE GREATER OF (A) THE AMOUNTS YOU PAID TO NEXXUS FOR THE SERVICE IN THE **TWELVE (12) MONTHS** BEFORE THE EVENT GIVING RISE TO THE CLAIM, OR (B) **COP 1,000**.

**Mandatory rights.** Nothing in these Terms excludes or limits liability that **cannot be excluded or limited under applicable law**, including mandatory consumer, data-protection, or personal-injury rights where you are located. Where a limitation is unenforceable, it applies only to the extent permitted.

## 15. Indemnification

You will indemnify and hold harmless Nexxus from claims, damages, and expenses arising out of your use of the Service, Your Content, the systems you connect, the sources you enable, or your violation of these Terms or applicable law.

## 16. Suspension and termination

We may suspend or terminate access for violation of these Terms, legal requirements, security risks, or non-payment. You may stop using the Service at any time. Upon termination, your right to use the Service ends; provisions that by their nature should survive (including Sections 9, 11–15, 17, and 19) survive.

## 17. Export control and sanctions

You may not use, export, or re-export the Service in violation of applicable U.S., Colombian, or other export-control or sanctions laws. You represent that you are not located in, or a national or resident of, an embargoed jurisdiction, and that you are not on any restricted- or denied-party list.

## 18. Availability, governing law, and disputes

**Worldwide availability.** JPilot is offered **worldwide** for business and professional use, except where prohibited by law or export/sanctions rules (see Section 17). Marketing or access channels (including LinkedIn or other referrals) do not change these Terms.

**Governing law.** These Terms are governed by the laws of the **Republic of Colombia**, without regard to conflict-of-laws rules, except that mandatory laws of your country of residence or establishment may apply to the extent they cannot be waived by contract.

**Disputes.** Before filing a claim, you agree to contact us at **contact@nexxus-tech.com** and allow **thirty (30) days** to try to resolve the matter informally. Subject to mandatory local rules, exclusive jurisdiction and venue for disputes that are not resolved informally lie in the **competent courts of Bogotá D.C., Colombia**. You and Nexxus each waive any right to participate in a class or representative action **to the extent such waiver is permitted** by applicable law.

For customers with a Commercial Agreement, the governing law and dispute-resolution terms in that Commercial Agreement control.

## 19. General

These Terms (together with the Privacy Policy, AUP, EULA, and any Commercial Agreement) are the **entire agreement** between you and Nexxus regarding the Service **for Free-edition use**, and supersede prior agreements on that subject. **Licensed offerings under a Commercial Agreement are governed by that agreement**; where the documents conflict, the Commercial Agreement prevails as described in Section 1. If any provision is held unenforceable, the remaining provisions remain in effect (**severability**). Our failure to enforce a provision is not a **waiver**. You may not **assign** these Terms without our consent; we may assign them in connection with a merger, acquisition, or sale of assets. Neither party is liable for delays or failures caused by events beyond its reasonable control (**force majeure**). Notices to you may be given in-product or by email; notices to us must be sent to **contact@nexxus-tech.com**.

## 20. Changes to these Terms

We may update these Terms from time to time. Material changes take effect upon posting the updated "Last updated" date or as otherwise communicated. Continued use after changes constitutes acceptance.

## 21. Contact

**Nexxus Tech SAS Colombia** — **contact@nexxus-tech.com**.
