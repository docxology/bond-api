# Results

## Protocol surface

The frozen surface consists of {{BOND_NUM_DATACLASSES}} dataclasses —
{{BOND_PROTOCOL_DATACLASSES}} — and the {{BOND_NUM_PROVIDER_METHODS}}-stage
provider flow ({{BOND_PROVIDER_METHODS}}). The surface is verified by
`protocol_surface()` and pinned by `tests/test_protocol.py`, so any accidental
addition or removal of a contract type fails the suite.

## Conformance evidence

The test suite is the conformance evidence for the contract. Live test count
and measured coverage are tracked in `docs/_generated/COUNTS.md`; the enforced
floor is 90% line + branch coverage on `src/` (`--cov-fail-under=90`).

- **Round-trip serialization**: every protocol dataclass round-trips through
  `to_json`/`from_json` with exact type and value equality; tuples stay
  tuples, lists stay lists, nested protocol objects stay nested.
- **Registry semantics**: gadget registration/merging/overwrite/drop and
  mission-provider register/lookup/drop are exercised with real providers.
- **Discovery**: the reference film (SABLE) is discovered by slug and by
  autodiscovery; malformed packages fail with actionable `DiscoveryError`s.
- **Determinism**: the reference film runs the full lifecycle with fixed
  seed and zero wall-clock dependence; outcomes are byte-identical across
  runs.

All tests use real data and real computation — no mocks.
