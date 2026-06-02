"""Command-level index for NetScaler ADC CLI memory — atomic retrieval."""

from __future__ import annotations

import re
from typing import Any

from app.services.adc_cli_memory_service import (
    CLI_VERBS,
    MEMORY_CANDIDATE_PATHS,
    _load_memory_markdown,
    _split_sections,
    _terms,
)

_index_cache: tuple[float, list[dict[str, Any]]] | None = None

NAMESPACE_HINTS: dict[str, tuple[str, ...]] = {
    "ssl": ("ssl", "tls", "cert", "certificate", "certkey", "cipher", "sni", "ocsp", "crl"),
    "lb": ("lb", "load", "balancing", "balancer", "vserver", "virtual", "monitor", "persistence"),
    "cs": ("cs", "content", "switch", "switching"),
    "cr": ("cr", "cache", "redirection"),
    "ns": ("ns", "nsip", "snip", "vip", "feature", "mode", "version", "license", "runningconfig"),
    "vpn": ("vpn", "gateway", "ica", "citrix", "session"),
    "ha": ("ha", "high", "availability", "failover", "sync"),
    "route": ("route", "routing", "gateway", "static"),
    "vlan": ("vlan", "layer2", "l2"),
    "interface": ("interface", "nic", "link", "duplex"),
    "arp": ("arp", "mac", "neighbor"),
    "basic": ("service", "servicegroup", "server", "nstrace"),
    "appfw": ("appfw", "waf", "firewall"),
    "aaa": ("aaa", "authentication", "authorization"),
    "gslb": ("gslb", "dns", "global"),
    "rewrite": ("rewrite", "responder"),
    "system": ("system", "user", "rbac", "cmdpolicy"),
}

GENERIC_SECTION_MARKERS: tuple[str, ...] = (
    "cli fundamentals",
    "standard verbs",
    "universal command grammar",
    "namespace index",
    "operation matrix",
    "pixl / policy expression",
    "parameter conventions",
)

WORKFLOW_QUERY_TERMS: tuple[str, ...] = (
    "setup",
    "configure",
    "create",
    "workflow",
    "sequence",
    "multi-step",
    "set up",
    "full sequence",
)

STRONG_MATCH_SCORE = 8


def _memory_mtime() -> float:
    for path in MEMORY_CANDIDATE_PATHS:
        if path.is_file():
            return path.stat().st_mtime
    return 0.0


def _normalize_command(line: str) -> str:
    command = line.split("#", 1)[0].strip()
    return " ".join(command.split())


def _is_cli_command(text: str) -> bool:
    normalized = _normalize_command(text)
    if not normalized or len(normalized) > 200:
        return False
    return normalized.split()[0].lower() in CLI_VERBS


def _extract_namespace(command: str) -> str:
    tokens = command.strip().split()
    if len(tokens) < 2:
        return ""
    if tokens[0].lower() not in CLI_VERBS:
        return ""
    return tokens[1].lower()


def _derive_keywords(command: str, namespace: str, section: str) -> list[str]:
    terms = set(re.findall(r"[a-zA-Z0-9_]+", command.lower()))
    if namespace:
        terms.add(namespace)
        terms.update(NAMESPACE_HINTS.get(namespace, ()))
    section_leaf = section.rsplit(" / ", 1)[-1].lower()
    for ns, hints in NAMESPACE_HINTS.items():
        if f"`{ns}`" in section_leaf or section_leaf.startswith(f"{ns} "):
            terms.update(hints)
    return sorted(term for term in terms if len(term) > 1)


def _add_entry(
    command: str,
    section_title: str,
    entries: list[dict[str, Any]],
    seen: set[str],
) -> None:
    key = command.lower()
    if key in seen:
        return
    seen.add(key)
    namespace = _extract_namespace(command)
    entries.append(
        {
            "command": command,
            "namespace": namespace,
            "section": section_title,
            "keywords": _derive_keywords(command, namespace, section_title),
        }
    )


