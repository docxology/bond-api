---
name: bond-api
description: BOND-API — the frozen mission protocol contract for the BOND film suite (Layer 1, codename THE PROTOCOL).
version: 0.1.0
author: docxology
license: MIT
tags: [bond, protocol, frozen-contract, discovery, serialization]
---

# bond-api

Project-scoped skill for the BOND-API protocol package at
`projects/working/bond/bond-api/`. Load this when working inside the project.

## When to Use

- Working inside `bond-api` — editing source, running scripts, or touching
  the protocol surface.
- Implementing a film package against the contract (`<slug>/mission.py`).
- Verifying that the frozen contract, thin-orchestrator boundary, and
  zero-mock testing discipline still hold after changes.

## Quick Reference

```bash
# From the package directory
uv sync --extra dev
uv run pytest tests/ --cov=src --cov-fail-under=90
uv run ruff check src/ scripts/ films/
uv run mypy src/ scripts/ films/
uv run python scripts/00_preflight.py
uv run python scripts/demo_mission.py
uv run python scripts/z_generate_manuscript_variables.py
```

## Pitfalls

- **The protocol is frozen.** `src/bond_api/protocol.py` fields, defaults,
  and validation must not change casually — changes are versioned
  migrations. This is the contract all 27 film packages code against.
- **Keep scripts thin.** Business logic belongs in `src/bond_api/`, never in
  `scripts/`.
- **No mocks.** Tests must use real data, real files, real computation.
- **No wall clock in generated artifacts.** `generate_variables()` reads no
  clock; regenerating `output/` twice on one interpreter writes identical
  bytes (`tests/test_regeneration_determinism.py`).
- **Deterministic.** `to_json` output is byte-deterministic; no untracked
  random reliance; reference film uses a fixed seed.
- **Discovery binding order.** `load_provider` binds the slug before the
  runtime protocol check, because `film` is part of the checkable surface.
- **`sys.modules` caches slug imports.** Hosting two packages under the same
  slug in different locations requires distinct slugs.
- **Reserved key.** `__bond_type__` is reserved in serialized payloads; use
  the published `bond_api.serialization.SERIALIZATION_TAG` rather than
  retyping the literal.
- **Deepen additively.** New behavior goes in a new module or a new helper
  (as `src/bond_api/capabilities.py` did) — never by editing a frozen field.
- **A gate must be able to fail.** Every check needs an input that makes it
  fail, supplied in a test: assert non-empty scan sets, extract
  always-satisfied validity checks into callables a test can misfeed, and
  make structural claims with `ast` rather than substring greps.
- **No hand-authored metrics.** Manuscript numbers arrive as `{{TOKEN}}`s from
  `manuscript_variables.py` + `config.yaml` + `pyproject.toml`.

## Cross-refs

- Project contract: [`AGENTS.md`](../../../AGENTS.md)
- README: [`README.md`](../../../README.md)
- TODO: [`TODO.md`](../../../TODO.md)
- Agent rules: [`docs/agent_instructions.md`](../../../docs/agent_instructions.md)
