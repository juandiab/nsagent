import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.copilot_architect_discovery import (  # noqa: E402
    build_architect_discovery_nudge,
    extract_planning_intent,
    sanitize_architect_reply,
    user_wants_design_now,
    user_wants_change_control_now,
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
