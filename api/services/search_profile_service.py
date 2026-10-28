"""Creates, reads and saves the search profiles; a save re-evaluates every litter."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from enums.coat_color import CoatColor
from enums.color_preference_level import ColorPreferenceLevel
from enums.lof_preference import LofPreference
from enums.sex_preference import SexPreference
from models.breed import Breed
from models.department import Department
from models.search_profile import SearchProfile
from schemas.search_profile import SearchProfileUpdate
from seeders.breed_seeder import COCKER_SLUG
from services.matching.match_refresh import match_refresh_service

STARTING_PROFILE_NAME = "Cocker gold Bretagne"

# From the closest to the farthest, driving from Rennes (validated by Léo).
STARTING_DEPARTMENT_CODES: tuple[str, ...] = ("35", "56", "22", "29", "44", "53", "49", "72", "85")


class SearchProfileService:
    """Profile operations, always scoped to the signed-in user."""

    @staticmethod
    def create_starting_profile(db: Session, user_id: int) -> SearchProfile:
        """
        Add the starting profile of an account (docs/04-correspondance-et-notifications.md): cocker, gold
        preferred, black and tan acceptable, the other colours ignored, the nine departments around Rennes,
        LOF litters only (the « Pedigree LOF » criterion opens the others).

        Args:
            db: Database session; flushed, not committed.
            user_id: Owner.

        Returns:
            The profile, with its id.
        """
        profile = SearchProfile(
            user_id=user_id,
            name=STARTING_PROFILE_NAME,
            is_active=True,
            breed_ids=[COCKER_SLUG],
            department_codes=list(STARTING_DEPARTMENT_CODES),
            include_expected_litters=True,
            sex_preference=SexPreference.ANY,
            lof_preference=LofPreference.REQUIRED,
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
        db.add(profile)
        db.flush()
        return profile

    @staticmethod
    def list_for_user(db: Session, user_id: int) -> list[SearchProfile]:
        """
        The profiles of a user, oldest first.

        Args:
            db: Database session.
            user_id: Owner.

        Returns:
            The profiles.
        """
        return db.query(SearchProfile).filter(SearchProfile.user_id == user_id).order_by(SearchProfile.id).all()

    @staticmethod
    def update(db: Session, user_id: int, profile_id: int, payload: SearchProfileUpdate) -> SearchProfile:
        """
        Save the criteria, then re-evaluate every litter without notifying (see ``MatchRefreshService``).

        Args:
            db: Database session.
            user_id: Owner.
            profile_id: Profile to save.
            payload: New criteria.

        Returns:
            The saved profile.

        Raises:
            HTTPException: 404 for a profile of another user, 422 for an unknown breed or department.
        """
        profile = (
            db.query(SearchProfile).filter(SearchProfile.id == profile_id, SearchProfile.user_id == user_id).first()
        )
        if profile is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profil introuvable")
        known_breeds = {slug for (slug,) in db.query(Breed.slug).filter(Breed.slug.in_(payload.breed_ids))}
        unknown_breeds = sorted(set(payload.breed_ids) - known_breeds)
        known_departments = {
            code for (code,) in db.query(Department.code).filter(Department.code.in_(payload.department_codes))
        }
        unknown_departments = [code for code in payload.department_codes if code not in known_departments]
        if unknown_breeds or unknown_departments:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Race(s) inconnue(s) : {unknown_breeds}, département(s) inconnu(s) : {unknown_departments}",
            )

        profile.name = payload.name
        profile.is_active = payload.is_active
        profile.breed_ids = list(payload.breed_ids)
        profile.department_codes = list(dict.fromkeys(payload.department_codes))
        profile.include_expected_litters = payload.include_expected_litters
        profile.sex_preference = payload.sex_preference
        profile.lof_preference = payload.lof_preference
        profile.color_preferences = {color.value: level.value for color, level in payload.color_preferences.items()}
        profile.price_max_cents = payload.price_max_cents
        profile.notify_preferred_immediately = payload.notify_preferred_immediately
        profile.notify_acceptable_in_digest = payload.notify_acceptable_in_digest
        profile.digest_hour = payload.digest_hour
        profile.notify_birth_of_followed = payload.notify_birth_of_followed
        db.commit()
        match_refresh_service.refresh(db, naive_utc_now(), should_notify=False)
        db.refresh(profile)
        return profile
