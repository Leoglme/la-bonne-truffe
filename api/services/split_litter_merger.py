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
        litter. The followed group is the one kept, else the oldest; a litter followed under two groups stays
        as it is, each group with its notes.

        Args:
            db: Database session; flushed, not committed.

        Returns:
            Ids of the groups removed, each joined to another.
        """
        listings_by_group_id: dict[int, list[Listing]] = defaultdict(list)
        for listing in db.query(Listing).filter(Listing.litter_group_id.is_not(None)).order_by(Listing.id):
            if listing.litter_group_id is not None:
                listings_by_group_id[listing.litter_group_id].append(listing)

        group_ids_by_breeder_and_breed: dict[tuple[int, int], list[int]] = defaultdict(list)
        former_breeder_ids: set[int] = set()
        for group in db.query(LitterGroup).order_by(LitterGroup.id).all():
            breeder_ids_of_listings = {listing.breeder_id for listing in listings_by_group_id.get(group.id, [])}
            if len(breeder_ids_of_listings) != 1:
                continue
            breeder_id = breeder_ids_of_listings.pop()
            if breeder_id is None:
                continue
            if group.breeder_id != breeder_id:
                if group.breeder_id is not None:
                    former_breeder_ids.add(group.breeder_id)
                self._give_breeder(db, group, breeder_id)
            group_ids_by_breeder_and_breed[(breeder_id, group.breed_id)].append(group.id)

        followed_group_ids = {group_id for (group_id,) in db.query(FollowUp.litter_group_id).distinct()}
        removed_group_ids: list[int] = []
        for group_ids in group_ids_by_breeder_and_breed.values():
            listings_by_group_id_of_breeder = {group_id: listings_by_group_id[group_id] for group_id in group_ids}
            for group_ids_of_one_litter in self._litters_in_several_groups(listings_by_group_id_of_breeder):
                followed_ones = [group_id for group_id in group_ids_of_one_litter if group_id in followed_group_ids]
                if len(followed_ones) > 1:
                    continue
                kept_group_id = followed_ones[0] if followed_ones else min(group_ids_of_one_litter)
                for removed_group_id in group_ids_of_one_litter:
                    if removed_group_id == kept_group_id:
                        continue
                    self._move_into(db, listings_by_group_id[removed_group_id], removed_group_id, kept_group_id)
                    removed_group_ids.append(removed_group_id)
                    logger.info("Litter group %s joined group %s: one litter", removed_group_id, kept_group_id)

        db.flush()
        for former_breeder_id in former_breeder_ids:
            remove_breeder_left_with_nothing(db, former_breeder_id)
        return removed_group_ids

    @staticmethod
    def _litters_in_several_groups(listings_by_group_id: dict[int, list[Listing]]) -> list[list[int]]:
        """
        Find, among the groups of a breeder, those that are one litter: two groups are linked when every listing
        of one belongs to the other by a sure rule, and the groups linked one to the next are one litter, unless
        two of them cannot be (two litters a source declares apart, with an ad that fits both).

        Args:
            listings_by_group_id: The listings of each group of the breeder, for one breed.

        Returns:
            The group ids of each litter held in two groups or more.
        """

        def are_told_apart(first_group_id: int, second_group_id: int) -> bool:
            """Whether a listing of one group and a listing of the other cannot be the same litter."""
            return not all(
                LitterGroupingService.may_be_one_litter(first, second)
                for first in listings_by_group_id[first_group_id]
                for second in listings_by_group_id[second_group_id]
            )

        def does_belong_to(group_id: int, other_group_id: int) -> bool:
            """Whether a sure rule places every listing of a group in the other group."""
            return all(
                LitterGroupingService.group_id_by_sure_rule(listing, listings_by_group_id[other_group_id]) is not None
                for listing in listings_by_group_id[group_id]
            )

        linked_group_ids: dict[int, set[int]] = {group_id: {group_id} for group_id in listings_by_group_id}
        for first_group_id, second_group_id in combinations(listings_by_group_id, 2):
            if are_told_apart(first_group_id, second_group_id):
                continue
            if does_belong_to(first_group_id, second_group_id) or does_belong_to(second_group_id, first_group_id):
                joined_group_ids = linked_group_ids[first_group_id] | linked_group_ids[second_group_id]
                for group_id in joined_group_ids:
                    linked_group_ids[group_id] = joined_group_ids

        litters = {frozenset(group_ids) for group_ids in linked_group_ids.values() if len(group_ids) > 1}
        return [
            sorted(group_ids)
            for group_ids in sorted(litters, key=min)
            if not any(are_told_apart(first, second) for first, second in combinations(group_ids, 2))
        ]

    @staticmethod
    def _give_breeder(db: Session, group: LitterGroup, breeder_id: int) -> None:
        """
        Hand a group, its puppies and its parents to the breeder its listings now name.

        Args:
            db: Database session.
            group: The group, still under its former breeder.
            breeder_id: The breeder of its listings.
        """
        former_breeder_id = group.breeder_id
        group.breeder_id = breeder_id
        if former_breeder_id is None:
            return
        parent_dog_ids = [dog_id for dog_id in (group.sire_dog_id, group.dam_dog_id) if dog_id is not None]
        db.query(Dog).filter(
            Dog.breeder_id == former_breeder_id,
            or_(Dog.litter_group_id == group.id, Dog.id.in_(parent_dog_ids)),
        ).update({Dog.breeder_id: breeder_id}, synchronize_session=False)

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
