# src/

The `bond_api` package — the frozen mission protocol contract for the BOND
film suite.

| Module | Purpose |
|---|---|
| `protocol.py` | Frozen dataclasses + `MissionProvider` contract (pure stdlib) |
| `discovery.py` | Slug-based film discovery on `sys.path` |
| `registry.py` | `GadgetRegistry` + `MissionRegistry` |
| `serialization.py` | Deterministic JSON round-trips |
| `manuscript_variables.py` | Token hydration from `manuscript/config.yaml` |

See [`AGENTS.md`](AGENTS.md) for the full API reference and rules.
