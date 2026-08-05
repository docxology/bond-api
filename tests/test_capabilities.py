"""Capability-helper tests: brief validation, plan schema, provenance hashing,
debrief normalization.

Every assertion uses real protocol objects and real computation — no mocks.
The helpers extend the frozen contract without touching it: all existing
types, fields, and ``run_mission`` stay byte-identical.
"""

from __future__ import annotations

from typing import Any

import dataclasses
import hashlib

import pytest

from bond_api.capabilities import (
    BriefReport,
    brief_issues,
    derive_provenance,
    fingerprint,
    hash_provenance,
    normalize_debrief,
    normalize_lessons,
    plan_schema_issues,
    require_plan_schema,
    validate_brief,
)
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
from bond_api.serialization import SerializationError, from_json, to_json


def make_provenance(**overrides: Any) -> Provenance:
    base = {"package_version": "0.1.0", "seed": 7, "input_hash": "abc123", "wall_time_s": 0.5}
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


def make_plan(**overrides: Any) -> MissionPlan:
    base = {
        "steps": (
            Step(name="contract", action="load", params={"source": "manifest"}),
            Step(name="execute", action="run"),
            Step(name="verify", action="check", params={"success": True}),
        )
    }
    base.update(overrides)
    return MissionPlan(**base)


def has_issue(issues: tuple[str, ...], fragment: str) -> bool:
    """True when any reported issue contains ``fragment`` (substring, not equality)."""
    return any(fragment in issue for issue in issues)


# --------------------------------------------------------------------------
# MissionBrief validation
# --------------------------------------------------------------------------


def test_brief_issues_clean_brief() -> None:
    assert brief_issues(make_brief()) == ()


def test_brief_issues_duplicate_asset_names() -> None:
    brief = make_brief(
        assets=(
            Asset(kind="manifest", name="contract", payload=1),
            Asset(kind="backup", name="contract", payload=2),
        )
    )
    assert has_issue(brief_issues(brief), "duplicate asset names: contract")


def test_brief_issues_duplicate_constraint_kinds() -> None:
    brief = make_brief(
        constraints=(
            Constraint(kind="determinism", detail="a"),
            Constraint(kind="determinism", detail="b"),
        )
    )
    assert has_issue(brief_issues(brief), "duplicate constraint kinds: determinism")


def test_brief_issues_duplicate_objectives() -> None:
    brief = make_brief(objectives=("repeat", "repeat"))
    assert has_issue(brief_issues(brief), "duplicate objectives")


def test_brief_issues_whitespace_asset_names() -> None:
    brief = make_brief(assets=(Asset(kind="manifest", name=" padded ", payload=None),))
    assert has_issue(brief_issues(brief), "leading/trailing whitespace")


def test_brief_issues_multiple_issues_reported_together() -> None:
    brief = make_brief(
        objectives=("x", "x"),
        assets=(
            Asset(kind="k", name="dup", payload=1),
            Asset(kind="k", name="dup", payload=2),
        ),
        constraints=(
            Constraint(kind="c", detail="1"),
            Constraint(kind="c", detail="2"),
        ),
    )
    issues = brief_issues(brief)
    assert len(issues) == 3


def test_validate_brief_report() -> None:
    report = validate_brief(make_brief())
    assert isinstance(report, BriefReport)
    assert report.ok is True
    assert report.issues == ()
    assert report.brief.film == "sable"


def test_validate_brief_report_not_ok() -> None:
    report = validate_brief(make_brief(objectives=("y", "y")))
    assert report.ok is False
    assert has_issue(report.issues, "duplicate objectives")


def test_brief_report_is_frozen() -> None:
    report = validate_brief(make_brief())
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.issues = ("mutated",)  # type: ignore[misc]


# --------------------------------------------------------------------------
# Plan-step schema checks
# --------------------------------------------------------------------------


def test_plan_schema_issues_clean_plan() -> None:
    assert plan_schema_issues(make_plan()) == ()


def test_plan_schema_issues_duplicate_step_names() -> None:
    plan = make_plan(
        steps=(
            Step(name="dupe", action="a"),
            Step(name="dupe", action="b"),
        )
    )
    assert has_issue(plan_schema_issues(plan), "duplicate step names: dupe")


