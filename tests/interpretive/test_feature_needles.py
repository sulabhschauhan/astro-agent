"""
tests/interpretive/test_feature_needles.py
S119 Step 7: the leaf module agent/interpretive/feature_needles.py is THE
single source of truth for the per-feature needle vocabulary.

These tests pin the three properties the module exists to guarantee:
  1. SINGLE SOURCE -- palm_reading and claim_voicing read the SAME objects
     from here; no second needle literal survives anywhere in the package.
  2. NO CYCLE -- the leaf module imports nothing from agent.interpretive,
     which is the only reason both sides can import it. That property is
     load-bearing and silently breakable, so it is asserted structurally
     (on the module's own source), not just by "the import worked".
  3. THE DRIFT IS GONE -- claim_voicing._FEATURE_TRAIT_NEEDLES, the
     verbatim copy that had drifted to 10 features against the real 16,
     no longer exists in any form.
"""
from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

import pytest

from agent.interpretive import claim_voicing, feature_needles, palm_reading

_PKG_DIR = Path(feature_needles.__file__).parent


# ─── 1. Single source of truth ───────────────────────────────────────────


def test_palm_reading_and_claim_voicing_read_the_same_objects():
    """Not merely equal values -- the SAME dict object, so no copy can
    drift again. palm_reading imports the table under its own private
    names (an alias, not a copy); claim_voicing reads it directly."""
    assert palm_reading._OUTPUT_FEATURE_IDENTIFIERS is (
        feature_needles.OUTPUT_FEATURE_IDENTIFIERS
    )
    assert palm_reading._RETRIEVAL_NEEDLES is feature_needles.RETRIEVAL_NEEDLES
    assert palm_reading._FEATURE_NEEDLES_BASE is feature_needles.FEATURE_NEEDLES_BASE
    assert claim_voicing.OUTPUT_FEATURE_IDENTIFIERS is (
        feature_needles.OUTPUT_FEATURE_IDENTIFIERS
    )


def test_the_two_views_are_still_separately_addressable():
    """Step 6's guarantee, carried through the move: three distinct dict
    objects with identical values, so a future per-job value edit cannot
    reach the other job."""
    tables = (
        feature_needles.FEATURE_NEEDLES_BASE,
        feature_needles.RETRIEVAL_NEEDLES,
        feature_needles.OUTPUT_FEATURE_IDENTIFIERS,
    )
    assert len({id(t) for t in tables}) == 3
    assert (
        feature_needles.RETRIEVAL_NEEDLES
        == feature_needles.OUTPUT_FEATURE_IDENTIFIERS
        == feature_needles.FEATURE_NEEDLES_BASE
    )


def test_the_table_carries_all_sixteen_features():
    """The count is the whole point of Step 7: the drifted copy had 10."""
    assert len(feature_needles.FEATURE_NEEDLES_BASE) == 16
    for mount in (
        "mount of saturn",
        "mount of apollo",
        "mount of mercury",
        "mount of mars positive",
        "mount of mars negative",
        "mount of luna",
    ):
        assert mount in feature_needles.FEATURE_NEEDLES_BASE


def _is_needle_table(node: ast.Dict) -> bool:
    """The needle table's distinguishing SIGNATURE: each line feature maps
    to a tuple of strings CONTAINING that feature's own bare noun --
    "life line" -> ("life",), and so on.

    Deliberately narrower than "a dict keyed by feature names": this
    package legitimately holds several such dicts that are not needle
    tables and must not be flagged -- observation_extractor's
    feature->registry map and its feature->"Line of Life" display-name
    map, and palm_reading's feature->(field label, bullet label) map."""
    pairs = {
        k.value: v
        for k, v in zip(node.keys, node.values)
        if isinstance(k, ast.Constant) and isinstance(k.value, str)
    }
    for feature in ("life line", "head line", "heart line"):
        value = pairs.get(feature)
        if not isinstance(value, ast.Tuple):
            return False
        words = [e.value for e in value.elts if isinstance(e, ast.Constant)]
        if feature.split()[0] not in words:
            return False
    return True


def test_no_second_needle_literal_survives_in_the_package():
    """GREP-ASSERT (the Step 7 requirement), done structurally rather than
    by constant name: exactly ONE module in agent/interpretive/ may hold a
    needle-table literal, so a future re-transplant under a DIFFERENT name
    is caught too -- which is precisely how the deleted copy escaped
    notice, since it was named `_FEATURE_TRAIT_NEEDLES`, not
    `_SUPPORT_NEEDLES`."""
    offenders = sorted({
        path.name
        for path in _PKG_DIR.glob("*.py")
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.Dict) and _is_needle_table(node)
    })
    assert offenders == ["feature_needles.py"], (
        f"needle-table literal found outside the leaf module: {offenders}"
    )


def test_claim_voicing_no_longer_defines_the_drifted_copy():
    """The copy is DELETED, not re-synced or aliased. Both the attribute
    and any assignment to that name must be gone; a historical mention in
    a comment is intentional and does not count."""
    assert not hasattr(claim_voicing, "_FEATURE_TRAIT_NEEDLES")
    src = Path(claim_voicing.__file__).read_text(encoding="utf-8")
    assert not re.search(r"^_FEATURE_TRAIT_NEEDLES\s*[:=]", src, re.M)


# ─── 2. No circular import ───────────────────────────────────────────────


def test_leaf_module_imports_nothing_from_agent_interpretive():
    """The load-bearing LEAF property, asserted on the source rather than
    inferred from a successful import: an added sibling import would
    silently re-create the exact cycle this module was built to remove,
    and might not raise depending on import order."""
    tree = ast.parse(Path(feature_needles.__file__).read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    assert not [m for m in imported if m.startswith("agent")], imported


@pytest.mark.parametrize(
    "order",
    [
        "import agent.interpretive.claim_voicing, agent.interpretive.palm_reading",
        "import agent.interpretive.palm_reading, agent.interpretive.claim_voicing",
    ],
)
def test_both_modules_import_cleanly_in_either_order(order):
    """A cycle can be order-dependent, so both orders are exercised, each
    in a FRESH interpreter -- inside this process both modules are
    already in sys.modules, which would mask a real cycle entirely."""
    assert subprocess.run(
        [sys.executable, "-c", order],
        capture_output=True,
        cwd=Path(feature_needles.__file__).parents[2],
    ).returncode == 0
