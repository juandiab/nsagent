import base64
import re
from typing import Any

from app.schemas.copilot import ChatAttachment, CopilotSettings

MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_CONFIG_BYTES = 1 * 1024 * 1024
MAX_CONFIG_CHARS = 120_000

IMAGE_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/gif",
}

CONFIG_EXTENSIONS = {
    ".conf",
    ".cfg",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".xml",
    ".properties",
    ".ini",
    ".ns",
    ".cs",
    ".csv",
    ".md",
    ".markdown",
}


def validate_attachments(
    attachments: list[ChatAttachment],
    settings: CopilotSettings,
) -> None:
    if len(attachments) > settings.maxAttachments:
        raise ValueError(f"Maximum {settings.maxAttachments} attachments allowed per message")

    for attachment in attachments:
        if attachment.kind == "image":
            if not settings.allowImages:
                raise ValueError("Image attachments are disabled in Copilot settings")
            if attachment.mimeType not in IMAGE_MIME_TYPES:
                raise ValueError(f"Unsupported image type: {attachment.mimeType}")
            raw = _decode_base64(attachment.data)
            if len(raw) > MAX_IMAGE_BYTES:
                raise ValueError(f"Image '{attachment.name}' exceeds 5 MB limit")
        elif attachment.kind == "config":
            if not settings.allowConfigFiles:
                raise ValueError("Configuration file attachments are disabled in Copilot settings")
            _validate_config_attachment(attachment)
        else:
            raise ValueError(f"Unsupported attachment kind: {attachment.kind}")


def _decode_base64(data: str) -> bytes:
    try:
        return base64.b64decode(data, validate=True)
    except Exception as exc:
        raise ValueError("Invalid attachment encoding") from exc


def _validate_config_attachment(attachment: ChatAttachment) -> None:
    ext = _file_extension(attachment.name)
    if ext not in CONFIG_EXTENSIONS:
        raise ValueError(
            f"Unsupported config file type '{ext}'. "
            f"Allowed: {', '.join(sorted(CONFIG_EXTENSIONS))}"
        )

    if attachment.mimeType.startswith("text/") or attachment.mimeType in {
        "application/json",
        "application/xml",
        "application/yaml",
        "application/x-yaml",
        "application/markdown",
    }:
        content = _read_config_text(attachment)
        if len(content.encode("utf-8")) > MAX_CONFIG_BYTES:
            raise ValueError(f"Config file '{attachment.name}' exceeds 1 MB limit")
        if len(content) > MAX_CONFIG_CHARS:
            raise ValueError(f"Config file '{attachment.name}' exceeds character limit")
        return

    raise ValueError(f"Config file '{attachment.name}' must be a text-based format")


def _file_extension(filename: str) -> str:
    dot = filename.rfind(".")
    return filename[dot:].lower() if dot >= 0 else ""


def _read_config_text(attachment: ChatAttachment) -> str:
    raw = attachment.data
    if _looks_like_base64(raw):
        decoded = _decode_base64(raw)
        try:
            return decoded.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Config file '{attachment.name}' must be UTF-8 text") from exc
    return raw


def _looks_like_base64(value: str) -> bool:
    stripped = value.strip()
    if not stripped or len(stripped) % 4 != 0:
        return False
    return re.fullmatch(r"[A-Za-z0-9+/=\s]+", stripped) is not None


def _config_context_block(name: str, content: str) -> str:
    ext = _file_extension(name)
    if ext in {".md", ".markdown"}:
        return f"\n\n--- Attached design document: {name} ---\n{content}\n--- end ---\n"
    return f"\n\n--- Attached configuration: {name} ---\n{content}\n--- end ---\n"


def build_text_with_configs(message: str, attachments: list[ChatAttachment]) -> str:
    text = message
    for attachment in attachments:
        if attachment.kind == "config":
            text += _config_context_block(attachment.name, _read_config_text(attachment))
    return text


def build_openai_user_content(message: str, attachments: list[ChatAttachment]) -> str | list[dict[str, Any]]:
    image_attachments = [item for item in attachments if item.kind == "image"]
    text = build_text_with_configs(message, attachments)

    if not image_attachments:
        return text

    parts: list[dict[str, Any]] = [{"type": "text", "text": text}]
    for attachment in image_attachments:
        parts.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{attachment.mimeType};base64,{attachment.data.strip()}",
                },
            }
        )
    return parts


def build_anthropic_user_content(message: str, attachments: list[ChatAttachment]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = [{"type": "text", "text": build_text_with_configs(message, attachments)}]
    for attachment in attachments:
        if attachment.kind == "image":
            blocks.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": attachment.mimeType,
                        "data": attachment.data.strip(),
                    },
                }
            )
    return blocks


def build_gemini_user_parts(message: str, attachments: list[ChatAttachment]) -> list[dict[str, Any]]:
    parts: list[dict[str, Any]] = [{"text": build_text_with_configs(message, attachments)}]
    for attachment in attachments:
        if attachment.kind == "image":
            parts.append(
                {
                    "inline_data": {
                        "mime_type": attachment.mimeType,
                        "data": attachment.data.strip(),
                    }
                }
            )
    return parts
