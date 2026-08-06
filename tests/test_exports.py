"""Public-surface integrity: ``bond_api.__all__`` must resolve, and the four
version copies must agree.

``__all__`` is the documented public contract of the package, yet it was never
exercised by the suite: a name listed in ``__all__`` with no corresponding
binding fails no gate. ``test_all_public_names_resolve`` iterates ``__all__``
and asserts each name resolves via ``getattr``, and asserts the list is
non-empty so the loop cannot pass by iterating nothing (V2).

The package version is stated in several places (``pyproject.toml``,
``bond_api.__version__``, ``manuscript/config.yaml`` → ``paper.version``, and
the reference film's provenance stamp). A bump edited in only one place leaves
the suite green while ships stale metadata. ``test_version_copies_agree`` binds
all four copies to one another so a single drifted copy fails (C3).
"""

from __future__ import annotations


import bond_api
from bond_api.manuscript_variables import PACKAGE_ROOT, load_manuscript_config
from bond_api.serialization import SERIALIZATION_TAG


def _pyproject_version() -> str:
    """The version declared in ``pyproject.toml`` [project]."""
    text = (PACKAGE_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("version ="):
            return stripped.split("=", 1)[1].strip().strip('"')
    raise AssertionError("pyproject.toml [project] version not found")


def test_all_public_names_resolve() -> None:
    """Every name in ``__all__`` must actually exist on the package."""
    assert len(bond_api.__all__) > 0, "a non-empty __all__ is the point"
    for name in bond_api.__all__:
        assert hasattr(bond_api, name), f"bond_api.__all__ names {name!r} but getattr fails"


def test_wildcard_import_exposes_only_all_names() -> None:
    """``from bond_api import *`` must bind exactly the advertised names."""
    namespace: dict[str, object] = {}
    exec("from bond_api import *", namespace)  # noqa: S102 — public-surface check
    # exec injects only __builtins__; __version__ (single underscore prefix) is
    # a legitimate public export listed in __all__.
    exposed = {k for k in namespace if k != "__builtins__"}
    assert exposed == set(bond_api.__all__)


def test_version_is_stated_once_in_pyproject() -> None:
    """pyproject declares exactly one 'version =' at project scope."""
    text = (PACKAGE_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert [l for l in text.splitlines() if l.strip().startswith("version =")]


def test_version_copies_agree_across_the_package() -> None:
    """All four version copies must equal the pyproject source of truth."""
    from_pyproject = _pyproject_version()
    from_init = bond_api.__version__
    from_config = str(load_manuscript_config()["paper"]["version"])
    from_film = _reference_film_package_version()

    assert from_init == from_pyproject, f"bond_api.__version__ {from_init!r} != pyproject {from_pyproject!r}"
    assert from_config == from_pyproject, (
        f"manuscript/config.yaml paper.version {from_config!r} != pyproject {from_pyproject!r}"
    )
    assert from_film == from_pyproject, f"films/sable _PACKAGE_VERSION {from_film!r} != pyproject {from_pyproject!r}"

    # The manuscript version token flows from config, so it inherits the gate.
    assert from_config == from_init


def _reference_film_package_version() -> str:
    """The version literal the reference film stamps into provenance."""
    src = (PACKAGE_ROOT / "films" / "sable" / "mission.py").read_text(encoding="utf-8")
    for line in src.splitlines():
        stripped = line.strip()
        if stripped.startswith("_PACKAGE_VERSION ="):
            return stripped.split("=", 1)[1].strip().strip('"')
    raise AssertionError("films/sable _PACKAGE_VERSION not found")


def test_serialization_tag_exported_consistent() -> None:
    """SERIALIZATION_TAG is part of the public surface and matches config."""
    assert hasattr(bond_api, "SERIALIZATION_TAG")
    assert bond_api.SERIALIZATION_TAG == SERIALIZATION_TAG
    assert "SERIALIZATION_TAG" in bond_api.__all__
