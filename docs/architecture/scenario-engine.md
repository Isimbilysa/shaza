# Scenario engine: design before implementation

*Design note for charter sections 9 and 10, stage 6. Companion to
`docs/architecture/data-environments.md`. Written before any scenario code exists, which is the
point.*

---

## 1. Start from what is not true yet

The target interaction is:

```text
Musanze · Potato · rainfall -20% · temperature +1.5C · planting date +14 days
        -> model -> result + uncertainty + explanation
```

The honest problem with that picture is the word **model**. SHAZA holds daily weather and
nothing else. There is no yield, no harvest, no production figure, no observed agricultural
outcome of any kind. A model that turns rainfall into potato yield cannot be fitted, because
nothing in the database has ever recorded a potato.

This matters more than it sounds. A scenario engine is unusually easy to fake. A hardcoded
elasticity returns `yield -14%`, a plausible interval is printed beside it, and the result looks
indistinguishable from research. It would be an unsupported agricultural claim with a progress
bar. Charter rule 4 and section 10 both exist to prevent exactly this, and a disclaimer in the
footer does not prevent it.

So the engine is designed in layers, where each layer is honest on its own and the layer that
needs a model is gated behind having one.

## 2. Three layers

**Layer 1 — Perturbation. Buildable now. Claims nothing about agriculture.**

Take a real baseline series for a location, apply the stated deltas, emit a modified series.
Rainfall scaled by 0.8, temperature shifted by +1.5C, the window moved 14 days later. This is
arithmetic over ERA5. It requires no model and no agronomy.

Output provenance is `simulated`. The question it answers is *what would the weather look like*,
never *what would the harvest be*. Layer 1 alone already supports a genuinely useful product:
side-by-side baseline and perturbed climate for a location.

**Layer 2 — Published indices. Buildable after Stage 2. Cites literature, fits nothing.**

Compute standard agro-climatic indices from the perturbed series. These are defined formulas
from published sources, not relationships SHAZA discovered:

| Index | What it needs | Status for SHAZA today |
| --- | --- | --- |
| Growing degree days | daily mean temp, crop base temp | ready, needs a crop table |
| Consecutive dry days | daily precipitation | ready |
| Rainfall onset and cessation | daily precipitation, a defined threshold | ready |
| Standardised Precipitation Index | ~30 years of precipitation | blocked, see section 6 |
| Water balance (P - PET) | radiation, wind, humidity | blocked, variables not fetched |

Each index row stores the citation for its definition. Provenance is `derived`, because SHAZA
computed it from stored values using somebody else's published formula.

Layer 2 is where most of the real value sits, and it needs no yield data at all. "Under this
scenario the season has eleven more growing degree days and a dry spell four days longer" is a
defensible statement. "Yield falls 14%" is not.

**Layer 3 — Fitted prediction. Gated behind Stage 5 and real outcome data.**

Only here does a model map conditions to an agricultural outcome. Provenance is `predicted`,
source kind is `model_output`. Layer 3 stays unbuilt until the `CropOutcome` table described in
the data-environments note holds real observations to fit against and hold out.

The engine ships to users at Layer 2. Layer 3 appears when it has earned the right to.

## 3. The eight distinctions, and the three with no home

The eight things the platform must keep distinct are again a mix of different kinds of
statement. Sorted by where each one actually lives:

| Distinction | Where it lives | Exists today |
| --- | --- | --- |
| Observed data | `Provenance.OBSERVED` | yes |
| External data | `SourceKind.EXTERNAL_API`, `PUBLIC_DATASET` | yes |
| Synthetic data | `SourceKind.SYNTHETIC` + `Provenance.SIMULATED` | yes |
| Historical data | a date filter, not a category | n/a by design |
| Model output | `SourceKind.MODEL_OUTPUT` | **missing** |
| Predictions | `Provenance.PREDICTED` | **missing** |
| Uncertainty | `Observation.uncertainty` column | column exists, unpopulated |
| **Assumptions** | nowhere | **missing, and it is the important one** |

Assumptions are the gap that matters for this engine. "Rainfall falls 20%" is an assumption.
"Potato base temperature is 7C" is an assumption. "The 2015-2025 window is a fair baseline" is
an assumption. A scenario result read without them is not interpretable, and prose in a caption
is not a storage mechanism.

