"""Parse structured configuration forms embedded in assistant replies."""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.schemas.copilot import InputForm as ResponseInputForm


class SelectOption(BaseModel):
    value: str
    label: str


class InputFormField(BaseModel):
    id: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    label: str = Field(min_length=1, max_length=200)
    type: str = Field(default="text", pattern=r"^(text|number|textarea|boolean|select)$")
    required: bool = False
    placeholder: str = ""
    hint: str = ""
    default: str | bool | int | float | None = None
    options: list[SelectOption] = Field(default_factory=list)

    @field_validator("default", mode="before")
    @classmethod
    def normalize_default(cls, value: Any, info) -> Any:
        field_type = info.data.get("type")
        if field_type == "boolean":
            if isinstance(value, str):
                return value.strip().lower() in {"1", "true", "yes", "on"}
            return bool(value) if value is not None else None
        if value is None:
            return None
        return str(value)

    @field_validator("options", mode="before")
    @classmethod
    def normalize_options(cls, value: Any) -> list[dict[str, str]]:
        if not value:
            return []
        normalized: list[dict[str, str]] = []
        for item in value:
            if isinstance(item, dict):
                val = str(item.get("value", item.get("label", ""))).strip()
                label = str(item.get("label", val)).strip() or val
                if val:
                    normalized.append({"value": val, "label": label})
            elif item is not None:
                text = str(item).strip()
                if text:
                    normalized.append({"value": text, "label": text})
        return normalized


