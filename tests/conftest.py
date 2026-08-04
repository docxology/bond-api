"""Pytest configuration for BOND-API tests.

Adds ``src/`` and ``films/`` to ``sys.path`` so tests (and the discovery
contract) can import ``bond_api`` and the reference film by slug. The project
``pyproject.toml`` already lists ``src`` in ``pythonpath``; this conftest makes
the films directory discoverable exactly as a coordinator would.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _relative in ("src", "films"):
    _path = str(ROOT / _relative)
    if _path not in sys.path:
        sys.path.insert(0, _path)
