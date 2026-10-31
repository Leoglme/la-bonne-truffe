"""LitterShareService: the private link of a litter, and the page it opens without an account."""

import secrets
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.config import settings
from models.litter_share import LitterShare
from models.user import User
from schemas.litter import LitterDetail
from schemas.litter_share import LitterShareLink, SharedLitter
from services.litter_query_service import LitterQueryService

SHARE_LIFETIME = timedelta(days=30)
TOKEN_BYTES = 24
SHARE_PAGE_PATH = "/partage"


class LitterShareService:
    """Shares a litter by an unguessable link that opens without an account, for thirty days."""

    @staticmethod
    def create(db: Session, user: User, litter_group_id: int, message: str | None, now: datetime) -> LitterShareLink:
        """
        Create the link of a litter.

        Args:
            db: Database session.
            user: Who shares it.
            litter_group_id: The litter.
            message: Word for the people the link goes to; blank counts as none.
            now: Sharing time, naive UTC.

        Returns:
            The link and its expiry.

        Raises:
            HTTPException: 404 when the litter does not exist.
        """
        LitterQueryService.get_group(db, litter_group_id)
        share = LitterShare(
            token=secrets.token_urlsafe(TOKEN_BYTES),
            user_id=user.id,
            litter_group_id=litter_group_id,
            message=(message or "").strip() or None,
            created_at=now,
            expires_at=now + SHARE_LIFETIME,
        )
        db.add(share)
        db.commit()
        return LitterShareLink(
            url=f"{settings.web_base_url.rstrip('/')}{SHARE_PAGE_PATH}/{share.token}",
            expires_at=share.expires_at,
        )

    @staticmethod
    def read(db: Session, token: str, now: datetime) -> SharedLitter:
        """
        Read the page of a link: the litter as the sharer sees it, without their score, reasons nor follow-up.

        Args:
            db: Database session.
            token: Secret part of the link.
            now: Reading time, naive UTC.

        Returns:
            The page.

        Raises:
            HTTPException: 404 for an unknown link or a litter gone from the database, 410 once the link expired.
        """
        share = db.query(LitterShare).filter(LitterShare.token == token).one_or_none()
        if share is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ce lien n’existe pas ou a été retiré.")
        if share.expires_at <= now:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Ce lien a expiré.")
        sharer = db.get(User, share.user_id)
        detail: LitterDetail = LitterQueryService.detail(db, share.user_id, share.litter_group_id)
        return SharedLitter(
            sharer_name=sharer.name if sharer is not None else "",
            message=share.message,
            expires_at=share.expires_at,
            litter=detail.model_copy(
                update={
                    "tier": None,
                    "score": None,
                    "reasons": [],
                    "flags": [],
                    "follow_up_status": None,
                    "follow_up": None,
                }
            ),
        )
