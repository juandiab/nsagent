"""Tests for SDX CLI memory search."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.copilot_memory_gate import classify_sdx_command  # noqa: E402
from app.services.sdx_cli_memory_service import search_sdx_cli_memory  # noqa: E402


def test_search_sdx_cli_memory_finds_vpx():
    result = search_sdx_cli_memory("show virtualserver VPX lifecycle")
    assert result["vendor"] == "sdx"
    assert result["excerptCount"] >= 1
    assert any("virtualserver" in cmd.lower() for cmd in result["recommendedCommands"])


def test_classify_sdx_destructive_commands():
    assert classify_sdx_command("force-stop virtualserver vpx1") == "destructive"
    assert classify_sdx_command("show version") == "read"
