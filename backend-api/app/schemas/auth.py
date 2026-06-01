from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    username: str


class LoginResponse(BaseModel):
    accessToken: str
    tokenType: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    message: str
