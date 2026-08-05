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
(`uv run pytest tests/ --cov=src`) and the enforced floor is
{{BOND_COVERAGE_FLOOR}}% line **and** branch coverage on `src/`, read straight
from the `fail_under` gate declared in `pyproject.toml` rather than repeated
in prose.

- **Round-trip serialization**: every protocol dataclass round-trips through
  `to_json`/`from_json` with exact type and value equality; tuples stay
  tuples, lists stay lists, nested protocol objects stay nested. The wire tag
  (`{{BOND_SERIALIZATION_TAG}}`) is published as
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
  runs.
- **Capability helpers**: each of the {{BOND_NUM_CAPABILITIES}} helpers
  ({{BOND_CAPABILITIES}}) has dedicated tests — advisory brief issues,
  plan-schema matches and violations, SHA-256 fingerprint determinism and
  key-order independence, derived provenance records, and lesson
  normalization (strip/drop/dedupe, first-occurrence order).

## Gate integrity

Two gates in this package could have passed for the wrong reason, and both are
now controlled:

- **The unresolved-token gate is non-vacuous.** `resolve_manuscript_tree`
  scans every `NN_*.md` section for leftover brace-delimited tokens. A
  manuscript directory containing no sections would have scanned nothing and
  reported success; strict mode now raises instead, and the test suite pins
  that behavior with a real empty directory.
- **The empty-surface gate has a positive control.** The check that the
  protocol exposes dataclasses lives in `require_surface()`, which is called
  directly with a genuinely empty surface in the tests — so the gate is known
  to fire, not merely known to pass on the real package.

Thin-orchestrator conformance is likewise enforced by machine rather than by
review: a test parses each `scripts/*.py` file with `ast` and fails if a
script grows business logic beyond `main` or stops delegating to `bond_api`.

All tests use real data and real computation — no mocks.
