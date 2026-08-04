#!/usr/bin/env python3
"""Thin orchestrator: verify the bond_api environment.

Usage:
    uv run python scripts/00_preflight.py

Exits 0 when the protocol package imports and its surface is intact.
"""

from __future__ import annotations

import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bond_api import __version__  # noqa: E402
from bond_api.protocol import CODENAME, IDENTITY, protocol_surface  # noqa: E402


def main() -> int:
    surface = protocol_surface()
    print(f"bond_api {__version__} — {IDENTITY}, codename {CODENAME}")
    print(f"Python {platform.python_version()} on {platform.platform()}")
    print(f"Protocol dataclasses ({len(surface['dataclasses'])}): {', '.join(surface['dataclasses'])}")
    print(f"Provider flow: {' -> '.join(surface['provider_methods'])}")
    if not surface["dataclasses"]:
        print("ERROR: protocol surface is empty", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
