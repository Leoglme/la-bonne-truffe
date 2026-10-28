"""Reference data schemas: breeds and departments."""

from pydantic import BaseModel, ConfigDict


class BreedResponse(BaseModel):
    """A breed searchable by a profile."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name_fr: str
    slug: str
    is_active: bool


class DepartmentResponse(BaseModel):
    """A French department, grouped by region in the criteria screen."""

    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    region: str
