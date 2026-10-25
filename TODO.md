# TODO — bond-api (THE PROTOCOL)

BOND-API is Layer 1 of the BOND suite: the frozen mission protocol contract
(11 dataclasses, the `MissionProvider` structural contract, `run_mission`) plus
the machinery every coordinator needs — tagged deterministic JSON, slug-based
film discovery, two registries, capability helpers, and the `sable` reference
film. The package is published at `github.com/docxology/bond-api`.

Verified state at the Round-2 close (macOS arm64, CPython 3.14): **228 tests
pass, 100.00% line and branch coverage on `src/`**
(`uv run --extra dev pytest tests/ --cov=src --cov-fail-under=90`, enforced floor 90),
`ruff check`, `ruff format --check`, and `mypy src/ scripts/ films/` all clean.
All six findings from the adversarial audit (`output/verify/bond-api.json`)
were remediated in `aadd9f8`; the Round-2 pass closed the C1–C4, V1, V2, and
D1 backlog items (recorded below). What remains open is V3 and the extension
table.

The reproducibility section's byte-identity claim is now true and bound:
`generate_variables()` no longer reads a wall clock (the old
`GENERATION_TIMESTAMP` token is gone, replaced by `BOND_MANUSCRIPT_DATE` from
`manuscript/config.yaml` → `paper.date`), and
`tests/test_regeneration_determinism.py` runs the real generator twice across
a whole-second boundary and compares every artifact byte for byte. Before the
fix two consecutive regenerations hashed `2b1e126c…` and `365114ac…`; after it
they hash `d29b9acc…` both times.

This file is forward-only: completed items are pruned as they close; the most
recent round's record stays below.

## Open work

### Verification

#### V3 — platform and Python-version matrix (blocked: needs CI outside this package)

Carried from `output/verify/bond-api.unresolved.json` (item 1). Two claims are
asserted only over the single environment the suite has actually run in:

- **Cross-platform determinism.** The literal goldens at
  `tests/test_golden_determinism.py:66-120` make a platform-dependent encoding
  fail loudly wherever the suite runs, and `test_determinism_holds_across_processes`
  (`tests/test_golden_determinism.py:217`) binds the cross-*process* half with
  a fresh interpreter under `PYTHONHASHSEED=random`. Neither can establish
  behavior on a platform the suite has never executed on. The prose scope was
  already narrowed to match — `manuscript/03_results.md`,
  `manuscript/06_reproducibility.md`, `docs/architecture.md`,
  `docs/testing_philosophy.md`, and the `fingerprint()` docstring at
  `src/bond_api/capabilities.py:157-162`. Do not re-widen it without the
  matrix.
- **`requires-python = ">=3.10"`** (`pyproject.toml:16`). Nothing has run this
  package on 3.10–3.13. The floor is a declaration, not a measurement.

**Done looks like:** a CI matrix (Linux/macOS/Windows × CPython 3.10–3.14)
running `uv run pytest tests/` green, with `tests/test_golden_determinism.py`
producing byte-identical goldens on every cell. Until that exists, this stays
open and the scoped wording stays.

**Command:** `uv run --extra dev pytest tests/test_golden_determinism.py -v` locally
proves one cell only — the closing evidence is the matrix run, not this.

### Extension

Genuine future work. None of these is blocking, and none should be started
speculatively.

| Item | State | What it is |
|---|---|---|
| Adopt bond-utilities | Blocked, external | BOND-API declares it as a suite dependency but imports nothing from it — today the package is stdlib + `pyyaml`. When a real utilities package ships hashing, slug helpers, and shared exception bases, replace `capabilities.fingerprint`, `discovery._SLUG_RE` (`src/bond_api/discovery.py:35`), and the `DiscoveryError`/`SerializationError` bases, and delete the duplication. Do not restructure for a package that does not exist. Done = the local equivalents are gone and the suite is green. |
| Wire-format schema version | Deferred, needs a trigger | The envelope carries a type tag but no schema version. Add one the first time a field is added to any protocol dataclass, not before — an unused version field is one more thing to keep honest. Design note for that day: the version belongs alongside `SERIALIZATION_TAG` in `src/bond_api/serialization.py`, and `from_dict` must read an unversioned document as version 1. Done = a versioned document and an unversioned one both decode, pinned by tests. |
| Downstream conformance harness | Wanted, unblocked | Films are verified today by the one reference film plus in-test scripted providers. A reusable `src/bond_api/conformance.py` — "given any provider, assert it satisfies the contract, is deterministic across two runs, and round-trips every artifact" — lets each of the 27 film packages import one function instead of re-writing the assertions. Additive; no contract change. Done = `films/sable` passes the harness and a deliberately broken provider fails it. |
| Provenance chaining | Idea, unscoped | Chaining fingerprints (outcome N's provenance includes outcome N-1's fingerprint) would give the orchestrator a tamper-evident mission log. Blocked on a decision from bond-orchestrator about who owns and seals the chain tip — an append-only chain whose tip nobody seals proves nothing. Do not write code before that decision. |

## Known limitations (not bugs)

