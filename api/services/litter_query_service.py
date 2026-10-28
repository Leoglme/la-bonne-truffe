"""Reads the litters for the dashboard: cards, detail, follow-ups. Every query is scoped to the user."""

from enum import StrEnum

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from enums.listing_kind import ListingKind
from enums.match_flag import MatchFlag
from enums.match_tier import MatchTier
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
from services.matching.snapshot_builder import LitterSnapshotBuilder

SELECTED_BREEDING_GROUP = 1
GROUPS_WITH_AFFIX = (1, 2)


class LitterSort(StrEnum):
    """Order of the home screen list."""

    SCORE = "score"
    FRESHNESS = "freshness"


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
        cards: list[LitterCard] = []
        for group in groups:
            match = matches_by_group.get(group.id)
            if match is not None and match.tier == MatchTier.EXCLUDED:
                continue
            if tier is not None and (match is None or match.tier != tier):
                continue
            if tier is None and match is not None and match.tier == MatchTier.IGNORED:
                continue
            card = cls._card(db, user_id, group, match)
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
        card = cls._card(db, user_id, group, match)
        if card is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portée introuvable")
        listings = db.query(Listing).filter(Listing.litter_group_id == group.id).order_by(Listing.id).all()
        main_listing = next((listing for listing in listings if listing.is_active), listings[0])
        department = db.get(Department, card.department_code) if card.department_code else None
        breeder = db.get(Breeder, group.breeder_id) if group.breeder_id is not None else None
        follow_up = cls._follow_up(db, user_id, group.id)
        photos = list(dict.fromkeys(photo for listing in listings for photo in listing.photos))

        return LitterDetail(
            **card.model_dump(),
            reasons=[LitterReason(text=str(reason["text"]), points=int(reason["points"])) for reason in match.reasons]
            if match is not None
            else [],
            flags=[MatchFlag(flag) for flag in match.flags] if match is not None else [],
            department_name=department.name if department is not None else None,
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
        matches_by_group = cls._matches_by_group(db, user_id)
        follow_ups = db.query(FollowUp).filter(FollowUp.user_id == user_id).all()
        cards: list[FollowUpCard] = []
        for follow_up in follow_ups:
            group = db.get(LitterGroup, follow_up.litter_group_id)
            card = cls._card(db, user_id, group, matches_by_group.get(follow_up.litter_group_id)) if group else None
            if card is None:
                continue
            last_note = (
                db.query(FollowUpNote)
                .filter(FollowUpNote.follow_up_id == follow_up.id)
                .order_by(FollowUpNote.created_at.desc(), FollowUpNote.id.desc())
                .first()
            )
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

    @classmethod
    def _card(cls, db: Session, user_id: int, group: LitterGroup, match: ListingMatch | None) -> LitterCard | None:
        """
        Build the card of a group.

        Args:
            db: Database session.
            user_id: The user.
            group: The litter.
            match: Its match for the active profile, if evaluated.

        Returns:
            The card, or None for a group without listing.
        """
        snapshot = LitterSnapshotBuilder.build(db, group)
        if snapshot is None:
            return None
        listings = db.query(Listing).filter(Listing.litter_group_id == group.id).order_by(Listing.id).all()
        breeder = db.get(Breeder, group.breeder_id) if group.breeder_id is not None else None
        follow_up = cls._follow_up(db, user_id, group.id)
        city = breeder.city if breeder is not None else None
        return LitterCard(
            id=group.id,
            name=cls._litter_name(breeder, listings),
            place=city or snapshot.department_name,
            department_code=snapshot.department_code,
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
        )

    @staticmethod
    def _litter_name(breeder: Breeder | None, listings: list[Listing]) -> str:
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
        )

    @staticmethod
    def _follow_up(db: Session, user_id: int, litter_group_id: int) -> FollowUp | None:
        """
        The user's follow-up of a litter.

        Args:
            db: Database session.
            user_id: The user.
            litter_group_id: The litter.

        Returns:
            The follow-up, if any.
        """
        return (
            db.query(FollowUp)
            .filter(FollowUp.user_id == user_id, FollowUp.litter_group_id == litter_group_id)
            .one_or_none()
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
