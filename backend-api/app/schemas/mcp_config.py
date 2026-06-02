from datetime import datetime

from pydantic import BaseModel, Field


class MCPSettingsUpdate(BaseModel):
    serverUrl: str
    serverName: str = "netscaler-copilot"
    nitroTimeoutSeconds: int = Field(default=30, ge=5, le=120)
    verifySsl: bool = False
    enabledTools: list[str] = Field(default_factory=list)
    sseEnabled: bool = True
    sshFallbackEnabled: bool = True
    sshPort: int = Field(default=22, ge=1, le=65535)
    sshTimeoutSeconds: int = Field(default=30, ge=5, le=120)


class MCPSettingsResponse(MCPSettingsUpdate):
    id: str = "default"
    updatedAt: datetime


class MCPStatusResponse(BaseModel):
    online: bool
    serverUrl: str
    message: str
    toolCount: int = 0
    enabledToolCount: int = 0
