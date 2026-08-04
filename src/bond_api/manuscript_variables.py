"""Manuscript variable hydration for BOND-API.

Every ``{{TOKEN}}`` in ``manuscript/*.md`` resolves through
:func:`generate_variables`, which reads ``manuscript/config.yaml`` plus the
frozen protocol surface. Metrics are never hand-authored in prose: they flow
through this module so the manuscript cannot drift from the code.

The consuming orchestrator is ``scripts/z_generate_manuscript_variables.py``
(thin wrapper); the live cross-reference gate lives in
``tests/test_manuscript_variables.py``.
"""

from __future__ import annotations

import platform
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from bond_api.capabilities import CAPABILITY_NAMES
from bond_api.protocol import CODENAME, IDENTITY, protocol_surface

__all__ = ["generate_variables", "load_manuscript_config", "resolve_manuscript_tree"]

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "manuscript" / "config.yaml"

_TOKEN_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")


def load_manuscript_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate ``manuscript/config.yaml`` (or an explicit path)."""
    path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    if not path.is_file():
        raise FileNotFoundError(f"manuscript config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"manuscript config must be a top-level mapping, got {type(data).__name__}")
    return data


def generate_variables(
    *,
    config_path: str | Path | None = None,
    require_outputs: bool = True,
) -> dict[str, str]:
    """Compute the ``{{TOKEN}}`` → value mapping for the manuscript.

    Args:
        config_path: Override for ``manuscript/config.yaml``.
        require_outputs: When True (default), verify the protocol surface is
            non-empty — the strict-mode gate that replaced the exemplar's
            analysis-CSV requirement.
    """
    config = load_manuscript_config(config_path)
    paper = config.get("paper", {})
    if not isinstance(paper, dict):
        raise ValueError("manuscript config 'paper' section must be a mapping")
    surface = protocol_surface()
    if require_outputs and not surface["dataclasses"]:
        raise ValueError("protocol surface is empty — bond_api failed to expose its dataclasses")
    return {
        "BOND_IDENTITY": IDENTITY,
        "BOND_CODENAME": CODENAME,
        "BOND_VERSION": str(paper.get("version", "")),
        "BOND_TITLE": str(paper.get("title", "")),
        "BOND_SUBTITLE": str(paper.get("subtitle", "")),
        "BOND_NUM_DATACLASSES": str(len(surface["dataclasses"])),
        "BOND_PROTOCOL_DATACLASSES": ", ".join(surface["dataclasses"]),
        "BOND_NUM_PROVIDER_METHODS": str(len(surface["provider_methods"])),
        "BOND_PROVIDER_METHODS": ", ".join(surface["provider_methods"]),
        "BOND_NUM_CAPABILITIES": str(len(CAPABILITY_NAMES)),
        "BOND_CAPABILITIES": ", ".join(CAPABILITY_NAMES),
        "PYTHON_VERSION": platform.python_version(),
        "GENERATION_TIMESTAMP": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def resolve_manuscript_tree(
    variables: dict[str, str],
    *,
    manuscript_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    strict: bool = True,
) -> tuple[Path, list[str]]:
    """Copy each manuscript section to ``output/manuscript/``, substituting tokens.

    Only ``NN_*.md`` section files are copied (not sidecars such as
    ``SYNTAX.md``). In strict mode any leftover ``{{TOKEN}}`` fails the
    resolution so the manuscript can never render with raw braces.

    Returns the output directory and the sorted list of resolved file names.
    """
    manuscript_dir = Path(manuscript_dir) if manuscript_dir is not None else PACKAGE_ROOT / "manuscript"
    output_dir = Path(output_dir) if output_dir is not None else PACKAGE_ROOT / "output" / "manuscript"
    resolved: list[str] = []
    for source in sorted(manuscript_dir.glob("[0-9][0-9]_*.md")):
        text = source.read_text(encoding="utf-8")
        for token, value in variables.items():
            text = text.replace("{{" + token + "}}", value)
        unresolved = sorted(set(_TOKEN_RE.findall(text)))
        if unresolved and strict:
            raise ValueError(f"unresolved manuscript tokens in {source.name}: {unresolved}")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / source.name).write_text(text, encoding="utf-8")
        resolved.append(source.name)
    return output_dir, resolved
