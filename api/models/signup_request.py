"""SignupRequest model: someone who tried to sign up while signups are closed."""

from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.clock import naive_utc_now
from core.database import Base


class SignupRequest(Base):
    """
    A signup attempt kept while signups are closed (``SIGNUP_ENABLED``), one per address, to measure the interest.

    Attributes:
        id: Primary key.
        name: First name typed on the signup screen, the latest one.
        email: Address typed on the signup screen, in lowercase.
        requested_at: First attempt.
        last_requested_at: Latest attempt.
    """

    __tablename__ = "signup_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    requested_at: Mapped[datetime] = mapped_column(default=naive_utc_now, nullable=False)
    last_requested_at: Mapped[datetime] = mapped_column(default=naive_utc_now, nullable=False)

    def __repr__(self) -> str:
        return f"<SignupRequest id={self.id} email={self.email}>"
