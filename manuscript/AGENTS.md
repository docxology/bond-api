---
title: "Manuscript directory: bond-api"
type: "manuscript_guide"
version: "0.1.0"
---

# Manuscript (`projects/working/bond/bond-api/manuscript/`)

Repository-wide agent rules live in
[`../docs/agent_instructions.md`](../docs/agent_instructions.md). This file
covers **manuscript-specific** editing: file roles, the token protocol, and
the section modification workflow.

## File Inventory

| File / Pattern | Role | Tokens |
|---|---|---|
| `00_abstract.md` | Abstract; protocol identity and surface summary | `BOND_IDENTITY`, `BOND_CODENAME`, `BOND_NUM_DATACLASSES`, `BOND_PROTOCOL_DATACLASSES`, `BOND_NUM_PROVIDER_METHODS`, `BOND_PROVIDER_METHODS`, `BOND_VERSION` |
| `01_introduction.md` | Why the protocol exists; package contents; reader's guide | `BOND_NUM_PROVIDER_METHODS`, `BOND_PROVIDER_METHODS` |
| `02_methodology.md` | Lifecycle, frozen dataclasses, provider contract, discovery, serialization, registries | None |
| `03_results.md` | Protocol surface + conformance evidence | `BOND_NUM_DATACLASSES`, `BOND_PROTOCOL_DATACLASSES`, `BOND_NUM_PROVIDER_METHODS`, `BOND_PROVIDER_METHODS` |
| `04_conclusion.md` | What Phase 1 delivers; freeze statement | `BOND_NUM_DATACLASSES`, `BOND_NUM_PROVIDER_METHODS`, `BOND_VERSION` |
| `05_experimental_setup.md` | Layout, configuration, environment, run commands | `BOND_VERSION`, `PYTHON_VERSION`, `GENERATION_TIMESTAMP` |
| `06_reproducibility.md` | Determinism policy, artifact inventory, token hydration | None |
| `07_scope_and_related_work.md` | Out-of-scope, design relationships, related standards | None |
| `99_references.md` | Standards and repository references | None |
| `config.yaml` | Paper metadata + `protocol:` parameters | — |
| `config.yaml.example` | Reference copy for new projects | — |
| `preamble.md` | LaTeX injections shared by PDF output | — |
| `references.bib` | BibTeX bibliography | — |
| `SYNTAX.md` | Citation, figure, and cross-reference syntax reference | — |
| `README.md` | Human quick-reference | — |
| `AGENTS.md` | This file | — |

## Token Protocol

Numeric and identity values that come from code or config **must** use
token syntax. Hardcoding a value that changes when `config.yaml` is edited or
the protocol surface changes is the primary cause of inaccurate manuscripts.

**The token pipeline**:

1. `scripts/z_generate_manuscript_variables.py` calls
   `src/bond_api/manuscript_variables.py::generate_variables()`.
2. `generate_variables()` reads `manuscript/config.yaml` + the live protocol
   surface (`protocol_surface()`).
3. The script writes `output/data/manuscript_variables.json` and resolves
   every `NN_*.md` section into `output/manuscript/` (strict by default:
   unresolved tokens fail).

**Adding a new token**:

1. Add a key/value pair in `generate_variables()`.
2. Reference it in a manuscript file as `{{TOKEN_NAME}}`.
3. `tests/test_manuscript_variables.py::test_all_manuscript_tokens_are_generated`
   fails automatically if a manuscript token is missing from the generator.

**Detecting unresolved tokens** (before rendering):

```bash
rg -n "\{\{[A-Z0-9_]+\}\}" manuscript/[0-9][0-9]_*.md \
  && echo "UNRESOLVED TOKENS — re-run z_generate_manuscript_variables.py" \
  || echo "All tokens resolved"
```

## Section Modification Protocol

1. Update the source of truth first (`src/` code or `manuscript/config.yaml`).
2. Update the relevant section prose, using tokens for any value that comes
   from code or config.
3. Re-run `scripts/z_generate_manuscript_variables.py` (strict) and the token
   cross-reference test.
4. Never hand-edit `output/manuscript/` — regenerate.

## Infrastructure Coupling

Manuscript rendering (Pandoc → PDF) runs through the monorepo
`infrastructure.rendering` pipeline at the template root. This package ships
the token hydration and validation layer only; rendering commands live in the
template's `scripts/pipeline/`.
