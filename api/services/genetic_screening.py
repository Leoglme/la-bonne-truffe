"""
The APR and NF screening the parents of a litter went through, read from their Centrale Canine ratings with the
selection grid of the English cocker (Spaniel Club Français, validated by the Centrale Canine on 31/01/2024).
"""

from enums.genetic_screening import GeneticScreening
from seeders.breed_seeder import COCKER_SLUG

TESTED_PARENT_RATING = 2
UNAFFECTED_PARENT_RATING = 4


class GeneticScreeningReader:
    """Reads the ratings of the parents the way the selection grid of the breed defines them."""

    @staticmethod
    def of_parents(breed_slug: str, sire_rating: int | None, dam_rating: int | None) -> GeneticScreening | None:
        """
        What the ratings tell. From 2 points, a dog is tested for APR and NF, healthy or carrier; from 4 points it
        is healthy for both. Both diseases are recessive: with one healthy parent, no puppy can be affected.

        Args:
            breed_slug: Breed of the litter; the grid only holds for the English cocker.
            sire_rating: Rating of the father, 1 to 6, if known.
            dam_rating: Rating of the mother, 1 to 6, if known.

        Returns:
            The screening, or None when the ratings guarantee nothing or are unknown.
        """
        if breed_slug != COCKER_SLUG:
            return None
        known_ratings = [rating for rating in (sire_rating, dam_rating) if rating is not None]
        if any(rating >= UNAFFECTED_PARENT_RATING for rating in known_ratings):
            return GeneticScreening.PUPPIES_UNAFFECTED
        if len(known_ratings) == 2 and min(known_ratings) >= TESTED_PARENT_RATING:
            return GeneticScreening.PARENTS_TESTED
        return None
