# scripts/ — Thin Orchestrators

## Overview

The `scripts/` directory contains **thin orchestrators**: scripts that
coordinate business logic without implementing it. All protocol semantics,
discovery, serialization, and token logic live in `src/bond_api/`; scripts
bootstrap `sys.path`, parse CLI arguments, call `src/`, and print results.

## Inventory

| Script | Purpose |
|---|---|
| `00_preflight.py` | Verify the environment: protocol import, identity, surface inventory |
| `demo_mission.py` | Discover a film by slug and run the full five-stage mission flow |
| `z_generate_manuscript_variables.py` | Hydrate `{{TOKEN}}`s into `output/manuscript/` (strict by default) |

## Conventions

- Each script adds `<root>/src` (and `<root>/films` where relevant) to
  `sys.path` before importing `bond_api`.
- Entry point is `def main() -> int` guarded by
  `if __name__ == "__main__": raise SystemExit(main())`.
- Deterministic output: no timestamps in mission/demo output lines that tests
  assert on.
- No `infrastructure.*` imports; no numpy; no business logic.

## Running

```bash
uv run python scripts/00_preflight.py
uv run python scripts/demo_mission.py            # default: reference film sable
uv run python scripts/demo_mission.py <slug>     # any discoverable film
uv run python scripts/z_generate_manuscript_variables.py            # strict
uv run python scripts/z_generate_manuscript_variables.py --allow-draft
```

## Testing

Smoke tests in `tests/test_scripts_smoke.py` subprocess-invoke each script
with the real interpreter and assert on exit codes and stable output.
