# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pipeline corrosion assessment tool based on **DNV-RP-F101** standard. Python/Dash web app that calculates pressure resistance, maximum allowable defect depths, and remaining life for corroded carbon steel pipelines. Deployed at https://corrosion-analyser.onrender.com.

## Build & Run Commands

```bash
# Install dependencies
poetry install

# Run locally (serves at http://localhost:8050)
poetry run python -m src.app

# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov

# Run a single test file
poetry run pytest tests/unittests/test_pressure_calculations.py

# Lint (config in .flake8)
flake8 .

# Docker
docker compose up
```

## Architecture

**Multi-page Dash application** with three layers:

1. **Pages** (`src/pages/`) — Dash UI pages registered via `dash.register_page()`. `defect_analysis.py` is the main analysis page with input forms and Dash callbacks.

2. **Models** (`src/utils/models/`) — Dataclass-based domain objects. `Pipe` is the central orchestrator that holds dimensions, material properties, defects, environment, loading, and computed results. Derived properties are calculated in `__post_init__`.

3. **Calculations** (`src/utils/calculations/`) — Pure engineering computation functions consumed by models:
   - `pressure_calculations.py` — Pressure capacity and resistance
   - `defect_calculations.py` — Defect geometry and interaction
   - `stress_calculations.py` — Combined axial/bending stress
   - `statistical_calculations.py` — Safety factors per DNV standard

**Visualization** (`src/utils/graphing/`) generates Plotly figures for defect cross-sections and pressure resistance curves.

### Data Flow

User input → Validate → Create model objects (Pipe, Defect, Environment, Loading) → Calculate pressure resistance → Calculate effective pressure → Determine max allowable defect depth → (Optional: corrosion rate & remaining life from time-shifted data) → Generate plots → Display results.

### Caching & Async

- Development: `DiskcacheManager` for background callbacks
- Production: Redis + Celery (when `REDIS_URL` env var is set)
- Docker detection via `DOCKER` env var in `src/utils/__init__.py`

## Testing

- **Framework:** pytest with `syrupy` for snapshot testing
- **Fixtures:** `tests/conftest.py` loads JSON example data from `tests/fixtures/`
- **Test data:** Based on DNV-RP-F101 Appendix A examples (known correct values)
- **Snapshots:** stored in `__snapshots__/` directories — update with `pytest --snapshot-update`

## CI/CD

GitHub Actions (`.github/workflows/test-and-deploy.yml`):
- All branches: flake8 lint + pytest
- develop/main: Build multi-platform Docker image → push to Docker Hub (`nicholaslimck/corrosion-analyser`)
- main only: Deploy to Render via webhook

## Key Domain Concepts

- **Safety classes:** Low, Normal, High — affect partial safety factors (gamma_m, gamma_d)
- **Inspection methods:** Relative, Absolute — affect measurement uncertainty
- **Defect interaction:** Multiple nearby defects can be combined into a single effective defect
- **Time-shifted measurements:** Two defect profiles at different times enable corrosion rate and remaining life calculation
- **SMTS/SMYS:** Specified Minimum Tensile/Yield Strength — key material inputs
- **Temperature de-rating:** Material strength reduction at elevated temperatures (via `f_u_temp` tables in `material.py`)
