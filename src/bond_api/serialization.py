"""Deterministic JSON round-trip serialization for every BOND-API protocol object.

Coordinators, orchestrators, and CLIs move mission artifacts across process
boundaries with :func:`to_json` / :func:`from_json`. No pickling: the wire
format is plain JSON, so any language can consume it.

Format notes:

* Protocol dataclasses encode as ``{"__bond_type__": "<ClassName>", ...fields}``.
* ``tuple`` and ``list`` are distinguished with explicit tags so round-trips
  preserve container types exactly.
* The single reserved key is ``__bond_type__``. Payload dicts (e.g. inside
  :class:`~bond_api.protocol.Asset`) may not use it, and this is **enforced at
  encode time**: a dict carrying the reserved key raises
  :class:`SerializationError` rather than being written to the wire, where it
  would decode back as a protocol object instead of a dict.
* Only the exact protocol types round-trip. The check is on class *identity*,
  not class name: a subclass, or an unrelated dataclass whose ``__name__``
  shadows a protocol type, is rejected rather than silently flattened.
"""

from __future__ import annotations

import dataclasses
import inspect
import json
from typing import Any

import bond_api.protocol as _protocol

__all__ = [
    "SERIALIZATION_TAG",
    "SerializationError",
    "from_dict",
    "from_json",
    "to_dict",
    "to_json",
]

_TYPE_TAG = "__bond_type__"
_TUPLE_TAG = "tuple"
_LIST_TAG = "list"

#: The single reserved wire-format key, published so documentation, manuscript
#: tokens, and downstream layers bind to the live value instead of repeating
#: the literal string. Changing it is a wire-format migration.
SERIALIZATION_TAG = _TYPE_TAG

_PRIMITIVES = (str, int, float, bool)


def _known_types() -> dict[str, type]:
    """Registry of protocol dataclasses, keyed by class name (deterministic)."""
    members = inspect.getmembers(
        _protocol,
        predicate=lambda member: isinstance(member, type) and dataclasses.is_dataclass(member),
    )
    return {name: member for name, member in members}


_KNOWN_TYPES = _known_types()


class SerializationError(ValueError):
    """Raised when a value cannot be encoded to or decoded from JSON."""


def _encode(value: Any) -> Any:
    if value is None or isinstance(value, _PRIMITIVES):
        return value
    if isinstance(value, tuple):
        return {_TYPE_TAG: _TUPLE_TAG, "items": [_encode(item) for item in value]}
    if isinstance(value, list):
        return {_TYPE_TAG: _LIST_TAG, "items": [_encode(item) for item in value]}
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise SerializationError(f"dict keys must be strings, got {type(key).__name__} in {value!r}")
        if _TYPE_TAG in value:
            # Encoding it would emit a wire object the decoder reads back as a
            # tuple, list, or protocol dataclass — silently turning a dict into
            # something else. Reject rather than corrupt.
            raise SerializationError(
                f"dict uses the reserved wire key {_TYPE_TAG!r}: payload dicts must not use it "
                f"(offending dict: {value!r})"
            )
        return {key: _encode(item) for key, item in value.items()}
    cls = type(value)
    if dataclasses.is_dataclass(value):
        # Identity, not name: a subclass or an unrelated dataclass whose
        # ``__name__`` shadows a protocol type would otherwise be flattened
        # onto the protocol type's fields and lose everything else.
        known = _KNOWN_TYPES.get(cls.__name__)
        if known is cls:
            encoded: dict[str, Any] = {_TYPE_TAG: cls.__name__}
            for field in dataclasses.fields(value):
                encoded[field.name] = _encode(getattr(value, field.name))
            return encoded
        if known is not None:
            raise SerializationError(
                f"cannot serialize {cls.__module__}.{cls.__qualname__}: its name {cls.__name__!r} "
                f"shadows protocol type {known.__module__}.{known.__qualname__} but is a different "
                "class; only the exact protocol types round-trip"
            )
    raise SerializationError(
        f"cannot serialize {cls.__name__}: protocol payloads must be JSON-serializable "
        "(str/int/float/bool/None/list/tuple/dict/protocol dataclasses)"
    )


def _decode(value: Any) -> Any:
    if isinstance(value, list):
        return [_decode(item) for item in value]
    if isinstance(value, dict):
        tag = value.get(_TYPE_TAG)
        if tag is not None:
            if tag == _TUPLE_TAG:
                items = value.get("items")
                if not isinstance(items, list):
                    raise SerializationError("malformed tuple encoding: missing 'items' list")
                return tuple(_decode(item) for item in items)
            if tag == _LIST_TAG:
                items = value.get("items")
                if not isinstance(items, list):
                    raise SerializationError("malformed list encoding: missing 'items' list")
                return [_decode(item) for item in items]
            cls = _KNOWN_TYPES.get(tag)
            if cls is None:
                raise SerializationError(f"unknown bond type {tag!r}")
            try:
                fields = {field.name: _decode(value[field.name]) for field in dataclasses.fields(cls)}
            except KeyError as exc:
                raise SerializationError(f"malformed encoding for {tag}: missing field {exc.args[0]!r}") from exc
            return cls(**fields)
        return {key: _decode(item) for key, item in value.items()}
    return value


def to_dict(obj: Any) -> dict[str, Any]:
    """Encode a protocol object (or JSON-safe composite) into a plain dict."""
    encoded = _encode(obj)
    if not isinstance(encoded, dict):
        raise SerializationError(f"to_dict requires a dict-encodable value, got {type(encoded).__name__}")
    return encoded


def from_dict(data: dict[str, Any]) -> Any:
    """Decode a dict produced by :func:`to_dict` back into protocol objects."""
    return _decode(data)


def to_json(obj: Any) -> str:
    """Serialize a protocol object to a deterministic JSON string.

    Keys are sorted and indentation fixed, so identical objects always produce
    byte-identical text.
    """
    return json.dumps(_encode(obj), sort_keys=True, indent=2)


def from_json(text: str, *, expected: type | None = None) -> Any:
    """Parse a JSON string produced by :func:`to_json` back into protocol objects.

    Args:
        text: The JSON document.
        expected: Optional type the decoded object must be an instance of.

    Raises:
        SerializationError: if the text is invalid JSON, references an unknown
            bond type, or (when ``expected`` is given) decodes to a different
            type.
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SerializationError(f"invalid JSON: {exc}") from exc
    obj = from_dict(data)
    if expected is not None and not isinstance(obj, expected):
        raise SerializationError(f"decoded object is {type(obj).__name__}, expected {expected.__name__}")
    return obj
