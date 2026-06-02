"""Backend self-connectivity checks: can the JPilot server itself reach the docs/web?

This is distinct from appliance reachability (ping/telnet from a NetScaler). The doc
fetch, getting-started guide, and Brave web search all egress from THIS backend, so
"can you reach the documentation?" must be answered from here, not from an appliance.
"""

import time

import httpx

DOC_TARGETS = (
    "https://developer-docs.netscaler.com/",
    "https://docs.netscaler.com/",
    "https://docs.citrix.com/",
)
BRAVE_HOST = "https://api.search.brave.com/"


async def _probe(client: httpx.AsyncClient, url: str) -> dict:
    started = time.perf_counter()
    try:
        response = await client.head(url)
        return {
            "url": url,
            "reachable": True,
            "status": response.status_code,
            "latencyMs": round((time.perf_counter() - started) * 1000),
        }
    except Exception as exc:
        return {"url": url, "reachable": False, "error": str(exc)[:200]}


async def check_doc_connectivity(db) -> dict:
    from app.services.copilot_platform_service import get_platform_settings

    doc_results: list[dict] = []
    web: dict = {}

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        for url in DOC_TARGETS:
            doc_results.append(await _probe(client, url))

        settings = await get_platform_settings(db)
        web = {
            "configured": settings.hasBraveSearchApiKey,
            "enabled": settings.allowWebSearch and settings.hasBraveSearchApiKey,
        }
        if web["enabled"]:
            # Connection-level reach only (a 401 here still proves we reached Brave) —
            # we do NOT spend a search query just to check reachability.
            probe = await _probe(client, BRAVE_HOST)
            web["providerReachable"] = probe.get("reachable", False)

    reachable = [r for r in doc_results if r.get("reachable")]
    return {
        "source": "JPilot backend server (NOT a NetScaler appliance)",
        "transport": "HTTPS",
        "docsReachable": bool(reachable),
        "docDomains": doc_results,
        "webSearch": web,
        "summary": (
            f"The JPilot backend reached {len(reachable)}/{len(doc_results)} official documentation "
            f"domain(s) over HTTPS."
        ),
    }
