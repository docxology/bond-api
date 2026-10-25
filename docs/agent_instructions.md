# AI Agent Instructions — BOND-API Protocol Package

## Why This File Exists

`bond-api` is the **frozen mission protocol contract** for the BOND film
suite. Every downstream package (coordinators, orchestrators, CLIs, and the
film packages) is coded against this surface. Deviating from the rules below —
introducing a mock, moving logic to scripts/, breaking the layer boundary,
silently editing the protocol — breaks the contract and misleads every agent
that implements against it.

Read this file before touching any other file in this project. It states seven
rules; `docs/architecture.md` states where each module's logic belongs, and
`docs/testing_philosophy.md` states how the rules are enforced by tests.

---

## Rule 1: The Protocol Is Frozen

`src/bond_api/protocol.py` defines the contract: the frozen dataclasses
(`MissionBrief`, `ReconRequest`, `ReconReport`, `MissionPlan`,
`MissionOutcome`, `Debrief`, `Provenance`, `Asset`, `Constraint`, `Finding`,
`Step`) and the runtime-checkable `MissionProvider` Protocol.

- Do **not** change the dataclasses' fields, defaults, or validation
  casually. A change is a **versioned migration** (bump `__version__`, keep
  the old surface importable) — never a silent edit.
- Do **not** add `infrastructure.*` imports, `numpy`, or other heavy
  dependencies to the core. The protocol must stay liftable into any Python
  environment (stdlib + `pyyaml` for config parsing only).

### What "frozen" permits

Additive work is allowed and encouraged; subtractive or mutating work is not.
Phase 4 added `src/bond_api/capabilities.py` and Phase 5 published
`SERIALIZATION_TAG` without touching a single existing field — that is the
pattern to follow.

| Change | Allowed? |
|---|---|
| New module under `src/bond_api/` | Yes |
| New helper function, new exported constant | Yes |
| New keyword argument with a default that preserves current behavior | Yes |
| Renaming a field, tightening validation, changing a default | No — versioned migration |
| Changing `MissionProvider`'s five stage signatures or `MISSION_FLOW` | No — the whole fleet implements them |
| Changing the wire tag or the JSON encoding rules | No — wire-format migration |

## Rule 2: Coverage Gate — ≥90% on `src/`

```bash
uv run --extra dev pytest tests/ --cov=src --cov-fail-under=90 --cov-report=term-missing -v
```

If coverage drops, do not delete tests to make the number work — fix the gap.

## Rule 3: The Thin Orchestrator Boundary — `scripts/` vs `src/`

`src/bond_api/` contains all business logic. `scripts/*.py` are thin
orchestrators: they bootstrap `sys.path`, parse CLI arguments, call `src/`
functions, and print results. No protocol semantics, discovery logic, or
serialization details belong in scripts.

**Forbidden**: re-implementing discovery, validation, or JSON encoding inside
a script.

## Rule 4: No Mocks

No `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec` anywhere in
`tests/`. Tests exercise real providers (the reference film `films/sable/`,
scripted in-test providers) with real data and real computation.

## Rule 5: Determinism Policy

- Fixed seeds; no untracked random reliance.
- `to_json` output is byte-deterministic (key-sorted, fixed indent) — tests
  assert exact equality, not bounds.
- **No wall clock in generated artifacts.** `generate_variables()` reads no
  clock, so regenerating `output/` twice on one interpreter writes identical
  bytes. Adding a `datetime.now`/`time.time` token would break that and is
  caught by `tests/test_regeneration_determinism.py`.
- Any future timing assertions must use bounds, not exact values, and must
  document why timing is the relevant property.

## Rule 6: Manuscript Variables Are Injected, Never Hand-Authored

Every token in `manuscript/*.md` resolves through
`src/bond_api/manuscript_variables.py::generate_variables()`, which reads
`manuscript/config.yaml` and the live protocol surface. Hardcoding a metric in
prose is the primary cause of manuscripts drifting from code.

The token pipeline:

1. `scripts/z_generate_manuscript_variables.py` calls
   `generate_variables()` (strict by default).
2. It writes `output/data/manuscript_variables.json`.
3. `resolve_manuscript_tree()` copies each `NN_*.md` section to
   `output/manuscript/` with tokens substituted; strict mode fails on any
   unresolved `{{TOKEN}}`.

Adding a token: add it to the `variables` dict in
`src/bond_api/manuscript_variables.py`, reference it in a manuscript file,
and let `tests/test_manuscript_variables.py::test_all_manuscript_tokens_are_generated`
verify the cross-reference.

The current token map and where each value comes from:

| Token | Source of truth |
|---|---|
| `BOND_IDENTITY`, `BOND_CODENAME` | `protocol.py` constants |
| `BOND_NUM_DATACLASSES`, `BOND_PROTOCOL_DATACLASSES` | `protocol_surface()` |
| `BOND_NUM_PROVIDER_METHODS`, `BOND_PROVIDER_METHODS` | `MISSION_FLOW` |
| `BOND_NUM_CAPABILITIES`, `BOND_CAPABILITIES` | `capabilities.CAPABILITY_NAMES` |
| `BOND_SERIALIZATION_TAG` | `serialization.SERIALIZATION_TAG` |
| `BOND_VERSION`, `BOND_TITLE`, `BOND_SUBTITLE` | `manuscript/config.yaml` → `paper:` |
| `BOND_REFERENCE_FILM`, `BOND_NUM_FILMS` | `manuscript/config.yaml` → `protocol:` |
| `BOND_COVERAGE_FLOOR` | `pyproject.toml` → `[tool.coverage.report] fail_under` |
| `BOND_MANUSCRIPT_DATE` | `manuscript/config.yaml` → `paper.date` (committed; never a clock read) |
| `PYTHON_VERSION` | the running interpreter |

Prefer a token over a literal whenever the value could change without the
prose being edited — counts, floors, slugs, wire keys, versions.

## Rule 7: A Gate That Cannot Fail Is Not a Gate

Before adding or trusting a check, ask what input makes it fail, then supply
that input in a test. Three patterns are already enforced here and must not
regress:

- an inventory-scanning gate asserts its scan set is non-empty
  (`resolve_manuscript_tree` strict mode, `test_script_inventory_is_not_empty`,
  `test_all_manuscript_tokens_are_generated`);
- a validity check that the real package always satisfies is extracted into a
  callable helper so a test can feed it invalid input (`require_surface`);
- structural claims about code are checked with `ast`, not substring greps
  (`test_scripts_are_thin_orchestrators`).

See `docs/testing_philosophy.md` § "Gates must be able to fail".

## Verification Checklist

Run all of these before submitting any change:

```bash
# 1. Tests pass and coverage gate is met
uv run --extra dev pytest tests/ --cov=src --cov-fail-under=90 -q

# 2. No mocks anywhere in tests/
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo "Clean"

# 3. Pure core is infrastructure-free
grep -nE "^(from|import) infrastructure" src/bond_api/*.py || echo "Clean"

# 4. No leftover exemplar scaffold strings (bracket split keeps this doc from matching itself)
rg -n "template[_]code_project" . || echo "Clean"

# 5. Ruff and mypy clean on src/, scripts/, films/
uv run --extra dev ruff check src/ scripts/ films/
uv run --extra dev mypy src/ scripts/ films/
```

All must pass (or print the "Clean" marker).
