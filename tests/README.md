# tests/

Zero-mock test suite for BOND-API. Covers the frozen protocol invariants,
exact JSON round-trips, registries, slug-based discovery (with real film
packages), manuscript token hydration, and script smoke runs.

```bash
uv run --extra dev pytest tests/ --cov=src --cov-fail-under=90
```

See [`AGENTS.md`](AGENTS.md) for the inventory and conventions.
