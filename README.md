# bond-api — BOND-API: the frozen mission protocol contract

**BOND-API** (codename **THE PROTOCOL**) is Layer 1 of the BOND suite: the
single contract every film package implements and every coordinator consumes.
This package freezes that contract so the 27 film agents code against a
stable, tested surface.

## What it provides

| Module | Role |
|---|---|
| `src/bond_api/protocol.py` | Frozen dataclasses for the full mission lifecycle (`MissionBrief`, `ReconRequest`, `ReconReport`, `MissionPlan`, `MissionOutcome`, `Debrief`, `Provenance`, `Asset`, `Constraint`, `Finding`, `Step`) + the runtime-checkable `MissionProvider` contract (pure stdlib, no dependencies) |
| `src/bond_api/discovery.py` | Discover film packages on `sys.path` by slug convention — a top-level module named by its slug exposing `mission.MissionProvider` |
| `src/bond_api/registry.py` | `GadgetRegistry` (film → gadgets) and `MissionRegistry` (slug → provider) |
| `src/bond_api/serialization.py` | Deterministic JSON round-trips of every protocol object — no pickling |
| `src/bond_api/manuscript_variables.py` | `{{TOKEN}}` hydration from `manuscript/config.yaml` + the live protocol surface |
| `films/sable/mission.py` | The reference film: a real, deterministic provider implementing the contract |
| `scripts/` | Thin orchestrators only (preflight, demo mission, token hydration) |
| `tests/` | Zero-mock suite; ≥90% line + branch coverage on `src/` |

## Quickstart

```bash
# From this directory
uv sync --extra dev

# Run the suite (the enforced gate)
uv run pytest tests/ --cov=src --cov-fail-under=90

# Verify the environment
uv run python scripts/00_preflight.py

# Run the reference film end-to-end (discovery -> brief -> recon -> plan -> execute -> debrief)
uv run python scripts/demo_mission.py

# Hydrate manuscript tokens
uv run python scripts/z_generate_manuscript_variables.py

# Code quality (both must pass)
uv run ruff check src/ scripts/ films/
uv run mypy src/ scripts/ films/
```

## The protocol in one paragraph

A film package is a top-level module named by its slug (e.g. `sable`) exposing
`mission.MissionProvider` — a class with `film` and five stages:
`brief() -> MissionBrief`, `recon(request) -> ReconReport`,
`plan(brief) -> MissionPlan`, `execute(plan) -> MissionOutcome`,
`debrief(outcome) -> Debrief`. Every artifact is a frozen dataclass validated
at construction time; every outcome carries `Provenance` (package version,
seed, input hash, wall time) so results are auditable. Coordinators find
providers with `discover()`, hold them in a `MissionRegistry`, and move
artifacts across process boundaries with `to_json` / `from_json`.

## Implementation rules (from `AGENTS.md`)

- **Pure core**: `src/bond_api/` is dependency-free logic (stdlib + `pyyaml`
  for config parsing). Scripts are thin orchestrators; business logic lives in
  `src/`.
- **No mocks**: tests use real data and real computation only.
- **Deterministic**: fixed seeds, no untracked random reliance; `to_json` is
  byte-deterministic.
- **Frozen contract**: this is the protocol freeze — change it only through a
  versioned migration, never a silent edit.

## Layout

```
src/bond_api/          The package (protocol · discovery · registry · serialization · manuscript variables)
films/sable/           Reference film implementing the contract
scripts/               Thin orchestrators
tests/                 Zero-mock test suite
manuscript/            Protocol manuscript + config.yaml (token-hydrated)
docs/                  Agent-facing documentation hub
```

## Status

Phase 1 of the BOND suite (protocol layer). Downstream packages —
bond-coordinator, bond-orchestrator, bond-cli, and the film packages — code
against this contract. Integration points and the bond-utilities dependency
are tracked in [`TODO.md`](TODO.md).
