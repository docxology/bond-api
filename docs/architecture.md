# Architecture — BOND-API Layer Boundaries

## Overview

BOND-API is a single-purpose package: freeze the mission protocol and ship the
machinery that makes it usable. It is Layer 1 of the BOND suite — every film
package implements this contract and every coordinator consumes it, so the
cost of a breaking change here is multiplied by the size of the fleet.

The dependency arrow is one-directional and never bends:

```
scripts/  ──▶  src/bond_api/  ◀──  films/<slug>/mission.py
                    ▲
tests/  ────────────┘  (+ films/)
```

`src/bond_api/` imports nothing from `scripts/`, `films/`, `tests/`, or
`infrastructure.*`. Its only third-party dependency is `pyyaml`, and only in
the config adapter — the protocol core itself is stdlib-only, so a film can
implement the contract in any Python environment.

## Module-by-module

### `src/bond_api/protocol.py` — the frozen contract

The single file the whole suite is coded against. Nothing here changes except
through a versioned migration.

| Symbol | What it is |
|---|---|
| `Asset(kind, name, payload)` | A typed, named artifact attached to a brief. `payload` is deliberately untyped: any JSON-serializable value. |
| `Constraint(kind, detail)` | A declared mission constraint (e.g. `determinism`). |
| `Finding(label, detail)` | One recon observation. |
| `Step(name, action, params)` | One plan step; `params` is a plain dict. |
| `ReconRequest(goal)` | What a mission needs to learn. |
| `MissionBrief(film, codename, objectives, assets, constraints)` | The mission definition a film declares for itself. `objectives` must be non-empty. |
| `ReconReport(findings)` | Ordered recon output. |
| `MissionPlan(steps)` | Ordered plan output. |
| `Provenance(package_version, seed, input_hash, wall_time_s)` | The audit record every outcome carries. |
| `MissionOutcome(success, results, provenance)` | Execution result. |
| `Debrief(outcome, lessons)` | Final stage: outcome plus lessons learned. |
| `MissionProvider` | `@runtime_checkable` `typing.Protocol` — `film` plus the five stages. |
| `run_mission(provider, request)` | Composes the five stages in order, returns the `Debrief`. |
| `protocol_surface()` | Deterministic inventory of the surface (identity, sorted dataclass names, provider flow). Manuscript tokens and preflight read this instead of hardcoding names. |
| `MISSION_FLOW`, `IDENTITY`, `CODENAME` | Constants; `MISSION_FLOW` is the canonical stage order. |

Every dataclass is `frozen=True` and validates in `__post_init__` through the
private helpers `_require`, `_require_non_empty`, `_require_tuple_of`, and
`_require_number`. Validation raises `ValueError` at construction, so an
invalid protocol object cannot exist — downstream code never re-checks.

Two deliberate design notes live in this module:

- **`run_mission` executes recon but does not thread its report into `plan`.**
  The frozen signature is `plan(brief) -> MissionPlan`. A film needing recon
  evidence while planning carries it itself; callers who want the report drive
  the five stages directly (see `scripts/demo_mission.py`).
- **Protocol objects are values, not dict keys.** Hashability follows Python's
  rules — an instance holding a mutable `payload` is unhashable. Compare by
  value; do not key dictionaries on them.

### `src/bond_api/serialization.py` — the wire format

Encodes any protocol object (or JSON-safe composite) to plain JSON and back.
No pickling anywhere, so other languages can consume the format.

- `to_dict` / `from_dict` — dict-level encode/decode.
- `to_json` / `from_json` — text-level; `to_json` is key-sorted with fixed
  indentation, so identical objects produce byte-identical text.
  `from_json(text, expected=Type)` additionally asserts the decoded type.
- `SERIALIZATION_TAG` — the single reserved key (`__bond_type__`), published
  so docs, manuscript tokens, and downstream layers bind to the live value
  instead of repeating a string literal.
