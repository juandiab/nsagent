from pydantic import BaseModel, Field


class AccountRecoveryRequest(BaseModel):
    username: str = Field(min_length=2, max_length=64)


class PasswordResetConfirmRequest(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    code: str = Field(min_length=4, max_length=16)
    newPassword: str | None = Field(default=None, min_length=8, max_length=128)


class AccountRecoveryConfirmResponse(BaseModel):
    message: str
    recoveryToken: str | None = None