Accepted and deliberate. Recorded here so nobody re-litigates them.

- **`discover()` silently skips an invalid slug.** Carried from
  `output/verify/bond-api.unresolved.json` (item 2). Slug validation happens
  inside `load_provider` (`src/bond_api/discovery.py:98`), whose
  `DiscoveryError` `discover` catches (`src/bond_api/discovery.py:175-176`), so
  `discover(slugs=["9bad-slug"])` returns `{}` rather than raising. The audit
  flagged this as a doc/code mismatch; it was resolved by correcting the
  documentation, **not** by changing the behavior — skipping is the
  "one broken film never hides the rest" design, and `load_provider` remains
  the strict entry point. Honest scope: a caller who passes a typo'd slug to
  `discover()` gets silence, not an error. Both sides of the contrast are now
  pinned by `tests/test_discovery.py` and documented at
  `src/bond_api/discovery.py:161-166` and `manuscript/02_methodology.md:68-74`,
  so it cannot drift back into being undocumented. Reopen only on a deliberate
  decision that eager validation is the better design — that is an API change,
  not a bug fix.
- **`sys.modules` caches slug imports.** Hosting two packages under the same
  slug in different locations requires distinct slugs. Documented at
  `src/bond_api/discovery.py:15-17`.
- **`load_provider` mutates `sys.path` for the duration of an import** and
  restores it in a `finally` block; a film that rewrites `sys.path` itself on
  import is tolerated rather than treated as a discovery failure
  (`src/bond_api/discovery.py:138-147`). This makes concurrent discovery from
  multiple threads unsafe by construction — discovery is a startup-time
  operation.
- **Protocol objects with mutable payloads are unhashable.** Value equality,
  not dict-key semantics. Documented in `src/bond_api/protocol.py`,
  `manuscript/02_methodology.md`, `docs/architecture.md:59-61`.
- **`run_mission` executes `recon` but does not thread its report into
  `plan`.** The frozen signature is `plan(brief)`; callers needing the report
  drive the five stages directly, as `scripts/demo_mission.py` does.
  Documented at `src/bond_api/protocol.py:271-277`. Do not "fix" this by
  changing the flow — it is the contract.
- **Manuscript PDF rendering lives outside this package.** This package ships
  token hydration and validation only; the PDF comes from the monorepo
  `infrastructure.rendering` pipeline reading `output/manuscript/`.
- **`output/` is disposable.** Regenerate it; never hand-edit it to pass a
  gate.

## Verification

The gates for this package, with what a pass looks like:

```bash
# 1. Tests + the enforced coverage gate (line AND branch on src/, floor 90)
uv run --extra dev pytest tests/ --cov=src --cov-fail-under=90
#    → all tests pass; TOTAL coverage ≥ 90.00%. Read the number, not the exit code.

# 2. No mocks anywhere in tests/
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo "Clean"
#    → "Clean"

# 3. Pure core: no infrastructure imports in src/
grep -nE "^(from|import) infrastructure" src/bond_api/*.py || echo "Clean"
#    → "Clean"

# 4. Lint, format, types
uv run --extra dev ruff check src/ scripts/ films/ tests/     # → All checks passed!
uv run --extra dev ruff format --check src/ scripts/ films/ tests/
uv run --extra dev mypy src/ scripts/ films/                  # → Success: no issues found

# 5. Manuscript tokens hydrate strictly (an unresolved token exits non-zero)
uv run python scripts/z_generate_manuscript_variables.py

# 6. The package runs end-to-end
uv run python scripts/00_preflight.py
uv run python scripts/demo_mission.py
```

Steps 1, 4, and 5 are the ones that can actually fail on a bad change.

If `uv` reports `Failed to initialize cache at ~/.cache/uv` you are inside a
sandbox that cannot write the cache — rerun the same command with the sandbox
disabled. `uv run` syncs the default environment, which excludes the `dev`
extra: a bare `uv run` prunes pytest, ruff, and mypy, so dev tools must be
invoked as `uv run --extra dev pytest|ruff|mypy ...` (verified with
`uv sync --dry-run`, which lists them as "would uninstall"). Equivalently,
`uv sync --extra dev` followed by `UV_NO_SYNC=1 uv run ...` uses the synced
environment as-is.

## Standing rules for whoever picks this up

1. Preserve the freeze. Additive changes only; anything else is a versioned
   migration with the old surface kept importable.
2. Never hand-author a metric in the manuscript — add a token.
3. Never add a check without an input that makes it fail. Write the failing
   input first and watch it fail.
4. Re-run the verification block above before claiming done, and read the
   output rather than the exit code.

## Round-2 (2026-08-06)

Round-2 improvement pass. Baseline: 211 tests passed, 100.00% line & branch
coverage on `src/`, `ruff check` clean, `mypy src/ scripts/ films/` clean,
`ruff format --check` failing on `tests/test_manuscript_variables.py:59`
(one long string). This round closed six of the open backlog items and added
a new limitations manuscript section.

### Fixed this round (with test evidence)

