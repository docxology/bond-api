# scripts/ Conventions

1. **Thin.** No protocol/discovery/serialization logic in scripts — call
   `src/bond_api/`.
2. **Bootstrap.** Each script inserts `<root>/src` (and `<root>/films` for
   discovery) into `sys.path` before importing `bond_api`. Never rely on the
   caller's cwd.
3. **CLI.** `argparse`; `main() -> int`; `SystemExit(main())` guard.
4. **Deterministic.** Output that tests assert on must be stable (no
   timestamps, no absolute paths in mission output).
5. **Errors.** Let exceptions propagate with their message; scripts are thin —
   no elaborate error handling layers.
