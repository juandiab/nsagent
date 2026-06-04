"""Load and search the NetScaler Next-Gen API memory file for Copilot RAG."""

from __future__ import annotations

import re
from typing import Any

from app.services.memory_paths import get_memory_source_path as _memory_source_path
from app.services.memory_paths import resolve_memory_file
from app.services.copilot_vendors import DEFAULT_COPILOT_VENDOR

MEMORY_FILENAME = "netscaler_nextgen_api_memory.md"
MEMORY_VENDOR = DEFAULT_COPILOT_VENDOR

_memory_cache: tuple[float, str] | None = None


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
    cleaned = query.strip().lower()
    found = [term for term in re.findall(r"[a-zA-Z0-9_/-]+", cleaned) if len(term) > 2]
    return found or [cleaned]


def _score_section(title: str, body: str, terms: list[str]) -> int:
    haystack = f"{title}\n{body}".lower()
    return sum(1 for term in terms if term in haystack)


def _extract_get_paths(body: str) -> list[str]:
    paths: list[str] = []
    for match in re.finditer(r"GET /mgmt/api/nextgen/v1/([^\s`]+)", body, flags=re.IGNORECASE):
        path = match.group(1).strip().rstrip(".")
        if path and path not in paths:
            paths.append(path)
    for match in re.finditer(r"\|\s*GET\s*\|\s*`?(/mgmt/api/nextgen/v1/[^`|]+)`?\s*\|", body):
        path = match.group(1).replace("/mgmt/api/nextgen/v1/", "").strip()
        if path and path not in paths:
            paths.append(path)
    return paths


def _extract_post_paths(body: str) -> list[str]:
    paths: list[str] = []
    for match in re.finditer(r"POST /mgmt/api/nextgen/v1/([^\s`{]+)", body, flags=re.IGNORECASE):
        path = match.group(1).strip().rstrip(".")
        if path and path not in paths:
            paths.append(path)
    for match in re.finditer(r"\|\s*POST\s*\|\s*`?(/mgmt/api/nextgen/v1/[^`|]+)`?\s*\|", body):
        path = match.group(1).replace("/mgmt/api/nextgen/v1/", "").strip()
        if path and path not in paths:
            paths.append(path)
    return paths


def get_behavioral_rules() -> str:
    markdown = _load_memory_markdown()
    match = re.search(
        r"## 20\. IMPORTANT BEHAVIORAL RULES FOR THE COPILOT\s+(.*?)(?=\n## |\Z)",
        markdown,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()
    return ""


def search_nextgen_memory(query: str, max_sections: int = 6, max_chars_per_section: int = 1200) -> dict[str, Any]:
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
    suggested_get_paths: list[str] = []
    suggested_write_paths: list[str] = []
    seen_paths: set[str] = set()
    seen_write_paths: set[str] = set()

    for _, section in ranked[:max_sections]:
        body = section["body"]
        if len(body) > max_chars_per_section:
            body = body[: max_chars_per_section - 3].rstrip() + "..."
        memory_excerpts.append({"title": section["title"], "content": body})
        for path in _extract_get_paths(section["body"]):
            if path not in seen_paths:
                seen_paths.add(path)
                suggested_get_paths.append(path)
        for path in _extract_post_paths(section["body"]):
            if path not in seen_write_paths:
                seen_write_paths.add(path)
                suggested_write_paths.append(path)

    if not memory_excerpts and "endpoint" in cleaned_query.lower():
        for section in sections:
            if "COMPLETE ENDPOINT QUICK REFERENCE" in section["title"].upper():
                memory_excerpts.append(
                    {
                        "title": section["title"],
                        "content": section["body"][: max_chars_per_section - 3] + "...",
                    }
                )
                suggested_get_paths.extend(_extract_get_paths(section["body"]))
                suggested_write_paths.extend(_extract_post_paths(section["body"]))
                break

    create_terms = ("create", "add", "post", "application", "app")
    if any(term in cleaned_query.lower() for term in create_terms):
        if "applications" not in suggested_write_paths:
            suggested_write_paths.insert(0, "applications")

    return {
        "sourceFile": get_memory_source_path(),
        "query": cleaned_query,
        "excerptCount": len(memory_excerpts),
        "memoryExcerpts": memory_excerpts,
        "suggestedGetPaths": suggested_get_paths[:15],
        "suggestedWritePaths": suggested_write_paths[:10],
        "behavioralRulesIncluded": bool(get_behavioral_rules()),
    }


def suggest_path_for_nextgen_get(path: str) -> dict[str, Any] | None:
    """Return memory-backed guidance when a GET path looks wrong or incomplete."""
    normalized = path.strip().lstrip("/")
    if not normalized:
        return None

    markdown = _load_memory_markdown()
    if normalized in markdown:
        return None

    hints: list[str] = []
    if normalized == "routes":
        hints.append("Routes are nested: applications/{app_name}/routes")
    if normalized in {"frontends", "listeners", "backends", "servers"}:
        hints.append(f"{normalized} are nested under applications/{{app_name}}/...")
    if normalized in {"filter_value_sets", "filter-values", "filtervaluesets"}:
        hints.append("Use filters/value_sets for filter value sets")
    if normalized.startswith("responder_html"):
        hints.append("Use responder_html_page (singular) for HTML pages")

    memory = search_nextgen_memory(normalized.replace("/", " "), max_sections=3)
    if not hints and not memory["suggestedGetPaths"]:
        return None

    return {
        "requestedPath": normalized,
        "hints": hints,
        "suggestedGetPaths": memory["suggestedGetPaths"],
        "memoryExcerpts": memory["memoryExcerpts"],
    }
