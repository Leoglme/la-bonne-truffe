"""Reads the breeders for the Éleveurs tab: list, search, detail. Every query is scoped to the user (docs/05)."""

from dataclasses import dataclass, field
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.text import without_accents
from enums.coat_color import CoatColor
from enums.color_confidence import ColorConfidence
from enums.dog_role import DogRole
from enums.listing_source import ListingSource
from enums.match_tier import MatchTier
from models.breeder import Breeder
from models.breeder_follow import BreederFollow, BreederFollowNote
from models.department import Department
from models.dog import Dog
from models.litter_group import LitterGroup
from models.search_profile import SearchProfile
from schemas.breeder import (
    BreederCard,
    BreederColorShare,
    BreederDetail,
    BreederDog,
    BreederFilter,
    BreederFollowNoteResponse,
    BreederFollowResponse,
    BreederLink,
    BreederSearchResults,
    BreederSort,
)
from schemas.litter import LitterCard
from services.breeder_search_text import BreederSearchText
from services.litter_query_service import LitterCardFacts, LitterQueryService, LitterSort

NAMELESS_BREEDER = "Éleveur sans nom"
SELECTED_BREEDING_GROUP = 1
SEARCH_LIMIT = 8
REPRODUCER_ROLES: tuple[DogRole, ...] = (DogRole.REPRODUCER, DogRole.PARENT)


@dataclass
class BreederFacts:
    """What the cards of some breeders are built from, loaded in one query per table."""

    litter_cards_by_breeder: dict[int, list[LitterCard]] = field(default_factory=dict)
    follows_by_breeder: dict[int, BreederFollow] = field(default_factory=dict)
    departments_by_code: dict[str, Department] = field(default_factory=dict)

    @classmethod
    def load(cls, db: Session, user_id: int, breeders: list[Breeder]) -> "BreederFacts":
        """
        Load the litters, the follows and the departments of some breeders.

        Args:
            db: Database session.
            user_id: The user.
            breeders: The breeders to build cards for.

        Returns:
            The facts, empty for no breeder.
        """
        facts = cls()
        if not breeders:
            return facts
        breeder_ids = [breeder.id for breeder in breeders]
        groups = db.query(LitterGroup).filter(LitterGroup.breeder_id.in_(breeder_ids)).order_by(LitterGroup.id).all()
        matches_by_group = LitterQueryService.matches_by_group(db, user_id)
        litter_facts = LitterCardFacts.load(db, user_id, groups)
        for group in groups:
            card = LitterQueryService.build_card(group, matches_by_group.get(group.id), litter_facts)
            if card is not None and group.breeder_id is not None:
                facts.litter_cards_by_breeder.setdefault(group.breeder_id, []).append(card)
        for cards in facts.litter_cards_by_breeder.values():
            cards.sort(key=cls._litter_order)
        facts.follows_by_breeder = {
            follow.breeder_id: follow
            for follow in db.query(BreederFollow).filter(
                BreederFollow.user_id == user_id, BreederFollow.breeder_id.in_(breeder_ids)
            )
        }
        department_codes = {breeder.department_code for breeder in breeders if breeder.department_code}
        if department_codes:
            facts.departments_by_code = {
                department.code: department
                for department in db.query(Department).filter(Department.code.in_(department_codes))
            }
        return facts

    @staticmethod
    def _litter_order(card: LitterCard) -> tuple[int, int, int]:
        """
        The current litters first, best score first, then the past ones, latest first.

        Args:
            card: A litter card.

        Returns:
            The sort key.
        """
        latest_day = card.birth_date or card.expected_birth_date or date.min
        return (0 if card.is_active else 1, -(card.score or 0) if card.is_active else 0, -latest_day.toordinal())


