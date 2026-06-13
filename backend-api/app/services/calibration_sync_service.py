from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.services.license_service import get_installation_fingerprint, license_document_id

CALIBRATIONS_DIR = Path("data/calibrations")
COLLECTION = "stack_calibrations"


class CalibrationSyncError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class CalibrationSyncResult:
    installed: int
    updated: int
    removed: int
    skills: list[dict[str, Any]]


def _calibrations_root() -> Path:
    return CALIBRATIONS_DIR


def _safe_segment(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", (value or "").strip())
    return cleaned or "unknown"


async def ensure_calibration_indexes(db: AsyncIOMotorDatabase) -> None:
    await db[COLLECTION].create_index([("skillId", 1), ("version", 1)], unique=True)
    await db[COLLECTION].create_index([("enabled", 1)])


def list_installed_skills() -> list[dict[str, Any]]:
    root = _calibrations_root()
    if not root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for skill_dir in sorted(root.iterdir()):
        if not skill_dir.is_dir():
            continue
        for version_dir in sorted(skill_dir.iterdir()):
            manifest_file = version_dir / "manifest.json"
            if manifest_file.is_file():
                try:
                    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    continue
                rows.append(
                    {
                        "skillId": manifest.get("id") or skill_dir.name,
                        "version": manifest.get("version") or version_dir.name,
                        "label": manifest.get("label") or skill_dir.name,
                        "vendor": manifest.get("vendor"),
                        "path": str(version_dir),
                    }
                )
    return rows


def _write_skill_bundle(skill_id: str, version: str, bundle: dict[str, Any]) -> Path:
    target = _calibrations_root() / _safe_segment(skill_id) / _safe_segment(version)
    target.mkdir(parents=True, exist_ok=True)

    manifest = bundle.get("manifest") or {}
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    for rel_path, content in (bundle.get("files") or {}).items():
        file_path = target / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(str(content), encoding="utf-8")

    return target


async def _upsert_calibration_index(
    db: AsyncIOMotorDatabase,
    *,
    skill_id: str,
    version: str,
    vendor: str | None,
    label: str | None,
) -> None:
    now = datetime.now(timezone.utc)
    await db[COLLECTION].update_one(
        {"skillId": skill_id, "version": version},
        {
            "$set": {
                "skillId": skill_id,
                "version": version,
                "vendor": vendor,
                "label": label,
                "enabled": True,
                "path": str(_calibrations_root() / _safe_segment(skill_id) / _safe_segment(version)),
                "updatedAt": now,
            },
            "$setOnInsert": {"installedAt": now},
        },
        upsert=True,
    )


async def sync_calibrations_from_studio(db: AsyncIOMotorDatabase) -> CalibrationSyncResult:
    if not settings.calibration_sync_enabled:
        raise CalibrationSyncError("Calibration sync is disabled on this installation.")

    fingerprint = await get_installation_fingerprint(db)
    app_fingerprint = fingerprint.get("fingerprint") or license_document_id()

    installed_versions = {
        row["skillId"]: row["version"]
        for row in list_installed_skills()
        if row.get("skillId") and row.get("version")
    }

    base = settings.nexxus_calibration_base_url.rstrip("/")
    sync_url = f"{base}/calibrations/sync"
    body = {
        "appFingerprint": app_fingerprint,
        "appName": settings.jpilot_app_name,
        "installedVersions": installed_versions,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(sync_url, json=body)
        except httpx.RequestError as exc:
            raise CalibrationSyncError(f"Could not reach Calibration Studio: {exc}") from exc

    if response.status_code >= 400:
        raise CalibrationSyncError(
            f"Calibration sync failed ({response.status_code}): {(response.text or '')[:300]}",
            status_code=response.status_code,
        )

    payload = response.json() if response.content else {}
    skills = payload.get("skills") or []
    removed = payload.get("removed") or []

    updated = 0
    installed = 0
    for skill in skills:
        skill_id = str(skill.get("id") or "")
        version = str(skill.get("version") or "")
        bundle_url = str(skill.get("bundleUrl") or "")
        if not skill_id or not version or not bundle_url:
            continue

        bundle_path = bundle_url if bundle_url.startswith("/") else f"/{bundle_url}"
        fetch_url = f"{base}{bundle_path}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            bundle_response = await client.get(fetch_url)
        if bundle_response.status_code >= 400:
            continue
        bundle = bundle_response.json()

        _write_skill_bundle(skill_id, version, bundle)
        await _upsert_calibration_index(
            db,
            skill_id=skill_id,
            version=version,
            vendor=(bundle.get("manifest") or {}).get("vendor"),
            label=skill.get("label") or (bundle.get("manifest") or {}).get("label"),
        )
        if installed_versions.get(skill_id) == version:
            installed += 1
        else:
            updated += 1

    return CalibrationSyncResult(
        installed=installed,
        updated=updated,
        removed=len(removed),
        skills=skills,
    )
