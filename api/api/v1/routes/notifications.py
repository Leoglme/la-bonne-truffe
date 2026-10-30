"""
Notification routes — bell history, VAPID key, subscribe / unsubscribe, test push.
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from core.config import settings
from core.database import get_db
from models.notification import Notification
from models.push_subscription import PushSubscription
from models.user import User
from schemas.notification import (
    NotificationListResponse,
    PushSubscriptionCreate,
    PushSubscriptionDelete,
    TestNotificationResult,
    VapidKeyResponse,
)
from services.auth_service import get_current_user
from services.notification_query_service import notification_query_service
from services.push_service import push_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    limit: int = Query(default=20, ge=1, le=50),
    before: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationListResponse:
    """
    Return a page of the notification history, newest first, with its litters and the unread count.

    Args:
        limit: Page size.
        before: Return the notifications whose id is strictly below this one (« voir plus »).
        current_user: The authenticated user.
        db: Database session.

    Returns:
        The page and the unread count.
    """
    return notification_query_service.list_history(db, current_user.id, limit, before)


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Mark every unread notification of the user as read (the bell was opened).

    Args:
        current_user: The authenticated user.
        db: Database session.
    """
    db.query(Notification).filter(Notification.user_id == current_user.id, Notification.read_at.is_(None)).update(
        {Notification.read_at: naive_utc_now()}
    )
    db.commit()


@router.get("/vapid-key", response_model=VapidKeyResponse)
async def get_vapid_key(current_user: User = Depends(get_current_user)) -> VapidKeyResponse:
    """
    Return the public VAPID key so the PWA can subscribe.

    Args:
        current_user: The authenticated user.

    Returns:
        The public key and whether push is configured server-side.
    """
    return VapidKeyResponse(public_key=settings.vapid_public_key, configured=push_service.is_configured())


@router.post("/subscribe", status_code=status.HTTP_204_NO_CONTENT)
async def subscribe(
    payload: PushSubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Register (or refresh) a browser push subscription for the user.

    Args:
        payload: The browser PushSubscription.
        current_user: The authenticated user.
        db: Database session.
    """
    existing = db.query(PushSubscription).filter(PushSubscription.endpoint == payload.endpoint).first()
    if existing is not None:
        existing.user_id = current_user.id
        existing.p256dh = payload.keys.p256dh
        existing.auth = payload.keys.auth
        existing.user_agent = payload.user_agent
    else:
        db.add(
            PushSubscription(
                user_id=current_user.id,
                endpoint=payload.endpoint,
                p256dh=payload.keys.p256dh,
                auth=payload.keys.auth,
                user_agent=payload.user_agent,
            )
        )
    db.commit()


@router.delete("/subscribe", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe(
    payload: PushSubscriptionDelete,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Remove a browser push subscription of the user.

    Args:
        payload: The endpoint to unregister.
        current_user: The authenticated user.
        db: Database session.
    """
    db.query(PushSubscription).filter(
        PushSubscription.endpoint == payload.endpoint,
        PushSubscription.user_id == current_user.id,
    ).delete(synchronize_session=False)
    db.commit()


@router.post("/test", response_model=TestNotificationResult)
async def send_test_notification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TestNotificationResult:
    """
    Send a test notification now and report the delivery outcome.

    A non-zero ``failed`` with the push service's HTTP status pinpoints the break: a 403/400 is a
    VAPID problem on the server, while ``delivered`` with nothing on the phone points at an iOS
    setting (app not added to the home screen).

    Args:
        current_user: The authenticated user.
        db: Database session.

    Returns:
        Configuration flag, subscription count, delivered/failed counts and any failure detail.
    """
    subscription_count = db.query(PushSubscription).filter(PushSubscription.user_id == current_user.id).count()
    result = push_service.send(
        db,
        current_user.id,
        "La Bonne Truffe",
        "Notification de test : la truffe est à l'affût.",
        "/reglages/notifications",
    )
    return TestNotificationResult(
        configured=push_service.is_configured(),
        subscriptions=subscription_count,
        delivered=result.delivered,
        failed=result.failed,
        detail="; ".join(result.details)[:300] or None,
    )
