import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.copilot_architect_discovery import (  # noqa: E402
    architect_discovery_ready_for_deliverable,
    architect_tools_enabled,
    block_architect_tool_during_discovery,
    build_architect_discovery_nudge,
    build_architect_session_nudge,
    build_discovery_form_submit_nudge,
    conversation_has_deliverable,
    extract_planning_intent,
    is_rich_change_control_request,
    sanitize_architect_reply,
    user_wants_design_now,
    user_wants_change_control_now,
    user_wants_deliverable_revision,
)


def test_user_wants_design_now_short():
    assert user_wants_design_now("go")
    assert user_wants_design_now("Generate the design document")


def test_user_wants_change_control_now():
    assert user_wants_change_control_now("Generate the change control record")
    assert not user_wants_change_control_now("go")


def test_extract_planning_intent_from_form():
    text = "Planning inputs for: What are you planning?\n- Planning intent: change_control"
    assert extract_planning_intent(text) == "change_control"


def test_extract_planning_intent_from_rich_firmware_request():
    msg = (
        "Create a phased firmware upgrade plan for HA pairs: prerequisites, risks, "
        "maintenance windows, rollback, and verification checklist."
    )
    assert extract_planning_intent(msg) == "change_control"
    assert is_rich_change_control_request(msg)


def test_rich_change_control_fast_path_nudge():
    msg = (
        "Create a phased firmware upgrade plan for HA pairs: prerequisites, risks, "
        "maintenance windows, rollback, and verification checklist."
    )
    nudge = build_architect_session_nudge(msg, conversation_text=msg)
    assert nudge is not None
    assert "What are you planning?" not in nudge
    assert "ONE ```jpilot-form```" in nudge
    assert "Do NOT call any MCP tools" in nudge


def test_architect_tools_disabled_during_discovery():
    history = "Planning inputs for: What are you planning?\n- Planning intent: change_control"
    assert not architect_tools_enabled(
        "architect",
        "Planning inputs for: Classification\n- class: emergency",
        conversation_text=history,
    )


def test_architect_tools_disabled_when_deliverable_ready():
    conversation = (
        "Create a phased firmware upgrade plan for HA pairs: prerequisites, risks, rollback.\n"
        "Planning inputs for: Essentials\n- current: 13.1\n- target: 14.1\n"
    )
    assert architect_discovery_ready_for_deliverable(conversation, "change_control")
    assert not architect_tools_enabled(
        "architect",
        "Planning inputs for: Essentials\n- current: 13.1\n- target: 14.1\n",
        conversation_text=conversation,
    )


def test_change_control_ready_after_four_forms():
    conversation = (
        "Planning inputs for: What are you planning?\n- Planning intent: change_control\n"
        + "\n".join(f"Planning inputs for: Step {i}\n- x: y" for i in range(3))
    )
    assert architect_discovery_ready_for_deliverable(conversation, "change_control")


def test_nudge_on_checklist_without_form():
    content = "Still missing:\n❌ Turn 1: Platform\nLet me ask Turn 1 first."
    nudge = build_architect_discovery_nudge(content, "hello", "f5")
    assert nudge is not None
    assert "jpilot-form" in nudge


def test_no_nudge_when_form_present():
    content = """Intro.

```jpilot-form
{"inputForm": {"title": "HA", "submitLabel": "Continue", "fields": [
  {"id": "ha_mode", "label": "Mode", "type": "choice", "required": true, "options": [
    {"value": "ap", "label": "Active/Standby"}
  ]}
]}}
```
"""
    assert build_architect_discovery_nudge(content, "hello", "f5") is None


def test_design_now_nudge():
    nudge = build_architect_discovery_nudge("Almost there.", "go", "f5")
    assert nudge is not None
    assert "jpilot-design-document" in nudge
    assert "search_f5_documentation" in nudge


def test_change_control_now_nudge():
    history = "Planning inputs for: What are you planning?\n- Planning intent: change_control"
    nudge = build_architect_discovery_nudge(
        "Almost there.",
        "generate the change control document",
        "netscaler",
        conversation_text=history,
    )
    assert nudge is not None
    assert "jpilot-change-control-document" in nudge
    assert "change control outline" in nudge


