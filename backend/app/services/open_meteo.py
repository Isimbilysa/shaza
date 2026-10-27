"""Client for the Open-Meteo archive API.

Open-Meteo serves ERA5 reanalysis from ECMWF. Two things about that matter enough to encode
rather than mention in a README:

1. It is a *reanalysis*, not a station reading -- hence Provenance.REANALYSIS everywhere here.
2. It answers on a grid of roughly 9-11 km. Ask for Musanze at (-1.4997, 29.6344) and the
   response comes back stamped (-1.5114, 29.6437): the centre of the cell it actually used.
   We keep the returned coordinates and put the distance in the caveat, because a value
   labelled "Musanze" that is really "the 11 km cell containing Musanze" is the kind of small
   silent inaccuracy that compounds once models are fitted on top of it.

Docs: https://open-meteo.com/en/docs/historical-weather-api
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

import httpx

from app.core.config import get_settings
from app.models.variable import Variable

logger = logging.getLogger(__name__)
settings = get_settings()

SOURCE_SLUG = "open-meteo-era5"


class OpenMeteoError(RuntimeError):
    """The upstream API failed or answered with something we cannot use."""


@dataclass(frozen=True)
class DailyRecord:
    variable: Variable
    observed_on: date
    value: float | None
    unit: str


@dataclass(frozen=True)
class ArchiveResponse:
    """A parsed archive response, with the grid cell it really describes."""

    grid_latitude: float
    grid_longitude: float
    elevation_m: float | None
    timezone: str
    records: list[DailyRecord]

    def caveat(self, requested_lat: float, requested_lon: float) -> str:
        offset_km = _haversine_km(
            requested_lat, requested_lon, self.grid_latitude, self.grid_longitude
        )
        return (
            "ERA5 reanalysis, not a station measurement. Values describe a ~9-11 km grid "
            f"cell centred {offset_km:.1f} km from the requested point "
            f"({self.grid_latitude:.4f}, {self.grid_longitude:.4f})."
        )


def fetch_archive(
    latitude: float,
    longitude: float,
    start: date,
    end: date,
    variables: list[Variable],
    *,
    client: httpx.Client | None = None,
) -> ArchiveResponse:
    """Fetch daily values for one point. Raises OpenMeteoError on any upstream problem."""
    if start > end:
        raise ValueError(f"start {start} is after end {end}")
    if not variables:
        raise ValueError("at least one variable is required")

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": ",".join(v.value for v in variables),
        "timezone": "auto",
    }

    owns_client = client is None
    client = client or httpx.Client(timeout=settings.http_timeout_seconds)
    try:
        response = client.get(settings.open_meteo_archive_url, params=params)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPStatusError as exc:
        # Open-Meteo puts the actual complaint in the body; surface it, it is usually precise.
        detail = exc.response.text[:300]
        raise OpenMeteoError(f"HTTP {exc.response.status_code}: {detail}") from exc
    except httpx.HTTPError as exc:
        raise OpenMeteoError(f"request failed: {exc}") from exc
    finally:
        if owns_client:
            client.close()

    return _parse(payload, variables)


def _parse(payload: dict, variables: list[Variable]) -> ArchiveResponse:
    daily = payload.get("daily")
    if not daily or "time" not in daily:
        raise OpenMeteoError("response contained no daily block")

    units = payload.get("daily_units", {})
    days = [date.fromisoformat(d) for d in daily["time"]]

    records: list[DailyRecord] = []
    for variable in variables:
        series = daily.get(variable.value)
        if series is None:
            logger.warning("source returned no series for %s", variable.value)
            continue
        if len(series) != len(days):
            raise OpenMeteoError(
                f"{variable.value}: {len(series)} values for {len(days)} days"
            )
        for day, raw in zip(days, series, strict=True):
            records.append(
                DailyRecord(
                    variable=variable,
                    observed_on=day,
                    # A null is a genuine gap in the archive. Store it as one; do not
                    # interpolate here, where the interpolation would become invisible.
                    value=None if raw is None else float(raw),
                    # Prefer our canonical unit over the source's "°C"/"%" glyphs.
                    unit=variable.unit or units.get(variable.value, ""),
                )
            )

    return ArchiveResponse(
        grid_latitude=float(payload["latitude"]),
        grid_longitude=float(payload["longitude"]),
        elevation_m=(
            float(payload["elevation"]) if payload.get("elevation") is not None else None
        ),
        timezone=payload.get("timezone", "UTC"),
        records=records,
    )


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import asin, cos, radians, sin, sqrt

    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    return 2 * r * asin(sqrt(a))
