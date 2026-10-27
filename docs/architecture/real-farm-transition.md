# The real farm transition

*Design note for charter sections 6 and 11, stage 9. Completes the set with
`data-environments.md`, `scenario-engine.md` and `ask-shaza.md`. The requirement: acquiring land
must not mean rebuilding the platform.*

---

## 1. What already survives the transition untouched

Most of the answer is in the schema already, which is the payoff of decisions made before there
was anything to lose.

`SourceKind.FIELD_OBSERVATION` exists and is documented as "measured by SHAZA on real land --
stage 9". `Provenance.OBSERVED` exists and is reserved for values a real instrument produced.
The one-fact-table design means a thermometer on SHAZA land registers as a source and writes into
the same `observations` table that already holds reanalysis for the same point. The natural key
`(location, source, variable, day)` makes the comparison a self join rather than a migration.

So the weather half of stage 9 is done. A real rain gauge needs a `Source` row and nothing else.

What follows is the half that is not done.

## 2. One farm entity, real and synthetic separated by provenance

The scenario note introduces `SyntheticFarm`. The instinct at stage 9 is to add a parallel `Farm`
for real land, and that instinct is the rebuild this document exists to avoid.

A hypothetical farm and a real farm have the same shape. Both sit at a location, have an area, a
soil description, a crop, a planting date. The difference is not structural. It is whether each
value was invented or measured, which is exactly what provenance records.

```text
Farm
  location_id      the point whose climate applies
  area_ha, soil_*, crop, ...
  source_id        synthetic simulator, or SHAZA field records
  provenance       simulated | observed
```

One entity. A synthetic farm's soil pH is `simulated`; a real farm's measured soil pH is
`observed`. The consequence is the one that matters: **the scenario engine runs unchanged on a
real farm the day you own one.** No porting, no second code path, no "real mode".

Per-field provenance is worth keeping rather than one flag for the whole row. A real farm whose
soil was measured but whose rooting depth was assumed is the normal case, not an edge case.

## 3. The missing third fact table

SHAZA has `observations`, what the environment did, and the planned `CropOutcome`, what came out.
It has no concept of **what somebody did**, and that is the independent variable in every real
experiment.

```text
ManagementEvent
  farm_id, event_date
  kind         planting | fertiliser | irrigation | pest treatment | tillage | harvest
  detail       quantity, product, method
  source_id, provenance, uncertainty
```

Without this table an outcome cannot be attributed, because nothing records what was done to
produce it. A yield with no planting date and no fertiliser record is a number without an
experiment attached.

The design point is the same as section 2. The scenario engine's "planting date plus fourteen
days" **is** a management event with `provenance = simulated`. A real planting is the same row
with `provenance = observed`. Once that holds, a simulated season and a real season are the same
three tables differing only in provenance, and that identity is what the phrase digital twin
should mean here. Anything looser is a metaphor.

## 4. A prediction has to be written before the observation exists

This is methodology, and it is free now and impossible to retrofit.

If a model is fitted after the harvest is known, comparing it to that harvest measures nothing.
The guard is that predictions are rows, written with a timestamp, before the outcome they
concern has been observed:

- the prediction is stored at the moment it is made, with `provenance = predicted` and the model
  version as its source;
- the outcome arrives later as a separate row with `provenance = observed`;
- `ingested_at` on both makes the ordering checkable rather than asserted.

A prediction written after its observation is detectable by comparing timestamps, and should be
treated as a defect in the experiment rather than a result. Charter section 14 already asks for
a hypothesis before a result. This puts that discipline in the database.

## 5. The comparison needs its own record

The charter's loop is data, model, prediction, experiment, observation, evaluation, improved
model. Steps six and seven have nowhere to live, so each comparison becomes an ad hoc notebook
and the loop never accumulates.

```text
Validation
  prediction_id, observation_id
  error, error_unit, method
  n              how many paired cases this covers
  compared_at, notes
```

`n` is required rather than optional, because stage 9 begins at `n = 1`. One farm, one season,
one crop is a single data point, and the pull toward writing "SHAZA predicted the harvest
correctly" will be strong and the claim will be worthless. Requiring the sample size on every
validation row makes the weakness travel with the result instead of being dropped on the way to
the dashboard.

The platform's statement of its own validation status should be **derived from this table**, not
written by hand. With no rows, every model surface says unvalidated, automatically, because it
is reading a count rather than a caption somebody has to remember to update.

## 6. A second scale mismatch, arriving for the same reason as the first

Models trained on ERA5 learn a grid cell roughly nine to eleven kilometres across. A farm is a
point inside one of those cells, with its own slope, aspect, drainage and shade.

So the first real-farm comparison will show error from two sources that look identical in the
output: the model being wrong, and the grid not being the farm. Separating them needs the
on-farm weather record compared against the reanalysis for the same days, independently of any
yield question. That comparison is the first experiment stage 9 should run, before any model is
judged, and it is the same experiment the provenance distinction was protected for.

## 7. What genuinely will need new work

The architecture carries the transition. It does not make it free, and claiming otherwise would
be its own kind of overclaim.

- **Photos.** Binary, large, and not database rows. First real use for object storage.
- **Irregular human records.** Farm notes arrive late, partial, inconsistent and sometimes wrong.
  The validation layer built for a well-formed JSON API will not cover a notebook transcribed
  three weeks later.
- **Subjective observations.** "Leaves looked yellow on the lower field" is real evidence and
  fits no numeric column. It needs a typed observation with a controlled vocabulary, or it
  becomes unsearchable text.
- **No randomisation.** A real farm is managed to produce food, not to produce clean inference.
  Treatments will be confounded with field, season and attention. Charter section 4's warning
  about correlation applies with more force on one farm than it ever did on public data.

## 8. What to do now, before there is land

Three things are cheap today and expensive later.

1. **Add the candidate location the moment one exists, and backfill.** The pipeline already
   handles arbitrary windows, and ERA5 reaches 1940. On day one of owning land you then have
   decades of baseline for that exact point rather than starting a clock.
2. **Find station data and run the reanalysis comparison early.** Rwanda Meteorology Agency
   records, or any public station in the region, let the reanalysis-versus-instrument experiment
   run years before SHAZA owns a gauge. It de-risks the central stage 9 question using somebody
   else's thermometer.
3. **Add `ManagementEvent` when the synthetic farm is built, not when land arrives.** It is the
   same table either way, and building it under simulation means the real-farm path is already
   exercised.

The transition is designed to be boring. If acquiring land turns out to be an architectural
event rather than a data event, something in the three notes before this one was not followed.
