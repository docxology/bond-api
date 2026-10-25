# Results

## Protocol surface

The frozen surface consists of {{BOND_NUM_DATACLASSES}} dataclasses —
{{BOND_PROTOCOL_DATACLASSES}} — and the {{BOND_NUM_PROVIDER_METHODS}}-stage
provider flow ({{BOND_PROVIDER_METHODS}}). The surface is verified by
`protocol_surface()` and pinned by `tests/test_protocol.py`, so any accidental
addition or removal of a contract type fails the suite.

## Conformance evidence

The test suite is the conformance evidence for the contract. Test counts and
measured coverage are not restated here: they are produced by the run itself
(`uv run --extra dev pytest tests/ --cov=src`) and the enforced floor is
{{BOND_COVERAGE_FLOOR}}% line **and** branch coverage on `src/`, read straight
from the `fail_under` gate declared in `pyproject.toml` rather than repeated
in prose.

- **Round-trip serialization**: every protocol dataclass round-trips through
  `to_json`/`from_json` with exact type and value equality; tuples stay
  tuples, lists stay lists, nested protocol objects stay nested. Exactness is
  now enforced rather than assumed on the two paths that previously broke it:
  a payload dict carrying the reserved wire key is rejected at encode time
  instead of decoding back as a protocol object, and the protocol-type check
  is on class identity instead of class name, so a dataclass whose `__name__`
  shadows a protocol type is rejected instead of being flattened onto that
  type's fields. The wire tag (`{{BOND_SERIALIZATION_TAG}}`) is published as
  `bond_api.serialization.SERIALIZATION_TAG`, and a test pins the value
  declared in `manuscript/config.yaml` to the live constant, so the format
  cannot drift from its documentation.
- **Registry semantics**: gadget registration/merging/overwrite/drop and
  mission-provider register/lookup/drop are exercised with real providers.
- **Discovery**: the reference film ({{BOND_REFERENCE_FILM}}) is discovered by
  slug and by autodiscovery; malformed packages fail with actionable
  `DiscoveryError`s; unreadable search-path entries are skipped rather than
  raised, verified against a real permission-denied directory.
- **Determinism**: the reference film runs the full lifecycle with fixed
  seed and zero wall-clock dependence; outcomes are byte-identical across
  runs. The wire text and the fingerprint digests are pinned to checked-in
  literal goldens (`tests/test_golden_determinism.py`) rather than to
  same-process self-comparisons, and the same goldens are re-derived in a
  freshly spawned interpreter under a randomized hash seed — which is what the
  "across processes" half of the claim asserts. Platform independence is
  established only over the platforms the suite actually runs on; a literal
  golden makes a platform-dependent encoding fail there rather than pass
  silently, but no test in this package can assert an untested platform.
- **Capability helpers**: each of the {{BOND_NUM_CAPABILITIES}} helpers
  ({{BOND_CAPABILITIES}}) has dedicated tests — advisory brief issues,
  plan-schema matches and violations, SHA-256 fingerprint determinism and
  key-order independence, derived provenance records, and lesson
  normalization (strip/drop/dedupe, first-occurrence order).

## Capability-helper surface

The {{BOND_NUM_CAPABILITIES}} capability helpers layer reusable semantics on
the frozen contract without changing a field. Their names are public API
(pinned by ``CAPABILITY_NAMES`` and exercised by ``tests/test_capabilities.py``);

| Helper(s) | Role |
|---|---|
| `brief_issues` / `validate_brief` | Advisory brief validation — duplicate asset names, duplicate constraint kinds, duplicate objectives, whitespace-slack asset names |
| `plan_schema_issues` / `require_plan_schema` | Plan-step schema checks — duplicate step names, param-key sanity, JSON-serializable params, optional exact step-name sequence |
| `fingerprint` | Deterministic SHA-256 over the canonical JSON encoding of arbitrary parts |
| `hash_provenance` | Fingerprint of a full provenance record (all four fields) |
| `derive_provenance` | Provenance whose `input_hash` derives from the mission inputs |
| `normalize_lessons` / `normalize_debrief` | Strip, drop, and dedupe lessons preserving first-occurrence order; re-validate the outcome |

Each helper's exact behavior and failure mode is pinned by a dedicated test, and
all of them serialize through the same JSON surface as the protocol objects.

## Gate integrity

Four gates in this package could have passed for the wrong reason, and all
four are now controlled:

- **The unresolved-token gate is non-vacuous.** `resolve_manuscript_tree`
  scans every `NN_*.md` section for leftover brace-delimited tokens. A
  manuscript directory containing no sections would have scanned nothing and
  reported success; strict mode now raises instead, and the test suite pins
  that behavior with a real empty directory.
- **The empty-surface gate has a positive control.** The check that the
  protocol exposes dataclasses lives in `require_surface()`, which is called
  directly with a genuinely empty surface in the tests — so the gate is known
  to fire, not merely known to pass on the real package.
- **The determinism assertions pin values, not themselves.** Assertions of the
  form `fingerprint(x) == fingerprint(x)` and `to_json(o) == to_json(o)` hold
  for any deterministic function and cannot fail; they have been replaced by
  literal goldens plus a fresh-interpreter re-derivation.
- **The claim ledger is read by a gate.** `data/claim_ledger.yaml` restates six
  values the package derives elsewhere. Nothing consumed the file, so a stale
  row was undetectable. `tests/test_claim_ledger.py` now re-derives every row
  from its cited source of truth and fails when a row is added without a
  verifier, so the check cannot lapse into covering nothing.

Thin-orchestrator conformance is likewise enforced by machine rather than by
review: a test parses each `scripts/*.py` file with `ast` and fails if a
script grows business logic beyond `main` or stops delegating to `bond_api`.

All tests use real data and real computation — no mocks.
