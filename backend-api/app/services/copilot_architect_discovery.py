"""Architect discovery guardrails — jpilot-form only, no checklist loops."""

from __future__ import annotations

import re

from app.services.copilot_form import is_form_submission, parse_input_form
from app.services.copilot_roles import JPilotRole, normalize_role

ARCHITECT_SEARCH_TOOL_NAMES = frozenset(
    {
        "search_jpilot_architect_resources",
        "search_f5_documentation",
    }
)

_BAD_DISCOVERY_RE = re.compile(
    r"(✅|❌|still missing|discovery checklist|let me ask turn|"
    r"one quick question to check off|we('re| are) making progress|almost there\. let me get|"
    r"</tool_calls?>|<\|tool|DSML\|tool)",
    re.IGNORECASE,
)

_TURN_CHECKLIST_RE = re.compile(r"turn\s*[1-5]\s*:", re.IGNORECASE)

_DESIGN_NOW_RE = re.compile(
    r"^\s*(go|yes|ok|okay|continue|proceed|generate|draft|build)\s*\.?\s*$",
    re.IGNORECASE,
)

_DESIGN_NOW_PHRASES = (
    "generate the design",
    "produce the design",
    "write the design",
    "design document",
    "ready to generate",
    "let's generate",
    "lets generate",
)

_DELIVERABLE_MARKERS = (
    "<!-- jpilot-design-document -->",
    "<!-- jpilot-change-control-document -->",
)

_REVISION_PHRASES = (
    "fill in the tbd",
    "fill the tbd",
    "fill in tbd",
    "include the tbd",
    "include tbd",
    "ask me for the tbd",
    "ask me for tbd",
    "update the design",
    "revise the design",
    "edit the design",
    "update the document",
    "revise the document",
    "edit the document",
    "update design document",
    "revise design document",
    "something missing",
    "missing from the design",
    "fill in missing",
    "complete the tbd",
)

_CHANGE_CONTROL_NOW_PHRASES = (
    "generate the change control",
    "produce the change control",
    "write the change control",
    "change control document",
    "change control record",
    "maintenance window document",
)

_PLANNING_INTENT_FIELD_RE = re.compile(
    r"planning intent:\s*(new_deployment|new_functionality|change_control)\b",
    re.IGNORECASE,
)


def user_wants_design_now(user_message: str) -> bool:
    text = (user_message or "").strip()
    if not text:
        return False
    if _DESIGN_NOW_RE.match(text):
        return True
    lowered = text.lower()
    return any(phrase in lowered for phrase in _DESIGN_NOW_PHRASES)


def user_wants_change_control_now(user_message: str) -> bool:
    text = (user_message or "").strip()
    if not text:
        return False
    if _DESIGN_NOW_RE.match(text):
        return False
    lowered = text.lower()
    return any(phrase in lowered for phrase in _CHANGE_CONTROL_NOW_PHRASES)


def user_wants_deliverable_now(user_message: str) -> bool:
    return user_wants_design_now(user_message) or user_wants_change_control_now(user_message)


def conversation_has_deliverable(conversation_text: str) -> bool:
    text = conversation_text or ""
    return any(marker in text for marker in _DELIVERABLE_MARKERS)


def user_wants_deliverable_revision(user_message: str) -> bool:
    text = (user_message or "").strip()
    if not text or is_form_submission(text):
        return False
    lowered = text.lower()
    return any(phrase in lowered for phrase in _REVISION_PHRASES)


JPILOT_FORM_NOT_A_TOOL_HINT = (
    "jpilot-form is NOT an MCP tool. Never call jpilot-form, inputForm, or similar as tool_calls. "
    "Embed exactly one ```jpilot-form``` JSON fence in your assistant markdown reply instead."
)


