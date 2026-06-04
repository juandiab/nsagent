"""Copilot tool and resource grouping by appliance vendor (manifest-driven)."""

from __future__ import annotations

from enum import StrEnum

from app.services.vendor_registry import (
    DEFAULT_VENDOR_ID,
    allowed_tool_names_for_vendor,
    get_supported_vendor_ids,
    is_vendor_copilot_supported,
    resolve_chat_vendor,
)

DEFAULT_COPILOT_VENDOR = DEFAULT_VENDOR_ID


class CopilotVendor(StrEnum):
    NETSCALER = "netscaler"
    F5 = "f5"
    CISCO = "cisco"


COPILOT_SUPPORTED_VENDORS = get_supported_vendor_ids()


def normalize_copilot_vendor(vendor: str | None) -> str:
    value = (vendor or DEFAULT_COPILOT_VENDOR).strip().lower()
    if value in COPILOT_SUPPORTED_VENDORS:
        return value
    if value in {CopilotVendor.F5.value, CopilotVendor.CISCO.value}:
        return value
    return DEFAULT_COPILOT_VENDOR


def copilot_vendor_is_supported(vendor: str | None) -> bool:
    return is_vendor_copilot_supported(vendor)


def filter_tools_by_vendor(tools: list[dict], vendor: str | None) -> list[dict]:
    allowed = allowed_tool_names_for_vendor(vendor)
    return [tool for tool in tools if tool.get("name") in allowed]
