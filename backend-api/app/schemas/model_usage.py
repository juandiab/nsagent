from pydantic import BaseModel, Field


class ProviderUsageLimitsUpdate(BaseModel):
    providerId: str
    monthlyTokenLimit: int | None = Field(default=None, ge=0)
    monthlyRequestLimit: int | None = Field(default=None, ge=0)


class UsageLimitsUpdate(BaseModel):
    braveMonthlyQueryLimit: int | None = Field(default=None, ge=0)
    providers: list[ProviderUsageLimitsUpdate] = Field(default_factory=list)


class ProviderUsageItem(BaseModel):
    id: str
    providerName: str
    providerType: str
    model: str
    enabled: bool
    isDefault: bool
    requestsUsed: int
    tokensUsed: int
    monthlyRequestLimit: int | None = None
    monthlyTokenLimit: int | None = None
    requestPercent: float | None = None
    tokenPercent: float | None = None
    primaryPercent: float | None = None
    remainingRequests: int | None = None
    remainingTokens: int | None = None
    unlimited: bool = False


class BraveUsageItem(BaseModel):
    configured: bool
    enabled: bool
    queriesUsed: int
    monthlyQueryLimit: int | None = None
    percent: float | None = None
    remainingQueries: int | None = None
    unlimited: bool = False


class ModelUsageDashboardResponse(BaseModel):
    periodLabel: str
    periodKey: str
    providers: list[ProviderUsageItem]
    braveSearch: BraveUsageItem