```text
Assumption    statement, value, unit, kind (premise | parameter | baseline choice),
              citation or explicitly "SHAZA assumption, unvalidated",
              linked to the scenarios that rely on it
```

Every scenario result returns its full assumption list. Not a summary, the list.

## 4. What a scenario result has to carry

A bare number is the failure mode. The returned object is:

```text
ScenarioResult
  baseline        location, real date window, source, provenance
  deltas          what was changed, from what, to what
  assumptions     every one, each with citation or unvalidated flag
  layer           1 perturbation | 2 index | 3 prediction
  outputs         series or indices, each with its own provenance
  uncertainty     decomposed, see below
  validated       has this been checked against reality? at stage 6: no, always
  run             scenario id, seed, code version, timestamp
```

`validated` is a required field rather than an optional one, so that shipping an unvalidated
engine means shipping a field that says `false` on every response. That is harder to forget
than a disclaimer.

## 5. Uncertainty is three things, and one of them is not a number

Reporting a single interval on a scenario result is itself a false claim. Three distinct
sources, which must not be added together:

- **Baseline uncertainty.** ERA5 is a roughly 9 to 11 km grid cell, not Musanze. Quantifiable in
  principle, currently unpopulated: every row in the database has `uncertainty = NULL`, which
  the model docstring correctly defines as "the source did not quantify it", never "there is
  none".
- **Model uncertainty.** Fit error, holdout performance, interval width. Only exists at Layer 3.
- **Scenario uncertainty.** None. There is no probability that rainfall falls 20%, because
  nobody claimed it would. It is a premise, not a forecast.

That third point drives the framing. A scenario is **conditional**, and the uncertainty attaches
to the consequent, never the premise:

> IF rainfall falls 20 percent, THEN under the listed assumptions the dry spell lengthens by
> four days, plus or minus the baseline and model error.

Never "rainfall will fall 20 percent and yield will drop." Attaching a confidence interval to
the whole statement quietly implies the premise is likely.

## 6. Two years is not a climatology

The database holds 731 days, from 2024-09-24 to 2026-09-24. Several standard indices need about
thirty years to define a normal, and "this season is dry" is meaningless without a distribution
to be dry relative to. With two years, every baseline is an anecdote.

Open-Meteo's ERA5 archive reaches back to 1940 and the ingestion pipeline is already idempotent
over arbitrary windows. Deepening history is a flag change, not a feature. Stage 2 should extend
backwards as well as adding sources, because the scenario engine's baseline quality is capped by
it.

## 7. Always a comparison, never a bare number

A scenario reported alone reads as a prediction about the world. Reported against its baseline it
reads as what it is, a difference under stated assumptions. The API returns the pair, and the UI
renders the pair. "Eleven more growing degree days than the 1990-2020 baseline" is a sentence
SHAZA can defend. "Growing degree days: 1,462" is a number pretending to be an answer.

This also answers the *which variables appear related to an outcome* question. Any relationship
SHAZA surfaces carries its sample size, its period, and an explicit non-causal label. Charter
section 4 already says correlation is not causation; the API should make that structural by
never returning a correlation without its n and window.

## 8. The explanation is assembled, not written

Stage 7's Ask SHAZA narrates scenario results. The rule is that it narrates the structured object
and may not add agronomy absent from it. At stage 6 the explanation is a template over
`ScenarioResult`, which is deliberately boring and cannot hallucinate a crop response. A
generated explanation becomes acceptable only when it is constrained to the fields above, and
even then the assumptions and the `validated` flag are rendered by the template, not the model.

## 9. Build order

1. Deepen the ERA5 history and add the outcome dataset. Stage 2.
2. Crop table and the `Assumption` entity. Small, and Layer 2 blocks on them.
3. Layer 1 perturbation over a real baseline. Honest and shippable.
4. Layer 2 indices, each with its citation.
5. `CropOutcome` populated with real yields. Only then Stage 5 models.
6. Layer 3, with `validated = false` until it is checked against observations.

Layers 1 and 2 are a real scenario engine. They are not a lesser version of the thing, they are
the part that does not require pretending.
