"""Health check route."""

import logging

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.clock import naive_utc_now
from core.config import settings
from core.database import get_db
from schemas.health import HealthStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthStatus)
async def health_check(response: Response, db: Session = Depends(get_db)) -> HealthStatus:
    """
    Report the real health of the API and its database.

    The database is probed with ``SELECT 1``; when it fails the endpoint returns HTTP 503 so an
    uptime monitor detects the outage.

    Args:
        response: Injected so the status code can flip to 503 on a database failure.
        db: Database session used for the probe.

    Returns:
        Per-service statuses and an overall status.
    """
    services: dict[str, str] = {"api": "healthy"}
    overall_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
        services["database"] = "healthy"
    except Exception as error:
        logger.warning("Health check database probe failed: %s", error)
        services["database"] = "unhealthy"
        overall_status = "unhealthy"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthStatus(
        status=overall_status,
        version=settings.api_version,
        timestamp=naive_utc_now().isoformat(),
        services=services,
    )
