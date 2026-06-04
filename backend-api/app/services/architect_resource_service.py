"""Search Architect role reference markdown (design outline, integration refs)."""

from __future__ import annotations

import re
from typing import Any

from app.services.vendor_registry import DEFAULT_VENDOR_ID
from app.services.memory_paths import architect_dir

ARCHITECT_FILES = (
    "jpilot_architect_design_outline.md",
    "jpilot_architect_citrix_integration_refs.md",
)


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


def search_architect_resources(
    query: str,
    *,
    vendor: str = DEFAULT_VENDOR_ID,
    max_sections: int = 4,
    max_chars_per_section: int = 900,
) -> dict[str, Any]:
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("Search query is required")

    resource_dir = architect_dir(vendor)
    terms = _terms(cleaned_query)
    ranked: list[tuple[int, str, dict[str, str]]] = []

    for filename in ARCHITECT_FILES:
        path = resource_dir / filename
        if not path.is_file():
            continue
        markdown = path.read_text(encoding="utf-8")
        for section in _split_sections(markdown):
            score = _score_section(section["title"], section["body"], terms)
            if score:
                ranked.append((score, filename, section))

    ranked.sort(key=lambda item: item[0], reverse=True)

    excerpts: list[dict[str, str]] = []
    for _, filename, section in ranked[:max_sections]:
        body = section["body"]
        if len(body) > max_chars_per_section:
            body = body[: max_chars_per_section - 3].rstrip() + "..."
        excerpts.append({"sourceFile": filename, "title": section["title"], "content": body})

    return {
        "vendor": vendor,
        "query": cleaned_query,
        "excerptCount": len(excerpts),
        "excerpts": excerpts,
        "sourceFiles": list(ARCHITECT_FILES),
    }
