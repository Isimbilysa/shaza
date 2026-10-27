# Using SHAZA to learn, without faking the need

*Companion to charter sections 8, 13 and rule 7. A technology is unlocked by a problem that has
actually appeared, not by a date on a roadmap. This note lists, for each technology on the
learning list, the specific SHAZA problem that earns it.*

---

## 1. The rule, made operational

Charter rule 7 says every major technology should solve a problem. The failure mode is subtle:
it is easy to manufacture a problem in order to justify a technology you wanted anyway. Redis
because the roadmap says Redis, then an artificial cache in front of a query that runs in two
milliseconds.

So each entry below names a **trigger**: an observable condition in SHAZA, not a feeling. If the
trigger has not fired, the technology is not needed yet, and that is a finding rather than a
delay.

## 2. Already earned

In the repository and solving something real today: Python, FastAPI, Pydantic, SQLAlchemy, REST,
Alembic migrations, constraints and indexes, logging.

Two of these are worth noticing because the problem that justified them is visible in the code.
The unique constraint on `(location_id, source_id, variable, observed_on)` exists because the
pipeline reruns over overlapping windows and must converge rather than duplicate. The composite
index on `(location_id, variable, observed_on)` exists because that is the query the dashboard
makes. Neither was added because indexes are good practice. That is the pattern to keep.

## 3. Triggered now, unsolved

Four problems exist in the repository today.

**Testing. The trigger has fired loudly.** `backend/tests/` contains an empty `__init__.py` and
nothing else. Pytest and ruff are already in `requirements-dev.txt`. Meanwhile 21,930 rows have
been ingested and the data-environments note defines query rules that are conventions right now.
A convention is a thing a tired person forgets; a failing test is not. First tests, in order:
validation boundaries, upsert idempotence on a rerun, and the rule that a default query excludes
synthetic sources.

**GitHub Actions.** `.github/` is empty. Charter section 15 and 16 describe a scheduled pipeline
that fetches, validates, tests and commits only when something meaningful changed. The ingestion
script already returns meaningful exit codes and the upsert already makes "nothing changed"
detectable. The workflow is the missing piece, and it is the most honest possible introduction to
CI/CD because the job is real work rather than a demonstration.

**Next.js, TypeScript, charts.** Stage 1 does not close without a dashboard, and the frontend has
no app directory at all. The first chart has a real design problem attached: rendering a series
whose provenance block says reanalysis, in a way a viewer cannot mistake for a measurement.

**NumPy and Pandas.** Triggered by the Layer 2 indices in the scenario-engine note. Growing
degree days and consecutive dry days over a daily series is exactly the shape Pandas exists for.

## 4. Waiting for a named trigger

| Technology | The trigger | Likely stage |
| --- | --- | --- |
| PostgreSQL | deployment, or concurrent scheduled writes against API reads | 2 to 8 |
| PostGIS | a question about distance, containment or rasters, not six lat/lon pairs | 3+ |
| async httpx | ingestion wall time once history deepens and sources multiply | 2 |
| Background jobs | an ingestion run too long for a request or an Actions timeout | 2 to 6 |
| Queues | a scenario run too slow to answer inside an HTTP request | 6 |
| Redis | a repeated expensive deterministic computation, scenario results first | 6 |
| Object storage | the first satellite raster, which does not belong in Postgres | 6+ |
| Auth and RBAC | a second user, or any write path exposed to a browser | 8 |
| Docker | a second machine needing to run this, or Postgres locally without pain | 8 |
| Monitoring | something running unattended that can fail silently | 8 |
| Vector database | text to search semantically, see section 7 | 7 |
| LLM tool calling | Ask SHAZA over the existing endpoints | 7 |

Authentication deserves a note. SHAZA has one user and no write endpoints. Building auth now
would be building a lock for a door that opens onto a wall. The trigger is genuine
multi-tenancy or browser-initiated writes, and until then the absence of auth is correct rather
than a gap.

## 5. Two corrections to the ML ladder

The order given is statistics, linear regression, logistic regression, decision trees, random
forests, gradient boosting, neural networks, time-series, computer vision.

