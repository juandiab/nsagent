from pydantic import BaseModel, Field


class VersionResponse(BaseModel):
    version: str
    display_version: str


class UpdateInstructions(BaseModel):
    summary: str
    steps: list[str] = Field(default_factory=list)
    commands_linux_mac: list[str] = Field(default_factory=list)
    commands_windows: list[str] = Field(default_factory=list)


class UpdateCheckResponse(BaseModel):
    current_version: str
    display_version: str
    latest_version: str | None = None
    latest_display_version: str | None = None
    update_available: bool = False
    release_url: str | None = None
    release_name: str | None = None
    release_notes: str | None = None
    checked_at: str
    check_error: str | None = None
    update_instructions: UpdateInstructions
