"""Tests for vendor-scoped prompt loading."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.copilot_roles import build_system_prompt  # noqa: E402
from app.services.prompt_loader import load_role_prompt  # noqa: E402
from app.services.prompt_paths import prompts_dir, resolve_prompt_vendor, role_prompt_path  # noqa: E402


def test_netscaler_role_prompt_files_exist():
    for role in ("architect", "operator", "analyst"):
        assert role_prompt_path(role, "netscaler").is_file()


def test_load_role_prompt_includes_shared_rules():
    prompt = load_role_prompt("operator", "netscaler")
    assert "search_netscaler_nextgen_api" in prompt
    assert "{{include:" not in prompt


def test_build_system_prompt_uses_vendor_folder():
    prompt = build_system_prompt("architect", vendor="netscaler")
    assert "Architect" in prompt
    assert "search_jpilot_architect_resources" in prompt


def test_unknown_vendor_falls_back_to_netscaler_prompts():
    assert resolve_prompt_vendor("f5") == "netscaler"
    assert prompts_dir("netscaler").is_dir()


def test_sdx_operator_prompt_loads():
    prompt = load_role_prompt("operator", "sdx")
    assert "NetScaler SDX" in prompt
    assert "search_sdx_cli_reference" in prompt
    assert "{{include:" not in prompt
