from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CALIBRATIONS_DIR = Path("data/calibrations")


def _load_manifest(path: Path) -> dict[str, Any] | None:
    manifest_file = path / "manifest.json"
    if not manifest_file.is_file():
        return None
    try:
        return json.loads(manifest_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _message_matches_triggers(message: str, triggers: dict[str, Any]) -> bool:
    lowered = (message or "").lower()
    intents = triggers.get("intents") or []
    for intent in intents:
        if str(intent).lower() in lowered:
            return True
    commands = triggers.get("commands") or []
    for command in commands:
        if str(command).lower() in lowered:
            return True
    return False


def load_skill_prompt_fragment(skill_dir: Path, role: str) -> str | None:
    manifest = _load_manifest(skill_dir)
    if not manifest:
        return None

    includes = manifest.get("promptIncludes") or []
    role_file = f"prompts/{role}.md"
    if role_file.lstrip("prompts/") not in {p.replace("prompts/", "") for p in includes} and includes:
        if role_file not in includes:
            pass

    prompt_path = skill_dir / "prompts" / f"{role}.md"
    if prompt_path.is_file():
        return prompt_path.read_text(encoding="utf-8").strip()

    if includes:
        first = includes[0]
        alt = skill_dir / first
        if alt.is_file():
            return alt.read_text(encoding="utf-8").strip()
    return None


def load_skill_memory_excerpt(skill_dir: Path, role: str, *, max_chars: int = 4000) -> str:
    manifest = _load_manifest(skill_dir)
    if not manifest:
        return ""

    chunks: list[str] = []
    for module in manifest.get("memoryModules") or []:
        role_tags = module.get("roleTags") or []
        if role_tags and role not in role_tags:
            continue
        rel = module.get("filename") or module.get("path")
        if not rel:
            continue
        file_path = skill_dir / rel
        if file_path.is_file():
            chunks.append(file_path.read_text(encoding="utf-8").strip())

    combined = "\n\n".join(chunks).strip()
    if len(combined) <= max_chars:
        return combined
    return combined[: max_chars - 3].rstrip() + "..."


def match_installed_skills(
    *,
    user_message: str,
    role: str,
    vendor: str,
    installed: list[dict[str, Any]],
    limit: int = 2,
) -> list[dict[str, Any]]:
    matches: list[tuple[int, dict[str, Any]]] = []
    for row in installed:
        skill_vendor = str(row.get("vendor") or "")
        if skill_vendor and skill_vendor != vendor:
            continue

        skill_dir = Path(row.get("path") or "")
        manifest = _load_manifest(skill_dir) if skill_dir.is_dir() else None
        if not manifest:
            continue

        roles = manifest.get("roles") or []
        if roles and role not in roles:
            continue

        triggers = manifest.get("triggers") or {}
        score = 0
        if _message_matches_triggers(user_message, triggers):
            score += 100
        score += int(manifest.get("priority") or 0)

        if score > 0:
            matches.append((score, {**row, "manifest": manifest, "skillDir": str(skill_dir)}))

    matches.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in matches[:limit]]


def build_skill_injection_block(
    *,
    user_message: str,
    role: str,
    vendor: str,
    installed: list[dict[str, Any]],
) -> str | None:
    matched = match_installed_skills(
        user_message=user_message,
        role=role,
        vendor=vendor,
        installed=installed,
    )
    if not matched:
        return None

    sections: list[str] = ["## Matched calibration skills"]
    for row in matched:
        skill_dir = Path(row["skillDir"])
        manifest = row.get("manifest") or {}
        label = manifest.get("label") or row.get("skillId")
        sections.append(f"### {label} (`{manifest.get('id')}`)")

        prompt = load_skill_prompt_fragment(skill_dir, role)
        if prompt:
            sections.append(prompt)

        memory = load_skill_memory_excerpt(skill_dir, role)
        if memory:
            sections.append(memory)

    return "\n\n".join(sections).strip()
