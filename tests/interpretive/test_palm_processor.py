"""
tests/interpretive/test_palm_processor.py
Regression test locking agent.palm_processor's vision prompt menus to
data/ontology_registry.json's vision_relational_menus block (Generalization
steps 3/4-scan, S98) -- the exact drift this guards against is a per-line
ORIGIN/TERMINATION/CONVERGENCE/CONVERGENCE_LOCATION menu silently going
hardcoded/stale again (as vocab_reachability_scan.py's own copy did, missing
Line of Fate ORIGIN's "Plain of Mars" until step 4-scan re-derived it).

Deliberately does NOT snapshot the whole prompt string -- that would break
on any prose/wording edit unrelated to the menus themselves. Only asserts
the registry->prompt link: each menu's exact "{tok1 | tok2 | ...}" string
is present in the built prompt and reproduced by _menu(). No network, no
image, no API call -- _build_description_system_prompt is pure.
"""

from __future__ import annotations

import json
from pathlib import Path

from agent.palm_processor import _build_description_system_prompt, _menu

_REGISTRY_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "ontology_registry.json"
_VISION_RELATIONAL_MENUS: dict[str, dict[str, list[str]]] = json.loads(
    _REGISTRY_PATH.read_text(encoding="utf-8")
)["vision_relational_menus"]

_PROMPTS = {hand: _build_description_system_prompt(hand) for hand in ("left", "right")}


def _expected_menu_string(tokens: list[str]) -> str:
    return "{" + " | ".join(tokens) + "}"


def test_every_registry_menu_appears_verbatim_in_the_built_prompt():
    for feature, fields in _VISION_RELATIONAL_MENUS.items():
        if feature.startswith("_"):
            continue
        for field, tokens in fields.items():
            expected = _expected_menu_string(tokens)
            for hand, prompt in _PROMPTS.items():
                assert expected in prompt, (
                    f"{feature!r}/{field!r} menu {expected!r} not found verbatim "
                    f"in the built prompt for hand={hand!r}"
                )


def test_menu_helper_reproduces_the_same_string_for_every_registry_entry():
    for feature, fields in _VISION_RELATIONAL_MENUS.items():
        if feature.startswith("_"):
            continue
        for field, tokens in fields.items():
            assert _menu(feature, field) == _expected_menu_string(tokens)


def test_fate_line_origin_menu_includes_plain_of_mars():
    """Guards the specific drift step 4-scan found and fixed: Line of Fate's
    ORIGIN menu previously omitted "Plain of Mars" in a hardcoded copy
    elsewhere. Confirms the vision prompt itself carries this registry
    member, proving the menu is genuinely registry-sourced, not a second
    stale transcription."""
    assert "Plain of Mars" in _VISION_RELATIONAL_MENUS["Line of Fate"]["ORIGIN"]
    expected = _expected_menu_string(_VISION_RELATIONAL_MENUS["Line of Fate"]["ORIGIN"])
    for hand, prompt in _PROMPTS.items():
        assert "Plain of Mars" in prompt, f"'Plain of Mars' missing from built prompt for hand={hand!r}"
        assert expected in prompt
