"""Reads and saves the search profiles; a save re-evaluates every litter."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from models.breed import Breed
from models.department import Department
from models.search_profile import SearchProfile
from schemas.search_profile import SearchProfileUpdate
from services.matching.match_refresh import match_refresh_service


class SearchProfileService:
    """Profile operations, always scoped to the signed-in user."""

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
