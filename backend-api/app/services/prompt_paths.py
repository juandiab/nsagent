"""Resolve paths to vendor-scoped JPilot prompt markdown files."""

from __future__ import annotations

from pathlib import Path

from app.services.vendor_registry import DEFAULT_VENDOR_ID, get_vendor_manifest

PROMPTS_ROOT = Path(__file__).resolve().parent.parent / "resources" / "prompts"

ROLE_PROMPT_NAMES = ("architect", "operator", "analyst")
ROLE_FRAGMENT_NAMES = (
    "shared_doc_rules",
    "architect_discovery",
    "operator_design_implementation_suffix",
)


def prompts_dir(vendor: str = DEFAULT_VENDOR_ID) -> Path:
    manifest = get_vendor_manifest(vendor)
    if manifest:
        return manifest.prompts_dir
    return PROMPTS_ROOT / vendor.strip().lower() / "roles"


def role_prompt_path(role: str, vendor: str = DEFAULT_VENDOR_ID) -> Path:
    return prompts_dir(vendor) / f"{role.strip().lower()}.md"


def role_fragment_path(fragment: str, vendor: str = DEFAULT_VENDOR_ID) -> Path:
    return prompts_dir(vendor) / f"{fragment.strip().lower()}.md"


def vendor_prompt_path(filename: str, vendor: str = DEFAULT_VENDOR_ID) -> Path:
    manifest = get_vendor_manifest(vendor)
    if manifest:
        return manifest.prompts_dir.parent / filename
    return PROMPTS_ROOT / vendor.strip().lower() / filename


def resolve_prompt_vendor(vendor: str | None) -> str:
    normalized = (vendor or DEFAULT_VENDOR_ID).strip().lower()
    if role_prompt_path("operator", normalized).is_file():
        return normalized
    return DEFAULT_VENDOR_ID
