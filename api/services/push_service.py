"""
Web Push delivery — send PWA notifications to the user's browsers (VAPID).

Copied from DevLeadHunter and gathered in a class. Best-effort by design: ``notify`` never raises,
so a push failure can never break the run that triggered it. Stale endpoints (HTTP 404/410) are
pruned automatically.
"""

import asyncio
import base64
import json
import logging
from dataclasses import dataclass, field

from py_vapid import Vapid01
from pywebpush import WebPushException, webpush
from sqlalchemy.orm import Session

from core.config import settings
from core.database import SessionLocal
from models.push_subscription import PushSubscription

logger = logging.getLogger(__name__)


@dataclass
class PushResult:
    """Outcome of a push send — surfaced to the test endpoint to diagnose delivery failures."""

    delivered: int = 0
    failed: int = 0
    details: list[str] = field(default_factory=list)


class PushService:
    """Sends Web Push notifications to every browser a user subscribed."""

    @staticmethod
    def is_configured() -> bool:
        """Whether both VAPID keys are set (push is disabled otherwise)."""
        return bool(settings.vapid_public_key and settings.vapid_private_key_b64)

    @staticmethod
    def _vapid_private_pem() -> str | None:
        """
        Decode the PKCS8 PEM VAPID private key from its base64 environment value.

        Returns:
            The PEM, or None when the key is missing or not valid base64.
        """
        if not settings.vapid_private_key_b64:
            return None
        try:
            return base64.b64decode(settings.vapid_private_key_b64).decode("utf-8")
        except ValueError:
            logger.error("Invalid VAPID_PRIVATE_KEY_B64 — push disabled")
            return None

    def send(self, db: Session, user_id: int, title: str, body: str, url: str, tag: str | None = None) -> PushResult:
        """
        Send a Web Push notification to every subscription of a user (blocking).

        Args:
            db: Database session.
            user_id: Target user.
            title: Notification title.
            body: Notification body.
            url: In-app path to open on click.
            tag: Optional notification tag (collapses same-tag notifications).

        Returns:
            The delivery outcome (delivered / failed counts + per-failure detail).
        """
        result = PushResult()
        pem = self._vapid_private_pem()
        if not pem:
            result.details.append("VAPID not configured")
            return result

        subscriptions = db.query(PushSubscription).filter(PushSubscription.user_id == user_id).all()
        payload_fields: dict[str, str] = {"title": title, "body": body, "url": url}
        if tag:
            payload_fields["tag"] = tag
        payload = json.dumps(payload_fields)
        try:
            # pywebpush treats a *string* key as a raw base64url key and cannot parse a PEM:
            # load the PEM explicitly and pass the Vapid instance instead.
            vapid = Vapid01.from_pem(pem.encode("utf-8"))
        except Exception as error:
            result.failed = len(subscriptions)
            result.details.append(f"VAPID key load failed: {str(error)[:160]}")
            logger.error("VAPID key load failed: %s", error)
            return result

        stale_subscription_ids: list[int] = []
        for subscription in subscriptions:
            try:
                webpush(
                    subscription_info={
                        "endpoint": subscription.endpoint,
                        "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
                    },
                    data=payload,
                    vapid_private_key=vapid,
                    vapid_claims={"sub": settings.vapid_subject},
                    ttl=3600,
                )
                result.delivered += 1
            except WebPushException as error:
                status_code = getattr(error.response, "status_code", None)
                result.failed += 1
                result.details.append(f"HTTP {status_code}: {str(error)[:160]}")
                logger.warning("Push failed (user=%s status=%s): %s", user_id, status_code, error)
                if status_code in (404, 410):
                    stale_subscription_ids.append(subscription.id)
            except Exception as error:
                result.failed += 1
                result.details.append(str(error)[:160])
                logger.warning("Push error (user=%s): %s", user_id, error)

        if stale_subscription_ids:
            db.query(PushSubscription).filter(PushSubscription.id.in_(stale_subscription_ids)).delete(
                synchronize_session=False
            )
            db.commit()
        return result

    async def notify(self, user_id: int, title: str, body: str, url: str = "/", tag: str | None = None) -> None:
        """
        Deliver a push without blocking the event loop (own session in a worker thread). Never raises.

        Args:
            user_id: Target user.
            title: Notification title.
            body: Notification body.
            url: In-app path to open on click.
            tag: Optional notification tag.
        """
        if not self.is_configured():
            return

        def send_in_own_session() -> None:
            """Send with a session owned by the worker thread."""
            db = SessionLocal()
            try:
                self.send(db, user_id, title, body, url, tag)
            finally:
                db.close()

        try:
            await asyncio.to_thread(send_in_own_session)
        except Exception as error:
            logger.warning("Push notify failed (user=%s): %s", user_id, error)


push_service = PushService()
