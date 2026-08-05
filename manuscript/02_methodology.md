# Methodology

## The mission lifecycle

A mission is a deterministic {{BOND_NUM_PROVIDER_METHODS}}-stage flow. Each
stage has one input, one output, and no hidden state:

| Stage | Input | Output |
|---|---|---|
| `brief` | — | `MissionBrief` |
| `recon` | `ReconRequest` | `ReconReport` |
| `plan` | `MissionBrief` | `MissionPlan` |
| `execute` | `MissionPlan` | `MissionOutcome` |
| `debrief` | `MissionOutcome` | `Debrief` |

The orchestrator helper `run_mission(provider, request)` composes the
{{BOND_NUM_PROVIDER_METHODS}} stages in exactly this order and returns the
final `Debrief`. Because the stages are pure functions of their inputs, coordinators can re-run, cache, or
serialize any stage boundary without special-casing a film.

## Frozen dataclasses

Every artifact in the table above is a frozen dataclass (`@dataclass(frozen=True)`):
immutable by construction, value-equal, and validated at construction time.
(Hashability follows Python's rules: an object is hashable when all of its
fields are; opaque payloads such as `Asset.payload` may hold mutable values,
which makes those particular instances unhashable — coordinators should treat
protocol objects as values, not dict keys.) Validation is strict where the
contract demands it — a mission brief must declare a non-empty `film`,
`codename`, and at least one objective; provenance must carry a non-negative
integer seed and a non-empty input hash — and permissive where flexibility is
the point (`Asset.payload` is opaque and JSON-serializable).

## The provider contract

`MissionProvider` is a `typing.Protocol` marked `@runtime_checkable`. A film
package is a top-level module named by its slug exposing
`mission.MissionProvider`; discovery instantiates it, verifies the structural
contract with `isinstance`, and binds it to its slug. A provider that declares
a `film` different from the slug it was discovered under is rejected as an
identity mismatch.

## Discovery

`load_provider(slug, search_paths=...)` imports `<slug>.mission` from the
given search paths (default `sys.path`). `discover(slugs=..., search_paths=...)`
autodetects candidate slugs — top-level directories containing `mission.py` —
or takes an explicit slug list, loading every discoverable provider and
skipping broken ones so one bad film never hides the rest.

### Failure semantics

Discovery is deliberately strict in one direction and tolerant in the other,
because the two callers want opposite things:

| Situation | `load_provider` (single film) | `discover` (bulk) |
|---|---|---|
| Search path is not an existing directory | `DiscoveryError` | `DiscoveryError` (path validation precedes any loading) |
| Slug is not an importable module name | `DiscoveryError` | slug skipped |
| Package missing, provider absent, constructor raises | `DiscoveryError` | slug skipped |
| Provider fails the structural protocol check | `DiscoveryError` | slug skipped |
| Provider declares a film different from its slug | `DiscoveryError` (identity mismatch) | slug skipped |
| Search-path entry exists but cannot be listed | not reached | entry skipped |

A coordinator asking for one named film wants a loud failure; a coordinator
sweeping the {{BOND_NUM_FILMS}}-film fleet wants every healthy film to load
regardless of a sick one. The split is not "validation before loading" versus
"failures during loading": slug validation happens *inside* the per-slug load,
which `discover` catches, so an explicitly requested but malformed slug is
skipped exactly like an unimportable one and `discover` returns the healthy
remainder. Search-path validation is the one check that runs before any
loading and therefore raises from `discover` too. Both behaviors are pinned by
`tests/test_discovery.py`; a caller that needs a malformed slug to be loud
must call `load_provider`.
Both paths leave `sys.path` exactly as they found it: entries inserted for the
import are removed in a `finally` block, and the one tolerated exception there
— a film that rewrote `sys.path` itself on import — is documented at the call
site rather than silently swallowed.

## Serialization

Protocol objects serialize to plain JSON via `to_json` / `from_json`. The
wire format is tagged (`{"{{BOND_SERIALIZATION_TAG}}": "<ClassName>",
...fields}`) so the exact type reconstructs on decode; tuples and lists are explicitly
distinguished; output is key-sorted with fixed indentation so identical
objects produce byte-identical text. No pickling is used anywhere.

## Registries

`GadgetRegistry` maps film slugs to named gadgets (opaque payloads — data,
callables, handlers). `MissionRegistry` is the mission/package registry of
discovered providers, keyed by film slug, filled from `discover()` and used by
coordinators to drive providers without touching import machinery again.

## Capability helpers

The frozen contract is deliberately minimal; capability helpers layer
reusable semantics on top of it without changing a single field or flow
(`src/bond_api/capabilities.py`):

- **Soft brief validation** — `brief_issues` / `validate_brief` report
  advisory issues (duplicate asset names, duplicate constraint kinds,
  duplicate objectives, whitespace-slack asset names) that a coordinator may
  tolerate or escalate, complementing the constructor's hard invariants.
- **Plan-step schema checks** — `plan_schema_issues` / `require_plan_schema`
  verify no duplicate step names, well-formed param keys, JSON-serializable
  params, and optionally an exact expected step-name sequence.
- **Provenance hashing** — `fingerprint` is a deterministic SHA-256 over the
  canonical JSON encoding of arbitrary parts; `hash_provenance` fingerprints a
  full provenance record; `derive_provenance` builds a provenance whose
  `input_hash` follows from the mission's inputs, making outcomes auditable
  without re-running the film.
- **Debrief normalization** — `normalize_lessons` / `normalize_debrief` strip,
  drop, and dedupe lessons while preserving first-occurrence order, and
  re-validate the outcome.

All helpers are deterministic and serialize cleanly through the same JSON
surface as the protocol objects they consume.
