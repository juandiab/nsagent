"""Load and search the NetScaler ADC CLI memory file for Copilot RAG."""

from __future__ import annotations

import re
from typing import Any

from pathlib import Path

from app.services.memory_paths import MEMORY_ROOT, get_memory_source_path as _memory_source_path
from app.services.memory_paths import memory_dir, memory_file_path, resolve_memory_file
from app.services.copilot_vendors import DEFAULT_COPILOT_VENDOR

MEMORY_FILENAME = "netscaler_adc_cli_memory.md"
MEMORY_VENDOR = DEFAULT_COPILOT_VENDOR


def _build_memory_candidate_paths() -> tuple[Path, ...]:
    """Paths checked for CLI memory index cache invalidation (newest mtime wins)."""
    seen: set[str] = set()
    candidates: list[Path] = []
    for path in (
        memory_file_path(MEMORY_FILENAME, MEMORY_VENDOR),
        memory_dir(MEMORY_VENDOR) / MEMORY_FILENAME,
        MEMORY_ROOT / MEMORY_VENDOR / MEMORY_FILENAME,
        MEMORY_ROOT / MEMORY_FILENAME,
    ):
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        candidates.append(path)
    return tuple(candidates)


MEMORY_CANDIDATE_PATHS: tuple[Path, ...] = _build_memory_candidate_paths()

_memory_cache: tuple[float, str] | None = None

CLI_VERBS = frozenset(
    {
        "add",
        "rm",
        "set",
        "unset",
        "show",
        "bind",
        "unbind",
        "enable",
        "disable",
        "stat",
        "clear",
        "rename",
        "link",
        "unlink",
        "import",
        "export",
        "update",
        "create",
        "save",
        "switch",
        "force",
        "sync",
        "flush",
        "count",
        "kill",
        "reset",
        "install",
        "apply",
        "diff",
        "batch",
        "source",
        "start",
        "stop",
        "get",
        "ping",
        "ping6",
        "traceroute",
        "traceroute6",
        "shell",
        "reboot",
        "shutdown",
    }
)

READONLY_VERBS = ("show ", "stat ", "get ", "count ", "ping ", "ping6 ", "traceroute ", "traceroute6 ")
WRITE_VERBS = ("add ns ip ", "add ns ip6 ")


def _load_memory_markdown() -> str:
    global _memory_cache
    path = resolve_memory_file(MEMORY_FILENAME, MEMORY_VENDOR)
    mtime = path.stat().st_mtime
    if _memory_cache and _memory_cache[0] == mtime:
        return _memory_cache[1]
    text = path.read_text(encoding="utf-8")
    _memory_cache = (mtime, text)
    return text


def get_memory_source_path() -> str:
    return _memory_source_path(MEMORY_FILENAME, MEMORY_VENDOR)


def _split_sections(markdown: str) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    current_title = "Overview"
    current_lines: list[str] = []

    for line in markdown.splitlines():
        if line.startswith("## "):
            if current_lines:
                sections.append({"title": current_title, "body": "\n".join(current_lines).strip()})
            current_title = line[3:].strip()
            current_lines = []
            continue
        if line.startswith("### "):
            if current_lines:
                sections.append({"title": current_title, "body": "\n".join(current_lines).strip()})
            current_title = f"{current_title} / {line[4:].strip()}"
            current_lines = []
            continue
        current_lines.append(line)

    if current_lines:
        sections.append({"title": current_title, "body": "\n".join(current_lines).strip()})
    return sections


def _terms(query: str) -> list[str]:
    cleaned = query.strip().lower().replace("routnig", "routing")
    found = [term for term in re.findall(r"[a-zA-Z0-9_/-]+", cleaned) if len(term) > 2]
    return found or [cleaned]


def _extract_readonly_commands(body: str) -> list[str]:
    commands: list[str] = []
    seen: set[str] = set()

    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        lowered = stripped.lower()
        if not any(lowered.startswith(verb) for verb in (*READONLY_VERBS, *WRITE_VERBS)):
            continue
        command = stripped.split("#", 1)[0].strip()
        command = " ".join(command.split())
        if len(command) > 120:
            continue
        normalized = command.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        commands.append(command)

    for match in re.finditer(r"`((?:show|stat|get|count)\s+[^`]{3,80})`", body, flags=re.IGNORECASE):
        command = " ".join(match.group(1).split())
        normalized = command.lower()
        if normalized not in seen:
            seen.add(normalized)
            commands.append(command)

    return commands


def get_cli_behavioral_rules() -> str:
    markdown = _load_memory_markdown()
    match = re.search(
        r"## 14\. CRITICAL BEHAVIORAL RULES FOR THE COPILOT\s+(.*?)(?=\n## |\Z)",
        markdown,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()
    return ""


def search_adc_cli_memory(
    query: str,
    max_sections: int = 2,
    max_chars_per_section: int = 600,
) -> dict[str, Any]:
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("Search query is required")

    from app.services.cli_command_index import score_section_for_query

    markdown = _load_memory_markdown()
    sections = _split_sections(markdown)
    terms = _terms(cleaned_query)

    ranked: list[tuple[int, dict[str, str]]] = []
    for section in sections:
        score = score_section_for_query(section["title"], section["body"], terms, cleaned_query)
        if score > 0:
            ranked.append((score, section))

    ranked.sort(key=lambda item: item[0], reverse=True)

    memory_excerpts: list[dict[str, str]] = []
    suggested_commands: list[str] = []
    seen_commands: set[str] = set()

    for _, section in ranked[:max_sections]:
        body = section["body"]
        if len(body) > max_chars_per_section:
            body = body[: max_chars_per_section - 3].rstrip() + "..."
        memory_excerpts.append({"title": section["title"], "content": body})
        for command in _extract_readonly_commands(section["body"]):
            key = command.lower()
            if key not in seen_commands:
                seen_commands.add(key)
                suggested_commands.append(command)

    if "statistics" in cleaned_query.lower() or "stat" in cleaned_query.lower():
        for command in suggested_commands:
            if command.lower().startswith("stat "):
                break
        else:
            for section in sections:
                for command in _extract_readonly_commands(section["body"]):
                    if command.lower().startswith("stat "):
                        key = command.lower()
                        if key not in seen_commands:
                            seen_commands.add(key)
                            suggested_commands.insert(0, command)

    if any(term in cleaned_query.lower() for term in ("add vip", "add ip", "new vip", "create vip")):
        if "add ns ip <ipaddress> <netmask> -type vip" not in {c.lower() for c in suggested_commands}:
            suggested_commands.insert(0, "add ns ip <IPAddress> <netmask> -type VIP")

    return {
        "sourceFile": get_memory_source_path(),
        "query": cleaned_query,
        "excerptCount": len(memory_excerpts),
        "memoryExcerpts": memory_excerpts,
        "suggestedCommands": suggested_commands[:8],
        "behavioralRulesIncluded": bool(get_cli_behavioral_rules()),
        "mustReviewMemoryFirst": True,
    }
