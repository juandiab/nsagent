"""Load and search F5 BIG-IP TMSH memory for Copilot RAG."""

from __future__ import annotations

import re
from typing import Any

from app.services.vendor_registry import get_vendor_manifest

MEMORY_FILENAME = "f5_bigip_tmsh_memory.md"
MEMORY_VENDOR = "f5"

_memory_cache: tuple[float, str] | None = None


def _memory_path():
    manifest = get_vendor_manifest(MEMORY_VENDOR)
    if manifest:
        return manifest.memory_dir / MEMORY_FILENAME
    from app.services.memory_paths import memory_file_path

    return memory_file_path(MEMORY_FILENAME, MEMORY_VENDOR)


def _load_memory_markdown() -> str:
    global _memory_cache
    path = _memory_path()
    if not path.is_file():
        raise FileNotFoundError(f"F5 memory file not found: {path}")
    mtime = path.stat().st_mtime
    if _memory_cache and _memory_cache[0] == mtime:
        return _memory_cache[1]
    text = path.read_text(encoding="utf-8")
    _memory_cache = (mtime, text)
    return text


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
        current_lines.append(line)
    if current_lines:
        sections.append({"title": current_title, "body": "\n".join(current_lines).strip()})
    return sections


def _terms(query: str) -> list[str]:
    cleaned = query.strip().lower()
    found = [term for term in re.findall(r"[a-zA-Z0-9_/-]+", cleaned) if len(term) > 2]
    return found or [cleaned]


def _score_section(title: str, body: str, terms: list[str]) -> int:
    haystack = f"{title}\n{body}".lower()
    return sum(1 for term in terms if term in haystack)


def _extract_commands(body: str) -> list[str]:
    commands: list[str] = []
    seen: set[str] = set()
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("|"):
            continue
        lowered = stripped.lower()
        if lowered.startswith(
            (
                "tmsh show ",
                "tmsh list ",
                "tmsh create ",
                "tmsh modify ",
                "show ",
                "list ",
                "ping ",
                "traceroute ",
            )
        ):
            command = stripped.split("#", 1)[0].strip()
            if not command.lower().startswith("tmsh "):
                command = f"tmsh {command}"
            key = command.lower()
            if key not in seen and len(command) <= 160:
                seen.add(key)
                commands.append(command)
    return commands


def search_f5_tmsh_memory(
    query: str,
    max_sections: int = 3,
    max_chars_per_section: int = 700,
) -> dict[str, Any]:
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("Search query is required")

    markdown = _load_memory_markdown()
    terms = _terms(cleaned_query)
    ranked: list[tuple[int, dict[str, str]]] = []
    for section in _split_sections(markdown):
        score = _score_section(section["title"], section["body"], terms)
        if score:
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
        for command in _extract_commands(section["body"]):
            key = command.lower()
            if key not in seen_commands:
                seen_commands.add(key)
                suggested_commands.append(command)

    return {
        "sourceFile": str(_memory_path()),
        "vendor": MEMORY_VENDOR,
        "query": cleaned_query,
        "excerptCount": len(memory_excerpts),
        "memoryExcerpts": memory_excerpts,
        "recommendedCommands": suggested_commands[:8],
        "mustReviewMemoryFirst": True,
    }
