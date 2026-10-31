"""Decides which litters have their Centrale Canine pages read this hour, and in what order (docs/05)."""

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from enums.dog_role import DogRole
from enums.listing_source import ListingSource
from enums.match_tier import MatchTier
from models.breeder_follow import BreederFollow
from models.dog import Dog
from models.follow_up import FollowUp
from models.listing import Listing
from models.listing_match import ListingMatch
from models.litter_group import LitterGroup
from services.collectors.scc_dogs import SccDogCollectionPlan, SccLitterTarget
from services.collectors.scc_value_parser import SccValueParser

PAGE_BUDGET = 60
PARENT_REFRESH_DAYS = 90
PUPPIES_FIRST_LOOK_DAYS = 21
PUPPIES_RETRY_DAYS = 7
PUPPIES_GIVE_UP_DAYS = 180

TIER_PRIORITIES: dict[MatchTier, int] = {
    MatchTier.PREFERRED: 1,
    MatchTier.ACCEPTABLE: 2,
    MatchTier.IGNORED: 3,
    MatchTier.EXCLUDED: 4,
}
FOLLOWED_PRIORITY = 0
UNRATED_PRIORITY = 3


class DogCollectionPlanner:
    """
    Picks the active litters of the Centrale Canine whose parents are not read yet (or read long ago), and
    those born three weeks ago or more whose puppies are not found yet: the followed ones first, then the
    preferred, then the acceptable, within a budget of pages.
    """

    @classmethod
    def build(cls, db: Session, now: datetime, page_budget: int = PAGE_BUDGET) -> SccDogCollectionPlan:
        """
        Plan the run of the hour.

        Args:
            db: Database session.
            now: Current time, naive UTC.
            page_budget: Pages the run may read.

        Returns:
            The plan, empty when every litter is up to date.
        """
        scc_listings = (
            db.query(Listing)
            .filter(
                Listing.source == ListingSource.CENTRALE_CANINE,
                Listing.is_active.is_(True),
                Listing.litter_group_id.is_not(None),
            )
            .order_by(Listing.id)
            .all()
        )
        scc_litter_ids_by_group: dict[int, str] = {}
        for listing in scc_listings:
            scc_litter_id = SccValueParser.to_text((listing.raw_json or {}).get("n_litter_id"))
            if listing.litter_group_id is not None and scc_litter_id is not None:
                scc_litter_ids_by_group.setdefault(listing.litter_group_id, scc_litter_id)
        if not scc_litter_ids_by_group:
            return SccDogCollectionPlan(litters=(), page_budget=page_budget)

        groups = (
            db.query(LitterGroup)
            .filter(LitterGroup.id.in_(scc_litter_ids_by_group), LitterGroup.is_active.is_(True))
            .all()
        )
        priorities = cls._priorities_by_group(db, [group.id for group in groups])
        dogs_by_id = cls._parent_dogs_by_id(db, groups)
        puppy_counts = cls._puppy_counts_by_group(db, [group.id for group in groups])
        today = now.date()

        targets: list[tuple[int, int, SccLitterTarget]] = []
        for group in groups:
            fresh_parent_ids = cls._fresh_parent_ids(group, dogs_by_id, now)
            read_parents = len(fresh_parent_ids) < 2
            read_puppies = cls._should_look_for_puppies(group, puppy_counts.get(group.id, 0), now, today)
            if not read_parents and not read_puppies:
                continue
            targets.append(
                (
                    priorities.get(group.id, UNRATED_PRIORITY),
                    group.id,
                    SccLitterTarget(
                        group_id=group.id,
                        scc_litter_id=scc_litter_ids_by_group[group.id],
                        read_parents=read_parents,
                        read_puppies=read_puppies,
                        fresh_dog_ids=fresh_parent_ids,
                    ),
                )
            )
        targets.sort(key=lambda item: (item[0], item[1]))
        return SccDogCollectionPlan(litters=tuple(target for _, _, target in targets), page_budget=page_budget)

    @staticmethod
    def _priorities_by_group(db: Session, group_ids: list[int]) -> dict[int, int]:
        """
        The priority of each group: followed litters and litters of followed breeders first, then by best tier.

        Args:
            db: Database session.
            group_ids: The groups.

        Returns:
            Group id → priority, the smallest first.
        """
        if not group_ids:
            return {}
        priorities: dict[int, int] = {}
        for match in db.query(ListingMatch).filter(ListingMatch.litter_group_id.in_(group_ids)):
            priority = TIER_PRIORITIES.get(match.tier, UNRATED_PRIORITY)
            priorities[match.litter_group_id] = min(priorities.get(match.litter_group_id, priority), priority)
        for (group_id,) in db.query(FollowUp.litter_group_id).filter(FollowUp.litter_group_id.in_(group_ids)):
            priorities[group_id] = FOLLOWED_PRIORITY
        followed_breeder_ids = {breeder_id for (breeder_id,) in db.query(BreederFollow.breeder_id)}
        if followed_breeder_ids:
            for group in db.query(LitterGroup).filter(
                LitterGroup.id.in_(group_ids), LitterGroup.breeder_id.in_(followed_breeder_ids)
            ):
                priorities[group.id] = FOLLOWED_PRIORITY
        return priorities

    @staticmethod
    def _parent_dogs_by_id(db: Session, groups: list[LitterGroup]) -> dict[int, Dog]:
        """
        The parent dogs the groups already point at.

        Args:
            db: Database session.
            groups: The groups.

        Returns:
            Dog id → dog.
        """
        dog_ids = {dog_id for group in groups for dog_id in (group.sire_dog_id, group.dam_dog_id) if dog_id is not None}
        if not dog_ids:
            return {}
        return {dog.id: dog for dog in db.query(Dog).filter(Dog.id.in_(dog_ids))}

    @staticmethod
    def _puppy_counts_by_group(db: Session, group_ids: list[int]) -> dict[int, int]:
        """
        How many registered puppies each group already has.

        Args:
            db: Database session.
            group_ids: The groups.

        Returns:
            Group id → puppies found.
        """
        counts: dict[int, int] = {}
        if not group_ids:
            return counts
        for (group_id,) in db.query(Dog.litter_group_id).filter(
            Dog.litter_group_id.in_(group_ids), Dog.role == DogRole.PUPPY
        ):
            if group_id is not None:
                counts[group_id] = counts.get(group_id, 0) + 1
        return counts

    @staticmethod
    def _fresh_parent_ids(group: LitterGroup, dogs_by_id: dict[int, Dog], now: datetime) -> frozenset[str]:
        """
        The Centrale Canine identifiers of the parents whose page was read recently enough.

        Args:
            group: The group.
            dogs_by_id: The parent dogs loaded.
            now: Current time, naive UTC.

        Returns:
            The identifiers to skip this run.
        """
        oldest_fresh_read = now - timedelta(days=PARENT_REFRESH_DAYS)
        fresh_ids: set[str] = set()
        for dog_id in (group.sire_dog_id, group.dam_dog_id):
            dog = dogs_by_id.get(dog_id) if dog_id is not None else None
            if dog is not None and dog.fetched_at is not None and dog.fetched_at >= oldest_fresh_read:
                fresh_ids.add(dog.external_id)
        return frozenset(fresh_ids)

    @staticmethod
    def _should_look_for_puppies(group: LitterGroup, puppies_found: int, now: datetime, today: date) -> bool:
        """
        Whether the registered puppies of a litter are worth looking for now: born three weeks ago or more,
        none found yet, the previous look old enough, and the litter not too old to still matter.

        Args:
            group: The group.
            puppies_found: Puppies already registered for it.
            now: Current time, naive UTC.
            today: Day of the run.

        Returns:
            True when the run reads the puppies.
        """
        if group.birth_date is None or puppies_found > 0:
            return False
        age_in_days = (today - group.birth_date).days
        if age_in_days < PUPPIES_FIRST_LOOK_DAYS or age_in_days > PUPPIES_GIVE_UP_DAYS:
            return False
        return group.puppies_detail_next_try_at is None or group.puppies_detail_next_try_at <= now
