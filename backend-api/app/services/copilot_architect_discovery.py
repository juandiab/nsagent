"""Architect discovery guardrails — jpilot-form only, no checklist loops."""

from __future__ import annotations

import re

from app.services.copilot_form import parse_input_form
from app.services.copilot_roles import JPilotRole, normalize_role

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

    if user_wants_deliverable_now(user_message):
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
