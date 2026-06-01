import re
from typing import Any

import httpx

from app.services.nextgen_api_reference import (
    NEXTGEN_API_DOCS_URL,
    build_reference_index_text,
    flatten_operations,
    search_api_reference,
    suggest_read_paths_for_query,
)

NEXTGEN_GUIDE_URL = "https://developer-docs.netscaler.com/en-us/nextgen-api/getting-started-guide.html"
NEXTGEN_API_BASE = "/mgmt/api/nextgen/v1"

_GUIDE_CACHE: str | None = None
_REFERENCE_CACHE: str | None = None


def _strip_html(html: str) -> str:
    cleaned = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"<style[^>]*>.*?</style>", " ", cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


async def fetch_guide_text() -> str:
    global _GUIDE_CACHE
    if _GUIDE_CACHE:
        return _GUIDE_CACHE

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(NEXTGEN_GUIDE_URL)
        if response.status_code >= 400:
            raise ValueError(f"Could not fetch Next-Gen API guide (HTTP {response.status_code})")
        _GUIDE_CACHE = _strip_html(response.text)
        return _GUIDE_CACHE


def fetch_reference_index_text() -> str:
    global _REFERENCE_CACHE
    if _REFERENCE_CACHE is None:
        _REFERENCE_CACHE = build_reference_index_text()
    return _REFERENCE_CACHE


def _extract_api_paths(text: str) -> list[str]:
    paths = set(re.findall(r"/mgmt/api/nextgen/v1[/a-zA-Z0-9_{}-]+", text))
    for row in flatten_operations():
        paths.add(row["fullPath"])
    return sorted(paths)


def _score_sentence(sentence: str, terms: list[str]) -> int:
    lowered = sentence.lower()
    return sum(1 for term in terms if term in lowered)


async def search_nextgen_guide(query: str, max_excerpts: int = 8) -> dict[str, Any]:
    from app.services.nextgen_memory_service import search_nextgen_memory

    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("Search query is required")

    memory = search_nextgen_memory(cleaned_query)

    guide_text = await fetch_guide_text()
    reference_text = fetch_reference_index_text()
    combined_text = f"{guide_text} {reference_text}"

    terms = [term.lower() for term in re.findall(r"[a-zA-Z0-9_/-]+", cleaned_query) if len(term) > 2]
    if not terms:
        terms = [cleaned_query.lower()]

    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", combined_text) if part.strip()]
    ranked: list[tuple[int, str]] = []
    for sentence in sentences:
        score = _score_sentence(sentence, terms)
        if score:
            ranked.append((score, sentence))

    ranked.sort(key=lambda item: item[0], reverse=True)
    excerpts = [sentence for _, sentence in ranked[:max_excerpts]]

    paths = _extract_api_paths(combined_text)
    matching_paths = [
        path
        for path in paths
        if any(term.replace(" ", "") in path.lower() or term in path.lower() for term in terms)
    ]

    api_reference_matches = search_api_reference(cleaned_query, max_results=12)
    suggested_get_paths = list(memory.get("suggestedGetPaths") or [])
    for path in suggest_read_paths_for_query(cleaned_query):
        if path not in suggested_get_paths:
            suggested_get_paths.append(path)

    return {
        "guideUrl": NEXTGEN_GUIDE_URL,
        "apiDocsUrl": NEXTGEN_API_DOCS_URL,
        "memorySourceFile": memory.get("sourceFile"),
        "query": cleaned_query,
        "excerptCount": len(excerpts),
        "excerpts": excerpts,
        "memoryExcerptCount": memory.get("excerptCount", 0),
        "memoryExcerpts": memory.get("memoryExcerpts", []),
        "knownApiPaths": paths[:40],
        "matchingApiPaths": matching_paths[:20],
        "apiReferenceMatches": api_reference_matches,
        "suggestedGetPaths": suggested_get_paths[:20],
        "suggestedWritePaths": list(memory.get("suggestedWritePaths") or [])[:10],
        "apiBase": NEXTGEN_API_BASE,
        "mustReviewMemoryFirst": True,
    }
