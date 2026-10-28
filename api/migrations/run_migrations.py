"""Execute database migrations in order (DevLeadHunter style, SQLite flavour).

Each migration runs at most once: the module name is recorded in ``schema_migrations``.
Before applying tracked migrations, ``init_db()`` ensures all SQLAlchemy model tables exist.

Run with:
    python migrations/run_migrations.py
"""

import importlib
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from sqlalchemy import Engine, text

from core.database import engine, init_db

_SCHEMA_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
  name VARCHAR(255) NOT NULL PRIMARY KEY,
  applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

# Order matters for incremental upgrades on existing databases.
MIGRATION_MODULES: list[tuple[str, str]] = [
    ("create_initial_tables", "migrations.create_initial_tables"),
    ("add_litter_group_confirmed_colors", "migrations.add_litter_group_confirmed_colors"),
    ("add_digest_entries_table", "migrations.add_digest_entries_table"),
    (
        "add_breeder_coordinates_and_listing_publication",
        "migrations.add_breeder_coordinates_and_listing_publication",
    ),
]

_NON_MIGRATION_MODULES: set[str] = {"__init__", "run_migrations"}


class MigrationRunner:
    """Applies the registered migrations that the database has not recorded yet."""

    def __init__(self, database_engine: Engine) -> None:
        """
        Bind the runner to a database.

        Args:
            database_engine: Engine of the database to migrate.
        """
        self.engine = database_engine

    @staticmethod
    def assert_registry_is_exhaustive() -> None:
        """
        Fail loudly when a migration file exists but is not registered in ``MIGRATION_MODULES``.

        An unregistered migration would silently never run: ``init_db()`` creates missing tables
        but never alters an existing one.

        Raises:
            RuntimeError: When at least one migration module is missing from the registry.
        """
        on_disk = {
            path.stem
            for path in Path(__file__).resolve().parent.glob("*.py")
            if path.stem not in _NON_MIGRATION_MODULES
        }
        registered = {name for name, _ in MIGRATION_MODULES}
        unregistered = sorted(on_disk - registered)
        if unregistered:
            raise RuntimeError("Migration(s) not registered in MIGRATION_MODULES: " + ", ".join(unregistered))

    def is_applied(self, name: str) -> bool:
        """
        Tell whether a migration is already recorded.

        Args:
            name: Migration name.

        Returns:
            Whether ``schema_migrations`` holds it.
        """
        with self.engine.connect() as connection:
            row = connection.execute(text("SELECT 1 FROM schema_migrations WHERE name = :name"), {"name": name}).first()
        return row is not None

    def mark_applied(self, name: str) -> None:
        """
        Record a migration as applied.

        Args:
            name: Migration name.
        """
        with self.engine.begin() as connection:
            connection.execute(text("INSERT INTO schema_migrations (name) VALUES (:name)"), {"name": name})

    def run(self) -> list[str]:
        """
        Ensure the base schema, then apply every pending migration in order.

        Returns:
            Names of the migrations applied by this run.

        Raises:
            RuntimeError: When the registry is incomplete or a module has no ``run_migration()``.
        """
        self.assert_registry_is_exhaustive()
        with self.engine.begin() as connection:
            connection.execute(text(_SCHEMA_TABLE_DDL))
        init_db(self.engine)

        applied: list[str] = []
        for migration_name, module_name in MIGRATION_MODULES:
            if self.is_applied(migration_name):
                continue
            module = importlib.import_module(module_name)
            run_migration = getattr(module, "run_migration", None)
            if run_migration is None:
                raise RuntimeError(f"{module_name} must define run_migration()")
            run_migration(self.engine)
            self.mark_applied(migration_name)
            applied.append(migration_name)
        return applied


if __name__ == "__main__":
    applied_names = MigrationRunner(engine).run()
    print("Applied: " + ", ".join(applied_names) if applied_names else "Database already up to date.")
