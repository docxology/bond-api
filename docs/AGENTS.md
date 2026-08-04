# docs/ — Agent Guide

## Overview

Technical guide for the BOND-API documentation hub. Every document is a hard
constraint for agents working in this package, not a suggestion.

## File Inventory

| File | Purpose |
|---|---|
| `README.md` | Quick navigation index |
| `AGENTS.md` | This index |
| `agent_instructions.md` | Behavioral constraints (read-first priority) |
| `architecture.md` | Layer boundaries and key flows |
| `testing_philosophy.md` | Zero-mock policy, coverage mechanics, test inventory |

## Key Conventions

**Read-first protocol**: agents must read `agent_instructions.md` before
modifying any project file. The most common agent errors are: introducing
mocks (Rule 4), moving logic into scripts (Rule 3), and silently editing the
frozen protocol (Rule 1).

**Architecture isolation**: `src/bond_api/` is pure logic (stdlib +
`pyyaml` only); `scripts/` is thin glue; `tests/` is zero-mock; `films/` holds
real implementations of the contract. The dependency arrow is one-directional
and nothing imports upward.

**Frozen surface**: `src/bond_api/protocol.py` is the contract every film
package implements. Changes are versioned migrations, never silent edits.

## REQUIRED vs AESTHETIC

| Path | Status | Enforcing gate / source of truth |
|------|--------|---------------------------------|
| `src/bond_api/protocol.py` | REQUIRED | Coverage gate; `tests/test_protocol.py`; discovery conformance |
| `src/bond_api/discovery.py` | REQUIRED | `tests/test_discovery.py` |
| `src/bond_api/registry.py` | REQUIRED | `tests/test_registry.py` |
| `src/bond_api/serialization.py` | REQUIRED | `tests/test_serialization.py` |
| `src/bond_api/capabilities.py` | REQUIRED | `tests/test_capabilities.py` |
| `src/bond_api/manuscript_variables.py` | REQUIRED | `tests/test_manuscript_variables.py` + live token cross-reference |
| `tests/` (all `test_*.py`) | REQUIRED | 90% coverage gate on `src/` |
| `tests/conftest.py` | REQUIRED | Adds `src/` + `films/` to `sys.path`; without it discovery tests cannot collect |
| `films/sable/mission.py` | REQUIRED | Reference film; discovery + demo + smoke tests depend on it |
| `scripts/00_preflight.py`, `demo_mission.py`, `z_generate_manuscript_variables.py` | REQUIRED | Subprocess smoke tests; token hydration pipeline |
| `manuscript/config.yaml` | REQUIRED | Token source; `load_manuscript_config()` |
