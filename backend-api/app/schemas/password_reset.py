from pydantic import BaseModel, Field


class PasswordResetConfirmRequest(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    code: str = Field(min_length=4, max_length=16)
    newPassword: str = Field(min_length=8, max_length=128)
