#!/usr/bin/env python3
"""Thin orchestrator: run a reference mission against a discovered film.

Usage:
    uv run python scripts/demo_mission.py [slug] [--films-dir DIR]

Discovers the film package by slug (default ``sable``, the reference film),
executes the five-stage mission flow, and prints a deterministic debrief plus
the outcome as round-trip JSON.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
FILMS = ROOT / "films"
for _path in (SRC, FILMS):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from bond_api.discovery import load_provider  # noqa: E402
from bond_api.protocol import ReconRequest  # noqa: E402
from bond_api.serialization import to_json  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", nargs="?", default="sable", help="film slug to run (default: sable)")
    parser.add_argument("--films-dir", default=None, help="directory containing film packages")
    args = parser.parse_args()

    films_dir = Path(args.films_dir) if args.films_dir else FILMS
    provider = load_provider(args.slug, search_paths=[films_dir])

    brief = provider.brief()
    report = provider.recon(ReconRequest(goal="survey available assets and constraints"))
    plan = provider.plan(brief)
    outcome = provider.execute(plan)
    debrief = provider.debrief(outcome)

    print(f"Film: {brief.film} ({brief.codename})")
    print(f"Objectives: {', '.join(brief.objectives)}")
    print(f"Recon findings: {len(report.findings)}")
    print(f"Plan steps: {len(plan.steps)}")
    print(f"Outcome success: {outcome.success}")
    print(f"Lessons: {len(debrief.lessons)}")
    print("Outcome JSON:")
    print(to_json(outcome))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
