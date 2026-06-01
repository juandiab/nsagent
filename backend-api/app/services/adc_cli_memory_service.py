"""Load and search the NetScaler ADC CLI memory file for Copilot RAG."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

MEMORY_FILENAME = "netscaler_adc_cli_memory.md"

MEMORY_CANDIDATE_PATHS = (
    Path(__file__).resolve().parent.parent / "resources" / MEMORY_FILENAME,
    Path(__file__).resolve().parents[3] / MEMORY_FILENAME,
)

_memory_cache: tuple[float, str] | None = None

READONLY_VERBS = ("show ", "stat ", "get ", "count ")
WRITE_VERBS = ("add ns ip ", "add ns ip6 ")


def _load_memory_markdown() -> str:
    global _memory_cache
    for path in MEMORY_CANDIDATE_PATHS:
        if path.is_file():
            mtime = path.stat().st_mtime
            if _memory_cache and _memory_cache[0] == mtime:
                return _memory_cache[1]
            text = path.read_text(encoding="utf-8")
            _memory_cache = (mtime, text)
            return text
    raise FileNotFoundError(
        f"NetScaler ADC CLI memory file not found. Expected one of: "
        f"{', '.join(str(p) for p in MEMORY_CANDIDATE_PATHS)}"
    )


def get_memory_source_path() -> str:
    for path in MEMORY_CANDIDATE_PATHS:
        if path.is_file():
            return str(path)
    return str(MEMORY_CANDIDATE_PATHS[0])


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


def _score_section(title: str, body: str, terms: list[str]) -> int:
    haystack = f"{title}\n{body}".lower()
    return sum(1 for term in terms if term in haystack)


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


def search_adc_cli_memory(query: str, max_sections: int = 6, max_chars_per_section: int = 1200) -> dict[str, Any]:
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("Search query is required")

    markdown = _load_memory_markdown()
    sections = _split_sections(markdown)
    terms = _terms(cleaned_query)

    ranked: list[tuple[int, dict[str, str]]] = []
    for section in sections:
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
        "suggestedCommands": suggested_commands[:20],
        "behavioralRulesIncluded": bool(get_cli_behavioral_rules()),
        "mustReviewMemoryFirst": True,
    }
