from pydantic import BaseModel, Field


class PortalConfigResponse(BaseModel):
    displayHomePage: bool = True


class JpilotSettingsResponse(BaseModel):
    displayHomePage: bool = True


class JpilotSettingsUpdate(BaseModel):
    displayHomePage: bool = Field(default=True)
