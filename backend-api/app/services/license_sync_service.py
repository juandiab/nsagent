from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings


def normalize_license_sync_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Flatten Nexxus bodies that nest license fields under ``detail``."""
    if not isinstance(payload, dict):
        return {}
    detail = payload.get("detail")
    if isinstance(detail, dict):
        merged = {key: value for key, value in payload.items() if key != "detail"}
        merged.update(detail)
        return merged
    if isinstance(detail, str) and detail.strip():
        merged = {key: value for key, value in payload.items() if key != "detail"}
        merged.setdefault("message", detail.strip())
        return merged
    return payload


class LicenseSyncError(Exception):
    """Unexpected sync failure (network, wrong code, or unhandled HTTP status)."""

    def __init__(self, message: str, *, status_code: int | None = None, payload: dict[str, Any] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload or {}


@dataclass(frozen=True)
class LicenseSyncResult:
    http_status: int
    payload: dict[str, Any]

    @property
    def status(self) -> str:
        return str(self.payload.get("status") or "").strip().lower()

    @property
    def message(self) -> str:
        return str(self.payload.get("message") or self.payload.get("detail") or "").strip()

    @property
    def is_success(self) -> bool:
        return self.http_status == 200 and self.status in ("active", "renewed")

    @property
    def is_terminal(self) -> bool:
        """License no longer usable locally (expired, deactivated, or removed)."""
        if self.http_status == 404:
            return True
        return self.http_status == 403 and self.status in ("expired", "deactivated")


async def post_license_sync(
    *,
    app_fingerprint: str,
    app_name: str,
    license_code: str | None,
) -> LicenseSyncResult:
    base = settings.nexxus_licensing_base_url.rstrip("/")
    url = f"{base}/licensing/sync"
    body: dict[str, str] = {
        "appFingerprint": app_fingerprint,
        "appName": app_name,
        "licenseCode": (license_code or "").strip(),
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=body)
        except httpx.RequestError as exc:
            raise LicenseSyncError(f"Could not reach the license server: {exc}") from exc

    try:
        payload = response.json() if response.content else {}
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    payload = normalize_license_sync_payload(payload)

    if response.status_code == 200:
        return LicenseSyncResult(200, payload)

    if response.status_code == 404:
        detail = str(payload.get("detail") or "No license found for this deployment.")
        return LicenseSyncResult(
            404,
            {
                "status": "missing",
                "message": detail,
                "detail": detail,
            },
        )

    if response.status_code == 403:
        status = str(payload.get("status") or "").strip().lower()
        if status in ("expired", "deactivated"):
            return LicenseSyncResult(403, payload)
        detail = str(payload.get("detail") or "License verification was denied.")
        raise LicenseSyncError(detail, status_code=403, payload=payload)

    detail = payload.get("detail") or payload.get("message")
    if not detail and response.text:
        detail = response.text.strip()[:300]
    if not detail:
        detail = f"License sync failed ({response.status_code})."
    raise LicenseSyncError(str(detail), status_code=response.status_code, payload=payload)
