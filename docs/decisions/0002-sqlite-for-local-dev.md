# 0002 — SQLite for local development, PostgreSQL as the target

*Status: accepted. Written 2026-10-27. Referenced from `backend/app/core/config.py` and
`backend/.env.example`, which cited this file before it existed.*

## Context

The charter names PostgreSQL. Running Postgres locally means either installing it or running it
in Docker, and `docs/roadmap.md` defers Docker to month 6 at the earliest. Stage 1 needed a
database the pipeline could write to on day one, on one laptop, with nothing else installed.

## Decision

`DATABASE_URL` defaults to `sqlite:///./shaza.db`. Every environment that has PostgreSQL uses it,
selected by setting `DATABASE_URL`. Nothing else in the code chooses between the two.

PostgreSQL URLs must name the psycopg 3 driver: `postgresql+psycopg://...`. A bare
`postgresql://` makes SQLAlchemy look for psycopg2, which is not installed.

## What makes this safe

SQLite and PostgreSQL disagree in ways that usually surface late. These choices keep them in step:

- **Enums are stored as strings** (`native_enum=False`), so there is no Postgres `ENUM` type that
  SQLite cannot represent, and adding a value is not a type migration.
- **The upsert is written for both dialects** in `app/services/ingest.py`, and raises on any other
  dialect rather than falling back to something untested.
- **Upserts are chunked to 500 rows.** A two-year fetch of five variables is 32,850 bound
  parameters, just over SQLite's limit of 32,766. Chunking keeps both databases well clear.
- **The SQLite path is anchored to `backend/`.** Alembic runs from `backend/` and the pipeline from
  the repository root. With a bare relative path they wrote to two different files, which looked
  exactly like "the migration did not work".
- **`check_same_thread=False`** is passed to SQLite only; Postgres rejects it.
- **`/health` reports the engine,** so it is always visible which database the API is reading.

## What it costs

- **Parity is assumed, not tested.** SQLite is loose about types and stores dates as text. Code
  can pass on SQLite and fail on Postgres. Until CI runs against Postgres, the only check is
  running the pipeline against Postgres by hand.
- **One writer at a time.** Fine for one developer and one pipeline. Not fine for a scheduled
  ingest running while the API serves.
- **Two databases can drift.** A local SQLite file and a hosted Postgres are separate stores. The
  dashboard shows whichever one `DATABASE_URL` names, and nothing warns that the other differs.

## When to revisit

Move local development to Postgres, and drop SQLite, at whichever comes first:

- CI is added (`docs/roadmap.md`, month 1 week 4). Tests should run on the database production
  uses.
- A scheduled ingest needs to write while the API reads.
- A feature needs something SQLite lacks: Postgres-specific indexes, PostGIS for the stage 3 map,
  or real concurrent writes.

First parity check, 2026-10-27: a hosted PostgreSQL (Neon) was migrated with `alembic upgrade
head` and loaded by a fresh pipeline run. It holds the same 21,930 observations as the SQLite
copy, and the API serves the dashboard from it. One run is not CI, so the cost above still stands.
