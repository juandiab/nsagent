# JPilot ↔ Stack Calibration Studio

JPilot syncs **skills** from [Stack Calibration Studio](https://scstudio.nexxus-tech.com) and sends **calibration feedback** when a chat session fails to meet the user's objective.

**Normative HTTP contract (shared with scstudio):** [JPILOT_SCSTUDIO_INTEGRATION.md](./JPILOT_SCSTUDIO_INTEGRATION.md)

---

## Overview

| Direction | Endpoint (scstudio) | JPilot client |
|-----------|-------------------|---------------|
| Pull skills | `POST /calibrations/sync` | `calibration_sync_service.py` + `POST /copilot/calibrations/sync` |
| Push feedback | `POST /skill-feedback` | `skill_feedback_service.py` |
| In-app export | — | `POST /copilot/calibration-feedback` (local API → forwards to scstudio) |

Custom org calibrations **persist across JPilot upgrades**: synced skills are cached under `data/calibrations/` with version pins; customer overlays take precedence until the org opts into a Nexxus base update.

---

## Send to Calibration (in-app)

When the user did not achieve their goal, chat exposes **Send to Calibration**:

1. User clicks the button (or it is suggested after tool-limit / error replies).
2. Optional dialog: user goal summary, category, comment, include appliance name.
3. JPilot backend builds a redacted payload and `POST`s to `{nexxus_calibration_base_url}/skill-feedback`.
4. scstudio creates a `skill_feedback` record (`status: new`) and links it to calibration chat for Nexxus SMEs or Enterprise Pro authors.

### Local API

`POST /copilot/calibration-feedback`

See [JPILOT_SCSTUDIO_INTEGRATION.md](./JPILOT_SCSTUDIO_INTEGRATION.md) for request/response shapes.

### Frontend

- `frontend/src/services/calibrationFeedback.js`
- `frontend/src/utils/buildCalibrationFeedbackPayload.js`
- Button in `ChatPane.vue` (beta + classic layouts)

### Settings (env)

| Variable | Default | Purpose |
|----------|---------|---------|
| `NEXXUS_CALIBRATION_BASE_URL` | `https://scstudio.nexxus-tech.com` | scstudio public base URL |
| `CALIBRATION_FEEDBACK_ENABLED` | `true` | Disable outbound feedback (air-gapped installs) |

**Local dev:** run scstudio with `docker compose up` (port 8090) and set `NEXXUS_CALIBRATION_BASE_URL=http://host.docker.internal:8090` on JPilot.

Studio LLM keys are configured **only in scstudio** (Settings → AI Providers). JPilot never sends customer LLM keys to Studio.

---

## What Studio changes vs platform code

| Layer | Calibrated in Studio | Updated via jpilot release |
|-------|----------------------|----------------------------|
| Skill prompts, memory, triggers, scenarios | Yes | — |
| Tool pack (prefer existing MCP tools) | Yes | — |
| MCP SSH / Next-Gen execution | No | `mcp-server/` |
| Orchestrator gates, tool schemas | No (proposal only) | `backend-api/` |

See sample skill: [calibrations/samples/netscaler-firmware-ha-upgrade/](./calibrations/samples/netscaler-firmware-ha-upgrade/).

---

## Phasing

| Phase | JPilot | scstudio |
|-------|--------|----------|
| **1** (this doc + feedback client) | Send to Calibration, `/skill-feedback` forward | Inbox + calibration chat pre-fill |
| **2** | Pull sync, local cache, matcher injection | Publish `.calpkg`, signing |
| **3** | Auto-suggest after repeated failures | Cluster patterns, scenario regression |

---

## Related plans

- `.cursor/plans/skill_feedback_api_2490d1a8.plan.md`
- Stack Calibration Studio concept: `stack_calibration_studio_4f36c161.plan.md`
