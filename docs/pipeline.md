# The stage 1 pipeline: source to dashboard

*Written 2026-10-27, describing the code as it stands. This is the "documented" half of the stage 1
gate in `CLAUDE.md`. If the code and this note disagree, the code is right and this note is a bug.*

---

## 1. What flows

```text
Open-Meteo archive API (ERA5)
        |  pipelines/fetch_weather.py
        v
fetch        app/services/open_meteo.py     one HTTP call per location, five daily variables
        v
validate     app/services/validation.py     plausibility + unit checks, gaps counted
        v
upsert       app/services/ingest.py         keyed on (location, source, variable, day)
        v
database     locations / sources / observations   SQLite locally, PostgreSQL target
        v
API          app/routers/*.py               /api/v1/health, /locations, /observations/{slug}
        v
dashboard    frontend/app/page.tsx          one location, one variable, provenance on the chart
```

Every arrow carries the provenance with it. There is no stage at which a number exists without
the claim it is making.

## 2. Source

**What it is.** The Open-Meteo historical weather API
(`https://archive-api.open-meteo.com/v1/archive`), which serves ECMWF ERA5 reanalysis.

**What it is not.** A station measurement. ERA5 is a physical model run against assimilated
observations from stations, satellites, balloons, ships and aircraft. It is excellent data, and
it is stored as `provenance = reanalysis`, never `observed`. `Provenance.is_measurement` is false
for it, and every surface downstream reads that flag.

**The grid cell.** The API answers for the grid cell containing the requested point, roughly
9-11 km across, and returns that cell's centre coordinates. Ask for Musanze at
(-1.4997, 29.6344) and the answer describes (-1.5114, 29.6437). The pipeline computes the offset
and writes it into the ingest caveat. In hilly terrain a cell averages over ridges and valleys, so
the value for "Kigali" is the cell's value, not any particular field's.

**Variables.** Five daily series, defined in `app/models/variable.py` with canonical units:

| Variable | Unit |
| --- | --- |
| `temperature_2m_mean` | degC |
| `temperature_2m_max` | degC |
| `temperature_2m_min` | degC |
| `precipitation_sum` | mm |
| `relative_humidity_2m_mean` | percent |

A variable is added when a pipeline fetches it, not in anticipation.

**Days.** The request uses `timezone=auto`, so a "day" is a local calendar day at the location,
not a UTC day.

**Lag.** ERA5 is published about five days behind real time. Asking for yesterday returns nulls
that look like gaps, so the pipeline stops its window six days short of today
(`ERA5_LAG_DAYS` in `pipelines/fetch_weather.py`).

**Licence.** CC BY 4.0 (Open-Meteo) and ECMWF's ERA5 terms. Attribution is a licence condition,
and it is stored on the `sources` row and returned with every series.

## 3. Locations

Six district centres, seeded by `app/services/seed.py` on every pipeline run (idempotent):
Kigali, Musanze, Huye, Rubavu, Nyagatare and Rwamagana. Between them they span the Kigali plateau,
the volcanic north, the wetter south, Lake Kivu's shore and the drier eastern lowlands.
Coordinates are district-seat approximations.

`elevation_m` is not typed in. It is filled once, on first ingest, from the elevation of the grid
cell the source used.

## 4. Validation

`app/services/validation.py` runs on every record before anything is written.

- **Plausible range.** Deliberately wide and global, not Rwandan: mean temperature -90 to 60 degC,
  precipitation 0 to 2000 mm, humidity 0 to 100 percent. The job is to catch a broken parse, a
  unit mix-up or a sentinel like -999, not to second-guess the climate.
- **Unit check.** A record whose unit is not the variable's canonical unit is rejected.
- **Nulls are kept.** A null from the archive is a genuine gap. It is stored as a null and counted,
  never interpolated here, where the interpolation would become invisible.

Rejected records are logged with the reason and not stored. The pipeline reports
`N accepted, N gaps, N rejected` per location.

## 5. Storage

Three tables, created by the single Alembic migration `fa8abdef3399`:

- `locations` — slug, name, country, admin1, coordinates, elevation.
- `sources` — one row per origin: kind, url, licence, attribution, notes. Open-Meteo is
  `open-meteo-era5`, kind `external_api`, created on first ingest.
- `observations` — one value, for one variable, at one location, on one day, from one source.

In `observations` the provenance columns are declared before the value columns, on purpose:

| Column | Stage 1 value |
| --- | --- |
| `provenance` | `reanalysis` |
| `maturity` | `in-progress` |
| `uncertainty` | null — ERA5 publishes spread, not through this endpoint. Null means "not quantified", never "none" |
| `variable`, `observed_on`, `value`, `unit` | the measurement itself |

**Re-runs do not duplicate.** A unique constraint on `(location_id, source_id, variable,
observed_on)` is the natural key, and ingestion upserts against it, updating value, unit and
provenance where the row exists. Overlapping windows converge. The upsert is written for both
PostgreSQL and SQLite and is sent in chunks of 500 rows, which keeps it under SQLite's limit of
32,766 bound parameters.

Enums are stored as strings (`native_enum=False`), so the schema is the same on both databases.

