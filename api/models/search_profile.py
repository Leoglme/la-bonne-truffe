"""SearchProfile model: the search criteria, editable in the app."""

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from enums.lof_preference import LofPreference
from enums.sex_preference import SexPreference
from models.timestamps import TimestampMixin


class SearchProfile(TimestampMixin, Base):
    """
    A set of criteria a litter is scored against. One profile is active for Léo, several are possible.

    Attributes:
        id: Primary key.
        user_id: Owner.
        name: Name shown in the app (« Cocker gold Bretagne »).
        is_active: Whether the matching runs this profile.
        breed_ids: Breed slugs searched.
        department_codes: Department codes, ordered from the closest to the farthest.
        include_expected_litters: Whether declared matings (litters to be born) are wanted.
        sex_preference: ``SexPreference`` value.
        lof_preference: ``LofPreference`` value.
        color_preferences: ``CoatColor`` → ``ColorPreferenceLevel``; a colour left out is ``ignored``.
        price_max_cents: Price ceiling, null for none.
        notify_preferred_immediately: Push a preferred litter right away.
        notify_acceptable_in_digest: Send the acceptable litters in the evening digest.
        digest_hour: Local hour of the evening digest.
        notify_birth_of_followed: Push the birth of a followed litter whatever its tier.
    """

    __tablename__ = "search_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    breed_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    department_codes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    include_expected_litters: Mapped[bool] = mapped_column(default=True, nullable=False)
    sex_preference: Mapped[str] = mapped_column(String(10), default=SexPreference.ANY.value, nullable=False)
    lof_preference: Mapped[str] = mapped_column(String(10), default=LofPreference.PREFERRED.value, nullable=False)
    color_preferences: Mapped[dict[str, str]] = mapped_column(JSON, default=dict, nullable=False)
    price_max_cents: Mapped[int | None]
    notify_preferred_immediately: Mapped[bool] = mapped_column(default=True, nullable=False)
    notify_acceptable_in_digest: Mapped[bool] = mapped_column(default=True, nullable=False)
    digest_hour: Mapped[int] = mapped_column(default=19, nullable=False)
    notify_birth_of_followed: Mapped[bool] = mapped_column(default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<SearchProfile id={self.id} name={self.name}>"
