"""Bind the byte-identical-regeneration claim to the real generator.

``manuscript/06_reproducibility.md``, ``README.md`` and ``AGENTS.md`` all state
that regenerating ``output/`` twice on one interpreter writes identical bytes.
Nothing enforced that until this module existed, and the claim was in fact
false: ``generate_variables`` carried a ``GENERATION_TIMESTAMP`` token read
from ``datetime.now(timezone.utc)``, which was substituted into
``manuscript/05_experimental_setup.md`` and written into
``output/data/manuscript_variables.json``. Every regeneration produced
different bytes.

Two independent gates, because either one alone has a hole:

* :func:`test_regenerating_the_manuscript_tree_is_byte_identical` runs the real
  orchestrator script twice as a subprocess, into two separate output
  directories, **sleeping across a whole-second boundary in between** so a
  second-granularity clock read cannot hide inside one tick. It then compares
  every produced file byte for byte. This is the behavioural claim itself, not
  a proxy for it. Deliberately *not* an injected-``now`` test: injecting a
  fixed clock is exactly the shape of test that lets a wall clock survive in
  production, because it only ever exercises the frozen value.

* :func:`test_generator_module_reads_no_wall_clock` walks the ``ast`` of
  ``manuscript_variables.py`` for clock calls. This catches a reintroduction at
  *any* granularity — a ``time.time()`` float or an ISO timestamp with
  microseconds would slip past a one-second sleep only if the two runs happened
  to collide, but never past this. Per ``AGENTS.md`` rule 8 the scanner carries
  a positive control (:func:`test_wall_clock_scanner_flags_a_real_clock_read`)
  that feeds it source which *does* read the clock, so it cannot pass by
  looking for something it would never match.

No mocks: real subprocesses, real files, real source parsing.
"""

from __future__ import annotations

import ast
import subprocess
import sys
import time
from pathlib import Path

import pytest

from bond_api.manuscript_variables import generate_variables

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "z_generate_manuscript_variables.py"
GENERATOR_MODULE = ROOT / "src" / "bond_api" / "manuscript_variables.py"

#: ``module.attribute`` pairs that read the wall clock.
_CLOCK_CALLS = {
    ("datetime", "now"),
    ("datetime", "today"),
    ("datetime", "utcnow"),
    ("date", "today"),
    ("time", "time"),
    ("time", "time_ns"),
    ("time", "monotonic"),
    ("time", "localtime"),
    ("time", "gmtime"),
    ("os", "times"),
}
#: Bare names that read the wall clock when imported directly (``from time import time``).
_CLOCK_NAMES = {"time_ns", "monotonic"}


def _run_generator(output_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GENERATOR), "--output-dir", str(output_dir)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def _artifact_bytes(output_dir: Path) -> dict[str, bytes]:
    """Every generated ``.json``/``.md`` file, keyed by path relative to the root."""
    return {
        str(path.relative_to(output_dir)): path.read_bytes()
        for path in sorted(output_dir.rglob("*"))
        if path.is_file() and path.suffix in {".json", ".md"}
    }


def wall_clock_call_sites(source: str) -> list[str]:
    """Return ``ast``-derived descriptions of every wall-clock read in ``source``.

    Structural, not a substring grep: the word "now" in a docstring or a
    variable called ``timestamp`` is not a clock read, and only a real ``Call``
    node targeting a known clock function counts.
    """
    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if (func.value.id, func.attr) in _CLOCK_CALLS:
                found.append(f"line {node.lineno}: {func.value.id}.{func.attr}()")
        elif isinstance(func, ast.Name) and func.id in _CLOCK_NAMES:
            found.append(f"line {node.lineno}: {func.id}()")
    return found


def test_regenerating_the_manuscript_tree_is_byte_identical(tmp_path: Path) -> None:
    """The claim itself: two real regenerations, separated in time, agree byte for byte."""
    first_dir = tmp_path / "run_one"
    second_dir = tmp_path / "run_two"

    first = _run_generator(first_dir)
    assert first.returncode == 0, first.stderr

    # Cross a whole-second boundary, then some: a second-granularity clock read
    # in the generator is guaranteed to produce a different value on run two.
    start = time.time()
    time.sleep(1.0 - (start % 1.0) + 0.2)

    second = _run_generator(second_dir)
    assert second.returncode == 0, second.stderr

    first_files = _artifact_bytes(first_dir)
    second_files = _artifact_bytes(second_dir)

    # Anti-vacuity: an empty comparison set would make byte equality trivially true.
    assert first_files, "the generator produced no artifacts — the comparison would be vacuous"
    assert "data/manuscript_variables.json" in first_files
    assert any(name.startswith("manuscript/") for name in first_files)

    assert sorted(second_files) == sorted(first_files), "the two runs produced different file sets"
    differing = sorted(name for name in first_files if first_files[name] != second_files[name])
    assert differing == [], f"regeneration is not byte-identical; these files differ between runs: {differing}"


def test_generate_variables_is_stable_across_a_second_boundary() -> None:
    """The unit-level half: the token map itself does not move with the clock."""
    before = generate_variables()
    start = time.time()
    time.sleep(1.0 - (start % 1.0) + 0.2)
    after = generate_variables()
    drifted = sorted(token for token in before if before[token] != after[token])
    assert drifted == [], f"these tokens changed between two calls one second apart: {drifted}"


def test_generator_module_reads_no_wall_clock() -> None:
    """No clock call may exist in the module that fills the manuscript tokens."""
    sites = wall_clock_call_sites(GENERATOR_MODULE.read_text(encoding="utf-8"))
    assert sites == [], (
        f"{GENERATOR_MODULE.name} reads the wall clock at {sites}; that makes every regeneration "
        "of output/ differ and falsifies the byte-identity claim in manuscript/06_reproducibility.md"
    )


def test_wall_clock_scanner_flags_a_real_clock_read() -> None:
    """Positive control: the scanner fires on source that genuinely reads the clock."""
    source = (
        "from datetime import datetime, timezone\n"
        "import time\n"
        "def f():\n"
        "    stamp = datetime.now(timezone.utc).isoformat()\n"
        "    elapsed = time.time()\n"
        "    return stamp, elapsed\n"
    )
    sites = wall_clock_call_sites(source)
    assert len(sites) == 2, sites
    assert any("datetime.now" in site for site in sites)
    assert any("time.time" in site for site in sites)


def test_wall_clock_scanner_ignores_lookalikes() -> None:
    """The scanner is structural: names that merely *read* like clocks are not calls to one."""
    source = (
        '"""A docstring mentioning datetime.now and time.time()."""\n'
        "now = 1\n"
        "timestamp = 'datetime.now()'\n"
        "def now():\n"
        "    return 2\n"
        "value = now()\n"
    )
    assert wall_clock_call_sites(source) == []


@pytest.mark.parametrize(
    "source",
    [
        "import time\nx = time.time_ns()\n",
        "from datetime import date\nx = date.today()\n",
        "from time import monotonic\nx = monotonic()\n",
    ],
)
def test_wall_clock_scanner_covers_each_clock_form(source: str) -> None:
    """Each accepted clock form is individually detected, not just the common one."""
    assert wall_clock_call_sites(source)
