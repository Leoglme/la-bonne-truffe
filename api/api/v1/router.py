"""Main API v1 router."""

from fastapi import APIRouter

from api.v1.routes import (
    auth,
    health,
    litters,
    notifications,
    profiles,
    puppy_arrival,
    references,
    shares,
    sources,
)

router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(notifications.router)
router.include_router(references.router)
router.include_router(profiles.router)
router.include_router(litters.router)
router.include_router(shares.router)
router.include_router(puppy_arrival.router)
router.include_router(sources.router)
