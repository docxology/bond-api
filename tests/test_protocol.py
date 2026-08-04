"""Protocol contract tests: frozen dataclasses, invariants, provider protocol.

Every assertion uses real values and real computation — no mocks. The
invariants exercised here are the same checks films hit at construction time,
so a film that passes these guarantees interoperates with every coordinator.
"""

from __future__ import annotations

import dataclasses
from typing import Any

import pytest

from bond_api.protocol import (
    Asset,
    CODENAME,
    Constraint,
    Debrief,
    Finding,
    IDENTITY,
    MISSION_FLOW,
    MissionBrief,
    MissionOutcome,
    MissionPlan,
    MissionProvider,
    Provenance,
    ReconReport,
    ReconRequest,
    Step,
    protocol_surface,
    run_mission,
)

DATACLASS_NAMES = (
    "Asset",
    "Constraint",
    "Debrief",
    "Finding",
    "MissionBrief",
    "MissionOutcome",
    "MissionPlan",
    "Provenance",
    "ReconReport",
    "ReconRequest",
    "Step",
)


def make_provenance(**overrides: Any) -> Provenance:
    base = {"package_version": "0.1.0", "seed": 7, "input_hash": "abc123", "wall_time_s": 0.25}
    base.update(overrides)
    return Provenance(**base)


def make_brief(**overrides: Any) -> MissionBrief:
    base = {
        "film": "sable",
        "codename": "SMOKE",
        "objectives": ("objective one", "objective two"),
        "assets": (Asset(kind="manifest", name="contract", payload={"k": 1}),),
        "constraints": (Constraint(kind="determinism", detail="no draws"),),
    }
    base.update(overrides)
    return MissionBrief(**base)


def make_outcome(**overrides: Any) -> MissionOutcome:
    base = {"success": True, "results": {"steps": 3}, "provenance": make_provenance()}
    base.update(overrides)
    return MissionOutcome(**base)


class ScriptedProvider:
    """A real, deterministic provider that records the order of stage calls."""

    film = "scripted"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def brief(self) -> MissionBrief:
        self.calls.append("brief")
        return make_brief(film=self.film, codename="SCRIPTED")

    def recon(self, request: ReconRequest) -> ReconReport:
        self.calls.append("recon")
        return ReconReport(findings=(Finding(label="goal", detail=request.goal),))

    def plan(self, brief: MissionBrief) -> MissionPlan:
        self.calls.append("plan")
        return MissionPlan(steps=(Step(name="step", action="act"),))

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        self.calls.append("execute")
        return MissionOutcome(success=True, results={"steps": len(plan.steps)}, provenance=make_provenance())

    def debrief(self, outcome: MissionOutcome) -> Debrief:
        self.calls.append("debrief")
        return Debrief(outcome=outcome, lessons=("done",))


class MissingExecuteProvider:
    """Deliberately violates the protocol: no ``execute`` stage."""

    film = "broken"

    def brief(self) -> MissionBrief:
        return make_brief()

    def recon(self, request: ReconRequest) -> ReconReport:
        return ReconReport()

    def plan(self, brief: MissionBrief) -> MissionPlan:
        return MissionPlan()

    def debrief(self, outcome: MissionOutcome) -> Debrief:
        return Debrief(outcome=outcome)


def test_identity_constants() -> None:
    assert IDENTITY == "BOND-API"
    assert CODENAME == "THE PROTOCOL"


def test_all_protocol_dataclasses_are_frozen() -> None:
    instances: list[object] = [
        Asset(kind="k", name="n"),
        Constraint(kind="k", detail="d"),
        Finding(label="l", detail="d"),
        Step(name="n", action="a"),
        ReconRequest(goal="g"),
        ReconReport(findings=(Finding(label="l", detail="d"),)),
        make_brief(),
        MissionPlan(steps=(Step(name="n", action="a"),)),
        make_provenance(),
        make_outcome(),
        Debrief(outcome=make_outcome(), lessons=("l",)),
    ]
    for instance in instances:
        assert dataclasses.is_dataclass(instance)
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(instance, dataclasses.fields(instance)[0].name, "mutated")


def test_brief_requires_non_empty_film() -> None:
    with pytest.raises(ValueError):
        make_brief(film="")


def test_brief_requires_non_empty_codename() -> None:
    with pytest.raises(ValueError):
        make_brief(codename="  ")


def test_brief_requires_non_empty_objectives() -> None:
    with pytest.raises(ValueError):
        make_brief(objectives=())


def test_brief_objectives_entries_must_be_non_empty_strings() -> None:
    with pytest.raises(ValueError):
        make_brief(objectives=("fine", ""))


