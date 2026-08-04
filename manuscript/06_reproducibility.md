# Reproducibility

## Determinism policy

The protocol makes determinism a contract, not a hope:

- every mission outcome carries `Provenance(package_version, seed, input_hash, wall_time_s)`;
- the reference film uses a fixed seed and performs no random draws;
- `to_json` output is key-sorted with fixed indentation, so identical objects
  serialize byte-identically;
- provenance hashing (`fingerprint`, `hash_provenance`, `derive_provenance`)
  uses the SHA-256 secure hash standard [@nist_fips180_4] over the canonical
  JSON encoding, so identical inputs yield identical fingerprints across
  processes and platforms;
- tests use fixed inputs throughout; any future timing assertions must use
  bounds, not exact values, per `docs/testing_philosophy.md`.

## Artifact inventory

| Artifact | Producer |
|---|---|
| `output/data/manuscript_variables.json` | `scripts/z_generate_manuscript_variables.py` |
| `output/manuscript/*.md` (token-resolved sections) | `scripts/z_generate_manuscript_variables.py` |

`output/` is disposable: regenerate, never hand-edit.

## Token hydration

Every token in `manuscript/*.md` resolves through
`src/bond_api/manuscript_variables.py::generate_variables()`, which reads
`manuscript/config.yaml` and the live protocol surface. The strict-mode script
fails on any unresolved token, and `tests/test_manuscript_variables.py`
cross-references every manuscript token against the generator, so prose cannot
drift from the code.
