# Methodology

## The mission lifecycle

A mission is a deterministic five-stage flow. Each stage has one input, one
output, and no hidden state:

| Stage | Input | Output |
|---|---|---|
| `brief` | — | `MissionBrief` |
| `recon` | `ReconRequest` | `ReconReport` |
| `plan` | `MissionBrief` | `MissionPlan` |
| `execute` | `MissionPlan` | `MissionOutcome` |
| `debrief` | `MissionOutcome` | `Debrief` |

The orchestrator helper `run_mission(provider, request)` composes the five
stages in exactly this order and returns the final `Debrief`. Because the
stages are pure functions of their inputs, coordinators can re-run, cache, or
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

## Serialization

Protocol objects serialize to plain JSON via `to_json` / `from_json`. The
wire format is tagged (`{"__bond_type__": "<ClassName>", ...fields}`) so the
exact type reconstructs on decode; tuples and lists are explicitly
distinguished; output is key-sorted with fixed indentation so identical
objects produce byte-identical text. No pickling is used anywhere.

## Registries

`GadgetRegistry` maps film slugs to named gadgets (opaque payloads — data,
callables, handlers). `MissionRegistry` is the mission/package registry of
discovered providers, keyed by film slug, filled from `discover()` and used by
coordinators to drive providers without touching import machinery again.