def test_brief_assets_must_be_tuple_of_asset() -> None:
    with pytest.raises(ValueError):
        make_brief(assets=[Asset(kind="k", name="n")])
    with pytest.raises(ValueError):
        make_brief(assets=("not an asset",))


def test_brief_constraints_must_be_tuple_of_constraint() -> None:
    with pytest.raises(ValueError):
        make_brief(constraints=[Constraint(kind="k", detail="d")])
    with pytest.raises(ValueError):
        make_brief(constraints=("nope",))


def test_asset_invariants() -> None:
    with pytest.raises(ValueError):
        Asset(kind="", name="n")
    with pytest.raises(ValueError):
        Asset(kind="k", name=" ")
    assert Asset(kind="k", name="n").payload is None


def test_constraint_requires_kind() -> None:
    with pytest.raises(ValueError):
        Constraint(kind="", detail="d")


def test_finding_requires_label() -> None:
    with pytest.raises(ValueError):
        Finding(label="", detail="d")


def test_step_invariants() -> None:
    with pytest.raises(ValueError):
        Step(name="", action="a")
    with pytest.raises(ValueError):
        Step(name="n", action="")
    with pytest.raises(ValueError):
        Step(name="n", action="a", params=[("k", 1)])
    step = Step(name="n", action="a")
    assert step.params == {}
    assert Step(name="n", action="a") == Step(name="n", action="a")


def test_recon_request_requires_goal() -> None:
    with pytest.raises(ValueError):
        ReconRequest(goal="")


def test_recon_report_findings_must_be_tuple_of_finding() -> None:
    with pytest.raises(ValueError):
        ReconReport(findings=[Finding(label="l", detail="d")])
    with pytest.raises(ValueError):
        ReconReport(findings=("bad",))
    assert ReconReport().findings == ()


def test_mission_plan_steps_must_be_tuple_of_step() -> None:
    with pytest.raises(ValueError):
        MissionPlan(steps=[Step(name="n", action="a")])
    assert MissionPlan().steps == ()


def test_provenance_invariants() -> None:
    with pytest.raises(ValueError):
        make_provenance(package_version="")
    with pytest.raises(ValueError):
        make_provenance(seed=-1)
    with pytest.raises(ValueError):
        make_provenance(seed=1.5)
    with pytest.raises(ValueError):
        make_provenance(seed=True)
    with pytest.raises(ValueError):
        make_provenance(input_hash="")
    with pytest.raises(ValueError):
        make_provenance(wall_time_s=-0.1)


def test_outcome_invariants() -> None:
    with pytest.raises(ValueError):
        make_outcome(success="yes")
    with pytest.raises(ValueError):
        make_outcome(results=[])
    with pytest.raises(ValueError):
        make_outcome(provenance="not a provenance")


def test_debrief_invariants() -> None:
    with pytest.raises(ValueError):
        Debrief(outcome="nope")
    with pytest.raises(ValueError):
        Debrief(outcome=make_outcome(), lessons=["a", ""])
    with pytest.raises(ValueError):
        Debrief(outcome=make_outcome(), lessons=("ok", "nope", 3))


def test_equality_and_hash() -> None:
    assert make_brief() == make_brief()
    assert make_brief(objectives=("different",)) != make_brief()
    # Hashability follows Python's rules: objects whose fields are all
    # hashable are hashable (Provenance); objects carrying mutable payloads
    # (dicts in Asset.payload) are not.
    assert hash(make_provenance()) == hash(make_provenance())
    assert hash(Asset(kind="k", name="n", payload=None)) == hash(Asset(kind="k", name="n", payload=None))
    with pytest.raises(TypeError):
        hash(make_brief())


def test_mission_provider_runtime_checkable() -> None:
    assert isinstance(ScriptedProvider(), MissionProvider)
    assert not isinstance(MissingExecuteProvider(), MissionProvider)


def test_run_mission_end_to_end() -> None:
    provider = ScriptedProvider()
    debrief = run_mission(provider, ReconRequest(goal="go"))
    assert provider.calls == ["brief", "recon", "plan", "execute", "debrief"]
    assert debrief.outcome.success is True
    assert debrief.outcome.provenance.seed == 7
    assert debrief.lessons == ("done",)
    assert debrief.outcome.results["steps"] == 1


def test_protocol_surface_is_complete() -> None:
    surface = protocol_surface()
    assert surface["identity"] == "BOND-API"
    assert surface["codename"] == "THE PROTOCOL"
    assert surface["dataclasses"] == DATACLASS_NAMES
    assert surface["provider_methods"] == MISSION_FLOW
    assert MISSION_FLOW == ("brief", "recon", "plan", "execute", "debrief")
