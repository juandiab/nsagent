from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

CalibrationFeedbackCategory = Literal[
    "wrong_tool",
    "missing_step",
    "wrong_answer",
    "skill_not_triggered",
    "too_slow",
    "tool_limit",
    "other",
]

CalibrationFeedbackRating = Literal["positive", "negative", "neutral"]


class CalibrationFeedbackMessage(BaseModel):
    role: str
    content: str = ""
    createdAt: str | None = None
    toolCalls: list[dict[str, Any]] = Field(default_factory=list)
    isError: bool = False


class CalibrationFeedbackSession(BaseModel):
    sessionId: str | None = None
    startedAt: str | None = None
    messages: list[CalibrationFeedbackMessage] = Field(default_factory=list)


class CalibrationFeedbackDiagnostics(BaseModel):
    lastErrorType: str | None = None
    formSubmissionCount: int | None = None
    planningIntent: str | None = None


class CalibrationFeedbackRequest(BaseModel):
    objectiveMet: bool = False
    userGoal: str = ""
    vendor: str = "netscaler"
    role: str = "architect"
    category: CalibrationFeedbackCategory = "other"
    rating: CalibrationFeedbackRating = "negative"
    userComment: str = ""
    matchedSkills: list[str] = Field(default_factory=list)
    suggestedSkillId: str | None = None
    includeApplianceName: bool = False
    applianceName: str | None = None
    session: CalibrationFeedbackSession
    diagnostics: CalibrationFeedbackDiagnostics | None = None
    source: str = "jpilot_in_app"


class CalibrationFeedbackResponse(BaseModel):
    status: str
    message: str = ""
    feedbackId: str | None = None
    calibrationUrl: str | None = None
