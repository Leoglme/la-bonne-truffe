"""Run all database seeders in order (``cli.py init-db``). Seeders are idempotent: existing rows are kept."""

from typing import Protocol

from sqlalchemy.orm import Session

from seeders.breed_seeder import BreedSeeder
from seeders.department_seeder import DepartmentSeeder
from seeders.search_profile_seeder import SearchProfileSeeder
from seeders.user_seeder import UserSeeder


class Seeder(Protocol):
    """What every seeder exposes."""

    def run(self, db: Session) -> int:
        """Seed and return the number of rows created."""
        ...


# Order matters: references first, the user before the profile it owns.
SEEDERS: tuple[tuple[str, Seeder], ...] = (
    ("departments", DepartmentSeeder()),
    ("breeds", BreedSeeder()),
    ("user", UserSeeder()),
    ("search_profile", SearchProfileSeeder()),
)


class SeederRunner:
    """Runs every seeder in order on one session."""

    @staticmethod
    def run(db: Session) -> dict[str, int]:
        """
        Run the seeders.

        Args:
            db: Database session.

        Returns:
            Rows created, by seeder name.
        """
        return {name: seeder.run(db) for name, seeder in SEEDERS}
