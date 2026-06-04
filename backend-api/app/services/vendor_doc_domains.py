"""Official documentation domains per appliance vendor (web search isolation)."""

from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorDatabase

# NetScaler / Citrix — used only for netscaler and sdx chat vendors.
NETSCALER_DOC_DOMAINS: tuple[str, ...] = (
    "developer-docs.netscaler.com",
    "docs.netscaler.com",
    "docs.citrix.com",
    "community.citrix.com",
    "citrix.com",
    "netscaler.com",
)

# Cisco — used only for cisco vendor searches.
CISCO_DOC_DOMAINS: tuple[str, ...] = (
    "cisco.com",
    "docs.cisco.com",
    "learningnetwork.cisco.com",
    "community.cisco.com",
    "developer.cisco.com",
    "support.cisco.com",
)

# F5 — used only for f5 vendor searches.
F5_DOC_DOMAINS: tuple[str, ...] = (
    "f5.com",
    "clouddocs.f5.com",
    "techdocs.f5.com",
    "devcentral.f5.com",
    "support.f5.com",
    "my.f5.com",
)

VENDOR_DOC_DOMAINS: dict[str, tuple[str, ...]] = {
    "netscaler": NETSCALER_DOC_DOMAINS,
    "sdx": NETSCALER_DOC_DOMAINS,
    "cisco": CISCO_DOC_DOMAINS,
    "f5": F5_DOC_DOMAINS,
}

# Backward-compatible alias for settings UI and NetScaler-only callers.
LOCKED_DOMAINS = NETSCALER_DOC_DOMAINS


def locked_domains_for_vendor(vendor: str | None) -> tuple[str, ...]:
    normalized = (vendor or "netscaler").strip().lower()
    return VENDOR_DOC_DOMAINS.get(normalized, NETSCALER_DOC_DOMAINS)


async def get_allowed_domains_for_vendor(db: AsyncIOMotorDatabase, vendor: str | None) -> list[str]:
    """Return locked vendor domains plus admin extra domains (NetScaler/Citrix baseline only)."""
    document = await db.copilotPlatformSettings.find_one({"_id": "default"}) or {}
    locked = locked_domains_for_vendor(vendor)
    if (vendor or "netscaler").strip().lower() not in {"netscaler", "sdx"}:
        return list(locked)
    extra = [d for d in document.get("extraDomains", []) if d not in locked]
    return list(locked) + extra


def all_locked_domain_groups() -> dict[str, list[str]]:
    return {vendor: list(domains) for vendor, domains in VENDOR_DOC_DOMAINS.items()}
