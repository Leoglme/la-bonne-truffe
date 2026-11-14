"""Builds the ``LitterSnapshot`` of a group from its active listings."""

from datetime import date

from sqlalchemy.orm import Session

from core.clock import french_date_of
from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.dog_role import DogRole
from enums.dog_sex import DogSex
from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.lof_status import LofStatus
from models.breed import Breed
from models.breeder import Breeder
from models.department import Department
from models.dog import Dog
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
        breeder = db.get(Breeder, group.breeder_id) if group.breeder_id is not None else None
        department_code = cls.department_code_of(listings, breeder)
        puppies = (
            db.query(Dog).filter(Dog.litter_group_id == group.id, Dog.role == DogRole.PUPPY).order_by(Dog.id).all()
        )
        return cls.build_from_listings(
            group,
            listings,
            breed=db.get(Breed, group.breed_id),
            breeder=breeder,
            department=db.get(Department, department_code) if department_code is not None else None,
            puppies=puppies,
        )

    @classmethod
    def build_from_listings(
        cls,
        group: LitterGroup,
        listings: list[Listing],
        breed: Breed | None,
        breeder: Breeder | None,
        department: Department | None,
        puppies: list[Dog] | None = None,
    ) -> LitterSnapshot | None:
        """
        Merge the listings of a group: a born listing wins over a declaration, LOF over unknown, a
        confirmed colour over everything, then the registered puppies, then what the parents imply. When the
        listings still online say nothing of the colour, those gone offline still tell it: the Centrale Canine drops
        a litter from its list long before the breeder's site stops showing its puppies, all reserved.

        Args:
            group: The group.
            listings: Every listing of the group, in id order.
            breed: Breed of the group, when known.
            breeder: Breeder of the group, when known.
            department: Department ``department_code_of`` the listings gives, when known.
            puppies: The registered puppies of the group read at the Centrale Canine, when any.

        Returns:
            The snapshot, or None when the group has no listing.
        """
        active_listings = cls.active_listings_of(listings)
        if not active_listings:
            return None
        department_code = cls.department_code_of(listings, breeder)
        registered_puppies = puppies or []
        male_count, female_count = cls._sex_counts(group, active_listings, registered_puppies)
        known_prices = [listing.price_cents for listing in active_listings if listing.price_cents is not None]

        return LitterSnapshot(
            group_id=group.id,
            name=cls.litter_name(breeder, listings),
            breed_slug=breed.slug if breed is not None else "",
            kind=cls._merged_kind(active_listings),
            department_code=department_code,
            department_name=department.name if department is not None else None,
            colors=cls._merged_colors(group, active_listings, registered_puppies)
            or cls._merged_colors(group, listings, registered_puppies),
            lof_status=cls._merged_lof_status(active_listings),
            male_count=male_count,
            female_count=female_count,
            puppies_available=group.puppies_available,
            price_cents=min(known_prices, default=None),
            highest_price_cents=max(known_prices, default=None),
            appeared_on=cls._appeared_on(group, listings),
            birth_date=group.birth_date,
            expected_birth_date=group.expected_birth_date,
            available_from=group.available_from,
            breeder_selection_group=breeder.scc_selection_group if breeder is not None else None,
            sire_rating=cls._first_known(
                [listing.sire_rating for listing in cls.centrale_canine_first(active_listings)]
            ),
            dam_rating=cls._first_known([listing.dam_rating for listing in cls.centrale_canine_first(active_listings)]),
            gold_puppy_odds=cls.gold_puppy_odds(group),
        )

    @staticmethod
    def gold_puppy_odds(group: LitterGroup) -> float | None:
        """
        The share of gold puppies the parents' genotypes give, as the expected colours of the group keep it.

        Args:
            group: The group.

        Returns:
            1, 0.5 or 0.25, or None while the genotypes do not tell it.
        """
        for entry in group.expected_colors:
            odds = entry.get("puppy_odds")
            if entry.get("color") == CoatColor.GOLD.value and isinstance(odds, int | float):
                return float(odds)
        return None

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
    def department_code_of(cls, listings: list[Listing], breeder: Breeder | None) -> str | None:
        """
        The department of a litter: the first one its active listings give, else the one of its breeder, since the
        pages of a breeder's own site do not say where the breeding is.

        Args:
            listings: Every listing of the group.
            breeder: Breeder of the group, when known.

        Returns:
            The department code, or None while neither the listings nor the breeder give one.
        """
        listed_department_code = next(
            (listing.department_code for listing in cls.active_listings_of(listings) if listing.department_code), None
        )
        return listed_department_code or (breeder.department_code if breeder is not None else None)

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

    @classmethod
    def _merged_colors(
        cls, group: LitterGroup, listings: list[Listing], puppies: list[Dog]
    ) -> tuple[ColorReading, ...]:
        """
        Confirmed colours win; then the colours of the registered puppies; then a colour the parents make
        certain; then the certain colours an ad states itself; then what the parents make possible; then a bundle
        an ad states; then the variety of the Centrale Canine, which is the one of the mother whatever the father
        is: a gold mother and a black and tan father are filed under « rouge et doré ».

        Args:
            group: The group, holding the colours confirmed by hand and those its parents imply.
            listings: Active listings of the group.
            puppies: The registered puppies of the group.

        Returns:
            The colours, empty when unknown.
        """
        if group.confirmed_colors:
            return tuple(ColorReading(CoatColor(color), ColorConfidence.CONFIRMED) for color in group.confirmed_colors)
        puppy_readings = [
            ColorReading(puppy.color, ColorConfidence.CERTAIN) for puppy in puppies if puppy.color != CoatColor.INCONNUE
        ]
        if puppy_readings:
            return cls._unique_colors(puppy_readings)
        expected = [
            ColorReading(CoatColor(str(entry["color"])), ColorConfidence(str(entry["confidence"])))
            for entry in group.expected_colors
        ]
        inferred = [reading for reading in expected if reading.confidence == ColorConfidence.INFERRED]
        if inferred:
            return cls._unique_colors(inferred)
        ads_stating_a_colour = [listing for listing in listings if listing.variety_source_id is None]
        litters_filed_under_a_variety = [listing for listing in listings if listing.variety_source_id is not None]
        stated_readings = cls._color_readings(ads_stating_a_colour)
        certain_stated_readings = cls._certain_readings(stated_readings)
        if certain_stated_readings:
            return cls._unique_colors(certain_stated_readings)
        if expected or stated_readings:
            return cls._unique_colors(expected or stated_readings)
        variety_readings = cls._color_readings(litters_filed_under_a_variety)
        return cls._unique_colors(cls._certain_readings(variety_readings) or variety_readings)

    @staticmethod
    def _color_readings(listings: list[Listing]) -> list[ColorReading]:
        """
        The colours listings hold, in listing order.

        Args:
            listings: Listings of a group.

        Returns:
            One reading per colour of each listing.
        """
        return [
            ColorReading(CoatColor(entry["color"]), ColorConfidence(entry["confidence"]))
            for listing in listings
            for entry in listing.colors
        ]

    @staticmethod
    def _certain_readings(readings: list[ColorReading]) -> list[ColorReading]:
        """
        The readings a source is sure of.

        Args:
            readings: Colour readings.

        Returns:
            Those that are not a bundle of possible colours.
        """
        return [reading for reading in readings if reading.confidence != ColorConfidence.AMBIGUOUS]

    @staticmethod
    def _unique_colors(readings: list[ColorReading]) -> tuple[ColorReading, ...]:
        """
        Each colour once, the first reading of it kept.

        Args:
            readings: Readings in order of trust.

        Returns:
            The readings without a colour twice.
        """
        unique: dict[CoatColor, ColorReading] = {}
        for reading in readings:
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
    def _sex_counts(
        cls, group: LitterGroup, listings: list[Listing], puppies: list[Dog]
    ) -> tuple[int | None, int | None]:
        """
        Males and females of a litter, from the most trusted source first.

        The counts confirmed by hand after a call win; else those the Centrale Canine declares for the born
        litter; else the registered puppies read one by one; else the puppies still offered by a litter ad; else
        the puppies its puppy ads still offer, one puppy per ad (a reserved, sold or adopted puppy no longer
        counts). A declared mating reports none.

        Args:
            group: The group, holding the counts confirmed by hand.
            listings: Active listings of the group.
            puppies: The registered puppies of the group.

        Returns:
            The male and female counts, each None while unknown.
        """
        if group.confirmed_male_count is not None and group.confirmed_female_count is not None:
            return group.confirmed_male_count, group.confirmed_female_count
        born_litters = cls.centrale_canine_first(
            [listing for listing in listings if listing.kind == ListingKind.LITTER_BORN]
        )
        if born_litters:
            male_count = cls._first_known([listing.male_count for listing in born_litters])
            female_count = cls._first_known([listing.female_count for listing in born_litters])
            if male_count is not None and female_count is not None:
                return male_count, female_count
        sexed_puppies = [puppy for puppy in puppies if puppy.sex != DogSex.UNKNOWN]
        if sexed_puppies:
            return (
                sum(1 for puppy in sexed_puppies if puppy.sex == DogSex.MALE),
                sum(1 for puppy in sexed_puppies if puppy.sex == DogSex.FEMALE),
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
