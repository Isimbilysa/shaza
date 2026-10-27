# ml/models

Trained model artefacts. Not committed.

A model is an output: reproducible from code, data and a seed. What carries the result is the
experiment record in `ml/experiments/`, not the serialised weights.

When a model version is used to produce stored predictions, it is registered as a row in the
`sources` table so its output carries provenance like any other source. See
`docs/architecture/data-environments.md` section 3.
