# TODO — bond-api (THE PROTOCOL)

BOND-API is Layer 1 of the BOND suite: the frozen mission protocol contract
(11 dataclasses, the `MissionProvider` structural contract, `run_mission`) plus
the machinery every coordinator needs — tagged deterministic JSON, slug-based
film discovery, two registries, capability helpers, and the `sable` reference
film. Verified state as of the run recorded below (macOS arm64, CPython
3.14.6): **211 tests pass, 100.00% line and branch coverage on `src/`**
(`uv run pytest tests/ --cov=src --cov-fail-under=90`, enforced floor 90),
`ruff check` and `mypy src/ scripts/ films/` both clean. All six findings from
the adversarial audit (`output/verify/bond-api.json`) were remediated in
`aadd9f8`; what remains below is what that pass could not close plus what
reading the code this session turned up.

The reproducibility section's byte-identity claim is now true and bound:
`generate_variables()` no longer reads a wall clock (the old
`GENERATION_TIMESTAMP` token is gone, replaced by `BOND_MANUSCRIPT_DATE` from
`manuscript/config.yaml` → `paper.date`), and
`tests/test_regeneration_determinism.py` runs the real generator twice across
a whole-second boundary and compares every artifact byte for byte. Before the
fix two consecutive regenerations hashed `2b1e126c…` and `365114ac…`; after it
they hash `d29b9acc…` both times.

This file is forward-only: completed items are deleted, not archived.

## Open work

### Correctness

#### C1 — `to_json` emits tokens that are not valid JSON

`src/bond_api/serialization.py:158` calls
`json.dumps(_encode(obj), sort_keys=True, indent=2)` with `json.dumps`'
default `allow_nan=True`. A non-finite float anywhere in a payload is written
as the bare literals `Infinity`, `-Infinity`, or `NaN`, which RFC 8259 does
not define. Python's own `json.loads` accepts them, so nothing in this package
notices.

Reproduced live this session:

```
to_json(Asset(kind='k', name='n', payload={'x': float('inf'), 'y': float('nan')}))
  → ...  "payload": { "x": Infinity, "y": NaN }
json.loads(text, parse_constant=<raiser>)  → ValueError: Infinity
```

`Provenance` admits the same value: `_require_number` at
`src/bond_api/protocol.py:76` tests `value >= minimum`, and `inf >= 0.0` is
True, so `Provenance(..., wall_time_s=float('inf'))` constructs and serializes.
(NaN is rejected there only incidentally, because `nan >= 0.0` is False.)

