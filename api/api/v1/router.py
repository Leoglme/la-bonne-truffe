"""Main API v1 router."""

from fastapi import APIRouter

from api.v1.routes import auth, health, notifications, profiles, references

router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(notifications.router)
router.include_router(references.router)
router.include_router(profiles.router)
