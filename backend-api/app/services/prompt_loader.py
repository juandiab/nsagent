"""Load vendor- and role-specific system prompts from markdown files."""

from __future__ import annotations

import re
from functools import lru_cache

from app.services.copilot_vendors import DEFAULT_COPILOT_VENDOR
from app.services.prompt_paths import (
    role_fragment_path,
    role_prompt_path,
    resolve_prompt_vendor,
)

_INCLUDE_PATTERN = re.compile(r"\{\{include:([a-z_]+)\}\}")


@lru_cache(maxsize=32)
def _read_prompt_file(path_str: str) -> str:
    from pathlib import Path

    return Path(path_str).read_text(encoding="utf-8").strip()


def _load_fragment(fragment: str, vendor: str) -> str:
    path = role_fragment_path(fragment, vendor)
    if not path.is_file():
        raise FileNotFoundError(f"Prompt fragment not found: {path}")
    return _read_prompt_file(str(path))


def _expand_includes(text: str, vendor: str) -> str:
    expanded = text
    for _ in range(8):
        match = _INCLUDE_PATTERN.search(expanded)
        if not match:
            break
        fragment_name = match.group(1)
        replacement = _load_fragment(fragment_name, vendor)
        expanded = expanded.replace(match.group(0), replacement, 1)
    return expanded


def load_role_prompt(role: str, vendor: str | None = None) -> str:
    prompt_vendor = resolve_prompt_vendor(vendor)
    path = role_prompt_path(role, prompt_vendor)
    if not path.is_file():
        raise FileNotFoundError(f"Role prompt not found: {path}")
    template = _read_prompt_file(str(path))
    return _expand_includes(template, prompt_vendor)


def load_operator_design_implementation_suffix(appliance_name: str, vendor: str | None = None) -> str:
    prompt_vendor = resolve_prompt_vendor(vendor)
    template = _load_fragment("operator_design_implementation_suffix", prompt_vendor)
    return template.replace("{{appliance_name}}", appliance_name or "the connected appliance")
