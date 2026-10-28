"""Stores the listings of a run: insert, update, change history, disappearance."""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from models.breeder import Breeder
from models.department import Department
from models.listing import Listing
from models.listing_change import ListingChange
from services.collectors.raw_listing import RawListing

# Fields whose change is history worth keeping (« les sexes sont apparus », « la portée est née »).
TRACKED_FIELDS: tuple[str, ...] = (
    "kind",
    "lof_status",
    "litter_number",
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
        source: str,
        raw_listings: list[RawListing],
        collected_department_codes: set[str],
        now: datetime,
    ) -> IngestionSummary:
        """
        Store a run: new listings, changed fields, and listings that disappeared from the departments read.

        Args:
            db: Database session; committed at the end.
            source: ``ListingSource`` value of the run.
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
            breeder_id = self._upsert_breeder(db, raw_listing, known_department_codes)
            values = self._listing_values(raw_listing, known_department_codes)
            if listing is None:
                listing = Listing(
                    source=source,
                    external_id=raw_listing.external_id,
                    breed_id=raw_listing.breed_id,
                    breeder_id=breeder_id,
                    first_seen_at=now,
                    last_seen_at=now,
                    **values,
                )
                db.add(listing)
                db.flush()
                summary.new_listing_ids.append(listing.id)
                continue

            has_changed = self._record_changes(db, listing, values, now)
            if not listing.is_active:
                db.add(ListingChange(listing_id=listing.id, field="is_active", old_value="false", new_value="true"))
                has_changed = True
            for column, value in values.items():
                setattr(listing, column, value)
            listing.breeder_id = breeder_id or listing.breeder_id
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

    @staticmethod
    def content_hash(values: dict[str, object]) -> str:
        """
        Hash the tracked content of a listing, to tell at a glance whether it moved.

        Args:
            values: Column values of the listing.

        Returns:
            Hex SHA-256 of the tracked fields.
        """
        tracked = {name: ListingIngestionService._serialize(values.get(name)) for name in TRACKED_FIELDS}
        return hashlib.sha256(json.dumps(tracked, sort_keys=True).encode("utf-8")).hexdigest()

    @classmethod
    def _listing_values(cls, raw_listing: RawListing, known_department_codes: set[str]) -> dict[str, object]:
        """
        Column values of a listing from its raw form.

        Args:
            raw_listing: Listing read by the collector.
            known_department_codes: Seeded department codes (foreign key targets).

        Returns:
            The values, ``content_hash`` and ``raw_json`` included.
        """
        department_code = raw_listing.department_code if raw_listing.department_code in known_department_codes else None
        values: dict[str, object] = {
            "external_url": raw_listing.external_url,
            "kind": raw_listing.kind,
            "lof_status": raw_listing.lof_status,
            "litter_number": raw_listing.litter_number,
            "mating_date": raw_listing.mating_date,
            "birth_date": raw_listing.birth_date,
            "male_count": raw_listing.male_count,
            "female_count": raw_listing.female_count,
            "puppies_available": raw_listing.puppies_available,
            "variety_source_id": raw_listing.variety_source_id,
            "colors": [color.as_json() for color in raw_listing.colors],
            "color_text": raw_listing.color_text,
            "price_cents": raw_listing.price_cents,
            "department_code": department_code,
            "zip_code": raw_listing.zip_code,
            "city": raw_listing.city,
            "sire_name": raw_listing.sire_name,
            "sire_rating": raw_listing.sire_rating,
            "dam_name": raw_listing.dam_name,
            "dam_rating": raw_listing.dam_rating,
            "litter_rating": raw_listing.litter_rating,
            "photos": list(raw_listing.photos),
            "description": raw_listing.description,
            "raw_json": raw_listing.raw_json,
        }
        values["content_hash"] = cls.content_hash(values)
        return values

    @classmethod
    def _record_changes(cls, db: Session, listing: Listing, values: dict[str, object], now: datetime) -> bool:
        """
        Write one ``ListingChange`` per tracked field whose value moved.

        Args:
            db: Database session.
            listing: Stored listing, before the update.
            values: New values.
            now: Run time.

        Returns:
            Whether at least one field changed.
        """
        if listing.content_hash == values["content_hash"]:
            return False
        has_changed = False
        for name in TRACKED_FIELDS:
            old_value = cls._serialize(getattr(listing, name))
            new_value = cls._serialize(values.get(name))
            if old_value != new_value:
                db.add(
                    ListingChange(
                        listing_id=listing.id, field=name, old_value=old_value, new_value=new_value, changed_at=now
                    )
                )
                has_changed = True
        return has_changed

    @staticmethod
    def _upsert_breeder(db: Session, raw_listing: RawListing, known_department_codes: set[str]) -> int | None:
        """
        Find or create the breeder by its source identifier. The Centrale Canine JSON carries no name,
        phone or SIREN: those come later from the litter page (docs/02-sources.md).

        Args:
            db: Database session.
            raw_listing: Listing read by the collector.
            known_department_codes: Seeded department codes.

        Returns:
            The breeder id, or None when the source gives no breeder identifier.
        """
        if raw_listing.breeder_source_id is None:
            return None
        breeder = db.query(Breeder).filter(Breeder.scc_breeder_id == raw_listing.breeder_source_id).one_or_none()
        if breeder is None:
            breeder = Breeder(
                scc_breeder_id=raw_listing.breeder_source_id,
                department_code=(
                    raw_listing.department_code if raw_listing.department_code in known_department_codes else None
                ),
            )
            db.add(breeder)
        if raw_listing.breeder_selection_group is not None:
            breeder.scc_selection_group = raw_listing.breeder_selection_group
        db.flush()
        return breeder.id

    @staticmethod
    def _deactivate_missing(
        db: Session, source: str, seen_external_ids: set[str], collected_department_codes: set[str], now: datetime
    ) -> list[int]:
        """
        Count a missed run for every active listing of the departments read that the run did not see,
        and deactivate those missed twice in a row or born more than six months ago.

        Args:
            db: Database session.
            source: ``ListingSource`` value of the run.
            seen_external_ids: Identifiers the run saw.
            collected_department_codes: Departments the run read.
            now: Run time.

        Returns:
            Ids of the listings deactivated by this run.
        """
        deactivated_ids: list[int] = []
        oldest_active_birth: date = (now - timedelta(days=BORN_LITTER_ACTIVE_DAYS)).date()
        active_listings = db.query(Listing).filter(
            Listing.source == source,
            Listing.is_active.is_(True),
            Listing.department_code.in_(collected_department_codes),
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
    def _serialize(value: object) -> str | None:
        """
        Text form of a value, for the change history and the content hash.

        Args:
            value: Column value.

        Returns:
            The text, or None for None.
        """
        if value is None:
            return None
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, list | dict):
            return json.dumps(value, sort_keys=True, ensure_ascii=False)
        return str(value)


listing_ingestion_service = ListingIngestionService()
