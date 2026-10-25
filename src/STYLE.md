# src/ Style Guide

Short style rules for `src/bond_api/` (see `../../docs/agent_instructions.md`
for the full operating contract).

1. **Pure core first.** `protocol.py`, `registry.py`, `discovery.py`,
   `serialization.py` are stdlib-only. `manuscript_variables.py` may use
   `pyyaml` for config parsing and nothing else third-party.
2. **Type hints + docstrings everywhere.** Mypy-clean (`uv run --extra dev mypy src/`).
3. **Explicit errors.** Validation raises `ValueError` with actionable
   messages; discovery raises `DiscoveryError`; serialization raises
   `SerializationError`. Never bare `assert` for input validation.
4. **Deterministic.** No random draws; no hidden state; `to_json` output is
   byte-deterministic.
5. **Public surface in `__init__.py`.** Keep `__all__` in sync; don't export
   private helpers.
6. **Frozen contract.** `protocol.py` field changes are versioned migrations,
   never silent edits.
7. **Formatting.** Ruff format (88-col default alignment as configured by the
   template); `uv run --extra dev ruff check src/` clean.
