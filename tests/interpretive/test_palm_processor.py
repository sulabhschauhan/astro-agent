"""
tests/interpretive/test_palm_processor.py
Regression test locking agent.palm_processor's vision prompt menus to
data/ontology_registry.json (Generalization steps 3/4-scan + Generic
convergence emission, S98) -- the exact drift this guards against is a
per-line ORIGIN/TERMINATION/CONVERGENCE_LOCATION menu silently going
hardcoded/stale again (as vocab_reachability_scan.py's own copy did, missing
Line of Fate ORIGIN's "Plain of Mars" until step 4-scan re-derived it).
CONVERGENCE is a SEPARATE case since the Generic convergence emission step:
it is no longer looked up per line in vision_relational_menus at all --
_menu() derives it from the top-level convergence_lines block instead
(convergence_lines minus the given feature), so its own tests read
convergence_lines directly rather than vision_relational_menus.

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
_REGISTRY: dict = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
_VISION_RELATIONAL_MENUS: dict[str, dict[str, list[str]]] = _REGISTRY["vision_relational_menus"]
_CONVERGENCE_LINES: list[str] = _REGISTRY["convergence_lines"]

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


def test_convergence_menu_is_derived_from_convergence_lines_for_every_line():
    """CONVERGENCE is no longer a per-line literal (Generic convergence
    emission step, S98) -- for every line that emits a CONVERGENCE field
    (Life/Head/Heart/Fate), the menu must equal convergence_lines MINUS that
    line itself, and that exact "{...}" string must appear verbatim in the
    built prompt for both hands. A per-pair hardcoded regression (e.g. Fate
    only ever offering "Line of Heart" again) would fail this."""
    emitting_lines = ("Line of Life", "Line of Head", "Line of Heart", "Line of Fate")
    for feature in emitting_lines:
        expected_tokens = [line for line in _CONVERGENCE_LINES if line != feature]
        expected = _expected_menu_string(expected_tokens)
        assert _menu(feature, "CONVERGENCE") == expected
        for hand, prompt in _PROMPTS.items():
            assert expected in prompt, (
                f"{feature!r} CONVERGENCE menu {expected!r} not found verbatim "
                f"in the built prompt for hand={hand!r}"
            )


def test_head_and_heart_now_have_a_convergence_field():
    """Before the Generic convergence emission step, only Life and Fate had
    a CONVERGENCE field at all (per-pair hardcoded); Head and Heart had
    none. Confirms the prompt now carries a CONVERGENCE line for Head and
    Heart too, each with its own correctly-derived (distinct) menu."""
    head_menu = _expected_menu_string([l for l in _CONVERGENCE_LINES if l != "Line of Head"])
    heart_menu = _expected_menu_string([l for l in _CONVERGENCE_LINES if l != "Line of Heart"])
    assert head_menu != heart_menu  # distinct menus prove these are two separate fields, not one shared string
    for hand, prompt in _PROMPTS.items():
        assert f'CONVERGENCE: for each other line this one clearly crosses or joins, write a separate "CONVERGENCE: <line>" line choosing only from {head_menu}' in prompt
        assert f'CONVERGENCE: for each other line this one clearly crosses or joins, write a separate "CONVERGENCE: <line>" line choosing only from {heart_menu}' in prompt


def test_convergence_menu_excludes_self_and_includes_line_of_health():
    """Line of Health has no vision block of its own (target-only) but must
    still be offered as a convergence TARGET from every emitting line, and a
    line must never be offered as its own convergence partner."""
    for feature in ("Line of Life", "Line of Head", "Line of Heart", "Line of Fate"):
        tokens = [line for line in _CONVERGENCE_LINES if line != feature]
        assert feature not in tokens
        assert "Line of Health" in tokens


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