def test_sanitize_tool_call_leak():
    raw = "Hello\n</tool_calls>\nDSML tool_calls\nDone"
    assert "</tool_calls>" not in sanitize_architect_reply(raw)


def test_user_wants_deliverable_revision():
    assert user_wants_deliverable_revision("let's include the TBDs in the design document")
    assert user_wants_deliverable_revision("please ask me for the TBD values")
    assert not user_wants_deliverable_revision("Planning inputs for: VLAN\n- id: 10")


def test_conversation_has_deliverable():
    doc = "<!-- jpilot-design-document -->\n# Design\n| VIP | TBD |"
    assert conversation_has_deliverable(doc)


def test_revision_form_nudge():
    history = "<!-- jpilot-design-document -->\n# Design\nNSIP: TBD"
    nudge = build_architect_discovery_nudge(
        "OK",
        "please ask me for the TBD values",
        "netscaler",
        conversation_text=history,
    )
    assert nudge is not None
    assert "jpilot-form" in nudge
    assert "NOT an MCP tool" in nudge
    assert "Do NOT call search" in nudge


def test_revision_apply_after_form_submit():
    history = "<!-- jpilot-design-document -->\n# Design\nNSIP: TBD"
    nudge = build_architect_discovery_nudge(
        "",
        "Planning inputs for: TBD network values\n- NSIP ADC1: 10.0.0.1\n",
        "netscaler",
        conversation_text=history,
    )
    assert nudge is not None
    assert "COMPLETE revised" in nudge
    assert "jpilot-design-document" in nudge


def test_discovery_form_submit_nudge():
    history = (
        "Planning inputs for: What are you planning?\n- Planning intent: new_deployment\n"
        "Planning inputs for: Business goal\n- goal: citrix_gateway_remote_access"
    )
    nudge = build_architect_discovery_nudge(
        "Planning inputs for: Network model\n- topology: one_arm",
        "Planning inputs for: Network model\n- topology: one_arm",
        "netscaler",
        conversation_text=history,
    )
    assert nudge is not None
    assert "Do NOT call search_jpilot_architect_resources" in nudge
    assert "jpilot-form" in nudge


def test_block_architect_search_on_form_submit():
    blocked = block_architect_tool_during_discovery(
        "search_jpilot_architect_resources",
        role="architect",
        user_message="Planning inputs for: VLAN\n- count: 2",
        tool_traces=[],
    )
    assert blocked is not None
    assert "BLOCKED" in blocked


def test_block_architect_inventory_during_discovery():
    blocked = block_architect_tool_during_discovery(
        "netscaler_list_inventory",
        role="architect",
        user_message="Planning inputs for: VIP\n- vlan: 100",
        tool_traces=[],
    )
    assert blocked is not None


def test_block_architect_search_during_discovery_after_one():
    class Trace:
        name = "search_jpilot_architect_resources"

    blocked = block_architect_tool_during_discovery(
        "search_jpilot_architect_resources",
        role="architect",
        user_message="continue with the next topic",
        tool_traces=[Trace()],
    )
    assert blocked is not None


def test_discovery_ready_nudge_after_enough_forms():
    conversation = (
        "Planning inputs for: What are you planning?\n- Planning intent: new_functionality\n"
        "Planning inputs for: Existing env\n- platform: vp\n"
        "Planning inputs for: Protocols\n- ssl: bridge\n"
        "Planning inputs for: Monitors\n- method: lc\n"
        "Planning inputs for: VIP\n- vip: 192.168.20.55"
    )
    nudge = build_discovery_form_submit_nudge(
        "Planning inputs for: VIP\n- vip: 192.168.20.55",
        conversation_text=conversation,
    )
    assert nudge is not None
    assert "jpilot-design-document" in nudge
    assert "Do NOT call any tools" in nudge


def test_architect_discovery_ready_for_deliverable():
    text = (
        "Planning inputs for: What are you planning?\n- Planning intent: new_functionality\n"
        + "\n".join(f"Planning inputs for: Step {i}\n- x: y" for i in range(4))
    )
    assert architect_discovery_ready_for_deliverable(text, "new_functionality")
