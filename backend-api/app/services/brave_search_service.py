import json
from typing import Any

import httpx


BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
NEXTGEN_SEARCH_PREFIX = "NetScaler Next-Gen API"

OFFICIAL_DOC_DOMAINS = (
    "developer-docs.netscaler.com",
    "docs.netscaler.com",
    "docs.citrix.com",
    "community.citrix.com",
    "citrix.com",
    "netscaler.com",
)


def _is_allowed_url(url: str, allowed_domains: tuple[str, ...]) -> bool:
    lowered = (url or "").lower()
    return any(domain in lowered for domain in allowed_domains)


async def search_web(
    api_key: str,
    query: str,
    count: int = 5,
    *,
    allowed_domains: list[str] | tuple[str, ...] | None = None,
    topic_hint: str = NEXTGEN_SEARCH_PREFIX,
) -> str:
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("Search query is required")

    domains = tuple(allowed_domains) if allowed_domains else OFFICIAL_DOC_DOMAINS

    if topic_hint and topic_hint.lower() not in cleaned_query.lower():
        cleaned_query = f"{topic_hint} {cleaned_query}"

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }
    params = {
        "q": cleaned_query,
        "count": max(count, 10),
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
    for item in web_results:
        if not isinstance(item, dict):
            continue
        url = item.get("url", "")
        if url and not _is_allowed_url(url, domains):
            continue
        results.append(
            {
                "title": item.get("title", ""),
                "url": url,
                "description": item.get("description", ""),
            }
        )
        if len(results) >= count:
            break

    return json.dumps(
        {
            "query": cleaned_query,
            "allowedDomains": list(domains),
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
