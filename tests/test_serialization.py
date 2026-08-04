"""Serialization tests: exact JSON round-trips for every protocol object.

No mocks: every case builds real protocol objects and verifies byte-level
determinism and type-exact reconstruction (tuples stay tuples, lists stay
lists, nested objects stay nested objects).
"""

from __future__ import annotations

import json
from typing import Any

import pytest

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
from bond_api.serialization import SerializationError, from_dict, from_json, to_dict, to_json


def make_provenance(**overrides: Any) -> Provenance:
    base = {"package_version": "0.1.0", "seed": 7, "input_hash": "abc123", "wall_time_s": 0.5}
    base.update(overrides)
    return Provenance(**base)


def make_outcome(**overrides: Any) -> MissionOutcome:
    base = {
        "success": True,
        "results": {"n": 3, "items": (1, 2), "asset": Asset(kind="k", name="n", payload=[1])},
        "provenance": make_provenance(),
    }
    base.update(overrides)
    return MissionOutcome(**base)


ROUND_TRIP_CASES: list[Any] = [
    Asset(kind="manifest", name="contract", payload={"version": "0.1.0", "flags": [1, 2, 3], "nested": {"a": None, "b": True}}),
    Asset(kind="note", name="empty", payload=None),
    Constraint(kind="determinism", detail="no draws"),
    Finding(label="goal", detail="survey"),
    Step(name="contract", action="load", params={"k": "v"}),
    ReconRequest(goal="survey assets"),
    ReconReport(findings=(Finding(label="a", detail="x"), Finding(label="b", detail="y"))),
    MissionBrief(
        film="sable",
        codename="THE PROTOCOL",
        objectives=("one", "two"),
        assets=(Asset(kind="manifest", name="contract", payload={"k": 1}),),
        constraints=(Constraint(kind="determinism", detail="none"),),
    ),
    MissionPlan(steps=(Step(name="s1", action="a1"), Step(name="s2", action="a2", params={"p": 2}))),
    make_provenance(),
    make_outcome(),
    Debrief(outcome=make_outcome(), lessons=("l1", "l2")),
    MissionOutcome(
        success=False,
        results={"levels": {"a": {"b": (1, (2, 3))}}},
        provenance=make_provenance(seed=0, wall_time_s=1),
    ),
]


@pytest.mark.parametrize(
    "obj",
    ROUND_TRIP_CASES,
    ids=[type(case).__name__ for case in ROUND_TRIP_CASES],
)
def test_json_round_trip_is_exact(obj: Any) -> None:
    text = to_json(obj)
    decoded = from_json(text)
    assert decoded == obj
    assert type(decoded) is type(obj)


def test_container_types_are_preserved() -> None:
    outcome = make_outcome(results={"t": (1, 2), "l": [3, 4], "tl": (1, [2, 3])})
    decoded = from_json(to_json(outcome))
    assert decoded.results["t"] == (1, 2)
    assert isinstance(decoded.results["t"], tuple)
    assert decoded.results["l"] == [3, 4]
    assert isinstance(decoded.results["l"], list)
    assert decoded.results["tl"] == (1, [2, 3])
    assert isinstance(decoded.results["tl"], tuple)


def test_to_json_is_deterministic() -> None:
    first = to_json(make_brief_like())
    second = to_json(make_brief_like())
    assert first == second


def make_brief_like() -> MissionBrief:
    return MissionBrief(
        film="sable",
        codename="THE PROTOCOL",
        objectives=("one", "two"),
        assets=(Asset(kind="manifest", name="contract", payload={"k": 1}),),
        constraints=(Constraint(kind="determinism", detail="none"),),
    )


def test_output_is_valid_json() -> None:
    text = to_json(make_outcome())
    assert json.loads(text)["success"] is True
    assert isinstance(json.loads(text), dict)


def test_from_dict_round_trip() -> None:
    brief = make_brief_like()
    assert from_dict(to_dict(brief)) == brief


def test_dict_keys_must_be_strings() -> None:
    with pytest.raises(SerializationError):
        to_json(Asset(kind="k", name="n", payload={1: "x"}))


def test_unsupported_payloads_are_rejected() -> None:
    with pytest.raises(SerializationError):
        to_json(Asset(kind="k", name="n", payload=object()))
    with pytest.raises(SerializationError):
        to_json(Asset(kind="k", name="n", payload=b"bytes"))
    with pytest.raises(SerializationError):
        to_json(Asset(kind="k", name="n", payload={1, 2}))
    with pytest.raises(SerializationError):
        to_json(object())


def test_unknown_bond_type_is_rejected() -> None:
    with pytest.raises(SerializationError, match="unknown bond type"):
        from_json('{"__bond_type__": "NoSuchType", "x": 1}')


def test_reserved_tag_encodes_and_decodes_tuples() -> None:
    assert from_json('{"__bond_type__": "tuple", "items": [1, 2]}') == (1, 2)
    assert from_json('{"__bond_type__": "list", "items": [1, 2]}') == [1, 2]


def test_malformed_container_encodings_are_rejected() -> None:
    with pytest.raises(SerializationError, match="malformed tuple"):
        from_json('{"__bond_type__": "tuple"}')
    with pytest.raises(SerializationError, match="malformed list"):
        from_json('{"__bond_type__": "list"}')


def test_malformed_dataclass_encoding_is_rejected() -> None:
    with pytest.raises(SerializationError, match="missing field"):
        from_json('{"__bond_type__": "Asset", "kind": "k"}')


def test_from_json_expected_type() -> None:
    brief = make_brief_like()
    assert from_json(to_json(brief), expected=MissionBrief) == brief
    with pytest.raises(SerializationError, match="expected"):
        from_json(to_json(brief), expected=MissionPlan)


def test_from_json_primitives_and_plain_data() -> None:
    assert from_json('"hi"') == "hi"
    assert from_json("42") == 42
    assert from_json("[1, 2]") == [1, 2]
    assert from_json('{"a": [1, {"b": 2}]}') == {"a": [1, {"b": 2}]}


def test_from_json_invalid_json_is_rejected() -> None:
    with pytest.raises(SerializationError, match="invalid JSON"):
        from_json("{not json")


def test_to_dict_rejects_non_dict_encodable() -> None:
    with pytest.raises(SerializationError, match="dict-encodable"):
        to_dict(42)


def test_unknown_tag_in_payload_dict_is_rejected() -> None:
    # A payload dict using the reserved key with an unknown type is malformed.
    with pytest.raises(SerializationError, match="unknown bond type"):
        from_json('{"payload": {"__bond_type__": "gadget", "items": []}}')