class InputForm(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    submitLabel: str = "Submit"
    fields: list[InputFormField] = Field(min_length=1, max_length=24)


LB_MONITOR_OPTIONS: list[dict[str, str]] = [
    {"value": "tcp-default", "label": "tcp-default"},
    {"value": "http", "label": "http"},
    {"value": "ping", "label": "ping"},
    {"value": "none", "label": "No monitor"},
]

LB_METHOD_OPTIONS: list[dict[str, str]] = [
    {"value": "LEASTCONNECTION", "label": "LEASTCONNECTION"},
    {"value": "ROUNDROBIN", "label": "ROUNDROBIN"},
    {"value": "SOURCEIP", "label": "SOURCEIP"},
]

LB_SERVICE_TYPE_OPTIONS: list[dict[str, str]] = [
    {"value": "HTTP", "label": "HTTP"},
    {"value": "SSL", "label": "SSL"},
    {"value": "TCP", "label": "TCP"},
    {"value": "UDP", "label": "UDP"},
    {"value": "SSL_BRIDGE", "label": "SSL_BRIDGE (SSL pass-through)"},
]

_LB_SELECT_FIELD_PRESETS: dict[str, list[dict[str, str]]] = {
    "monitor": LB_MONITOR_OPTIONS,
    "health_monitor": LB_MONITOR_OPTIONS,
    "lb_method": LB_METHOD_OPTIONS,
    "load_balancing_method": LB_METHOD_OPTIONS,
    "service_type": LB_SERVICE_TYPE_OPTIONS,
    "serviceType": LB_SERVICE_TYPE_OPTIONS,
    "protocol": LB_SERVICE_TYPE_OPTIONS,
}


def normalize_lb_form_fields(form: InputForm) -> InputForm:
    """Coerce known LB fields to select dropdowns when the model emits plain text fields."""
    updated_fields: list[InputFormField] = []
    changed = False
    for field in form.fields:
        preset_options = _LB_SELECT_FIELD_PRESETS.get(field.id)
        if preset_options and (field.type != "select" or not field.options):
            data = field.model_dump()
            data["type"] = "select"
            data["options"] = preset_options
            field = InputFormField.model_validate(data)
            changed = True
        updated_fields.append(field)
    if not changed:
        return form
    return InputForm.model_validate({**form.model_dump(), "fields": updated_fields})


_FORM_BLOCK = re.compile(r"```(?:json|jpilot-form)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)


def _extract_input_form_payload(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    raw_form = payload.get("inputForm")
    if isinstance(raw_form, dict):
        return raw_form
    if payload.get("fields"):
        return payload
    return None


def _validate_form(raw_form: dict[str, Any]) -> InputForm | None:
    try:
        return InputForm.model_validate(raw_form)
    except ValidationError:
        return None


def _find_balanced_json(content: str, start: int) -> tuple[int, int] | None:
    depth = 0
    in_string = False
    escape = False

    for index in range(start, len(content)):
        char = content[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return start, index + 1

    return None


def _find_raw_json_form(content: str) -> tuple[int, int, InputForm] | None:
    marker = '"inputForm"'
    search_from = 0
    while True:
        marker_index = content.find(marker, search_from)
        if marker_index == -1:
            return None

        start = content.rfind("{", 0, marker_index)
        if start == -1:
            search_from = marker_index + 1
            continue

        bounds = _find_balanced_json(content, start)
        if bounds is None:
            search_from = marker_index + 1
            continue

        json_start, json_end = bounds
        try:
            payload = json.loads(content[json_start:json_end])
        except json.JSONDecodeError:
            search_from = marker_index + 1
            continue

        raw_form = _extract_input_form_payload(payload)
        if raw_form is None:
            search_from = marker_index + 1
            continue

        form = _validate_form(raw_form)
        if form is None:
            search_from = marker_index + 1
            continue

        return json_start, json_end, normalize_lb_form_fields(form)

    return None


def parse_input_form(content: str) -> tuple[str, InputForm | None]:
    if not content:
        return content, None

    match = _FORM_BLOCK.search(content)
    if match:
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError:
            payload = None
        if payload is not None:
            raw_form = _extract_input_form_payload(payload)
            if raw_form is not None:
                form = _validate_form(raw_form)
                if form is not None:
                    cleaned = (content[: match.start()] + content[match.end() :]).strip()
                    return cleaned, normalize_lb_form_fields(form)

    raw_match = _find_raw_json_form(content)
    if raw_match is not None:
        json_start, json_end, form = raw_match
        cleaned = (content[:json_start] + content[json_end:]).strip()
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned, form

    return content, None


def format_form_submission(form: InputForm, values: dict[str, Any]) -> str:
    lines = [f"Configuration inputs for: {form.title}"]
    for field in form.fields:
        value = values.get(field.id)
        if field.type == "boolean":
            rendered = "yes" if value else "no"
        elif value is None or value == "":
            rendered = "(not provided)"
        else:
            rendered = str(value).strip()
        lines.append(f"- {field.label}: {rendered}")
    lines.append("")
    lines.append("Proceed with the configuration using these values.")
    return "\n".join(lines)


def to_response_input_form(form: InputForm | None) -> ResponseInputForm | None:
    """Convert parsed form model to the API response schema (distinct Pydantic classes)."""
    if form is None:
        return None
    return ResponseInputForm.model_validate(form.model_dump(mode="json"))


def is_form_submission(user_message: str) -> bool:
    return user_message.strip().startswith("Configuration inputs for:")


_LB_CREATE_VERBS = ("create", "add", "new", "setup", "set up", "configure", "provision")

# Policy, responder, rewrite, SSL bind, etc. — attach to existing vservers, not new LB provisioning.
_NON_LB_CONFIG_MARKERS = (
    "responder",
    "rewrite",
    "transform",
    "spillover",
    "bot policy",
    "appfw",
    "application firewall",
    "urlfilter",
    "url filter",
    "filter policy",
    "audit policy",
    "authentication policy",
    "authorization policy",
    "aaa policy",
    "compression policy",
    "cache policy",
    "cs policy",
    "content switching policy",
    "dns policy",
    "responder policy",
    "rewrite policy",
    "transform policy",
    "responder action",
    "rewrite action",
    "transform action",
    "policylabel",
    "policy label",
    "http to https",
    "http-to-https",
    "redirect all traffic",
    "certkey",
    "bind ssl",
    "ssl policy",
    "cipher suite",
    "ocsp",
    "rate limit",
    "stream identifier",
    "persistence",
)

_CREATE_POLICY_RE = re.compile(
    r"\b(?:create|add|set)\s+(?:a\s+)?(?:\w+\s+){0,3}policy\b",
    re.IGNORECASE,
)

_APPLY_OR_BIND_TO_VSERVER_RE = re.compile(
    r"\b(?:apply|bind|attach)\s+(?:it\s+)?(?:to\s+)?(?:the\s+)?(?:lb\s+)?vserver\b",
    re.IGNORECASE,
)

_CREATE_LB_VSERVER_RE = re.compile(
    r"\b(?:create|add|new|setup|set up|provision)\s+(?:a\s+)?(?:lb\s+)?(?:virtual\s+)?(?:load\s+)?server\b",
    re.IGNORECASE,
)

_LB_PROVISION_MARKERS = (
    "load balanc",
    "new lb",
    "new load",
    "add lb vserver",
    "create lb vserver",
    "create a lb",
    "add a lb",
    "service group",
    "backend ip",
    "backend server",
    "vip address",
    " with vip",
    "vip ",
)

_LB_WORKLOAD_MARKERS = (
    "delivery controller",
    "storefront",
    "front-end",
    "frontend",
)


def message_targets_policy_or_feature_config(user_message: str) -> bool:
    """True when the user is configuring policies/features on existing objects, not a new LB."""
    lowered = user_message.lower()
    if any(marker in lowered for marker in _NON_LB_CONFIG_MARKERS):
        return True
    if _CREATE_POLICY_RE.search(lowered):
        return True
    if _APPLY_OR_BIND_TO_VSERVER_RE.search(lowered):
        return True
    if re.search(r"\b(?:on|to)\s+(?:the\s+)?(?:lb\s+)?vserver\b", lowered):
        if "policy" in lowered or "redirect" in lowered or "action" in lowered:
            return True
    if re.search(r"\bbind\s+(?:service|server|member)\b", lowered) and "load balanc" not in lowered:
        return True
    return False


def user_requests_lb_vserver_create(user_message: str) -> bool:
    lowered = user_message.lower()
    if not any(verb in lowered for verb in _LB_CREATE_VERBS):
        return False
    if message_targets_policy_or_feature_config(user_message):
        return False
    if any(term in lowered for term in _LB_PROVISION_MARKERS):
        return True
    if any(term in lowered for term in _LB_WORKLOAD_MARKERS):
        return True
    if _CREATE_LB_VSERVER_RE.search(lowered):
        return True
    if any(term in lowered for term in ("lb vserver", "virtual server", "vserver")):
        if any(
            hint in lowered
            for hint in ("backend", "port ", "monitor", "service group", "with vip", "vip ")
        ):
            return True
    return False


def infer_workload_label(user_message: str) -> str:
    lowered = user_message.lower()
    if "delivery controller" in lowered or "ddc" in lowered:
        return "Delivery Controllers"
    if "storefront" in lowered:
        return "StoreFront"
    if "virtual delivery" in lowered or "vda" in lowered:
        return "Virtual Delivery Agents"
    if "citrix" in lowered:
        return "Citrix"
    return "Application"


def default_lb_vserver_form(workload_label: str = "Application") -> InputForm:
    """Standard classic LB vserver form when official docs lack workload-specific steps."""
    is_dc = "delivery" in workload_label.lower()
    return InputForm.model_validate(
        {
            "title": f"Load balancer — {workload_label}",
            "description": (
                "Classic NetScaler LB virtual server and service group. "
                "JPilot will search official CLI syntax, then apply these values."
            ),
            "submitLabel": "Create load balancer",
            "fields": [
                {
                    "id": "vserver_name",
                    "label": "Virtual server name",
                    "type": "text",
                    "required": True,
                    "placeholder": "lb_dc_01" if is_dc else "lb_app_01",
                },
                {
                    "id": "vip",
                    "label": "VIP address",
                    "type": "text",
                    "required": True,
                    "placeholder": "10.0.0.10",
                },
                {
                    "id": "service_type",
                    "label": "Service type",
                    "type": "select",
                    "required": True,
                    "default": "SSL" if is_dc else "HTTP",
                    "hint": "Classic NetScaler serviceType for the LB vserver and service group.",
                    "options": LB_SERVICE_TYPE_OPTIONS,
                },
                {
                    "id": "frontend_port",
                    "label": "Front-end port",
                    "type": "number",
                    "required": True,
                    "default": 443 if is_dc else 80,
                },
                {
                    "id": "ssl_offload",
                    "label": "SSL offload on NetScaler",
                    "type": "boolean",
                    "default": is_dc,
                },
                {
                    "id": "backend_ips",
                    "label": "Backend IP addresses (comma-separated)",
                    "type": "textarea",
                    "required": True,
                    "placeholder": "192.168.1.10, 192.168.1.11",
                },
                {
                    "id": "backend_port",
                    "label": "Backend port",
                    "type": "number",
                    "required": True,
                    "default": 80,
                },
                {
                    "id": "lb_method",
                    "label": "Load balancing method",
                    "type": "select",
                    "required": True,
                    "default": "LEASTCONNECTION",
                    "options": LB_METHOD_OPTIONS,
                },
                {
                    "id": "monitor",
                    "label": "Health monitor",
                    "type": "select",
                    "required": False,
                    "default": "tcp-default",
                    "options": LB_MONITOR_OPTIONS,
                },
            ],
        }
    )


def attach_default_lb_form_if_missing(
    user_message: str,
    content: str,
    form: InputForm | None,
) -> tuple[str, InputForm | None]:
    """Ensure LB create requests always return a renderable form when inputs are missing."""
    if form is not None:
        return content, normalize_lb_form_fields(form)
    if is_form_submission(user_message):
        return content, form
    if not user_requests_lb_vserver_create(user_message):
        return content, form

    workload = infer_workload_label(user_message)
    intro = content.strip()
    if not intro:
        intro = (
            f"I'll set up a load balancing virtual server for {workload}. "
            "Review the defaults below — JPilot searched official NetScaler patterns and "
            "falls back to a standard classic LB if none apply."
        )
    elif "jpilot-form" not in content.lower() and "inputform" not in content.lower():
        intro = (
            f"{intro}\n\n"
            f"Please confirm the load balancer settings for {workload}:"
        )

    return intro, default_lb_vserver_form(workload)