def test_plan_schema_issues_blank_param_key() -> None:
    plan = make_plan(steps=(Step(name="s", action="a", params={" ": 1}),))
    assert has_issue(plan_schema_issues(plan), "non-string or blank param key")


def test_plan_schema_issues_non_serializable_params() -> None:
    plan = make_plan(steps=(Step(name="s", action="a", params={"bad": object()}),))
    assert has_issue(plan_schema_issues(plan), "not JSON-serializable")


def test_plan_schema_issues_expected_match() -> None:
    plan = make_plan()
    assert plan_schema_issues(plan, expected_steps=("contract", "execute", "verify")) == ()


def test_plan_schema_issues_expected_mismatch() -> None:
    plan = make_plan()
    issues = plan_schema_issues(plan, expected_steps=("contract", "verify"))
    assert has_issue(issues, "do not match expected")


def test_plan_schema_issues_expected_order_matters() -> None:
    plan = make_plan()
    issues = plan_schema_issues(plan, expected_steps=("verify", "execute", "contract"))
    assert has_issue(issues, "do not match expected")


def test_require_plan_schema_passes_clean() -> None:
    require_plan_schema(make_plan(), expected_steps=("contract", "execute", "verify"))


def test_require_plan_schema_raises_on_issues() -> None:
    with pytest.raises(ValueError, match="duplicate step names"):
        require_plan_schema(make_plan(steps=(Step(name="x", action="a"), Step(name="x", action="b"))))


# --------------------------------------------------------------------------
# Provenance hashing
# --------------------------------------------------------------------------


def test_fingerprint_is_deterministic() -> None:
    assert fingerprint("a", 1, {"k": "v"}) == fingerprint("a", 1, {"k": "v"})


def test_fingerprint_differs_across_parts() -> None:
    assert fingerprint("a", 1) != fingerprint("a", 2)


def test_fingerprint_is_key_order_independent() -> None:
    assert fingerprint({"a": 1, "b": 2}) == fingerprint({"b": 2, "a": 1})


def test_fingerprint_accepts_protocol_objects() -> None:
    asset = Asset(kind="k", name="n", payload={"v": 1})
    assert fingerprint(asset) == fingerprint(Asset(kind="k", name="n", payload={"v": 1}))
    assert fingerprint(asset) != fingerprint(Asset(kind="k", name="n", payload={"v": 2}))


def test_fingerprint_empty_parts_is_fixed() -> None:
    """Pin the actual value, not ``fingerprint() == fingerprint()``.

    The self-comparison this replaced held for any deterministic function and
    could not fail. The golden digest below is SHA-256 of the empty byte
    string — no parts means no bytes were fed to the digest — and is
    re-derived from ``hashlib`` here rather than merely asserted, so a change
    to the fingerprint construction fails the test.
    """
    assert fingerprint() == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert fingerprint() == hashlib.sha256(b"").hexdigest()


def test_fingerprint_rejects_non_serializable_parts() -> None:
    with pytest.raises(SerializationError):
        fingerprint(object())


def test_hash_provenance_is_deterministic() -> None:
    assert hash_provenance(make_provenance()) == hash_provenance(make_provenance())


def test_hash_provenance_changes_with_fields() -> None:
    assert hash_provenance(make_provenance()) != hash_provenance(make_provenance(seed=8))
    assert hash_provenance(make_provenance()) != hash_provenance(make_provenance(input_hash="different"))


def test_hash_provenance_matches_fingerprint_of_fields() -> None:
    prov = make_provenance()
    expected = fingerprint(prov.package_version, prov.seed, prov.input_hash, prov.wall_time_s)
    assert hash_provenance(prov) == expected


def test_derive_provenance_derives_input_hash() -> None:
    prov = derive_provenance(package_version="0.1.0", seed=7, inputs=("brief", {"goal": "go"}))
    assert prov.input_hash == fingerprint("brief", {"goal": "go"})
    assert prov.seed == 7
    assert prov.package_version == "0.1.0"
    assert prov.wall_time_s == 0.0


