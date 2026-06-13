from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings
from app.schemas.calibration_feedback import CalibrationFeedbackRequest
from app.services.calibration_feedback_redaction import redact_session_messages
from app.services.license_service import get_installation_fingerprint, license_document_id
from app.services.update_service import get_version_info

logger = logging.getLogger(__name__)

_FIRMWARE_SKILL_ID = "nexxus-netscaler-firmware-ha-upgrade"
_PLANNING_INTENT_RE = re.compile(
    r"planning intent:\s*(new_deployment|new_functionality|change_control)\b",
    re.IGNORECASE,
)
_FORM_COUNT_RE = re.compile(r"planning inputs for:", re.IGNORECASE)


class CalibrationFeedbackError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class CalibrationFeedbackResult:
    http_status: int
    payload: dict[str, Any]

    @property
    def feedback_id(self) -> str | None:
        value = self.payload.get("feedbackId")
        return str(value) if value else None


def infer_suggested_skill_id(*, user_goal: str, role: str, vendor: str) -> str | None:
    if vendor != "netscaler" or role != "architect":
        return None
    lowered = (user_goal or "").lower()
    if "firmware" in lowered and ("ha" in lowered or "upgrade" in lowered or "maintenance" in lowered):
        return _FIRMWARE_SKILL_ID
    if "change control" in lowered or "maintenance window" in lowered:
        return _FIRMWARE_SKILL_ID
    return None


def infer_planning_intent(messages: list[dict[str, Any]]) -> str | None:
    combined = "\n".join(str(item.get("content") or "") for item in messages if isinstance(item, dict))
    match = _PLANNING_INTENT_RE.search(combined)
    if match:
        return match.group(1).lower()
    lowered = combined.lower()
    if "firmware upgrade" in lowered or "maintenance window" in lowered:
        return "change_control"
    return None


def count_planning_form_submissions(messages: list[dict[str, Any]]) -> int:
    combined = "\n".join(str(item.get("content") or "") for item in messages if isinstance(item, dict))
    return len(_FORM_COUNT_RE.findall(combined))


def build_skill_feedback_payload(
    request: CalibrationFeedbackRequest,
    *,
    app_fingerprint: str,
    jpilot_version: str,
    client_id: str | None = None,
) -> dict[str, Any]:
    mask_ips = not request.includeApplianceName
    messages = [item.model_dump() for item in request.session.messages]
    suggested = request.suggestedSkillId or infer_suggested_skill_id(
        user_goal=request.userGoal,
        role=request.role,
        vendor=request.vendor,
    )
    diagnostics = request.diagnostics.model_dump(exclude_none=True) if request.diagnostics else {}
    if not diagnostics.get("planningIntent"):
        planning = infer_planning_intent(messages)
        if planning:
            diagnostics["planningIntent"] = planning
    if diagnostics.get("formSubmissionCount") is None:
        count = count_planning_form_submissions(messages)
        if count:
            diagnostics["formSubmissionCount"] = count

    return {
        "appFingerprint": app_fingerprint,
        "installSignature": None,
        "clientId": client_id,
        "jpilotVersion": jpilot_version,
        "objectiveMet": request.objectiveMet,
        "userGoal": request.userGoal.strip(),
        "vendor": request.vendor,
        "role": request.role,
        "category": request.category,
        "rating": request.rating,
        "userComment": request.userComment.strip(),
        "matchedSkills": request.matchedSkills,
        "suggestedSkillId": suggested,
        "includeApplianceName": request.includeApplianceName,
        "applianceName": request.applianceName if request.includeApplianceName else None,
        "session": {
            "sessionId": request.session.sessionId,
            "startedAt": request.session.startedAt,
            "messages": redact_session_messages(messages, mask_ips=mask_ips),
        },
        "diagnostics": diagnostics or None,
        "source": request.source,
    }


async def post_skill_feedback(payload: dict[str, Any]) -> CalibrationFeedbackResult:
    base = settings.nexxus_calibration_base_url.rstrip("/")
    url = f"{base}/skill-feedback"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=payload)
        except httpx.RequestError as exc:
            raise CalibrationFeedbackError(
                f"Could not reach Calibration Studio: {exc}",
            ) from exc

    try:
        body = response.json() if response.content else {}
    except ValueError:
        body = {}
    if not isinstance(body, dict):
        body = {}

    if response.status_code in (200, 202):
        return CalibrationFeedbackResult(response.status_code, body)

    detail = body.get("detail") or body.get("message") or response.text or f"HTTP {response.status_code}"
    raise CalibrationFeedbackError(str(detail)[:500], status_code=response.status_code)


async def submit_calibration_feedback(
    db,
    request: CalibrationFeedbackRequest,
) -> CalibrationFeedbackResult:
    if not settings.calibration_feedback_enabled:
        raise CalibrationFeedbackError("Calibration feedback is disabled on this installation.")

    fingerprint = await get_installation_fingerprint(db)
    app_fingerprint = fingerprint.get("fingerprint") or license_document_id()
    version = get_version_info().version

    license_doc = await db.licenses.find_one({"_id": app_fingerprint}) or {}
    client_id = str(license_doc.get("clientId") or license_doc.get("organizationId") or "").strip() or None

    payload = build_skill_feedback_payload(
        request,
        app_fingerprint=app_fingerprint,
        jpilot_version=version,
        client_id=client_id,
    )
    logger.info(
        "calibration_feedback submit fingerprint=%s role=%s category=%s messages=%d",
        app_fingerprint[:12],
        request.role,
        request.category,
        len(payload.get("session", {}).get("messages") or []),
    )
    return await post_skill_feedback(payload)
