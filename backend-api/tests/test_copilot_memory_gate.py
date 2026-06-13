"""Tests for copilot memory review gates."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.copilot_memory_gate import (  # noqa: E402
    apply_memory_review_gates,
    nextgen_memory_review_required,
)


def test_list_ip_addresses_does_not_require_nextgen_memory_search():
    assert nextgen_memory_review_required("netscaler_list_ip_addresses") is False


def test_curated_inventory_reads_skip_nextgen_memory_gate():
    for tool_name in (
        "netscaler_get_system_info",
        "netscaler_list_applications",
        "netscaler_list_virtual_servers",
        "netscaler_list_virtual_ips",
        "netscaler_list_ip_addresses",
        "netscaler_list_service_status",
    ):
        assert nextgen_memory_review_required(tool_name) is False


def test_generic_nextgen_get_still_requires_memory_search():
    assert nextgen_memory_review_required("netscaler_nextgen_get") is True


def test_list_ip_addresses_allowed_without_prior_search():
    allowed, blocked = apply_memory_review_gates(
        "netscaler_list_ip_addresses",
        nextgen_memory_reviewed=False,
        cli_memory_reviewed=True,
    )
    assert allowed is True
    assert blocked is None
