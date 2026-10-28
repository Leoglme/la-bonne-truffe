"""User model: the single account that signs in to the dashboard."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from models.timestamps import TimestampMixin


class User(TimestampMixin, Base):
    """
    The dashboard account. La Bonne Truffe has one user, but every owned row still carries ``user_id``.

    Attributes:
        id: Primary key.
        name: First name shown in the greeting (« Bonjour Léo »).
        email: Login email, unique.
        hashed_password: bcrypt hash.
        is_active: Whether the account may sign in.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
