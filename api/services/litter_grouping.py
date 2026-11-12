"""
Groups the listings into real litters (``litter_groups``) and keeps the group dates up to date.

Rules of docs/03-modele-de-donnees.md, in order, for a listing without group, always within the same
breeder and breed: the same litter number; the same mating number on the same source (the Centrale Canine
may declare the birth under a new identifier); for a puppy ad, a puppy ad of the same source born the same
day of the same mother (such a source lists each puppy apart); a listing of another source born, or
mated, three days apart at most, thirty when both name the same mother, or born a week at most from the birth
the mating of the other announces; the single litter of the breeder another source says was
born the very same day, whatever mother it names (a breeder's site may name another of its females; flagged
``is_grouping_probable``); for an ad without birth date, the single litter seen in the last sixty days
(flagged too). Apart from the very same day, two named mothers that differ never group, and two litter
listings of the same source are never grouped on a guess: a source lists a litter once.
"""

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from core.text import without_accents
from enums.listing_kind import ListingKind
from models.listing import Listing
from models.litter_group import LitterGroup

GESTATION_DAYS = 63
LEGAL_HANDOVER_DAYS = 56
DATE_TOLERANCE_DAYS = 3
SAME_DAM_TOLERANCE_DAYS = 30
GESTATION_TOLERANCE_DAYS = 7
NON_LETTER_OR_DIGIT_PATTERN = re.compile(r"[^a-z0-9]+")
PROBABLE_GROUPING_WINDOW_DAYS = 60


@dataclass
class GroupingResult:
    """What a regrouping changed."""

    new_group_ids: list[int] = field(default_factory=list)
    born_group_ids: list[int] = field(default_factory=list)
    fewer_puppies_group_ids: list[int] = field(default_factory=list)


