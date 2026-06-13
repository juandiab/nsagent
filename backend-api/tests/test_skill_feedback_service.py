from app.services.calibration_feedback_redaction import redact_session_messages, redact_text
from app.services.skill_feedback_service import (
    build_skill_feedback_payload,
    count_planning_form_submissions,
    infer_suggested_skill_id,
)


def test_redact_text_masks_password():
    raw = "password: SuperSecret123 and api_key=abc"
    assert "SuperSecret123" not in redact_text(raw)
    assert "abc" not in redact_text(raw) or "[REDACTED]" in redact_text(raw)


def test_build_skill_feedback_payload_suggests_firmware_skill():
    from app.schemas.calibration_feedback import (
        CalibrationFeedbackMessage,
        CalibrationFeedbackRequest,
        CalibrationFeedbackSession,
    )

    user_content = (
        "Create a phased firmware upgrade plan for HA pairs: prerequisites, risks, rollback."
    )
    payload = build_skill_feedback_payload(
        CalibrationFeedbackRequest(
            userGoal=user_content,
            vendor="netscaler",
            role="architect",
            category="too_slow",
            session=CalibrationFeedbackSession(
                messages=[CalibrationFeedbackMessage(role="user", content=user_content)]
            ),
        ),
        app_fingerprint="fp-test",
        jpilot_version="0.58",
    )
    assert payload["suggestedSkillId"] == "nexxus-netscaler-firmware-ha-upgrade"
    assert payload["diagnostics"]["planningIntent"] == "change_control"
    assert payload["appFingerprint"] == "fp-test"


def test_infer_suggested_skill_id_returns_none_for_operator():
    assert infer_suggested_skill_id(user_goal="firmware upgrade", role="operator", vendor="netscaler") is None


def test_count_planning_form_submissions():
    messages = [
        {"role": "user", "content": "Planning inputs for: What are you planning?\n- Planning intent: change_control"},
        {"role": "user", "content": "Planning inputs for: Scope\n- title: upgrade"},
    ]
    assert count_planning_form_submissions(messages) == 2


def test_redact_session_messages_truncates_tool_results():
    messages = [
        {
            "role": "assistant",
            "content": "blocked",
            "toolCalls": [{"name": "netscaler_list_inventory", "arguments": {}, "result": "x" * 2000}],
        }
    ]
    cleaned = redact_session_messages(messages, max_tool_result_chars=100)
    assert len(cleaned[0]["toolCalls"][0]["resultExcerpt"]) <= 100
