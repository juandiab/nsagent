"""Tests for LB vserver form detection heuristics."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.copilot_form import (  # noqa: E402
    InputForm,
    attachment_is_design_document,
    format_form_submission,
    is_form_submission,
    message_targets_policy_or_feature_config,
    parse_input_form,
    user_configures_existing_lb,
    user_requests_design_implementation,
    user_requests_lb_vserver_create,
)


def test_design_implementation_with_md_attachment():
    assert attachment_is_design_document("jpilot-design-2026-06-04.md")
    assert user_requests_design_implementation(
        "Can you configure this?",
        ["jpilot-design-2026-06-04.md"],
    )
    assert not user_requests_design_implementation("show version", ["notes.md"])


def test_responder_redirect_on_existing_vserver_is_not_lb_create():
    msg = (
        "create a responder policy to redirect all traffic from HTTP to HTTPs "
        "and apply it to the lb Vserver web_example"
    )
    assert message_targets_policy_or_feature_config(msg)
    assert not user_requests_lb_vserver_create(msg)


def test_rewrite_policy_bind_is_not_lb_create():
    msg = "add rewrite policy pol1 and bind it to the lb vserver web_example"
    assert message_targets_policy_or_feature_config(msg)
    assert not user_requests_lb_vserver_create(msg)


def test_create_load_balancer_still_triggers_form():
    msg = "create a load balancer for StoreFront with VIP 192.168.1.10"
    assert user_requests_lb_vserver_create(msg)


def test_create_lb_vserver_with_vip_still_triggers_form():
    msg = "create lb vserver web_app HTTP 10.20.30.40 80 with backend 10.0.0.5"
    assert user_requests_lb_vserver_create(msg)


def test_configure_delivery_controllers_still_triggers_form():
    msg = "configure delivery controllers load balancing"
    assert user_requests_lb_vserver_create(msg)


def test_show_vservers_is_not_lb_create():
    msg = "show all lb vservers"
    assert not user_requests_lb_vserver_create(msg)


def test_parse_choice_jpilot_form():
    content = """Pick one option.

```jpilot-form
{"inputForm": {"title": "Scope", "submitLabel": "Continue", "fields": [
  {"id": "ha", "label": "HA mode", "type": "choice", "required": true, "options": [
    {"value": "ap", "label": "Active/Passive", "description": "One primary node"},
    {"value": "other", "label": "Other", "description": "Custom"}
  ]}
]}}
```
"""
    cleaned, form = parse_input_form(content)
    assert "jpilot-form" not in cleaned
    assert form is not None
    assert form.fields[0].type == "choice"
    assert form.fields[0].options[0].description == "One primary node"


def test_planning_form_submission_detected():
    assert is_form_submission("Planning inputs for: Sites\n- HA: dual")


def test_architect_form_submission_prefix():
    form = InputForm.model_validate(
        {
            "title": "Sites",
            "fields": [{"id": "x", "label": "X", "type": "text", "required": True}],
        }
    )
    text = format_form_submission(form, {"x": "dual"}, role="architect")
    assert text.startswith("Planning inputs for:")
    assert "Continue design discovery" in text


def test_secure_headers_on_named_lb_is_not_lb_create():
    msg = "I want to configure HTTP secure headers in a load balancer called lb_01"
    assert user_configures_existing_lb(msg)
    assert not user_requests_lb_vserver_create(msg)
