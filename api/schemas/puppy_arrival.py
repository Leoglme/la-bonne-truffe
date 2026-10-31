"""Puppy arrival schemas: the puppy found, the day it comes home, and the preparations ticked."""

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

MAX_CHECKLIST_ITEMS = 40
MAX_CHECKLIST_KEY_LENGTH = 60

ChecklistKey = Annotated[str, StringConstraints(min_length=1, max_length=MAX_CHECKLIST_KEY_LENGTH)]


class PuppyArrivalStart(BaseModel):
    """« C’est lui ! » : the litter of the puppy and the day it comes home."""

    litter_group_id: int
    arrival_on: date


class PuppyArrivalChecklist(BaseModel):
    """The preparations ticked, by the keys the web app gives them."""

    done_items: list[ChecklistKey] = Field(..., max_length=MAX_CHECKLIST_ITEMS)


class PuppyArrivalResponse(BaseModel):
    """The puppy found and where its arrival stands; the search is paused since then."""

    litter_group_id: int | None = Field(description="Null once the litter left the database")
    arrival_on: date
    done_items: list[str]
    paused_since: datetime
