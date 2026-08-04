"""Smoke tests: the package's thin orchestrator scripts run end-to-end.

Each script is subprocess-invoked with the real interpreter from the package
root — real execution, real files, no mocks.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _run_script(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def test_preflight_reports_identity() -> None:
    result = _run_script("scripts/00_preflight.py")
    assert result.returncode == 0, result.stderr
    assert "BOND-API" in result.stdout
    assert "THE PROTOCOL" in result.stdout
    assert "Protocol dataclasses (11)" in result.stdout


def test_demo_mission_runs_reference_film() -> None:
    result = _run_script("scripts/demo_mission.py")
    assert result.returncode == 0, result.stderr
    assert "Film: sable (THE PROTOCOL)" in result.stdout
    assert "Outcome success: True" in result.stdout
    assert "steps_completed" in result.stdout


def test_demo_mission_prints_valid_outcome_json() -> None:
    result = _run_script("scripts/demo_mission.py")
    json_block = result.stdout.split("Outcome JSON:\n", 1)[1]
    outcome = json.loads(json_block)
    assert outcome["__bond_type__"] == "MissionOutcome"
    assert outcome["success"] is True
    assert outcome["provenance"]["seed"] == 7


def test_demo_mission_unknown_slug_fails_cleanly() -> None:
    result = _run_script("scripts/demo_mission.py", "missing_slug_zzz")
    assert result.returncode != 0
    assert "DiscoveryError" in result.stderr or "not discoverable" in result.stderr


def test_generate_manuscript_variables_writes_artifacts(tmp_path: Path) -> None:
    result = _run_script(
        "scripts/z_generate_manuscript_variables.py",
        "--output-dir",
        str(tmp_path / "out"),
    )
    assert result.returncode == 0, result.stderr

    variables_path = tmp_path / "out" / "data" / "manuscript_variables.json"
    assert variables_path.is_file()
    variables = json.loads(variables_path.read_text(encoding="utf-8"))
    assert variables["BOND_IDENTITY"] == "BOND-API"
    assert variables["BOND_CODENAME"] == "THE PROTOCOL"

    abstract = tmp_path / "out" / "manuscript" / "00_abstract.md"
    assert abstract.is_file()
    text = abstract.read_text(encoding="utf-8")
    assert "{{" not in text
    assert "BOND-API" in text


def test_generate_manuscript_variables_strict_rejects_unresolved(tmp_path: Path) -> None:
    manuscript_dir = tmp_path / "ms"
    manuscript_dir.mkdir()
    (manuscript_dir / "00_abstract.md").write_text(
        "{{BOND_IDENTITY}} {{UNKNOWN_TOKEN}}",
        encoding="utf-8",
    )
    result = _run_script(
        "scripts/z_generate_manuscript_variables.py",
        "--manuscript-dir",
        str(manuscript_dir),
        "--output-dir",
        str(tmp_path / "out"),
    )
    assert result.returncode != 0
    assert "unresolved manuscript tokens" in result.stderr


@pytest.mark.parametrize("script", ["scripts/00_preflight.py", "scripts/demo_mission.py"])
def test_scripts_are_python_files(script: str) -> None:
    """Guard against accidental binary/exemplar leftovers in the scripts dir."""
    source = (ROOT / script).read_text(encoding="utf-8")
    assert "def main()" in source
