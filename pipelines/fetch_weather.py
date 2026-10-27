"""SHAZA weather ingestion pipeline.

    python pipelines/fetch_weather.py --days 730
    python pipelines/fetch_weather.py --location musanze --start 2020-01-01 --end 2024-12-31

Fetch -> validate -> store, per charter section 15. Safe to re-run: the upsert is keyed on
(location, source, variable, day), so overlapping windows converge instead of duplicating.

Exit codes: 0 all locations ingested, 1 at least one failed, 2 bad arguments.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

# Run from the repo root without installing the backend as a package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Location  # noqa: E402
from app.services.ingest import ingest_location  # noqa: E402
from app.services.open_meteo import OpenMeteoError  # noqa: E402
from app.services.seed import seed_locations  # noqa: E402

logger = logging.getLogger("shaza.pipeline")

# ERA5 lags real time by about five days. Asking for yesterday returns nulls, which then look
# like data gaps rather than "not published yet" -- so stop the window short of the lag.
ERA5_LAG_DAYS = 6


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest daily weather into SHAZA.")
    parser.add_argument(
        "--location",
        action="append",
        dest="locations",
        help="Location slug. Repeat for several. Omit for all seeded locations.",
    )
    parser.add_argument("--start", type=date.fromisoformat, help="YYYY-MM-DD, inclusive.")
    parser.add_argument("--end", type=date.fromisoformat, help="YYYY-MM-DD, inclusive.")
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Window length ending at the latest published day. Ignored if --start given.",
    )
    parser.add_argument(
        "--create-tables",
        action="store_true",
        help="Create tables directly instead of via Alembic. For a throwaway local database.",
    )
    return parser.parse_args(argv)


def resolve_window(args: argparse.Namespace) -> tuple[date, date]:
    end = args.end or date.today() - timedelta(days=ERA5_LAG_DAYS)
    start = args.start or end - timedelta(days=args.days)
    if start > end:
        raise SystemExit(f"start {start} is after end {end}")
    return start, end


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s"
    )
    args = parse_args(argv)
    start, end = resolve_window(args)

    if args.create_tables:
        Base.metadata.create_all(engine)
        logger.info("tables created")

    failures = 0
    with SessionLocal() as db:
        locations = seed_locations(db)
        if args.locations:
            wanted = set(args.locations)
            locations = [loc for loc in locations if loc.slug in wanted]
            missing = wanted - {loc.slug for loc in locations}
            if missing:
                logger.error("unknown location(s): %s", ", ".join(sorted(missing)))
                return 2

        logger.info(
            "ingesting %d location(s), %s..%s", len(locations), start, end
        )

        for location in locations:
            try:
                result = ingest_location(db, location, start, end)
            except OpenMeteoError as exc:
                # One location failing upstream should not lose the others' data.
                logger.error("%s: source failed: %s", location.slug, exc)
                db.rollback()
                failures += 1
                continue

            logger.info(result.summary())
            if not result.report.ok:
                logger.warning(
                    "%s: %d record(s) rejected by validation",
                    location.slug,
                    len(result.report.rejected),
                )

    if failures:
        logger.error("%d location(s) failed", failures)
        return 1

    logger.info("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