def extract_planning_intent(*texts: str) -> str | None:
    """Return planning_intent from form submissions or plain-text hints."""
    combined = "\n".join(t for t in texts if t).lower()
    match = _PLANNING_INTENT_FIELD_RE.search(combined)
    if match:
        return match.group(1).lower()
    if "planning intent: new deployment" in combined or "greenfield" in combined:
        return "new_deployment"
    if "planning intent: new functionality" in combined:
        return "new_functionality"
    if "planning intent: change control" in combined or "change control / maintenance" in combined:
        return "change_control"
    return None


def _uses_bad_discovery_prose(content: str) -> bool:
    if not content or not content.strip():
        return False
    if _BAD_DISCOVERY_RE.search(content):
        return True
    if _TURN_CHECKLIST_RE.search(content) and "jpilot-form" not in content.lower():
        return True
    return False


def sanitize_architect_reply(content: str) -> str:
    """Strip leaked tool-call markup from model output."""
    if not content:
        return content
    lines = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("</") and "tool" in stripped.lower():
            continue
        if "DSML" in stripped and "tool_calls" in stripped:
            continue
        if stripped in {"</tool_calls>", "<tool_calls>"}:
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _revision_form_nudge() -> str:
    return (
        "A design or change-control deliverable already exists in this conversation. "
        "The user wants to fill in **TBD** fields or revise the document. "
        f"{JPILOT_FORM_NOT_A_TOOL_HINT} "
        "Do NOT call search_* or other tools. "
        "Review the latest deliverable, identify fields still marked TBD (prioritize network/VLAN/IPs, "
        "licensing, firmware build, VIP address, and HA NSIPs), then output a short intro (≤2 sentences) "
        "and exactly one ```jpilot-form``` with up to 6 fields for those TBD values. "
        'Use submitLabel "Update design". No prose after the closing fence.'
    )


def _revision_apply_nudge(*, planning_intent: str | None) -> str:
    marker = (
        "<!-- jpilot-change-control-document -->"
        if planning_intent == "change_control"
        else "<!-- jpilot-design-document -->"
    )
    doc_label = "Change control record" if planning_intent == "change_control" else "Design document"
    return (
        "The user submitted values to update an existing deliverable. "
        f"{JPILOT_FORM_NOT_A_TOOL_HINT} "
        "Do NOT call any tools. "
        f"Re-output the COMPLETE revised {doc_label} in one markdown reply: first line {marker}, "
        "apply the new values everywhere relevant, keep remaining unknowns as TBD, "
        "preserve structure/tables, and keep **Handoff for Operator** if it was present. "
        "Do not ask more questions."
    )


def _design_now_nudge(*, doc_tool: str, planning_intent: str | None, vendor_id: str) -> str:
    if planning_intent == "change_control":
        outline_hint = (
            "Call search_jpilot_architect_resources with query 'change control outline' if you need the section structure. "
            if vendor_id == "netscaler"
            else "Follow the change control outline from your Architect prompt (ITIL/ServiceNow sections). "
        )
        return (
            "The user wants the formal change control record now. Do NOT ask more discovery questions or show checklists. "
            "Use conversation history for answers already given. "
            f"{outline_hint}"
            "Output the full Change control record. First line: <!-- jpilot-change-control-document -->. "
            "Use ITIL/ServiceNow-style vendor-neutral sections plus the vendor pre-change checklist appendix for this product. "
            "Mark unknowns TBD — do not re-open completed topics. "
            "Include **Handoff for Operator** only if the user requested on-appliance execution."
        )
    if planning_intent == "new_functionality":
        return (
            "The user wants the functional change design now. Do NOT ask more discovery questions or show checklists. "
            "Use conversation history for answers already given. "
            f"Call {doc_tool} if you need official references, then output the full Functional change design. "
            "First line: <!-- jpilot-design-document -->. End with **Handoff for Operator**. "
            "Mark unknowns TBD — do not re-open completed topics."
        )
    return (
        "The user wants the formal design document now. Do NOT ask more discovery questions or show checklists. "
        "Use conversation history for answers already given (including plain-text replies like VMware or one-arm). "
        f"Call {doc_tool} if you need official references, then output the full Design document. "
        "First line: <!-- jpilot-design-document -->. End with **Handoff for Operator**. "
        "Mark unknowns TBD — do not re-open completed topics."
    )


