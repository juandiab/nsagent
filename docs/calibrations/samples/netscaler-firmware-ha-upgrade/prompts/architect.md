## Firmware HA upgrade — Architect fast path

When `planning_intent` is **change_control** and the user asks for a firmware upgrade / maintenance plan (prerequisites, risks, rollback, verification):

1. **Do NOT** show the generic "What are you planning?" form — intent is already change control.
2. **Do NOT** call MCP tools during discovery (no inventory, no search).
3. Output **one consolidated** ```jpilot-form``` (≤6 fields) for values still unknown:
   - Change classification (standard / normal / emergency / expedited)
   - Current firmware version/build
   - Target firmware version/build
   - HA pair count + primary/secondary hostname or IP per pair
   - Planned maintenance window (date, start, end, timezone)
4. On form submit (or when user says generate / continue), output the full **Change control record**:
   - First line: `<!-- jpilot-change-control-document -->`
   - Sections: prerequisites, risk & impact, maintenance window, phased implementation per HA pair, rollback, post-change validation checklist
   - Appendix: **Vendor pre-change checklist — NetScaler ADC**
   - Mark unknowns **TBD**; do not re-ask topics already captured in chat or prior forms.
5. **Handoff for Operator** — include only if the user confirmed on-appliance execution.

Skip one-topic-per-turn discovery for this skill when the opening message already lists deliverable sections (prerequisites, risks, rollback, verification).
