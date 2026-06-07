"""Track JPilot LLM and Brave Search usage for the settings dashboard."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger("model_usage")

from app.models.ai_provider import parse_object_id, serialize_ai_provider
from app.schemas.model_usage import (
    BraveUsageItem,
    ModelUsageDashboardResponse,
    ProviderUsageItem,
    UsageLimitsUpdate,
)
from app.services.copilot_platform_service import get_platform_settings

USAGE_LIMITS_ID = "default"
BRAVE_COUNTER_ID = "brave"

DEFAULT_BRAVE_MONTHLY_QUERIES = 2000

# Suggested monthly caps when the admin has not set custom limits (local tracking only).
DEFAULT_TOKEN_LIMIT_BY_TYPE: dict[str, int | None] = {
    "OpenAI": 1_000_000,
    "Anthropic": 1_000_000,
    "Gemini": 1_000_000,
    "Grok": 500_000,
    "DeepSeek": 500_000,
    "OpenRouter": 1_000_000,
    "Azure OpenAI": 1_000_000,
    "AWS Bedrock": 1_000_000,
    "LM Studio": None,
    "OpenAI-Compatible": None,
}

DEFAULT_REQUEST_LIMIT_BY_TYPE: dict[str, int | None] = {
    "OpenAI": 5_000,
    "Anthropic": 5_000,
    "Gemini": 5_000,
    "Grok": 3_000,
    "DeepSeek": 3_000,
    "OpenRouter": 5_000,
    "Azure OpenAI": 5_000,
    "AWS Bedrock": 5_000,
    "LM Studio": None,
    "OpenAI-Compatible": None,
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def current_period_key(now: datetime | None = None) -> str:
    moment = now or utc_now()
    return moment.strftime("%Y-%m")


def period_label(period_key: str) -> str:
    try:
        year, month = period_key.split("-", 1)
        month_index = int(month)
        return datetime(int(year), month_index, 1, tzinfo=timezone.utc).strftime("%B %Y")
    except (ValueError, TypeError):
        return period_key


def _provider_counter_id(provider_id: str) -> str:
    return f"provider:{provider_id}"


def _counter_document_id(counter_key: str, period_key: str) -> str:
    return f"{counter_key}:{period_key}"


def extract_llm_usage_details(provider_type: str, data: dict[str, Any]) -> dict[str, int]:
    if not isinstance(data, dict):
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    if provider_type == "Anthropic":
        usage = data.get("usage") or {}
        input_tokens = int(usage.get("input_tokens") or 0)
        output_tokens = int(usage.get("output_tokens") or 0)
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        }

    if provider_type == "Gemini":
        for metadata in (
            data.get("usageMetadata"),
            ((data.get("candidates") or [{}])[0]).get("usageMetadata"),
        ):
            if isinstance(metadata, dict) and metadata:
                input_tokens = int(metadata.get("promptTokenCount") or 0)
                output_tokens = int(
                    metadata.get("candidatesTokenCount") or metadata.get("responseTokenCount") or 0
                )
                total = metadata.get("totalTokenCount")
                total_tokens = int(total) if total is not None else input_tokens + output_tokens
                return {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                }
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    usage = data.get("usage") or {}
    input_tokens = int(usage.get("prompt_tokens") or 0)
    output_tokens = int(usage.get("completion_tokens") or 0)
    total = usage.get("total_tokens")
    total_tokens = int(total) if total is not None else input_tokens + output_tokens
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


def extract_token_usage(provider_type: str, data: dict[str, Any]) -> int:
    return extract_llm_usage_details(provider_type, data)["total_tokens"]


def _percent(used: int, limit: int | None) -> float | None:
    if limit is None or limit <= 0:
        return None
    return round(min(100.0, (used / limit) * 100.0), 1)


def _remaining(used: int, limit: int | None) -> int | None:
    if limit is None:
        return None
    return max(0, limit - used)


async def ensure_usage_limits(db: AsyncIOMotorDatabase) -> dict[str, Any]:
    existing = await db.usageLimits.find_one({"_id": USAGE_LIMITS_ID})
    if existing is None:
        doc = {
            "_id": USAGE_LIMITS_ID,
            "braveMonthlyQueryLimit": DEFAULT_BRAVE_MONTHLY_QUERIES,
            "providers": {},
            "updatedAt": utc_now(),
        }
        await db.usageLimits.insert_one(doc)
        return doc
    return existing


async def get_provider_limits(db: AsyncIOMotorDatabase, provider_id: str) -> dict[str, int | None]:
    doc = await ensure_usage_limits(db)
    entry = (doc.get("providers") or {}).get(provider_id) or {}
    return {
        "monthlyTokenLimit": entry.get("monthlyTokenLimit"),
        "monthlyRequestLimit": entry.get("monthlyRequestLimit"),
    }


def resolve_limits(
    provider_type: str,
    custom: dict[str, int | None],
) -> tuple[int | None, int | None, bool]:
    token_limit = custom.get("monthlyTokenLimit")
    request_limit = custom.get("monthlyRequestLimit")
    if token_limit is None:
        token_limit = DEFAULT_TOKEN_LIMIT_BY_TYPE.get(provider_type)
    if request_limit is None:
        request_limit = DEFAULT_REQUEST_LIMIT_BY_TYPE.get(provider_type)
    unlimited = token_limit is None and request_limit is None
    return token_limit, request_limit, unlimited


async def _get_counter(
    db: AsyncIOMotorDatabase,
    counter_key: str,
    period_key: str,
) -> dict[str, Any]:
    doc = await db.modelUsageCounters.find_one({"_id": _counter_document_id(counter_key, period_key)})
    if doc is None:
        return {"requests": 0, "tokens": 0, "queries": 0}
    return {
        "requests": int(doc.get("requests") or 0),
        "tokens": int(doc.get("tokens") or 0),
        "queries": int(doc.get("queries") or 0),
    }


async def record_provider_usage(
    db: AsyncIOMotorDatabase,
    *,
    provider_id: str,
    tokens: int = 0,
    requests: int = 1,
) -> None:
    period_key = current_period_key()
    counter_key = _provider_counter_id(provider_id)
    doc_id = _counter_document_id(counter_key, period_key)
    await db.modelUsageCounters.update_one(
        {"_id": doc_id},
        {
            "$inc": {"requests": requests, "tokens": max(0, tokens)},
            "$set": {"updatedAt": utc_now(), "period": period_key, "counterKey": counter_key},
            "$setOnInsert": {"_id": doc_id},
        },
        upsert=True,
    )


async def record_brave_search_usage(db: AsyncIOMotorDatabase, *, queries: int = 1) -> None:
    period_key = current_period_key()
    doc_id = _counter_document_id(BRAVE_COUNTER_ID, period_key)
    await db.modelUsageCounters.update_one(
        {"_id": doc_id},
        {
            "$inc": {"queries": max(0, queries)},
            "$set": {"updatedAt": utc_now(), "period": period_key, "counterKey": BRAVE_COUNTER_ID},
            "$setOnInsert": {"_id": doc_id},
        },
        upsert=True,
    )


async def record_llm_response_usage(
    db: AsyncIOMotorDatabase,
    *,
    provider_id: str,
    provider_type: str,
    response_data: dict[str, Any],
) -> None:
    tokens = extract_token_usage(provider_type, response_data)
    await record_provider_usage(db, provider_id=provider_id, tokens=tokens, requests=1)


@dataclass
class UsageAccumulator:
    """In-memory totals for one JPilot chat turn; flushed to MongoDB after the LLM loop."""

    requests: int = 0
    tokens: int = 0

    def add_llm_response(self, provider_type: str, response_data: dict[str, Any]) -> None:
        self.requests += 1
        self.tokens += extract_token_usage(provider_type, response_data)


async def flush_usage_accumulator(
    db: AsyncIOMotorDatabase,
    provider_id: str,
    accumulator: UsageAccumulator,
) -> None:
    if not provider_id:
        return
    try:
        if accumulator.requests > 0:
            await record_provider_usage(
                db,
                provider_id=provider_id,
                tokens=accumulator.tokens,
                requests=accumulator.requests,
            )
            logger.info(
                "usage_recorded provider=%s requests=%s tokens=%s period=%s",
                provider_id,
                accumulator.requests,
                accumulator.tokens,
                current_period_key(),
            )
    except Exception:
        logger.exception("usage_record_failed provider=%s", provider_id)


async def update_usage_limits(db: AsyncIOMotorDatabase, payload: UsageLimitsUpdate) -> None:
    await ensure_usage_limits(db)
    update: dict[str, Any] = {"updatedAt": utc_now()}

    if payload.braveMonthlyQueryLimit is not None:
        update["braveMonthlyQueryLimit"] = payload.braveMonthlyQueryLimit

    if payload.providers:
        doc = await db.usageLimits.find_one({"_id": USAGE_LIMITS_ID}) or {}
        providers = dict(doc.get("providers") or {})
        for item in payload.providers:
            try:
                parse_object_id(item.providerId)
            except ValueError:
                continue
            providers[item.providerId] = {
                "monthlyTokenLimit": item.monthlyTokenLimit,
                "monthlyRequestLimit": item.monthlyRequestLimit,
            }
        update["providers"] = providers

    await db.usageLimits.update_one({"_id": USAGE_LIMITS_ID}, {"$set": update}, upsert=True)


async def get_usage_dashboard(db: AsyncIOMotorDatabase) -> ModelUsageDashboardResponse:
    period_key = current_period_key()
    limits_doc = await ensure_usage_limits(db)
    platform = await get_platform_settings(db)

    brave_limit = limits_doc.get("braveMonthlyQueryLimit", DEFAULT_BRAVE_MONTHLY_QUERIES)
    brave_counter = await _get_counter(db, BRAVE_COUNTER_ID, period_key)
    brave_used = brave_counter["queries"]
    brave_unlimited = brave_limit is None
    brave_percent = _percent(brave_used, brave_limit)

    brave_item = BraveUsageItem(
        configured=platform.hasBraveSearchApiKey,
        enabled=platform.allowWebSearch and platform.hasBraveSearchApiKey,
        queriesUsed=brave_used,
        monthlyQueryLimit=brave_limit,
        percent=brave_percent,
        remainingQueries=_remaining(brave_used, brave_limit),
        unlimited=brave_unlimited,
    )

    provider_items: list[ProviderUsageItem] = []
    cursor = db.aiProviders.find().sort("providerName", 1)
    async for doc in cursor:
        serialized = serialize_ai_provider(doc)
        provider_id = serialized["id"]
        custom = (limits_doc.get("providers") or {}).get(provider_id) or {}
        token_limit, request_limit, unlimited = resolve_limits(serialized["providerType"], custom)
        counter = await _get_counter(db, _provider_counter_id(provider_id), period_key)
        requests_used = counter["requests"]
        tokens_used = counter["tokens"]
        request_percent = _percent(requests_used, request_limit)
        token_percent = _percent(tokens_used, token_limit)
        if unlimited:
            primary_percent = None
        elif token_limit is not None and request_limit is not None:
            primary_percent = max(request_percent or 0.0, token_percent or 0.0)
        elif token_limit is not None:
            primary_percent = token_percent
        else:
            primary_percent = request_percent

        provider_items.append(
            ProviderUsageItem(
                id=provider_id,
                providerName=serialized["providerName"],
                providerType=serialized["providerType"],
                model=serialized["model"],
                enabled=serialized["enabled"],
                isDefault=serialized["isDefault"],
                requestsUsed=requests_used,
                tokensUsed=tokens_used,
                monthlyRequestLimit=request_limit,
                monthlyTokenLimit=token_limit,
                requestPercent=request_percent,
                tokenPercent=token_percent,
                primaryPercent=primary_percent,
                remainingRequests=_remaining(requests_used, request_limit),
                remainingTokens=_remaining(tokens_used, token_limit),
                unlimited=unlimited,
            )
        )

    return ModelUsageDashboardResponse(
        periodLabel=period_label(period_key),
        periodKey=period_key,
        providers=provider_items,
        braveSearch=brave_item,
    )