def count_planning_form_submissions(text: str) -> int:
    return len(re.findall(r"planning inputs for:", text or "", re.IGNORECASE))


def architect_discovery_ready_for_deliverable(
    conversation_text: str,
    planning_intent: str | None,
) -> bool:
    """Heuristic: enough discovery forms collected to write the deliverable."""
    count = count_planning_form_submissions(conversation_text)
    if planning_intent == "new_functionality":
        return count >= 5
    if planning_intent == "change_control":
        return count >= 8
    if planning_intent == "new_deployment":
        return count >= 7
    return count >= 6


def _deliverable_ready_nudge(*, planning_intent: str | None) -> str:
    if planning_intent == "change_control":
        marker = "<!-- jpilot-change-control-document -->"
        label = "Change control record"
    else:
        marker = "<!-- jpilot-design-document -->"
        label = (
            "Functional change design"
            if planning_intent == "new_functionality"
            else "Design document"
        )
    return (
        f"Discovery is sufficient for this request. {JPILOT_FORM_NOT_A_TOOL_HINT} "
        "Do NOT call any tools — use conversation history only. "
        f"Output the complete {label} in one markdown reply. "
        f"First line: {marker}. Include configuration tables and phased implementation steps. "
        "Mark unknowns **TBD**. End with **Handoff for Operator**. Do not ask more questions."
    )


def build_discovery_form_submit_nudge(
    user_message: str,
    *,
    conversation_text: str = "",
) -> str | None:
    """Proactive nudge after a planning form submit — next jpilot-form, no search tools."""
    if not is_form_submission(user_message):
        return None
    if conversation_has_deliverable(conversation_text):
        return None
    if user_wants_deliverable_now(user_message):
        return None
    planning_intent = extract_planning_intent(conversation_text, user_message)
    if architect_discovery_ready_for_deliverable(conversation_text, planning_intent):
        return _deliverable_ready_nudge(planning_intent=planning_intent)

    intent_hint = ""
    if planning_intent == "change_control":
        intent_hint = " Next topics: change classification, window, rollback, validation — per change-control branch."
    elif planning_intent == "new_functionality":
        intent_hint = " Next topics: delta/impact, dependencies, validation — not full greenfield topology."
    elif planning_intent == "new_deployment":
        intent_hint = (
            " Next topics still needed may include: authentication, Citrix Gateway/StoreFront integration, "
            "SSL/certificates, ADM/monitoring, backups, constraints — skip any already captured in chat."
        )
    return (
        "The user submitted a planning discovery form. "
        f"{JPILOT_FORM_NOT_A_TOOL_HINT} "
        "Do NOT call search_jpilot_architect_resources, search_* documentation tools, or any other tools. "
        "Acknowledge their answers in 1–2 sentences, then output exactly one ```jpilot-form``` for the "
        f"**next** unknown discovery topic only.{intent_hint} "
        'Use submitLabel "Continue". No prose after the closing fence.'
    )


