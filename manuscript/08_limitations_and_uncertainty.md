# Limitations and Uncertainty

Every engineering claim in this manuscript is scoped honestly. This section
collects the limits that a hostile reviewer of a protocol library would care
about — where the package is deliberately permissive, where a value is a
declared contract rather than a measurement, and where a reader should not
over-read the evidence.

## Deliberately permissive boundaries (documented, not bugs)

These are accepted design decisions, recorded so nobody re-litigates them:

- **`discover()` silently skips an invalid slug.** Slug validation happens
  inside `load_provider`, whose `DiscoveryError` `discover` catches, so
  `discover(slugs=["9bad-slug"])` returns the healthy remainder rather than
  raising — the "one broken film never hides the rest" design. The strict
  entry point is `load_provider`, which raises. A caller who passes a
  typo'd slug to `discover` gets silence, not an error; both sides are pinned
  by `tests/test_discovery.py`.
- **`sys.modules` caches slug imports.** Two film packages sharing a slug in
  different locations cannot both load in one interpreter. Distinct slugs per
  location are required.
- **Discovery mutates `sys.path` for the duration of an import** and restores
  it in a `finally` block. This makes concurrent discovery from multiple
  threads unsafe by construction; discovery is a startup-time operation.
- **Protocol objects with mutable payloads are unhashable.** Value equality,
  not dict-key semantics — coordinators should treat protocol objects as
  values, not hash keys.
- **`run_mission` executes `recon` but does not thread its report into
  `plan`.** The frozen signature is `plan(brief)`; callers needing the report
  drive the five stages directly.
- **The manuscript PDF is rendered outside this package.** This package ships
  token hydration and validation only; rendering runs in the monorepo
  `infrastructure.rendering` pipeline over `output/manuscript/`.

None of these is a defect; each is a trade-off chosen for the frozen contract
and stated at its call site and in the test suite.

## Wire-format strictness (enforced since Round 2)

The serialization layer is strict where loose encoders are costly. Two holes
were closed and are now pinned by regression tests:

- **Non-finite floats are rejected.** RFC 8259 defines no `NaN` or `Infinity`
  token, yet Python's `json.dumps` writes them as bare literals by default. A
  non-finite float anywhere in a payload — including `Provenance.wall_time_s`,
  where `inf >= 0` used to pass the non-negativity check — is now rejected at
  encode time and at decode time (a foreign document carrying `NaN`/`Infinity`
  fails loudly rather than decoding to a float the encoder could never
  re-emit). This narrows `to_json`/`from_json` to plain, portable JSON.
- **The reserved wire key must carry a known tag.** A payload dictionary whose
  `{{BOND_SERIALIZATION_TAG}}` value is `null`, `false`, `0`, or `[]` used to
  fall through to the plain-dict branch and decode as an untagged dict that
  the encoder then refused to re-encode. Every such tag is now loud, so
  `to_json(from_json(doc))` is total over the documents `from_json` accepts.

## Where the evidence is bounded

- **Coverage is a floor, not a proof.** The enforced gate is
  {{BOND_COVERAGE_FLOOR}}% line **and** branch coverage on `src/`
  (`--cov-fail-under={{BOND_COVERAGE_FLOOR}}`); the measured figure is whatever
  the suite prints, never restated here. Line and branch coverage across the
  six `src/` modules is intentionally not quoted, because it changes with the
  code.
- **Determinism is bounded by the interpreter.** `to_json` output and the
  provenance fingerprints are byte-deterministic and pinned to checked-in
  literal goldens, re-derived in a freshly spawned interpreter under
  `PYTHONHASHSEED=random` (the "across processes" claim). Platform
  independence is established only over the platforms the suite actually runs
  on; no test in this package can assert a platform it has never executed on.
- **Regeneration is byte-identical per interpreter.** `output/` regenerates to
  identical bytes on one interpreter because `generate_variables()` reads no
  wall clock. `{{PYTHON_VERSION}}` is the single environment-derived token, so
  upgrading Python deliberately changes those bytes — that is the token doing
  its job.

## Uncertainty in provenance

`Provenance.wall_time_s` is a recorded duration for auditability, not a
causal claim: nothing in this package asserts a wall-clock bound, and the
reference film stamps `0.0` by design so outcomes are reproducible regardless
of when they run. Where timing is measured by a film package, the value must
be finite (rejected by construction if not) and interpreted with any
timing-measurement granularity caveats the measuring package documents
(`docs/testing_philosophy.md`: use bounds, not exact values, for timing).

## Versioning uncertainty

The package version {{BOND_VERSION}} is declared in four places
(`pyproject.toml`, `bond_api.__version__`, `manuscript/config.yaml` →
`paper.version`, and the reference film's provenance stamp). All four are
gated to agree by `tests/test_exports.py`, so a bump edited in only one place
fails the suite instead of silently shipping stale metadata. The gate makes
drift detectable, but it does not make the version a single loaded value —
that single-source refactor is tracked in `TODO.md` if a future round wants
it.
