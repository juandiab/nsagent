from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


EnvironmentType = Literal["LAB", "DEV", "TEST", "UAT", "PROD"]
VendorType = Literal[
    "netscaler",
    "f5",
    "cisco",
    "juniper",
    "palo_alto",
    "fortinet",
    "checkpoint",
    "a10",
    "radware",
    "haproxy",
    "other",
]


class ApplianceCreate(BaseModel):
    name: str
    environment: EnvironmentType
    host: str
    username: str
    password: str
    notes: str = ""
    enabled: bool = True
    vendor: VendorType = "netscaler"


class ApplianceUpdate(BaseModel):
    name: str | None = None
    environment: EnvironmentType | None = None
    host: str | None = None
    username: str | None = None
    password: str | None = None
    notes: str | None = None
    enabled: bool | None = None
    vendor: VendorType | None = None


class ApplianceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    name: str
    environment: str
    enabled: bool
    notes: str
    vendor: str = "netscaler"
    copilotEligible: bool = True
    createdAt: datetime = Field(alias="createdAt")
    updatedAt: datetime = Field(alias="updatedAt")
