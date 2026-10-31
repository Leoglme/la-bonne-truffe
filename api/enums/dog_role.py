"""Why a dog is known: a parent of a litter, a reproducer shown by a breeder, or a puppy of a litter."""

from enum import StrEnum


class DogRole(StrEnum):
    """Why a dog is known: a parent of a litter, a reproducer shown by a breeder, or a puppy of a litter."""

    PARENT = "parent"
    REPRODUCER = "reproducer"
    PUPPY = "puppy"
