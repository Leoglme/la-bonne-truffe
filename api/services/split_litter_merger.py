"""
Joins the litter groups that are one litter although an earlier run kept them apart, and gives a group the
breeder its listings found since.

A listing is grouped once, when it first arrives (``LitterGroupingService``). What the sources say moves on
afterwards: a birth is declared, a rule learns to read the name of a mother, an ad finds its real breeder. Two
groups of a breeder are linked when every listing of one belongs to the other by a sure rule, never on a guess;
the groups linked one to the next are joined when nothing tells any two of them apart.
"""

import logging
from collections import defaultdict
from itertools import combinations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models.breeder_follow import BreederFollowEvent
from models.dog import Dog
from models.follow_up import FollowUp
from models.listing import Listing
from models.listing_match import ListingMatch
from models.litter_group import LitterGroup
from models.litter_share import LitterShare
from models.notification import Notification
from models.puppy_arrival import PuppyArrival
from services.litter_grouping import LitterGroupingService
from services.stored_value import known_or_current
from services.unused_breeder_remover import remove_breeder_left_with_nothing

logger = logging.getLogger(__name__)


class SplitLitterMerger:
    """Heals the groups an earlier run left apart, or under a breeder their listings have left."""

    def merge(self, db: Session) -> list[int]:
        """
        Give every group the breeder its listings agree on, then join the groups of a breeder that are one
        litter.

        Args:
            db: Database session; flushed, not committed.

        Returns:
            Ids of the groups removed, each joined to another.
        """
        listings_by_group_id = self._listings_by_group_id(db)
        groups = db.query(LitterGroup).order_by(LitterGroup.id).all()
        former_breeder_ids = self._give_each_group_the_breeder_of_its_listings(db, groups, listings_by_group_id)
        followed_group_ids = {group_id for (group_id,) in db.query(FollowUp.litter_group_id).distinct()}

        removed_group_ids: list[int] = []
        for group_ids_of_breeder in self._group_ids_by_breeder_and_breed(groups, listings_by_group_id):
            listings_by_group_id_of_breeder = {
                group_id: listings_by_group_id[group_id] for group_id in group_ids_of_breeder
            }
            for group_ids_of_one_litter in self._litters_in_several_groups(listings_by_group_id_of_breeder):
                removed_group_ids.extend(
                    self._join_into_one_group(db, group_ids_of_one_litter, followed_group_ids, listings_by_group_id)
                )

        db.flush()
        for former_breeder_id in former_breeder_ids:
            remove_breeder_left_with_nothing(db, former_breeder_id)
        return removed_group_ids

    @staticmethod
    def _listings_by_group_id(db: Session) -> dict[int, list[Listing]]:
        """
        Read every grouped listing.

        Args:
            db: Database session.

        Returns:
            The listings of each group, in id order.
        """
        listings_by_group_id: dict[int, list[Listing]] = defaultdict(list)
        for listing in db.query(Listing).filter(Listing.litter_group_id.is_not(None)).order_by(Listing.id):
            if listing.litter_group_id is not None:
                listings_by_group_id[listing.litter_group_id].append(listing)
        return listings_by_group_id

    @staticmethod
    def _breeder_id_of_listings(listings: list[Listing]) -> int | None:
        """
        The breeder the listings of a group agree on.

        Args:
            listings: The listings of a group.

        Returns:
            The breeder id, or None when they name none, or several.
        """
        breeder_ids = {listing.breeder_id for listing in listings}
        return breeder_ids.pop() if len(breeder_ids) == 1 else None

    @classmethod
    def _give_each_group_the_breeder_of_its_listings(
        cls, db: Session, groups: list[LitterGroup], listings_by_group_id: dict[int, list[Listing]]
    ) -> set[int]:
        """
        Hand a group, its puppies and its parents to the breeder its listings agree on, when it is not its own.

        Args:
            db: Database session.
            groups: Every group.
            listings_by_group_id: The listings of each group.

        Returns:
            The breeders a group left.
        """
        former_breeder_ids: set[int] = set()
        for group in groups:
            breeder_id = cls._breeder_id_of_listings(listings_by_group_id.get(group.id, []))
            former_breeder_id = group.breeder_id
            if breeder_id is None or breeder_id == former_breeder_id:
                continue
            group.breeder_id = breeder_id
            if former_breeder_id is None:
                continue
            former_breeder_ids.add(former_breeder_id)
            parent_dog_ids = [dog_id for dog_id in (group.sire_dog_id, group.dam_dog_id) if dog_id is not None]
            db.query(Dog).filter(
                Dog.breeder_id == former_breeder_id,
                or_(Dog.litter_group_id == group.id, Dog.id.in_(parent_dog_ids)),
            ).update({Dog.breeder_id: breeder_id}, synchronize_session=False)
        return former_breeder_ids

    @classmethod
    def _group_ids_by_breeder_and_breed(
        cls, groups: list[LitterGroup], listings_by_group_id: dict[int, list[Listing]]
    ) -> list[list[int]]:
        """
        Sort the groups whose listings agree on a breeder by that breeder and by breed.

        Args:
            groups: Every group.
            listings_by_group_id: The listings of each group.

        Returns:
            The group ids of each breeder, for one breed.
        """
        group_ids_by_breeder_and_breed: dict[tuple[int, int], list[int]] = defaultdict(list)
        for group in groups:
            breeder_id = cls._breeder_id_of_listings(listings_by_group_id.get(group.id, []))
            if breeder_id is not None:
                group_ids_by_breeder_and_breed[(breeder_id, group.breed_id)].append(group.id)
        return list(group_ids_by_breeder_and_breed.values())

    @classmethod
    def _litters_in_several_groups(cls, listings_by_group_id: dict[int, list[Listing]]) -> list[list[int]]:
        """
        Find, among the groups of a breeder, those that are one litter: two groups are linked when every listing
        of one belongs to the other by a sure rule, and the groups linked one to the next are one litter, unless
        two of them cannot be (two litters a source declares apart, with an ad that fits both).

        Args:
            listings_by_group_id: The listings of each group of the breeder, for one breed.

        Returns:
            The group ids of each litter held in two groups or more.
        """
        linked_group_ids: dict[int, set[int]] = {group_id: {group_id} for group_id in listings_by_group_id}
        for (first_group_id, first_listings), (second_group_id, second_listings) in combinations(
            listings_by_group_id.items(), 2
        ):
            if cls._are_told_apart(first_listings, second_listings):
                continue
            if cls._do_all_belong_to(first_listings, second_listings) or cls._do_all_belong_to(
                second_listings, first_listings
            ):
                joined_group_ids = linked_group_ids[first_group_id] | linked_group_ids[second_group_id]
                for group_id in joined_group_ids:
                    linked_group_ids[group_id] = joined_group_ids

        litters = {frozenset(group_ids) for group_ids in linked_group_ids.values() if len(group_ids) > 1}
        return [
            sorted(group_ids)
            for group_ids in sorted(litters, key=min)
            if not any(
                cls._are_told_apart(listings_by_group_id[first_group_id], listings_by_group_id[second_group_id])
                for first_group_id, second_group_id in combinations(group_ids, 2)
            )
        ]

    @staticmethod
    def _are_told_apart(first_listings: list[Listing], second_listings: list[Listing]) -> bool:
        """
        Whether a listing of one group and a listing of another cannot be the same litter.

        Args:
            first_listings: The listings of a group.
            second_listings: The listings of another group of the same breeder.

        Returns:
            True when the two groups are two litters.
        """
        return not all(
            LitterGroupingService.may_be_one_litter(first, second)
            for first in first_listings
            for second in second_listings
        )

    @staticmethod
    def _do_all_belong_to(listings: list[Listing], other_listings: list[Listing]) -> bool:
        """
        Whether a sure rule places every listing of a group in another group.

        Args:
            listings: The listings of a group.
            other_listings: The listings of another group of the same breeder.

        Returns:
            True when each listing would join the other group on arriving.
        """
        return all(
            LitterGroupingService.group_id_by_sure_rule(listing, other_listings) is not None for listing in listings
        )

    @classmethod
    def _join_into_one_group(
        cls,
        db: Session,
        group_ids_of_one_litter: list[int],
        followed_group_ids: set[int],
        listings_by_group_id: dict[int, list[Listing]],
    ) -> list[int]:
        """
        Join the groups of one litter into the one a user follows, else the oldest. A litter followed under two
        groups stays as it is, each group with its notes.

        Args:
            db: Database session.
            group_ids_of_one_litter: The groups that are one litter, in id order.
            followed_group_ids: The groups a user follows.
            listings_by_group_id: The listings of each group.

        Returns:
            Ids of the groups removed.
        """
        followed_ones = [group_id for group_id in group_ids_of_one_litter if group_id in followed_group_ids]
        if len(followed_ones) > 1:
            return []
        kept_group_id = followed_ones[0] if followed_ones else group_ids_of_one_litter[0]
        removed_group_ids = [group_id for group_id in group_ids_of_one_litter if group_id != kept_group_id]
        for removed_group_id in removed_group_ids:
            cls._move_into(db, listings_by_group_id[removed_group_id], removed_group_id, kept_group_id)
            logger.info("Litter group %s joined group %s: one litter", removed_group_id, kept_group_id)
        return removed_group_ids

    @staticmethod
    def _move_into(db: Session, moved_listings: list[Listing], removed_group_id: int, kept_group_id: int) -> None:
        """
        Move what a group holds into the group kept, then delete it: its listings, its puppies, its shared links,
        what was notified about it (so no event is sent twice), and what was confirmed by hand or read of its
        parents when the group kept knows less. Its pending digest lines go with it: a litter already known is
        no news.

        Args:
            db: Database session; flushed.
            moved_listings: Every listing of the group to remove.
            removed_group_id: The group to remove; no user follows it.
            kept_group_id: The group that stays.
        """
        kept_group = db.get(LitterGroup, kept_group_id)
        removed_group = db.get(LitterGroup, removed_group_id)
        if kept_group is None or removed_group is None:
            return
        for listing in moved_listings:
            listing.litter_group_id = kept_group_id
        for model in (Dog, Notification, PuppyArrival, BreederFollowEvent, LitterShare):
            db.query(model).filter(model.litter_group_id == removed_group_id).update(
                {model.litter_group_id: kept_group_id}, synchronize_session=False
            )

        kept_matches_by_profile_id = {
            match.profile_id: match
            for match in db.query(ListingMatch).filter(ListingMatch.litter_group_id == kept_group_id)
        }
        for removed_match in db.query(ListingMatch).filter(ListingMatch.litter_group_id == removed_group_id).all():
            kept_match = kept_matches_by_profile_id.get(removed_match.profile_id)
            if kept_match is None:
                removed_match.litter_group_id = kept_group_id
                kept_matches_by_profile_id[removed_match.profile_id] = removed_match
                continue
            kept_match.notified_events = {**removed_match.notified_events, **kept_match.notified_events}
            db.delete(removed_match)

        kept_group.confirmed_colors = kept_group.confirmed_colors or removed_group.confirmed_colors
        if kept_group.confirmed_male_count is None and kept_group.confirmed_female_count is None:
            kept_group.confirmed_male_count = removed_group.confirmed_male_count
            kept_group.confirmed_female_count = removed_group.confirmed_female_count
        kept_group.sire_dog_id = known_or_current(kept_group.sire_dog_id, removed_group.sire_dog_id)
        kept_group.dam_dog_id = known_or_current(kept_group.dam_dog_id, removed_group.dam_dog_id)
        kept_group.expected_colors = kept_group.expected_colors or removed_group.expected_colors
        db.flush()
        db.delete(removed_group)
        db.flush()


split_litter_merger = SplitLitterMerger()
