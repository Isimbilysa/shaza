# SHAZA: twelve months, thirty days, one week

*Planning note. Written 2026-10-22, against the repository as it actually stands rather than
against a blank directory. Supersedes nothing in `docs/charter.md`; it is the schedule, not the
intent.*

---

## 1. You are not at day zero

Any roadmap starting from "set up the repository" would waste the first six weeks. What exists
and works today:

| Built | State |
| --- | --- |
| FastAPI app, three routers, response envelope | working |
| SQLAlchemy models with provenance before value | working |
| Alembic migration | applied |
| Open-Meteo / ERA5 ingestion, validation, idempotent upsert | working |
| Observations in the database | 21,930 rows, 6 locations, 731 days |
| Charter and five architecture notes | written |

Stage 1 is roughly three quarters done. What is missing from it: a dashboard, any tests, the
pipeline write-up, and a first commit.

So month one is not a beginning. It is a closing.

## 2. The capacity this assumes

Six to ten hours a week, around a job and university. That is the number that makes this
roadmap honest, and it is the number most roadmaps quietly assume away.

At that rate, **twelve months covers stages 1 through 5, and starts 6.** It does not cover nine
stages. A twelve-month plan that reached stage 9 would be the scope explosion this document was
asked to prevent.

If the real number turns out to be three or four hours, cut months 8 to 12 rather than
compressing them. Finishing stage 3 properly beats starting stage 5 badly.

## 3. The twelve months

| Months | Stage | The goal | Done when |
| --- | --- | --- | --- |
| 1 | 1 — Foundation | close it | one location goes source to dashboard, documented, committed, tested |
| 2-3 | 2 — Data | a pipeline worth trusting | 30 years of history, a second source, an outcome dataset, Postgres, CI |
| 4-5 | 3 — Visualization | make the data legible | trends, location comparison, a map, provenance visible on every chart |
| 6-7 | 4 — Synthetic Farm | a sandbox, honestly labelled | farm and scenario entities, perturbation layer, published indices |
| 8-10 | 5 — ML | learn ML on a real problem | statistics, time-series, baselines, experiment records, holdout discipline |
| 11-12 | 6 — Scenario Engine | conditional answers with uncertainty | layers 1 and 2 shipped, layer 3 gated and unbuilt |

### The one dependency that decides the second half

Everything from month 8 onward assumes SHAZA has an **outcome variable** by the end of month 3.
Weather is all input. Without crop yield or production data there is nothing to predict, and
stage 5 has no target.

That makes "obtain outcome data" the highest-risk item in the year, and it sits early on
purpose. FAOSTAT and Rwanda's seasonal agricultural survey are the candidates. If both fail, say
so in month 3 and reshape: stage 5 becomes forecasting and gap-filling on weather itself, which
is still real ML on real data, just a different question.

Do not discover this in month 8.

## 4. Explicitly not in this year

Said plainly, because the request asked for it:

- **No AI layer.** Not Ask SHAZA, not RAG, not embeddings, not tool calling. The gate is in
  `docs/architecture/ask-shaza.md` section 8 and nothing this year clears it. A conversational
  layer over three endpoints is a worse product than three endpoints and a chart.
- **No authentication.** One user, no write paths. Building auth now is a lock on a door that
  opens onto a wall.
- **No neural networks.** Gradient boosting will beat them on a few hundred rows of seasonal
  yield, and stay interpretable, which is one of the charter's own questions.
- **No Redis, no queues, no vector database, no object storage.** None has a triggering problem
  this year. Triggers are listed in `docs/learning-path.md` section 4.
- **No Docker until month 6 at the earliest**, and only when Postgres locally or a second machine
  makes it hurt.
- **No real farm work.** Stage 9 is years out. The architecture for it is already written so it
  stays out of the way until then.

## 5. The first thirty days

### Week 1 — make it a repository

The code exists and is not under version control. Everything else waits on that.

