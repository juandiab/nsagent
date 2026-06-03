# End-User License Agreement (EULA)

**Last updated: June 3, 2026**

This End-User License Agreement ("EULA") is a legal agreement between you (an individual or a single entity, "you") and **Nexxus-Tech SAS** ("Nexxus Tech", "Nexxus", "we", "us", or "our") for the **JPilot** software, also referred to as "NSAgent," including its components, installers, and accompanying documentation (the "Software").

By installing, copying, or otherwise using the Software—including via the Docker installer for self-hosted deployments—you agree to this EULA. If you do not agree, do not install or use the Software.

This EULA governs the **software license**. Use of the hosted service is governed by the **Terms of Service**, and data handling by the **Privacy Policy**.

---

## 1. License grant

Subject to your compliance with this EULA, Nexxus grants you a limited, non-exclusive, non-transferable, non-sublicensable, revocable license to install and run the Software on infrastructure you own or control, for the **internal business or personal use of any individual or company**, for the edition you are entitled to (Free or, where applicable, Enterprise under a separate Enterprise Agreement).

**Managed Service Providers.** If you use the Software to manage infrastructure for, or deliver services to, third parties (for example, as a managed-services or hosting provider), you must obtain an **Enterprise license per managed server**, priced by Nexxus Tech according to the **scope, functionalities, and time/effort** involved.

## 2. Restrictions

You will not, except as expressly permitted by this EULA or applicable law:

- **resell**, copy, distribute, sell, rent, lease, sublicense, or make the Software available to third parties as a service or product (hosted or otherwise), whether or not for a fee, except under an Enterprise Agreement that expressly permits it;
- modify, adapt, translate, or create derivative works of the Software, or reverse engineer, decompile, or disassemble it;
- remove, alter, or obscure any proprietary notices, branding, or labels;
- circumvent license, edition, or usage controls; or
- use the Software in violation of the **Acceptable Use Policy** or applicable law.

## 3. Ownership

The Software is **licensed, not sold**. Nexxus and its licensors retain all right, title, and interest in and to the Software, including all intellectual property rights. No rights are granted except as expressly stated in this EULA.

**Third-party and open-source components** included with the Software (including Docker images) are licensed under their own terms, which control for those components. Attribution and license information is in **`THIRD_PARTY_NOTICES.txt`** at the root of the installation directory (the folder containing `docker-compose.yml` after install). Regenerate or request an updated notices file from **contact@nexxus-tech.com**.

## 4. Self-hosting responsibilities

For self-hosted deployments, **you are solely responsible** for installing, configuring, securing, updating, backing up, and operating the Software and its environment, including:

- the **security of the host operating system and environment** — patching, hardening, network controls, and access management;
- deploying in a **controlled environment with controlled, least-privilege user access**;
- the database, secrets, encryption keys, and any AI provider, web source, email/SMTP, or NetScaler/Citrix ADC systems you connect; and
- maintaining your own **backups**.

Nexxus does not host, access, receive data from, or send telemetry from your self-hosted deployment.

## 5. Assistive nature

The Software is an **assistive tool** and **does not replace System Administrators or other qualified professionals**; it is intended to optimize their work. It is **not designed or intended for safety-critical, life-safety, or other high-risk use** where failure could cause death, injury, or severe damage. AI output may be inaccurate or incomplete. Confirmation prompts (for example, before potentially destructive commands) are an **assistive safety feature, not a guarantee**, and may not appear for every risky action. You must independently review and approve **every** action before it executes and are responsible for the outcome.

## 6. Data, encryption, and no recovery

Sensitive information stored by the Software (such as API keys, appliance credentials, and SMTP credentials) is **encrypted at rest**, and in self-hosted deployments the data and the encryption key remain **solely under your control**. **Nexxus is not responsible for recovering any lost data, configurations, credentials, or content.** You are responsible for your own backups and for safeguarding your encryption keys and credentials.

## 7. Third-party services, AI, and sources

The Software can connect to third-party services you configure (AI providers, web search, email/SMTP, and managed appliances). Those services are governed by their own terms and are your responsibility. By default the Software enables only the **official vendor documentation sites**; any additional URL or source you add is **at your own risk**, including the risk of prompt-injection or similar attacks. **You are responsible for data you choose to expose to public/consumer SaaS LLMs**; for sensitive workloads, prefer an Enterprise SaaS, dedicated cloud, or self-hosted LLM.

## 8. Updates; no obligation to maintain

Nexxus may, but is **not obligated to**, provide updates, patches, improvements, or support for the Free edition, and may **discontinue the Software or any feature at any time**. Support and update commitments, if any, for Enterprise editions are defined in the applicable Enterprise Agreement. Updates may be subject to this EULA unless accompanied by separate terms.

## 9. Trademarks and no affiliation

"NetScaler" and "Citrix" are trademarks of their respective owner (Cloud Software Group). "OpenAI", "Anthropic", "Claude", "Google", "Gemini", "xAI", "Grok", "DeepSeek", "Brave", and other names are trademarks of their respective owners. **Nexxus Tech and JPilot are independent and are not affiliated with, sponsored by, or endorsed by any of these companies.** Such names are used solely for identification and interoperability.

## 10. Term and termination

This EULA is effective until terminated. It terminates automatically if you breach it. Upon termination, you must stop using the Software and remove all copies in your possession or control. Sections 2, 3, 6, 9, and 11–13 survive termination.

## 11. Disclaimer of warranties

THE SOFTWARE IS PROVIDED **"AS IS" WITHOUT WARRANTY OF ANY KIND**, EXPRESS OR IMPLIED, INCLUDING MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT, TO THE FULLEST EXTENT PERMITTED BY LAW. WE DO NOT WARRANT THAT THE SOFTWARE WILL PREVENT OUTAGES, MISCONFIGURATIONS, OR SECURITY INCIDENTS.

## 12. Limitation of liability

TO THE FULLEST EXTENT PERMITTED BY LAW, NEXXUS WILL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR FOR LOSS OF PROFITS, DATA, OR GOODWILL, OR FOR DAMAGE TO OR OUTAGE OF SYSTEMS YOU CONNECT, ARISING FROM OR RELATED TO THE SOFTWARE. NEXXUS'S TOTAL AGGREGATE LIABILITY WILL NOT EXCEED THE GREATER OF THE AMOUNTS YOU PAID FOR THE APPLICABLE LICENSE IN THE **TWELVE (12) MONTHS** PRECEDING THE CLAIM OR **USD $100**.

Nothing in this EULA excludes or limits liability that **cannot be excluded or limited under applicable law**, including mandatory consumer or personal-injury rights where you are located.

## 13. Export control; governing law

You may not use or export the Software in violation of applicable export-control or sanctions laws.

**Governing law.** This EULA is governed by the laws of the **Republic of Colombia**, without regard to conflict-of-laws rules, except that mandatory laws of your country of residence or establishment may apply to the extent they cannot be waived by contract. Subject to mandatory local rules, exclusive jurisdiction and venue lie in the **competent courts of Bogotá D.C., Colombia**. For Enterprise licensees, the Enterprise Agreement controls.

## 14. Contact

**Nexxus-Tech SAS** — **Carrera 13A # 28-21, Bogotá D.C., Colombia** — **contact@nexxus-tech.com**.
