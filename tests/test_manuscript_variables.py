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
    read_coverage_floor,
    require_surface,
    resolve_manuscript_tree,
)
from bond_api.protocol import protocol_surface
from bond_api.serialization import SERIALIZATION_TAG

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
    assert variables["BOND_NUM_CAPABILITIES"] == "9"
    assert "validate_brief" in variables["BOND_CAPABILITIES"]
    assert "fingerprint" in variables["BOND_CAPABILITIES"]
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
        'paper:\n  title: "Custom Title"\n  subtitle: "Custom Subtitle"\n  version: "9.9.9"\n',
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
    # this pins the default so coordinators cannot silently drop it. The gate's
    # positive control — that it actually fires — is the next two tests.
    variables = generate_variables(require_outputs=True)
    assert int(variables["BOND_NUM_DATACLASSES"]) >= 11


def test_require_surface_accepts_the_live_surface() -> None:
    require_surface(dict(protocol_surface()))


@pytest.mark.parametrize("surface", [{}, {"dataclasses": ()}, {"dataclasses": []}])
def test_require_surface_rejects_empty_surface(surface: dict[str, object]) -> None:
    """Positive control: the empty-surface gate fires on a genuinely empty surface."""
    with pytest.raises(ValueError, match="protocol surface is empty"):
        require_surface(surface)


def test_generate_variables_rejects_non_mapping_protocol_section(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text('paper:\n  version: "1.0"\nprotocol: [1, 2]\n', encoding="utf-8")
    with pytest.raises(ValueError, match="'protocol' section"):
        generate_variables(config_path=config)


def test_protocol_tokens_come_from_config_and_code() -> None:
    variables = generate_variables()
    assert variables["BOND_REFERENCE_FILM"] == "sable"
    assert variables["BOND_NUM_FILMS"] == "27"
    assert variables["BOND_SERIALIZATION_TAG"] == SERIALIZATION_TAG


def test_config_serialization_tag_matches_code() -> None:
    """The declared wire tag and the live constant must not drift apart."""
    protocol_config = load_manuscript_config()["protocol"]
    assert protocol_config["serialization_tag"] == SERIALIZATION_TAG


def test_coverage_floor_token_matches_the_enforced_gate() -> None:
    floor = read_coverage_floor()
    assert floor == 90
    pyproject = (PACKAGE_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert f"fail_under = {floor}" in pyproject
    assert generate_variables()["BOND_COVERAGE_FLOOR"] == str(floor)


def test_read_coverage_floor_custom_file(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.coverage.report]\nfail_under = 77\n", encoding="utf-8")
    assert read_coverage_floor(pyproject) == 77
    assert generate_variables(pyproject_path=pyproject)["BOND_COVERAGE_FLOOR"] == "77"


def test_read_coverage_floor_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_coverage_floor(tmp_path / "nope.toml")


def test_read_coverage_floor_missing_declaration(tmp_path: Path) -> None:
    """A pyproject with no gate is an error, never a silently substituted default."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[tool.coverage.report]\nshow_missing = true\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no 'fail_under' coverage gate"):
        read_coverage_floor(pyproject)


def test_resolve_manuscript_tree_strict_rejects_empty_section_set(tmp_path: Path) -> None:
    """An empty scan set would make the unresolved-token gate vacuous."""
    manuscript_dir = tmp_path / "ms"
    manuscript_dir.mkdir()
    (manuscript_dir / "SYNTAX.md").write_text("not a numbered section", encoding="utf-8")
    with pytest.raises(ValueError, match="no manuscript sections"):
        resolve_manuscript_tree(
            {"BOND_IDENTITY": "BOND-API"},
            manuscript_dir=manuscript_dir,
            output_dir=tmp_path / "out",
        )
    assert not (tmp_path / "out").exists()


def test_resolve_manuscript_tree_draft_tolerates_empty_section_set(tmp_path: Path) -> None:
    manuscript_dir = tmp_path / "ms"
    manuscript_dir.mkdir()
    _output_dir, resolved = resolve_manuscript_tree(
        {"BOND_IDENTITY": "BOND-API"},
        manuscript_dir=manuscript_dir,
        output_dir=tmp_path / "out",
        strict=False,
    )
    assert resolved == []


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


def test_generate_variables_without_surface_gate() -> None:
    """``require_outputs=False`` skips the gate but still produces the full map."""
    variables = generate_variables(require_outputs=False)
    assert variables["BOND_IDENTITY"] == "BOND-API"
    assert set(variables) == set(generate_variables(require_outputs=True))
