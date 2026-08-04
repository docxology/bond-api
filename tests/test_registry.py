"""Registry tests: gadget add/drop/lookup and mission provider registration.

Providers used here are real classes implementing the protocol (or plain
objects carrying a ``film`` attribute) — never mocks.
"""

from __future__ import annotations

from typing import Any

import pytest

from bond_api.protocol import (
    Asset,
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
from bond_api.registry import GadgetRegistry, MissionRegistry


class Provider:
    """A real, minimal provider; film set at construction."""

    def __init__(self, film: str) -> None:
        self.film = film

    def brief(self) -> MissionBrief:
        return MissionBrief(film=self.film, codename="TEST", objectives=("o",))

    def recon(self, request: ReconRequest) -> ReconReport:
        return ReconReport(findings=(Finding(label="g", detail=request.goal),))

    def plan(self, brief: MissionBrief) -> MissionPlan:
        return MissionPlan(steps=(Step(name="s", action="a"),))

    def execute(self, plan: MissionPlan) -> MissionOutcome:
        return MissionOutcome(
            success=True,
            results={"steps": len(plan.steps)},
            provenance=Provenance(package_version="0.1.0", seed=1, input_hash="h", wall_time_s=0.0),
        )

    def debrief(self, outcome: MissionOutcome) -> Debrief:
        return Debrief(outcome=outcome, lessons=("ok",))


def test_gadget_register_and_lookup() -> None:
    registry = GadgetRegistry()
    payload: dict[str, Any] = {"a": 1}
    registry.register("alpha", {"grapple": payload})
    assert registry.lookup("alpha", "grapple") is payload


def test_gadget_register_merges_across_calls() -> None:
    registry = GadgetRegistry()
    registry.register("alpha", {"one": 1})
    registry.register("alpha", {"two": 2})
    assert registry.lookup("alpha", "one") == 1
    assert registry.lookup("alpha", "two") == 2


def test_gadget_register_overwrites_same_name() -> None:
    registry = GadgetRegistry()
    registry.register("alpha", {"g": "old"})
    registry.register("alpha", {"g": "new"})
    assert registry.lookup("alpha", "g") == "new"


def test_gadget_lookup_missing_film_raises() -> None:
    registry = GadgetRegistry()
    with pytest.raises(KeyError, match="no gadgets registered for film"):
        registry.lookup("nope", "g")


def test_gadget_lookup_missing_gadget_raises() -> None:
    registry = GadgetRegistry()
    registry.register("alpha", {"one": 1})
    with pytest.raises(KeyError, match="no gadget 'two'"):
        registry.lookup("alpha", "two")


def test_gadget_drop_and_drop_film() -> None:
    registry = GadgetRegistry()
    registry.register("alpha", {"one": 1, "two": 2})
    registry.drop("alpha", "one")
    assert registry.gadgets_for("alpha") == ("two",)
    registry.drop_film("alpha")
    assert registry.films() == ()
    with pytest.raises(KeyError):
        registry.lookup("alpha", "two")


def test_gadget_drop_missing_raises() -> None:
    registry = GadgetRegistry()
    with pytest.raises(KeyError, match="no gadgets registered for film"):
        registry.drop("nope", "g")
    registry.register("alpha", {"one": 1})
    with pytest.raises(KeyError, match="no gadget 'two'"):
        registry.drop("alpha", "two")


def test_gadget_drop_last_gadget_removes_film() -> None:
    registry = GadgetRegistry()
    registry.register("alpha", {"only": 1})
    registry.drop("alpha", "only")
    assert registry.films() == ()
    with pytest.raises(KeyError):
        registry.drop_film("alpha")


def test_gadget_films_order_and_contains() -> None:
    registry = GadgetRegistry()
    registry.register("beta", {"b": 2})
    registry.register("alpha", {"a": 1})
    registry.register("gamma", {"c": 3})
    assert registry.films() == ("beta", "alpha", "gamma")
    assert registry.gadgets_for("beta") == ("b",)
    assert registry.gadgets_for("unknown") == ()
    assert registry.contains("alpha", "a") is True
    assert registry.contains("alpha", "zz") is False
    assert "alpha" in registry
    assert "nope" not in registry
    assert len(registry) == 3


def test_gadget_register_validation() -> None:
    registry = GadgetRegistry()
    with pytest.raises(ValueError):
        registry.register("", {"g": 1})
    with pytest.raises(ValueError):
        registry.register("   ", {"g": 1})
    with pytest.raises(ValueError):
        registry.register("alpha", [("g", 1)])


def test_mission_register_and_lookup() -> None:
    registry = MissionRegistry()
    provider = Provider("alpha")
    registry.register(provider)
    assert registry.lookup("alpha") is provider


def test_mission_lookup_missing_raises() -> None:
    registry = MissionRegistry()
    with pytest.raises(KeyError, match="no mission provider registered for slug"):
        registry.lookup("nope")


def test_mission_drop_and_missing_drop() -> None:
    registry = MissionRegistry()
    registry.register(Provider("alpha"))
    registry.drop("alpha")
    assert registry.slugs() == ()
    with pytest.raises(KeyError):
        registry.lookup("alpha")
    with pytest.raises(KeyError, match="no mission provider registered for slug"):
        registry.drop("alpha")


def test_mission_order_len_iter_contains() -> None:
    registry = MissionRegistry()
    alpha = Provider("alpha")
    beta = Provider("beta")
    registry.register(alpha)
    registry.register(beta)
    assert registry.slugs() == ("alpha", "beta")
    assert registry.providers() == (alpha, beta)
    assert len(registry) == 2
    assert list(registry) == [alpha, beta]
    assert "alpha" in registry
    assert "nope" not in registry


def test_mission_register_overwrites() -> None:
    registry = MissionRegistry()
    registry.register(Provider("alpha"))
    replacement = Provider("alpha")
    registry.register(replacement)
    assert registry.lookup("alpha") is replacement
    assert len(registry) == 1


def test_mission_register_requires_film() -> None:
    registry = MissionRegistry()
    with pytest.raises(ValueError, match="provider.film"):
        registry.register(Provider(""))
    with pytest.raises(ValueError, match="provider.film"):
        registry.register(object())  # type: ignore[arg-type]


def test_mission_register_all() -> None:
    registry = MissionRegistry()
    providers = {"a": Provider("a"), "b": Provider("b")}
    registry.register_all(providers)
    assert registry.slugs() == ("a", "b")
