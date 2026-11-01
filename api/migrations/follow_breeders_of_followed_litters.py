"""Migration: follow the breeder of every litter already followed (docs/04, « Suivre une portée suit son élevage »).

Since 01/11/2026 a litter entering the follow-up follows its breeder too, with the alerts « Suivre cet élevage »
starts with; the litters followed before left their breeder unfollowed. A breeder already followed keeps its follow.

Runs once (recorded in ``schema_migrations``): a breeder unfollowed afterwards is not followed again.
"""

from sqlalchemy import Engine, text

_FOLLOW_BREEDERS_SQL = """
INSERT INTO breeder_follows (
  user_id, breeder_id, status, notify_new_mating, notify_birth, notify_new_photos, notify_ignored_colors,
  created_at, updated_at
)
SELECT DISTINCT follow_ups.user_id, litter_groups.breeder_id, 'to_contact', 1, 1, 1, 0,
  CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM follow_ups
JOIN litter_groups ON litter_groups.id = follow_ups.litter_group_id
WHERE litter_groups.breeder_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM breeder_follows
    WHERE breeder_follows.user_id = follow_ups.user_id AND breeder_follows.breeder_id = litter_groups.breeder_id
  )
"""


def run_migration(database_engine: Engine) -> None:
    """
    Follow the known breeder of each followed litter, once per user and breeder, unless it is followed already.

    Args:
        database_engine: Engine of the database to migrate.
    """
    with database_engine.begin() as connection:
        connection.execute(text(_FOLLOW_BREEDERS_SQL))
