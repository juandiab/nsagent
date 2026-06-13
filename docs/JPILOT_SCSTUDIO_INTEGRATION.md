# JPilot ↔ scstudio integration contract

Normative contract between **JPilot** (`backend-api`) and **Stack Calibration Studio** (`scstudio.nexxus-tech.com`). Copy or symlink this file into `scstudio/docs/JPILOT_INTEGRATION.md` when the scstudio repo is scaffolded.

**Last updated:** 2026-06-13

---

## Base URL

Production: `https://scstudio.nexxus-tech.com`

nginx (nexxus-web):

```nginx
location /skill-feedback {
    proxy_pass http://scstudio-backend-api:8000/skill-feedback;
}
location /calibrations/ {
    proxy_pass http://scstudio-backend-api:8000/calibrations/;
}
```

---

## Authentication

| Caller | Required fields |
|--------|-----------------|
| Licensed JPilot (Enterprise / Enterprise Pro) | `appFingerprint`, `installSignature` (future), `licenseOrgId` when available |
| Free / Early Access | `appFingerprint` only |

JPilot derives `appFingerprint` from installation binding (see `license_service.licensefingerprint()`).

`installSignature` — reserved; HKDF over fingerprint + license code. Optional until licensing binding ships.

---

## POST /skill-feedback

Ingest a failed or unsatisfactory JPilot session for SME calibration.

### Request

```json
{
  "appFingerprint": "sha256-install-id",
  "installSignature": null,
  "clientId": "acme-corp",
  "jpilotVersion": "0.59",
  "objectiveMet": false,
  "userGoal": "Phased firmware upgrade plan for HA pairs",
  "vendor": "netscaler",
  "role": "architect",
  "category": "too_slow",
  "rating": "negative",
  "userComment": "Hit tool call limit before document was generated",
  "matchedSkills": [],
  "suggestedSkillId": "nexxus-netscaler-firmware-ha-upgrade",
  "includeApplianceName": false,
  "applianceName": null,
  "session": {
    "sessionId": "uuid-or-local-id",
    "startedAt": "2026-06-13T12:03:00Z",
    "messages": [
      { "role": "user", "content": "Create a phased firmware upgrade plan…", "createdAt": "2026-06-13T12:03:00Z" },
      { "role": "assistant", "content": "…", "toolCalls": [{ "name": "netscaler_list_inventory", "arguments": {}, "resultExcerpt": "BLOCKED: …" }] }
    ]
  },
  "diagnostics": {
    "lastErrorType": "tool_limit",
    "formSubmissionCount": 8,
    "planningIntent": "change_control"
  },
  "source": "jpilot_in_app"
}
```

### Field notes

| Field | Required | Description |
|-------|----------|-------------|
| `objectiveMet` | yes | `false` when user sends feedback / didn't achieve goal |
| `userGoal` | recommended | First user message or edited summary |
| `category` | yes | See categories below |
| `rating` | yes | `positive` \| `negative` \| `neutral` |
| `session.messages` | yes | Redacted excerpt (max messages/chars enforced by JPilot) |
| `matchedSkills` | no | Skill IDs active during session (future matcher) |
| `suggestedSkillId` | no | Heuristic skill to attach (e.g. firmware upgrade) |
| `diagnostics` | no | Structured hints for calibration chat |
| `source` | yes | `jpilot_in_app` \| `jpilot_thumbs` \| `studio_paste` |

### Categories

`wrong_tool`, `missing_step`, `wrong_answer`, `skill_not_triggered`, `too_slow`, `tool_limit`, `other`

### Response

HTTP **202 Accepted**

```json
{
  "status": "accepted",
  "feedbackId": "fb-uuid",
  "message": "Feedback queued for calibration",
  "calibrationUrl": "https://scstudio.nexxus-tech.com/feedback/fb-uuid"
}
```

### Storage (scstudio MongoDB `skill_feedback`)

```json
{
  "_id": "fb-uuid",
  "status": "new",
  "linkedCalibrationSessionId": null,
  "createdAt": "2026-06-13T12:15:00Z"
}
```

Status workflow: `new` → `triaged` → `in_calibration` → `resolved` | `wont_fix`

### Redaction (JPilot responsibility)

Before send, JPilot MUST strip or mask:

- Passwords, license codes, API keys, JWTs
- `nsagent_encryption_key` patterns
- PEM / private key blocks
- Optional: appliance hostnames unless `includeApplianceName: true`

---

## POST /calibrations/sync (pull — Phase 2)

JPilot pulls signed `.calpkg` bundles. Request/response defined in Stack Calibration Studio plan; not implemented in JPilot yet.

---

## JPilot proxy: POST /copilot/calibration-feedback

Authenticated JPilot users call the local API; JPilot forwards to scstudio after redaction.

### Request body

Same as `/skill-feedback` except install identity is added server-side (`appFingerprint`, `jpilotVersion`).

### Response

Pass-through of scstudio 202 body, or:

```json
{
  "status": "disabled",
  "message": "Calibration feedback is disabled on this installation."
}
```

When scstudio is unreachable:

```json
{
  "status": "queued",
  "message": "Feedback saved locally; will retry when Studio is reachable."
}
```

(Future: local Mongo queue — v1 returns 502 with detail.)

---

## Calibration apply model

| Tier | What changes | Who approves | Ships via |
|------|--------------|--------------|-----------|
| **Skill** | prompts, memory, triggers, scenarios, tool pack | SME or Enterprise Pro author | `.calpkg` publish → sync |
| **Platform proposal** | orchestrator, MCP, tool schemas | Nexxus only | jpilot release |
| **Full repo (Cursor power mode)** | multi-file patch | Nexxus + PR review | git tag |

Studio NEVER auto-publishes without human **Apply → lint → scenario pass**.

---

## Sample skill

See [calibrations/samples/netscaler-firmware-ha-upgrade/](./calibrations/samples/netscaler-firmware-ha-upgrade/).
