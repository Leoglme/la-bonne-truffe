"""Builds the ``LitterSnapshot`` of a group from its active listings."""

from datetime import date

from sqlalchemy.orm import Session

from core.clock import french_date_of
from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.lof_status import LofStatus
from models.breed import Breed
from models.breeder import Breeder
from models.department import Department
from models.listing import Listing
from models.litter_group import LitterGroup
from services.collectors.raw_listing import ColorReading
from services.matching.criteria import LitterSnapshot


class LitterSnapshotBuilder:
    """Merges what every source says about a litter group into one snapshot."""

    @classmethod
    def build(cls, db: Session, group: LitterGroup) -> LitterSnapshot | None:
        """
        Merge the listings of a group: a born listing wins over a declaration, LOF over unknown, a
        confirmed colour over everything.

        Args:
            db: Database session.
            group: The group.

        Returns:
            The snapshot, or None when the group has no listing left.
        """
        listings = db.query(Listing).filter(Listing.litter_group_id == group.id).order_by(Listing.id).all()
        active_listings = [listing for listing in listings if listing.is_active] or listings
        if not active_listings:
            return None
        breed = db.get(Breed, group.breed_id)
        breeder = db.get(Breeder, group.breeder_id) if group.breeder_id is not None else None
        department_code = next(
            (listing.department_code for listing in active_listings if listing.department_code), None
        )
        department = db.get(Department, department_code) if department_code is not None else None
        male_count, female_count = cls._sex_counts(active_listings)

        return LitterSnapshot(
            group_id=group.id,
            breed_slug=breed.slug if breed is not None else "",
            kind=cls._merged_kind(active_listings),
            department_code=department_code,
            department_name=department.name if department is not None else None,
            colors=cls._merged_colors(group, active_listings),
            lof_status=cls._merged_lof_status(active_listings),
            male_count=male_count,
            female_count=female_count,
            price_cents=min(
                (listing.price_cents for listing in active_listings if listing.price_cents is not None), default=None
            ),
            appeared_on=cls._appeared_on(group, listings),
            birth_date=group.birth_date,
            expected_birth_date=group.expected_birth_date,
            available_from=group.available_from,
            breeder_selection_group=breeder.scc_selection_group if breeder is not None else None,
            sire_rating=cls._first_known([listing.sire_rating for listing in active_listings]),
            dam_rating=cls._first_known([listing.dam_rating for listing in active_listings]),
        )

    @staticmethod
    def _appeared_on(group: LitterGroup, listings: list[Listing]) -> date:
        """
        The day the litter went online: the earliest publication date a source gives, else the day a
        collection first saw it. A litter discovered today but online for weeks is not news.

        Args:
            group: The group.
            listings: Every listing of the group.

        Returns:
            The day, in French time.
        """
        known_days = [french_date_of(listing.published_at) for listing in listings if listing.published_at is not None]
        known_days.append(french_date_of(group.first_seen_at))
        return min(known_days)

    @staticmethod
    def _merged_kind(listings: list[Listing]) -> ListingKind:
        """
        A litter is born as soon as one source says so, expected while every source says so.

        Args:
            listings: Active listings of the group.

        Returns:
            The kind of the litter.
        """
        kinds = {listing.kind for listing in listings}
        if ListingKind.LITTER_BORN in kinds:
            return ListingKind.LITTER_BORN
        if kinds == {ListingKind.LITTER_EXPECTED}:
            return ListingKind.LITTER_EXPECTED
        return ListingKind.PUPPY_AD

    @staticmethod
    def _merged_colors(group: LitterGroup, listings: list[Listing]) -> tuple[ColorReading, ...]:
        """
        Confirmed colours win; otherwise the certain colours of every source; otherwise the bundle.

        Args:
            group: The group, holding the colours confirmed by hand.
            listings: Active listings of the group.

        Returns:
            The colours, empty when unknown.
        """
        if group.confirmed_colors:
            return tuple(ColorReading(CoatColor(color), ColorConfidence.CONFIRMED) for color in group.confirmed_colors)
        readings = [
            ColorReading(CoatColor(entry["color"]), ColorConfidence(entry["confidence"]))
            for listing in listings
            for entry in listing.colors
        ]
        certain = [reading for reading in readings if reading.confidence != ColorConfidence.AMBIGUOUS]
        chosen = certain or readings
        unique: dict[CoatColor, ColorReading] = {}
        for reading in chosen:
            unique.setdefault(reading.color, reading)
        return tuple(unique.values())

    @staticmethod
    def _merged_lof_status(listings: list[Listing]) -> LofStatus:
        """
        LOF when one source says LOF, non-LOF when one says so and none says LOF, unknown otherwise.

        Args:
            listings: Active listings of the group.

        Returns:
            The LOF status.
        """
        statuses = {listing.lof_status for listing in listings}
        if LofStatus.LOF in statuses:
            return LofStatus.LOF
        if LofStatus.NON_LOF in statuses:
            return LofStatus.NON_LOF
        return LofStatus.UNKNOWN

    @classmethod
    def _sex_counts(cls, listings: list[Listing]) -> tuple[int | None, int | None]:
        """
        Males and females of a litter: as the Centrale Canine declares the born litter, else the puppies
        still offered by a litter ad, else the puppies its puppy ads offer, one puppy per ad. A declared
        mating reports none.

        Args:
            listings: Active listings of the group.

        Returns:
            The male and female counts, each None while unknown.
        """
        born_litters = sorted(
            (listing for listing in listings if listing.kind == ListingKind.LITTER_BORN),
            key=lambda listing: listing.source != ListingSource.CENTRALE_CANINE,
        )
        if born_litters:
            return (
                cls._first_known([listing.male_count for listing in born_litters]),
                cls._first_known([listing.female_count for listing in born_litters]),
            )
        puppy_ads = [
            listing
            for listing in listings
            if listing.kind == ListingKind.PUPPY_AD
            and listing.male_count is not None
            and listing.female_count is not None
        ]
        if not puppy_ads:
            return None, None
        return (
            sum(listing.male_count or 0 for listing in puppy_ads),
            sum(listing.female_count or 0 for listing in puppy_ads),
        )

    @staticmethod
    def _first_known(values: list[int | None]) -> int | None:
        """
        The first value a source knows.

        Args:
            values: Values of the listings.

        Returns:
            The first non-None value, or None.
        """
        return next((value for value in values if value is not None), None)
