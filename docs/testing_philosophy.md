# Testing Philosophy — Zero Mocks, Real Contracts

## The zero-mock policy

Every test in `tests/` exercises real objects, real files, and real
computation. No `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec`.
Mocks are forbidden because they test call signatures, not behavior — a
"passing" mocked test can coexist with a broken contract.

What tests use instead:

- **Real providers**: the reference film `films/sable/` and in-test scripted
  providers that genuinely implement the five lifecycle stages.
- **Real film packages**: discovery tests write actual `mission.py` modules
  to temporary directories and import them through `sys.path`.
- **Real subprocesses**: script smoke tests invoke the scripts with
  `sys.executable` and assert on real stdout/stderr/exit codes.
- **Real files**: manuscript resolution tests write and read real markdown.

## Coverage mechanics

The enforced gate is ≥90% line **and branch** coverage on `src/`:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 --cov-report=term-missing
```

Branch coverage is on (`[tool.coverage.run] branch = true`). Error paths are
first-class: every `ValueError`/`KeyError`/`DiscoveryError`/`SerializationError`
branch has a dedicated test.

## Test inventory

| File | Covers |
|---|---|
| `test_protocol.py` | Frozen dataclass invariants, equality/hash semantics, `MissionProvider` runtime checks, `run_mission` flow order, `protocol_surface()` |
| `test_serialization.py` | Exact JSON round-trips for every protocol type, container-type preservation, determinism, malformed/unsupported inputs |
| `test_registry.py` | Gadget register/merge/overwrite/drop, mission register/lookup/drop, ordering and containment |
| `test_discovery.py` | Slug loading, film binding, identity mismatch, all failure modes, autodiscovery |
| `test_manuscript_variables.py` | Config loading, token map, live manuscript cross-reference gate, strict/draft resolution |
| `test_scripts_smoke.py` | Real subprocess runs of `scripts/` (preflight, demo mission, token hydration) |

## Determinism

- Fixed seeds and fixed inputs throughout; no random draws.
- Serialization tests assert byte-identical output for identical objects.
- Subprocess smoke tests assert on stable output lines, never timestamps.

## Adding a test

1. Build the real object/file/provider the behavior needs.
2. Assert on behavior (return values, raised exceptions, written files).
3. Check the branch-missing report (`--cov-report=term-missing`) for the
   lines you were targeting and close them.
