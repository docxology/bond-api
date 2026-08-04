"""Discovery tests: slug loading, binding, autodiscovery, and failure modes.

Providers are real film packages written to temporary directories — no mocks.
Unique slugs per test keep ``sys.modules`` isolation deterministic.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bond_api.discovery import DiscoveryError, discover, load_provider
from bond_api.protocol import MissionProvider, ReconRequest, run_mission

FILMS_DIR = Path(__file__).resolve().parents[1] / "films"

_IMPORTS = (
    "from bond_api.protocol import (Asset, Constraint, Debrief, Finding, MissionBrief, "
    "MissionOutcome, MissionPlan, Provenance, ReconReport, ReconRequest, Step)\n"
)

_UNBOUND_PROVIDER = _IMPORTS + '''
class MissionProvider:
    """Deliberately declares no film attribute; discovery must bind it."""

    def brief(self) -> MissionBrief:
        return MissionBrief(film="", codename="UNBOUND", objectives=("o",))

    def recon(self, request: ReconRequest) -> ReconReport:
        return ReconReport(findings=(Finding(label="g", detail=request.goal),))

    def plan(self, brief: MissionBrief) -> MissionPlan:
        return MissionPlan(steps=(Step(name="s", action="a"),))

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        return MissionOutcome(
            success=True,
            results={},
            provenance=Provenance(package_version="0.1.0", seed=1, input_hash="h", wall_time_s=0.0),
        )

    def debrief(self, outcome: MissionOutcome) -> Debrief:
        return Debrief(outcome=outcome, lessons=("ok",))
'''

_MISMATCHED_PROVIDER = _IMPORTS + '''
class MissionProvider:
    film = "other"

    def brief(self) -> MissionBrief:
        return MissionBrief(film=self.film, codename="MISMATCH", objectives=("o",))

    def recon(self, request: ReconRequest) -> ReconReport:
        return ReconReport(findings=(Finding(label="g", detail=request.goal),))

    def plan(self, brief: MissionBrief) -> MissionPlan:
        return MissionPlan(steps=(Step(name="s", action="a"),))

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        return MissionOutcome(
            success=True,
            results={},
            provenance=Provenance(package_version="0.1.0", seed=1, input_hash="h", wall_time_s=0.0),
        )

    def debrief(self, outcome: MissionOutcome) -> Debrief:
        return Debrief(outcome=outcome, lessons=("ok",))
'''

_INCOMPLETE_PROVIDER = _IMPORTS + '''
class MissionProvider:
    film = "incomplete"

    def brief(self) -> MissionBrief:
        return MissionBrief(film=self.film, codename="INCOMPLETE", objectives=("o",))

    # execute() is deliberately missing: protocol violation.
'''

_RISING_PROVIDER = _IMPORTS + '''
class MissionProvider:
    film = "rising"

    def __init__(self) -> None:
        raise RuntimeError("boom")

    def brief(self) -> MissionBrief:
        return MissionBrief(film=self.film, codename="RISING", objectives=("o",))

    def recon(self, request: ReconRequest) -> ReconReport:
        return ReconReport()

    def plan(self, brief: MissionBrief) -> MissionPlan:
        return MissionPlan()

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        return MissionOutcome(
            success=True,
            results={},
            provenance=Provenance(package_version="0.1.0", seed=1, input_hash="h", wall_time_s=0.0),
        )

    def debrief(self, outcome: MissionOutcome) -> Debrief:
        return Debrief(outcome=outcome)
'''

_SLOTTED_PROVIDER = _IMPORTS + '''
class MissionProvider:
    """Slotted: instances cannot be bound to a slug by discovery."""

    __slots__ = ()

    def brief(self) -> MissionBrief:
        return MissionBrief(film="", codename="SLOTTED", objectives=("o",))

    def recon(self, request: ReconRequest) -> ReconReport:
        return ReconReport()

    def plan(self, brief: MissionBrief) -> MissionPlan:
        return MissionPlan()

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        return MissionOutcome(
            success=True,
            results={},
            provenance=Provenance(package_version="0.1.0", seed=1, input_hash="h", wall_time_s=0.0),
        )

    def debrief(self, outcome: MissionOutcome) -> Debrief:
        return Debrief(outcome=outcome)
'''


def _write_film(tmp_path: Path, slug: str, source: str) -> Path:
    films_dir = tmp_path / f"films_{slug}"
    (films_dir / slug).mkdir(parents=True)
    (films_dir / slug / "mission.py").write_text(source, encoding="utf-8")
    return films_dir


def test_load_reference_provider() -> None:
    provider = load_provider("sable", search_paths=[FILMS_DIR])
    assert isinstance(provider, MissionProvider)
    assert provider.film == "sable"
    debrief = run_mission(provider, ReconRequest(goal="smoke"))
    assert debrief.outcome.success is True
    assert debrief.outcome.results["steps_completed"] == 3


def test_load_provider_binds_missing_film(tmp_path: Path) -> None:
    films_dir = _write_film(tmp_path, "zeta", _UNBOUND_PROVIDER)
    provider = load_provider("zeta", search_paths=[films_dir])
    assert provider.film == "zeta"


def test_load_provider_rejects_identity_mismatch(tmp_path: Path) -> None:
    films_dir = _write_film(tmp_path, "eta", _MISMATCHED_PROVIDER)
    with pytest.raises(DiscoveryError, match="declares film 'other'"):
        load_provider("eta", search_paths=[films_dir])


def test_load_provider_missing_module() -> None:
    with pytest.raises(DiscoveryError, match="not discoverable"):
        load_provider("does_not_exist_42", search_paths=[FILMS_DIR])


def test_load_provider_module_without_mission_class(tmp_path: Path) -> None:
    films_dir = _write_film(tmp_path, "iota", "VALUE = 1\n")
    with pytest.raises(DiscoveryError, match="must expose a MissionProvider class"):
        load_provider("iota", search_paths=[films_dir])


def test_load_provider_non_class_mission_provider(tmp_path: Path) -> None:
    films_dir = _write_film(tmp_path, "kappa", 'MissionProvider = "not a class"\n')
    with pytest.raises(DiscoveryError, match="must expose a MissionProvider class"):
        load_provider("kappa", search_paths=[films_dir])


def test_load_provider_protocol_violation(tmp_path: Path) -> None:
    films_dir = _write_film(tmp_path, "lambda", _INCOMPLETE_PROVIDER)
    with pytest.raises(DiscoveryError, match="does not satisfy"):
        load_provider("lambda", search_paths=[films_dir])


def test_load_provider_instantiation_failure(tmp_path: Path) -> None:
    films_dir = _write_film(tmp_path, "mu", _RISING_PROVIDER)
    with pytest.raises(DiscoveryError, match="failed to instantiate"):
        load_provider("mu", search_paths=[films_dir])


def test_load_provider_cannot_bind_slotted_provider(tmp_path: Path) -> None:
    films_dir = _write_film(tmp_path, "xi", _SLOTTED_PROVIDER)
    with pytest.raises(DiscoveryError, match="cannot be bound"):
        load_provider("xi", search_paths=[films_dir])


def test_load_provider_invalid_slugs() -> None:
    for bad in ("", "bad/slug", "with space", "1starts_with_digit", "a.b"):
        with pytest.raises(DiscoveryError, match="invalid film slug"):
            load_provider(bad, search_paths=[FILMS_DIR])


def test_load_provider_nonexistent_search_path(tmp_path: Path) -> None:
    with pytest.raises(DiscoveryError, match="search path"):
        load_provider("sable", search_paths=[tmp_path / "nope"])


def test_discover_autodiscovery_finds_reference_film() -> None:
    providers = discover(search_paths=[FILMS_DIR])
    assert set(providers) == {"sable"}
    assert isinstance(providers["sable"], MissionProvider)


def test_discover_default_sys_path_finds_reference_film() -> None:
    providers = discover()
    assert "sable" in providers


def test_discover_explicit_slugs_skip_failures() -> None:
    providers = discover(slugs=["sable", "missing_zzz_42"], search_paths=[FILMS_DIR])
    assert set(providers) == {"sable"}


def test_discover_binds_and_collects_tmp_films(tmp_path: Path) -> None:
    films_dir = _write_film(tmp_path, "nu", _UNBOUND_PROVIDER)
    providers = discover(slugs=["nu"], search_paths=[films_dir])
    assert set(providers) == {"nu"}
    assert providers["nu"].film == "nu"


def test_discover_nonexistent_search_path() -> None:
    with pytest.raises(DiscoveryError, match="search path"):
        discover(search_paths=["/definitely/not/a/real/dir_xyz"])
