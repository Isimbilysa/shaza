# Automation, designed progressively

*Design note for charter sections 15 and 16. The rule is already settled: automation keeps the
project operational, and never manufactures contribution activity. This note is about the part
that is harder than it looks, which is deciding what "something meaningful changed" actually
means in this repository.*

---

## 1. The problem the design does not survive first contact with

The proposed loop ends with *store the data, then commit if something changed*. Follow it
literally against the repository as it stands and the result is this:

Ingestion writes to a database. The database is not in git, correctly, because
`.gitignore` excludes `*.db` and Postgres was never going to be in there anyway. So a scheduled
job that successfully fetches a new day of weather, validates it and stores it changes **no file
in the repository at all.**

A correct implementation of "commit only when something changed" therefore commits nothing.
Ever. The automation runs every day, does real work, and the repository looks abandoned.

That is the moment the original temptation comes back, now wearing better clothes: write a
timestamp somewhere so there is at least something to commit. That is the empty commit again,
and the rule in charter section 16 exists precisely to stop it.

So the question to answer first is not how to schedule the job. It is: **what legitimately
changes in the repository when SHAZA learns something new?**

## 2. The artifact that honestly changes: a coverage manifest

There is a real answer. The database holds facts about the world; the repository should hold a
small, committed record of *what SHAZA has*. Per location, per variable:

```text
data/documentation/coverage.yaml

  kigali:
    source: open-meteo-era5
    provenance: reanalysis
    temperature_2m_mean:
      first: 1990-01-01
      last:  2026-10-16
      rows:  13438
      gaps:  12
```

This changes when and only when SHAZA's holdings change. It is small, it is readable, it is
useful to someone who cannot reach the database, and it answers the first question any stranger
has about a data project, which is what data is actually in it. A commit that updates it is a
commit that says SHAZA now holds more than it did. That is a real claim, and it is true.

A second honest artifact is the **validation record**: when records are rejected, what was
rejected and why. A rejection means either the source changed or the pipeline is wrong, and both
are worth having in history rather than only in a log that expires.

## 3. The timestamp trap

The manifest must contain facts about **the data**, never facts about **the run**.

The moment it gains a `last_checked:` or `generated_at:` field, it changes on every execution,
and the automation is back to committing daily regardless of whether anything happened. The
change detection would still technically work. It would just always say yes.

Run metadata belongs in the Actions log and the job summary, which is where operational history
should live. Nothing that changes merely because time passed goes in a committed file.

## 4. Two things in the current code block this

**`rows_written` is not a change signal.** `_upsert_observations` ends with `return len(rows)`,
so `IngestResult.rows_written` reports how many rows were *submitted*, not how many were
inserted or modified. Re-running yesterday's window reports the same number as the first run.
The docstring on that module says the upsert is what makes "commit only when something changed"
checkable, and the intent is right, but the return value does not yet carry it. Postgres can
report the distinction with `RETURNING` and an `xmax` check; the simpler portable version is to
compare a count and a checksum before and after.

**Scheduled ingestion needs a database the runner can reach.** GitHub Actions cannot see a local
SQLite file. So the full fetch-validate-store loop is gated on hosted Postgres, which is the
genuine trigger for that part of stage 8. Until that exists, the useful scheduled job is a
different one, described below.

## 5. The progression

**Stage 0 — now. Nothing scheduled.** Run the pipeline by hand. Automating a process before
feeling its failure modes produces automation that handles the failures you imagined rather than
the ones that happen. This is the stated preference and it is the right one.

**Stage 1 — tests on push.** No schedule, no commits, no secrets, no database. It runs pytest
and ruff and reports. This is first because it is the only automation with no change-detection
question at all, and because it protects everything built afterwards.

*This is currently blocked.* `backend/tests/` contains one empty file. The first automation step
is to write the tests, not the workflow. A green pipeline running zero tests is worse than no
pipeline, because it reports success.

**Stage 2 — a source canary, daily, committing nothing.** Fetch a small window from Open-Meteo
into a throwaway database, run validation, assert the response still has the shape the parser
expects, then discard it. Commits nothing, needs no secrets, needs no hosting. It answers one
question every morning: *does SHAZA's data pipeline still work against the live source?* When
Open-Meteo changes a field name or the archive lags further than six days, this finds out within
a day instead of at the next manual run.

This is the step most worth having early and the one most likely to be skipped, because it
produces no visible output when things are fine. That is what a canary is.

**Stage 3 — scheduled ingestion and the manifest.** Requires hosted Postgres and real change
detection from section 4. Fetch, validate, store, regenerate `coverage.yaml`, and commit only if
the file differs. Most days it will differ by one date and a handful of row counts. Some days it
will not differ at all, and on those days there is no commit, which is the correct outcome and
should feel correct rather than like a failure.

**Stage 4 — issues on failure.** When the canary or the ingestion fails twice consecutively,
open an issue. Twice rather than once, because a single transient upstream timeout is not a
defect and an automation that cries wolf gets muted, after which it may as well not exist.

**Stage 5 — experiment reports.** Only once experiments exist and have a stable shape. Regenerate
the index in `ml/experiments/README.md` from the frontmatter of the records, and commit when it
changes. Low value until there are enough records for an index to be worth having.

## 6. Two things on the list worth resisting

**Running experiments automatically.** An experiment has a hypothesis recorded before the work,
per `docs/repository.md` section 6. Scheduled re-execution of a finished experiment is a
regression test, which is useful and should be called that. Scheduled execution of *new*
experiments inverts the method: the result arrives before anyone framed a question.

**Suggesting experiments.** This is the lowest-value item on the list and carries the project's
characteristic risk. An automated suggester generates work nobody chose, and a language model
proposing agricultural experiments will propose fluent, plausible, unfounded ones. If it is ever
built, its output is a draft question for a human to accept or discard, never an opened issue
and never a started run.

## 7. What "alive" should mean

A project is alive because its pipeline still runs, its tests still pass, its data still grows
and its failures get noticed. A contribution graph is a side effect of that, sometimes a sparse
one. Weeks where SHAZA holds exactly what it held before are weeks where the honest number of
commits is zero, and a repository willing to show that is making a more credible claim than one
that is green every day.
