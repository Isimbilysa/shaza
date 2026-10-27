# SHAZA — Project Charter

*Recorded 2026-09-30. The founding document: what SHAZA is for, how it grows, and the rules it
holds itself to. `CLAUDE.md` at the repo root is the working summary of this file.*

---

## 1. Core philosophy

SHAZA is not an agriculture website. It is a long-term software engineering project, data
engineering project, AI/ML research project, agricultural technology project, climate
intelligence project, experimentation platform, and eventually an agricultural operating
system. It should evolve over several years and grow through clearly defined stages rather
than arriving all at once.

> **Build the digital laboratory before building the physical laboratory.**

There is no farmland yet. That is not a reason to wait. Until there is, SHAZA draws on public
datasets, external APIs, historical agricultural data, climate and weather data, satellite and
geospatial data, government and open-data sources, research datasets, synthetic data, and
simulated agricultural scenarios — and eventually, real data from SHAZA farms and field
experiments.

Every data source must be clearly labeled. Simulated or external data is never presented as
data SHAZA collected.

## 2. The long-term vision

SHAZA should eventually combine weather, rainfall, temperature, humidity, soil, elevation,
satellite imagery, vegetation indices, crop information, agricultural production, historical
climate, planting dates, harvest data, pest and disease information, water availability,
farmer observations, and eventually sensor/IoT data.

It should be able to answer questions like:

- What environmental conditions exist in this location?
- How have these conditions changed historically?
- What crops are associated with these conditions?
- What happens if rainfall decreases? If temperature increases?
- How do different scenarios affect agricultural conditions?
- Which variables have the strongest relationship with an agricultural outcome?
- What does the available data suggest?

It must always distinguish observed data, historical data, modeled data, simulated data,
predictions, assumptions, and uncertainty. **Never present predictions as facts.**

## 3. Environment A — real external data

Real information from legitimate external sources: weather and climate APIs, public
agricultural datasets, FAOSTAT, World Bank, NASA, NOAA, Copernicus and open satellite data,
Rwanda government and open data, academic and research datasets. Ingested automatically where
practical.

```text
External API → Data ingestion → Validation → Cleaning → Transformation → PostgreSQL → SHAZA analytics
```

## 4. Environment B — historical data

Historical datasets let SHAZA ask questions that cannot yet be tested physically.

```text
Historical rainfall + Historical temperature + Location + Crop information
        → Analysis → Possible relationships
```

It is the training ground for data cleaning, feature engineering, exploratory analysis,
statistics, visualization, correlation, time-series analysis, anomaly detection, forecasting,
and ML experimentation. Correlation is not causation.

## 5. Environment C — synthetic data

A **SHAZA Synthetic Farm Simulator**: a controlled environment for experimenting without owning
land. Generate hypothetical conditions —

```text
Location: Musanze · Crop: Irish Potato · Rainfall: 120 mm · Temperature: 22°C
Humidity: 70% · Soil moisture: 65% · Planting date: October 15
```

— then change variables (rainfall 120 → 90 mm, temperature 22 → 24°C, soil moisture 65 → 50%)
and create a scenario. Always labeled **SYNTHETIC / SIMULATED DATA**. Never described as a real
agricultural experiment.

## 6. The digital twin

Before land:

```text
Simulated farm → Synthetic conditions → Crop assumptions → Simulated scenarios → Models
```

After land:

```text
Real farm → Real observations → Weather → Soil → Crop observations → Harvest
        → SHAZA database → Compare against simulations
```

This is how SHAZA moves from simulated agriculture to data-informed real-world experimentation.

## 7. Architecture

```text
                         SHAZA
                          │
          ┌───────────────┼────────────────┐
          │               │                │
      External Data   Public Data    Synthetic Data
          │               │                │
          └───────────────┼────────────────┘
                          ↓
                   Data Ingestion
                          ↓
                    Data Validation
                          ↓
                    Data Processing
                          ↓
                      Database
                          ↓
              ┌───────────┴───────────┐
              │                       │
         Analytics                 ML/AI
              │                       │
              └───────────┬───────────┘
                          ↓
                  Scenario Engine
                          ↓
                  SHAZA Intelligence
                          ↓
                Web Dashboard / API
```

## 8. Technology learning goals

SHAZA is a way to learn technologies, not a place to force them in.

- **Backend** — Python: fundamentals, FastAPI, Pydantic, SQLAlchemy, REST, authn/authz,
  background jobs, async, testing.
- **Database** — PostgreSQL: relational modeling, indexes, constraints, migrations,
  transactions, query optimization, geospatial extensions when appropriate. Later Redis, vector
  databases, object storage.
- **Frontend** — Next.js + TypeScript: dashboards, charts, maps, filters, scenario controls,
  auth, visualization.
- **Data** — Pandas, NumPy, cleaning, ETL/ELT, feature engineering, time-series, geospatial.
- **ML**, in order — statistics, linear regression, logistic regression, decision trees, random
  forests, gradient boosting, neural networks, time-series models, computer vision where useful,
  and only eventually more advanced architectures.

Do not use complex ML because it sounds impressive.

## 9. AI layer

Eventually, an interface called **Ask SHAZA**. It must not invent agricultural answers.

```text
User → AI interface → SHAZA tools → Database / APIs / models → Results → AI explanation
```

Candidate tools: `get_weather()`, `get_historical_weather()`, `get_crop_information()`,
`get_location_information()`, `get_soil_information()`, `run_scenario()`,
`compare_locations()`, `analyze_trend()`.

Answers are grounded in SHAZA's own data, and data / model output / AI explanation / uncertainty
stay clearly distinct.

## 10. Scenario engine