def _extract_commands_from_body(body: str, section_title: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    in_codeblock = False
    pending = ""

    def flush_pending() -> None:
        nonlocal pending
        if not pending:
            return
        cmd = _normalize_command(pending)
        pending = ""
        if cmd and _is_cli_command(cmd):
            _add_entry(cmd, section_title, entries, seen)

    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_pending()
            in_codeblock = not in_codeblock
            continue

        if not stripped:
            if not in_codeblock:
                flush_pending()
            continue

        if stripped.startswith("#") and not in_codeblock:
            flush_pending()
            continue

        if line.startswith((" ", "\t")) and pending:
            pending += " " + stripped
            continue

        flush_pending()

        if in_codeblock or _is_cli_command(stripped):
            pending = stripped

    flush_pending()

    verb_pattern = "|".join(re.escape(verb) for verb in sorted(CLI_VERBS, key=len, reverse=True))
    for match in re.finditer(rf"`(({verb_pattern})\s+[^`]{{3,120}})`", body, flags=re.IGNORECASE):
        cmd = _normalize_command(match.group(1))
        _add_entry(cmd, section_title, entries, seen)

    return entries


def build_command_index() -> list[dict[str, Any]]:
    global _index_cache
    mtime = _memory_mtime()
    if _index_cache and _index_cache[0] == mtime:
        return _index_cache[1]

    markdown = _load_memory_markdown()
    sections = _split_sections(markdown)
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()

    for section in sections:
        for entry in _extract_commands_from_body(section["body"], section["title"]):
            key = entry["command"].lower()
            if key in seen:
                continue
            seen.add(key)
            entries.append(entry)

    _index_cache = (mtime, entries)
    return entries


def detect_query_namespaces(terms: list[str], query: str) -> set[str]:
    detected: set[str] = set()
    blob = query.lower()
    if "load balancer" in blob or "load balancing" in blob:
        detected.add("lb")
    for ns, hints in NAMESPACE_HINTS.items():
        if ns in blob.split() or any(hint in blob for hint in hints):
            detected.add(ns)
    for term in terms:
        if term in NAMESPACE_HINTS:
            detected.add(term)
    return detected


def is_workflow_query(query: str) -> bool:
    lowered = query.lower()
    return any(term in lowered for term in WORKFLOW_QUERY_TERMS)


def _score_entry(
    entry: dict[str, Any],
    terms: list[str],
    query_lower: str,
    namespaces: set[str],
) -> int:
    command_lower = entry["command"].lower()
    section_lower = entry.get("section", "").lower()
    score = 0

    if query_lower in command_lower:
        score += 15

    score += sum(3 for term in terms if term in command_lower)
    score += sum(1 for term in terms if term in entry.get("keywords", []))

    namespace = entry.get("namespace", "")
    if namespace and namespace in namespaces:
        score += 8

    query_tokens = query_lower.split()
    cmd_tokens = command_lower.split()
    if len(query_tokens) >= 2 and len(cmd_tokens) >= 2:
        if query_tokens[0] == cmd_tokens[0] and query_tokens[1] == cmd_tokens[1]:
            score += 10
        elif query_tokens[0] == cmd_tokens[0]:
            score += 4

    if query_lower.startswith("show ") and command_lower.startswith("show "):
        score += 3
    if "stat" in query_lower and command_lower.startswith("stat "):
        score += 3
    if "create" in query_lower and command_lower.startswith("add "):
        score += 3

    entity_terms = [term for term in terms if term not in {"create", "setup", "configure", "show", "stat", "add"}]
    if entity_terms and all(term in command_lower for term in entity_terms):
        score += 12

    if any(marker in section_lower for marker in GENERIC_SECTION_MARKERS):
        score -= 8 if namespaces else 4

    if "<entity>" in command_lower or command_lower in {"show <entity>", "stat <entity>"}:
        score -= 20

    return score


def search_command_index(query: str, max_results: int = 3) -> list[dict[str, Any]]:
    cleaned = query.strip()
    if not cleaned:
        return []

    terms = _terms(cleaned)
    query_lower = cleaned.lower()
    namespaces = detect_query_namespaces(terms, cleaned)
    index = build_command_index()

    ranked: list[tuple[int, dict[str, Any]]] = []
    for entry in index:
        score = _score_entry(entry, terms, query_lower, namespaces)
        if score > 0:
            ranked.append((score, entry))

    ranked.sort(key=lambda item: (-item[0], item[1]["command"]))
    results: list[dict[str, Any]] = []
    for score, entry in ranked[:max_results]:
        row = dict(entry)
        row["score"] = score
        results.append(row)
    return results


def is_strong_command_match(hits: list[dict[str, Any]], query: str = "") -> bool:
    if not hits or hits[0].get("score", 0) < STRONG_MATCH_SCORE:
        return False
    if not query:
        return True
    tokens = query.strip().lower().split()
    if len(tokens) < 2:
        return True
    top_cmd = hits[0]["command"].lower()
    entity_terms = [token for token in tokens[1:] if len(token) > 2]
    if entity_terms and not all(token in top_cmd for token in entity_terms):
        return False
    return True


def score_section_for_query(title: str, body: str, terms: list[str], query: str) -> int:
    """Namespace-aware section scoring used as fallback when command index is weak."""
    haystack = f"{title}\n{body}".lower()
    score = sum(2 for term in terms if term in haystack)
    namespaces = detect_query_namespaces(terms, query)
    title_lower = title.lower()

    for namespace in namespaces:
        if namespace in title_lower or f"`{namespace}`" in title_lower:
            score += 6

    if any(marker in title_lower for marker in GENERIC_SECTION_MARKERS):
        score -= 8 if namespaces else 3

    return score
