"""Shared litter schemas: the link a user sends, and the page anyone opens with it."""

from datetime import datetime

from pydantic import BaseModel, Field

from schemas.litter import LitterDetail

MAX_SHARE_MESSAGE_LENGTH = 500


class LitterShareCreate(BaseModel):
    """What the share drawer sends: a word for the people the link goes to, if any."""

    message: str | None = Field(default=None, max_length=MAX_SHARE_MESSAGE_LENGTH)


class LitterShareLink(BaseModel):
    """The link to send."""

    url: str
    expires_at: datetime


class SharedLitter(BaseModel):
    """The page a shared link opens without an account: the litter, without what is personal to the sharer."""

    sharer_name: str
    message: str | None
    expires_at: datetime
    litter: LitterDetail = Field(description="No score, reasons, flags nor follow-up: they belong to the sharer")
