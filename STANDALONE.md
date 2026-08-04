# Standalone Guide

## Identity

BOND-API — the frozen mission protocol contract for the BOND film suite
(Layer 1, codename *THE PROTOCOL*). Version `0.1.0`.

This is a **local-only working tree** inside the BOND monorepo staging area.
There is no remote; do not push anywhere. When the suite is published, this
package ships as `docxology/bond-api` with citation sidecars
(`CITATION.cff`, `.zenodo.json`, `codemeta.json`) already in place.

## Lineage

Scaffolded in Phase 0 from the template's code-project exemplar; Phase 1
replaced the exemplar optimization core with the mission protocol package
described here. No exemplar artifacts remain (see `git log` for the phase-0
scaffold commit).

## What this package is for

- Films (the 27 BOND film packages) implement `mission.MissionProvider`.
- Coordinators/orchestrators discover providers and move mission artifacts
  with `to_json`/`from_json`.
- The protocol is frozen: change it only through a versioned migration.

## Local verification

```bash
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ films/
uv run mypy src/ scripts/ films/
uv run python scripts/00_preflight.py
uv run python scripts/demo_mission.py
```

See [`README.md`](README.md) and [`AGENTS.md`](AGENTS.md) for the full
operating contract.
