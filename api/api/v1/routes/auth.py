"""Authentication routes: login and the signed-in user."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from models.user import User
from schemas.user import Token, UserLogin, UserResponse
from services.auth_service import AuthService, get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)) -> Token:
    """
    Exchange the email and password for a bearer token.

    Args:
        credentials: Submitted email and password.
        db: Database session.

    Returns:
        The access token.

    Raises:
        HTTPException: 401 when the credentials match no active account.
    """
    user = AuthService.authenticate_user(db, credentials.email, credentials.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=AuthService.create_access_token(user.email))


@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Return the signed-in user.

    Args:
        current_user: The authenticated user.

    Returns:
        The user.
    """
    return current_user
