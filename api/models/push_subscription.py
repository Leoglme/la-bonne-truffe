"""
PushSubscription model — a browser Web Push endpoint registered for a user.

One row per browser / PWA install (the iPhone and iPad home-screen apps). Registered via the
/notifications API, pruned automatically when the push service answers 404 or 410.
"""

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from models.timestamps import TimestampMixin


class PushSubscription(TimestampMixin, Base):
    """
    A browser Web Push subscription used to notify the user on their home-screen app.

    Attributes:
        id: Primary key.
        user_id: Owner of the subscription.
        endpoint: Push service endpoint URL (unique per browser install).
        p256dh: Client public key for payload encryption.
        auth: Client auth secret for payload encryption.
        user_agent: Device hint shown in the settings screen.
    """

    __tablename__ = "push_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    p256dh: Mapped[str] = mapped_column(String(255), nullable=False)
    auth: Mapped[str] = mapped_column(String(255), nullable=False)
    user_agent: Mapped[str] = mapped_column(Text, default="", nullable=False)

    def __repr__(self) -> str:
        return f"<PushSubscription id={self.id} user_id={self.user_id}>"
