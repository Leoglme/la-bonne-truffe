"""Authentication and user schemas."""

from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, StringConstraints

PASSWORD_MIN_LENGTH = 8

BCRYPT_MAX_PASSWORD_BYTES = 72


def ensure_password_is_strong_enough(password: str) -> str:
    """
    Apply the rule the screens announce: 8 characters minimum, a digit among them.

    Args:
        password: Password typed on the signup or reset screen.

    Returns:
        The password, unchanged.

    Raises:
        ValueError: When it has no digit, or is longer than bcrypt accepts.
    """
    if not any(character.isdigit() for character in password):
        raise ValueError("Le mot de passe doit contenir au moins un chiffre")
    if len(password.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError(f"Le mot de passe doit faire {BCRYPT_MAX_PASSWORD_BYTES} octets au plus")
    return password


NewPassword = Annotated[str, Field(min_length=PASSWORD_MIN_LENGTH), AfterValidator(ensure_password_is_strong_enough)]


class UserLogin(BaseModel):
    """Credentials submitted by the login screen."""

    email: EmailStr
    password: str = Field(..., min_length=1)


FirstName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class UserSignup(BaseModel):
    """Account submitted by the signup screen."""

    name: FirstName
    email: EmailStr
    password: NewPassword


class SignupAvailability(BaseModel):
    """Whether the signup screen creates accounts, or keeps the attempt while signups are closed."""

    is_open: bool


class SignupRequestCreate(BaseModel):
    """Name and address typed on the signup screen while signups are closed; the password is never kept."""

    name: FirstName
    email: EmailStr


class SignupRequestRecorded(BaseModel):
    """What the « C'est noté » screen says: the address told when signups open."""

    email: str


class Token(BaseModel):
    """Bearer token returned after a successful login, signup or password reset."""

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


class PasswordResetRequest(BaseModel):
    """Email typed on the « Mot de passe oublié » screen."""

    email: EmailStr


class PasswordResetRequested(BaseModel):
    """What the « Regarde tes e-mails » screen says, whether or not the account exists."""

    expires_in_minutes: int
    resend_delay_seconds: int


class PasswordResetToken(BaseModel):
    """Token read from the link of the reset email."""

    token: str = Field(..., min_length=1)


class PasswordResetTarget(BaseModel):
    """Account a valid reset link belongs to, shown on the « Nouveau mot de passe » screen."""

    email: str


class PasswordResetConfirm(BaseModel):
    """New password chosen from the link of the reset email."""

    token: str = Field(..., min_length=1)
    password: NewPassword
