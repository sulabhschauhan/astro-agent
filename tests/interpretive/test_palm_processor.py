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

from agent.palm_processor import (
    _build_description_system_prompt,
    _contacts_field,
    _flat_subfield_menu,
    _menu,
)
from agent.interpretive.observation_extractor import _FLAT_SUBFIELD_REGISTRY

_REGISTRY_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "ontology_registry.json"
_REGISTRY: dict = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
_VISION_RELATIONAL_MENUS: dict[str, dict[str, list[str]]] = _REGISTRY["vision_relational_menus"]
_VISION_FLAT_SUBFIELDS: dict[str, dict[str, dict]] = _REGISTRY["vision_flat_subfields"]
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


def test_convergence_menu_is_derived_from_convergence_lines_for_line_of_life_only():
    """CONVERGENCE is retired for Head/Heart/Fate (typed-relationship arc
    Step 5d, S99, superseded by the typed RELATIONSHIP channel -- itself
    retired S107 in favor of CONTACTS) -- Line of Life is now the ONLY
    line that still emits a CONVERGENCE field. Its menu must still equal
    convergence_lines MINUS Life itself, and that exact "{...}" string
    must appear verbatim in the built prompt for both hands. Narrowed from
    the original 4-line tuple ("Line of Life", "Line of Head", "Line of
    Heart", "Line of Fate") -- the parallel assertion below preserves
    coverage for Head/Heart/Fate by confirming each still carries its own
    CONTACTS field, the channel that now carries relational-verb reporting
    for those three lines."""
    feature = "Line of Life"
    expected_tokens = [line for line in _CONVERGENCE_LINES if line != feature]
    expected = _expected_menu_string(expected_tokens)
    assert _menu(feature, "CONVERGENCE") == expected
    for hand, prompt in _PROMPTS.items():
        assert expected in prompt, (
            f"{feature!r} CONVERGENCE menu {expected!r} not found verbatim "
            f"in the built prompt for hand={hand!r}"
        )

    # Parallel assertion (coverage preserved, not lost): Head/Heart/Fate
    # each still carry their own, distinctly-menued CONTACTS field.
    for other_feature in ("Line of Head", "Line of Heart", "Line of Fate"):
        expected_field = _contacts_field(other_feature)
        for hand, prompt in _PROMPTS.items():
            assert expected_field in prompt, (
                f"{other_feature!r} CONTACTS field not found in built "
                f"prompt for hand={hand!r}"
            )


def test_head_and_heart_have_a_contacts_field():
    """Was test_head_and_heart_now_have_a_convergence_field, which proved
    Head/Heart each carried a CONVERGENCE field with its own distinct menu
    (added by the Generic convergence emission step, S98). Repurposed for
    CONVERGENCE's retirement on these two lines (typed-relationship arc
    Step 5d, S99): proved the opposite for CONVERGENCE (neither line's old
    field sentence remains) and the equivalent presence+distinctness for
    RELATIONSHIP, the field that took over the channel. S107 retired
    RELATIONSHIP in turn -- CONTACTS is now the sole relational-verb
    channel, so this test asserts against it instead."""
    head_convergence_menu = _expected_menu_string([l for l in _CONVERGENCE_LINES if l != "Line of Head"])
    heart_convergence_menu = _expected_menu_string([l for l in _CONVERGENCE_LINES if l != "Line of Heart"])
    head_field = _contacts_field("Line of Head")
    heart_field = _contacts_field("Line of Heart")
    assert head_field != heart_field  # distinct target menus prove these are two separate fields, not one shared string
    for hand, prompt in _PROMPTS.items():
        assert head_field in prompt, f"Line of Head CONTACTS field not found in built prompt for hand={hand!r}"
        assert heart_field in prompt, f"Line of Heart CONTACTS field not found in built prompt for hand={hand!r}"
        assert f'CONVERGENCE: for each other line this one clearly crosses or joins, write a separate "CONVERGENCE: <line>" line choosing only from {head_convergence_menu}' not in prompt
        assert f'CONVERGENCE: for each other line this one clearly crosses or joins, write a separate "CONVERGENCE: <line>" line choosing only from {heart_convergence_menu}' not in prompt


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


# ─── SLOPE MAGNITUDE -- S123 Step 3 ────────────────────────────────────────
# Guards the registry<->prompt link for the ONE vision_flat_subfields field
# currently routed through _flat_subfield_menu() (SLOPE, BREAK TYPE, LENGTH
# EXTENT remain hand-typed -- see _build_description_system_prompt's own
# docstring for why, a Step 6 candidate not done here). Two separate guards,
# per the instructing prompt: the MENU must never drift from the registry,
# and the LABEL must stay byte-identical to the registry key
# extract_flat_subfields's own regex is built from.


def test_slope_magnitude_menu_matches_registry_for_every_declaring_line():
    """The rendered SLOPE MAGNITUDE menu ("{tok1 | tok2 | ...}") must equal
    vision_flat_subfields[feature]["SLOPE MAGNITUDE"]["menu"] exactly, for
    every line that declares the field (Head/Heart/Fate) -- both via the
    helper directly and verbatim inside the built prompt for both hands, so
    prompt and registry can never silently drift apart."""
    for feature, fields in _VISION_FLAT_SUBFIELDS.items():
        if feature.startswith("_") or "SLOPE MAGNITUDE" not in fields:
            continue
        expected = _expected_menu_string(fields["SLOPE MAGNITUDE"]["menu"])
        assert _flat_subfield_menu(feature, "SLOPE MAGNITUDE") == expected
        for hand, prompt in _PROMPTS.items():
            assert expected in prompt, (
                f"{feature!r} SLOPE MAGNITUDE menu {expected!r} not found verbatim "
                f"in the built prompt for hand={hand!r}"
            )


def test_slope_magnitude_label_is_byte_identical_to_the_extractor_registry_key():
    """The literal "SLOPE MAGNITUDE:" label emitted in the prompt must match,
    byte-for-byte, the registry key
    observation_extractor.extract_flat_subfields's own regex is built from
    (_FLAT_SUBFIELD_REGISTRY, S123 Step 2) -- a label typo here would silently
    desync the ask from the reader even though both ultimately read the same
    registry block, since the prompt's label text is still a separate hand-
    typed literal from the regex-building code path. Checked against BOTH
    ends independently: the registry itself declares the key, and the
    extractor's own derived structure (not a second hand-copy) carries it
    too."""
    for feature in ("Line of Head", "Line of Heart", "Line of Fate"):
        assert "SLOPE MAGNITUDE" in _VISION_FLAT_SUBFIELDS[feature]
        assert "SLOPE MAGNITUDE" in _FLAT_SUBFIELD_REGISTRY[feature]
    for hand, prompt in _PROMPTS.items():
        # 3 occurrences: once each for Head, Heart, Fate.
        assert prompt.count("  SLOPE MAGNITUDE:") == 3, (
            f"expected exactly 3 'SLOPE MAGNITUDE:' labels (Head/Heart/Fate) "
            f"in the built prompt for hand={hand!r}, found "
            f"{prompt.count('  SLOPE MAGNITUDE:')}"
        )
