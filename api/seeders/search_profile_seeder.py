"""Seeder of Léo's starting search profile (docs/04-correspondance-et-notifications.md)."""

from sqlalchemy.orm import Session

from core.config import settings
from models.search_profile import SearchProfile
from services.auth_service import AuthService
from services.search_profile_service import SearchProfileService


class SearchProfileSeeder:
    """Creates the starting profile of the seeded user when they have no profile yet."""

    def run(self, db: Session) -> int:
        """
        Seed the starting profile, the same one a signup gets. Colours left out stay ``ignored``, as Léo decided.

        Args:
            db: Database session.

        Returns:
            1 when the profile was created, 0 otherwise.
        """
        user = AuthService.get_user_by_email(db, settings.admin_email)
        if user is None:
            return 0
        if db.query(SearchProfile).filter(SearchProfile.user_id == user.id).first() is not None:
            return 0
        SearchProfileService.create_starting_profile(db, user.id)
        db.commit()
        return 1