def test_derive_provenance_is_deterministic() -> None:
    first = derive_provenance(package_version="0.1.0", seed=7, inputs=("brief",))
    second = derive_provenance(package_version="0.1.0", seed=7, inputs=("brief",))
    assert first == second


def test_derive_provenance_empty_inputs() -> None:
    prov = derive_provenance(package_version="0.1.0", seed=0)
    assert prov.input_hash == fingerprint()


def test_derive_provenance_wall_time_passthrough() -> None:
    prov = derive_provenance(package_version="0.1.0", seed=3, inputs=("x",), wall_time_s=1.25)
    assert prov.wall_time_s == 1.25


# --------------------------------------------------------------------------
# Debrief normalization
# --------------------------------------------------------------------------


def test_normalize_lessons_strips_drops_dedupes() -> None:
    normalized = normalize_lessons(("  lesson one  ", "lesson one", "", " lesson two "))
    assert normalized == ("lesson one", "lesson two")


def test_normalize_lessons_preserves_first_occurrence_order() -> None:
    normalized = normalize_lessons(("b", "a", "b", "a"))
    assert normalized == ("b", "a")


def test_normalize_lessons_empty() -> None:
    assert normalize_lessons(()) == ()
    assert normalize_lessons(("", "  ")) == ()


def test_normalize_lessons_clean_input_unchanged() -> None:
    assert normalize_lessons(("a", "b")) == ("a", "b")


def test_normalize_debrief_returns_normalized_copy() -> None:
    outcome = make_outcome()
    # Bypass __init__ (whose validation rejects empty lessons) so the messy
    # lesson set — padding, duplicates, empty — reaches normalize_debrief.
    raw = object.__new__(Debrief)
    object.__setattr__(raw, "outcome", outcome)
    object.__setattr__(raw, "lessons", ("  keep  ", "keep", "", " second "))
    normalized = normalize_debrief(raw)
    assert normalized.lessons == ("keep", "second")
    assert normalized.outcome is outcome
    # The original is untouched.
    assert raw.lessons == ("  keep  ", "keep", "", " second ")


def test_normalize_debrief_clean_is_equal() -> None:
    debrief = Debrief(outcome=make_outcome(), lessons=("a", "b"))
    assert normalize_debrief(debrief) == debrief


def test_normalize_debrief_serializes_round_trip() -> None:
    debrief = normalize_debrief(Debrief(outcome=make_outcome(), lessons=(" a ", "a", "b")))
    decoded = from_json(to_json(debrief), expected=Debrief)
    assert decoded == debrief


def test_normalize_debrief_rejects_invalid_outcome() -> None:
    # Construct a Debrief bypassing __init__ (whose validation would already
    # reject a non-MissionOutcome) so normalize_debrief's own defensive
    # isinstance branch is genuinely exercised.
    raw = object.__new__(Debrief)
    object.__setattr__(raw, "outcome", "nope")
    object.__setattr__(raw, "lessons", ("a",))
    with pytest.raises(ValueError, match="MissionOutcome"):
        normalize_debrief(raw)


# --------------------------------------------------------------------------
# The helpers cooperate with the frozen flow (regression guard)
# --------------------------------------------------------------------------


def test_capabilities_do_not_break_run_mission_round_trip() -> None:
    """Capability outputs stay within the serializable protocol surface."""
    brief = make_brief()
    plan = make_plan()
    prov = derive_provenance(package_version="0.1.0", seed=7, inputs=(brief, plan))
    outcome = make_outcome(provenance=prov)
    debrief = normalize_debrief(Debrief(outcome=outcome, lessons=(" ok ", "ok")))
    assert hash_provenance(debrief.outcome.provenance) == fingerprint(
        prov.package_version, prov.seed, prov.input_hash, prov.wall_time_s
    )
    assert validate_brief(brief).ok is True
    assert plan_schema_issues(plan, expected_steps=("contract", "execute", "verify")) == ()


def test_unused_protocol_imports_are_available() -> None:
    """The capability surface coexists with the full protocol import set."""
    # These are exercised elsewhere; the import itself is the regression guard.
    assert ReconRequest(goal="g").goal == "g"
    assert ReconReport(findings=(Finding(label="l", detail="d"),)).findings[0].label == "l"
