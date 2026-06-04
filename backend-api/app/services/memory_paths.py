"""Resolve paths to JPilot memory (RAG) markdown files, grouped by vendor."""

from __future__ import annotations

from pathlib import Path

from app.services.vendor_registry import DEFAULT_VENDOR_ID, get_vendor_manifest

MEMORY_ROOT = Path(__file__).resolve().parent.parent / "resources" / "memory"


def memory_dir(vendor: str = DEFAULT_VENDOR_ID) -> Path:
    manifest = get_vendor_manifest(vendor)
    if manifest:
        return manifest.memory_dir
    return MEMORY_ROOT / vendor.strip().lower()


def architect_dir(vendor: str = DEFAULT_VENDOR_ID) -> Path:
    manifest = get_vendor_manifest(vendor)
    if manifest and manifest.architect_dir:
        return manifest.architect_dir
    return Path(__file__).resolve().parent.parent / "resources" / "architect" / vendor.strip().lower()


def memory_file_path(filename: str, vendor: str = DEFAULT_VENDOR_ID) -> Path:
    return memory_dir(vendor) / filename


def resolve_memory_file(filename: str, vendor: str = DEFAULT_VENDOR_ID) -> Path:
    path = memory_file_path(filename, vendor)
    if not path.is_file():
        raise FileNotFoundError(
            f"Memory file not found: {path}. Expected under {memory_dir(vendor)}."
        )
    return path


def get_memory_source_path(filename: str, vendor: str = DEFAULT_VENDOR_ID) -> str:
    path = memory_file_path(filename, vendor)
    return str(path if path.is_file() else path)


def list_memory_files(vendor: str = DEFAULT_VENDOR_ID) -> tuple[str, ...]:
    manifest = get_vendor_manifest(vendor)
    if manifest:
        return manifest.memory_files
    return ()
