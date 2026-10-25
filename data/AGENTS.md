# Data Directory — Agent Guide

Versioned project **inputs** only. Pipeline outputs must not be committed
here.

## `claim_ledger.yaml`

Evidence-registry for claims that are intentionally sourced from code,
config, or artifacts rather than token injection.

**This file is gated.** `tests/test_claim_ledger.py` re-derives every row from
the source it cites (live protocol surface, `CAPABILITY_NAMES`, the
`fail_under` gate in `pyproject.toml`, `SERIALIZATION_TAG`, the discovered
reference film) and fails when a declared value disagrees. Adding a row
without adding a verifier also fails, so the gate cannot silently stop
covering the file.

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
2. Re-run the gate that consumes the ledger:
   `uv run --extra dev pytest tests/test_claim_ledger.py -v`.
3. A new row needs a matching entry in that module's `VERIFIERS` map, or the
   coverage check fails.
4. Do not store generated JSON/CSV/PNG under `data/`.

Quick orientation: [`README.md`](README.md).
