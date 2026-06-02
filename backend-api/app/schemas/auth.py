from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    displayName: str
    role: str


class LoginResponse(BaseModel):
    accessToken: str
    tokenType: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    message: str