This falsifies four live claims:
`src/bond_api/serialization.py:5` ("plain JSON, so any language can consume
it"), `docs/architecture.md:65-66` ("No pickling anywhere, so other languages
can consume the format"), `manuscript/02_methodology.md:82` ("Protocol objects
serialize to plain JSON"), against a manuscript that cites RFC 8259 at
`manuscript/99_references.md:17`.

**Done looks like:** `_encode` raises `SerializationError` naming the offending
float on `inf`, `-inf`, and `nan`, with tests feeding each through both
`Asset.payload` and `Provenance.wall_time_s`. Decide explicitly whether
tightening `Provenance.wall_time_s` to finite-only is a versioned migration
(it rejects a value that constructs today) or whether only the serializer
tightens and the docstring keeps the honest scope. Do not close this by
softening the prose alone while the wire format still emits `NaN`.

**Command:** `uv run pytest tests/test_serialization.py -v` (new cases must
fail before the fix — verify that first).

#### C2 — the decoder is looser than the encoder on the reserved key

`_encode` rejects any dict containing `__bond_type__`
(`src/bond_api/serialization.py:79-86`, the remediation for audit finding 2).
`_decode` does not mirror it: `src/bond_api/serialization.py:115-116` reads
`tag = value.get(_TYPE_TAG)` and only treats the key as a tag when
`tag is not None`. A `null` tag therefore falls through to the plain-dict
branch.

Reproduced live this session:

```
from_json('{"__bond_type__": null, "a": 1}')  → {'__bond_type__': None, 'a': 1}
to_json(that)                                 → SerializationError
```

So `to_json(from_json(doc))` is not total over documents `from_json` accepts,
and a foreign producer that emits a null tag gets a silently untagged dict
back instead of an error. Every other bad tag value is already loud: `""` and
`0` reach `_KNOWN_TYPES.get(tag)` at line 127 and raise `unknown bond type`.
`null` is the single hole.

**Done looks like:** `_decode` raises `SerializationError` when `_TYPE_TAG` is
present with any value that is not a known string tag, with a test covering
`null`, `false`, `0`, and `[]` as tag values, and a test asserting
`to_json(from_json(doc))` succeeds for every document `from_json` accepts.

**Command:** `uv run pytest tests/test_serialization.py -v`

#### C3 — the package version is stated four times with no gate binding them

`0.1.0` is hand-written at:

- `pyproject.toml:10` — `[project] version`
- `src/bond_api/__init__.py:58` — `__version__`
- `manuscript/config.yaml:11` — `paper.version` (becomes `{{BOND_VERSION}}`)
- `films/sable/mission.py:30` — `_PACKAGE_VERSION`, stamped into every
  `Provenance.package_version` the reference film emits

The only binding is `tests/test_manuscript_variables.py:34`, which pins the
config value to the string literal `"0.1.0"` — it binds config to the test,
not the copies to each other. A version bump is five coordinated edits; miss
`films/sable/mission.py:30` and the reference film stamps stale provenance on
every outcome while the suite stays green. The package already has the right
mechanism for this: `data/claim_ledger.yaml` + `tests/test_claim_ledger.py`,
whose `coverage-floor` row already re-derives a value out of `pyproject.toml`.

**Done looks like:** one source of truth (read `pyproject.toml`, or make
`films/sable` and `manuscript/config.yaml` consume `bond_api.__version__`),
plus a `package-version` row in `data/claim_ledger.yaml` with a verifier in
`VERIFIERS` — so a drifted copy fails `test_ledger_row_matches_live_source_of_truth`.
Prove it by editing one copy to `0.1.1` and watching the suite go red before
reverting.

**Command:** `uv run pytest tests/test_claim_ledger.py -v`

#### C4 — mypy checks against a Python version the package neither floors nor runs

`pyproject.toml:66` sets `python_version = "3.12"`, while
`pyproject.toml:16` declares `requires-python = ">=3.10"` and the suite here
runs on 3.14.6. Syntax or stdlib usage that is valid on 3.12 but absent on
3.10 type-checks clean and would fail at import on the declared floor.

**Done looks like:** `python_version` matches the supported floor (`"3.10"`),
and `uv run mypy src/ scripts/ films/` still reports success — or the floor is
raised to 3.12 in `requires-python` if the 3.10/3.11 support claim is being
dropped. Pick one; do not leave the two numbers disagreeing.

**Command:** `uv run mypy src/ scripts/ films/`

### Verification

#### V1 — `test_output_is_valid_json` does not test JSON validity

`tests/test_serialization.py:125-128` asserts
`json.loads(text)["success"] is True`. Python's parser accepts `NaN` and
`Infinity`, so this test passes on output no strict RFC 8259 parser can read.
It is the hollow half of C1: the name claims interoperability, the assertion
checks only that Python can read what Python wrote.

**Done looks like:** the test parses with a `parse_constant` callback that
raises, so any non-finite token fails here, and a fixture containing a
non-finite float makes it go red before C1 is fixed.

**Command:** `uv run pytest tests/test_serialization.py::test_output_is_valid_json -v`

#### V2 — `bond_api.__all__` is never exercised

`src/bond_api/__init__.py:64-110` publishes 30 names as the package's
top-level surface. Coverage omits the file entirely
(`pyproject.toml` `[tool.coverage.run] omit = [..., "*/__init__.py"]`), so the
100% figure above says nothing about it, and no test in `tests/` performs
`from bond_api import *` or compares `__all__` against `dir(bond_api)`
(grepped this session — zero hits for `__all__` under `tests/`). A name listed
in `__all__` with no corresponding binding — a typo, or an export removed from
a submodule — fails no gate in this package.

**Done looks like:** a test asserting every name in `bond_api.__all__` resolves
via `getattr(bond_api, name)`, plus `len(__all__) > 0` so the loop cannot pass
by iterating nothing. Prove it fires by temporarily appending a bogus name.

**Command:** `uv run pytest tests/ -k exports -v`

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

**Command:** `uv run pytest tests/test_golden_determinism.py -v` locally
proves one cell only — the closing evidence is the matrix run, not this.

### Documentation

#### D1 — `pyproject.toml:52` points coverage at a file that does not track this package

The `[tool.coverage.report]` comment says the live coverage percentage "is
tracked in `docs/_generated/COUNTS.md`". That file lives at the monorepo root
and contains zero occurrences of `bond` (grepped this session) — bond-api is a
local-only `projects/working/` package and is outside the public roster
COUNTS.md is generated from. The pointer sends a reader to a file that will
never mention this package.

**Done looks like:** the comment names the real source (the suite run itself)
or is deleted; `fail_under = 90` stays, since that is the value the manuscript
token actually reads via `read_coverage_floor`.

**Command:** `grep -n "COUNTS" pyproject.toml` returns nothing, and
`uv run pytest tests/test_manuscript_variables.py -v` still passes.

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
uv run pytest tests/ --cov=src --cov-fail-under=90
#    → all tests pass; TOTAL coverage ≥ 90.00%. Read the number, not the exit code.

# 2. No mocks anywhere in tests/
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo "Clean"
#    → "Clean"

# 3. Pure core: no infrastructure imports in src/
grep -nE "^(from|import) infrastructure" src/bond_api/*.py || echo "Clean"
#    → "Clean"

# 4. Lint, format, types
uv run ruff check src/ scripts/ films/ tests/     # → All checks passed!
uv run ruff format --check src/ scripts/ films/ tests/
uv run mypy src/ scripts/ films/                  # → Success: no issues found

# 5. Manuscript tokens hydrate strictly (an unresolved token exits non-zero)
uv run python scripts/z_generate_manuscript_variables.py

# 6. The package runs end-to-end
uv run python scripts/00_preflight.py
uv run python scripts/demo_mission.py
```

Steps 1, 4, and 5 are the ones that can actually fail on a bad change.

If `uv` reports `Failed to initialize cache at ~/.cache/uv` you are inside a
sandbox that cannot write the cache — rerun the same command with the sandbox
disabled. If you touch `pyproject.toml`, resync with `uv sync --all-extras`; a
bare `uv sync` prunes pytest and `uv run pytest` then silently resolves a
different interpreter.

## Standing rules for whoever picks this up

1. Preserve the freeze. Additive changes only; anything else is a versioned
   migration with the old surface kept importable.
2. Never hand-author a metric in the manuscript — add a token.
3. Never add a check without an input that makes it fail. Write the failing
   input first and watch it fail.
4. Re-run the verification block above before claiming done, and read the
   output rather than the exit code.
