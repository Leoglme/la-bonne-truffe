"""Authentication: password hashing, JWT tokens, and the FastAPI auth dependencies."""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login")


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

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User | None:
        """
        Look a user up by email.

        Args:
            db: Active database session.
            email: Email to match.

        Returns:
            The user, or None when no row matches.
        """
        return db.query(User).filter(User.email == email).first()

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
        if not isinstance(email, str):
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
