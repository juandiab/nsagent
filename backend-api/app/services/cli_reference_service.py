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
from app.services.cli_command_index import (
    is_strong_command_match,
    is_workflow_query,
    search_command_index,
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


def _catalog_hit_for_command(catalog_hits: list[dict], command: str) -> dict | None:
    command_lower = command.lower()
    for hit in catalog_hits:
        if hit.get("command", "").lower() == command_lower:
            return hit
    command_prefix = " ".join(command_lower.split()[:3])
    for hit in catalog_hits:
        if hit.get("command", "").lower().startswith(command_prefix):
            return hit
    return None


async def build_recommended_commands(
    query: str,
    command_candidates: list[str],
    *,
    catalog_hits: list[dict] | None = None,
    index_hits: list[dict] | None = None,
    max_fetch_pages: int = 1,
    max_results: int = 3,
    prefer_index: bool = False,
) -> list[dict[str, Any]]:
    catalog_hits = catalog_hits if catalog_hits is not None else search_command_catalog(query, max_results=max_results)
    recommendations: list[dict[str, Any]] = []
    seen: set[str] = set()
    pages_fetched = 0

    async def append_catalog_hit(hit: dict) -> None:
        nonlocal pages_fetched
        command = hit["command"]
        key = command.lower()
        if key in seen:
            return
        seen.add(key)
        item: dict[str, Any] = {
            "command": command,
            "topic": hit.get("topic", ""),
            "docUrl": hit["docUrl"],
            "aliases": list(hit.get("aliases", ())),
            "invalidPatterns": list(hit.get("invalidPatterns", ())),
            "source": "catalog",
        }
        if pages_fetched < max_fetch_pages:
            try:
                page_text = await fetch_cli_topic_page(hit["docPath"])
                excerpt = _extract_section(page_text, hit.get("section", hit["command"]))
                if excerpt:
                    item["officialSyntax"] = excerpt
                pages_fetched += 1
            except Exception:
                pass
        recommendations.append(item)

    async def append_index_hit(entry: dict) -> None:
        nonlocal pages_fetched
        command = entry["command"]
        key = command.lower()
        if key in seen:
            return
        seen.add(key)
        catalog_match = _catalog_hit_for_command(catalog_hits, command)
        item: dict[str, Any] = {
            "command": command,
            "topic": entry.get("section", "From netscaler_adc_cli_memory.md"),
            "docUrl": catalog_match["docUrl"] if catalog_match else CLI_REFERENCE_ROOT,
            "source": "index",
        }
        if catalog_match and pages_fetched < max_fetch_pages:
            try:
                page_text = await fetch_cli_topic_page(catalog_match["docPath"])
                excerpt = _extract_section(page_text, catalog_match.get("section", catalog_match["command"]))
                if excerpt:
                    item["officialSyntax"] = excerpt
                pages_fetched += 1
            except Exception:
                pass
        recommendations.append(item)

    if prefer_index:
        for entry in index_hits or []:
            await append_index_hit(entry)
            if len(recommendations) >= max_results:
                return recommendations
        for hit in catalog_hits:
            await append_catalog_hit(hit)
            if len(recommendations) >= max_results:
                return recommendations
    else:
        for hit in catalog_hits:
            await append_catalog_hit(hit)
            if len(recommendations) >= max_results:
                return recommendations
        for entry in index_hits or []:
            await append_index_hit(entry)
            if len(recommendations) >= max_results:
                return recommendations

    for command in command_candidates:
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
        if len(recommendations) >= max_results:
            break

    return recommendations


async def search_cli_reference(query: str, max_commands: int = 3) -> dict[str, Any]:
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("Search query is required")

    index_hits = search_command_index(cleaned_query, max_results=max_commands)
    catalog_hits = search_command_catalog(cleaned_query, max_results=max_commands)
    strong_index = is_strong_command_match(index_hits, cleaned_query)
    strong_match = strong_index or bool(catalog_hits)
    workflow_query = is_workflow_query(cleaned_query)

    if strong_match and not workflow_query:
        memory = search_adc_cli_memory(cleaned_query, max_sections=0)
    elif strong_match:
        memory = search_adc_cli_memory(cleaned_query, max_sections=1, max_chars_per_section=800)
    else:
        memory = search_adc_cli_memory(cleaned_query, max_sections=2, max_chars_per_section=600)

    command_candidates = [hit["command"] for hit in index_hits]
    command_candidates.extend(memory.get("suggestedCommands") or [])

    max_fetch_pages = 1 if strong_match else 2
    recommended_commands = await build_recommended_commands(
        cleaned_query,
        command_candidates,
        catalog_hits=catalog_hits,
        index_hits=index_hits,
        max_fetch_pages=max_fetch_pages,
        max_results=max_commands,
        prefer_index=strong_index,
    )

    retrieval_mode = "command" if strong_match and not workflow_query else "section"
    memory_excerpts = memory.get("memoryExcerpts") or []

    excerpts: list[str] = []
    if retrieval_mode == "section":
        for excerpt in memory_excerpts:
            excerpts.append(f"{excerpt['title']}: {excerpt['content'][:400]}")
        for command in recommended_commands[:2]:
            syntax = command.get("officialSyntax")
            if syntax:
                excerpts.append(f"{command['command']}: {syntax}")

    topic_paths = topic_paths_for_query(cleaned_query)
    reference_url = official_doc_url(topic_paths[0]) if topic_paths else f"{CLI_REFERENCE_ROOT}/"

    return {
        "referenceUrl": reference_url,
        "referenceRoot": CLI_REFERENCE_ROOT,
        "memorySourceFile": memory.get("sourceFile"),
        "officialDocsOnly": True,
        "query": cleaned_query,
        "retrievalMode": retrieval_mode,
        "excerptCount": len(excerpts),
        "excerpts": excerpts,
        "memoryExcerptCount": len(memory_excerpts),
        "memoryExcerpts": memory_excerpts,
        "recommendedCommands": recommended_commands,
        "matchingCommands": [item["command"] for item in recommended_commands],
        "commandIndexHits": [
            {"command": hit["command"], "namespace": hit.get("namespace"), "score": hit.get("score")}
            for hit in index_hits
        ],
        "suggestedCommands": (memory.get("suggestedCommands") or [])[:max_commands],
        "topicPages": [official_doc_url(path) for path in topic_paths[:3]],
        "behavioralRules": get_cli_behavioral_rules() if workflow_query else "",
        "mustReviewMemoryFirst": True,
    }
