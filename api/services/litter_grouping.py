"""
Groups the listings into real litters (``litter_groups``) and keeps the group dates up to date.

Rules of docs/03-modele-de-donnees.md, in order, for a listing without group: same breeder and same
litter number; else same breeder, same breed and birth dates three days apart at most; else, for an
ad without birth date, the single litter of the same breeder and breed seen in the last sixty days
(flagged ``is_grouping_probable``). Two listings of the same source are never grouped on a guess: a
source lists a litter once, so two of its listings are two litters unless they share a litter number.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from enums.listing_kind import ListingKind
from models.listing import Listing
from models.litter_group import LitterGroup

GESTATION_DAYS = 63
LEGAL_HANDOVER_DAYS = 56
BIRTH_DATE_TOLERANCE_DAYS = 3
PROBABLE_GROUPING_WINDOW_DAYS = 60


@dataclass
class GroupingResult:
    """What a regrouping changed."""

    new_group_ids: list[int] = field(default_factory=list)
    born_group_ids: list[int] = field(default_factory=list)


class LitterGroupingService:
    """Assigns every ungrouped listing to a litter group and refreshes the group aggregates."""

    def regroup(self, db: Session, now: datetime) -> GroupingResult:
        """
        Group the listings that have no group yet, then refresh the dates and state of every group.

        Args:
            db: Database session; committed at the end.
            now: Run time, naive UTC.

        Returns:
            The groups created, and the existing groups whose birth appeared during this regrouping.
        """
        result = GroupingResult()
        ungrouped = db.query(Listing).filter(Listing.litter_group_id.is_(None)).order_by(Listing.id).all()
        for listing in ungrouped:
            group = self._find_group(db, listing, now)
            if group is None:
                group = LitterGroup(
                    breed_id=listing.breed_id,
                    breeder_id=listing.breeder_id,
                    first_seen_at=listing.first_seen_at,
                    last_seen_at=listing.last_seen_at,
                )
                db.add(group)
                db.flush()
                result.new_group_ids.append(group.id)
            listing.litter_group_id = group.id
        db.flush()

        for group in db.query(LitterGroup).all():
            was_born = group.birth_date is not None
            self._refresh_group(db, group)
            if not was_born and group.birth_date is not None and group.id not in result.new_group_ids:
                result.born_group_ids.append(group.id)
        db.commit()
        return result

    @staticmethod
    def _find_group(db: Session, listing: Listing, now: datetime) -> LitterGroup | None:
        """
        Find the existing group of a listing, following the rules of docs/03 in order.

        Args:
            db: Database session.
            listing: Listing without group.
            now: Run time.

        Returns:
            The group, or None when the listing is a new litter.
        """
        if listing.breeder_id is None:
            return None
        grouped_listings_of_breeder = (
            db.query(Listing)
            .filter(
                Listing.breeder_id == listing.breeder_id,
                Listing.breed_id == listing.breed_id,
                Listing.litter_group_id.is_not(None),
                Listing.id != listing.id,
            )
            .all()
        )

        if listing.litter_number:
            for other in grouped_listings_of_breeder:
                if other.litter_number == listing.litter_number:
                    return db.get(LitterGroup, other.litter_group_id)

        other_sources = [other for other in grouped_listings_of_breeder if other.source != listing.source]
        if listing.birth_date is not None:
            for other in other_sources:
                if other.birth_date is not None and abs((other.birth_date - listing.birth_date).days) <= (
                    BIRTH_DATE_TOLERANCE_DAYS
                ):
                    return db.get(LitterGroup, other.litter_group_id)
            return None

        if listing.kind != ListingKind.PUPPY_AD:
            return None
        recent_group_ids = {
            other.litter_group_id
            for other in other_sources
            if other.last_seen_at >= now - timedelta(days=PROBABLE_GROUPING_WINDOW_DAYS)
        }
        if len(recent_group_ids) != 1:
            return None
        group = db.get(LitterGroup, recent_group_ids.pop())
        if group is not None:
            group.is_grouping_probable = True
        return group

    @staticmethod
    def _refresh_group(db: Session, group: LitterGroup) -> None:
        """
        Recompute the dates and state of a group from its listings.

        Args:
            db: Database session.
            group: Group to refresh.
        """
        listings = db.query(Listing).filter(Listing.litter_group_id == group.id).all()
        if not listings:
            group.is_active = False
            return
        birth_dates = [listing.birth_date for listing in listings if listing.birth_date is not None]
        mating_dates = [listing.mating_date for listing in listings if listing.mating_date is not None]
        group.birth_date = min(birth_dates) if birth_dates else None
        group.mating_date = min(mating_dates) if mating_dates else None
        group.expected_birth_date = (
            group.mating_date + timedelta(days=GESTATION_DAYS)
            if group.birth_date is None and group.mating_date is not None
            else None
        )
        reference_birth: date | None = group.birth_date or group.expected_birth_date
        group.available_from = reference_birth + timedelta(days=LEGAL_HANDOVER_DAYS) if reference_birth else None
        group.first_seen_at = min(listing.first_seen_at for listing in listings)
        group.last_seen_at = max(listing.last_seen_at for listing in listings)
        group.is_active = any(listing.is_active for listing in listings)
        if group.breeder_id is None:
            group.breeder_id = next((listing.breeder_id for listing in listings if listing.breeder_id), None)


litter_grouping_service = LitterGroupingService()