## 6. API

FastAPI, all routes under `/api/v1`. Interactive docs at `/docs`.

| Endpoint | Returns |
| --- | --- |
| `GET /health` | liveness, plus a real `SELECT 1`, and which engine is in use |
| `GET /locations` | all locations |
| `GET /locations/{slug}` | one location, 404 if unknown |
| `GET /observations/{slug}` | series for a location; `variable` (repeatable), `start`, `end` |

Every response is an envelope, `{"ok": ..., "data": ...}`.

**The observations endpoint cannot return a bare number.** Each series carries a provenance
block: the claim (`reanalysis`), its human label, `is_measurement`, maturity, the full source
reference including licence and attribution, and the source's caveat. There is no parameter to
turn it off.

Series are grouped by `(variable, provenance)`, so a forecast and a reanalysis of the same
variable are never merged into one line. The default window is the last 365 days; the maximum is
30 years.

## 7. Dashboard

`frontend/app/page.tsx`, Next.js, rendered on the server. One location (Kigali) and one variable
(mean temperature), as constants. The stage 1 gate is one location end to end; a picker is
stage 3.

- **Latest value, min, mean, max, count**, all with units.
- **The chart's line style follows the provenance block, not a hard-coded rule.** Modeled data is
  dashed and muted; only measured data may be solid green. The day a real gauge writes to this
  location, the same component draws it solid with no edit.
- **The claim is inside the plot frame** ("REANALYSIS · NOT MEASURED"), so it survives a
  screenshot that crops the caption.
- **Failure is not shown as emptiness.** If the API is unreachable the page says so instead of
  drawing an empty chart, because an empty chart would claim that no data exists. An API that
  answers with zero rows gets a different message.
- **No caching.** A stale read would look exactly like an ingestion bug.

The API base URL comes from `NEXT_PUBLIC_API_BASE` (default `http://localhost:8000/api/v1`).

## 8. Running it from nothing

From the repository root, in PowerShell:

```powershell
# backend
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env            # SQLite by default; see section 9 for Postgres
alembic upgrade head              # create the tables
cd ..

# ingest: seeds the six locations, fetches two years for each
python pipelines/fetch_weather.py --days 730

# API (leave running)
cd backend
uvicorn app.main:app --reload     # http://localhost:8000/docs

# dashboard, in a second terminal
cd frontend
npm install
copy .env.local.example .env.local
npm run dev                       # http://localhost:3000
```

The pipeline and Alembic both read `backend/.env` by absolute path, and a relative SQLite path is
anchored to `backend/`, so it does not matter which directory they are run from.

Pipeline options: `--location <slug>` (repeatable), `--start` / `--end` (YYYY-MM-DD, inclusive),
`--days N`. Exit code 0 means every location ingested, 1 means at least one failed upstream (the
others are still stored), 2 means bad arguments.

**Verified end to end** on both databases, 2026-10-27: SQLite and PostgreSQL (Neon) each hold
6 locations, 1 source and 21,930 observations, 2024-10-21 to 2026-10-21, and the dashboard renders
from either. The Postgres copy was fetched fresh from the source rather than copied from SQLite,
so matching totals are a real parity check.

## 9. Things that have gone wrong

Each of these happened once. Recorded so they cost minutes the second time instead of an hour.

**`No module named 'psycopg2'`.** The URL starts `postgresql://`. SQLAlchemy reads a bare
`postgresql://` as "use psycopg2", but this project installs psycopg 3. Use
`postgresql+psycopg://...`. Hosted providers such as Neon hand out the bare form, so this
recurs whenever a URL is pasted in.

**`relation "locations" does not exist`, while `/health` says the database is up.** The API is
connected to a database with no tables, usually a freshly pointed-at Postgres. Run
`alembic upgrade head`, then the pipeline. `/health` checks the connection, not the schema.

**`.env` has two `DATABASE_URL` lines.** The last one wins. Comment out the one not in use.

**`[WinError 10013]` on start.** Something already holds port 8000, often an API started earlier
in the background. `Get-NetTCPConnection -LocalPort 8000` shows the owning process. If that
process has a parent that restarts it, stop the parent.

## 10. Known limitations

Deliberate for stage 1, listed so they are not mistaken for finished:

- **Series grouping omits the source.** Correct with one source; wrong the day a second
  reanalysis source lands. Fix before adding one. See `docs/architecture/data-environments.md`
  section 6.
- **No environment filter.** Once the simulator writes to `observations`, synthetic series will
  appear in ordinary responses by default (correctly labelled, but present). Same section.
- **No uncertainty.** `uncertainty` is null for every row.
- **`/health` does not check the schema.** A database with no tables reports healthy.
- **Tests cover the three properties that matter, not the whole surface.** `backend/tests/`
  checks validation, idempotent ingestion and provenance (`python -m pytest` from `backend/`).
  They run on in-memory SQLite with the source stubbed, so they never touch the network or the
  database in `.env`, and they say nothing yet about Postgres-specific behaviour.
- **Two years of history.** Enough for a stage 1 chart, not a climatology. Deepening it is a
  `--start` flag.
