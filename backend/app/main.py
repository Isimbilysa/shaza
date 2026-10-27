"""SHAZA API -- stage 1.

One job: serve environmental data that SHAZA retrieved, stored, and labelled honestly.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import health, locations, observations

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)-7s %(name)s: %(message)s"
)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=(
        "Environmental data for African agriculture, Rwanda first.\n\n"
        "**Every value carries its provenance.** SHAZA retrieves this data from external "
        "sources; it does not collect it. Historical weather is ERA5 reanalysis -- model "
        "output constrained by observations, not station measurements. Nothing here is "
        "farming advice."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(locations.router, prefix="/api/v1")
app.include_router(observations.router, prefix="/api/v1")


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "ok": True,
        "data": {
            "service": settings.app_name,
            "version": settings.version,
            "stage": "1 - foundation",
            "docs": "/docs",
        },
    }