class LitterGroupingService:
    """Assigns every ungrouped listing to a litter group and refreshes the group aggregates."""

    def regroup(self, db: Session, now: datetime) -> GroupingResult:
        """
        Group the listings that have no group yet, then refresh the dates and state of every group.

        Args:
            db: Database session; flushed, not committed: the caller commits with the matching that follows.
            now: Run time, naive UTC.

        Returns:
            The groups created, and the existing groups whose birth appeared, or which offer fewer puppies,
            since the previous regrouping.
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
            puppies_available_before = group.puppies_available
            self._refresh_group(db, group)
            if group.id in result.new_group_ids:
                continue
            if not was_born and group.birth_date is not None:
                result.born_group_ids.append(group.id)
            if (
                puppies_available_before is not None
                and group.puppies_available is not None
                and group.puppies_available < puppies_available_before
            ):
                result.fewer_puppies_group_ids.append(group.id)
        db.flush()
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

        if listing.mating_number:
            for other in grouped_listings_of_breeder:
                if other.source == listing.source and other.mating_number == listing.mating_number:
                    return db.get(LitterGroup, other.litter_group_id)

        if listing.kind == ListingKind.PUPPY_AD and listing.birth_date is not None:
            for other in grouped_listings_of_breeder:
                if (
                    other.source == listing.source
                    and other.kind == ListingKind.PUPPY_AD
                    and other.birth_date == listing.birth_date
                    and LitterGroupingService._has_same_dam(other, listing)
                ):
                    return db.get(LitterGroup, other.litter_group_id)

        other_sources = [other for other in grouped_listings_of_breeder if other.source != listing.source]
        for other in other_sources:
            if LitterGroupingService._have_close_dates(other, listing):
                return db.get(LitterGroup, other.litter_group_id)

        same_day_group_id = LitterGroupingService._single_litter_born_the_same_day(listing, grouped_listings_of_breeder)
        if same_day_group_id is not None:
            same_day_group = db.get(LitterGroup, same_day_group_id)
            if same_day_group is not None:
                same_day_group.is_grouping_probable = True
            return same_day_group

        if listing.kind != ListingKind.PUPPY_AD or listing.birth_date is not None:
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
    def _single_litter_born_the_same_day(listing: Listing, grouped_listings_of_breeder: list[Listing]) -> int | None:
        """
        The single litter of the breeder that another source says was born the very day of the listing, whatever
        mother it names: a breeder's site may name another of its females than the Centrale Canine. A litter that
        already holds a listing of the same source naming another mother is another litter.

        Args:
            listing: Listing without group.
            grouped_listings_of_breeder: The grouped listings of its breeder and breed.

        Returns:
            The group id, or None without a birth day, or when no litter, or several, were born that day.
        """
        if listing.birth_date is None:
            return None
        born_that_day_group_ids = {
            other.litter_group_id
            for other in grouped_listings_of_breeder
            if other.source != listing.source and other.birth_date == listing.birth_date
        }
        other_litter_group_ids = {
            other.litter_group_id
            for other in grouped_listings_of_breeder
            if other.source == listing.source and not LitterGroupingService._has_same_dam(other, listing)
        }
        candidate_group_ids = born_that_day_group_ids - other_litter_group_ids
        return candidate_group_ids.pop() if len(candidate_group_ids) == 1 else None

    @staticmethod
    def _have_close_dates(first: Listing, second: Listing) -> bool:
        """
        Whether two listings of the same breeder are one litter by their dates: births compared when both
        are known, else matings. Three days apart at most; thirty when both name the same mother, who
        cannot have two litters a month apart (two sources often date the mating a few days apart). Else the
        birth of one faces the birth the mating of the other announces, a week apart at most when both name the
        same mother (a gestation lasts 56 to 70 days), three days otherwise.

        Args:
            first: A listing.
            second: A listing of another source.

        Returns:
            True when the dates match.
        """
        if not LitterGroupingService._has_same_dam(first, second):
            return False
        are_both_dams_named = bool(first.dam_name and second.dam_name)
        tolerance_days = SAME_DAM_TOLERANCE_DAYS if are_both_dams_named else DATE_TOLERANCE_DAYS
        if first.birth_date is not None and second.birth_date is not None:
            return abs((first.birth_date - second.birth_date).days) <= tolerance_days
        if first.mating_date is not None and second.mating_date is not None:
            return abs((first.mating_date - second.mating_date).days) <= tolerance_days
        born_listing, mated_listing = (first, second) if first.birth_date is not None else (second, first)
        if born_listing.birth_date is None or mated_listing.mating_date is None:
            return False
        announced_birth_date = mated_listing.mating_date + timedelta(days=GESTATION_DAYS)
        gestation_tolerance_days = GESTATION_TOLERANCE_DAYS if are_both_dams_named else DATE_TOLERANCE_DAYS
        return abs((born_listing.birth_date - announced_birth_date).days) <= gestation_tolerance_days

    @staticmethod
    def _has_same_dam(first: Listing, second: Listing) -> bool:
        """
        Whether two listings may be the same litter as far as the mother goes: an unknown mother never
        tells two litters apart; two named mothers must have the same name, one source sometimes adding
        her titles before it or the breeder's affix after it (« CH. Victoire… », « Vutha Du Galain »).

        Args:
            first: A listing.
            second: Another listing.

        Returns:
            False only when both mothers are named and neither name holds the other.
        """
        if not first.dam_name or not second.dam_name:
            return True
        first_words = f" {LitterGroupingService._name_key(first.dam_name)} "
        second_words = f" {LitterGroupingService._name_key(second.dam_name)} "
        return first_words in second_words or second_words in first_words

    @staticmethod
    def _name_key(name: str) -> str:
        """
        A dog name for comparison: lowercase, without accents or punctuation.

        Args:
            name: Name as a source writes it (« Violette Of Loving Star »).

        Returns:
            « violette of loving star ».
        """
        plain_name = without_accents(name).lower()
        return " ".join(NON_LETTER_OR_DIGIT_PATTERN.sub(" ", plain_name).split())

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
        legal_handover_day = reference_birth + timedelta(days=LEGAL_HANDOVER_DAYS) if reference_birth else None
        group.available_from = LitterGroupingService._departure_day(listings, legal_handover_day)
        group.first_seen_at = min(listing.first_seen_at for listing in listings)
        group.last_seen_at = max(listing.last_seen_at for listing in listings)
        group.is_active = any(listing.is_active for listing in listings)
        group.puppies_available = LitterGroupingService._puppies_still_offered(listings)
        if group.breeder_id is None:
            group.breeder_id = next((listing.breeder_id for listing in listings if listing.breeder_id), None)

    @staticmethod
    def _departure_day(listings: list[Listing], legal_handover_day: date | None) -> date | None:
        """
        The day the puppies of a litter may leave: the earliest day its ads still online announce (those of every
        ad once all are gone), else the legal handover age. A breeder often keeps its puppies longer than the law
        asks; a day announced before the legal age is a slip, and the legal age stands.

        Args:
            listings: Every listing of the group.
            legal_handover_day: Birth (or expected birth) + 56 days, None while neither is known.

        Returns:
            The departure day, or None while no ad announces one and the birth is unknown.
        """
        announced_days = [
            (listing.available_from, listing.is_active) for listing in listings if listing.available_from is not None
        ]
        days_still_online = [day for day, is_online in announced_days if is_online]
        announced_day = min(days_still_online or [day for day, _ in announced_days], default=None)
        if announced_day is None or (legal_handover_day is not None and announced_day < legal_handover_day):
            return legal_handover_day
        return announced_day

    @staticmethod
    def _puppies_still_offered(listings: list[Listing]) -> int | None:
        """
        Puppies a litter still offers, from its active listings: the lowest count of its litter ads, else
        one per puppy ad still for sale (a puppy ad that left its source no longer counts).

        Args:
            listings: Every listing of the group.

        Returns:
            The count, or None while no active listing tells.
        """
        active_listings = [listing for listing in listings if listing.is_active]
        litter_ad_counts = [
            listing.puppies_available
            for listing in active_listings
            if listing.kind != ListingKind.PUPPY_AD and listing.puppies_available is not None
        ]
        if litter_ad_counts:
            return min(litter_ad_counts)
        puppy_ad_counts = [
            listing.puppies_available
            for listing in active_listings
            if listing.kind == ListingKind.PUPPY_AD and listing.puppies_available is not None
        ]
        return sum(puppy_ad_counts) if puppy_ad_counts else None


litter_grouping_service = LitterGroupingService()
