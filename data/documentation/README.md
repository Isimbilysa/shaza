# data/documentation

This directory **is** committed. It is the part of `data/` that matters to a reader.

One file per source, recording: what it is, who publishes it, the licence and required
attribution, the URL or retrieval method, the variables and units it provides, its spatial and
temporal resolution, known gaps, and the provenance SHAZA assigns to its values.

The `sources` table in the database holds the machine-readable version of some of this. These
files hold the part a human needs: the caveats, the oddities, and the reason a value is labelled
the way it is. Open-Meteo historical data being ERA5 reanalysis rather than station measurement
is exactly the kind of thing that belongs here.
