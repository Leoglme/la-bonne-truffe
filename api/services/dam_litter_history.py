"""The litters of each mother of a breeding, and when her next one is likely (docs/03, « Les mères d'un élevage »)."""

from dataclasses import dataclass, field
from datetime import date, timedelta
from difflib import SequenceMatcher
from statistics import median

from sqlalchemy.orm import Session

from core.text import without_accents
from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.dog_role import DogRole
from enums.dog_sex import DogSex
from enums.listing_source import ListingSource
from models.breeder import Breeder
from models.dog import Dog
from models.listing import Listing
from models.litter_group import LitterGroup
from services.collectors.raw_listing import ColorReading
from services.dog_color_inference import DogColorInference
from services.dog_ingestion import DogIngestionService
from services.dog_name import DogName

SAME_LITTER_DAYS = 3
DAYS_PER_MONTH = 30.44
DAYS_PER_YEAR = 365.25
TITLE_WORDS: frozenset[str] = frozenset({"ch", "multi", "multip", "int", "jch", "tr", "champion", "championne"})
GONE_STATUS_WORDS: tuple[str, ...] = ("retrait", "decede")
SAME_MOTHER_NAME_LIKENESS = 0.85
PARENT_ROLES: tuple[DogRole, ...] = (DogRole.REPRODUCER, DogRole.PARENT)
LEAST_GAPS_FOR_A_RHYTHM = 2

PROBABLE_LITTER_GAP_DAYS = 365
PROBABLE_LITTER_SHOWN_DAYS_BEFORE = 120
PROBABLE_LITTER_SHOWN_DAYS_AFTER = 30
OLDEST_MOTHER_AGE_YEARS = 8


@dataclass(frozen=True)
class DamLitter:
    """One litter of a mother: when it was born, and its father as a source names him."""

    born_on: date
    sire_name: str | None


