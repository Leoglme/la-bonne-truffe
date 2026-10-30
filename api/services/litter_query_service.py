"""Reads the litters for the dashboard: cards, detail, follow-ups. Every query is scoped to the user."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Self

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.listing_kind import ListingKind
from enums.match_flag import MatchFlag
from enums.match_tier import MatchTier
from models.breed import Breed
from models.breeder import Breeder
from models.department import Department
from models.follow_up import FollowUp, FollowUpNote
from models.listing import Listing
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
    LitterFollowUp,
    LitterParent,
    LitterReason,
    LitterSourceListing,
)
from services.genetic_screening import GeneticScreeningReader
from services.matching.snapshot_builder import LitterSnapshotBuilder

SELECTED_BREEDING_GROUP = 1
GROUPS_WITH_AFFIX = (1, 2)


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

    @classmethod
    def load(cls, db: Session, user_id: int, groups: list[LitterGroup]) -> Self:
        """
        Load the listings, breeds, breeders, departments and the user's follow-ups of some groups.

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
                LitterSnapshotBuilder.department_code_of(listings) for listings in facts.listings_by_group.values()
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
        return facts


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
        main_listing = next((listing for listing in listings if listing.is_active), listings[0])
        breeder = facts.breeders_by_id.get(group.breeder_id) if group.breeder_id is not None else None
        follow_up = facts.follow_ups_by_group.get(group.id)
        photos = list(dict.fromkeys(photo for listing in listings for photo in listing.photos))

        return LitterDetail(
            **card.model_dump(),
            reasons=[LitterReason(text=str(reason["text"]), points=int(reason["points"])) for reason in match.reasons]
            if match is not None
            else [],
            flags=[MatchFlag(flag) for flag in match.flags] if match is not None else [],
            litter_number=next((listing.litter_number for listing in listings if listing.litter_number), None),
            mating_date=group.mating_date,
            sire=LitterParent(name=main_listing.sire_name, rating=main_listing.sire_rating)
            if main_listing.sire_name
            else None,
            dam=LitterParent(name=main_listing.dam_name, rating=main_listing.dam_rating)
            if main_listing.dam_name
            else None,
            breeder=cls._breeder(breeder) if breeder is not None else None,
            photos=photos,
            listings=[
                LitterSourceListing(
                    source=listing.source,
                    kind=listing.kind,
                    external_url=listing.external_url,
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
                )
                for listing in listings
            ],
            follow_up=cls._follow_up_payload(db, follow_up) if follow_up is not None else None,
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
        department_code = LitterSnapshotBuilder.department_code_of(listings)
        snapshot = LitterSnapshotBuilder.build_from_listings(
            group,
            listings,
            breed=facts.breeds_by_id.get(group.breed_id),
            breeder=breeder,
            department=facts.departments_by_code.get(department_code) if department_code is not None else None,
        )
        if snapshot is None:
            return None
        follow_up = facts.follow_ups_by_group.get(group.id)
        city = breeder.city if breeder is not None else None
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
            birth_date=group.birth_date,
            expected_birth_date=group.expected_birth_date,
            available_from=group.available_from,
            photo_url=next((photo for listing in listings for photo in listing.photos), None),
            first_seen_at=group.first_seen_at,
            is_active=group.is_active,
            sources=list(dict.fromkeys(listing.source for listing in listings)),
            follow_up_status=follow_up.status if follow_up is not None else None,
            genetic_screening=GeneticScreeningReader.of_parents(
                snapshot.breed_slug, snapshot.sire_rating, snapshot.dam_rating
            ),
        )

    @staticmethod
    def _breeder(breeder: Breeder) -> LitterBreeder:
        """
        The breeder payload.

        Args:
            breeder: The breeder.

        Returns:
            What is known of it.
        """
        group = breeder.scc_selection_group
        return LitterBreeder(
            display_name=breeder.display_name,
            affix=breeder.affix,
            city=breeder.city,
            phone_e164=breeder.phone_e164,
            siren=breeder.siren,
            website=breeder.website,
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
