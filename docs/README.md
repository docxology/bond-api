# docs/ — Agent-Facing Documentation Hub

Technical guide for `projects/working/bond/bond-api/docs/` — the operational
rulebook for agents and developers working inside the BOND-API protocol
package.

## File Inventory

| File | Purpose |
|---|---|
| `README.md` | This index |
| `AGENTS.md` | Technical overview of the docs directory |
| `agent_instructions.md` | Behavioral constraints for agents (read-first) |
| `architecture.md` | Layer boundaries: protocol core, services, films, scripts |
| `testing_philosophy.md` | Zero-mock policy, coverage mechanics, test inventory |

## Reading Order

1. `agent_instructions.md` — start here; 6 hard rules + verification checklist.
2. `architecture.md` — layer boundaries before touching `src/` or `scripts/`.
3. `testing_philosophy.md` — zero-mock constraint before writing tests.

## Verification Commands

```bash
# Tests + coverage ≥90% line + branch on src/
uv run pytest tests/ --cov=src --cov-fail-under=90 -q

# No mocks in tests/
grep -r "unittest.mock\|MagicMock\|@patch\|create_autospec" tests/ || echo "Clean"

# Pure core is infrastructure-free
grep -nE "^(from|import) infrastructure" src/bond_api/*.py || echo "Clean"
```