**Time-series belongs near the front, not seventh.** Every row SHAZA holds is a daily observation
with trend, seasonality and strong autocorrelation. Fitting an ordinary regression to
autocorrelated daily weather produces confident, wrong standard errors, and that mistake is
invisible unless you already know to look for it. Statistics and time-series are the same first
step here, because the data is a time series before it is anything else.

**The first ML problem is not yield.** There is no yield data, so the ladder cannot start where
the charter's questions point. It can start on what is in the database today. Good candidates,
in order of how much they teach per unit of effort:

1. Temperature against elevation across locations, section 6 below.
2. Seasonal decomposition of rainfall at one location, which makes Rwanda's two rainy seasons
   fall out of the data rather than out of a textbook.
3. Gap filling: predict one location's temperature from the other five, then hold out a location
   entirely and see what happens. This teaches the difference between interpolation and
   extrapolation, which is the single idea that will matter most at Stage 6.

## 6. The first regression, concretely

SHAZA already holds everything needed for a complete first experiment with a known right answer.
Mean temperature against elevation, six Rwandan locations, two years:

| | |
| --- | --- |
| Fitted slope | -7.62 C per km |
| Published environmental lapse rate | about -6.5 C per km |
| r squared | 0.814 |
| Sample size | 6 |

This is a good first experiment precisely because physics already knows the answer. A result near
the published lapse rate means the pipeline, the units and the aggregation are probably correct.
A wildly different slope would mean a bug, and you would know to look for it.

The residuals are the interesting part:

```text
rubavu      1546 m   actual 18.75   fitted 20.02   resid -1.27
rwamagana   1532 m   actual 20.65   fitted 20.13   resid +0.52
```

Fourteen metres of elevation apart, nearly two degrees apart in reality. Rubavu sits on Lake
Kivu and Rwamagana does not. The model is missing a variable, the residual says so, and chasing
that residual is feature engineering arriving from a real finding instead of a tutorial.

The sample size is also a lesson. An r squared of 0.814 on six points is not strong evidence, and
reporting it without the n would be exactly the kind of overclaim the charter forbids. Write the
experiment record with that caveat in it.

## 7. Technologies that may never be justified

The most useful thing this document can do is name the entries likely to stay unearned. Leaving
them unbuilt is a result, and the charter already treats a negative result as a result.

**Distributed systems.** SHAZA is one database, one API and a scheduled job. Nothing in the nine
stages implies multiple coordinating nodes. The honest version of this learning goal is system
design, which SHAZA exercises constantly, rather than distribution, which it probably never needs.
If it is wanted for its own sake, `lysa-lab` is the right home.

**Neural networks for yield.** Consider the shape of the eventual training set: a few decades of
seasonal yield, a handful of crops, thirty districts. That is hundreds of rows with maybe a dozen
features. Gradient boosting will beat a neural network on that, usually by a lot, and will also
be interpretable enough to say which variables matter, which is one of the charter's stated
questions. Neural networks get a genuine trigger from imagery or from long sequence data, not
from tabular agronomy.

**Vector databases and RAG.** SHAZA stores numbers, and there is almost no text to embed. There is
one real use, and it is a good one: the Layer 2 indices each need a citation for their published
definition. A corpus of agronomic literature, retrievable and cited, would let Ask SHAZA ground an
index definition in a source rather than in its own memory. That is RAG solving a provenance
problem, which fits the project. RAG over SHAZA's own numeric data would not be.

**Computer vision.** Worth separating from satellite imagery, because they are not the same thing.
NDVI and most vegetation indices are arithmetic on two raster bands, which is NumPy, not computer
vision. The real trigger is Stage 9 and photographs: leaf disease identification from a farmer's
phone. That is a genuine vision problem and it is years away.

## 8. How to hold yourself to this

Each technology that gets adopted gets an experiment record under charter section 14, and the
`Question` field names the trigger that fired. If that field cannot be filled in honestly, the
technology is not ready, and the record of deciding not to adopt it is itself worth keeping.
