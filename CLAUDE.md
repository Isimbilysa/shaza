# SHAZA — working rules

SHAZA is a multi-year agricultural intelligence project for Africa, Rwanda first. It is a
software engineering + data engineering + AI research project, not a website. The full charter
lives in `docs/charter.md`; this file is the short version that governs day-to-day work.

## Current phase

**No farmland yet.** This is the digital research phase, by choice:

> Build the digital laboratory before the physical laboratory.

Current stage: **Stage 1 — Foundation.** Done when one location's real external environmental
data flows source → database → API → dashboard, and the pipeline is documented.

## The nine stages, in order

1. Foundation — repo, FastAPI, PostgreSQL, Next.js, one endpoint, one dashboard
2. Data — external source, ingestion, validation, cleaning, storage, history
3. Visualization — charts, maps, filters, trends, location comparison
4. Synthetic Farm — simulated farms, weather, crop conditions, scenario generation
5. ML — baselines, evaluation, feature engineering, experiment tracking
6. Scenario Engine — modify rainfall / temperature / planting date / soil, see outcomes
7. AI — "Ask SHAZA", tool-based access to SHAZA's own data and models
8. Production Engineering — Docker, CI/CD, auth, RBAC, monitoring, tests, deploy
9. Real Farm — connect real observations, compare against simulation, close the loop

Do not build ahead of the current stage. If a request belongs to a later stage, say which
stage it is and offer the current-stage version instead.

## Data provenance — the one hard rule

Three environments, and the difference must be visible everywhere:

- **A — real external data**: weather/climate APIs, FAOSTAT, World Bank, NASA, NOAA,
  Copernicus, Rwanda open data, academic datasets
- **B — historical data**: for questions that can't be tested physically yet
- **C — synthetic data**: the Synthetic Farm Simulator, a controlled sandbox

Every record carries its source and maturity. Never present synthetic data as a real
experiment, external data as SHAZA-collected, or a prediction as a fact. Keep
observed / historical / modeled / simulated / predicted / assumed distinct all the way to the
UI, and carry uncertainty with any number that has it. Put the provenance field in the schema
before the data field, so the type system enforces it rather than a caption.

The existing landing site already does this: a required `Provenance`
(`illustrative | in-progress | verified`) on every record, surfaced by `StatusBadge`. Match it.

Correlation is not causation. The scenario engine is research simulation, not farming advice,
until it has been validated against real observations.

## Stack

Target: Python · FastAPI · Pydantic · SQLAlchemy · PostgreSQL · Next.js + TypeScript ·
Pandas / NumPy. ML progresses upward from statistics and linear regression; simple models
before complex ones.

> This repository is the platform: FastAPI in `backend/`, Next.js in `frontend/`, ingestion in
> `pipelines/`. The React/Vite + Express landing site lives outside it — see
> `docs/decisions/0001-platform-repository-layout.md`. The stage 1 pipeline is documented in
> `docs/pipeline.md`.

Every major technology must solve a problem that has actually appeared. No technology because
it is fashionable, and AI last rather than first.

## Experiments

Every meaningful experiment gets a record, failures included — a failure is a result:

```
Experiment / Date / Question / Hypothesis / Data / Method / Technology /
Result / What worked / What failed / What I learned / Next experiment
```

Exploratory work lives in `notebooks/` or `ml/experiments/` and does not have to graduate into
the product. Unrelated technology experiments belong in the separate `lysa-lab` repo, and
migrate in only once they prove useful.

## Automation

Scheduled work may fetch data, validate, test, and report — and commits **only when something
meaningful changed**. Never an empty commit to colour the contribution graph. Large datasets do
not go into git; document where the data came from instead.