**C1 — non-finite floats now rejected at encode and decode.**
`serialization.py::_encode` rejects `inf`/`-inf`/`nan` floats with
`SerializationError` (RFC 8259 has no such token), `from_json` parses with a
`parse_constant` callback that refuses `NaN`/`Infinity` literals from foreign
documents, and `protocol.py::_require_number` rejects a non-finite
`Provenance.wall_time_s` at construction (`inf >= 0` previously passed).
Regression tests: `test_non_finite_payload_float_is_rejected_at_encode`,
`test_from_json_rejects_non_finite_literals`,
`test_provenance_rejects_non_finite_wall_time`,
`test_output_is_valid_strict_json` (formerly `test_output_is_valid_json`,
which only proved Python could read what Python wrote). Before/after
reproduced live: `to_json(Asset(payload={'x': inf}))` emitted `Infinity` and
`Provenance(wall_time_s=inf)` constructed; both now raise.

**C2 — null-tag decode hole closed.** `_decode` now treats `__bond_type__`
as a tag whenever the key is present, so `null`, `false`, `0`, `[]`, `{}`,
and unknown strings all raise `unknown bond type` instead of decoding to an
untagged dict that the encoder refuses to re-encode. Reproduced live before
the fix: `from_json('{"__bond_type__": null, "a": 1}')` returned an untagged
dict whose `to_json` then dead-ended. Regression tests:
`test_reserved_tag_with_invalid_value_is_rejected_on_decode` (parametrized
over `null`/`false`/`0`/`[]`/`{}`/`"gadget"`) and
`test_round_trip_is_total_over_accepted_documents`.

**C3 — version copies gated together.** `data/claim_ledger.yaml` gained a
`package-version` row with a verifier reading `pyproject.toml` `[project]
version`, and new `tests/test_exports.py::test_version_copies_agree_across_the_package`
asserts the four copies (`pyproject.toml`, `bond_api.__version__`,
`manuscript/config.yaml` → `paper.version`, `films/sable/_PACKAGE_VERSION`)
all agree with `pyproject.toml` as the source of truth. A bump in one copy
now fails the suite (`tests/test_claim_ledger.py` + `tests/test_exports.py`).

**C4 — mypy version floor aligned.** `[tool.mypy] python_version` changed
`"3.12"` → `"3.10"` to match `requires-python = ">=3.10"`; `uv run mypy src/
scripts/ films/` still reports success.

**V1 — JSON-validity test now strict.** Renamed
`test_output_is_valid_json` → `test_output_is_valid_strict_json`, parsing with
a `parse_constant` callback that raises so any non-finite token fails.

**V2 — `__all__` is now exercised.** `tests/test_exports.py` asserts every
name in `bond_api.__all__` resolves via `getattr` (with `len(__all__) > 0`)
and that `from bond_api import *` binds exactly `__all__`.

**D1 — misleading pointer removed.** The `[tool.coverage.report]` comment in
`pyproject.toml` no longer points the live coverage percentage at the
monorepo `docs/_generated/COUNTS.md` (which never mentions this package); it
now says the live figure comes from the suite run itself. `fail_under = 90`
is unchanged.

Also fixed: `ruff format` gate (baseline failing on
`tests/test_manuscript_variables.py:59`) is now green.

### Manuscript improvements

Added `manuscript/08_limitations_and_uncertainty.md` — an honest limitations
section covering the deliberately permissive discovery/`sys.modules`/
`sys.path`/hashability boundaries, the now-enforced wire-format strictness
(non-finite floats, reserved-key tags), the interpreter-bounded determinism
claims, provenance uncertainty, and versioning drift control. Added a
live-bound capability-helper table to `manuscript/03_results.md` (helper names
are public API, count from `{{BOND_NUM_CAPABILITIES}}`), and updated the
reader's guide (`01_introduction.md`), conclusion (`04_conclusion.md`), and
`manuscript/AGENTS.md` inventory. All tokens resolve strictly; `output/`
regenerated via `scripts/z_generate_manuscript_variables.py` (17 variables,
byte-identical on re-run).

### Final gate numbers (round-2 close)

- `uv run pytest tests/ --cov=src --cov-fail-under=90` → **228 passed**,
  **100.00%** line & branch coverage on `src/`, 0 skipped, 0 failed
  (updated from the 211-pass / 100.00% baseline).
- `uv run ruff check src/ scripts/ films/ tests/` → clean.
- `uv run ruff format --check src/ scripts/ films/ tests/` → clean.
- `uv run mypy src/ scripts/ films/` → success, no issues.
- No mocks / no `infrastructure.*` imports in `src/` → clean.
- `scripts/z_generate_manuscript_variables.py` strict → resolves 17 variables.
- `scripts/00_preflight.py` and `scripts/demo_mission.py` → run clean.

### Left for a future round

- **V3 — platform/Python-version matrix** remains open (needs CI outside this
  package, per the original entry).
- **Version single-source-of-truth** — the four copies are gated to agree but
  not yet loaded from one value; a future round could make all four read
  `pyproject.toml` at import.
- The **extension table** items (adopt bond-utilities, wire-format schema
  version, downstream conformance harness, provenance chaining) remain as
  listed; none started speculatively.