Ends with: a first commit, a README that leads with provenance, and three tests that matter.

### Week 2 — close stage 1

One page, one location, one chart, with the reanalysis label visible on it. Not six locations,
not a map, not filters. The charter's gate is one location flowing end to end and the pipeline
documented, and meeting it exactly is the point.

Ends with: the dashboard rendering real data, and `docs/pipeline.md` written.

### Week 3 — fix what stage 2 would break

Two defects from `docs/architecture/data-environments.md` section 6: the series grouping omits
the source, and there is no environment filter. Both are cheap now and expensive once a second
source exists. Then deepen the ERA5 history, which is a flag change and turns two years of
anecdote into a climatology.

Ends with: correct attribution under multiple sources, and roughly 30 years of data.

### Week 4 — the first automation

Tests on push, then the source canary from `docs/automation.md` section 5. Neither commits
anything, so neither has a change-detection problem.

Ends with: CI green on every push, and a daily job that tells you when Open-Meteo changes.

**At thirty days:** stage 1 closed, the repository under version control and tested, three
decades of weather, and automation that reports rather than performs.

## 6. Week one, task by task

Roughly eight hours. Ordered so that stopping early still leaves the repository better than it
started.

1. **Review `.gitignore`, then make the first commit.** It is written and verified: 55 source
   files staged, with the virtual environment, `node_modules`, the local database and `.env`
   excluded. Read it before trusting it. (~30 min)
2. **Write `README.md`.** Leading, in order: SHAZA retrieves external data and does not collect
   it; stored weather is ERA5 reanalysis, not measurement; nothing here is farming advice; then
   how to run it. Installation instructions first would bury the one thing a stranger most needs
   to understand. (~1 h)
3. **Three tests.** Not a suite, these three. Validation rejects a value outside its plausible
   range and accepts one inside it. A second ingest of the same window does not duplicate rows.
   Every stored observation has a non-null provenance. The third is the charter's hard rule,
   expressed as something a machine checks. (~3 h)
4. **Decide the licence and add it.** It interacts with the licences of ingested data, and
   attribution is already a stored condition on the source. Worth ten minutes of deliberate
   thought rather than a default. (~30 min)
5. **Resolve the dangling references.** `CLAUDE.md` points at a `client/` and `server/` landing
   site that is not in this repository, and `backend/.env.example` cites
   `docs/decisions/0002-sqlite-for-local-dev.md`, which does not exist. Write the decision record
   or drop the reference. A pointer to a missing document reads like reasoning that was captured
   when it was not. (~1 h)
6. **Open experiment 0001 and leave it open.** Question, hypothesis, data and method for the
   temperature-against-elevation regression in `docs/learning-path.md` section 6. Sections 1 to 7
   only, committed. Running it is week 5 or later; opening it now is the practice the project is
   supposed to have. (~1 h)

Slack is deliberate. A week planned to the hour is a week that fails on the first surprise.

## 7. Where the rest of the request already lives

Items 4 through 14 are mostly answered, and repeating them here would be the scope explosion
this note exists to avoid.

| Asked for | Where it is |
| --- | --- |
| Technologies to use initially | `docs/learning-path.md` §2-4 |
| Repository structure | `docs/repository.md` §1-4 |
| First database schema | built; design in `docs/architecture/data-environments.md` |
| First API endpoints | built: health, locations, observations |
| First external data source | integrated: Open-Meteo / ERA5 |
| First synthetic-data system | `docs/architecture/scenario-engine.md` §2-3 |
| First meaningful experiment | `docs/learning-path.md` §6 |
| GitHub workflow strategy | `docs/automation.md` §5 |
| Documentation strategy | `docs/repository.md` §6 |

Two are genuinely unanswered and are scheduled rather than designed here: **the frontend pages**,
which week 2 settles by building the smallest one that closes stage 1, and **a full testing
strategy**, which week 1 starts with three tests and which should grow from defects found rather
than from a plan written before any test exists.
