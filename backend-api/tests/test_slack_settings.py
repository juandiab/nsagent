import pytest

from app.services.slack_settings_service import mask_webhook_url, validate_slack_webhook_url


def test_validate_slack_webhook_url_accepts_valid_url():
    url = "https://hooks.slack.com/services/T000/B000/XXXXXXXX"
    assert validate_slack_webhook_url(url) == url


def test_validate_slack_webhook_url_rejects_invalid_host():
    with pytest.raises(ValueError, match="valid Slack incoming webhook"):
        validate_slack_webhook_url("https://example.com/webhook")


def test_mask_webhook_url_hides_middle_segment():
    url = "https://hooks.slack.com/services/T000/B000/XXXXXXXX"
    masked = mask_webhook_url(url)
    assert masked.startswith("https://hooks.slack.com/services/T0")
    assert masked.endswith("XXXX")
