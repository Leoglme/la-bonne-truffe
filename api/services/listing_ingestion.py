"""Stores the listings of a run: insert, update, change history, disappearance."""

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import StrEnum
from typing import TypeVar

from sqlalchemy.orm import Session

from enums.listing_source import ListingSource
from models.breeder import Breeder
from models.department import Department
from models.listing import Listing
from models.listing_change import ListingChange
from services.collectors.breeder_contact_parser import BreederContactParser
from services.collectors.raw_listing import RawBreeder, RawListing

# Fields whose change is history worth keeping (« les sexes sont apparus », « la portée est née »).
TRACKED_FIELDS: tuple[str, ...] = (
    "kind",
    "lof_status",
    "litter_number",
    "mating_number",
    "mating_date",
    "birth_date",
    "male_count",
    "female_count",
    "puppies_available",
    "variety_source_id",
    "colors",
    "color_text",
    "price_cents",
    "department_code",
    "zip_code",
    "city",
    "sire_name",
    "sire_rating",
    "dam_name",
    "dam_rating",
    "litter_rating",
    "photos",
    "description",
    "external_url",
)

# A listing missing from this many runs in a row has left its source.
MISSED_RUNS_BEFORE_INACTIVE = 2

# A born litter older than this is no longer followed.
BORN_LITTER_ACTIVE_DAYS = 183

ColumnValue = str | int | float | bool | date | datetime | StrEnum | list[str] | list[dict[str, str]] | None

StoredValue = TypeVar("StoredValue", str, bool, int, float)


@dataclass
class IngestionSummary:
    """What a run changed in the database."""

    seen_count: int = 0
    new_listing_ids: list[int] = field(default_factory=list)
    changed_listing_ids: list[int] = field(default_factory=list)
    deactivated_listing_ids: list[int] = field(default_factory=list)


