"""Golden pins for the two determinism guarantees the package advertises.

The docs claim ``to_json`` produces byte-identical text and that
``fingerprint`` is "deterministic across processes and platforms". Both claims
were previously supported only by same-process self-comparisons
(``to_json(o) == to_json(o)``), which hold for *any* deterministic pure
function and therefore pin nothing: a change to ``indent``, ``sort_keys``, the
container tags, the NUL separator, or the field order would leave every such
assertion green.

This module pins the actual bytes. Two independent mechanisms:

1. **Literal goldens.** The expected JSON text and SHA-256 digests are checked
   in as literals. They were computed once and are re-checked on every machine
   and every Python version that runs the suite, so drift in the wire format
   or the hash construction fails here rather than silently shipping.
2. **A fresh interpreter.** ``test_*_across_processes`` re-derives the same
   values in a subprocess started with a randomized hash seed, which is what
   "across processes" actually means. A dict-iteration- or hash-seed-dependent
   encoding would pass the in-process test and fail this one.

No mocks: real protocol objects, real ``hashlib``, a real subprocess.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from bond_api.capabilities import derive_provenance, fingerprint, hash_provenance
from bond_api.protocol import Asset, Constraint, MissionBrief, Provenance
from bond_api.serialization import to_json

PACKAGE_ROOT = Path(__file__).resolve().parents[1]

# --------------------------------------------------------------------------
# The canonical fixtures the goldens below were computed from.
# --------------------------------------------------------------------------


def canonical_brief() -> MissionBrief:
    """A brief exercising every wire construct: dataclass, tuple, list, dict."""
    return MissionBrief(
        film="sable",
        codename="THE PROTOCOL",
        objectives=("one", "two"),
        assets=(Asset(kind="manifest", name="contract", payload={"k": 1, "l": [1, 2], "t": (3, 4)}),),
        constraints=(Constraint(kind="determinism", detail="none"),),
    )


def canonical_provenance() -> Provenance:
    return Provenance(package_version="0.1.0", seed=7, input_hash="abc123", wall_time_s=0.5)


# --------------------------------------------------------------------------
# Literal goldens. Changing the wire format or the hash construction must
# change these — that is the point. Do not "refresh" them to make a red test
# green without deciding the format change is intended and versioned.
# --------------------------------------------------------------------------

GOLDEN_BRIEF_JSON = """{
  "__bond_type__": "MissionBrief",
  "assets": {
    "__bond_type__": "tuple",
    "items": [
      {
        "__bond_type__": "Asset",
        "kind": "manifest",
        "name": "contract",
        "payload": {
          "k": 1,
          "l": {
            "__bond_type__": "list",
            "items": [
              1,
              2
            ]
          },
          "t": {
            "__bond_type__": "tuple",
            "items": [
              3,
              4
            ]
          }
        }
      }
    ]
  },
  "codename": "THE PROTOCOL",
  "constraints": {
    "__bond_type__": "tuple",
    "items": [
      {
        "__bond_type__": "Constraint",
        "detail": "none",
        "kind": "determinism"
      }
    ]
  },
  "film": "sable",
  "objectives": {
    "__bond_type__": "tuple",
    "items": [
      "one",
      "two"
    ]
  }
}"""

#: ``fingerprint()`` with no parts: SHA-256 of the empty byte string.
GOLDEN_EMPTY_FINGERPRINT = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
GOLDEN_PARTS_FINGERPRINT = "7ec4c2e90fbb6ac2adf920c9cc51b22c437bf72b0788e45ed51a10d10812a93d"
GOLDEN_BRIEF_FINGERPRINT = "e4e4c9748c3bea852ed9b057b45fba487ec204daac944618774d4b8335f4adac"
GOLDEN_PROVENANCE_FINGERPRINT = "403e0640fbfec86935e46cd3f5dc04bdc9dc98405a6d1f3a4fec713308c5bdcb"


# --------------------------------------------------------------------------
# In-process goldens
# --------------------------------------------------------------------------


def test_to_json_matches_golden_bytes() -> None:
    """The wire text is pinned byte-for-byte, not merely compared to itself."""
    assert to_json(canonical_brief()) == GOLDEN_BRIEF_JSON


def test_golden_json_is_the_documented_shape() -> None:
    """Sanity: the golden really is key-sorted, 2-space-indented JSON."""
    parsed = json.loads(GOLDEN_BRIEF_JSON)
    assert json.dumps(parsed, sort_keys=True, indent=2) == GOLDEN_BRIEF_JSON
    assert list(parsed) == sorted(parsed)


def test_empty_fingerprint_matches_golden_digest() -> None:
    assert fingerprint() == GOLDEN_EMPTY_FINGERPRINT
    # Independently derived: no parts means no bytes were fed to the digest.
    assert fingerprint() == hashlib.sha256(b"").hexdigest()


def test_parts_fingerprint_matches_golden_digest() -> None:
    assert fingerprint("a", 1, {"k": "v"}) == GOLDEN_PARTS_FINGERPRINT


def test_protocol_object_fingerprint_matches_golden_digest() -> None:
    assert fingerprint(canonical_brief()) == GOLDEN_BRIEF_FINGERPRINT


def test_hash_provenance_matches_golden_digest() -> None:
    assert hash_provenance(canonical_provenance()) == GOLDEN_PROVENANCE_FINGERPRINT


def test_derive_provenance_input_hash_matches_golden_digest() -> None:
    prov = derive_provenance(package_version="0.1.0", seed=7, inputs=(canonical_brief(),))
    assert prov.input_hash == GOLDEN_BRIEF_FINGERPRINT


def test_fingerprint_construction_is_nul_separated_canonical_json() -> None:
    """Pin the construction itself, re-derived from hashlib rather than assumed."""
    parts = ("a", 1, {"k": "v"})
    digest = hashlib.sha256()
    for part in parts:
        digest.update(to_json(part).encode("utf-8"))
        digest.update(b"\x00")
    assert fingerprint(*parts) == digest.hexdigest() == GOLDEN_PARTS_FINGERPRINT


# --------------------------------------------------------------------------
# Cross-process goldens (what "across processes" actually claims)
# --------------------------------------------------------------------------

_SUBPROCESS_SOURCE = """
import json, sys
from bond_api.capabilities import fingerprint, hash_provenance
from bond_api.protocol import Asset, Constraint, MissionBrief, Provenance
from bond_api.serialization import to_json

