"""Reference data schemas: the French departments."""

from pydantic import BaseModel, ConfigDict


class DepartmentResponse(BaseModel):
    """A French department, grouped by region in the criteria screen."""

    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    region: str