def block_architect_tool_during_discovery(
    tool_name: str,
    *,
    role: str | None,
    user_message: str,
    tool_traces: list | None = None,
    conversation_text: str = "",
) -> str | None:
    """Block all MCP tools during Architect discovery; allow limited search when generating deliverable."""
    if normalize_role(role) != JPilotRole.ARCHITECT:
        return None

    traces = tool_traces or []
    search_count = sum(1 for trace in traces if trace.name in ARCHITECT_SEARCH_TOOL_NAMES)

    if user_wants_deliverable_now(user_message):
        if tool_name in ARCHITECT_SEARCH_TOOL_NAMES and search_count >= 3:
            return (
                "BLOCKED: You already searched architect resources enough times. "
                "Write the full deliverable now using conversation history and prior search results. "
                "Do NOT call more search tools."
            )
        return None

    if architect_discovery_ready_for_deliverable(
        conversation_text,
        extract_planning_intent(conversation_text, user_message),
    ):
        return (
            f"BLOCKED: Discovery is complete — do not call `{tool_name}` or any other tool. "
            "Write the full deliverable in markdown now (see system instructions)."
        )

    return (
        f"BLOCKED: Architect discovery uses ```jpilot-form``` in chat only — do not call `{tool_name}` "
        "or any MCP tool. Acknowledge the user's form answers, then output the next ```jpilot-form``` "
        'or the final deliverable if enough is known (submitLabel "Continue").'
    )


def block_architect_search_during_discovery(
    tool_name: str,
    *,
    role: str | None,
    user_message: str,
    tool_traces: list | None = None,
    conversation_text: str = "",
) -> str | None:
    """Backward-compatible alias — blocks all architect tools during discovery."""
    return block_architect_tool_during_discovery(
        tool_name,
        role=role,
        user_message=user_message,
        tool_traces=tool_traces,
        conversation_text=conversation_text,
    )


def build_architect_discovery_nudge(
    content: str,
    user_message: str,
    vendor: str | None = None,
    *,
    conversation_text: str = "",
) -> str | None:
    """System retry when Architect discovery violates jpilot-form workflow."""
    _, form = parse_input_form(content or "")
    if form is not None:
        return None

    vendor_id = (vendor or "netscaler").strip().lower()
    doc_tool = "search_f5_documentation" if vendor_id == "f5" else "search_jpilot_architect_resources"
    if vendor_id == "cisco":
        doc_tool = "search_cisco_cli_reference (syntax appendix only)"

    planning_intent = extract_planning_intent(conversation_text, user_message)
    has_deliverable = conversation_has_deliverable(conversation_text)

    if has_deliverable and is_form_submission(user_message):
        return _revision_apply_nudge(planning_intent=planning_intent)

    if has_deliverable and user_wants_deliverable_revision(user_message):
        return _revision_form_nudge()

    form_submit_nudge = build_discovery_form_submit_nudge(
        user_message,
        conversation_text=conversation_text,
    )
    if form_submit_nudge is not None:
        return form_submit_nudge

    if user_wants_deliverable_now(user_message) and not has_deliverable:
        return _design_now_nudge(
            doc_tool=doc_tool,
            planning_intent=planning_intent,
            vendor_id=vendor_id,
        )

    if not _uses_bad_discovery_prose(content):
        return None

    intent_hint = ""
    if planning_intent == "change_control":
        intent_hint = " User intent is change_control — discovery forms should cover change record topics only."
    elif planning_intent == "new_functionality":
        intent_hint = " User intent is new_functionality — focus on delta/impact forms, not greenfield topology."
    elif planning_intent is None:
        intent_hint = " If planning intent is not yet captured, output the 'What are you planning?' jpilot-form first."

    return (
        "Your last reply violated Architect discovery rules. Do NOT use checklists (✅/❌), "
        'Still missing, Turn N labels, or prose question lists. Do NOT emit tool_calls or XML markup. '
        "Acknowledge any answers the user already gave in chat (1 sentence max), then output exactly one "
        "```jpilot-form``` JSON block for the **next** unknown topic only — or the final deliverable if enough "
        f"is known.{intent_hint} No prose after the form fence."
    )


def architect_discovery_should_retry(
    content: str,
    user_message: str,
    role: str | None,
    vendor: str | None = None,
    *,
    conversation_text: str = "",
) -> str | None:
    if normalize_role(role) != JPilotRole.ARCHITECT:
        return None
    cleaned = sanitize_architect_reply(content)
    return build_architect_discovery_nudge(
        cleaned,
        user_message,
        vendor,
        conversation_text=conversation_text,
    )
