# .agents

Per-folder technical reference for the project-local agent scaffolding.

| Subdirectory | Purpose |
| --- | --- |
| [`skills/`](skills/AGENTS.md) | Project-local skills. Each ships `SKILL.md` with YAML frontmatter. |

## When to update

- A new skill specific to this package lands → add a folder under
  `skills/<name>/` with `SKILL.md`, `AGENTS.md`, `README.md`.

The project-level skill for BOND-API lives at
[`skills/bond-api/SKILL.md`](skills/bond-api/SKILL.md) — load it when working
inside this package; it carries when-to-use guidance, quick reference
commands, and pitfalls. The package operating contract is
[`../AGENTS.md`](../AGENTS.md).
