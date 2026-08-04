# Manuscript

The BOND-API protocol manuscript: identity, methodology, conformance
evidence, and reproducibility contract for the frozen mission protocol
(Layer 1 of the BOND suite, codename *THE PROTOCOL*).

## Files

- `00_abstract.md` … `99_references.md` — manuscript sections, token-hydrated
- `config.yaml` — paper metadata + `protocol:` parameters (token source)
- `config.yaml.example` — reference copy for new projects
- `preamble.md` — LaTeX preamble for PDF output
- `references.bib` — BibTeX bibliography
- `SYNTAX.md` — pandoc citation/cross-reference syntax
- `AGENTS.md` — agent rules for this directory

## Quick commands

```bash
# Hydrate tokens (strict) into output/manuscript/ + output/data/manuscript_variables.json
uv run python scripts/z_generate_manuscript_variables.py

# Check for unresolved tokens in the sources
rg -n "\{\{[A-Z0-9_]+\}\}" [0-9][0-9]_*.md || echo "All tokens resolved"
```

See [`docs/agent_instructions.md`](../docs/agent_instructions.md) for the
token protocol and verification checklist.
