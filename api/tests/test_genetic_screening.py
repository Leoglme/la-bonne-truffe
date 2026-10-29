"""GeneticScreeningReader: the selection grid of the English cocker, read from the ratings of the parents."""

import pytest

from enums.genetic_screening import GeneticScreening
from services.genetic_screening import GeneticScreeningReader

COCKER = "cocker-spaniel-anglais"


@pytest.mark.parametrize(
    ("sire_rating", "dam_rating", "expected_screening"),
    [
        (4, 1, GeneticScreening.PUPPIES_UNAFFECTED),
        (None, 6, GeneticScreening.PUPPIES_UNAFFECTED),
        (2, 3, GeneticScreening.PARENTS_TESTED),
        (2, 1, None),
        (3, None, None),
        (1, 1, None),
        (None, None, None),
    ],
)
def test_the_ratings_of_the_parents_tell_what_the_grid_guarantees(
    sire_rating: int | None, dam_rating: int | None, expected_screening: GeneticScreening | None
) -> None:
    assert GeneticScreeningReader.of_parents(COCKER, sire_rating, dam_rating) == expected_screening


def test_the_grid_of_the_cocker_says_nothing_of_another_breed() -> None:
    assert GeneticScreeningReader.of_parents("cocker-americain", 6, 6) is None
