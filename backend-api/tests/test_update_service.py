from app.services.update_service import _normalize_version, _pick_latest_semver_tag, is_newer_version


def test_normalize_version_strips_v_prefix():
    assert _normalize_version("v0.06") == "0.06"
    assert _normalize_version("0.06") == "0.06"


def test_is_newer_version_compares_numeric_segments():
    assert is_newer_version("0.07", "0.06")
    assert not is_newer_version("0.06", "0.06")
    assert not is_newer_version("0.05", "0.06")


def test_pick_latest_semver_tag():
    tags = [{"name": "v0.05"}, {"name": "v0.06"}, {"name": "bad-tag"}]
    assert _pick_latest_semver_tag(tags) == "v0.06"
