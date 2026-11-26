# Standalone Guide

## Identity

BOND-API — the frozen mission protocol contract for the BOND film suite
(Layer 1, codename *THE PROTOCOL*). Version `0.1.0`.

This package ships as `docxology/bond-api` — the canonical `origin` — with
citation sidecars (`CITATION.cff`, `.zenodo.json`, `codemeta.json`) in place.
Push to `origin`; never force-push and never rewrite history.

## Lineage

Scaffolded in Phase 0 from the template's code-project exemplar; Phase 1
replaced the exemplar optimization core with the mission protocol package
described here. No exemplar artifacts remain (see `git log` for the phase-0
scaffold commit).

## What this package is for

- Films (the 27 BOND film packages) implement `mission.MissionProvider`.
- Coordinators/orchestrators discover providers and move mission artifacts
  with `to_json`/`from_json`.
- The protocol is frozen: change it only through a versioned migration.

Use the [runbook](runbook.md) to verify this package and build its manuscript.
