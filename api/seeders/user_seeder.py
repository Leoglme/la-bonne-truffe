"""Seeder of the single dashboard user, from ADMIN_NAME, ADMIN_EMAIL and ADMIN_PASSWORD."""

from sqlalchemy.orm import Session

from core.config import settings
from models.user import User
from services.auth_service import AuthService


class UserSeeder:
    """Creates the user of the ``.env`` when no account has that email."""

    def run(self, db: Session) -> int:
        """
        Seed the user; an existing account is never touched (its password may have changed).

        Args:
            db: Database session.

        Returns:
            1 when the user was created, 0 otherwise.
        """
        if AuthService.get_user_by_email(db, settings.admin_email) is not None:
            return 0
        db.add(
            User(
                name=settings.admin_name,
                email=settings.admin_email,
                hashed_password=AuthService.hash_password(settings.admin_password),
                is_active=True,
            )
        )
        db.commit()
        return 1
