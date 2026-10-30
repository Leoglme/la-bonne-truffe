"""Authentication: password hashing, JWT tokens, and the FastAPI auth dependencies."""

import hashlib
import hmac
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login")

PASSWORD_RESET_PURPOSE = "password_reset"


class AuthService:
    """Password hashing, JWT issuing and user lookup — everything the auth flow needs, HTTP aside."""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Check a plain password against its bcrypt hash.

        Args:
            plain_password: Password as typed by the user.
            hashed_password: Hash stored on the user row.

        Returns:
            Whether the password matches.
        """
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password with bcrypt, salt included.

        Args:
            password: Password as typed by the user.

        Returns:
            The hash to store on the user row.
        """
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def create_access_token(email: str, expires_delta: timedelta | None = None) -> str:
        """
        Issue a signed JWT access token whose subject is the user email.

        Args:
            email: Email of the user the token identifies.
            expires_delta: Lifetime override, defaulting to the configured one.

        Returns:
            The encoded token.
        """
        expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
        return jwt.encode({"sub": email, "exp": expire}, settings.secret_key, algorithm=settings.algorithm)

    @classmethod
    def renew_access_token_if_due(cls, token: str, now: datetime) -> str | None:
        """
        Issue a fresh token when the given one is past half its lifetime (the sliding session).

        The token has already been accepted by the auth dependency; a token that fails to decode here
        is simply not renewed.

        Args:
            token: Raw JWT the request carried.
            now: Current time, aware UTC.

        Returns:
            A new token to use from now on, or None while the current one is young enough.
        """
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        except jwt.PyJWTError:
            return None
        email = payload.get("sub")
        expires_at_timestamp = payload.get("exp")
        if not isinstance(email, str) or not isinstance(expires_at_timestamp, int | float):
            return None
        expires_at = datetime.fromtimestamp(expires_at_timestamp, tz=UTC)
        lifetime = timedelta(minutes=settings.access_token_expire_minutes)
        if expires_at - now >= lifetime / 2:
            return None
        return cls.create_access_token(email)

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User | None:
        """
        Look a user up by email, whatever its case: a phone keyboard capitalises the first letter.

        Args:
            db: Active database session.
            email: Email to match.

        Returns:
            The user, or None when no row matches.
        """
        return db.query(User).filter(func.lower(User.email) == email.strip().lower()).first()

    @classmethod
    def create_password_reset_token(cls, user: User) -> str:
        """
        Issue the short-lived token of the « Mot de passe oublié » link.

        The token carries a fingerprint of the current password hash: once the password changes, every
        link sent before stops working, which makes each one single-use without storing anything.

        Args:
            user: Account the link resets.

        Returns:
            The encoded token.
        """
        expire = datetime.now(UTC) + timedelta(minutes=settings.password_reset_token_expire_minutes)
        payload = {
            "sub": user.email,
            "purpose": PASSWORD_RESET_PURPOSE,
            "pwd": cls._password_fingerprint(user.hashed_password),
            "exp": expire,
        }
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

    @classmethod
    def resolve_password_reset_token(cls, db: Session, token: str) -> User:
        """
        Resolve the account a reset link belongs to.

        Args:
            db: Active database session.
            token: Token read from the link.

        Returns:
            The account, active and with the password the link was issued for.

        Raises:
            HTTPException: 400 when the link is malformed, expired, already used, or not a reset link.
        """
        invalid_link_exception = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Ce lien a expiré ou a déjà servi."
        )
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        except jwt.PyJWTError as error:
            raise invalid_link_exception from error

        email = payload.get("sub")
        fingerprint = payload.get("pwd")
        if payload.get("purpose") != PASSWORD_RESET_PURPOSE or not isinstance(email, str):
            raise invalid_link_exception
        user = cls.get_user_by_email(db, email)
        if user is None or not user.is_active or not isinstance(fingerprint, str):
            raise invalid_link_exception
        if not hmac.compare_digest(fingerprint, cls._password_fingerprint(user.hashed_password)):
            raise invalid_link_exception
        return user

    @staticmethod
    def _password_fingerprint(hashed_password: str) -> str:
        """
        Keyed fingerprint of a password hash, short enough for a link.

        Args:
            hashed_password: bcrypt hash stored on the user row.

        Returns:
            The first 16 hexadecimal characters of its HMAC-SHA256 under the secret key.
        """
        digest = hmac.new(settings.secret_key.encode("utf-8"), hashed_password.encode("utf-8"), hashlib.sha256)
        return digest.hexdigest()[:16]

    @classmethod
    def authenticate_user(cls, db: Session, email: str, password: str) -> User | None:
        """
        Authenticate a login attempt.

        Args:
            db: Active database session.
            email: Submitted email.
            password: Submitted password.

        Returns:
            The user when the credentials match an active account, None otherwise — the three
            failure causes are deliberately indistinguishable to the caller.
        """
        user = cls.get_user_by_email(db, email)
        if user is None or not user.is_active:
            return None
        if not cls.verify_password(password, user.hashed_password):
            return None
        return user

    @classmethod
    def resolve_user_from_token(cls, token: str, db: Session) -> User:
        """
        Resolve the active user a raw JWT belongs to.

        Args:
            token: Raw JWT.
            db: Active database session.

        Returns:
            The authenticated user.

        Raises:
            HTTPException: 401 when the token is invalid, expired, or points at no active user.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        except jwt.PyJWTError as error:
            raise credentials_exception from error

        email = payload.get("sub")
        if not isinstance(email, str) or payload.get("purpose") is not None:
            raise credentials_exception
        user = cls.get_user_by_email(db, email)
        if user is None or not user.is_active:
            raise credentials_exception
        return user


# FastAPI resolves dependencies by inspecting plain callables, so this stays module-level and
# only delegates to AuthService. It is the auth contract the routes declare with Depends().


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Resolve the caller from the bearer token.

    Args:
        token: Bearer token extracted by the OAuth2 scheme.
        db: Active database session.

    Returns:
        The authenticated user.

    Raises:
        HTTPException: 401 when the token is invalid or points at no active user.
    """
    return AuthService.resolve_user_from_token(token, db)
