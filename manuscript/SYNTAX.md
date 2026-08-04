# Manuscript Syntax (bond-api)

Project-specific overlay on the canonical
[`docs/guides/manuscript-semantics.md`](../../../docs/guides/manuscript-semantics.md) —
read that file first; this file documents the **bond-api**-specific figure
registry, labels, and token table.

## Citations

Use Pandoc bracket syntax:

- `[@pep544]` — parenthetical citation
- `@pep544` — narrative citation

Keys are defined in `references.bib`.

## Figures

The BOND-API manuscript currently defines no figures (Phase 1 is a protocol
package, not a measurement study). If a figure is added, register it here with
its label, path, and generator:

| Label | PNG Filename | Generator |
|---|---|---|
| (none) | — | — |

## Tokens

The authoritative token set is the return value of
`src/bond_api/manuscript_variables.py::generate_variables()`; the live
cross-reference gate is
`tests/test_manuscript_variables.py::test_all_manuscript_tokens_are_generated`.

| Token | Meaning |
|---|---|
| `BOND_IDENTITY` | Package identity (`BOND-API`) |
| `BOND_CODENAME` | Codename (`THE PROTOCOL`) |
| `BOND_VERSION` | Version from `config.yaml` → `paper.version` |
| `BOND_TITLE` / `BOND_SUBTITLE` | Title / subtitle from config |
| `BOND_NUM_DATACLASSES` | Count of frozen protocol dataclasses |
| `BOND_PROTOCOL_DATACLASSES` | Comma-joined dataclass names |
| `BOND_NUM_PROVIDER_METHODS` | Count of provider stages |
| `BOND_PROVIDER_METHODS` | Comma-joined stage names |
| `PYTHON_VERSION` | Interpreter version at generation time |
| `GENERATION_TIMESTAMP` | UTC ISO timestamp at generation time |

## Rules

- No hardcoded metrics in prose — always tokens.
- No literal `{{...}}` text outside real token references.
- Keep `config.yaml` and `config.yaml.example` in sync.
