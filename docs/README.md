# docs/ — Agent-Facing Documentation Hub

Technical guide for `projects/working/bond/bond-api/docs/` — the operational
rulebook for agents and developers working inside BOND-API, the frozen mission
protocol contract (Layer 1 of the BOND suite, codename *THE PROTOCOL*).

These documents are this package's rules, not general advice. Where they
disagree with habit, they win; where they disagree with the code, either the
code or the doc is wrong — fix one of them in the same change.

## File Inventory

| File | Purpose |
|---|---|
| `README.md` | This index |
| `AGENTS.md` | Technical overview of the docs directory + the REQUIRED/AESTHETIC map |
| `agent_instructions.md` | The seven hard rules for agents, the token map, and the verification checklist (read-first) |
| `architecture.md` | Module-by-module architecture of `src/bond_api/`, the layer boundaries, and how `films/sable/mission.py` implements the contract |
| `testing_philosophy.md` | Zero-mock policy, coverage mechanics, non-vacuous gate discipline, test inventory |

## Reading Order

1. `agent_instructions.md` — start here: seven rules, the token map, and the
   verification checklist you must run before claiming done.
2. `architecture.md` — what each module in `src/bond_api/` computes and where
   new logic is allowed to live, before touching `src/` or `scripts/`.
3. `testing_philosophy.md` — the zero-mock constraint and the "a gate must be
   able to fail" discipline, before writing tests.

## Where the rest of the documentation lives

| Question | File |
|---|---|
| How do I run this package? | [`../README.md`](../README.md) |
| What is the operating contract for this repo? | [`../AGENTS.md`](../AGENTS.md) |
| What is still outstanding? | [`../TODO.md`](../TODO.md) |
| How do I edit the manuscript? | [`../manuscript/AGENTS.md`](../manuscript/AGENTS.md) |
| How do I lift this package standalone? | [`../STANDALONE.md`](../STANDALONE.md) |

## Verification Commands

```bash
# Tests + the enforced coverage gate (line + branch on src/)
uv run pytest tests/ --cov=src --cov-fail-under=90 -q

# No mocks in tests/
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo "Clean"

# Pure core is infrastructure-free
grep -nE "^(from|import) infrastructure" src/bond_api/*.py || echo "Clean"

# Lint + types
uv run ruff check src/ scripts/ films/ tests/
uv run ruff format --check src/ scripts/ films/ tests/
uv run mypy src/ scripts/ films/

# Manuscript tokens hydrate strictly (an unresolved token exits non-zero)
uv run python scripts/z_generate_manuscript_variables.py
```