```text
Location: Musanze · Crop: Potato
Scenario: Rainfall −20% · Temperature +1.5°C · Planting date +14 days

Scenario → Changed variables → Model → Results → Uncertainty → Explanation
```

Research and educational simulation. Not described as reliable farming advice until validated
against appropriate real-world data.

## 11. Real farm transition

When land becomes available, SHAZA does not start from zero — the digital infrastructure already
exists. Add farm location, crop records, planting dates, fertilizer, irrigation, soil
observations, pest observations, weather measurements, growth observations, harvest quantity
and quality, photos, farmer notes. Later: sensors, IoT, drones, satellite imagery, computer
vision. Then compare SHAZA's prediction against the real observation:

```text
Data → Model → Prediction → Real-world experiment → Observation → Evaluation
     → Improved model → Better experiment
```

## 12. Repository structure

```text
shaza/
├── frontend/
├── backend/
├── data/           # raw · processed · synthetic · documentation
├── ml/             # experiments · models · features · evaluation
├── pipelines/
├── simulations/
├── notebooks/
├── tests/
├── docs/
├── infrastructure/
├── scripts/
├── .github/workflows/
├── README.md
├── CONTRIBUTING.md
└── LICENSE
```

Do not commit huge datasets. Use appropriate storage and document where the data came from.

## 13. Experimentation philosophy

SHAZA is also a personal engineering laboratory: Python, FastAPI, Next.js, databases, APIs, ML,
neural networks, LLMs, RAG, AI agents, computer vision, geospatial systems, maps, Docker,
CI/CD, GitHub Actions, Redis, queues, cloud deployment, auth, system design, distributed
systems, data pipelines, monitoring, testing.

Not every experiment has to become part of the product. Some stay in `ml/experiments/` or
`notebooks/`. The project should encourage experimentation over perfection.

## 14. Experiments must be documented

```text
Experiment:
Date:
Question:
Hypothesis:
Data:
Method:
Technology:
Result:
What worked:
What failed:
What I learned:
Next experiment:
```

Failures are valid results. A note reading *Random Forest performed poorly because the
available dataset lacked sufficient predictive features* is useful research information.

## 15. Automated data pipeline

```text
Fetch available data → Validate → Transform → Store → Run selected analysis → Generate reports
```

GitHub Actions where appropriate. Automation commits only when something meaningful changed.

## 16. Daily GitHub automation

The GitHub account should stay active over the long term, but **not** through fake contribution
activity. No empty commits to green the graph.

```text
Scheduled workflow → Check external data → Validate → Run tests
    → Update experiment metadata → Generate report if necessary → Commit meaningful changes
```

If nothing meaningful changed: **no commit.** Automation exists to keep the project
operational, not to manufacture activity.

## 17. Personal experiment laboratory

A separate repository, **lysa-lab**, for freely experimenting with technologies that may or may
not reach SHAZA: `python/`, `backend/`, `frontend/`, `databases/`, `networking/`, `devops/`,
`ai/`, `machine-learning/`, `computer-vision/`, `system-design/`, `random/`.

```text
lysa-lab → Experiment → Understand technology → Prototype → If useful → SHAZA
```

This keeps SHAZA from becoming restrictive.

## 18. Development roadmap

| Stage | Build | Goal |
| ----- | ----- | ---- |
| **1 — Foundation** | Repo, README, architecture, FastAPI, PostgreSQL, Next.js, basic API, basic dashboard | Get data from a source into a database and display it |
| **2 — Data** | External source, ingestion pipeline, validation, cleaning, storage, history | Build a reliable data pipeline |
| **3 — Visualization** | Charts, maps, filters, historical trends, location comparison | Make the data understandable |
| **4 — Synthetic Farm** | Simulated farms, weather, crop conditions, scenario generation | A safe environment for experimentation before owning land |
| **5 — ML** | Baseline models, evaluation, feature engineering, experiment tracking, comparison | Learn ML through a real problem |
| **6 — Scenario Engine** | Modify rainfall, temperature, planting date, soil variables | Explore hypothetical conditions |
| **7 — AI** | Ask SHAZA, with tool-based access to real data and models | A grounded agricultural intelligence interface |
| **8 — Production** | Docker, CI/CD, auth, RBAC, monitoring, logging, tests, deploy, jobs, caching | Production-quality software |
| **9 — Real Farm** | Connect real farm data and evaluate models against it | From simulated research to real-world experimentation |

## 19. Career objective

The repository should demonstrate the ability to design software systems, build APIs, work with
databases, consume external APIs, build data pipelines, analyze data, build ML models, work
with AI, build frontends, deploy software, automate workflows, test systems, document
engineering decisions, conduct experiments, and learn unfamiliar technologies — through
**evidence of actual work**, not a list of technologies.

## 20. Rules

1. Do not wait for farmland before building SHAZA.
2. Do not pretend synthetic data is real data.
3. Do not pretend external data was collected by SHAZA.
4. Do not build AI features just because AI is fashionable.
5. Prefer simple models before complex models.
6. Document experiments and failures.
7. Every major technology should solve a problem.
8. Build incrementally.
9. Automate meaningful work, not GitHub contribution squares.
10. When real farmland becomes available, integrate the real observations into the system
    instead of abandoning the digital infrastructure.

## 21. First objective

Not AI. Not machine learning. Not satellite imagery. Not a chatbot.

```text
SHAZA v0.1

Choose a location
        ↓
Retrieve real external environmental data
        ↓
Store it
        ↓
Expose it through FastAPI
        ↓
Display it in Next.js
        ↓
Document the entire pipeline
```

> **The first milestone: a working SHAZA data pipeline from an external source, to a database,
> to an API, to a web dashboard.**

Then add one capability at a time. The goal is not to finish SHAZA quickly. The goal is a
project that can keep growing for years.
