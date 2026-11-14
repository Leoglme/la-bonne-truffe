"""Reads the litters for the dashboard: cards, detail, follow-ups. Every query is scoped to the user."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Self

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.dog_role import DogRole
from enums.listing_kind import ListingKind
from enums.listing_source import ListingSource
from enums.litter_photo_source import LitterPhotoSource
from enums.match_flag import MatchFlag
from enums.match_tier import MatchTier
from models.breed import Breed
from models.breeder import Breeder
from models.department import Department
from models.dog import Dog
from models.follow_up import FollowUp, FollowUpNote
from models.listing import Listing
from models.listing_change import ListingChange
from models.listing_match import ListingMatch
from models.litter_group import LitterGroup
from models.search_profile import SearchProfile
from schemas.litter import (
    FollowUpCard,
    FollowUpNoteResponse,
    LitterBreeder,
    LitterCard,
    LitterColor,
    LitterDetail,
    LitterExpectedColor,
    LitterFollowUp,
    LitterParent,
    LitterPuppy,
    LitterReason,
    LitterSourceListing,
)
from schemas.notification import NotificationLitter
from services.collectors.chiens_de_france_sites import breed_page_of
from services.dog_chip import DogChip
from services.dog_color_inference import DogColorInference
from services.dog_ingestion import DogIngestionService
from services.dog_name import DogName
from services.genetic_screening import GeneticScreeningReader
from services.matching.snapshot_builder import LitterSnapshotBuilder
from services.puppy_ad_state_reader import PuppyAdStateReader

SELECTED_BREEDING_GROUP = 1
GROUPS_WITH_AFFIX = (1, 2)
PHOTOS_FIELD = "photos"


class LitterSort(StrEnum):
    """Order of the home screen list."""

    SCORE = "score"
    FRESHNESS = "freshness"


@dataclass
class LitterCardFacts:
    """What the cards of some groups are built from, loaded in one query per table instead of one per litter."""

    listings_by_group: dict[int, list[Listing]] = field(default_factory=dict)
    breeds_by_id: dict[int, Breed] = field(default_factory=dict)
    breeders_by_id: dict[int, Breeder] = field(default_factory=dict)
    departments_by_code: dict[str, Department] = field(default_factory=dict)
    follow_ups_by_group: dict[int, FollowUp] = field(default_factory=dict)
    puppies_by_group: dict[int, list[Dog]] = field(default_factory=dict)
    parent_photos_by_dog_id: dict[int, str] = field(default_factory=dict)

    @classmethod
    def load(cls, db: Session, user_id: int, groups: list[LitterGroup]) -> Self:
        """
        Load the listings, breeds, breeders, departments, registered puppies, the user's follow-ups of some groups,
        and the photos of the parents of those without a photo of their own.

        Args:
            db: Database session.
            user_id: The user.
            groups: The groups to build cards for.

        Returns:
            The facts, empty for no group.
        """
        facts = cls()
        if not groups:
            return facts
        group_ids = [group.id for group in groups]
        for listing in db.query(Listing).filter(Listing.litter_group_id.in_(group_ids)).order_by(Listing.id):
            if listing.litter_group_id is not None:
                facts.listings_by_group.setdefault(listing.litter_group_id, []).append(listing)
        facts.breeds_by_id = {
            breed.id: breed for breed in db.query(Breed).filter(Breed.id.in_({group.breed_id for group in groups}))
        }
        breeder_ids = {group.breeder_id for group in groups if group.breeder_id is not None}
        if breeder_ids:
            facts.breeders_by_id = {
                breeder.id: breeder for breeder in db.query(Breeder).filter(Breeder.id.in_(breeder_ids))
            }
        department_codes = {
            code
            for code in (
                LitterSnapshotBuilder.department_code_of(
                    facts.listings_by_group.get(group.id, []),
                    facts.breeders_by_id.get(group.breeder_id) if group.breeder_id is not None else None,
                )
                for group in groups
            )
            if code is not None
        }
        if department_codes:
            facts.departments_by_code = {
                department.code: department
                for department in db.query(Department).filter(Department.code.in_(department_codes))
            }
        facts.follow_ups_by_group = {
            follow_up.litter_group_id: follow_up
            for follow_up in db.query(FollowUp).filter(
                FollowUp.user_id == user_id, FollowUp.litter_group_id.in_(group_ids)
            )
        }
        for puppy in (
            db.query(Dog).filter(Dog.litter_group_id.in_(group_ids), Dog.role == DogRole.PUPPY).order_by(Dog.id)
        ):
            if puppy.litter_group_id is not None:
                facts.puppies_by_group.setdefault(puppy.litter_group_id, []).append(puppy)
        facts.parent_photos_by_dog_id = cls._parent_photos_of_groups_without_photo(db, groups, facts.listings_by_group)
        return facts

    @classmethod
    def _parent_photos_of_groups_without_photo(
        cls, db: Session, groups: list[LitterGroup], listings_by_group: dict[int, list[Listing]]
    ) -> dict[int, str]:
        """
        The photo of each parent of the groups none of whose listings has a photo: its own, else the one a
        breeder's site shows of it.

        Args:
            db: Database session.
            groups: The groups.
            listings_by_group: Their listings.

        Returns:
            Photo URL by parent dog id.
        """
        parent_ids = {
            dog_id
            for group in groups
            if not any(listing.photos for listing in listings_by_group.get(group.id, []))
            for dog_id in (group.dam_dog_id, group.sire_dog_id)
            if dog_id is not None
        }
        if not parent_ids:
            return {}
        parents = db.query(Dog).filter(Dog.id.in_(parent_ids)).order_by(Dog.id).all()
        photos_by_parent_id = cls.site_photos_of_parents(db, parents)
        for parent in parents:
            if parent.photos:
                photos_by_parent_id[parent.id] = parent.photos[0]
        return photos_by_parent_id

    @staticmethod
    def site_photos_of_parents(db: Session, parents: list[Dog]) -> dict[int, str]:
        """
        The first photo the breeders' sites on Chiens de France show of each parent: the dog of the same chip, else
        of the same full name, since the Centrale Canine knows some dogs by a tattoo and some sites give no chip.

        Args:
            db: Database session.
            parents: The parents read at the Centrale Canine.

        Returns:
            Photo URL by parent dog id, for the parents a site shows with a photo.
        """
        if not parents:
            return {}
        photos_by_chip: dict[str, str] = {}
        photos_by_name: dict[str, str] = {}
        for site_dog in db.query(Dog).filter(Dog.source == ListingSource.CHIENS_DE_FRANCE).order_by(Dog.id):
            if not site_dog.photos:
                continue
            chip = DogChip.key_of(site_dog.identifier)
            if chip is not None:
                photos_by_chip.setdefault(chip, site_dog.photos[0])
            name = DogName.key_of(site_dog.full_name or site_dog.name)
            if name:
                photos_by_name.setdefault(name, site_dog.photos[0])
        photos_by_parent_id: dict[int, str] = {}
        for parent in parents:
            chip = DogChip.key_of(parent.identifier)
            photo = (photos_by_chip.get(chip) if chip is not None else None) or photos_by_name.get(
                DogName.key_of(parent.full_name or parent.name)
            )
            if photo is not None:
                photos_by_parent_id[parent.id] = photo
        return photos_by_parent_id


class LitterQueryService:
    """Builds the litter payloads from the groups, their listings and the user's active profile."""

    @classmethod
    def list_cards(
        cls,
        db: Session,
        user_id: int,
        tier: MatchTier | None,
        kind: ListingKind | None,
        is_active: bool,
        sort: LitterSort,
    ) -> list[LitterCard]:
        """
        The litters of the home screen; excluded litters never show, ignored ones only on request.

        Args:
            db: Database session.
            user_id: The user.
            tier: Only this tier, when given.
            kind: Only this kind (``litter_expected`` for « À naître »), when given.
            is_active: Only active litters (True) or only gone ones (False).
            sort: Best score first, or most recently seen first.

        Returns:
            The cards.
        """
        matches_by_group = cls._matches_by_group(db, user_id)
        groups = db.query(LitterGroup).filter(LitterGroup.is_active.is_(is_active)).all()
        listed_groups = [group for group in groups if cls._is_listed(matches_by_group.get(group.id), tier)]
        facts = LitterCardFacts.load(db, user_id, listed_groups)
        cards: list[LitterCard] = []
        for group in listed_groups:
            card = cls._card(group, matches_by_group.get(group.id), facts)
            if card is None or (kind is not None and card.kind != kind):
                continue
            cards.append(card)
        if sort == LitterSort.FRESHNESS:
            return sorted(cards, key=lambda card: card.first_seen_at, reverse=True)
        return sorted(cards, key=lambda card: (card.score or 0, card.first_seen_at), reverse=True)

    @classmethod
    def detail(cls, db: Session, user_id: int, litter_group_id: int) -> LitterDetail:
        """
        Everything the detail screen shows about a litter.

        Args:
            db: Database session.
            user_id: The user.
            litter_group_id: The litter.

        Returns:
            The detail.

        Raises:
            HTTPException: 404 when the litter does not exist.
        """
        group = cls.get_group(db, litter_group_id)
        match = cls._matches_by_group(db, user_id).get(group.id)
        facts = LitterCardFacts.load(db, user_id, [group])
        card = cls._card(group, match, facts)
        if card is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portée introuvable")
        listings = facts.listings_by_group.get(group.id, [])
        breeder = facts.breeders_by_id.get(group.breeder_id) if group.breeder_id is not None else None
        breed = facts.breeds_by_id.get(group.breed_id)
        follow_up = facts.follow_ups_by_group.get(group.id)
        photos = list(dict.fromkeys(photo for listing in listings for photo in listing.photos))

        sire = cls._parent(listings, lambda listing: listing.sire_name, lambda listing: listing.sire_rating)
        dam = cls._parent(listings, lambda listing: listing.dam_name, lambda listing: listing.dam_rating)
        sire_dog = db.get(Dog, group.sire_dog_id) if group.sire_dog_id else None
        dam_dog = db.get(Dog, group.dam_dog_id) if group.dam_dog_id else None
        site_photos_by_parent_id = LitterCardFacts.site_photos_of_parents(
            db, [dog for dog in (sire_dog, dam_dog) if dog is not None]
        )
        return LitterDetail(
            **card.model_dump(),
            reasons=[LitterReason(text=str(reason["text"]), points=int(reason["points"])) for reason in match.reasons]
            if match is not None
            else [],
            flags=[MatchFlag(flag) for flag in match.flags] if match is not None else [],
            litter_number=next((listing.litter_number for listing in listings if listing.litter_number), None),
            mating_date=group.mating_date,
            sire=cls._parent_with_dog(sire, sire_dog, site_photos_by_parent_id),
            dam=cls._parent_with_dog(dam, dam_dog, site_photos_by_parent_id),
            breeder=cls._breeder(breeder, breed.chiens_de_france_id if breed is not None else None)
            if breeder is not None
            else None,
            photos=photos,
            puppies=[
                LitterPuppy(
                    id=puppy.id,
                    name=puppy.name,
                    sex=puppy.sex,
                    color=puppy.color,
                    color_code=puppy.color_code,
                    identifier=puppy.identifier,
                    lof_number=puppy.lof_number,
                    external_url=puppy.external_url,
                )
                for puppy in facts.puppies_by_group.get(group.id, [])
            ],
            expected_colors=[
                LitterExpectedColor(
                    color=CoatColor(str(entry["color"])),
                    confidence=ColorConfidence(str(entry["confidence"])),
                    reason=str(entry.get("reason", "")),
                    puppy_odds=float(odds) if isinstance(odds := entry.get("puppy_odds"), int | float) else None,
                )
                for entry in group.expected_colors
            ],
            gold_exclusion_reason=DogColorInference.gold_exclusion_of(group.expected_colors),
            listings=[
                LitterSourceListing(
                    id=listing.id,
                    source=listing.source,
                    kind=listing.kind,
                    external_url=listing.breeder_site_page_url or listing.external_url,
                    litter_number=listing.litter_number,
                    last_seen_at=listing.last_seen_at,
                    is_active=listing.is_active,
                    male_count=listing.male_count,
                    female_count=listing.female_count,
                    colors=[
                        LitterColor(color=CoatColor(entry["color"]), confidence=ColorConfidence(entry["confidence"]))
                        for entry in listing.colors
                    ],
                    photos=listing.photos,
                    puppy_state=PuppyAdStateReader.state_of(listing),
                    confirmed_color=listing.confirmed_color,
                    price_cents=listing.price_cents,
                )
                for listing in listings
            ],
            follow_up=cls._follow_up_payload(db, follow_up) if follow_up is not None else None,
            photos_added_at=cls._photos_added_at(db, listings),
        )

    @classmethod
    def list_follow_ups(cls, db: Session, user_id: int) -> list[FollowUpCard]:
        """
        The followed litters, the next reminder first.

        Args:
            db: Database session.
            user_id: The user.

        Returns:
            The follow-up cards.
        """
        follow_ups = db.query(FollowUp).filter(FollowUp.user_id == user_id).all()
        if not follow_ups:
            return []
        matches_by_group = cls._matches_by_group(db, user_id)
        followed_group_ids = [follow_up.litter_group_id for follow_up in follow_ups]
        groups_by_id = {
            group.id: group for group in db.query(LitterGroup).filter(LitterGroup.id.in_(followed_group_ids))
        }
        facts = LitterCardFacts.load(db, user_id, list(groups_by_id.values()))
        last_notes = cls._last_notes_by_follow_up(db, [follow_up.id for follow_up in follow_ups])
        cards: list[FollowUpCard] = []
        for follow_up in follow_ups:
            group = groups_by_id.get(follow_up.litter_group_id)
            card = cls._card(group, matches_by_group.get(group.id), facts) if group is not None else None
            if card is None:
                continue
            last_note = last_notes.get(follow_up.id)
            cards.append(
                FollowUpCard(
                    litter=card,
                    status=follow_up.status,
                    next_reminder_at=follow_up.next_reminder_at,
                    last_contact_at=follow_up.last_contact_at,
                    last_note=FollowUpNoteResponse(
                        id=last_note.id, created_at=last_note.created_at, text=last_note.text
                    )
                    if last_note is not None
                    else None,
                )
            )
        return sorted(
            cards,
            key=lambda card: (card.next_reminder_at is None, card.next_reminder_at or card.litter.first_seen_at),
        )

    @classmethod
    def list_notification_litters(
        cls, db: Session, user_id: int, litter_group_ids: set[int]
    ) -> dict[int, NotificationLitter]:
        """
        The litters the notifications of a user show: their card and the breeder's phone, by group.

        Args:
            db: Database session.
            user_id: The user.
            litter_group_ids: Groups the notifications are about.

        Returns:
            One litter per group still readable, by group id.
        """
        if not litter_group_ids:
            return {}
        groups = db.query(LitterGroup).filter(LitterGroup.id.in_(litter_group_ids)).all()
        facts = LitterCardFacts.load(db, user_id, groups)
        matches_by_group = cls._matches_by_group(db, user_id)
        litters: dict[int, NotificationLitter] = {}
        for group in groups:
            card = cls._card(group, matches_by_group.get(group.id), facts)
            if card is None:
                continue
            breeder = facts.breeders_by_id.get(group.breeder_id) if group.breeder_id is not None else None
            litters[group.id] = NotificationLitter(
                **card.model_dump(), breeder_phone_e164=breeder.phone_e164 if breeder is not None else None
            )
        return litters

    @staticmethod
    def get_group(db: Session, litter_group_id: int) -> LitterGroup:
        """
        Load a litter group.

        Args:
            db: Database session.
            litter_group_id: The litter.

        Returns:
            The group.

        Raises:
            HTTPException: 404 when it does not exist.
        """
        group = db.get(LitterGroup, litter_group_id)
        if group is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portée introuvable")
        return group

    @classmethod
    def matches_by_group(cls, db: Session, user_id: int) -> dict[int, ListingMatch]:
        """
        Matches of the user's first active profile, by group, for the other query services.

        Args:
            db: Database session.
            user_id: The user.

        Returns:
            Group id → match.
        """
        return cls._matches_by_group(db, user_id)

    @classmethod
    def build_card(cls, group: LitterGroup, match: ListingMatch | None, facts: LitterCardFacts) -> LitterCard | None:
        """
        The card of a group, for the other query services.

        Args:
            group: The litter.
            match: Its match for the active profile, if evaluated.
            facts: The facts already loaded for it.

        Returns:
            The card, or None for a group without listing.
        """
        return cls._card(group, match, facts)

    @staticmethod
    def _matches_by_group(db: Session, user_id: int) -> dict[int, ListingMatch]:
        """
        Matches of the user's first active profile, by group.

        Args:
            db: Database session.
            user_id: The user.

        Returns:
            Group id → match.
        """
        profile = (
            db.query(SearchProfile)
            .filter(SearchProfile.user_id == user_id, SearchProfile.is_active.is_(True))
            .order_by(SearchProfile.id)
            .first()
        )
        if profile is None:
            return {}
        return {
            match.litter_group_id: match
            for match in db.query(ListingMatch).filter(ListingMatch.profile_id == profile.id)
        }

    @staticmethod
    def _is_listed(match: ListingMatch | None, tier: MatchTier | None) -> bool:
        """
        Whether a group belongs to the home list: never an excluded one, only the asked tier when there is
        one, and an ignored one only when asked for.

        Args:
            match: The match of the group for the active profile, if evaluated.
            tier: The tier asked for, if any.

        Returns:
            True when the group is listed.
        """
        if match is not None and match.tier == MatchTier.EXCLUDED:
            return False
        if tier is not None:
            return match is not None and match.tier == tier
        return match is None or match.tier != MatchTier.IGNORED

    @staticmethod
    def _last_notes_by_follow_up(db: Session, follow_up_ids: list[int]) -> dict[int, FollowUpNote]:
        """
        The newest note of each follow-up, in one query.

        Args:
            db: Database session.
            follow_up_ids: The follow-ups.

        Returns:
            Follow-up id → its newest note, absent when it has none.
        """
        last_notes: dict[int, FollowUpNote] = {}
        notes = (
            db.query(FollowUpNote)
            .filter(FollowUpNote.follow_up_id.in_(follow_up_ids))
            .order_by(FollowUpNote.created_at.desc(), FollowUpNote.id.desc())
        )
        for note in notes:
            last_notes.setdefault(note.follow_up_id, note)
        return last_notes

    @classmethod
    def _card(cls, group: LitterGroup, match: ListingMatch | None, facts: LitterCardFacts) -> LitterCard | None:
        """
        Build the card of a group.

        Args:
            group: The litter.
            match: Its match for the active profile, if evaluated.
            facts: The listings, breeds, breeders, departments and follow-ups already loaded.

        Returns:
            The card, or None for a group without listing.
        """
        listings = facts.listings_by_group.get(group.id, [])
        breeder = facts.breeders_by_id.get(group.breeder_id) if group.breeder_id is not None else None
        department_code = LitterSnapshotBuilder.department_code_of(listings, breeder)
        snapshot = LitterSnapshotBuilder.build_from_listings(
            group,
            listings,
            breed=facts.breeds_by_id.get(group.breed_id),
            breeder=breeder,
            department=facts.departments_by_code.get(department_code) if department_code is not None else None,
            puppies=facts.puppies_by_group.get(group.id, []),
        )
        if snapshot is None:
            return None
        follow_up = facts.follow_ups_by_group.get(group.id)
        city = breeder.city if breeder is not None else None
        photo_url, photo_source = cls._photo_of(group, listings, facts)
        return LitterCard(
            id=group.id,
            name=snapshot.name,
            place=city or snapshot.department_name,
            town=city,
            department_code=snapshot.department_code,
            department_name=snapshot.department_name,
            breeder_latitude=breeder.latitude if breeder is not None else None,
            breeder_longitude=breeder.longitude if breeder is not None else None,
            kind=snapshot.kind,
            tier=match.tier if match is not None else None,
            score=match.score if match is not None else None,
            colors=[LitterColor(color=reading.color, confidence=reading.confidence) for reading in snapshot.colors],
            lof_status=snapshot.lof_status,
            male_count=snapshot.male_count,
            female_count=snapshot.female_count,
            has_confirmed_sexes=group.confirmed_male_count is not None,
            puppies_available=snapshot.puppies_available,
            price_cents=snapshot.price_cents,
            highest_price_cents=snapshot.highest_price_cents,
            birth_date=group.birth_date,
            expected_birth_date=group.expected_birth_date,
            available_from=group.available_from,
            photo_url=photo_url,
            photo_source=photo_source,
            first_seen_at=group.first_seen_at,
            latest_listing_appeared_at=max(listing.first_seen_at for listing in listings),
            last_seen_at=max(listing.last_seen_at for listing in listings),
            is_active=group.is_active,
            sources=list(dict.fromkeys(listing.source for listing in listings)),
            follow_up_status=follow_up.status if follow_up is not None else None,
            genetic_screening=GeneticScreeningReader.of_parents(
                snapshot.breed_slug, snapshot.sire_rating, snapshot.dam_rating
            ),
            gold_puppy_odds=snapshot.gold_puppy_odds,
        )

    @staticmethod
    def _photo_of(
        group: LitterGroup, listings: list[Listing], facts: LitterCardFacts
    ) -> tuple[str | None, LitterPhotoSource | None]:
        """
        The photo a litter shows: the first photo of its ads, else its mother, else its father, so that a litter
        without photo shows a dog of its own, whose coat tells something of the puppies, rather than the cover of
        its breeding.

        Args:
            group: The litter.
            listings: Its listings.
            facts: The facts loaded for it, with the photos of its parents.

        Returns:
            The photo and where it comes from, or two None.
        """
        listing_photo = next((photo for listing in listings for photo in listing.photos), None)
        if listing_photo is not None:
            return listing_photo, LitterPhotoSource.LISTING
        for dog_id, source in ((group.dam_dog_id, LitterPhotoSource.DAM), (group.sire_dog_id, LitterPhotoSource.SIRE)):
            parent_photo = facts.parent_photos_by_dog_id.get(dog_id) if dog_id is not None else None
            if parent_photo is not None:
                return parent_photo, source
        return None, None

    @staticmethod
    def _parent(
        listings: list[Listing],
        name_of: Callable[[Listing], str | None],
        rating_of: Callable[[Listing], int | None],
    ) -> LitterParent | None:
        """
        A parent of the litter, merged across its active listings in the order of the snapshot (Centrale
        Canine first): the first name a listing gives, with the first rating a listing gives.

        Args:
            listings: Every listing of the group, in id order.
            name_of: Reads the name of the parent on a listing.
            rating_of: Reads the rating of the parent on a listing.

        Returns:
            The parent, or None while no listing names it.
        """
        ordered_listings = LitterSnapshotBuilder.centrale_canine_first(
            LitterSnapshotBuilder.active_listings_of(listings)
        )
        name = next((name_of(listing) for listing in ordered_listings if name_of(listing)), None)
        if name is None:
            return None
        rating = next((rating_of(listing) for listing in ordered_listings if rating_of(listing) is not None), None)
        return LitterParent(name=name, rating=rating)

    @staticmethod
    def _parent_with_dog(
        parent: LitterParent | None, dog: Dog | None, site_photos_by_parent_id: dict[int, str]
    ) -> LitterParent | None:
        """
        A parent completed with its Centrale Canine page (colour, E locus, health tests, page) and with the first
        photo a breeder's site shows of it.

        Args:
            parent: The parent as the listings name it, if any.
            dog: Its dog row, once its page is read.
            site_photos_by_parent_id: First photo on a breeder's site, by parent dog id.

        Returns:
            The parent, from the dog alone when no listing names it.
        """
        if dog is None:
            return parent
        name = parent.name if parent is not None else (dog.full_name or dog.name or "")
        if not name:
            return parent
        color_facts = DogIngestionService.color_facts_of(dog)
        return LitterParent(
            name=name,
            rating=parent.rating if parent is not None and parent.rating is not None else dog.rating,
            color=color_facts.color if color_facts.color != CoatColor.INCONNUE else None,
            color_code=dog.color_code,
            e_locus=color_facts.e_locus,
            carries_gold_by_parents=color_facts.carries_gold_by_parents,
            health_codes=list(dog.health_codes),
            scc_url=dog.external_url,
            photo_url=site_photos_by_parent_id.get(dog.id),
        )

    @staticmethod
    def _photos_added_at(db: Session, listings: list[Listing]) -> datetime | None:
        """
        The last time new photos reached the litter: a listing seen first with photos, or new photos on one.

        Args:
            db: Database session.
            listings: Every listing of the group.

        Returns:
            The time, naive UTC, or None while no listing has a photo.
        """
        arrivals = [listing.first_seen_at for listing in listings if listing.photos]
        listing_ids = [listing.id for listing in listings]
        if listing_ids:
            last_photo_change = (
                db.query(func.max(ListingChange.changed_at))
                .filter(ListingChange.listing_id.in_(listing_ids), ListingChange.field == PHOTOS_FIELD)
                .scalar()
            )
            if last_photo_change is not None:
                arrivals.append(last_photo_change)
        return max(arrivals, default=None)

    @staticmethod
    def _breeder(breeder: Breeder, site_breed_slug: str | None) -> LitterBreeder:
        """
        The breeder payload.

        Args:
            breeder: The breeder.
            site_breed_slug: The breed of the litter in the addresses of the Chiens de France sites, None when unknown.

        Returns:
            What is known of it.
        """
        group = breeder.scc_selection_group
        return LitterBreeder(
            id=breeder.id,
            display_name=breeder.display_name,
            affix=breeder.affix,
            city=breeder.city,
            phone_e164=breeder.phone_e164,
            siren=breeder.siren,
            website=breed_page_of(breeder.website or breeder.chiens_de_france_site_url, site_breed_slug or ""),
            is_selected_breeding=group == SELECTED_BREEDING_GROUP,
            has_affix=(group in GROUPS_WITH_AFFIX) if group is not None else (True if breeder.affix else None),
            is_breed_club_member=breeder.is_breed_club_member is True,
        )

    @staticmethod
    def _follow_up_payload(db: Session, follow_up: FollowUp) -> LitterFollowUp:
        """
        The follow-up payload with its notes, newest first.

        Args:
            db: Database session.
            follow_up: The follow-up.

        Returns:
            The payload.
        """
        notes = (
            db.query(FollowUpNote)
            .filter(FollowUpNote.follow_up_id == follow_up.id)
            .order_by(FollowUpNote.created_at.desc(), FollowUpNote.id.desc())
            .all()
        )
        return LitterFollowUp(
            status=follow_up.status,
            next_reminder_at=follow_up.next_reminder_at,
            last_contact_at=follow_up.last_contact_at,
            notes=[FollowUpNoteResponse(id=note.id, created_at=note.created_at, text=note.text) for note in notes],
        )
