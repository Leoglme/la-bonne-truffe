"""Authentication and user schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserLogin(BaseModel):
    """Credentials submitted by the login screen."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class Token(BaseModel):
    """Bearer token returned after a successful login."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """The signed-in user, as the dashboard reads it."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    is_active: bool
    created_at: datetime
