# Local Lift

Local Lift is a data-driven lead generation platform for residential contractors. The system
identifies homeowners who exhibit near-term service intent by aggregating public
signals (property data, code violations, storm events, permits, etc.), scores each
property, and delivers exclusive leads through a territory-based subscription model.

This repository tracks the full stack implementation, starting with the Phase 1
property universe ingestion for the Austin, TX market.

## Project Structure

```
local-lift/
├── backend/           # FastAPI backend, ingestion pipelines, scoring engine
├── docs/              # Data source references, architecture notes
└── notebooks/         # Exploratory analysis (planned)
```

## Getting Started (Development)

> **Status:** Early Phase 1. Instructions will be expanded as infrastructure is added.

1. Install Python 3.11+ (3.15 target) and `uv` or `pip` for dependency management.
2. Copy `.env.example` (pending) to `.env` and set secrets when available.
3. Launch the Docker Compose stack (PostgreSQL, Redis) once defined.
4. Run ingestion pipelines from `backend/src/ingestion` to populate the property universe.

## Roadmap

- [ ] Phase 1 — Property universe, ZIP tiering, enrichment, and data validation
- [ ] Phase 2 — Pattern discovery + scoring algorithm
- [ ] Phase 3 — Production scoring engine, territory management
- [ ] Phase 4 — Lead delivery + engagement tracking
- [ ] Phase 5 — Feedback-driven continuous learning
- [ ] Phase 6 — Web application (admin + contractor portals)

See `docs/data-sources` for the latest research on public data APIs.

## Development Environment

````shell
# Start PostgreSQL + Redis
docker compose up -d

# Apply migrations (placeholder)
# alembic upgrade head

# Run ingestion script
python3 backend/src/ingestion/property_universe.py
````

> Note: Python 3.15 currently lacks prebuilt wheels for pydantic-core.
> Install dependencies using a Python 3.12 interpreter until upstream support lands,
> or install Rust toolchain and set `PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1`.