- `SerializationError` — raised for non-string dict keys, unsupported payload
  types, unknown tags, malformed container encodings, and missing fields.

Encoding rules worth knowing before writing a film: `tuple` and `list` carry
explicit tags so container types survive a round-trip exactly, and a payload
dict must not itself use the reserved key.

### `src/bond_api/discovery.py` — finding films

The convention: a film package is a **top-level importable module named by its
slug** containing `mission.py` that exposes a `MissionProvider` class.

- `load_provider(slug, search_paths=...)` — strict. Validates the slug against
  a module-name regex, temporarily prepends the search paths to `sys.path`,
  imports `<slug>.mission`, instantiates the provider, binds `film` to the
  slug when the provider declares none, then verifies the structural protocol
  with `isinstance`. Binding must precede the check because `film` is part of
  the checkable surface. Any failure raises `DiscoveryError`.
- `discover(slugs=..., search_paths=...)` — tolerant. Autodetects candidate
  slugs (directories containing `mission.py`) or takes an explicit list, and
  skips slugs that fail so one broken film cannot hide the rest. An unlistable
  search-path entry is skipped, never fatal.
- `DiscoveryError` — the single failure type for this module.

`sys.path` is restored in a `finally` block. The one tolerated exception — a
film that rewrote `sys.path` itself during import, leaving nothing to remove —
is commented at the call site and covered by a test that writes exactly such a
film.

### `src/bond_api/registry.py` — holding what was found

- `GadgetRegistry` — film slug → gadget name → opaque payload. Registration
  merges (re-registering a name replaces only that payload); `lookup`, `drop`,
  `drop_film`, `films`, `gadgets_for`, `contains`, `__contains__`, `__len__`.
  A film's entry disappears with its last gadget. The registry never
  interprets a payload.
- `MissionRegistry` — film slug → `MissionProvider`. `register` (keyed on the
  provider's own `film`), `register_all` (takes the mapping `discover()`
  returns), `lookup`, `drop`, `slugs`, `providers`, plus iteration,
  containment, and length.

Both preserve insertion order, so iteration is deterministic. Both reuse
`protocol.py`'s validation helpers rather than re-implementing argument
checks, which is why the modules share one error vocabulary.

### `src/bond_api/capabilities.py` — semantics on top of the freeze

Added in Phase 4 to deepen the layer **without** touching the contract. Every
helper is pure and deterministic.

| Helper | Behavior |
|---|---|
| `brief_issues(brief)` | Advisory issues beyond the constructor's hard invariants: duplicate asset names, duplicate constraint kinds, duplicate objectives, whitespace-slack asset names. |
| `validate_brief(brief)` | Wraps the above in a `BriefReport` (`.brief`, `.issues`, `.ok`). |
| `plan_schema_issues(plan, expected_steps=None)` | Duplicate step names, non-string/blank param keys, non-JSON-serializable params, and — when `expected_steps` is given — an exact name-and-order match. |
| `require_plan_schema(plan, expected_steps=None)` | The same checks, raising `ValueError` on any issue. |
| `fingerprint(*parts)` | SHA-256 over the canonical JSON encoding of each part, NUL-separated. Deterministic across processes and platforms. |
| `hash_provenance(provenance)` | Fingerprint of all four provenance fields. |
| `derive_provenance(package_version, seed, inputs, wall_time_s)` | Builds a `Provenance` whose `input_hash` follows from the inputs, so an outcome is auditable without re-running the film. |
| `normalize_lessons(lessons)` | Strip, drop empties, dedupe; first occurrence wins, order preserved. |
| `normalize_debrief(debrief)` | Re-validates the outcome and returns a new `Debrief` with normalized lessons. Never mutates — frozen dataclasses make that impossible. |

`CAPABILITY_NAMES` is the deterministic inventory the manuscript token map
consumes: the count in the prose is derived from this tuple, never typed.

