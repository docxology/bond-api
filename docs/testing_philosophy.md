# Testing Philosophy — Zero Mocks, Real Contracts, Non-Vacuous Gates

## The zero-mock policy

Every test in `tests/` exercises real objects, real files, and real
computation. No `unittest.mock`, `MagicMock`, `@patch`, or `create_autospec`.
Mocks are forbidden because they test call signatures, not behavior — a
"passing" mocked test can coexist with a broken contract, which is precisely
the failure a protocol package cannot afford.

What tests use instead:

- **Real providers**: the reference film `films/sable/` and in-test scripted
  providers that genuinely implement the five lifecycle stages.
- **Real film packages**: discovery tests write actual `mission.py` modules to
  temporary directories and import them through `sys.path` — including
  deliberately broken ones (missing `execute`, raising constructor, mismatched
  `film`, slotted class that cannot be bound) and one that rewrites `sys.path`
  on import.
- **Real filesystem conditions**: an unreadable search path is produced with a
  real `chmod(0o000)`, not a simulated `OSError`.
- **Real subprocesses**: script smoke tests invoke the scripts with
  `sys.executable` and assert on real stdout/stderr/exit codes.
- **Real files**: manuscript resolution tests write and read real markdown,
  and the coverage-floor test reads the real `pyproject.toml`.

## Coverage mechanics

The enforced gate is line **and** branch coverage on `src/`, at the floor
declared in `pyproject.toml` under `[tool.coverage.report] fail_under`:

```bash
uv run pytest tests/ --cov=src --cov-fail-under=90 --cov-report=term-missing
```

Branch coverage is on (`[tool.coverage.run] branch = true`). Error paths are
first-class: every `ValueError` / `KeyError` / `DiscoveryError` /
`SerializationError` branch has a dedicated test. The floor is a floor, not a
target — never delete a test to make a number work.

The only `pragma: no cover` in `src/` marks the five `...` stub bodies of the
`MissionProvider` Protocol, which are typing markers that never execute; the
exclusion is annotated in `protocol.py` with its reason.

## Gates must be able to fail

A test that cannot fail is worse than no test: it reports safety it never
checked. Three specific defenses are in place here.

**Positive controls.** `require_surface()` exists as a separate function
precisely so a test can call it with a genuinely empty surface and observe it
raise. Before the extraction, the empty-surface check was green only because
the real package always populates a surface — the gate had never fired.

**Non-empty scan sets.** `resolve_manuscript_tree` scans manuscript sections
for unresolved tokens; scanning zero sections would pass trivially. Strict
mode now raises on an empty section set, and a test pins that with a real
directory containing no `NN_*.md` files. The same principle governs
`test_all_manuscript_tokens_are_generated`, which asserts the token set it
collected is non-empty before comparing it, and
`test_script_inventory_is_not_empty`, which pins the exact script list the
thin-orchestrator gate iterates over.

**Structure, not substrings.** The thin-orchestrator test parses each script
with `ast` and fails on any public top-level function other than `main`, any
class definition, or a missing `bond_api` import. The previous version
asserted `"def main()" in source`, which a script with an entire analysis
engine bolted underneath would have passed.

## Cross-source pinning

Some values legitimately exist in two places. Where that happens, a test binds
them together rather than trusting convention:

| Test | Pins |
|---|---|
| `test_config_serialization_tag_matches_code` | `config.yaml`'s declared `serialization_tag` to `bond_api.serialization.SERIALIZATION_TAG` |
| `test_coverage_floor_token_matches_the_enforced_gate` | the `BOND_COVERAGE_FLOOR` token to the `fail_under` line in `pyproject.toml` |
| `test_all_manuscript_tokens_are_generated` | every manuscript token to `generate_variables()` |
| `test_preflight_reports_identity` | the preflight output to the live dataclass count |

## Test inventory

| File | Covers |
|---|---|
| `test_protocol.py` | Frozen dataclass invariants, equality/hash semantics, `MissionProvider` runtime checks, `run_mission` flow order, `protocol_surface()` |
| `test_serialization.py` | Exact JSON round-trips for every protocol type, container-type preservation, determinism, malformed/unsupported inputs, the published wire tag |
| `test_capabilities.py` | Soft brief validation, plan-step schema checks, provenance fingerprinting/derivation, debrief normalization, regression guard that capabilities coexist with the frozen flow |
| `test_registry.py` | Gadget register/merge/overwrite/drop, mission register/lookup/drop, ordering and containment |
| `test_discovery.py` | Slug loading, film binding, identity mismatch, every failure mode, autodiscovery, unreadable search paths, `sys.path` restoration |
| `test_manuscript_variables.py` | Config loading, token map, coverage-floor parsing, surface-gate positive control, live manuscript cross-reference, strict/draft resolution |
| `test_scripts_smoke.py` | Real subprocess runs of `scripts/` (preflight, demo mission, token hydration) plus the `ast` thin-orchestrator gate |

## Determinism

- Fixed seeds and fixed inputs throughout; no random draws.
- Serialization tests assert byte-identical output for identical objects.
- Fingerprint tests assert stability across key orderings and across calls.
- Subprocess smoke tests assert on stable output lines, never timestamps.
- Tests that mutate process state (`sys.path`) restore it before returning.

## Adding a test

1. Build the real object, file, or provider the behavior needs.
2. Assert on behavior — return values, raised exceptions, written files.
3. Ask what would make this test fail. If the answer is "nothing realistic",
   the test is decoration: write the failing case first, watch it fail, then
   make it pass.
4. Check the branch-missing report (`--cov-report=term-missing`) for the lines
   you were targeting and close them.
