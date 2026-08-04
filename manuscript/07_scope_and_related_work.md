# Scope and Related Work

## Scope

BOND-API defines *what* missions are and *how* films plug in; it does not run
missions. Explicitly out of scope for this package:

- mission scheduling, orchestration, or coordination (bond-coordinator,
  bond-orchestrator);
- film content — the 27 film packages implement `mission.MissionProvider`;
- CLI surface and user tooling (bond-cli);
- shared helpers for the suite (bond-utilities), when that package lands;
- any mutation of the protocol after this freeze — changes require a versioned
  migration, not a silent edit.

## Design relationship

- **Film packages**: implement the contract exactly as `films/sable/mission.py`
  does — discoverable by slug, deterministic, self-describing briefs.
- **Coordinators**: consume `discover()` + `MissionRegistry`, move artifacts
  with `to_json`/`from_json`, and never import film internals.
- **bond-utilities**: not yet available as a utilities package; BOND-API
  currently depends only on the stdlib plus `pyyaml`. The integration point is
  tracked in `TODO.md`.

## Related standards

The protocol follows the same conventions as the template it was scaffolded
from — frozen dataclasses for value objects, `typing.Protocol` for structural
contracts, deterministic serialization, and a zero-mock test discipline — so
code moving between template projects and the BOND suite keeps its shape.
