# JPilot

**JPilot** — an AI-assisted management platform for network appliances. Register NetScaler ADC (MPX/VPX), SDX, Cisco IOS/XE switches, and F5 BIG-IP; connect **your own** AI provider keys; and use JPilot chat with vendor-specific tools, prompts, and memory.

The **Free edition** is offered at no charge so teams can try the product and so practitioners can see how it works. **Nexxus-Tech SAS does not supply or pay for AI inference** — you choose the provider, you hold the API keys, and **you pay that provider** under its terms. JPilot only connects to what you configure.

Repository: [github.com/Nexxus-Tech-SAS/jpilot](https://github.com/Nexxus-Tech-SAS/jpilot)

> **Disclaimer:** JPilot is an independent project and is not affiliated with, endorsed by, or sponsored by Citrix Systems, Inc. NetScaler is a trademark of Citrix Systems, Inc.

**Current release:** `v0.46` — install-first README with per-platform sections, and in-app support contact in JPilot chat.

Bump the root [`VERSION`](VERSION) file when tagging a release so in-app update checks match GitHub.

## Install

One command downloads JPilot, generates its secrets and TLS certificate, writes `.env`,
launches the Docker stack, and opens it in your browser. Pick your platform:

### 🪟 Windows

In **PowerShell**, run:

```powershell
irm https://install.nexxus-tech.com/jpilot/ps1 | iex
```

Offers to install **Git for Windows** and **Docker Desktop** via `winget` if they're missing
(or install them yourself:
[Git](https://git-scm.com/download/win) ·
[Docker Desktop](https://docs.docker.com/desktop/install/windows-install/)).

### 🍎 macOS

In **Terminal**, run:

```bash
curl -fsSL https://install.nexxus-tech.com/jpilot | bash
```

Offers to install **git** and **Docker Desktop** for you (via Homebrew / Xcode Command Line
Tools) if they're missing.

### 🐧 Linux (Ubuntu recommended)

In a **terminal**, run:

```bash
curl -fsSL https://install.nexxus-tech.com/jpilot | bash
```

Offers to install **git** and **Docker Engine** if they're missing
(`apt`/`dnf`/`yum`/`pacman`/`zypper`/`apk` are detected automatically). Tested most on
**Ubuntu**.

> **Need help?** The installer prints its source and a support contact when it runs. If you
> get stuck, reach us at [www.nexxus-tech.com](https://www.nexxus-tech.com) or
> [support@nexxus-tech.com](mailto:support@nexxus-tech.com).

➡️ Once it runs, [finish setup in the browser](#quick-start).

## Features

- **Appliance inventory** — vendor → device → credentials wizard; **tags** for filtering; MPX, VPX, SDX, Cisco, and F5 product lines; **Beta Available** badges on SDX, Cisco, and F5; encrypted credentials (Fernet).
- **AI provider management** — OpenAI, Anthropic, Gemini, Grok, DeepSeek, LM Studio, **OpenRouter**, **Azure OpenAI**, **AWS Bedrock**, and OpenAI-compatible endpoints; assign each model to **Architect**, **Operator**, and/or **Analyst** roles; role suggestions with indicative pricing when loading models.
- **JPilot chat** — tool-calling agent bound to the selected appliance; credentials never sent to the LLM; classic UI at `/jpilot` and **Chat Beta** at `/jpilot/beta` (sidebar conversations, Diamond-style layout).
- **JPilot roles** — **Architect** (structured discovery and formal design documents), **Operator** (configure the ADC, including from attached `.md` designs), **Analyst** (read-first troubleshooting); dual-pane defaults to Architect + Operator; **Send to Operator** handoff from design deliverables; per-pane **context usage** ring (model-aware), live **generation speed** while thinking, and **Stop** while generating.
- **Architect design workflow** — choice/boolean `jpilot-form` discovery; deliverable outline with AWS/Azure, Gateway integrations, and AAA topics; downloadable design `.md` and one-click **Send to Operator** (opens pane 2 and starts implementation); official doc reference index (Citrix Gateway, authentication, Tech Zone).
- **JPilot command menu** — searchable recommended actions by role with section grouping (~200 prompts); filters to the **selected appliance vendor** (NetScaler, SDX, Cisco, F5).
- **MCP server** — Model Context Protocol tools for Next-Gen API, classic CLI over SSH, NITRO helpers, diagnostics, and SSL key/CSR generation.
- **Multi-vendor brain** — `resources/vendors/<id>/manifest.json` drives memory, prompts, tools, and connect mode; NetScaler, Cisco, SDX, and F5 BIG-IP supported today.
- **Token-optimized chat** — intent-based tool routing, slimmer Architect prompts (on-demand resource search), **model-aware** history and tool-result limits (scales with context window size).
- **Memory-guided RAG** — `backend-api/app/resources/memory/<vendor>/` gates API/CLI usage before execution.
- **Classic + Next-Gen** — list virtual servers from Next-Gen applications and classic `lbvserver`; create apps via Next-Gen or multi-step LB setup via CLI.
- **Guided load balancer forms** — JPilot can embed interactive `jpilot-form` blocks in chat (VIP, service type, backends, monitors); submissions drive CLI execution after reference lookup.
- **Smart form routing** — responder, rewrite, transform, and other policy-on-vserver requests do not trigger the LB creation form.
- **Authentication** — password login until a passkey is registered (when passkeys are enabled); optional **passkey policy** (disable / enable / enforce) under Settings → Security; failed password sign-in lockout and recovery-code attempt limits.
- **JPilot HTTPS certificate (admin)** — Settings → Security: view active nginx TLS cert, then replace via drag/drop, browse, or paste PEM; validates key match, expiry, and hostname before writing `nginx/ssl/` and reloading nginx.
- **Account recovery** — email OTP via SMTP; self-service at `/account-recovery` or admin-initiated from Users; revokes passkeys and resets password and/or registers a new passkey.
- **User management** — admin CRUD for users (roles `admin` / `user`), email for resets, initial password on create, passkey count and removal.
- **SSL certificate tools** — generate CSRs or self-signed certificates on the appliance (UI + API + MCP).
- **NetScaler diagnostics** — ICMP ping/traceroute, TCP port reachability via telnet from the appliance shell, and read-only `nsconmsg` performance/event collection.
- **Optional Brave Search** — vendor-isolated official-doc web search (Citrix/NetScaler, Cisco, or F5 domains only; Settings → AI Providers).
- **Settings → Beta features** — enable MCP tools per beta platform (SDX, Cisco IOS/XE, F5 BIG-IP) next to Next-Gen API; shared SSH settings on the Next-Gen tab.
- **Dashboard shortcuts** — recommended JPilot prompts and links (health summary, list IPs/vservers, diagnostics, guided LB).
- **Model usage dashboard** — Settings → AI Providers shows monthly LLM token/request usage and Brave Search query usage with progress bars (tracked locally per calendar month).
- **Cisco IOS/XE (SSH)** — Architect, Operator, and Analyst over SSH with `search_cisco_cli_reference` memory gate (beta).
- **NetScaler SDX (SSH)** — Operator and Analyst for SVM platform and VPX lifecycle with `search_sdx_cli_reference` memory gate (beta).
- **F5 BIG-IP (SSH / TMSH)** — Operator, Analyst, and Architect (official F5 docs only); `f5_*` MCP tools and `search_f5_tmsh_reference` / `search_f5_documentation` (beta).
- **Nexxus licensing** — Settings → **License**: enter a license code, import an offline `.lic` file, or sync with the Nexxus licensing API; installation fingerprint binding; encrypted payload validation; daily background sync and expiry enforcement; **activation gate** redirects unlicensed or expired installs to Settings → License before using the app.

## What's new in v0.46

| Area | Highlights |
|------|------------|
| **Install-first README** | The one-line installer now leads the README (right under the intro), with clear per-platform sections — 🪟 Windows, 🍎 macOS, 🐧 Linux (Ubuntu recommended) — so new users can get started immediately. |
| **In-app support** | The JPilot chat empty state now shows a **Need help?** line linking [support@nexxus-tech.com](mailto:support@nexxus-tech.com) and [nexxus-tech.com](https://www.nexxus-tech.com), so users can reach support without leaving the app. |
| **Clickable contact** | Support email is now a `mailto:` link everywhere it appears in the docs. |

## What's new in v0.45

| Area | Highlights |
|------|------------|
| **Transparent installer** | The bootstrap scripts now open with a provenance banner: publisher (Nexxus-Tech SAS), the exact source repo/branch JPilot is downloaded from, and a link to read the script before running it. |
| **Disclosed auto-installs** | Before installing git or Docker, the prompts name the exact source (winget official packages, your distro's package manager, `get.docker.com`, or Homebrew), warn that **Administrator (UAC) / sudo** rights may be required, and link the manual install as an alternative. |
| **Support contact** | Every run prints how to reach us — [www.nexxus-tech.com](https://www.nexxus-tech.com) or [support@nexxus-tech.com](mailto:support@nexxus-tech.com) — if you need help or hit trouble. |

## What's new in v0.44

| Area | Highlights |
|------|------------|
| **Branded install URLs** | One-liners now use the short, branded endpoint: `curl -fsSL https://install.nexxus-tech.com/jpilot \| bash` (macOS/Linux) and `irm https://install.nexxus-tech.com/jpilot/ps1 \| iex` (Windows), proxied to the canonical `get.sh` / `get.ps1`. |
| **Windows installer fix** | `get.ps1` no longer closes the PowerShell window silently when a prerequisite check fails under `irm \| iex`. Errors now pause (**Press Enter to close**) when interactive so the message stays readable; automated/CI runs are unaffected. |
| **Auto-install git** | When git is missing, the installer now offers to install it for you — `winget` on Windows, Homebrew / Xcode CLT on macOS, and apt/dnf/yum/pacman/zypper/apk on Linux — matching the existing Docker auto-install. |

## What's new in v0.43

| Area | Highlights |
|------|------------|
| **Command menu** | Recommended-actions dialog scrolls correctly on desktop and mobile — all sections and actions are reachable (PrimeVue dialog flex/overflow fix). |
| **Chat Beta (mobile)** | Full-screen chat on narrow layouts; **Chats** drawer to switch or create conversations; page toolbar and background picker hidden on mobile; compact message markdown. |
| **Auto role switching** | Picking a recommended action switches Architect / Operator / Analyst to match; free-text messages infer the best role with an inline notice (e.g. design work → Architect). |
| **Mobile footer** | Single-line legal link: **© year Nexxus Tech · Terms & legal** → `/legal`. |
| **Slack notifications** | Settings → **Slack** (Enterprise Pro): configure incoming webhook, choose events, and send a test message. |
| **Plans page** | Refreshed early-access layout with mobile plan tabs and updated copy. |

## What's new in v0.42

| Area | Highlights |
|------|------------|
| **Installer TLS UX** | Custom certificate step supports **drag-and-drop**, **Browse file**, and paste for certificate, private key, and optional CA chain; auto-routes keys/certs to the correct field and splits full-chain PEMs. |

## What's new in v0.41

| Area | Highlights |
|------|------------|
| **JPilot Chat Beta** | New **Chat Beta** under JPilot Chat (`/jpilot/beta`): Diamond-style sidebar, multiple conversations (up to 12), delete per thread, Architect→Operator handoff into beta sessions. Classic chat at `/jpilot` unchanged. |
| **Routes** | `/copilot` and `/copilot/beta` redirect to `/jpilot` and `/jpilot/beta`. |
| **Chat persistence** | Message history stored in **localStorage** (migrated from sessionStorage) so tabs and browser restarts keep conversations. |
| **HTTPS certificate UI** | Admins replace the **nginx** UI certificate from Settings → Security: status view by default, optional replace flow with validate + apply; PEM drag/drop and file browse; automatic nginx reload via shared Docker volume. |
| **TLS docs** | [nginx/ssl/README.md](nginx/ssl/README.md) rotation guide; README manual-setup section for host-side replacement. |
| **Command menu** | Ask JPilot recommended-actions dialog uses full width on desktop (no compressed results column). |

## What's new in v0.40

| Area | Highlights |
|------|------------|
| **Architect → Operator handoff** | **Send to Operator** on completed design documents; opens the Operator pane and starts implementation with the `.md` attached (no manual download step). |
| **Live generation metrics** | Chat streams progress over SSE — elapsed time, phase labels (model vs tools), and **tok/s** after each model round. |
| **AI providers** | **OpenRouter**, **Azure OpenAI**, and **AWS Bedrock**; model picker shows indicative **cost**; colorful **role suggestions** when loading models. |
| **Model-aware context** | History message count and tool-result truncation scale with the selected model’s context window; context ring tooltip shows limits. |
| **Passkey policy** | Admins set platform policy under Settings → Security: **Disable**, **Enable** (recommended), or **Enforce** passkeys. |
| **Command menu UX** | Browse recommendations sidebar no longer overlaps results in the Ask JPilot dialog. |

## What's new in v0.39

| Area | Highlights |
|------|------------|
| **Web installer launch** | After **Install JPilot**, the setup tab shows a progress bar and plain-language status while Docker builds; **keep this tab open**. |
| **Ready before open** | The wizard polls until JPilot responds on `/api/health`, then **redirects automatically** — no more broken “page not found” on first boot. |
| **Bootstrap URLs** | `get.sh` / `get.ps1` use canonical `Nexxus-Tech-SAS` org casing so `raw.githubusercontent.com` serves the current installer. |

## What's new in v0.38

| Area | Highlights |
|------|------------|
| **Repository** | Canonical home is [github.com/Nexxus-Tech-SAS/jpilot](https://github.com/Nexxus-Tech-SAS/jpilot); bootstrap scripts (`get.sh` / `get.ps1`) and in-app update checks point here. |
| **Docker naming** | Compose project name is `jpilot` (images/containers like `jpilot-frontend`, volume `jpilot_mongodb_data`) instead of `nsagent`. Fresh installs do not overwrite old `nsagent_*` volumes. |
| **Installer admin** | Choose any bootstrap username; **email is required** and written to `ADMIN_EMAIL` for password recovery after install. |
| **Installer legal** | Review step requires accepting Terms, Privacy, AUP, and EULA; legal docs open in the setup wizard. |
| **Installer branding** | JPilot favicon and Nexxus Tech full logo in the wizard; help links to [nexxus-tech.com](https://www.nexxus-tech.com). |

## What's new in v0.37

| Area | Highlights |
|------|------------|
| **Full screen** | Toggle in the desktop sidebar (next to theme) and mobile drawer menu; icon and label sync with browser full-screen state. |

## What's new in v0.36

| Area | Highlights |
|------|------------|
| **Dark mode nav** | Sidebar and mobile drawer use light pills with dark text on hover and when selected (readable on dark backgrounds). |
| **Mobile top bar** | Black bar in dark theme via global CSS overrides (fixes `--p-surface-50` staying light). |
| **Mobile drawer** | **JPilot** label in menu header; router active-state fix so Dashboard is not always highlighted. |
| **JPilot recommendations** | On phones, inline results hidden — open via **Browse recommended actions…**; dialog layout fixed so role tabs and category chips no longer overlap results. |

## What's new in v0.35

| Area | Highlights |
|------|------------|
| **Mobile top bar** | Full-width layout with iPhone safe-area support; JPilot logo centered; hamburger button visible in dark mode. |
| **Mobile drawer** | Full-width menu on phones; active item uses light pill with dark text in dark theme (matches desktop sidebar). |
| **Layout** | Flex shell fixes content overlap on small screens (`100dvh`, no sticky overlap). |

## What's new in v0.34

| Area | Highlights |
|------|------------|
| **Branding** | New JPilot logo component with light/dark variants (`JPilot-logo-big.svg` / `JPilot-logo-big-black.svg`); favicon (`jpilot-favicon.png`); installer setup page updated to match. |
| **Mobile layout** | Responsive shell: sticky top bar with menu drawer on small screens; desktop left sidebar unchanged at ≥992px. |
| **SSL tools** | Certificate UI copy uses **Appliance** / **ADC** instead of NetScaler-specific labels. |

## What's new in v0.33

| Area | Highlights |
|------|------------|
| **Login lockout** | After 5 failed password attempts per username, sign-in is blocked for 15 minutes (`429`); counter clears on successful login. |
| **Recovery codes** | Emailed codes are now 8 alphanumeric characters (larger search space than 6-digit numeric). |
| **Recovery attempts** | Five wrong guesses invalidate the active code; user must request a new one. |
| **nginx** | Stricter per-IP rate limit on `POST /api/auth/password-reset/confirm` (3 requests/minute). |

## What's new in v0.32

| Area | Highlights |
|------|------------|
| **License gate** | Router guard sends unactivated, expired, deactivated, or missing licenses to **Settings → License**; after successful activation, users return to their original destination. |
| **License (Settings)** | Two-column layout: activation on the left, **License information** on the right; **Licensed for** block (name, email, company or Personal Use); masked license code with reveal and **copy** actions. |
| **Plan-themed UI** | License info panel and **Plans** page use plan colors (Free green, Trial orange, Enterprise blue, Enterprise Pro purple); Plans highlights the current plan from the saved license. |
| **Activation flow** | Registration form and offline import hide once a license is saved; **Remove license** restores the full activation flow. |

## What's new in v0.31

| Area | Highlights |
|------|------------|
| **License (Settings)** | New **License** panel: save a `XXXX-XXXX-XXXX-XXXX` code, **Import offline license** (`.lic`), view status, type, expiry, and holder details. |
| **Online sync** | On startup and daily, JPilot POSTs to Nexxus `/licensing/sync` with `appFingerprint`, `appName`, and license code; persists `expirationDate`, `registrationDate`, `validityDays`, `licenseType`, `renewalCount`, and `encryptedLicense` in MongoDB. |
| **Encrypted payload** | Decrypts `encryptedLicense` with HKDF-SHA256 + AES-256-GCM; prefers signed bundle fields when they differ from top-level sync JSON. |
| **Sync outcomes** | Handles active/renewed (200), expired/deactivated (403), missing license (404), and code mismatch; local expiry check after each successful sync. |
| **Configuration** | Optional `NEXXUS_LICENSING_BASE_URL` and `LICENSE_SYNC_INTERVAL_SECONDS` in `.env` (see `.env.example`). |
| **Bootstrap admin** | Docs clarify installer-written `ADMIN_USERNAME` / `ADMIN_PASSWORD` (seed once; leave blank afterward). |

## What's new in v0.30

| Area | Highlights |
|------|------------|
| **Recommended actions** | Command menu shows only prompts for the **selected appliance vendor**; **15** starter actions each for SDX, Cisco IOS/XE, and F5 BIG-IP (plus Cisco Architect design prompts). |
| **Background chat** | JPilot keeps generating when you leave the pane or navigate away; **toast + sound** when the reply finishes (Settings → JPilot → Reply notifications); sidebar dot while a pane is busy. |
| **Architect discovery** | F5 and Cisco Architect roles use **`jpilot-form`** discovery (no checklist loops); server nudge when the model skips forms; **go** produces the design document from chat history. |
| **Cisco Architect** | New `architect.md` / `architect_discovery.md` prompts (fixes missing role prompt error). |
| **CLI memory fix** | Restored `MEMORY_CANDIDATE_PATHS` for the NetScaler CLI command index (fixes Operator form execution after CS/LB submissions). |

## What's new in v0.29

| Area | Highlights |
|------|------------|
| **About JPilot** | **Beta** tag displayed next to the installed version in Settings → Updates (toggle via `frontend/src/config/product.js`). |

## What's new in v0.28

| Area | Highlights |
|------|------------|
| **AI provider roles** | Settings → AI Providers: assign each LLM to Architect, Operator, and/or Analyst (icon + checkbox per role). Chat shows provider **names** only and auto-picks the role-matched model. |
| **Context usage ring** | Each chat pane shows an estimated **context %** (Cursor-style) with green / amber / red thresholds and a hover breakdown. |
| **Stop generation** | **Stop** in the toolbar, thinking bubble, and input bar cancels in-flight chat; backend stops between tool/LLM iterations when the client disconnects. |
| **Role-aware appliances** | **Architect** — all inventory appliances (optional reference, no connect required); **Operator** / **Analyst** — **NetScaler only**; beta vendors show a **Beta** tag. Inventory and chat lists show **name (vendor)**. |
| **Cisco chat fixes** | Correct vendor context when switching appliances; Cisco static-route memory; operator prompt forbids NetScaler syntax on IOS/XE devices. |
| **Stability** | Fix missing `copilot_vendor_is_supported` import that blocked Operator/Analyst chat; copilot appliance list returns full inventory. |

## What's new in v0.27

| Area | Highlights |
|------|------------|
| **F5 BIG-IP** | Vendor `f5`: TMSH over SSH (`f5_*` MCP tools), memory, Operator/Analyst/Architect prompts, manifest, and memory gate for destructive TMSH ops. |
| **Beta features settings** | Settings → **Beta features** tab (after Next-Gen API): per-platform tool toggles, doc links, enable/disable all for SDX, Cisco, and F5. |
| **Vendor-isolated web search** | Brave results scoped per vendor (`vendor_doc_domains.py`); Cisco and F5 CLI/doc search use only official vendor domains; Citrix/NetScaler extras unchanged. |
| **UI** | **Beta Available** tags on SDX, Cisco IOS/XE, and F5 in Add appliance and Vendor support; Brave Search panel shows locked domains per vendor. |

## What's new in v0.26

| Area | Highlights |
|------|------------|
| **License** | Root `LICENSE` is proprietary (Nexxus-Tech SAS); Free edition remains available under the EULA and Terms; third-party OSS stays in `THIRD_PARTY_NOTICES.txt`. |
| **Legal** | Updated EULA, Terms, Privacy, and AUP: Commercial Agreement for paid/Enterprise use, expanded trademark notices, BYOK AI and token costs on the user, contact as Nexxus Tech SAS Colombia, liability cap in COP. |
| **Product naming** | JPilot as the product name in legal docs and installer defaults (NSAgent retired as public codename). |
| **README** | Free edition and bring-your-own AI keys documented at the top and in the License section. |

## What's new in v0.25

| Area | Highlights |
|------|------------|
| **NetScaler SDX** | Vendor `sdx`: MCP `sdx_*` tools, SVM memory file, Operator/Analyst prompts, manifest, and memory gate for destructive VPX ops. |
| **Add appliance UX** | Stepped flow: vendor → device (Available / Coming soon) → details; Citrix MPX and VPX as separate products; single **Add appliance** button. |
| **Inventory tags** | Optional `tags[]` on appliances; tag chips in the table; click-to-filter bar above inventory. |
| **Product line** | Optional `productId` on appliances (e.g. `netscaler-mpx` vs `netscaler-vpx`) for accurate Platform labels. |
| **Vendor support** | Roadmap panel in its own section below the inventory table (not nested in the DataTable panel). |

## What's new in v0.24

| Area | Highlights |
|------|------------|
| **Vendor manifests** | `resources/vendors/{netscaler,cisco}/manifest.json` — single source of truth for tools, memory, prompts, connect mode, and roles (`vendor_registry.py`). |
| **Brain layout** | `memory/<vendor>/`, `prompts/<vendor>/roles/`, `architect/<vendor>/`; prod bind-mounts all of `resources/`. |
| **Prompts as files** | Live system prompts loaded from markdown with `{{include:…}}` fragments; `search_jpilot_architect_resources` for Architect outline on demand. |
| **Token optimization** | `copilot_tool_router.py` sends a subset of tools per intent; Architect prompt slimmed (~3k vs ~15k+ chars). |
| **Cisco switches** | MCP tools `cisco_*`, memory `cisco_ios_switch_memory.md`, Operator/Analyst prompts, SSH connect test, inventory `copilotEligible`. |
| **Tests** | Vendor registry, prompt loader, and tool router unit tests. |

## What's new in v0.23

| Area | Highlights |
|------|------------|
| **Architect** | One-topic discovery via `jpilot-form` (`choice` and boolean fields); design document outline (AWS, Azure autoscale, Gateway + Citrix integrations, Gateway AAA); `<!-- jpilot-design-document -->` marker and **Download design document** in chat. |
| **Operator** | Implement attached `.md` designs on the connected appliance using forms instead of prose questionnaires (`Configuration inputs for:`). |
| **Analyst** | Renamed from Investigator (`analyst` role id; legacy alias preserved). |
| **Command menu** | `AskJpilotCommandMenu` with tabs, filters, and section headers; expanded recommended actions for Architect, Operator, and Analyst. |
| **Chat errors** | Clear messages for 504/timeouts, quota exhaustion, and context limits; backend `httpx` timeouts return structured 504 detail. |
| **Nginx** | `/api/` proxy read/send timeouts increased to 300s for long JPilot turns. |
| **Settings** | Attach `.md` / `.markdown` design files in JPilot settings. |
| **Docs domains** | `community.citrix.com` (Tech Zone) allowed for web search and citations. |

## What's new in v0.22

| Area | Highlights |
|------|------------|
| **Passkey login** | Cross-device sign-in for passkey-only accounts: hybrid transport hints on the server, a **Sign in from your phone** panel under the passkey button, and auto-start of the QR flow once terms are accepted. |
| **WebAuthn API** | `POST /auth/webauthn/login/begin` accepts optional `preferCrossDevice` to prioritize the browser’s QR / phone passkey dialog. |

## What's new in v0.21

| Area | Highlights |
|------|------------|
| **Settings → MCP Server** | MCP status (URL, tools, message) lives inside the MCP Server panel instead of a separate row below MCP/SMTP. |

## What's new in v0.20

| Area | Highlights |
|------|------------|
| **About / updates** | When an update is available, GitHub release notes render in a side panel next to the upgrade instructions (fetched from the latest release). |

## What's new in v0.19

| Area | Highlights |
|------|------------|
| **About / updates** | Upgrade steps and `./scripts/upgrade.sh` / `upgrade.ps1` commands show only when a newer release is available. |
| **Settings** | Security, Legal, and About use full-width layout like other sections. |

## What's new in v0.18

| Area | Highlights |
|------|------------|
| **Settings layout** | AI Providers: documentation web search and model usage side by side. MCP Server and SMTP / Email side by side with a two-column SMTP form. Directional slide when changing tabs (left/right follows nav order). |
| **Page chrome** | Removed redundant page titles on Settings, JPilot, and Appliances. |
| **Dashboard** | Platform status tags in one row. |
| **Shell** | Main content height matches the sidebar; legal footer aligns with the bottom of the menu. |

## What's new in v0.17

| Area | Highlights |
|------|------------|
| **upgrade script** | After `git pull origin main`, pick **one** stack to rebuild: `1` development, `2` production, or `q` to skip. No more separate yes/no prompts for both stacks. |

## What's new in v0.16

| Area | Highlights |
|------|------------|
| **Deploy scripts** | `./scripts/prod-up.sh` — production `build` + `up -d` from repo root. `./scripts/upgrade.sh` — `git pull origin main`, then choose dev **or** prod to rebuild. PowerShell equivalents included. |

## What's new in v0.15

| Area | Highlights |
|------|------------|
| **Docker Compose** | Dev: `docker compose up -d --build` (no profiles). Prod: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`. Production overlay removes the Vite `frontend` service via compose merge. |
| **Dashboard** | Smaller welcome panel; removed page title/subtitle; appliances + AI providers stacked left, quick actions + platform status right; blog carousel pinned above the legal footer (duplicate marketing footer removed). |
| **Plans** | Removed page title/subtitle; plan cards first; compact platform highlights in a 2×3 grid (left two-thirds) beside **Need Enterprise?** (right one-third). |

## What's new in v0.14

| Area | Highlights |
|------|------------|
| **JPilot layout** | Copilot page height accounts for shell padding and main-content bottom spacing (`calc(100vh - 5rem)`); `overflow: hidden` prevents page scroll. |
| **Dashboard & Plans** | `@media (max-height: 900px)` compacts welcome/hero spacing, grids, marketing blog cards, and plan cards so Dashboard and Plans fit 1080p and iPad Pro 13″ landscape without scrolling past the footer. |

## What's new in v0.13

| Area | Highlights |
|------|------------|
| **Production compose** | `docker-compose.prod.yml` is an **overlay** on `docker-compose.yml` (use both `-f` flags or `./compose.sh` with `NSAGENT_DEPLOY_MODE=prod`). Clears dev bind mounts, removes the Vite frontend service, and serves the built UI from nginx. |
| **Startup order** | MCP and backend healthchecks; API waits for healthy MongoDB **and** MCP before starting; nginx waits for a healthy backend. |
| **MCP URL migration** | Stored MCP settings that point at `localhost` are rewritten to `http://mcp-server:8001` on startup (fixes MCP calls from inside Docker). |
| **MongoDB connect** | Backend verifies MongoDB with an admin `ping` and a 5s server-selection timeout during startup. |

## What's new in v0.12

| Area | Highlights |
|------|------------|
| **JPilot roles** | **Architect** (plan without a connected appliance), **Operator** (configure the ADC), **Analyst** (read-first troubleshooting). Icon `SelectButton` per chat pane; dual-pane layout defaults to Architect + Operator. `GET /api/copilot/roles`. |
| **Architect fixes** | No false “no changes applied” banner or auto LB creation form when planning changes on an existing vserver (e.g. secure headers on `lb_01`). |
| **Settings** | Fixed `KeepAlive` template structure so Settings tabs cache correctly without a Vue compile error. |
| **MongoDB (prod)** | Pin `mongo:8.2`, `restart: unless-stopped`, healthcheck; `backend-api` / `mcp-server` wait for healthy MongoDB. |
| **nginx** | Separate **login** zone (`10r/m`) for `POST /api/auth/login`; **contact** zone (`5r/m`) for recovery and other `/api/auth` paths. |

## What's new in v0.11

| Area | Highlights |
|------|------------|
| **Auth** | nginx `/api/auth` rate limit raised from 5 to **15 requests/minute** (burst 15) for login, passkey, and recovery flows. |

## What's new in v0.10

| Area | Highlights |
|------|------------|
| **Fix** | Settings sections cached with `KeepAlive` so switching tabs no longer remounts panels and refetches `/api/ai-providers`, platform settings, and usage dashboard on every visit. |
| **Fix** | Production nginx API rate limit aligned with dev (`30r/s`, burst 60) — fixes 503 errors when jumping between Settings tabs (was `20r/m` in prod templates). |
| **UI** | Login page visual refresh (animated background, scroll-in animations). |
| **UI** | Global page fade transitions on route changes. |

## What's new in v0.09

| Area | Highlights |
|------|------------|
| **Settings UX** | Tabs grouped as Platform, People, Personal, and App; setup-first order (AI Providers → JPilot → MCP → Next-Gen → Users → Security → About → Legal). |
| **Naming** | Settings tab renamed from Chat to JPilot. |

## What's new in v0.08

| Area | Highlights |
|------|------------|
| **Fix** | Dev stack mounts `VERSION` at `/usr/share/jpilot/VERSION` so it no longer conflicts with the `./backend-api:/app` bind mount. |

## What's new in v0.07

| Area | Highlights |
|------|------------|
| **Updates** | Settings → About checks GitHub for new versions; banner when an update is available; copy-paste rebuild instructions for macOS/Linux and Windows. |
| **Versioning** | Root `VERSION` file baked into the backend; compares against GitHub tags (falls back when no GitHub Release is published). |
| **Deploy modes** | Installer lets you pick production (compiled) or development (hot reload); `compose.sh` / `compose.ps1` pick the right stack from `.env`. |
| **Production stack** | `docker-compose.yml` + `docker-compose.prod.yml` overlay — compiled frontend in nginx, no dev bind mounts on API services. |

## What's new in v0.06

| Area | Highlights |
|------|------------|
| **Settings hub** | Single Settings page with tabs: MCP Server, Chat, AI Providers, Next-Gen API, Security, Legal. |
| **AI Providers** | LLM provider CRUD and Brave Search (visually separate from LLMs) moved from the main menu; usage dashboard lives in the same tab. |
| **Next-Gen API** | Connection and reference panel moved to Settings → Next-Gen API (`/next-gen-api` redirects). |
| **NetScalers** | SSL Certificate Tools moved to NetScalers → SSL Certificates tab (`/ssl-csr` redirects). |
| **Navigation** | Slimmer sidebar: Dashboard, JPilot, NetScalers, Settings (+ Users for admins). |
| **MCP catalog** | Settings tool list synced with server — Next-Gen request, diagnostics, telnet, nsconmsg, CSR generation. |
| **Performance** | nginx API rate limit raised (`30r/s`, burst 60) to prevent 503s when Settings loads multiple endpoints. |
| **Fixes** | Settings lazy-loads section data on tab switch; route redirects for moved pages. |

## What's new in v0.05

| Area | Highlights |
|------|------------|
| **JPilot forms** | `ChatConfigForm` in chat; backend parses `jpilot-form` JSON; default classic LB form when creating vservers; workload-aware defaults (StoreFront, Delivery Controllers). |
| **Form heuristics** | LB form only for real provisioning requests — not responder/rewrite/redirect/bind-to-existing-vserver work. |
| **Memory gates** | `search_netscaler_nextgen_api` required before Next-Gen inventory tools; `search_netscaler_cli_reference` before SSH/CLI writes; destructive ops need `confirmed=true`. |
| **Orchestrator** | Stronger tool-execution nudges, retry hints, discovery vs config-change detection, improved tool traces in the UI. |
| **CLI reference** | Command index, expanded catalog, richer memory search and recommended commands for JPilot. |
| **System info** | Firmware/version via NITRO `nsversion` when Next-Gen summary is incomplete. |
| **SSL tools** | `POST /ssl/generate-csr`, MCP CSR/self-signed generation on appliance via OpenSSL shell. |
| **Auth** | User email field, admin-triggered reset codes, public reset-password page. |
| **AI providers** | Grok (xAI), DeepSeek, LM Studio, OpenAI-Compatible with in-app setup hints. |
| **UI** | Dashboard actions, SSL CSR page, pricing/plans view, login/reset flows, session and chat polish. |

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────────┐
│  Vue 3 UI   │────▶│  Backend API │────▶│ MCP Server  │────▶│ NetScaler ADC    │
│  (5173)     │     │  FastAPI     │     │  (8001)     │     │ Next-Gen / SSH   │
└─────────────┘     └──────┬───────┘     └─────────────┘     └──────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  MongoDB    │
                    └─────────────┘
```

| Service      | Port  | Role                                      |
|--------------|-------|-------------------------------------------|
| Frontend     | 5173  | Vue 3 + PrimeVue admin UI and JPilot     |
| Backend API  | 8000  | Auth, CRUD, JPilot orchestration, MCP proxy |
| MCP Server   | 8001  | NetScaler tool execution (SSE-capable)    |
| MongoDB      | 27017 | Settings, appliances, AI providers, users |

## Prerequisites

- Docker and Docker Compose
- NetScaler ADC with **Next-Gen API** enabled (`enable ns nextgenapi`) for API tools
- SSH access to the appliance for classic CLI and diagnostic tools (port 22)
- SMTP server (optional, for password reset emails)

## Quick start

Run the one-liner for your platform from [Install](#install) above. The script checks for
Docker (offering to install it if absent), downloads JPilot, and starts the setup wizard.
Then:

1. Open **https://localhost:9443** (the installer uses a self-signed certificate, so
   accept the one-time browser warning).
2. Complete the wizard: admin account (username, email, password), domain, **deploy mode**
   (production or development), and TLS (self-signed or your own cert — drag/drop, browse, or paste PEM).
3. On **Review**, accept the legal terms, then **save the generated `NSAGENT_ENCRYPTION_KEY`** — it is
   required to restore or migrate the install and cannot be recovered.
4. Click **Install JPilot**. **Keep the setup tab open** — a progress bar runs while Docker
   builds; your browser opens JPilot automatically once the stack is ready (first boot is
   often 1–3 minutes).
5. Sign in at **https://&lt;your-domain&gt;** with the admin account you created.

> **Clone manually instead?** `git clone https://github.com/Nexxus-Tech-SAS/jpilot.git` then
> `cd jpilot` and run `./install.sh` (macOS/Linux) or `.\install.ps1` (Windows). If you already
> have a checkout, skip the one-liner and run the installer from the project root.

> **Need help?** The installer prints its source and a support contact when it runs. If you get
> stuck, reach us at [www.nexxus-tech.com](https://www.nexxus-tech.com) or
> [support@nexxus-tech.com](mailto:support@nexxus-tech.com).

To reconfigure an existing install (overwrites `.env`):

```bash
./install.sh --reconfigure      # macOS / Linux
.\install.ps1 -Reconfigure      # Windows (PowerShell)
```

> The installer generates `NSAGENT_ENCRYPTION_KEY` (Fernet) and `JWT_SECRET_KEY`
> automatically and derives the WebAuthn, CORS, and API-URL settings from the domain
> you choose. See [Manual setup](#manual-setup-advanced) below if you prefer to
> configure `.env` by hand.

After first login:

   - **NetScalers** — add your appliance (name, host, API/SSH user and password); **SSL Certificates** tab for CSR/self-signed generation.
   - **Settings → AI Providers** — add an LLM provider, set default, configure optional Brave Search, and view usage.
   - **Settings → MCP Server** — tool toggles, **SSH fallback** (required for diagnostics and SSL shell), SMTP, timeouts.
   - **Settings → Next-Gen API** — test Next-Gen connection and browse API reference.
   - **Settings → Security** — register an optional passkey after password login.
   - **Users** (admin) — create users with email (for password reset) and initial passwords.
   - **JPilot** — select an appliance and ask questions or request changes.

### Manual setup (advanced)

Prefer to configure things by hand instead of the wizard? You can:

1. **Generate an encryption key**

   ```bash
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. **Configure environment** — `cp .env.example .env` and edit:

   | Variable                 | Description                          |
   |--------------------------|--------------------------------------|
   | `NSAGENT_ENCRYPTION_KEY` | Fernet key for appliance credentials |
   | `JWT_SECRET_KEY`         | Secret for session JWTs              |
   | `ADMIN_USERNAME`         | Bootstrap admin (installer sets; leave blank after) |
   | `ADMIN_PASSWORD`         | Bootstrap password (installer sets; leave blank after) |
   | `ADMIN_EMAIL`            | Bootstrap admin email for password recovery (installer sets; leave blank after) |
   | `NSAGENT_DEPLOY_MODE`    | `prod` (compiled, default) or `dev` (hot reload) |
   | `NGINX_HOSTNAME`         | Public hostname for nginx TLS        |
   | `NEXXUS_LICENSING_BASE_URL` | Nexxus licensing API base (optional; default in config) |
   | `LICENSE_SYNC_INTERVAL_SECONDS` | Background license sync interval (default `86400`) |
   | `WEBAUTHN_RP_ID`         | WebAuthn RP ID (usually your hostname or `localhost`) |
   | `WEBAUTHN_ORIGIN`        | Exact UI origin (e.g. `https://your-domain`) |
   | `CORS_ORIGINS`           | Comma-separated allowed browser origins |
   | `SMTP_*`                 | Optional — required for email password reset |
   | `PASSWORD_RESET_LOG_CODES` | Dev only: log reset codes to backend logs |

3. **Provide TLS certificates** — place `cert.crt` and `cert.key` in `nginx/ssl/`
   (see [nginx/ssl/README.md](nginx/ssl/README.md)). nginx will not start without them.

4. **Start the stack** — `./compose.sh up --build` (reads `NSAGENT_DEPLOY_MODE` from `.env`), then open `https://<NGINX_HOSTNAME>`.

### Replace the JPilot UI SSL certificate (nginx)

HTTPS for the JPilot web UI is terminated by the **nginx** container. Certs are **host files**
mounted at `nginx/ssl/cert.crt` and `nginx/ssl/cert.key` (or `SSL_CERTS_PATH` from `.env`) — they
survive image rebuilds and `git pull`.

**Quick rotation:** back up the existing PEMs, install the new `cert.crt` (full chain) and
`cert.key`, then reload nginx without restarting the whole stack:

```bash
./compose.sh exec nginx nginx -s reload
```

**Wizard path:** `./install.sh --reconfigure` (or `.\install.ps1 -Reconfigure`) and choose a
custom certificate; the installer validates PEMs and rewrites `nginx/ssl/`.

Full steps (verification, rollback, WebAuthn/CORS notes): [nginx/ssl/README.md](nginx/ssl/README.md#replacing-the-certificate-rotation).

**Settings UI (admin):** **Settings → Security → JPilot HTTPS certificate** — paste certificate and
private key PEMs, validate (key match, expiry, hostname), then replace. nginx reloads automatically
when the stack mounts the shared TLS volume (Docker Compose default).

## Authentication

| Flow | Description |
|------|-------------|
| **Password login** | `POST /auth/login` — allowed only while the user has **no** registered passkeys; **5 failed attempts** per username triggers a **15-minute** lockout (`429`). |
| **Passkey login** | Required once a passkey exists; `POST /auth/webauthn/login/begin\|finish`. |
| **Passkey registration** | Authenticated users register in **Settings → Security** (email required on the account). |
| **Account recovery** | `POST /auth/account-recovery/request` (self-service) or admin from **Users**; user completes at `/account-recovery` via `POST /auth/password-reset/confirm` (8-character emailed code, **5** wrong guesses invalidate the code; removes passkeys; optional new password; optional short-lived token to register a new passkey). |
| **Bootstrap admin** | Installer writes `ADMIN_USERNAME` / `ADMIN_PASSWORD` to `.env` once; API seeds MongoDB on first startup. Leave blank in `.env` afterward — login uses the DB. |

WebAuthn and CORS origins must match how users open the UI (see `.env.example`).

## JPilot behavior

The orchestrator enforces:

1. **`search_netscaler_nextgen_api`** before Next-Gen API tools (returns blocked JSON if skipped).
2. **`search_netscaler_cli_reference`** before SSH/CLI write tools.
3. **Tool execution** for config changes — the model must call `netscaler_run_cli_command` or `netscaler_run_cli_commands`, not only list commands.
4. **Confirmation** for destructive CLI/API operations (`rm`, `DELETE`, `unbind`, etc.) via `confirmed=true` after user approval.
5. **Diagnostics run immediately** — no memory search required for ping, traceroute, TCP port checks, or nsconmsg.
6. **Guided LB forms** — for new classic LB vserver requests, JPilot may show an in-chat form; policy work (responder, rewrite, bind-to-existing vserver) does not use that form.

### Connectivity and diagnostics routing

| User question | Tool | Notes |
|---------------|------|-------|
| Can the appliance ping / reach host (no port)? | `netscaler_run_diagnostic` | `operation`: `ping`, `ping6`, `traceroute`, `traceroute6` |
| Is port N open on host? / reach `IP:PORT`? | `netscaler_telnet` or `netscaler_run_diagnostic` | `operation`: `tcp_port`, plus `port` |
| Performance stats, counters, event logs | `netscaler_collect_nsconmsg` | Read-only `/netscaler/nsconmsg` over SSH |

**Auto TCP port check:** when a JPilot message includes a host and port (e.g. `192.168.20.36:1234`), the backend runs `netscaler_telnet` automatically and returns the verdict — no need for the LLM to choose the tool.

**NetScaler ADC note:** TCP port checks use `/usr/bin/telnet` via `shell sh -c 'telnet HOST PORT </dev/null'`. NetScaler does not ship `nc`/netcat or GNU `timeout`. The CLI may append `ERROR: Export failed` after shell commands; ignore that when telnet output shows `Connected to` or `Connection refused`.

Example — classic LB virtual server with service group:

```text
add lb vserver webserver_02 HTTP 192.168.20.227 80
add serviceGroup webserver_02_sg HTTP
bind serviceGroup webserver_02_sg 192.168.20.36 5173
bind lb vserver webserver_02 -serviceGroupName webserver_02_sg
save ns config
```

JPilot runs these via **`netscaler_run_cli_commands`** in one tool call after CLI reference lookup (often after the user submits a guided form).

### In-chat configuration forms

JPilot may reply with a short intro and a fenced `jpilot-form` JSON block. The UI renders fields (text, number, select, boolean, textarea). On submit, values are sent back as `Configuration inputs for: …` and the agent executes CLI with those values.

The backend also attaches a default classic LB form when the user clearly asks to **create** a load balancer / lb vserver and the model omitted the form — but **not** for responder, rewrite, transform, redirect, or bind/apply-to-existing-vserver requests.

## MCP tools

### Configuration and inventory

| Tool | Description |
|------|-------------|
| `netscaler_test_connection` | Next-Gen API login test |
| `netscaler_get_system_info` | Management IP, version, hostname, serial |
| `netscaler_list_applications` | Next-Gen applications only |
| `netscaler_list_virtual_servers` | Next-Gen apps + classic NITRO `lbvserver` |
| `netscaler_list_virtual_ips` | VIPs from Next-Gen applications |
| `netscaler_list_ip_addresses` | NSIP, SNIP, VIP, servers (Next-Gen + NITRO) |

### Next-Gen API and classic CLI

| Tool | Description |
|------|-------------|
| `netscaler_nextgen_get` | Read-only GET on any Next-Gen path |
| `netscaler_nextgen_request` | GET/POST/PUT/DELETE on Next-Gen paths |
| `netscaler_create_application` | POST `/applications` (VIP + backends) |
| `netscaler_add_ip_address` | Classic VIP/SNIP/NSIP via NITRO |
| `netscaler_ssh_run_command` | Read-only CLI (`show` / `stat` / `get`) |
| `netscaler_run_cli_command` | Single classic CLI command (read or write) |
| `netscaler_run_cli_commands` | Ordered sequence of CLI commands (multi-step setup) |

### Diagnostics

| Tool | Description |
|------|-------------|
| `netscaler_run_diagnostic` | ICMP/path diagnostics: `ping`, `ping6`, `traceroute`, `traceroute6`, or **`tcp_port`** (with `port`) |
| `netscaler_telnet` | TCP port reachability from the appliance via telnet; returns verdict **`open`**, **`refused`**, or **`no_response`** |
| `netscaler_collect_nsconmsg` | Read-only performance/event collection via `/netscaler/nsconmsg` (`current`, `stats`, `event`, `memstats`, etc.) |

### SSL (v0.05)

| Tool / API | Description |
|------------|-------------|
| MCP `generate_ssl_csr` | Create key + CSR on appliance (OpenSSL via shell) |
| MCP `generate_ssl_self_signed` | Create key + self-signed certificate on appliance |
| `POST /ssl/generate-csr` | Backend proxy to MCP for the SSL Certificate Tools UI |

Enable or disable tools under **Settings → MCP Server**. **SSH fallback must be enabled** for diagnostic and SSL shell tools.

## Vendor brain layout

Each supported platform is defined under `backend-api/app/resources/vendors/<vendor>/manifest.json` and points at:

- `memory/<vendor>/` — RAG markdown (e.g. `cisco_ios_switch_memory.md`)
- `prompts/<vendor>/roles/` — live system prompts (`operator.md`, `analyst.md`, …)
- `architect/<vendor>/` — planning templates (NetScaler today)
- MCP tool names + connect mode (`nextgen` vs `ssh`) in the manifest

Registry: `backend-api/app/services/vendor_registry.py` loads manifests and drives tool filtering, prompt paths, and appliance eligibility.

**Supported today:** `netscaler`, `cisco` (IOS/XE switches via SSH).

## Memory files

Official-syntax references for JPilot RAG live under `backend-api/app/resources/memory/<vendor>/`:

- `memory/netscaler/netscaler_nextgen_api_memory.md` — Next-Gen API endpoints, payloads, behavioral rules
- `memory/netscaler/netscaler_adc_cli_memory.md` — ADC CLI namespaces, commands, behavioral rules
- `memory/f5/`, `memory/cisco/` — placeholders for future vendor memory packs

Architect planning references: `backend-api/app/resources/architect/<vendor>/` (NetScaler: design outline, Citrix integration refs).

## Prompts (vendor + role)

Live chat system prompts load from `backend-api/app/resources/prompts/<vendor>/`:

- `prompts/netscaler/roles/architect.md`, `operator.md`, `analyst.md` — sent to the LLM based on chat role and connected appliance vendor
- `prompts/netscaler/roles/shared_doc_rules.md`, `architect_discovery.md` — shared fragments included via `{{include:…}}`
- `prompts/netscaler/netscaler-copilot-prompt.md` — original project build spec (reference only, not loaded at chat runtime)
- `prompts/f5/`, `prompts/cisco/` — placeholders for future vendor prompt packs

Selection logic: `resolve_chat_vendor()` + `prompt_loader.load_role_prompt()` (see `prompt_paths.py`, `copilot_vendors.py`).

Add more `.md` files under the vendor memory folder; register filenames in `copilot_vendors.py` and wire a memory service. In production, `resources/` is bind-mounted so you can update memory and prompts without rebuilding the image.

JPilot search tools read memory before executing NetScaler write operations. Blocked tool responses include `requiredAction` telling the model to search first.

## API endpoints (backend)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Health check |
| `POST` | `/auth/login` | Password login (blocked if user has passkeys) |
| `GET` | `/auth/me` | Current user |
| `POST` | `/auth/logout` | Logout |
| `POST` | `/auth/account-recovery/request` | Self-service recovery code (generic response) |
| `POST` | `/auth/password-reset/confirm` | Complete account recovery with emailed code |
| `POST` | `/auth/webauthn/status` | Passkey availability for username |
| `POST` | `/auth/webauthn/register/begin\|finish` | Register passkey (authenticated) |
| `POST` | `/auth/webauthn/login/begin\|finish` | Passkey sign-in |
| `GET/POST/PUT/DELETE` | `/users` | User management (admin) |
| `POST` | `/users/{user_id}/reset-password` | Admin send reset code to user's email |
| `DELETE` | `/users/{id}/passkeys/{passkeyId}` | Remove a user's passkey |
| `GET/POST` | `/appliances` | Appliance CRUD |
| `GET/POST` | `/ai-providers` | AI provider CRUD |
| `GET/PUT` | `/mcp/config` | MCP settings |
| `GET` | `/mcp/tools` | Enabled MCP tools |
| `GET` | `/mcp/status` | MCP server online status |
| `GET/PUT` | `/copilot/platform-settings` | Platform settings (Brave Search, web search toggle) |
| `POST` | `/copilot/platform-settings/test` | Test Brave Search API key |
| `POST` | `/copilot/chat` | JPilot chat with tool traces and optional `inputForm` |
| `GET` | `/copilot/usage-dashboard` | LLM and Brave Search usage vs monthly limits |
| `PUT` | `/copilot/usage-limits` | Update monthly usage caps (optional) |
| `GET` | `/copilot/status` | JPilot readiness (default provider) |
| `POST` | `/ssl/generate-csr` | Generate CSR or self-signed cert on appliance |

## Development

Set `NSAGENT_DEPLOY_MODE=dev` in `.env` (or pick **Development** in the installer). Source is
bind-mounted into containers; **Uvicorn `--reload`** and **Vite HMR** pick up changes without rebuild.

```bash
docker compose up -d --build
# or: ./compose.sh up -d --build
# pull main, then pick dev or prod to rebuild:
./scripts/upgrade.sh
```

Health checks (dev stack exposes service ports via containers):

- Backend: [http://localhost:8000/health](http://localhost:8000/health)
- MCP: [http://localhost:8001/health](http://localhost:8001/health)
- MCP tools: [http://localhost:8001/tools](http://localhost:8001/tools)

After changing Python dependencies in `requirements.txt`, rebuild the affected image:

```bash
./compose.sh build backend-api mcp-server && ./compose.sh up -d backend-api mcp-server
```

## Production

Set `NSAGENT_DEPLOY_MODE=prod` in `.env` (the installer default). Production merges the base
stack with `docker-compose.prod.yml`: the frontend is compiled into the nginx image, and API
services run without reload or source bind mounts.

```bash
./scripts/prod-up.sh
# pull main and optionally rebuild stacks:
./scripts/upgrade.sh
# or with NSAGENT_DEPLOY_MODE=prod in .env:
./compose.sh up -d --build
# or explicitly:
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Do **not** use `docker-compose.prod.yml` alone — it only contains production overrides. The base
`docker-compose.yml` defines MongoDB, networks, volumes, and shared service settings.

After changing the domain or `VITE_API_BASE_URL`, rebuild nginx so the UI picks up the new API URL:

```bash
./compose.sh up -d --build nginx
```

Use strong secrets, TLS in front of the UI/API, restrict MongoDB network access, configure SMTP
for password reset, and set `WEBAUTHN_RP_ID`, `WEBAUTHN_ORIGIN`, and `CORS_ORIGINS` to your
real hostname.

### MongoDB crashes (production)

The stack pins **`mongo:8.2`** (not `latest`), uses **`restart: unless-stopped`** on all
services, and a **healthcheck** so `backend-api` and `mcp-server` start only after MongoDB
responds to `ping`.

**Why 8.2 and not 7.0?** Recent installs used `mongo:latest` (MongoDB **8.2.x**). Existing
data has feature compatibility version **8.2** — `mongo:7.0` or `mongo:8.0` exit with code
**62**. Pin **`mongo:8.2`** on existing servers; use **`mongo:7.0`** only for a **new** volume.

Before recreating, confirm the running image:

```bash
docker inspect jpilot-mongodb-1 --format '{{index .Config.Labels "org.opencontainers.image.version"}} {{.Config.Image}}'
```

**Check logs for corruption / abrupt shutdown:**

```bash
docker logs jpilot-mongodb-1 2>&1 | grep -i "fatal\|assert\|crash\|signal\|segfault\|abrupt\|unclean"
```

**Redeploy after pulling compose changes** (recreate Mongo so the pinned image applies):

```bash
./compose.sh up -d --force-recreate mongodb
./compose.sh up -d backend-api mcp-server nginx
```

**If MongoDB keeps exiting with code 139**, stop the stack and repair the data volume (volume
name is `jpilot_mongodb_data`; older installs may still use `nsagent_nsagent_mongodb_data`):

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml stop mongodb
docker run --rm -v jpilot_mongodb_data:/data/db mongo:8.2 mongod --repair
./compose.sh up -d mongodb
./compose.sh up -d backend-api mcp-server nginx
```

### Project layout

```
├── frontend/          # Vue 3 + PrimeVue UI
├── backend-api/       # FastAPI backend, JPilot orchestrator
│   └── app/resources/ # memory/<vendor>/, architect/<vendor>/, prompts/<vendor>/
├── mcp-server/        # MCP NetScaler tool server
├── backend-api/tests/ # Backend unit tests (e.g. form heuristics)
├── docker-compose.yml
├── docker-compose.prod.yml
├── compose.sh              # picks dev/prod compose from .env
├── scripts/prod-up.sh      # production build + up (from repo root)
├── scripts/upgrade.sh      # git pull + dev or prod rebuild (picker)
└── .env.example
```

## License

**JPilot** is **proprietary software** owned by **Nexxus-Tech SAS**. The **Free edition** stays available at no charge when you accept the [EULA](frontend/src/legal/eula.md) and [Terms of Service](frontend/src/legal/terms-of-service.md) — that is **not** an open-source license (no right to redistribute, resell, or offer JPilot to others as a product or MSP service). Paid and Enterprise use requires a separate Commercial Agreement. Details: root [`LICENSE`](LICENSE).

Open-source **third-party** components are listed in [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt) (regenerate with `./scripts/generate-third-party-notices.sh`). Those licenses apply only to the bundled dependencies, not to Nexxus application code.
