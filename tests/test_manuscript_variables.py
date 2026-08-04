"""Manuscript variable tests: config loading, token map, and live cross-reference.

The live cross-reference gate (``test_all_manuscript_tokens_are_generated``)
scans every manuscript section for ``{{TOKEN}}`` and fails if any token is
missing from :func:`~bond_api.manuscript_variables.generate_variables` — the
same gate that keeps prose from drifting from the code.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from bond_api.manuscript_variables import (
    PACKAGE_ROOT,
    generate_variables,
    load_manuscript_config,
    resolve_manuscript_tree,
)

_TOKEN_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def test_generate_variables_defaults() -> None:
    variables = generate_variables()
    assert variables["BOND_IDENTITY"] == "BOND-API"
    assert variables["BOND_CODENAME"] == "THE PROTOCOL"
    assert variables["BOND_VERSION"] == "0.1.0"
    assert variables["BOND_NUM_DATACLASSES"] == "11"
    assert "Asset" in variables["BOND_PROTOCOL_DATACLASSES"]
    assert variables["BOND_NUM_PROVIDER_METHODS"] == "5"
    assert "brief" in variables["BOND_PROVIDER_METHODS"]
    assert all(isinstance(value, str) for value in variables.values())


def test_all_manuscript_tokens_are_generated() -> None:
    variables = generate_variables()
    used: set[str] = set()
    for section in sorted(PACKAGE_ROOT.glob("manuscript/[0-9][0-9]_*.md")):
        used.update(_TOKEN_RE.findall(section.read_text(encoding="utf-8")))
    assert used, "manuscript sections use no tokens — the gate would be vacuous"
    missing = used - set(variables)
    assert missing == set(), f"manuscript tokens missing from generate_variables(): {sorted(missing)}"


def test_generate_variables_custom_config(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text(
        "paper:\n  title: \"Custom Title\"\n  subtitle: \"Custom Subtitle\"\n  version: \"9.9.9\"\n",
        encoding="utf-8",
    )
    variables = generate_variables(config_path=config)
    assert variables["BOND_TITLE"] == "Custom Title"
    assert variables["BOND_SUBTITLE"] == "Custom Subtitle"
    assert variables["BOND_VERSION"] == "9.9.9"


def test_load_manuscript_config_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_manuscript_config(tmp_path / "nope.yaml")


def test_load_manuscript_config_non_mapping(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text("just a string\n", encoding="utf-8")
    with pytest.raises(ValueError, match="top-level mapping"):
        load_manuscript_config(config)


def test_generate_variables_paper_must_be_mapping(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text("paper: [1, 2]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="'paper' section"):
        generate_variables(config_path=config)


def test_generate_variables_require_outputs_gate() -> None:
    # The strict gate passes when the protocol surface is present (always here);
    # this pins the default so coordinators cannot silently drop it.
    variables = generate_variables(require_outputs=True)
    assert int(variables["BOND_NUM_DATACLASSES"]) >= 11


def test_resolve_manuscript_tree_substitutes(tmp_path: Path) -> None:
    manuscript_dir = tmp_path / "ms"
    manuscript_dir.mkdir()
    (manuscript_dir / "00_abstract.md").write_text(
        "Identity: {{BOND_IDENTITY}} version {{BOND_VERSION}}.",
        encoding="utf-8",
    )
    output_dir, resolved = resolve_manuscript_tree(
        {"BOND_IDENTITY": "BOND-API", "BOND_VERSION": "0.1.0"},
        manuscript_dir=manuscript_dir,
        output_dir=tmp_path / "out",
    )
    assert resolved == ["00_abstract.md"]
    assert (output_dir / "00_abstract.md").read_text(encoding="utf-8") == "Identity: BOND-API version 0.1.0."


def test_resolve_manuscript_tree_strict_rejects_unresolved(tmp_path: Path) -> None:
    manuscript_dir = tmp_path / "ms"
    manuscript_dir.mkdir()
    (manuscript_dir / "00_abstract.md").write_text(
        "{{BOND_IDENTITY}} and {{UNKNOWN_TOKEN}}",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unresolved manuscript tokens"):
        resolve_manuscript_tree(
            {"BOND_IDENTITY": "BOND-API"},
            manuscript_dir=manuscript_dir,
            output_dir=tmp_path / "out",
        )


def test_resolve_manuscript_tree_draft_writes_anyway(tmp_path: Path) -> None:
    manuscript_dir = tmp_path / "ms"
    manuscript_dir.mkdir()
    (manuscript_dir / "00_abstract.md").write_text(
        "{{BOND_IDENTITY}} and {{UNKNOWN_TOKEN}}",
        encoding="utf-8",
    )
    output_dir, _ = resolve_manuscript_tree(
        {"BOND_IDENTITY": "BOND-API"},
        manuscript_dir=manuscript_dir,
        output_dir=tmp_path / "out",
        strict=False,
    )
    text = (output_dir / "00_abstract.md").read_text(encoding="utf-8")
    assert "BOND-API" in text
    assert "{{UNKNOWN_TOKEN}}" in text


def test_resolve_default_manuscript_tree_has_no_leftovers(tmp_path: Path) -> None:
    variables = generate_variables()
    output_dir, resolved = resolve_manuscript_tree(variables, output_dir=tmp_path / "out")
    assert resolved
    for section in output_dir.glob("*.md"):
        assert "{{" not in section.read_text(encoding="utf-8")
