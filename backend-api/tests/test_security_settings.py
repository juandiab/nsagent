from app.services.security_settings_service import normalize_passkey_policy


def test_normalize_passkey_policy_defaults_to_enabled():
    assert normalize_passkey_policy(None) == "enabled"
    assert normalize_passkey_policy("") == "enabled"
    assert normalize_passkey_policy("unknown") == "enabled"


def test_normalize_passkey_policy_accepts_valid_values():
    assert normalize_passkey_policy("disabled") == "disabled"
    assert normalize_passkey_policy("ENABLED") == "enabled"
    assert normalize_passkey_policy(" enforced ") == "enforced"
