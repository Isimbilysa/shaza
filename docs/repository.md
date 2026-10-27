# Repository structure, the lab boundary, and experiment records

*Design note for charter sections 12, 13, 14 and 17. Covers what lives in this repository, what
deliberately does not, and how experiments get recorded so that failures survive.*

---

## 1. The ignore rules, and why `data/` is denied by default

Before this note existed the repository had no root ignore file and no commits. A first
`git add .` would have committed the virtual environment, `node_modules`, the local SQLite
database and `backend/.env`: roughly 455 MB and a configuration file. With `.gitignore` in
place the same command stages 47 source files.

One rule in that file is a design decision rather than hygiene. Everything under `data/raw/`,
`data/processed/` and `data/synthetic/` is ignored, and the common bulk formats are ignored
repository-wide. Charter section 12 says large datasets do not go into git and that the
provenance should be documented instead. A `data/raw/` directory invites the opposite, because
the natural thing to do with a downloaded CSV is to commit it.

So committing a dataset must be deliberate. `git add -f` is required, which makes it a decision
someone made rather than a side effect of staging everything. Small hand-maintained reference
tables under `reference/` and `fixtures/` stay committable, because those are source.

Trained models are ignored on the same reasoning. A model is an output, reproducible from code,
data and a seed. What carries the result is the experiment record, not the pickle.

## 2. Git does not store empty directories

The proposed tree has `data/raw/`, `ml/experiments/`, `simulations/` and others that are empty
today. Git tracks files, not directories, so every one of them disappears on clone.

The usual fix is a `.gitkeep`. A `README.md` in each is better, because the problem those
directories actually have is not emptiness but ambiguity: six months from now the question is
not whether `data/processed/` exists, it is what is allowed to go in it. Each README states what
belongs there, what does not, and for the data directories, the size limit and where the real
data lives.

## 3. Two adjustments to the proposed tree

**Tests belong next to what they test.** The proposal has a root `tests/`, while the repository
already has `backend/tests/`. Keep them next to the code: Python tooling assumes it, imports
stay simple, and a backend test that lives three directories away from the backend tends not to
get written. Reserve a root `tests/` for genuinely cross-cutting work, such as a check that the
API and the dashboard agree about a provenance label.

**`docs/decisions/` exists but is empty.** Both `CLAUDE.md` and `backend/.env.example` point at
it, and `.env.example` cites a specific file, `0002-sqlite-for-local-dev.md`, that was never
written. Either write the decision records or drop the references. A pointer to a missing
document is worse than no pointer, because it reads as though the reasoning was captured
somewhere when it was not. An empty directory also vanishes on clone, so it needs a README like
the others in section 2.

## 4. The three missing top-level files

`README.md`, `CONTRIBUTING.md` and `LICENSE` are all absent. For this project they are not
boilerplate.

**README.** A reader arriving cold needs to know, in order: that SHAZA retrieves external data and
does not collect it, that stored weather is reanalysis rather than measurement, that nothing here
is farming advice, and only then how to run it. Leading with installation instructions buries the
one thing the project most needs a stranger to understand.

**CONTRIBUTING.** On a solo project this is the file where the rules that govern the work are
written down, which is what makes them checkable later. The provenance rule, the no-building-ahead
rule, the no-empty-commits rule.

**LICENSE.** Worth deciding deliberately rather than by default, because it interacts with the
licences of the ingested data. Open-Meteo's terms and ECMWF's ERA5 terms are already recorded in
the `sources` table, and attribution is a condition rather than a courtesy.

## 5. What the lysa-lab boundary is actually for

The split is usually described as serious project versus safe place to break things. That is
true but not operational. The function is narrower:

> Everything in SHAZA should be defensible to a reader. Nothing in lysa-lab has to be justified
> at all.

That is what the boundary protects. The moment SHAZA contains a technology that is there because
it was interesting, the repository stops being evidence of judgement and becomes a list of
things tried. The lab exists so that curiosity has somewhere to go that is not the main project.

**The migration test** is the same trigger rule as `docs/learning-path.md`: something crosses
from the lab into SHAZA when a SHAZA problem exists that it solves. Not when it works, not when it
is finished, not when it is impressive. When there is a problem.

When something does migrate, the SHAZA commit should reference the lab experiment that produced
it. That reference is the difference between a project with a history of reasoning and a project
with a history of file changes.

## 6. Experiment records, and the reason failures go unwritten

The twelve-field template in charter section 14 is good. The thing it needs is not more fields
but a rule about *when* it is filled in.

Records written entirely after the work are reports, not experiments. More importantly, they are
the mechanism by which failures quietly never get documented. Nobody sits down after a model
performs badly and writes up the hypothesis they held beforehand. The intention survives for
about a day. The result is a repository where every recorded experiment succeeded, which is both
useless as research and obviously false to anyone reading it.

So the record is opened in two commits:

1. **Before the work.** `Experiment`, `Date`, `Question`, `Hypothesis`, `Data`, `Method`,
   `Technology`. Commit it.
2. **After the work.** `Result`, `What worked`, `What failed`, `What I learned`,
   `Next experiment`. Commit it.

Git history then proves the hypothesis preceded the result, and a failure writes itself because
the question was already on disk when the answer arrived. This is the same discipline as
`docs/architecture/real-farm-transition.md` section 4, where a prediction must be stored before
the observation it concerns. One version is about the database and one is about the practice,
and both exist because a claim made after the fact cannot be checked.

**Location and naming.** `ml/experiments/NNNN-short-slug.md`, numbered in order, with an
`ml/experiments/README.md` acting as the index. Exploratory work that never becomes an
experiment stays in `notebooks/` and needs no record.

A template lives at `ml/experiments/TEMPLATE.md`.

## 7. Automation and the contribution graph

Charter section 16 is already half-implemented without anyone having framed it that way. The
ingestion pipeline upserts against a natural key and reports how many rows it wrote, which makes
"did anything meaningful change" a value the automation can read rather than a judgement it has
to make. A scheduled workflow that fetches, validates, tests and commits only on a non-zero
meaningful change is a short step from what exists.

The rule stands as written: no commit when nothing changed. A contribution graph coloured by
empty commits is a claim about work that was not done, which puts it in the same category as
every other overclaim these documents are built to prevent.
