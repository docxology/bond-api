# Experimental Setup

## Package layout

| Path | Role |
|---|---|
| `src/bond_api/protocol.py` | Frozen dataclasses + `MissionProvider` contract (pure, stdlib only) |
| `src/bond_api/discovery.py` | Slug-based film discovery on `sys.path` |
| `src/bond_api/registry.py` | `GadgetRegistry` + `MissionRegistry` |
| `src/bond_api/serialization.py` | Deterministic JSON round-trips |
| `src/bond_api/capabilities.py` | Soft brief validation, plan schema checks, provenance hashing, debrief normalization |
| `src/bond_api/manuscript_variables.py` | Token hydration from `config.yaml` |
| `films/{{BOND_REFERENCE_FILM}}/mission.py` | Reference film implementing the contract |
| `scripts/` | Thin orchestrators (preflight, demo mission, token hydration) |
| `tests/` | Zero-mock test suite |

## Configuration

Protocol parameters live in `manuscript/config.yaml` under `protocol:`
(identity, codename, reference film slug, serialization tag). Token variables
inject them into this manuscript — metrics are never hand-authored in prose.
The current version is {{BOND_VERSION}}.

## Environment

- Python: {{PYTHON_VERSION}} (the interpreter that generated this text)
- Manuscript date: {{BOND_MANUSCRIPT_DATE}} — read from `manuscript/config.yaml`
  → `paper.date`, a committed value, not a clock read. The generator reads no
  wall clock at all, so regenerating `output/` twice produces byte-identical
  files; see `manuscript/06_reproducibility.md`.
- Only external runtime dependency: `pyyaml` (manuscript config parsing); the
  protocol core is stdlib-only.

## Running the suite

```bash
cd bond-api
uv run pytest tests/ --cov=src --cov-fail-under={{BOND_COVERAGE_FLOOR}}
uv run python scripts/00_preflight.py
uv run python scripts/demo_mission.py
uv run python scripts/z_generate_manuscript_variables.py
```
