# data/raw

Data exactly as it arrived from its source. Never edited by hand.

**Contents are not committed.** See `docs/repository.md` section 1 and charter section 12.
Large datasets do not belong in git; what belongs here in version control is the *record* of
where the data came from, which lives in `data/documentation/`.

If a file genuinely must be committed, it has to be small, stable and useful to a reader, and it
takes an explicit `git add -f`. That friction is deliberate.