@dataclass
class DamLitters:
    """
    One mother of a breeding: her name as a source writes it, her litters born, the litter she is announced to
    have, and her rows (on the breeder's site, at the Centrale Canine).
    """

    key: str
    written_name: str
    litters: list[DamLitter] = field(default_factory=list)
    expected_birth_date: date | None = None
    dogs: list[Dog] = field(default_factory=list)

    @property
    def name(self) -> str:
        """
        Her name as the app shows it: without the affix when one of her rows gives it so.

        Returns:
            « Selune », else the name a source writes (« Selune du Clos de l'Ecotay »).
        """
        return next((dog.name for dog in self.dogs if dog.name), self.written_name)

    @property
    def birth_dates(self) -> list[date]:
        """
        Her litters born, the oldest first.

        Returns:
            Their birth dates.
        """
        return sorted(litter.born_on for litter in self.litters)

    @property
    def last_litter(self) -> DamLitter | None:
        """
        Her latest litter born.

        Returns:
            The litter, None while none is known.
        """
        return max(self.litters, key=lambda litter: litter.born_on, default=None)

    @property
    def birth_date(self) -> date | None:
        """
        Her own birth date, as one of her rows gives it.

        Returns:
            The date, None while unknown.
        """
        return next((dog.birth_date for dog in self.dogs if dog.birth_date is not None), None)

    @property
    def is_gone(self) -> bool:
        """
        Whether her breeder's site says she is retired or dead.

        Returns:
            True when a status of hers says so.
        """
        return any(
            word in without_accents(dog.availability_text or "").lower()
            for dog in self.dogs
            for word in GONE_STATUS_WORDS
        )

    def age_years_on(self, day: date) -> int | None:
        """
        Her age in whole years on a day.

        Args:
            day: The day.

        Returns:
            Her age, None while her birth date is unknown.
        """
        if self.birth_date is None:
            return None
        return int((day - self.birth_date).days // DAYS_PER_YEAR)

    def rank_of(self, born_on: date) -> int | None:
        """
        Which of her known litters a litter is: 1 for the first one known.

        Args:
            born_on: Birth (or expected birth) of the litter.

        Returns:
            Its rank, None when the litter is not one of hers.
        """
        for index, birth_date in enumerate(self.birth_dates):
            if abs((birth_date - born_on).days) <= SAME_LITTER_DAYS:
                return index + 1
        return None

    def months_since_litter_before(self, born_on: date) -> int | None:
        """
        How long after her previous litter a litter of hers came.

        Args:
            born_on: Birth (or expected birth) of the litter.

        Returns:
            Whole months, None when no earlier litter of hers is known.
        """
        earlier = [day for day in self.birth_dates if (born_on - day).days > SAME_LITTER_DAYS]
        if not earlier:
            return None
        return round((born_on - max(earlier)).days / DAYS_PER_MONTH)

    def add_litter(self, born_on: date, sire_name: str | None) -> None:
        """
        Add a litter, unless one born within three days is known already (the same litter, from another source).

        Args:
            born_on: Its birth date.
            sire_name: Its father, as a source names him.
        """
        for index, litter in enumerate(self.litters):
            if abs((litter.born_on - born_on).days) <= SAME_LITTER_DAYS:
                if litter.sire_name is None and sire_name:
                    self.litters[index] = DamLitter(litter.born_on, sire_name)
                return
        self.litters.append(DamLitter(born_on, sire_name or None))


@dataclass(frozen=True)
class ProbableLitterEstimate:
    """The next litter a mother is likely to have: a year after her last one."""

    dam: DamLitters
    last_litter: DamLitter
    expected_on: date


class DamLitterHistory:
    """Gathers the litters of each mother of some breedings, from their litters in the app and from their sites."""

    @staticmethod
    def key_of(name: str | None) -> str:
        """
        A mother's name as two sources compare it: the dog name key, without the titles a source writes before it nor
        the number the Centrale Canine adds to a name already given (« Violette 1 du Clos de l'Ecotay »).

        Args:
            name: « TR. CH. Tess princess for kerdero (Sans Affixe) », « Violette 1 du Clos de l'Ecotay ».

        Returns:
            « tess princess for kerdero », « violette du clos de l ecotay »; empty for no name.
        """
        words = DogName.key_of(name).split()
        while words and words[0] in TITLE_WORDS:
            words = words[1:]
        return " ".join(word for word in words if not word.isdigit())

    @classmethod
    def of_breeders(cls, db: Session, breeder_ids: list[int]) -> dict[int, list[DamLitters]]:
        """
        The mothers of some breedings with their litters: those of the litters the app knows (the mother named by
        an ad, else by her Centrale Canine page), and those « Chiots nés chez nous » lists on their sites.

        Args:
            db: Database session.
            breeder_ids: The breedings.

        Returns:
            Their mothers by breeder id, a breeder without a known litter left out.
        """
        if not breeder_ids:
            return {}
        groups = db.query(LitterGroup).filter(LitterGroup.breeder_id.in_(breeder_ids)).order_by(LitterGroup.id).all()
        parent_names_by_group = cls._parent_names_by_group(db, [group.id for group in groups])
        dogs = (
            db.query(Dog)
            .filter(Dog.breeder_id.in_(breeder_ids), Dog.role != DogRole.PUPPY)
            .order_by(Dog.source, Dog.id)
            .all()
        )
        dogs_by_id = {dog.id: dog for dog in dogs}
        missing_dam_ids = {group.dam_dog_id for group in groups if group.dam_dog_id is not None} - set(dogs_by_id)
        if missing_dam_ids:
            dogs_by_id.update({dog.id: dog for dog in db.query(Dog).filter(Dog.id.in_(missing_dam_ids))})

        dams_by_breeder: dict[int, dict[str, DamLitters]] = {}
        for group in groups:
            if group.breeder_id is None:
                continue
            dams = dams_by_breeder.setdefault(group.breeder_id, {})
            dam_name, sire_name = parent_names_by_group.get(group.id, (None, None))
            dam_dog = dogs_by_id.get(group.dam_dog_id) if group.dam_dog_id is not None else None
            dam = cls._dam_named(dams, dam_name or (dam_dog.full_name or dam_dog.name if dam_dog else None))
            if dam is None:
                continue
            if dam_dog is not None and dam_dog not in dam.dogs:
                dam.dogs.append(dam_dog)
            if group.birth_date is not None:
                dam.add_litter(group.birth_date, sire_name)
            elif group.is_active and group.expected_birth_date is not None:
                dam.expected_birth_date = max(filter(None, (dam.expected_birth_date, group.expected_birth_date)))
        for breeder in db.query(Breeder).filter(Breeder.id.in_(breeder_ids)):
            dams = dams_by_breeder.setdefault(breeder.id, {})
            for entry in breeder.chiens_de_france_litters:
                dam = cls._dam_named(dams, entry.get("dam_name"))
                if dam is not None:
                    dam.add_litter(date.fromisoformat(entry["birth_date"]), entry.get("sire_name") or None)
        for dog in dogs:
            if dog.breeder_id is None or dog.sex == DogSex.MALE:
                continue
            dam = dams_by_breeder.get(dog.breeder_id, {}).get(cls.key_of(dog.full_name or dog.name))
            if dam is not None and dog not in dam.dogs:
                dam.dogs.append(dog)
        return {
            breeder_id: cls._merged_namesakes(list(dams.values()))
            for breeder_id, dams in dams_by_breeder.items()
            if dams
        }

    @staticmethod
    def probable_litters(dams: list[DamLitters], today: date) -> list[ProbableLitterEstimate]:
        """
        The next litter of each mother due soon: a year after her last one, from four months before until a month
        after. A mother with a litter announced already, retired, dead, or too old by then is left out.

        Args:
            dams: The mothers of a breeding.
            today: The day, in French time.

        Returns:
            The estimates, the soonest first.
        """
        estimates: list[ProbableLitterEstimate] = []
        for dam in dams:
            last_litter = dam.last_litter
            if last_litter is None or dam.expected_birth_date is not None or dam.is_gone:
                continue
            expected_on = last_litter.born_on + timedelta(days=PROBABLE_LITTER_GAP_DAYS)
            is_due_soon = (
                today - timedelta(days=PROBABLE_LITTER_SHOWN_DAYS_AFTER)
                <= expected_on
                <= today + timedelta(days=PROBABLE_LITTER_SHOWN_DAYS_BEFORE)
            )
            age_then = dam.age_years_on(expected_on)
            if not is_due_soon or (age_then is not None and age_then >= OLDEST_MOTHER_AGE_YEARS):
                continue
            estimates.append(ProbableLitterEstimate(dam, last_litter, expected_on))
        return sorted(estimates, key=lambda estimate: estimate.expected_on)

    @staticmethod
    def parents_by_name(db: Session) -> dict[str, Dog]:
        """
        Every parent and reproducer known, by name, the row with a colour code first: the Centrale Canine holds the
        colour genes.

        Args:
            db: Database session.

        Returns:
            One dog per name.
        """
        dogs_by_name: dict[str, Dog] = {}
        for dog in db.query(Dog).filter(Dog.role.in_(PARENT_ROLES)).order_by(Dog.id):
            name = DamLitterHistory.key_of(dog.full_name or dog.name)
            known = dogs_by_name.get(name)
            if name and (known is None or (known.source != ListingSource.CENTRALE_CANINE and dog.color_code)):
                dogs_by_name[name] = dog
        return dogs_by_name

    @staticmethod
    def likely_colors(estimate: ProbableLitterEstimate, parents_by_name: dict[str, Dog]) -> tuple[ColorReading, ...]:
        """
        The colours of the next litter of a mother if she has it with the father of her last one: what the couple
        gives, else her own colour, as a possibility.

        Args:
            estimate: The probable litter.
            parents_by_name: Every parent and reproducer known, by name.

        Returns:
            The colours, empty while hers is unknown.
        """
        dam_dog = next(
            (dog for dog in estimate.dam.dogs if dog.source == ListingSource.CENTRALE_CANINE),
            next(iter(estimate.dam.dogs), None),
        )
        if dam_dog is None:
            return ()
        dam_facts = DogIngestionService.color_facts_of(dam_dog)
        sire_dog = parents_by_name.get(DamLitterHistory.key_of(estimate.last_litter.sire_name))
        sire_facts = DogIngestionService.color_facts_of(sire_dog) if sire_dog is not None else None
        if sire_facts is not None and CoatColor.INCONNUE not in (sire_facts.color, dam_facts.color):
            expected = DogColorInference.expected_colors(sire_facts, dam_facts)
            if expected:
                return tuple(ColorReading(color.color, color.confidence) for color in expected)
        if dam_facts.color == CoatColor.INCONNUE:
            return ()
        return (ColorReading(dam_facts.color, ColorConfidence.AMBIGUOUS),)

    @staticmethod
    def median_gap_months(dams: list[DamLitters]) -> int | None:
        """
        How long a mother of the breeding waits between two litters, the middle value of every gap known.

        Args:
            dams: The mothers of a breeding.

        Returns:
            Whole months, None while fewer than two gaps are known.
        """
        gaps = [
            (later - earlier).days
            for dam in dams
            for earlier, later in zip(dam.birth_dates, dam.birth_dates[1:], strict=False)
        ]
        if len(gaps) < LEAST_GAPS_FOR_A_RHYTHM:
            return None
        return round(median(gaps) / DAYS_PER_MONTH)

    @staticmethod
    def dam_of(dams: list[DamLitters], name: str | None, dog: Dog | None) -> DamLitters | None:
        """
        The mother a litter names, among the mothers of its breeding.

        Args:
            dams: The mothers of the breeding.
            name: Her name as the ads of the litter write it.
            dog: Her Centrale Canine row, once read.

        Returns:
            The mother, None when none of them is hers.
        """
        for dam in dams:
            if (dog is not None and dog in dam.dogs) or (name and dam.key == DamLitterHistory.key_of(name)):
                return dam
        return None

    @staticmethod
    def _parent_names_by_group(db: Session, group_ids: list[int]) -> dict[int, tuple[str | None, str | None]]:
        """
        The mother and the father each litter's ads name first.

        Args:
            db: Database session.
            group_ids: The litters.

        Returns:
            Mother's then father's name by litter, each None while no ad names it.
        """
        names: dict[int, tuple[str | None, str | None]] = {}
        if not group_ids:
            return names
        for group_id, dam_name, sire_name in (
            db.query(Listing.litter_group_id, Listing.dam_name, Listing.sire_name)
            .filter(Listing.litter_group_id.in_(group_ids))
            .order_by(Listing.id)
        ):
            if group_id is None:
                continue
            known_dam, known_sire = names.get(group_id, (None, None))
            names[group_id] = (known_dam or dam_name or None, known_sire or sire_name or None)
        return names

    @classmethod
    def _dam_named(cls, dams: dict[str, DamLitters], name: str | None) -> DamLitters | None:
        """
        The mother of a name, added to the breeding's mothers the first time she is named.

        Args:
            dams: The mothers of the breeding, by key.
            name: Her name as a source writes it.

        Returns:
            The mother, None for no name.
        """
        key = cls.key_of(name)
        if not key or name is None:
            return None
        return dams.setdefault(key, DamLitters(key=key, written_name=" ".join(name.split())))

    @staticmethod
    def _merged_namesakes(dams: list[DamLitters]) -> list[DamLitters]:
        """
        One mother for the two spellings two sources give of her (« Sweety so love suzy », « … susy »): two names
        alike, each litter of one born with a litter of the other.

        Args:
            dams: The mothers of a breeding, one per spelling.

        Returns:
            The mothers, each once.
        """
        merged: list[DamLitters] = []
        for dam in sorted(dams, key=lambda candidate: -len(candidate.litters)):
            twin = next(
                (
                    kept
                    for kept in merged
                    if SequenceMatcher(None, kept.key, dam.key).ratio() >= SAME_MOTHER_NAME_LIKENESS
                    and dam.litters
                    and all(kept.rank_of(litter.born_on) is not None for litter in dam.litters)
                ),
                None,
            )
            if twin is None:
                merged.append(dam)
                continue
            twin.dogs.extend(dog for dog in dam.dogs if dog not in twin.dogs)
            if dam.expected_birth_date is not None:
                twin.expected_birth_date = max(filter(None, (twin.expected_birth_date, dam.expected_birth_date)))
        return merged