class ListingIngestionService:
    """Upserts the listings read from one source and records what moved."""

    def ingest(
        self,
        db: Session,
        source: ListingSource,
        raw_listings: list[RawListing],
        collected_department_codes: set[str],
        now: datetime,
    ) -> IngestionSummary:
        """
        Store a run: new listings, changed fields, and listings that disappeared from the departments read.

        Args:
            db: Database session; committed at the end.
            source: Source of the run.
            raw_listings: Listings read by the collector.
            collected_department_codes: Departments the run read; only their listings can disappear.
            now: Run time, naive UTC.

        Returns:
            The summary of the run.
        """
        summary = IngestionSummary()
        known_department_codes = {code for (code,) in db.query(Department.code)}
        latest_by_external_id = {raw_listing.external_id: raw_listing for raw_listing in raw_listings}
        summary.seen_count = len(latest_by_external_id)

        for raw_listing in latest_by_external_id.values():
            listing = (
                db.query(Listing)
                .filter(Listing.source == source, Listing.external_id == raw_listing.external_id)
                .one_or_none()
            )
            breeder_id = self._upsert_breeder(
                db, source, raw_listing, known_department_codes, listing.breeder_id if listing is not None else None
            )
            if listing is None:
                listing = Listing(
                    source=source,
                    external_id=raw_listing.external_id,
                    breed_id=raw_listing.breed_id,
                    breeder_id=breeder_id,
                    first_seen_at=now,
                    last_seen_at=now,
                )
                self._apply_content(listing, raw_listing, known_department_codes)
                db.add(listing)
                db.flush()
                summary.new_listing_ids.append(listing.id)
                continue

            values_before = self._tracked_values(listing)
            was_active = listing.is_active
            self._apply_content(listing, raw_listing, known_department_codes)
            has_changed = self._record_changes(db, listing.id, values_before, self._tracked_values(listing), now)
            if not was_active:
                db.add(
                    ListingChange(
                        listing_id=listing.id, field="is_active", old_value="false", new_value="true", changed_at=now
                    )
                )
                has_changed = True
            if breeder_id is not None:
                listing.breeder_id = breeder_id
            listing.last_seen_at = now
            listing.missed_run_count = 0
            listing.is_active = True
            if has_changed:
                listing.last_changed_at = now
                summary.changed_listing_ids.append(listing.id)

        summary.deactivated_listing_ids = self._deactivate_missing(
            db, source, set(latest_by_external_id), collected_department_codes, now
        )
        db.commit()
        return summary

    @classmethod
    def _apply_content(cls, listing: Listing, raw_listing: RawListing, known_department_codes: set[str]) -> None:
        """
        Copy what the source says onto the stored listing, and refresh its content hash.

        Args:
            listing: Listing to update.
            raw_listing: Listing read by the collector.
            known_department_codes: Seeded department codes (foreign key targets).
        """
        listing.external_url = raw_listing.external_url
        listing.kind = raw_listing.kind
        listing.lof_status = raw_listing.lof_status
        listing.litter_number = raw_listing.litter_number
        listing.mating_number = raw_listing.mating_number
        listing.mating_date = raw_listing.mating_date
        listing.birth_date = raw_listing.birth_date
        listing.male_count = raw_listing.male_count
        listing.female_count = raw_listing.female_count
        listing.puppies_available = raw_listing.puppies_available
        listing.variety_source_id = raw_listing.variety_source_id
        listing.colors = [color.as_json() for color in raw_listing.colors]
        listing.color_text = raw_listing.color_text
        listing.price_cents = raw_listing.price_cents
        listing.department_code = (
            raw_listing.department_code if raw_listing.department_code in known_department_codes else None
        )
        listing.zip_code = raw_listing.zip_code
        listing.city = raw_listing.city
        listing.sire_name = raw_listing.sire_name
        listing.sire_rating = raw_listing.sire_rating
        listing.dam_name = raw_listing.dam_name
        listing.dam_rating = raw_listing.dam_rating
        listing.litter_rating = raw_listing.litter_rating
        listing.photos = list(raw_listing.photos)
        listing.description = raw_listing.description
        listing.published_at = raw_listing.published_at
        listing.raw_json = raw_listing.raw_json

    @classmethod
    def _tracked_values(cls, listing: Listing) -> dict[str, str | None]:
        """
        Serialize the tracked fields of a listing.

        Args:
            listing: Listing to read.

        Returns:
            Field name → text value.
        """
        return {name: cls._serialize(getattr(listing, name)) for name in TRACKED_FIELDS}

    @staticmethod
    def _record_changes(
        db: Session,
        listing_id: int,
        values_before: dict[str, str | None],
        values_after: dict[str, str | None],
        now: datetime,
    ) -> bool:
        """
        Write one ``ListingChange`` per tracked field whose value moved.

        Args:
            db: Database session.
            listing_id: Listing that may have changed.
            values_before: Serialized tracked fields before the update.
            values_after: Serialized tracked fields after the update.
            now: Run time.

        Returns:
            Whether at least one field changed.
        """
        has_changed = False
        for name in TRACKED_FIELDS:
            if values_before[name] != values_after[name]:
                db.add(
                    ListingChange(
                        listing_id=listing_id,
                        field=name,
                        old_value=values_before[name],
                        new_value=values_after[name],
                        changed_at=now,
                    )
                )
                has_changed = True
        return has_changed

    @classmethod
    def _upsert_breeder(
        cls,
        db: Session,
        source: ListingSource,
        raw_listing: RawListing,
        known_department_codes: set[str],
        current_breeder_id: int | None,
    ) -> int | None:
        """
        Find the breeder of a listing, or create it, then copy what the source knows about it.

        A value the source leaves empty never erases a known one, and a SIREN or a Centrale Canine
        identifier already carried by another breeder is never moved onto this one. A breeder no rule
        finds (a private seller without SIREN, phone or affix) stays the one the listing already has,
        instead of a new one at every run.

        Args:
            db: Database session.
            source: Source of the listing.
            raw_listing: Listing read by the collector.
            known_department_codes: Seeded department codes.
            current_breeder_id: Breeder of the listing since an earlier run, if any.

        Returns:
            The breeder id, or None when the source names no breeder.
        """
        raw_breeder = raw_listing.breeder
        if raw_breeder is None:
            return None
        department_code = raw_listing.department_code if raw_listing.department_code in known_department_codes else None
        affix_key = BreederContactParser.affix_key(raw_breeder.affix)

        breeder = cls._find_breeder(db, source, raw_breeder, affix_key, department_code)
        if breeder is None and current_breeder_id is not None:
            breeder = db.get(Breeder, current_breeder_id)
        if breeder is None:
            breeder = Breeder()
            db.add(breeder)
            db.flush()

        if source == ListingSource.CENTRALE_CANINE and not cls._is_scc_breeder_id_taken(
            db, raw_breeder.source_id, breeder.id
        ):
            breeder.scc_breeder_id = raw_breeder.source_id
        if raw_breeder.siren is not None and not cls._is_siren_taken(db, raw_breeder.siren, breeder.id):
            breeder.siren = raw_breeder.siren
        breeder.display_name = cls._known_or_current(raw_breeder.display_name, breeder.display_name)
        breeder.affix = cls._known_or_current(raw_breeder.affix, breeder.affix)
        breeder.affix_normalized = cls._known_or_current(affix_key, breeder.affix_normalized)
        breeder.phone_e164 = cls._known_or_current(raw_breeder.phone_e164, breeder.phone_e164)
        breeder.zip_code = cls._known_or_current(raw_breeder.zip_code, breeder.zip_code)
        breeder.city = cls._known_or_current(raw_breeder.city, breeder.city)
        breeder.department_code = cls._known_or_current(department_code, breeder.department_code)
        breeder.latitude = cls._known_or_current(raw_breeder.latitude, breeder.latitude)
        breeder.longitude = cls._known_or_current(raw_breeder.longitude, breeder.longitude)
        breeder.website = cls._known_or_current(raw_breeder.website, breeder.website)
        breeder.scc_selection_group = cls._known_or_current(raw_breeder.selection_group, breeder.scc_selection_group)
        breeder.is_breed_club_member = cls._known_or_current(
            raw_breeder.is_breed_club_member, breeder.is_breed_club_member
        )
        db.flush()
        return breeder.id

    @staticmethod
    def _find_breeder(
        db: Session,
        source: ListingSource,
        raw_breeder: RawBreeder,
        affix_key: str | None,
        department_code: str | None,
    ) -> Breeder | None:
        """
        Match a breeder in the order of docs/03: SIREN, then the Centrale Canine identifier, then the
        phone, then the affix in the same department.

        Args:
            db: Database session.
            source: Source of the listing.
            raw_breeder: Breeder as the source describes it.
            affix_key: Normalized affix, for the last rule.
            department_code: Department of the listing, for the last rule.

        Returns:
            The existing breeder, or None for a breeder never seen.
        """
        if raw_breeder.siren is not None:
            breeder = db.query(Breeder).filter(Breeder.siren == raw_breeder.siren).first()
            if breeder is not None:
                return breeder
        if source == ListingSource.CENTRALE_CANINE:
            breeder = db.query(Breeder).filter(Breeder.scc_breeder_id == raw_breeder.source_id).first()
            if breeder is not None:
                return breeder
        if raw_breeder.phone_e164 is not None:
            breeder = db.query(Breeder).filter(Breeder.phone_e164 == raw_breeder.phone_e164).first()
            if breeder is not None:
                return breeder
        if affix_key is not None and department_code is not None:
            return (
                db.query(Breeder)
                .filter(Breeder.affix_normalized == affix_key, Breeder.department_code == department_code)
                .first()
            )
        return None

    @staticmethod
    def _is_siren_taken(db: Session, siren: str, breeder_id: int) -> bool:
        """
        Whether another breeder already carries this SIREN (the column is unique).

        Args:
            db: Database session.
            siren: SIREN to store.
            breeder_id: Breeder being updated.

        Returns:
            True when another breeder has it.
        """
        return db.query(Breeder).filter(Breeder.siren == siren, Breeder.id != breeder_id).first() is not None

    @staticmethod
    def _is_scc_breeder_id_taken(db: Session, scc_breeder_id: str, breeder_id: int) -> bool:
        """
        Whether another breeder already carries this Centrale Canine identifier (the column is unique).

        Args:
            db: Database session.
            scc_breeder_id: Identifier to store.
            breeder_id: Breeder being updated.

        Returns:
            True when another breeder has it.
        """
        return (
            db.query(Breeder).filter(Breeder.scc_breeder_id == scc_breeder_id, Breeder.id != breeder_id).first()
            is not None
        )

    @staticmethod
    def _known_or_current(new_value: StoredValue | None, current_value: StoredValue | None) -> StoredValue | None:
        """
        The value the source gives now, or the stored one when the source gives none.

        Args:
            new_value: Value read by the collector.
            current_value: Value stored.

        Returns:
            The value to keep.
        """
        return new_value if new_value is not None else current_value

    @staticmethod
    def _deactivate_missing(
        db: Session,
        source: ListingSource,
        seen_external_ids: set[str],
        collected_department_codes: set[str],
        now: datetime,
    ) -> list[int]:
        """
        Count a missed run for every active listing of the departments read that the run did not see,
        and deactivate those missed twice in a row or born more than six months ago.

        Args:
            db: Database session.
            source: Source of the run.
            seen_external_ids: Identifiers the run saw.
            collected_department_codes: Departments the run read.
            now: Run time.

        Returns:
            Ids of the listings deactivated by this run.
        """
        deactivated_ids: list[int] = []
        oldest_active_birth = (now - timedelta(days=BORN_LITTER_ACTIVE_DAYS)).date()
        active_listings = (
            db.query(Listing)
            .filter(
                Listing.source == source,
                Listing.is_active.is_(True),
                Listing.department_code.in_(collected_department_codes),
            )
            .all()
        )
        for listing in active_listings:
            if listing.external_id not in seen_external_ids:
                listing.missed_run_count += 1
            is_gone = listing.missed_run_count >= MISSED_RUNS_BEFORE_INACTIVE
            is_too_old = listing.birth_date is not None and listing.birth_date < oldest_active_birth
            if is_gone or is_too_old:
                listing.is_active = False
                db.add(
                    ListingChange(
                        listing_id=listing.id, field="is_active", old_value="true", new_value="false", changed_at=now
                    )
                )
                deactivated_ids.append(listing.id)
        return deactivated_ids

    @staticmethod
    def _serialize(value: ColumnValue) -> str | None:
        """
        Text form of a value, for the change history and the content hash.

        Args:
            value: Column value.

        Returns:
            The text, or None for None.
        """
        if value is None:
            return None
        if isinstance(value, StrEnum):
            return value.value
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, list):
            return json.dumps(value, sort_keys=True, ensure_ascii=False)
        return str(value)


listing_ingestion_service = ListingIngestionService()
