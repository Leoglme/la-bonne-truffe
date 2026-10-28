"""Health check schema."""

from pydantic import BaseModel


class HealthStatus(BaseModel):
    """Health of the API and of its database, for uptime monitoring."""

    status: str
    version: str
    timestamp: str
    services: dict[str, str]
