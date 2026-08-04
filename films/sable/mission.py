"""SABLE — the reference film package for BOND-API.

SABLE is the protocol's own smoke film: a real, deterministic
``MissionProvider`` implementation that exercises the full mission lifecycle
with zero external dependencies. Film agents copy this shape; the tests and
``scripts/demo_mission.py`` discover it by slug on ``sys.path``.

Discovery contract (see ``src/bond_api/discovery.py``): a film package is a
top-level module named by its slug exposing ``mission.MissionProvider``.
"""

from __future__ import annotations

from bond_api.protocol import (
    Asset,
    Constraint,
    Debrief,
    Finding,
    MissionBrief,
    MissionOutcome,
    MissionPlan,
    Provenance,
    ReconReport,
    ReconRequest,
    Step,
)

__all__ = ["MissionProvider"]

_PACKAGE_VERSION = "0.1.0"
_SEED = 7


class MissionProvider:  # noqa: N801 — class name is fixed by the discovery contract
    """Deterministic reference implementation of the BOND-API mission protocol."""

    film = "sable"

    def brief(self) -> MissionBrief:
        """Declare the reference mission: contract verification, two objectives."""
        return MissionBrief(
            film=self.film,
            codename="THE PROTOCOL",
            objectives=("verify the frozen contract", "exercise every mission stage"),
            assets=(
                Asset(
                    kind="manifest",
                    name="contract",
                    payload={"version": _PACKAGE_VERSION, "seed": _SEED},
                ),
            ),
            constraints=(Constraint(kind="determinism", detail="no random draws, no external calls"),),
        )

    def recon(self, request: ReconRequest) -> ReconReport:
        """Survey the request, the available asset, and the determinism constraint."""
        return ReconReport(
            findings=(
                Finding(label="goal", detail=request.goal),
                Finding(label="assets", detail="one contract manifest available"),
                Finding(label="constraints", detail="deterministic execution required"),
            )
        )

    def plan(self, brief: MissionBrief) -> MissionPlan:
        """Plan the three deterministic steps: load, execute, verify."""
        return MissionPlan(
            steps=(
                Step(name="contract", action="load_manifest", params={"source": brief.assets[0].name}),
                Step(name="execute", action="run_mission_flow", params={"objectives": len(brief.objectives)}),
                Step(name="verify", action="check_outcome", params={"success": True}),
            )
        )

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        """Run the plan and return a deterministic outcome with full provenance."""
        return MissionOutcome(
            success=True,
            results={
                "steps_completed": len(plan.steps),
                "outputs": tuple(step.name for step in plan.steps),
            },
            provenance=Provenance(
                package_version=_PACKAGE_VERSION,
                seed=_SEED,
                input_hash="sable-reference-input",
                wall_time_s=0.0,
            ),
        )

    def debrief(self, outcome: MissionOutcome) -> Debrief:
        """Summarize the mission and record the protocol's standing lessons."""
        return Debrief(
            outcome=outcome,
            lessons=(
                "the contract is frozen; films must not change it",
                "deterministic provenance is mandatory",
            ),
        )
