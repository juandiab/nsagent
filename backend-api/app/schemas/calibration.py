from pydantic import BaseModel, Field


class CalibrationSkillSummary(BaseModel):
    skillId: str
    version: str
    label: str = ""
    vendor: str | None = None
    path: str = ""


class CalibrationSyncResponse(BaseModel):
    installed: int
    updated: int
    removed: int
    skills: list[dict] = Field(default_factory=list)
    message: str = ""
