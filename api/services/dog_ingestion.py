"""Stores the dogs of a run and ties them to their litters: parents, registered puppies, expected colours."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from enums.dog_role import DogRole
from enums.dog_sex import DogSex
from enums.listing_source import ListingSource
from models.dog import Dog
from models.litter_group import LitterGroup
from services.collectors.raw_dog import RawDog
from services.collectors.scc_dogs import RawLitterDetail
from services.dog_collection_planner import PUPPIES_RETRY_DAYS
from services.dog_color_inference import BROWN_COAT_COLORS, DogColorInference, ParentColorFacts


@dataclass
class DogIngestionSummary:
    """What a dog run changed in the database."""

    seen_count: int = 0
    new_dog_ids: list[int] = field(default_factory=list)
    changed_group_ids: list[int] = field(default_factory=list)


class DogIngestionService:
    """Upserts dogs by source and identifier, and keeps the litters' parents and expected colours in step."""

    def ingest(
        self, db: Session, dogs: list[RawDog], litter_details: list[RawLitterDetail], now: datetime
    ) -> DogIngestionSummary:
        """
        Store a run: every dog read, then, for each litter read, its parents, its registered puppies and the
        colours the parents imply.

        Args:
            db: Database session; committed at the end.
            dogs: Dogs read by the collector.
            litter_details: Litter pages read by the collector.
            now: Run time, naive UTC.

        Returns:
            The summary of the run.
        """
        summary = DogIngestionSummary(seen_count=len(dogs))
        for raw_dog in dogs:
            dog, is_new = self.upsert(db, raw_dog, now)
            if is_new:
                summary.new_dog_ids.append(dog.id)
        for detail in litter_details:
            group = db.get(LitterGroup, detail.group_id)
            if group is None:
                continue
            self._tie_parents(db, group, detail)
            self._tie_puppies(db, group, detail, now)
            self.refresh_expected_colors(db, group)
            summary.changed_group_ids.append(group.id)
        db.commit()
        return summary

    @staticmethod
    def upsert(db: Session, raw_dog: RawDog, now: datetime) -> tuple[Dog, bool]:
        """
        Find a dog by source and identifier, or create it, then copy what the source says. A value the source
        leaves empty never erases a known one; a dog first known as a puppy keeps that role.

        Args:
            db: Database session; flushed.
            raw_dog: Dog read by the collector.
            now: Run time, naive UTC.

        Returns:
            The dog, and whether it was just created.
        """
        dog = db.query(Dog).filter(Dog.source == raw_dog.source, Dog.external_id == raw_dog.external_id).one_or_none()
        is_new = dog is None
        if dog is None:
            dog = Dog(source=raw_dog.source, external_id=raw_dog.external_id, role=raw_dog.role)
            db.add(dog)
        if raw_dog.role == DogRole.PUPPY:
            dog.role = DogRole.PUPPY
        if raw_dog.litter_group_id is not None:
            dog.litter_group_id = raw_dog.litter_group_id
        dog.external_url = raw_dog.external_url or dog.external_url
        dog.name = raw_dog.name or dog.name
        dog.affix = raw_dog.affix or dog.affix
        dog.full_name = raw_dog.full_name or dog.full_name
        if raw_dog.sex != DogSex.UNKNOWN:
            dog.sex = raw_dog.sex
        dog.birth_date = raw_dog.birth_date or dog.birth_date
        dog.lof_number = raw_dog.lof_number or dog.lof_number
        dog.identifier = raw_dog.identifier or dog.identifier
        if raw_dog.color_code:
            dog.color_code = raw_dog.color_code
            dog.color = raw_dog.color
        dog.rating = raw_dog.rating if raw_dog.rating is not None else dog.rating
        if raw_dog.health_codes:
            dog.health_codes = list(raw_dog.health_codes)
        dog.e_locus = raw_dog.e_locus or dog.e_locus
        dog.has_dna_profile = raw_dog.has_dna_profile if raw_dog.has_dna_profile is not None else dog.has_dna_profile
        dog.sire_external_id = raw_dog.sire_external_id or dog.sire_external_id
        dog.dam_external_id = raw_dog.dam_external_id or dog.dam_external_id
        dog.sire_color_code = raw_dog.sire_color_code or dog.sire_color_code
        dog.dam_color_code = raw_dog.dam_color_code or dog.dam_color_code
        if raw_dog.photos:
            dog.photos = list(raw_dog.photos)
        dog.availability_text = raw_dog.availability_text or dog.availability_text
        dog.fetched_at = now
        db.flush()
        return dog, is_new

    @staticmethod
    def _tie_parents(db: Session, group: LitterGroup, detail: RawLitterDetail) -> None:
        """
        Point the group at its parents, when their pages are stored. The dam whelps at the breeder's: she is
        one of the dogs of the breeding, unless another breeding already claims her; the sire often comes
        from elsewhere and stays unattached.

        Args:
            db: Database session.
            group: The group.
            detail: What the litter page said.
        """
        for attribute, external_id in (("sire_dog_id", detail.sire_dog_id), ("dam_dog_id", detail.dam_dog_id)):
            if external_id is None:
                continue
            parent = (
                db.query(Dog)
                .filter(Dog.source == ListingSource.CENTRALE_CANINE, Dog.external_id == external_id)
                .first()
            )
            if parent is None:
                continue
            setattr(group, attribute, parent.id)
            if attribute == "dam_dog_id" and parent.breeder_id is None and group.breeder_id is not None:
                parent.breeder_id = group.breeder_id

    @staticmethod
    def _tie_puppies(db: Session, group: LitterGroup, detail: RawLitterDetail, now: datetime) -> None:
        """
        Tie the registered puppies to the group, and note when to look again while none is registered.

        Args:
            db: Database session.
            group: The group.
            detail: What the litter page said.
            now: Run time, naive UTC.
        """
        puppies_found = 0
        for reference in detail.puppies:
            puppy = (
                db.query(Dog)
                .filter(Dog.source == ListingSource.CENTRALE_CANINE, Dog.external_id == reference.dog_id)
                .first()
            )
            if puppy is None:
                continue
            puppy.litter_group_id = group.id
            puppy.role = DogRole.PUPPY
            puppy.breeder_id = group.breeder_id
            if puppy.sex == DogSex.UNKNOWN:
                puppy.sex = reference.sex
            puppies_found += 1
        group.puppies_detail_fetched_at = now
        group.puppies_detail_next_try_at = None if puppies_found else now + timedelta(days=PUPPIES_RETRY_DAYS)

    @staticmethod
    def refresh_expected_colors(db: Session, group: LitterGroup) -> None:
        """
        Store the colours the parents of a group imply (docs/04).

        Args:
            db: Database session.
            group: The group, whose parents are tied already.
        """
        sire = db.get(Dog, group.sire_dog_id) if group.sire_dog_id is not None else None
        dam = db.get(Dog, group.dam_dog_id) if group.dam_dog_id is not None else None
        expected = DogColorInference.expected_colors(
            DogIngestionService.color_facts_of(sire) if sire is not None else None,
            DogIngestionService.color_facts_of(dam) if dam is not None else None,
        )
        group.expected_colors = [color.as_json() for color in expected]

    @staticmethod
    def color_facts_of(dog: Dog) -> ParentColorFacts:
        """
        What a parent's page tells of its colour genes: its colour, its tested E locus, whether one of its own
        parents had a coat of the gold family, and whether its coat is brown.

        Args:
            dog: The parent.

        Returns:
            The facts the colour inference works on.
        """
        return ParentColorFacts(
            color=DogColorInference.canonical_color(dog.color_code) if dog.color_code else dog.color,
            e_locus=dog.e_locus or DogColorInference.e_locus_of(dog.health_codes),
            has_gold_parent=DogColorInference.has_gold_coat(dog.sire_color_code)
            or DogColorInference.has_gold_coat(dog.dam_color_code),
            has_brown_coat=DogColorInference.has_brown_coat(dog.color_code)
            if dog.color_code
            else dog.color in BROWN_COAT_COLORS,
        )


dog_ingestion_service = DogIngestionService()