brief = MissionBrief(
    film="sable",
    codename="THE PROTOCOL",
    objectives=("one", "two"),
    assets=(Asset(kind="manifest", name="contract", payload={"k": 1, "l": [1, 2], "t": (3, 4)}),),
    constraints=(Constraint(kind="determinism", detail="none"),),
)
prov = Provenance(package_version="0.1.0", seed=7, input_hash="abc123", wall_time_s=0.5)
sys.stdout.write(json.dumps({
    "json": to_json(brief),
    "empty_fp": fingerprint(),
    "parts_fp": fingerprint("a", 1, {"k": "v"}),
    "brief_fp": fingerprint(brief),
    "prov_fp": hash_provenance(prov),
}))
"""


def _run_in_fresh_interpreter() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(PACKAGE_ROOT / "src"), env.get("PYTHONPATH", "")]).rstrip(os.pathsep)
    # Randomized hash seed: a dict-ordering-dependent encoding cannot hide.
    env["PYTHONHASHSEED"] = "random"
    completed = subprocess.run(
        [sys.executable, "-c", _SUBPROCESS_SOURCE],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(PACKAGE_ROOT),
        check=True,
    )
    return json.loads(completed.stdout)


def test_determinism_holds_across_processes() -> None:
    """Re-derive every golden in a fresh interpreter with a randomized hash seed."""
    result = _run_in_fresh_interpreter()
    assert result["json"] == GOLDEN_BRIEF_JSON
    assert result["empty_fp"] == GOLDEN_EMPTY_FINGERPRINT
    assert result["parts_fp"] == GOLDEN_PARTS_FINGERPRINT
    assert result["brief_fp"] == GOLDEN_BRIEF_FINGERPRINT
    assert result["prov_fp"] == GOLDEN_PROVENANCE_FINGERPRINT
