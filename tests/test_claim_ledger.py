"""Bind ``data/claim_ledger.yaml`` to the live package.

The ledger hand-maintains values the package otherwise derives rigorously
(dataclass count, provider-stage count, capability count, coverage floor, wire
tag, reference-film slug). Until this module existed nothing read the file:
every row could drift to a wrong value and no gate anywhere would notice,
while ``data/AGENTS.md`` told editors to "re-run evidence validation" that did
not exist.

This is the evidence validation. Each row is re-derived from its cited source
of truth — the live protocol surface, ``CAPABILITY_NAMES``, the ``fail_under``
gate in ``pyproject.toml``, the published wire constant, the discovered
reference film — and compared to the declared value.

Two anti-vacuity guards, because a checker that checks nothing is worse than
no checker:

* ``test_every_ledger_claim_has_a_verifier`` fails when a row is added without
  a verifier, so the gate cannot quietly stop covering the file.
* ``test_ledger_is_not_empty`` fails on an empty or truncated ledger, so the
  per-row loop can never pass by iterating zero rows.

No mocks: real YAML, real package introspection, real file reads.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pytest
import yaml

from bond_api.capabilities import CAPABILITY_NAMES
from bond_api.discovery import load_provider
from bond_api.manuscript_variables import read_coverage_floor
from bond_api.protocol import MISSION_FLOW, protocol_surface
from bond_api.serialization import SERIALIZATION_TAG

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = PACKAGE_ROOT / "data" / "claim_ledger.yaml"
FILMS_DIR = PACKAGE_ROOT / "films"

LEDGER_FIELDS = ("claim_id", "kind", "value", "source", "source_tier", "freshness")


def _reference_film_slug() -> str:
    """The slug the reference film actually answers to, from discovery."""
    return str(load_provider("sable", search_paths=[FILMS_DIR]).film)


#: claim_id -> callable returning the value re-derived from the source of truth.
VERIFIERS: dict[str, Callable[[], Any]] = {
    "protocol-dataclass-count": lambda: len(protocol_surface()["dataclasses"]),
    "provider-stage-count": lambda: len(MISSION_FLOW),
    "capability-helper-count": lambda: len(CAPABILITY_NAMES),
    "coverage-floor": lambda: read_coverage_floor(),
    "serialization-type-tag": lambda: SERIALIZATION_TAG,
    "reference-film-slug": _reference_film_slug,
}


def load_ledger() -> list[dict[str, Any]]:
    """Read the ledger rows, failing loudly on a missing or malformed file."""
    assert LEDGER_PATH.is_file(), f"claim ledger not found: {LEDGER_PATH}"
    data = yaml.safe_load(LEDGER_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "claim ledger must be a top-level mapping"
    claims = data.get("claims")
    assert isinstance(claims, list), "claim ledger must declare a 'claims' list"
    return claims


LEDGER_CLAIMS = load_ledger()


def test_ledger_is_not_empty() -> None:
    """A zero-row ledger would make every parametrized check vacuous."""
    assert len(LEDGER_CLAIMS) >= len(VERIFIERS) > 0


def test_every_ledger_claim_has_a_verifier() -> None:
    """A new row without a verifier fails here rather than going unchecked."""
    declared = {claim["claim_id"] for claim in LEDGER_CLAIMS}
    assert declared == set(VERIFIERS), (
        f"ledger rows without a verifier: {sorted(declared - set(VERIFIERS))}; "
        f"verifiers without a ledger row: {sorted(set(VERIFIERS) - declared)}"
    )


@pytest.mark.parametrize("claim", LEDGER_CLAIMS, ids=[claim["claim_id"] for claim in LEDGER_CLAIMS])
def test_ledger_row_matches_live_source_of_truth(claim: dict[str, Any]) -> None:
    """Each declared value must equal the value re-derived from live code."""
    claim_id = claim["claim_id"]
    actual = VERIFIERS[claim_id]()
    assert claim["value"] == actual, (
        f"claim_ledger.yaml row {claim_id!r} declares {claim['value']!r} but {claim['source']} yields {actual!r}"
    )


@pytest.mark.parametrize("claim", LEDGER_CLAIMS, ids=[claim["claim_id"] for claim in LEDGER_CLAIMS])
def test_ledger_row_schema(claim: dict[str, Any]) -> None:
    """The schema documented in ``data/AGENTS.md`` is enforced, not just described."""
    for required in LEDGER_FIELDS:
        assert required in claim, f"{claim.get('claim_id')!r} is missing required field {required!r}"
    assert claim["kind"] in {"number", "string"}, f"unknown claim kind {claim['kind']!r}"
    expected_type = int if claim["kind"] == "number" else str
    assert isinstance(claim["value"], expected_type), f"{claim['claim_id']!r} value is not a {claim['kind']}"
    artifact = claim.get("artifact_path")
    if artifact is not None:
        assert (PACKAGE_ROOT / artifact).exists(), f"{claim['claim_id']!r} cites a missing artifact: {artifact}"