### `src/bond_api/manuscript_variables.py` — the config adapter

The only module that touches YAML and the filesystem for configuration.

- `load_manuscript_config(path=None)` — loads and validates `config.yaml`.
- `read_coverage_floor(pyproject_path=None)` — parses `fail_under` out of
  `[tool.coverage.report]`. The manuscript therefore quotes the gate that
  actually runs; a missing declaration raises rather than defaulting.
- `require_surface(surface)` — fails when the protocol exposes no dataclasses.
  Extracted so the gate has a positive control (it is called with a genuinely
  empty surface in the tests) instead of being green only because the real
  package always populates one.
- `generate_variables(...)` — the token map, assembled from the live package,
  `config.yaml`, `pyproject.toml`, and the interpreter.
- `resolve_manuscript_tree(variables, ...)` — copies each `NN_*.md` section to
  `output/manuscript/` with tokens substituted. Strict mode fails on leftover
  tokens **and** on an empty section set, because scanning nothing would make
  the token gate vacuous.

## How `films/sable/mission.py` implements the contract

SABLE is the protocol's own smoke film — the shape every film package copies.
It is a plain class importing only from `bond_api.protocol`, with **no base
class**: `MissionProvider` is a structural `Protocol`, so satisfying it means
having the right attributes, not inheriting anything.

```
films/sable/mission.py
├── film = "sable"                    ← matches the directory slug; a mismatch
│                                       is rejected as an identity mismatch
├── brief()     -> MissionBrief        two objectives, one manifest Asset,
│                                      one determinism Constraint
├── recon(req)  -> ReconReport         three Findings, one echoing req.goal
├── plan(brief) -> MissionPlan         three Steps: contract → execute → verify
├── execute(p)  -> MissionOutcome      success + results + Provenance(seed=7)
└── debrief(o)  -> Debrief             the outcome plus two standing lessons
```

Four properties make it a reference rather than a stub:

1. **Deterministic.** No random draws, no clock reads, no I/O. `wall_time_s`
   is `0.0` and `input_hash` is a fixed string, so two runs are byte-identical
   through `to_json`.
2. **Self-consistent.** `plan()` reads `brief.assets` and `brief.objectives`
   instead of restating constants, so the stages are genuinely wired together.
3. **Discoverable.** It lives at `films/sable/mission.py` and declares
   `film = "sable"`, satisfying both halves of the discovery convention.
4. **Fully typed.** Every stage is annotated with its protocol return type, so
   `mypy` verifies conformance statically while `isinstance` verifies it at
   runtime.

A new film copies this file, renames the directory and the `film` attribute,
and replaces the bodies. Nothing else is required.

## Key flows

**Discovery** — `discover()` scans search paths for top-level directories
containing `mission.py`, imports `<slug>.mission`, instantiates
`MissionProvider`, binds it to its slug, verifies the structural contract, and
returns `{slug: provider}`.

**Serialization** — `to_json(obj)` encodes protocol dataclasses as
`{"__bond_type__": "<ClassName>", ...fields}` with explicit tuple/list tags;
`from_json(text)` reconstructs exact types.

**Mission flow** — `run_mission(provider, request)` composes
brief → recon → plan → execute → debrief in that exact order.

**Token hydration** — `generate_variables()` builds the map,
`resolve_manuscript_tree()` writes the resolved sections, and
`scripts/z_generate_manuscript_variables.py` is the thin wrapper that runs
both and fails loudly on unresolved tokens.

## Forbidden patterns

- Math or protocol logic in `scripts/` (Rule 3 of `agent_instructions.md`) —
  enforced by an `ast`-based test, not by review.
- `infrastructure.*` imports in `src/bond_api/*.py`.
- Mocks in tests.
- Silent edits to `protocol.py` fields, defaults, or validation.
- Restating a code-derived value (a count, a floor, the wire tag) as a literal
  in prose instead of a token.
