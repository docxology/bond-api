# Architecture — BOND-API Layer Boundaries

## Overview

BOND-API is a single-purpose package: freeze the mission protocol and ship the
machinery that makes it usable. The dependency arrow is one-directional:
`scripts/` → `src/`; `tests/` → `src/` + `films/`; nothing imports upward.

## Layers

| Layer | Modules | Rules |
|---|---|---|
| **Protocol core** | `src/bond_api/protocol.py` | Frozen dataclasses + `MissionProvider` Protocol. Pure: stdlib only, no I/O, no imports of other `bond_api` modules at import time beyond the stdlib. |
| **Services** | `src/bond_api/registry.py`, `discovery.py`, `serialization.py` | Pure logic over the protocol surface. `discovery.py` uses `importlib` only; `serialization.py` uses `json` + `dataclasses`. |
| **Config adapter** | `src/bond_api/manuscript_variables.py` | Reads `manuscript/config.yaml` via `pyyaml`; computes `{{TOKEN}}` maps; resolves manuscript trees. |
| **Films** | `films/<slug>/mission.py` | External implementations of the contract (reference: `films/sable/mission.py`). |
| **Orchestrators** | `scripts/*.py` | Thin: path bootstrap, CLI parsing, calls into `src/`, prints results. |
| **Tests** | `tests/` | Zero-mock; real providers, real files, real subprocesses. |

## Key flows

**Discovery** — `discover()` scans search paths for top-level directories
containing `mission.py`, imports `<slug>.mission`, instantiates
`MissionProvider`, binds the provider to its slug (binding precedes the
runtime protocol check because `film` is part of the checkable surface), and
returns `{slug: provider}`.

**Serialization** — `to_json(obj)` encodes protocol dataclasses as
`{"__bond_type__": "<ClassName>", ...fields}` with explicit tuple/list tags;
`from_json(text)` reconstructs exact types. `__bond_type__` is the single
reserved key in payloads.

**Mission flow** — `run_mission(provider, request)` composes
brief → recon → plan → execute → debrief in that exact order.

## Forbidden patterns

- Math/logic in `scripts/` (Rule 3 of `agent_instructions.md`).
- `infrastructure.*` imports in `src/bond_api/*.py`.
- Mocks in tests.
- Silent edits to `protocol.py` fields or validation.
