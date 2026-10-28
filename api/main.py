"""
FastAPI application entry point. The collection runs in a separate process: see ``worker.py``.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.router import router as api_router
from core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

app = FastAPI(
    title="La Bonne Truffe API",
    description="Portées de cocker spaniel anglais : collecte, correspondance et notifications.",
    version=settings.api_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.debug)
