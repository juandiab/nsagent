"""Load vendor manifests — single source of truth for JPilot brain layout."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

RESOURCES_ROOT = Path(__file__).resolve().parent.parent / "resources"
VENDORS_ROOT = RESOURCES_ROOT / "vendors"
DEFAULT_VENDOR_ID = "netscaler"

GLOBAL_TOOL_NAMES = frozenset(
    {
        "netscaler_list_inventory",
        "jpilot_check_doc_connectivity",
    }
)


@dataclass(frozen=True)
class VendorManifest:
    id: str
    label: str
    supported: bool
    connect_mode: str
    connect_test_tool: str
    connect_test_command: str
    memory_dir: Path
    memory_files: tuple[str, ...]
    architect_dir: Path | None
    prompts_dir: Path
    roles: tuple[str, ...]
    vendor_prefix: str
    mcp_tools: frozenset[str]
    search_tools: frozenset[str]
    analyst_blocked: frozenset[str]
    router: str
    reference_prompts: tuple[str, ...] = field(default_factory=tuple)

    @property
    def copilot_tool_names(self) -> frozenset[str]:
        return self.mcp_tools | self.search_tools

    @property
    def planning_tool_names(self) -> frozenset[str]:
        names = set(GLOBAL_TOOL_NAMES) | set(self.search_tools)
        if self.id == DEFAULT_VENDOR_ID:
            names.add("netscaler_list_inventory")
        return frozenset(names)

    @property
    def analyst_tool_names(self) -> frozenset[str]:
        return self.planning_tool_names | self.mcp_tools - self.analyst_blocked


def _parse_manifest(path: Path) -> VendorManifest:
    data = json.loads(path.read_text(encoding="utf-8"))
    vendor_id = data["id"]
    tools = data.get("tools") or {}
    memory_rel = data.get("memoryDir", f"memory/{vendor_id}")
    prompts_rel = data.get("promptsDir", f"prompts/{vendor_id}/roles")
    architect_rel = data.get("architectDir")
    connect = data.get("connect") or {}

    mcp_tools = frozenset(tools.get("mcpTools") or [])

    return VendorManifest(
        id=vendor_id,
        label=data.get("label", vendor_id),
        supported=bool(data.get("supported", False)),
        connect_mode=str(connect.get("mode", "ssh")),
        connect_test_tool=str(connect.get("testTool", "")),
        connect_test_command=str(connect.get("testCommand", "show version")),
        memory_dir=RESOURCES_ROOT / memory_rel,
        memory_files=tuple(data.get("memoryFiles") or ()),
        architect_dir=(RESOURCES_ROOT / architect_rel) if architect_rel else None,
        prompts_dir=RESOURCES_ROOT / prompts_rel,
        roles=tuple(data.get("roles") or ("operator",)),
        vendor_prefix=str(tools.get("vendorPrefix", f"{vendor_id}_")),
        mcp_tools=mcp_tools,
        search_tools=frozenset(tools.get("searchTools") or ()),
        analyst_blocked=frozenset(tools.get("analystBlocked") or ()),
        router=str(data.get("router", vendor_id)),
        reference_prompts=tuple(data.get("referencePrompts") or ()),
    )


@lru_cache(maxsize=1)
def load_vendor_manifests() -> dict[str, VendorManifest]:
    manifests: dict[str, VendorManifest] = {}
    if not VENDORS_ROOT.is_dir():
        return manifests
    for entry in sorted(VENDORS_ROOT.iterdir()):
        manifest_path = entry / "manifest.json"
        if entry.is_dir() and manifest_path.is_file():
            manifest = _parse_manifest(manifest_path)
            manifests[manifest.id] = manifest
    return manifests


def get_vendor_manifest(vendor: str | None) -> VendorManifest | None:
    vendor_id = (vendor or DEFAULT_VENDOR_ID).strip().lower()
    return load_vendor_manifests().get(vendor_id)


def get_supported_vendor_ids() -> frozenset[str]:
    return frozenset(vid for vid, manifest in load_vendor_manifests().items() if manifest.supported)


def is_vendor_copilot_supported(vendor: str | None) -> bool:
    manifest = get_vendor_manifest(vendor)
    return bool(manifest and manifest.supported)


def allowed_tool_names_for_vendor(vendor: str | None) -> frozenset[str]:
    manifest = get_vendor_manifest(vendor)
    if manifest and manifest.supported:
        return GLOBAL_TOOL_NAMES | manifest.copilot_tool_names
    return GLOBAL_TOOL_NAMES


def resolve_chat_vendor(
    *,
    appliance_vendor: str | None,
    role: str,
    appliance_name: str = "",
) -> str:
    if not appliance_name and role == "architect":
        return DEFAULT_VENDOR_ID
    normalized = (appliance_vendor or DEFAULT_VENDOR_ID).strip().lower()
    if is_vendor_copilot_supported(normalized):
        return normalized
    if role == "architect":
        return DEFAULT_VENDOR_ID
    return normalized


def validate_vendor_resources() -> list[str]:
    """Startup-style validation; returns list of warnings."""
    warnings: list[str] = []
    for manifest in load_vendor_manifests().values():
        if not manifest.supported:
            continue
        for filename in manifest.memory_files:
            path = manifest.memory_dir / filename
            if not path.is_file():
                warnings.append(f"Missing memory file: {path}")
        for role in manifest.roles:
            role_path = manifest.prompts_dir / f"{role}.md"
            if not role_path.is_file():
                warnings.append(f"Missing role prompt: {role_path}")
    return warnings
