"""Stores the breeder profiles of a directory run: the breeder found or created, its directory fields refreshed."""

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.orm import Session

from models.breeder import Breeder
from models.department import Department
from services.breeder_contact_writer import apply_breeder_contact
from services.breeder_matcher import BreederMatcher
from services.breeder_search_text import BreederSearchText
from services.collectors.breeder_contact_parser import BreederContactParser
from services.collectors.raw_dog import RawBreederProfile
from services.stored_value import known_or_current


@dataclass
class BreederDirectoryIngestionSummary:
    """What a directory run changed in the database."""

    seen_count: int = 0
    new_breeder_ids: list[int] = field(default_factory=list)
    updated_breeder_ids: list[int] = field(default_factory=list)


class BreederDirectoryIngestionService:
    """Upserts the breeders the Centrale Canine directory and the club list name."""

    def ingest(self, db: Session, profiles: list[RawBreederProfile], now: datetime) -> BreederDirectoryIngestionSummary:
        """
        Store a run: each profile finds its breeder by the rules of docs/03, or creates it, and refreshes what
        the directory knows. A value the directory leaves empty never erases a known one.

        Args:
            db: Database session; committed at the end.
            profiles: Profiles read by the collector; the last one of a breeder wins.
            now: Run time, naive UTC.

        Returns:
            The summary of the run.
        """
        summary = BreederDirectoryIngestionSummary()
        known_department_codes = {code for (code,) in db.query(Department.code)}
        latest_by_source_id = {profile.source_id: profile for profile in profiles}
        summary.seen_count = len(latest_by_source_id)
        for profile in latest_by_source_id.values():
            breeder, is_new = self._find_or_create(db, profile, known_department_codes)
            self._apply_profile(db, breeder, profile, known_department_codes, now)
            if is_new:
                summary.new_breeder_ids.append(breeder.id)
            else:
                summary.updated_breeder_ids.append(breeder.id)
        db.commit()
        return summary

    @staticmethod
    def _find_or_create(
        db: Session, profile: RawBreederProfile, known_department_codes: set[str]
    ) -> tuple[Breeder, bool]:
        """
        The breeder a profile describes, created when no rule finds it.

        Args:
            db: Database session.
            profile: The profile.
            known_department_codes: Seeded department codes.

        Returns:
            The breeder, and whether it was just created.
        """
        department_code = profile.department_code if profile.department_code in known_department_codes else None
        breeder = BreederMatcher.find(
            db,
            siren=profile.siren,
            scc_breeder_id=profile.source_id,
            phone_e164=profile.phone_e164,
            affix_key=BreederContactParser.affix_key(profile.affix),
            department_code=department_code,
            scc_user_id=profile.scc_user_id,
        )
        if breeder is not None:
            return breeder, False
        breeder = Breeder()
        db.add(breeder)
        db.flush()
        return breeder, True

    @classmethod
    def _apply_profile(
        cls,
        db: Session,
        breeder: Breeder,
        profile: RawBreederProfile,
        known_department_codes: set[str],
        now: datetime,
    ) -> None:
        """
        Copy what the directory says onto the breeder.

        Args:
            db: Database session.
            breeder: Breeder to update.
            profile: The profile.
            known_department_codes: Seeded department codes.
            now: Run time.
        """
        if not BreederMatcher.is_scc_breeder_id_taken(db, profile.source_id, breeder.id):
            breeder.scc_breeder_id = profile.source_id
        if profile.scc_user_id is not None and not BreederMatcher.is_scc_user_id_taken(
            db, profile.scc_user_id, breeder.id
        ):
            breeder.scc_user_id = profile.scc_user_id
        if profile.siren is not None and not BreederMatcher.is_siren_taken(db, profile.siren, breeder.id):
            breeder.siren = profile.siren
        department_code = profile.department_code if profile.department_code in known_department_codes else None
        breeder.scc_breeder_number = known_or_current(profile.breeder_number, breeder.scc_breeder_number)
        apply_breeder_contact(
            breeder,
            display_name=profile.display_name,
            affix=profile.affix,
            is_from_centrale_canine=True,
            phone_e164=profile.phone_e164,
            zip_code=profile.zip_code,
            city=profile.city,
            department_code=department_code,
            latitude=profile.latitude,
            longitude=profile.longitude,
        )
        breeder.logo_url = known_or_current(profile.logo_url, breeder.logo_url)
        breeder.scc_site_slug = known_or_current(profile.site_slug, breeder.scc_site_slug)
        if profile.variety_ids:
            breeder.scc_variety_ids = list(profile.variety_ids)
        breeder.scc_last_litter_at = known_or_current(profile.last_litter_at, breeder.scc_last_litter_at)
        breeder.is_scc_selected = known_or_current(profile.is_selected, breeder.is_scc_selected)
        if profile.is_breed_club_member is True or breeder.is_breed_club_member is None:
            breeder.is_breed_club_member = known_or_current(profile.is_breed_club_member, breeder.is_breed_club_member)
        breeder.scc_directory_seen_at = now
        breeder.search_text = BreederSearchText.build(breeder)
        db.flush()


breeder_directory_ingestion_service = BreederDirectoryIngestionService()
