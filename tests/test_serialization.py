"""Serialization tests: exact JSON round-trips for every protocol object.

No mocks: every case builds real protocol objects and verifies byte-level
determinism and type-exact reconstruction (tuples stay tuples, lists stay
lists, nested objects stay nested objects).
"""

from __future__ import annotations

import dataclasses
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
from bond_api.serialization import (
    SERIALIZATION_TAG,
    SerializationError,
    from_dict,
    from_json,
    to_dict,
    to_json,
)


def _raise_on_constant(_token: str) -> Any:
    """json.loads parse_constant that refuses NaN/Infinity literals."""
    raise ValueError(_token)


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
    Asset(
        kind="manifest",
        name="contract",
        payload={"version": "0.1.0", "flags": [1, 2, 3], "nested": {"a": None, "b": True}},
    ),
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


def test_output_is_valid_strict_json() -> None:
    """The wire output must parse with a strict RFC 8259 parser.

    Python's own json.loads accepts bare ``NaN``/``Infinity`` literals, so a
    plain ``json.loads`` cannot certify validity. Parsing with a
    ``parse_constant`` callback that raises makes any non-finite token fail
    here. (C1/V1.)
    """
    text = to_json(make_outcome())
    assert isinstance(text, str)
    data = json.loads(text, parse_constant=_raise_on_constant)
    assert data["success"] is True
    assert isinstance(data, dict)


def test_non_finite_payload_float_is_rejected_at_encode() -> None:
    """A non-finite float anywhere in a payload must never reach the wire."""
    for bad in (float("inf"), float("-inf"), float("nan")):
        with pytest.raises(SerializationError, match="non-finite float"):
            to_json(Asset(kind="k", name="n", payload={"x": bad}))
        with pytest.raises(SerializationError, match="non-finite float"):
            to_json(make_outcome(results={"x": bad}))
        with pytest.raises(SerializationError, match="non-finite float"):
            to_dict(make_outcome(results={"nested": {"x": bad}}))


def test_from_json_rejects_non_finite_literals() -> None:
    """A foreign document carrying NaN/Infinity must fail loudly, not silently
    decode to Python floats the encoder could never re-emit as JSON."""
    for doc in ('{"a": Infinity}', '{"a": -Infinity}', '{"a": NaN}', "[NaN, 1]"):
        with pytest.raises(SerializationError, match="not valid RFC 8259 JSON"):
            from_json(doc)


def test_provenance_rejects_non_finite_wall_time() -> None:
    """``Provenance.wall_time_s`` must be finite: inf passes the >=0 check but
    can never be serialized to RFC 8259 JSON, so it is rejected at construction."""
    for bad in (float("inf"), float("-inf")):
        with pytest.raises(ValueError, match="finite number"):
            make_provenance(wall_time_s=bad)


@pytest.mark.parametrize("tag", [None, False, 0, [], {}, "gadget"])
def test_reserved_tag_with_invalid_value_is_rejected_on_decode(tag) -> None:
    """The reserved key may only carry a known wire tag; null/false/0/[]/{} and
    unknown strings must fail loudly instead of decoding to an untagged dict."""
    import json as _json

    doc = _json.dumps({"__bond_type__": tag, "a": 1})
    with pytest.raises(SerializationError, match="unknown bond type"):
        from_json(doc)


def test_round_trip_is_total_over_accepted_documents() -> None:
    """Every document from_json accepts must re-encode through to_json: the
    decode::encode closure must be total so the round trip never dead-ends."""
    accepted = [
        '{"a": 1, "b": [1, {"c": null}]}',
        to_json(make_outcome()),
        to_json(make_provenance()),
        '{"__bond_type__": "tuple", "items": [1, 2]}',
        '{"__bond_type__": "list", "items": ["x"]}',
        '"hi"',
        "[1, true, null, {}]",
    ]
    for doc in accepted:
        decoded = from_json(doc)
        reencoded = to_json(decoded)
        assert from_json(reencoded, expected=type(decoded)) == decoded


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


def test_payload_dict_using_reserved_key_is_rejected_at_encode() -> None:
    """A dict carrying the reserved key must never reach the wire.

    Before this was enforced, ``Asset(payload={"__bond_type__": "Finding",
    "label": "x", "detail": "y"})`` encoded happily and decoded back as a
    ``Finding`` *object* — silent corruption that broke the advertised exact
    round-trip without raising anything.
    """
    corrupting = {SERIALIZATION_TAG: "Finding", "label": "x", "detail": "y"}
    with pytest.raises(SerializationError, match="reserved wire key"):
        to_json(Asset(kind="k", name="n", payload=corrupting))
    with pytest.raises(SerializationError, match="reserved wire key"):
        to_dict(Asset(kind="k", name="n", payload=dict(corrupting)))
    # Also for the container tags and for a nested position.
    with pytest.raises(SerializationError, match="reserved wire key"):
        to_json(Asset(kind="k", name="n", payload={SERIALIZATION_TAG: "tuple", "items": [1]}))
    with pytest.raises(SerializationError, match="reserved wire key"):
        to_json(Asset(kind="k", name="n", payload={"deep": [{SERIALIZATION_TAG: "list", "items": []}]}))


def test_plain_payload_dicts_still_encode() -> None:
    """The rejection is targeted: ordinary dicts are unaffected."""
    asset = Asset(kind="k", name="n", payload={"bond_type": "not reserved", "__other__": 1})
    assert from_json(to_json(asset)) == asset


def test_name_shadowing_dataclass_is_rejected_not_flattened() -> None:
    """The type check is identity-based, not a string-name comparison.

    A dataclass whose ``__name__`` shadows a protocol type used to be accepted
    and encoded under that tag; decoding then rebuilt the *real* protocol type
    and silently dropped every extra field.
    """

    @dataclasses.dataclass(frozen=True)
    class Impostor:
        label: str
        detail: str
        extra: str = "dropped-on-decode"

    Impostor.__name__ = "Finding"
    with pytest.raises(SerializationError, match="shadows protocol type"):
        to_json(Impostor(label="l", detail="d"))
    with pytest.raises(SerializationError, match="shadows protocol type"):
        to_json(Asset(kind="k", name="n", payload=Impostor(label="l", detail="d")))


def test_protocol_subclass_is_rejected() -> None:
    """Subclasses do not round-trip: they would lose their own fields."""

    @dataclasses.dataclass(frozen=True)
    class ExtendedFinding(Finding):
        weight: int = 1

    with pytest.raises(SerializationError, match="cannot serialize"):
        to_json(ExtendedFinding(label="l", detail="d", weight=3))

    # ...including when it shadows the base class name.
    ExtendedFinding.__name__ = "Finding"
    with pytest.raises(SerializationError, match="shadows protocol type"):
        to_json(ExtendedFinding(label="l", detail="d", weight=3))


def test_serialization_tag_constant_is_the_live_wire_key() -> None:
    """The published tag must be the key actually emitted, not a copy of it."""
    encoded = to_dict(ReconRequest(goal="tag"))
    assert SERIALIZATION_TAG in encoded
    assert encoded[SERIALIZATION_TAG] == "ReconRequest"
    assert SERIALIZATION_TAG in to_json(ReconRequest(goal="tag"))
