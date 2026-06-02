from pydantic import BaseModel


class ApplianceTestPreview(BaseModel):
    host: str
    username: str
    password: str


class TestConnectionResponse(BaseModel):
    success: bool
    message: str
