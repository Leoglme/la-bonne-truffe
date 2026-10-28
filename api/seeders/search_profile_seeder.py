"""Seeder of Léo's starting search profile (docs/04-correspondance-et-notifications.md)."""

from sqlalchemy.orm import Session

from core.config import settings
from enums.coat_color import CoatColor
from enums.color_preference_level import ColorPreferenceLevel
from enums.lof_preference import LofPreference
from enums.sex_preference import SexPreference
from models.search_profile import SearchProfile
from seeders.breed_seeder import COCKER_SLUG
from services.auth_service import AuthService

STARTING_PROFILE_NAME = "Cocker gold Bretagne"

# From the closest to the farthest, driving from Rennes (validated by Léo).
STARTING_DEPARTMENT_CODES: tuple[str, ...] = ("35", "56", "22", "29", "44", "53", "49", "72", "85")


class SearchProfileSeeder:
    """Creates the starting profile of the seeded user when they have no profile yet."""

    def run(self, db: Session) -> int:
        """
        Seed the starting profile. Colours left out stay ``ignored``, as Léo decided.

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
        db.add(
            SearchProfile(
                user_id=user.id,
                name=STARTING_PROFILE_NAME,
                is_active=True,
                breed_ids=[COCKER_SLUG],
                department_codes=list(STARTING_DEPARTMENT_CODES),
                include_expected_litters=True,
                sex_preference=SexPreference.ANY,
                lof_preference=LofPreference.PREFERRED,
                color_preferences={
                    CoatColor.GOLD.value: ColorPreferenceLevel.PREFERRED.value,
                    CoatColor.NOIR_ET_FEU.value: ColorPreferenceLevel.ACCEPTABLE.value,
                },
                price_max_cents=None,
                notify_preferred_immediately=True,
                notify_acceptable_in_digest=True,
                digest_hour=19,
                notify_birth_of_followed=True,
            )
        )
        db.commit()
        return 1
