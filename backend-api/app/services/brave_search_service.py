import json
from typing import Any

import httpx


BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
NEXTGEN_SEARCH_PREFIX = "NetScaler Next-Gen API"

OFFICIAL_DOC_DOMAINS = (
    "developer-docs.netscaler.com",
    "docs.netscaler.com",
    "docs.citrix.com",
    "citrix.com",
    "netscaler.com",
)


def _is_official_doc_url(url: str) -> bool:
    lowered = (url or "").lower()
    return any(domain in lowered for domain in OFFICIAL_DOC_DOMAINS)


async def search_web(api_key: str, query: str, count: int = 5) -> str:
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("Search query is required")

    if NEXTGEN_SEARCH_PREFIX.lower() not in cleaned_query.lower():
        cleaned_query = f"{NEXTGEN_SEARCH_PREFIX} {cleaned_query}"

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }
    params = {
        "q": cleaned_query,
        "count": count,
        "search_lang": "en",
        "text_decorations": False,
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(BRAVE_SEARCH_URL, headers=headers, params=params)
        if response.status_code == 401:
            raise ValueError("Brave Search API key is invalid or unauthorized")
        if response.status_code >= 400:
            raise ValueError(response.text or f"Brave Search failed with HTTP {response.status_code}")
        payload = response.json()

    results = []
    web_results = (payload.get("web") or {}).get("results") or []
    for item in web_results[:count]:
        if not isinstance(item, dict):
            continue
        url = item.get("url", "")
        if url and not _is_official_doc_url(url):
            continue
        results.append(
            {
                "title": item.get("title", ""),
                "url": url,
                "description": item.get("description", ""),
            }
        )

    return json.dumps(
        {
            "query": cleaned_query,
            "resultCount": len(results),
            "results": results,
        },
        indent=2,
    )


async def test_brave_search(api_key: str) -> tuple[bool, str]:
    try:
        result = await search_web(api_key, "applications endpoint documentation", count=1)
        payload = json.loads(result)
        count = payload.get("resultCount", 0)
        if count:
            return True, f"Brave Search connected — {count} result(s) returned"
        return False, "Brave Search connected but returned no results"
    except Exception as exc:
        return False, str(exc)
