# 0001 — Where the platform lives

*Status: accepted, retroactively. Written 2026-10-27 to record a layout the code already uses,
because `CLAUDE.md` still described the question as open.*

## Context

`CLAUDE.md` says this repository contains a React/Vite + Express landing site in `client/` and
`server/`, which predates the charter, and that where the FastAPI backend should live "is not yet
settled".

That is no longer what the repository contains. There is no `client/` or `server/` here. What
exists is a FastAPI backend in `backend/`, a Next.js dashboard in `frontend/`, and an ingestion
pipeline in `pipelines/`, all built against the charter's stack. The question was answered by
building, without being written down.

## Decision

This repository is the SHAZA platform.

```text
backend/     FastAPI, SQLAlchemy, Alembic. The API and everything it owns: models,
             schemas, ingestion services, migrations, backend tests.
frontend/    Next.js + TypeScript. The dashboard. Talks to the API over HTTP only.
pipelines/   Runnable entry points (fetch_weather.py). Thin: they import the backend's
             services rather than duplicating them.
docs/        Charter, architecture notes, decisions, the pipeline write-up.
ml/, notebooks/, simulations/, data/   Later stages; each has a README saying what belongs.
```

The landing site is not part of the platform and stays outside this repository.

## Why

- **One repository, two deployables.** The API and dashboard change together at this stage. A
  provenance field added to a schema needs a matching change in `frontend/lib/types.ts`, and one
  commit that does both is easier to review than two commits in two repositories.
- **The frontend does not import the backend.** The boundary is HTTP. Either half can be
  replaced, or deployed separately in stage 8, without untangling imports.
- **Pipelines reuse the backend's code.** `fetch_weather.py` puts `backend/` on `sys.path` and
  calls `ingest_location`. One definition of validation and upsert, whether it runs from a
  terminal, a schedule or a test.
- **The landing site is a different kind of thing.** It presents SHAZA; it does not run it.
  Mixing a marketing page into the platform's history makes the history harder to read as a
  record of research.

## Consequences

- `pipelines/` depends on the backend's internal layout. Moving `backend/app/services/` breaks
  the pipeline. Acceptable while there is one pipeline; if there are several, make the backend
  an installable package (`pip install -e backend`) and drop the `sys.path` line.
- The landing site's `Provenance` type (`illustrative | in-progress | verified`) is mirrored by
  `Maturity` in `backend/app/models/provenance.py`. With the two in different repositories,
  keeping them in step is manual.
- `CLAUDE.md` is updated to point here instead of describing the question as open.
