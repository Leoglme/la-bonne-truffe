"""Run all database seeders in order. Seeders are idempotent: existing rows are kept.

Run with:
    python seeders/run_seeders.py
"""

import sys
from pathlib import Path
from typing import Protocol

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from sqlalchemy.orm import Session

from core.database import SessionLocal, init_db
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


if __name__ == "__main__":
    init_db()
    session = SessionLocal()
    try:
        for seeder_name, created_count in SeederRunner.run(session).items():
            print(f"{seeder_name}: {created_count} created")
    finally:
        session.close()
