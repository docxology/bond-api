# Data Directory — Agent Guide

Versioned project **inputs** only. Pipeline outputs must not be committed
here.

## `claim_ledger.yaml`

Evidence-registry for claims that are intentionally sourced from code,
config, or artifacts rather than token injection.

### Schema (preserve when adding rows)

| Field | Purpose |
| --- | --- |
| `claim_id` | Stable identifier |
| `kind` | Claim category (`number` / `string`) |
| `value` | Declared value |
| `source` | Provenance (module, config, artifact) |
| `source_tier` | Trust tier for validation |
| `freshness` | Staleness policy |
| `artifact_path` | Optional path to backing file |

## Edit protocol

1. Edit only when source-backed claims change.
2. Re-run evidence validation / pipeline stages that consume the ledger.
3. Do not store generated JSON/CSV/PNG under `data/`.

Quick orientation: [`README.md`](README.md).
