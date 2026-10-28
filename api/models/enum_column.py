"""Column type storing a ``StrEnum`` as its value, read back as the enum member."""

from enum import StrEnum

from sqlalchemy import Enum


def str_enum_column(enum_class: type[StrEnum]) -> Enum:
    """
    Build the SQLAlchemy type of a column holding one member of ``enum_class``.

    The value (``"litter_born"``) is stored in a plain VARCHAR, never the member name, and SQLite
    gets no native enum: adding a member later needs no migration.

    Args:
        enum_class: The enum the column holds.

    Returns:
        The column type.
    """
    return Enum(
        enum_class,
        native_enum=False,
        create_constraint=False,
        length=40,
        validate_strings=True,
        values_callable=lambda members: [member.value for member in members],
    )
