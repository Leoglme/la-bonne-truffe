"""Authentication routes: login, signup, the forgotten password, and the signed-in user."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from models.user import User
from schemas.user import (
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetRequested,
    PasswordResetTarget,
    PasswordResetToken,
    Token,
    UserLogin,
    UserResponse,
    UserSignup,
)
from services.account_service import account_service
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
            detail="E-mail ou mot de passe incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=AuthService.create_access_token(user.email))


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(payload: UserSignup, db: Session = Depends(get_db)) -> Token:
    """
    Create an account and sign it in.

    Args:
        payload: Name, email and password typed on the signup screen.
        db: Database session.

    Returns:
        The access token of the new account.

    Raises:
        HTTPException: 403 when signups are closed, 409 when the email already has an account.
    """
    user = account_service.sign_up(db, payload)
    return Token(access_token=AuthService.create_access_token(user.email))


@router.post("/forgot-password", response_model=PasswordResetRequested, status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    payload: PasswordResetRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
) -> PasswordResetRequested:
    """
    Email a reset link to the address when it has an account; the answer never tells whether it does.

    Args:
        payload: Address typed on the « Mot de passe oublié » screen.
        background_tasks: Where the email waits for the response to leave.
        db: Database session.

    Returns:
        The lifetime of the link and the delay before another one may be asked.
    """
    return account_service.request_password_reset(db, payload.email, background_tasks)


@router.post("/reset-password/verify", response_model=PasswordResetTarget)
async def verify_password_reset_link(payload: PasswordResetToken, db: Session = Depends(get_db)) -> PasswordResetTarget:
    """
    Check a reset link before the screen asks for the new password.

    Args:
        payload: Token read from the link.
        db: Database session.

    Returns:
        The address of the account the link resets.

    Raises:
        HTTPException: 400 when the link is expired or already used.
    """
    user = AuthService.resolve_password_reset_token(db, payload.token)
    return PasswordResetTarget(email=user.email)


@router.post("/reset-password", response_model=Token)
async def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)) -> Token:
    """
    Set the password chosen from a reset link, and sign the account in.

    Args:
        payload: Token read from the link, and the new password.
        db: Database session.

    Returns:
        The access token of the account.

    Raises:
        HTTPException: 400 when the link is expired or already used.
    """
    user = account_service.reset_password(db, payload.token, payload.password)
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
