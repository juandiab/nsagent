from datetime import datetime

from pydantic import BaseModel, Field


class SlackSettingsUpdate(BaseModel):
    enabled: bool = False
    webhookUrl: str | None = None
    defaultChannel: str = ""
    notifyLicenseAlerts: bool = True
    notifyWorkflowUpdates: bool = True
    notifyHealthChecks: bool = False


class SlackSettingsResponse(BaseModel):
    enabled: bool = False
    hasWebhookUrl: bool = False
    webhookUrlPreview: str | None = None
    defaultChannel: str = ""
    notifyLicenseAlerts: bool = True
    notifyWorkflowUpdates: bool = True
    notifyHealthChecks: bool = False
    updatedAt: datetime | None = None


class SlackTestRequest(BaseModel):
    webhookUrl: str | None = None
    message: str = Field(default="JPilot Slack test notification.", max_length=500)
