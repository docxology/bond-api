# Introduction

The BOND suite is a family of packages that cooperate to run missions:
{{BOND_NUM_PROVIDER_METHODS}} lifecycle stages — {{BOND_PROVIDER_METHODS}} —
carry a mission from declaration to debrief. For that cooperation to be
possible, every participant must agree on the shape of the artifacts that
cross its boundaries: what a mission brief contains, what a recon report
looks like, what an outcome must prove about itself.

BOND-API exists to make that agreement explicit and durable. It is *the
protocol*: the single contract every film package implements and every
coordinator consumes. Freezing it first — before any of the 27 film packages
are written — means the films are coded against a stable, tested surface
rather than a moving one.

## What this package provides

- **The protocol** (`src/bond_api/protocol.py`): the frozen dataclasses and
  the runtime-checkable `MissionProvider` contract.
- **Discovery** (`src/bond_api/discovery.py`): find film packages on
  `sys.path` by slug convention — a top-level module named by its slug
  exposing `mission.MissionProvider`.
- **Registries** (`src/bond_api/registry.py`): `GadgetRegistry` for
  film-provided gadgets and `MissionRegistry` for discovered providers.
- **Serialization** (`src/bond_api/serialization.py`): deterministic JSON
  round-trips of every protocol object — no pickling.
- **The reference film** (`films/sable/mission.py`): a real, deterministic
  provider that exercises the full lifecycle and demonstrates the contract.

## Reader's guide

Chapter 2 defines the protocol and the discovery/serialization conventions.
Chapter 3 reports conformance evidence from the test suite. Chapters 5–6
document the environment and reproducibility contract.
