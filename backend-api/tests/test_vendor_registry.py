"""Tests for vendor manifest registry."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.vendor_registry import (  # noqa: E402
    get_supported_vendor_ids,
    get_vendor_manifest,
    is_vendor_copilot_supported,
    resolve_chat_vendor,
    validate_vendor_resources,
)


def test_cisco_is_supported_vendor():
    assert is_vendor_copilot_supported("cisco")
    assert "cisco" in get_supported_vendor_ids()


def test_sdx_is_supported_vendor():
    assert is_vendor_copilot_supported("sdx")
    assert "sdx" in get_supported_vendor_ids()


def test_cisco_manifest_paths():
    manifest = get_vendor_manifest("cisco")
    assert manifest is not None
    assert (manifest.memory_dir / "cisco_ios_switch_memory.md").is_file()
    assert (manifest.prompts_dir / "operator.md").is_file()


def test_resolve_chat_vendor_for_cisco_appliance():
    assert resolve_chat_vendor(appliance_vendor="cisco", role="operator", appliance_name="sw01") == "cisco"


def test_sdx_manifest_paths():
    manifest = get_vendor_manifest("sdx")
    assert manifest is not None
    assert (manifest.memory_dir / "netscaler_sdx_cli_memory.md").is_file()
    assert (manifest.prompts_dir / "operator.md").is_file()


def test_resolve_chat_vendor_for_sdx_appliance():
    assert resolve_chat_vendor(appliance_vendor="sdx", role="operator", appliance_name="sdx01") == "sdx"


def test_f5_is_supported_vendor():
    assert is_vendor_copilot_supported("f5")
    assert "f5" in get_supported_vendor_ids()


def test_f5_manifest_paths():
    manifest = get_vendor_manifest("f5")
    assert manifest is not None
    assert (manifest.memory_dir / "f5_bigip_tmsh_memory.md").is_file()
    assert (manifest.prompts_dir / "operator.md").is_file()
    assert (manifest.prompts_dir / "architect.md").is_file()


def test_resolve_chat_vendor_for_f5_appliance():
    assert resolve_chat_vendor(appliance_vendor="f5", role="operator", appliance_name="bigip01") == "f5"


def test_validate_vendor_resources_clean():
    warnings = validate_vendor_resources()
    assert warnings == []
