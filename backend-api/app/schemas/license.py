from datetime import datetime

from pydantic import BaseModel, Field


class LicenseCodeUpdate(BaseModel):
    licenseCode: str = Field(min_length=16, max_length=24)


class LicenseDetailsResponse(BaseModel):
    licenseType: str | None = None
    licenseCode: str | None = None
    daysToExpire: int | None = None
    expirationDate: str | None = None
    registrationDate: str | None = None
    validityDays: int | None = None
    customerName: str | None = None
    customerEmail: str | None = None
    company: str | None = None


class LicenseResponse(BaseModel):
    appFingerprint: str
    appName: str
    activationDate: str
    hasLicenseCode: bool = False
    status: str = "pending"
    message: str = ""
    renewalCount: int = 0
    licenseType: str | None = None
    expirationDate: str | None = None
    registrationDate: str | None = None
    validityDays: int | None = None
    algorithm: str | None = None
    version: int | None = None
    lastSyncedAt: datetime | None = None
    syncError: str | None = None
    hasCachedLicense: bool = False
    obtainedOffline: bool = False
    details: LicenseDetailsResponse | None = None
