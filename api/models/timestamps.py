"""Creation and update timestamps shared by every table, stored as naive UTC."""

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from core.clock import naive_utc_now


class TimestampMixin:
    """Adds ``created_at`` and ``updated_at`` (naive UTC, refreshed on every update)."""

    created_at: Mapped[datetime] = mapped_column(default=naive_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=naive_utc_now, onupdate=naive_utc_now, nullable=False)