class BreederQueryService:
    """Builds the breeder payloads from the breeders, their litters, their dogs and the user's follows."""

    @classmethod
    def list_cards(
        cls, db: Session, user_id: int, breeder_filter: BreederFilter, sort: BreederSort
    ) -> list[BreederCard]:
        """
        The breeders of the Éleveurs tab: those of the profile's departments, the followed ones, those added by
        hand, and those with a litter in the app.

        Args:
            db: Database session.
            user_id: The user.
            breeder_filter: Which breeders to keep.
            sort: The most promising first, or by name.

        Returns:
            The cards.
        """
        breeders = cls._listed_breeders(db, user_id)
        facts = BreederFacts.load(db, user_id, breeders)
        cards = [cls._card(breeder, facts) for breeder in breeders]
        cards = [card for card in cards if cls._passes(card, breeder_filter)]
        if sort == BreederSort.NAME:
            return sorted(cards, key=lambda card: without_accents(card.name).lower())
        return sorted(cards, key=cls._promising_key)

    @classmethod
    def search(cls, db: Session, user_id: int, query: str, limit: int = SEARCH_LIMIT) -> BreederSearchResults:
        """
        The suggestions of the search: the breeders whose search text holds every word of the query, those
        holding the whole phrase first, then the litters whose name or place does.

        Args:
            db: Database session.
            user_id: The user.
            query: What the user typed.
            limit: Breeders and litters kept at most, each.

        Returns:
            The suggestions, empty for an empty query.
        """
        words = BreederSearchText.normalize(query).split()
        if not words:
            return BreederSearchResults(breeders=[], litters=[])
        matching_breeders = [
            breeder
            for breeder in cls._breeders_with_search_text(db)
            if BreederSearchText.matches(breeder.search_text, query)
        ]
        phrase_breeder_ids = {
            breeder.id for breeder in matching_breeders if BreederSearchText.holds_phrase(breeder.search_text, query)
        }
        facts = BreederFacts.load(db, user_id, matching_breeders)
        breeder_cards = sorted(
            (cls._card(breeder, facts) for breeder in matching_breeders),
            key=lambda card: (0 if card.id in phrase_breeder_ids else 1, cls._promising_key(card)),
        )
        litter_cards = [
            card
            for card in LitterQueryService.list_cards(db, user_id, None, None, True, LitterSort.SCORE)
            if cls._litter_matches(card, words)
        ]
        return BreederSearchResults(breeders=breeder_cards[:limit], litters=litter_cards[:limit])

    @classmethod
    def detail(cls, db: Session, user_id: int, breeder_id: int) -> BreederDetail:
        """
        Everything the breeder screen shows.

        Args:
            db: Database session.
            user_id: The user.
            breeder_id: The breeder.

        Returns:
            The detail.

        Raises:
            HTTPException: 404 when the breeder does not exist.
        """
        breeder = cls.get_breeder(db, breeder_id)
        facts = BreederFacts.load(db, user_id, [breeder])
        card = cls._card(breeder, facts)
        litters = facts.litter_cards_by_breeder.get(breeder.id, [])
        follow = facts.follows_by_breeder.get(breeder.id)
        reproducers = (
            db.query(Dog)
            .filter(Dog.breeder_id == breeder.id, Dog.role.in_(REPRODUCER_ROLES))
            .order_by(Dog.role, Dog.full_name, Dog.id)
            .all()
        )
        return BreederDetail(
            **card.model_dump(),
            phone_e164=breeder.phone_e164,
            siren=breeder.siren,
            website=breeder.website,
            chiens_de_france_site_url=breeder.chiens_de_france_site_url,
            facebook_url=breeder.facebook_url,
            instagram_url=breeder.instagram_url,
            youtube_url=breeder.youtube_url,
            scc_breeder_id=breeder.scc_breeder_id,
            links=[
                BreederLink(label=str(link.get("label", "")), url=str(link.get("url", ""))) for link in breeder.links
            ],
            notes=breeder.notes,
            chiens_de_france_registered_on=breeder.chiens_de_france_registered_on,
            scc_last_litter_at=breeder.scc_last_litter_at,
            scc_directory_seen_at=breeder.scc_directory_seen_at,
            litters=litters,
            color_shares=cls._color_shares(litters),
            reproducers=[cls._dog(dog) for dog in reproducers],
            photos=list(breeder.scc_site_photos),
            follow=cls._follow_payload(db, follow) if follow is not None else None,
        )

    @staticmethod
    def _breeders_with_search_text(db: Session) -> list[Breeder]:
        """
        Every breeder, its search text written when it is still missing: the breeders stored before the search
        existed get theirs the first time a search runs, without waiting for a run of their source.

        Args:
            db: Database session; committed when a text was written.

        Returns:
            The breeders, by id.
        """
        breeders: list[Breeder] = db.query(Breeder).order_by(Breeder.id).all()
        has_written_text = False
        for breeder in breeders:
            if breeder.search_text is None:
                breeder.search_text = BreederSearchText.build(breeder)
                has_written_text = True
        if has_written_text:
            db.commit()
        return breeders

    @staticmethod
    def get_breeder(db: Session, breeder_id: int) -> Breeder:
        """
        Load a breeder.

        Args:
            db: Database session.
            breeder_id: The breeder.

        Returns:
            The breeder.

        Raises:
            HTTPException: 404 when it does not exist.
        """
        breeder = db.get(Breeder, breeder_id)
        if breeder is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Éleveur introuvable")
        return breeder

    @staticmethod
    def _listed_breeders(db: Session, user_id: int) -> list[Breeder]:
        """
        The breeders worth listing for a user: in the departments of the active profile, followed, added by hand,
        or with a litter in the app.

        Args:
            db: Database session.
            user_id: The user.

        Returns:
            The breeders, by id.
        """
        profile = (
            db.query(SearchProfile)
            .filter(SearchProfile.user_id == user_id, SearchProfile.is_active.is_(True))
            .order_by(SearchProfile.id)
            .first()
        )
        department_codes = set(profile.department_codes) if profile is not None else set()
        followed_ids = {
            breeder_id for (breeder_id,) in db.query(BreederFollow.breeder_id).filter(BreederFollow.user_id == user_id)
        }
        breeder_ids_with_litter = {
            breeder_id
            for (breeder_id,) in db.query(LitterGroup.breeder_id).filter(LitterGroup.breeder_id.is_not(None))
            if breeder_id is not None
        }
        return [
            breeder
            for breeder in db.query(Breeder).order_by(Breeder.id)
            if breeder.department_code in department_codes
            or breeder.id in followed_ids
            or breeder.is_manual
            or breeder.id in breeder_ids_with_litter
        ]

    @classmethod
    def _card(cls, breeder: Breeder, facts: BreederFacts) -> BreederCard:
        """
        Build the card of a breeder.

        Args:
            breeder: The breeder.
            facts: The litters, follows and departments already loaded.

        Returns:
            The card.
        """
        litters = facts.litter_cards_by_breeder.get(breeder.id, [])
        follow = facts.follows_by_breeder.get(breeder.id)
        department = facts.departments_by_code.get(breeder.department_code) if breeder.department_code else None
        current_litter = next(
            (
                card
                for card in litters
                if card.is_active and card.puppies_available != 0 and card.tier != MatchTier.EXCLUDED
            ),
            next((card for card in litters if card.is_active and card.puppies_available != 0), None),
        )
        name = breeder.card_name or NAMELESS_BREEDER
        return BreederCard(
            id=breeder.id,
            name=name,
            person_name=breeder.display_name if breeder.affix and breeder.display_name != breeder.affix else None,
            affix=breeder.affix,
            city=breeder.city,
            zip_code=breeder.zip_code,
            department_code=breeder.department_code,
            department_name=department.name if department is not None else None,
            latitude=breeder.latitude,
            longitude=breeder.longitude,
            logo_url=breeder.logo_url,
            photo_url=breeder.cover_photo_url
            or breeder.scc_site_cover_url
            or next((card.photo_url for card in litters if card.photo_url), None),
            is_selected_breeding=breeder.scc_selection_group == SELECTED_BREEDING_GROUP
            or breeder.is_scc_selected is True,
            is_breed_club_member=breeder.is_breed_club_member is True,
            has_siren=breeder.siren is not None,
            has_chiens_de_france_site=breeder.chiens_de_france_site_url is not None,
            is_manual=breeder.is_manual,
            sources=cls._sources(breeder, litters),
            gold_litters_count=sum(1 for card in litters if cls._is_gold(card)),
            litters_count=len(litters),
            last_litter_date=cls._last_litter_date(breeder, litters),
            litters_last_year_count=breeder.litters_last_year_count,
            breeding_females_count=breeder.breeding_females_count,
            current_litter=current_litter,
            is_followed=follow is not None,
            follow_status=follow.status if follow is not None else None,
        )

    @staticmethod
    def _sources(breeder: Breeder, litters: list[LitterCard]) -> list[ListingSource]:
        """
        Where a breeder is listed: the Centrale Canine, its Chiens de France site, and the sources of its litters.

        Args:
            breeder: The breeder.
            litters: Its litter cards.

        Returns:
            The sources, each once, the Centrale Canine first.
        """
        sources: dict[ListingSource, None] = {}
        if breeder.scc_breeder_id or breeder.scc_user_id:
            sources[ListingSource.CENTRALE_CANINE] = None
        if breeder.chiens_de_france_site_url:
            sources[ListingSource.CHIENS_DE_FRANCE] = None
        for card in litters:
            for source in card.sources:
                sources.setdefault(source, None)
        return list(sources)

    @staticmethod
    def _is_gold(card: LitterCard) -> bool:
        """
        Whether a litter is known gold: a certain, confirmed or inferred gold reading.

        Args:
            card: A litter card.

        Returns:
            True for a gold litter.
        """
        return any(
            reading.color == CoatColor.GOLD and reading.confidence != ColorConfidence.AMBIGUOUS
            for reading in card.colors
        )

    @staticmethod
    def _last_litter_date(breeder: Breeder, litters: list[LitterCard]) -> date | None:
        """
        The latest litter known of a breeder: the latest birth, expected birth or mating of its litters, or the
        date the Centrale Canine directory gives when it is later.

        Args:
            breeder: The breeder.
            litters: Its litter cards.

        Returns:
            The date, or None when no litter is known.
        """
        days = [card.birth_date or card.expected_birth_date for card in litters]
        known_days = [day for day in days if day is not None]
        if breeder.scc_last_litter_at is not None:
            known_days.append(breeder.scc_last_litter_at.date())
        return max(known_days) if known_days else None

    @staticmethod
    def _passes(card: BreederCard, breeder_filter: BreederFilter) -> bool:
        """
        Whether a card belongs to a filtered list.

        Args:
            card: The card.
            breeder_filter: The filter.

        Returns:
            True when the card is listed.
        """
        if breeder_filter == BreederFilter.FOLLOWED:
            return card.is_followed
        if breeder_filter == BreederFilter.GOLD:
            return card.gold_litters_count > 0
        if breeder_filter == BreederFilter.CLUB:
            return card.is_breed_club_member
        if breeder_filter == BreederFilter.ACTIVE_LITTER:
            return card.current_litter is not None
        return True

    @staticmethod
    def _promising_key(card: BreederCard) -> tuple[int, int, int, int, int, str]:
        """
        The most promising first: a litter to talk about now, then the most gold litters, then the latest litter,
        then a selected breeding, then a club member, then the name.

        Args:
            card: The card.

        Returns:
            The sort key.
        """
        return (
            0 if card.current_litter is not None else 1,
            -card.gold_litters_count,
            -card.last_litter_date.toordinal() if card.last_litter_date is not None else 0,
            0 if card.is_selected_breeding else 1,
            0 if card.is_breed_club_member else 1,
            without_accents(card.name).lower(),
        )

    @staticmethod
    def _litter_matches(card: LitterCard, words: list[str]) -> bool:
        """
        Whether a litter answers a search: every word in its name, town or department.

        Args:
            card: The litter card.
            words: Normalized words of the query.

        Returns:
            True when the litter is suggested.
        """
        haystack = BreederSearchText.normalize(" ".join(filter(None, (card.name, card.town, card.department_name))))
        compact = haystack.replace(" ", "")
        return all(word in haystack or word in compact for word in words)

    @staticmethod
    def _color_shares(litters: list[LitterCard]) -> list[BreederColorShare]:
        """
        How many known litters were of each colour, the most frequent first.

        Args:
            litters: The litter cards of the breeder.

        Returns:
            The shares, ambiguous colours left out.
        """
        counts: dict[CoatColor, int] = {}
        for card in litters:
            for reading in card.colors:
                if reading.confidence != ColorConfidence.AMBIGUOUS and reading.color != CoatColor.INCONNUE:
                    counts[reading.color] = counts.get(reading.color, 0) + 1
        return [
            BreederColorShare(color=color, litters_count=count)
            for color, count in sorted(counts.items(), key=lambda item: (-item[1], item[0].value))
        ]

    @staticmethod
    def _dog(dog: Dog) -> BreederDog:
        """
        The payload of a reproducer or a parent.

        Args:
            dog: The dog.

        Returns:
            What the detail shows of it.
        """
        return BreederDog(
            id=dog.id,
            role=dog.role,
            name=dog.name,
            full_name=dog.full_name,
            sex=dog.sex,
            birth_date=dog.birth_date,
            color=dog.color,
            color_code=dog.color_code,
            rating=dog.rating,
            health_codes=list(dog.health_codes),
            e_locus=dog.e_locus,
            photos=list(dog.photos),
            external_url=dog.external_url,
            availability_text=dog.availability_text,
        )

    @staticmethod
    def _follow_payload(db: Session, follow: BreederFollow) -> BreederFollowResponse:
        """
        The follow payload with its notes, newest first.

        Args:
            db: Database session.
            follow: The follow.

        Returns:
            The payload.
        """
        notes = (
            db.query(BreederFollowNote)
            .filter(BreederFollowNote.follow_id == follow.id)
            .order_by(BreederFollowNote.created_at.desc(), BreederFollowNote.id.desc())
            .all()
        )
        return BreederFollowResponse(
            status=follow.status,
            notify_new_mating=follow.notify_new_mating,
            notify_birth=follow.notify_birth,
            notify_new_photos=follow.notify_new_photos,
            notify_ignored_colors=follow.notify_ignored_colors,
            next_reminder_at=follow.next_reminder_at,
            last_contact_at=follow.last_contact_at,
            notes=[BreederFollowNoteResponse(id=note.id, created_at=note.created_at, text=note.text) for note in notes],
        )
