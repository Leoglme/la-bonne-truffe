"""The account operations open to a signed-out visitor: signing up and resetting a forgotten password."""

from datetime import datetime, timedelta
from urllib.parse import urlencode

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from core.config import settings
from models.user import User
from schemas.user import PasswordResetRequested, UserSignup
from services.account_emails import AccountEmails
from services.auth_service import AuthService
from services.email_service import EmailService, email_service
from services.matching.match_refresh import match_refresh_service
from services.search_profile_service import SearchProfileService

PASSWORD_RESET_RESEND_DELAY_SECONDS = 45

RESET_PASSWORD_SCREEN_PATH = "/nouveau-mot-de-passe"


class AccountService:
    """Creates accounts and resets forgotten passwords."""

    def __init__(self, mailer: EmailService) -> None:
        """
        Args:
            mailer: Service that delivers the reset emails.
        """
        self._mailer = mailer
        self._reset_email_sent_at_by_user_id: dict[int, datetime] = {}

    def sign_up(self, db: Session, payload: UserSignup) -> User:
        """
        Create an account with the starting search profile, and evaluate the litters for it.

        Args:
            db: Database session.
            payload: Name, email and password typed on the signup screen.

        Returns:
            The new account.

        Raises:
            HTTPException: 403 when signups are closed (``SIGNUP_ENABLED``), 409 when the email has an account.
        """
        if not settings.signup_enabled:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Les inscriptions sont fermées.")
        email = payload.email.lower()
        if AuthService.get_user_by_email(db, email) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Un compte existe déjà avec cette adresse."
            )

        user = User(
            name=payload.name,
            email=email,
            hashed_password=AuthService.hash_password(payload.password),
            is_active=True,
        )
        db.add(user)
        db.flush()
        profile = SearchProfileService.create_starting_profile(db, user.id)
        db.commit()
        match_refresh_service.refresh(db, naive_utc_now(), should_notify=False, profile_ids={profile.id})
        db.refresh(user)
        return user

    def request_password_reset(
        self, db: Session, email: str, background_tasks: BackgroundTasks
    ) -> PasswordResetRequested:
        """
        Email a reset link when the address belongs to an active account.

        The answer is the same either way, so the screen never tells whether an address has an account,
        and the email leaves after the response, so its timing does not tell either.

        Args:
            db: Database session.
            email: Address typed on the « Mot de passe oublié » screen.
            background_tasks: Tasks run once the response has left.

        Returns:
            The lifetime of the link and the delay before another one may be sent.
        """
        user = AuthService.get_user_by_email(db, email)
        now = naive_utc_now()
        if user is not None and user.is_active and not self._has_recently_sent_reset_email(user.id, now):
            self._reset_email_sent_at_by_user_id[user.id] = now
            query = urlencode({"token": AuthService.create_password_reset_token(user)})
            link = f"{settings.web_base_url.rstrip('/')}{RESET_PASSWORD_SCREEN_PATH}?{query}"
            message = AccountEmails.password_reset(
                user.email, user.name, link, settings.password_reset_token_expire_minutes
            )
            background_tasks.add_task(self._mailer.send, message)
        return PasswordResetRequested(
            expires_in_minutes=settings.password_reset_token_expire_minutes,
            resend_delay_seconds=PASSWORD_RESET_RESEND_DELAY_SECONDS,
        )

    def reset_password(self, db: Session, token: str, password: str) -> User:
        """
        Set the password chosen from a reset link; the link, like every other one sent before, stops working.

        Args:
            db: Database session.
            token: Token read from the link.
            password: New password, already checked by the schema.

        Returns:
            The account.

        Raises:
            HTTPException: 400 when the link is expired or already used.
        """
        user = AuthService.resolve_password_reset_token(db, token)
        user.hashed_password = AuthService.hash_password(password)
        db.commit()
        self._reset_email_sent_at_by_user_id.pop(user.id, None)
        return user

    def _has_recently_sent_reset_email(self, user_id: int, now: datetime) -> bool:
        """
        Whether a reset email left for this account less than the resend delay ago.

        Args:
            user_id: Account.
            now: Current time, naive UTC.

        Returns:
            True while the screen still shows its countdown.
        """
        sent_at = self._reset_email_sent_at_by_user_id.get(user_id)
        return sent_at is not None and now - sent_at < timedelta(seconds=PASSWORD_RESET_RESEND_DELAY_SECONDS)


account_service = AccountService(email_service)
