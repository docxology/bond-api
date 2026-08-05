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
  processes and platforms. What is *tested*, in
  `tests/test_golden_determinism.py`: the wire text and four digests are
  pinned to checked-in literals, and re-derived in a freshly spawned
  interpreter under `PYTHONHASHSEED=random`. That binds the cross-process
  claim directly and turns any encoding change into a red test. Platform
  independence is bounded by the platforms the suite is run on — the literals
  fail loudly on a platform that disagrees, but the suite cannot assert a
  platform it has never executed;
- tests use fixed inputs throughout; any future timing assertions must use
  bounds, not exact values, per `docs/testing_philosophy.md`.

## Artifact inventory

| Artifact | Producer |
|---|---|
| `output/data/manuscript_variables.json` | `scripts/z_generate_manuscript_variables.py` |
| `output/manuscript/*.md` (token-resolved sections) | `scripts/z_generate_manuscript_variables.py` |

`output/` is disposable: regenerate, never hand-edit.

### Regeneration is byte-identical

Both artifacts above are byte-identical across repeated regeneration on one
interpreter: running `scripts/z_generate_manuscript_variables.py` twice writes
the same bytes, no matter how much time passes between the runs. This holds
because `generate_variables()` reads **no wall clock**. Every token resolves
from a committed source — the live package surface, `manuscript/config.yaml`,
or the `fail_under` gate in `pyproject.toml`. The manuscript date is
`paper.date` from the config, a value that changes in a diff rather than on
every run.

The scope of that claim, stated exactly:

- **In scope**: repeated runs of the generator on the same interpreter produce
  identical bytes for `output/data/manuscript_variables.json` and every file
  under `output/manuscript/`.
- **Out of scope**: a *different* interpreter. `PYTHON_VERSION` is the one
  environment-derived token, so upgrading Python deliberately changes those
  bytes — that is the token doing its job, and the manuscript says which
  interpreter produced its text.

This is bound by `tests/test_regeneration_determinism.py`, which runs the real
generator script twice into two directories, sleeps across a whole-second
boundary between them so any clock read would show, and compares every output
file byte for byte. A companion `ast` gate fails if a wall-clock call is
reintroduced into the generator module, and that gate carries a positive
control — it is fed a source that *does* read the clock and must flag it, so
it cannot pass by scanning for something it would never find.

## Token hydration

Every token in `manuscript/*.md` resolves through
`src/bond_api/manuscript_variables.py::generate_variables()`, which reads
its sources of truth — live code, configuration, and gate declarations —
and never a hand-typed value:

| Token group | Source of truth |
|---|---|
| Identity, surface inventory, capability list | the live package (`protocol_surface()`, `CAPABILITY_NAMES`) |
| Version, title, subtitle, reference film, film count | `manuscript/config.yaml` |
| Wire-format tag | `bond_api.serialization.SERIALIZATION_TAG` |
| Coverage floor | the `fail_under` gate in `pyproject.toml` |
| Manuscript date | `manuscript/config.yaml` → `paper.date` (committed, never a clock read) |
| Python version | the running interpreter |

Deriving the coverage floor from `pyproject.toml` rather than from prose or
config means the manuscript quotes the gate that actually runs; deriving the
wire tag from the module means renaming the tag breaks the build rather than
the documentation.

Three checks keep this honest: the strict-mode script fails on any unresolved
token; `tests/test_manuscript_variables.py` cross-references every manuscript
token against the generator; and strict resolution refuses to report success
over an empty section set, so the token gate cannot pass by scanning nothing.

`data/claim_ledger.yaml` is the one place that deliberately restates
code-derived values outside the token map. It is not self-certifying prose:
`tests/test_claim_ledger.py` re-derives every row from the source the row
cites and fails on a row with no verifier.
