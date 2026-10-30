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
        Merge the listings of a group, read from the database with its breed, breeder and department.

        Args:
            db: Database session.
            group: The group.

        Returns:
            The snapshot, or None when the group has no listing left.
        """
        listings = db.query(Listing).filter(Listing.litter_group_id == group.id).order_by(Listing.id).all()
        department_code = cls.department_code_of(listings)
        return cls.build_from_listings(
            group,
            listings,
            breed=db.get(Breed, group.breed_id),
            breeder=db.get(Breeder, group.breeder_id) if group.breeder_id is not None else None,
            department=db.get(Department, department_code) if department_code is not None else None,
        )

    @classmethod
    def build_from_listings(
        cls,
        group: LitterGroup,
        listings: list[Listing],
        breed: Breed | None,
        breeder: Breeder | None,
        department: Department | None,
    ) -> LitterSnapshot | None:
        """
        Merge the listings of a group: a born listing wins over a declaration, LOF over unknown, a
        confirmed colour over everything.

        Args:
            group: The group.
            listings: Every listing of the group, in id order.
            breed: Breed of the group, when known.
            breeder: Breeder of the group, when known.
            department: Department ``department_code_of`` the listings gives, when known.

        Returns:
            The snapshot, or None when the group has no listing.
        """
        active_listings = cls.active_listings_of(listings)
        if not active_listings:
            return None
        department_code = cls.department_code_of(listings)
        male_count, female_count = cls._sex_counts(active_listings)

        return LitterSnapshot(
            group_id=group.id,
            name=cls.litter_name(breeder, listings),
            breed_slug=breed.slug if breed is not None else "",
            kind=cls._merged_kind(active_listings),
            department_code=department_code,
            department_name=department.name if department is not None else None,
            colors=cls._merged_colors(group, active_listings),
            lof_status=cls._merged_lof_status(active_listings),
            male_count=male_count,
            female_count=female_count,
            puppies_available=group.puppies_available,
            price_cents=min(
                (listing.price_cents for listing in active_listings if listing.price_cents is not None), default=None
            ),
            appeared_on=cls._appeared_on(group, listings),
            birth_date=group.birth_date,
            expected_birth_date=group.expected_birth_date,
            available_from=group.available_from,
            breeder_selection_group=breeder.scc_selection_group if breeder is not None else None,
            sire_rating=cls._first_known(
                [listing.sire_rating for listing in cls.centrale_canine_first(active_listings)]
            ),
            dam_rating=cls._first_known([listing.dam_rating for listing in cls.centrale_canine_first(active_listings)]),
        )

    @staticmethod
    def centrale_canine_first(listings: list[Listing]) -> list[Listing]:
        """
        Put the Centrale Canine listings first: what the breeder declared to the LOF wins over an ad.

        Args:
            listings: Listings of a group, in id order.

        Returns:
            The same listings, the Centrale Canine ones first, the others in their order.
        """
        declared = [listing for listing in listings if listing.source == ListingSource.CENTRALE_CANINE]
        advertised = [listing for listing in listings if listing.source != ListingSource.CENTRALE_CANINE]
        return declared + advertised

    @staticmethod
    def active_listings_of(listings: list[Listing]) -> list[Listing]:
        """
        The listings still online, or every listing once all are gone: the litter then shows greyed.

        Args:
            listings: Every listing of the group.

        Returns:
            The listings the snapshot is built from.
        """
        return [listing for listing in listings if listing.is_active] or listings

    @classmethod
    def department_code_of(cls, listings: list[Listing]) -> str | None:
        """
        The department of a litter: the first one its active listings give.

        Args:
            listings: Every listing of the group.

        Returns:
            The department code, or None while no listing gives one.
        """
        return next(
            (listing.department_code for listing in cls.active_listings_of(listings) if listing.department_code), None
        )

    @staticmethod
    def litter_name(breeder: Breeder | None, listings: list[Listing]) -> str:
        """
        Name of a litter: the breeder's affix, else the mother's name, else its LOF number.

        Args:
            breeder: The breeder, if known.
            listings: Listings of the litter.

        Returns:
            The name; never an invented one.
        """
        if breeder is not None and (breeder.affix or breeder.display_name):
            return breeder.affix or breeder.display_name or ""
        dam_name = next((listing.dam_name for listing in listings if listing.dam_name), None)
        if dam_name:
            return f"Portée de {dam_name}"
        litter_number = next((listing.litter_number for listing in listings if listing.litter_number), None)
        return f"Portée {litter_number}" if litter_number else "Portée sans nom"

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
        still offered by a litter ad, else the puppies its puppy ads still offer, one puppy per ad (a
        reserved, sold or adopted puppy no longer counts). A declared mating reports none.

        Args:
            listings: Active listings of the group.

        Returns:
            The male and female counts, each None while unknown.
        """
        born_litters = cls.centrale_canine_first(
            [listing for listing in listings if listing.kind == ListingKind.LITTER_BORN]
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
        offered_puppy_ads = [listing for listing in puppy_ads if listing.puppies_available != 0]
        return (
            sum(listing.male_count or 0 for listing in offered_puppy_ads),
            sum(listing.female_count or 0 for listing in offered_puppy_ads),
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
