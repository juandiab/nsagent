import re
from typing import Any

import httpx

from app.services.adc_cli_memory_service import get_cli_behavioral_rules, search_adc_cli_memory
from app.services.cli_command_catalog import (
    CLI_REFERENCE_ROOT,
    official_doc_url,
    search_command_catalog,
    topic_paths_for_query,
)

_PAGE_CACHE: dict[str, str] = {}


def _strip_html(html: str) -> str:
    cleaned = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"<style[^>]*>.*?</style>", " ", cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"<[^>]+>", "\n", cleaned)
    cleaned = re.sub(r"\n{2,}", "\n", cleaned)
    return cleaned.strip()


async def fetch_cli_topic_page(doc_path: str) -> str:
    if doc_path in _PAGE_CACHE:
        return _PAGE_CACHE[doc_path]

    url = official_doc_url(doc_path)
    async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as client:
        response = await client.get(url)
        if response.status_code >= 400:
            raise ValueError(f"Could not fetch ADC CLI topic page (HTTP {response.status_code})")
        _PAGE_CACHE[doc_path] = _strip_html(response.text)
        return _PAGE_CACHE[doc_path]


def _extract_section(text: str, section_title: str) -> str:
    pattern = re.compile(
        rf"{re.escape(section_title)}\s*(.*?)(?=\n## |\Z)",
        flags=re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return ""

    body = match.group(1)
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    useful: list[str] = []
    for line in lines[:12]:
        lowered = line.lower()
        if any(token in lowered for token in ("usage:", "show ", "stat ", "get ", "alias for")):
            useful.append(line)
        elif line.startswith("```"):
            continue
        elif len(useful) < 4 and len(line) < 180:
            useful.append(line)
    return " ".join(useful[:6])


async def build_recommended_commands(query: str, memory_commands: list[str]) -> list[dict[str, Any]]:
    catalog_hits = search_command_catalog(query)
    recommendations: list[dict[str, Any]] = []
    seen: set[str] = set()

    for command in memory_commands:
        key = command.lower()
        if key in seen:
            continue
        seen.add(key)
        recommendations.append(
            {
                "command": command,
                "topic": "From netscaler_adc_cli_memory.md",
                "docUrl": CLI_REFERENCE_ROOT,
                "source": "memory",
            }
        )

    for hit in catalog_hits:
        command = hit["command"]
        key = command.lower()
        if key in seen:
            continue
        seen.add(key)
        item: dict[str, Any] = {
            "command": command,
            "topic": hit.get("topic", ""),
            "docUrl": hit["docUrl"],
            "aliases": list(hit.get("aliases", ())),
            "invalidPatterns": list(hit.get("invalidPatterns", ())),
            "source": "catalog",
        }
        try:
            page_text = await fetch_cli_topic_page(hit["docPath"])
            excerpt = _extract_section(page_text, hit.get("section", hit["command"]))
            if excerpt:
                item["officialSyntax"] = excerpt
        except Exception:
            pass
        recommendations.append(item)

    return recommendations


async def search_cli_reference(query: str, max_excerpts: int = 6) -> dict[str, Any]:
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("Search query is required")

    memory = search_adc_cli_memory(cleaned_query)
    recommended_commands = await build_recommended_commands(
        cleaned_query,
        memory.get("suggestedCommands") or [],
    )

    excerpts: list[str] = []
    for excerpt in memory.get("memoryExcerpts") or []:
        excerpts.append(f"{excerpt['title']}: {excerpt['content'][:400]}")

    for command in recommended_commands:
        syntax = command.get("officialSyntax")
        if syntax:
            excerpts.append(f"{command['command']}: {syntax}")
        elif command.get("source") == "catalog":
            excerpts.append(f"{command['command']} — {command.get('topic', '')}")

        for alias in command.get("aliases", []):
            excerpts.append(f"Valid alias: {alias}")
        for invalid in command.get("invalidPatterns", []):
            excerpts.append(f"Invalid — do not use: {invalid}")

    topic_paths = topic_paths_for_query(cleaned_query)
    reference_url = official_doc_url(topic_paths[0]) if topic_paths else f"{CLI_REFERENCE_ROOT}/"

    return {
        "referenceUrl": reference_url,
        "referenceRoot": CLI_REFERENCE_ROOT,
        "memorySourceFile": memory.get("sourceFile"),
        "officialDocsOnly": True,
        "query": cleaned_query,
        "excerptCount": min(len(excerpts), max_excerpts),
        "excerpts": excerpts[:max_excerpts],
        "memoryExcerptCount": memory.get("excerptCount", 0),
        "memoryExcerpts": memory.get("memoryExcerpts", []),
        "recommendedCommands": recommended_commands,
        "matchingCommands": [item["command"] for item in recommended_commands],
        "suggestedCommands": memory.get("suggestedCommands", []),
        "topicPages": [official_doc_url(path) for path in topic_paths[:5]],
        "mustReviewMemoryFirst": True,
    }
