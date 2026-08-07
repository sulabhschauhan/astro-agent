"""
tests/interpretive/test_observation_to_tokens.py
Tests for agent/interpretive/observation_to_tokens.py's to_tokens()
adapter. Hardest case first (compound valid + dropped invalid value +
defaulted missing confidence, all in one payload), per this task's own
instruction, then focused unit coverage for each sub-behavior.
"""

from __future__ import annotations

import pytest

from agent.interpretive.observation_to_tokens import to_tokens


# ─── HARDEST CASE (a + b + c combined) ───────────────────────────────────


def test_hardest_case_valid_compound_plus_dropped_value_plus_defaulted_confidence():
    # (a) valid compound: Line of Heart/Position=high AND Quadrangle/
    #     Breadth=narrow -- this is the REAL antecedent shape of the
    #     Sulabh-verified rule HL_006 in data/palm_rules_head_heart_v1.json,
    #     so a real fired rule depends on this surviving intact.
    # (b) out-of-registry value: Line of Head/Length="gigantic" is not in
    #     ontology_registry.json's length_values -- must be dropped, not
    #     coerced to the nearest real token.
    # (c) missing magnitude: the Quadrangle/Breadth entry supplies no
    #     "confidence" key at all -- must default to 1.0.
    payload = {
        "Line of Heart": {
            "Position": {"value": "high", "confidence": 0.92},
        },
        "Quadrangle": {
            "Breadth": {"value": "narrow"},  # no confidence -> default 1.0
        },
        "Line of Head": {
            "Length": {"value": "gigantic", "confidence": 0.7},  # not a real token
        },
    }

    observation, magnitudes = to_tokens(payload)

    # (a) valid compound survives into observation, untouched.
    assert observation["Line of Heart"]["Position"] == "high"
    assert observation["Quadrangle"]["Breadth"] == "narrow"

    # (b) invalid value dropped from observation, but recorded.
    assert "Line of Head" not in observation or "Length" not in observation.get("Line of Head", {})
    assert {"feature": "Line of Head", "attribute": "Length", "value": "gigantic"} in magnitudes["_dropped"]

    # (c) missing confidence defaults to 1.0 -- and magnitudes is an
    #     UNFILTERED passthrough, so the dropped Line of Head/Length entry
    #     still carries its own (valid) confidence float.
    assert magnitudes["Line of Heart"]["Position"] == 0.92
    assert magnitudes["Quadrangle"]["Breadth"] == 1.0
    assert magnitudes["Line of Head"]["Length"] == 0.7


# ─── THICKNESS -> WIDTH CANONICALIZATION (line features only) ────────────
# Real, verified silence: Width and Thickness are both valid registry
# attributes for line features, and 'narrow' is a valid value for both, so
# the extractor may emit a line's thinness as either -- but zero line
# rules key on Thickness (all 5 that care key on Width). See
# _canonicalize_thickness_to_width() in observation_to_tokens.py.
# Hardest case first: the collision (both attributes present).


def test_width_and_thickness_both_present_width_wins_thickness_dropped():
    payload = {
        "Line of Life": {
            "Width": {"value": "narrow", "confidence": 1.0},
            "Thickness": {"value": "narrow", "confidence": 0.6},
        },
    }
    observation, magnitudes = to_tokens(payload)

    assert observation["Line of Life"] == {"Width": "narrow"}
    assert magnitudes["Line of Life"]["Width"] == 1.0
    assert "Thickness" not in observation["Line of Life"]
    assert "Thickness" not in magnitudes["Line of Life"]
    assert {
        "feature": "Line of Life",
        "from": "Thickness",
        "to": "Width",
        "action": "dropped_dup",
        "value": "narrow",
        "confidence": 0.6,
    } in magnitudes["_canonicalized"]


def test_thickness_only_renamed_to_width_the_athira_silence_case():
    payload = {
        "Line of Life": {
            "Thickness": {"value": "narrow", "confidence": 0.6},
        },
    }
    observation, magnitudes = to_tokens(payload)

    assert observation["Line of Life"] == {"Width": "narrow"}
    assert magnitudes["Line of Life"]["Width"] == 0.6
    assert "Thickness" not in observation["Line of Life"]
    assert "Thickness" not in magnitudes["Line of Life"]
    assert {
        "feature": "Line of Life",
        "from": "Thickness",
        "to": "Width",
        "action": "renamed",
        "value": "narrow",
        "confidence": 0.6,
    } in magnitudes["_canonicalized"]


def test_width_and_thickness_different_values_width_still_wins_deterministically():
    payload = {
        "Line of Life": {
            "Width": {"value": "narrow", "confidence": 1.0},
            "Thickness": {"value": "broad", "confidence": 0.8},
        },
    }
    observation, magnitudes = to_tokens(payload)

    assert observation["Line of Life"] == {"Width": "narrow"}
    assert magnitudes["Line of Life"]["Width"] == 1.0
    assert "Thickness" not in observation["Line of Life"]
    assert "Thickness" not in magnitudes["Line of Life"]
    assert {
        "feature": "Line of Life",
        "from": "Thickness",
        "to": "Width",
        "action": "dropped_dup",
        "value": "broad",
        "confidence": 0.8,
    } in magnitudes["_canonicalized"]


def test_non_line_feature_thickness_left_untouched_scope_guard():
    payload = {
        "Thumb": {
            "Thickness": {"value": "thick", "confidence": 0.9},
        },
    }
    observation, magnitudes = to_tokens(payload)

    assert observation["Thumb"]["Thickness"] == "thick"
    assert magnitudes["Thumb"]["Thickness"] == 0.9
    assert magnitudes["_canonicalized"] == []


def test_line_of_head_thickness_only_renamed_to_width():
    payload = {
        "Line of Head": {
            "Thickness": {"value": "narrow", "confidence": 0.75},
        },
    }
    observation, magnitudes = to_tokens(payload)

    assert observation["Line of Head"] == {"Width": "narrow"}
    assert magnitudes["Line of Head"]["Width"] == 0.75
    assert {
        "feature": "Line of Head",
        "from": "Thickness",
        "to": "Width",
        "action": "renamed",
        "value": "narrow",
        "confidence": 0.75,
    } in magnitudes["_canonicalized"]


def test_line_of_sun_thickness_not_canonicalized_width_not_valid_there():
    # "Line of Sun" is in the registry's "lines" category but is NOT in
    # attribute_feature_mapping["Width"] (VERIFIED against
    # data/ontology_registry.json) -- so the tightened _LINE_FEATURES
    # (lines ∩ Width-valid) excludes it, and Thickness must NOT be
    # canonicalized for it. "Line of Sun" is also absent from
    # attribute_feature_mapping["Thickness"] (VERIFIED), so its Thickness
    # entry follows the normal validation path and is dropped as an
    # invalid (feature, attribute, value) triple -- not renamed, not kept.
    payload = {
        "Line of Sun": {
            "Thickness": {"value": "narrow", "confidence": 0.6},
        },
    }
    observation, magnitudes = to_tokens(payload)

    assert "Line of Sun" not in observation
    assert magnitudes["_canonicalized"] == []
    assert {"feature": "Line of Sun", "attribute": "Thickness", "value": "narrow"} in magnitudes["_dropped"]
    # Unfiltered passthrough still records the confidence under Thickness
    # (magnitudes is never gated by observation validity -- see module
    # docstring's "Design decision: magnitudes are unfiltered").
    assert magnitudes["Line of Sun"]["Thickness"] == 0.6


# ─── OBSERVATION FILTERING (registry validation) ─────────────────────────


def test_unknown_feature_entirely_dropped():
    payload = {"Some Unknown Feature": {"Position": {"value": "high"}}}
    observation, magnitudes = to_tokens(payload)
    assert observation == {}
    assert {"feature": "Some Unknown Feature", "attribute": "Position", "value": "high"} in magnitudes["_dropped"]


def test_unknown_attribute_for_a_real_feature_dropped():
    # "Line of Heart" is a real registry feature, but "Bogus_Attribute" is
    # not in attribute_feature_mapping at all.
    payload = {"Line of Heart": {"Bogus_Attribute": {"value": "high"}}}
    observation, magnitudes = to_tokens(payload)
    assert observation == {}
    assert {"feature": "Line of Heart", "attribute": "Bogus_Attribute", "value": "high"} in magnitudes["_dropped"]


def test_attribute_valid_but_not_for_this_feature_dropped():
    # "Angle" is a real attribute (attribute_feature_mapping["Angle"] ==
    # {"Thumb"}), but never valid for "Line of Heart".
    payload = {"Line of Heart": {"Angle": {"value": "right_angle"}}}
    observation, magnitudes = to_tokens(payload)
    assert observation == {}
    assert {"feature": "Line of Heart", "attribute": "Angle", "value": "right_angle"} in magnitudes["_dropped"]


def test_non_string_value_dropped_not_coerced():
    payload = {"Line of Heart": {"Position": {"value": None}}}
    observation, magnitudes = to_tokens(payload)
    assert observation == {}
    assert {"feature": "Line of Heart", "attribute": "Position", "value": None} in magnitudes["_dropped"]


def test_no_drops_key_is_always_present_even_when_empty():
    payload = {"Line of Heart": {"Position": {"value": "high"}}}
    _, magnitudes = to_tokens(payload)
    assert magnitudes["_dropped"] == []


# ─── MALFORMED PAYLOAD -> MEANINGFUL ERROR NAMING THE BAD KEY ────────────


def test_non_dict_payload_raises_value_error():
    with pytest.raises(ValueError, match="vision_payload must be a dict"):
        to_tokens(["not", "a", "dict"])  # type: ignore[arg-type]


def test_feature_mapping_to_non_dict_raises_naming_the_feature():
    with pytest.raises(ValueError, match=r"feature key 'Line of Heart'"):
        to_tokens({"Line of Heart": "not a dict of attributes"})


def test_entry_missing_value_key_raises_naming_feature_and_attribute():
    with pytest.raises(ValueError, match=r"feature='Line of Heart', attribute='Position'"):
        to_tokens({"Line of Heart": {"Position": {"confidence": 0.9}}})  # no "value" key


def test_entry_not_a_dict_raises_naming_feature_and_attribute():
    with pytest.raises(ValueError, match=r"feature='Line of Heart', attribute='Position'"):
        to_tokens({"Line of Heart": {"Position": "high"}})  # bare string, not {"value": ...}


# ─── EMPTY INPUT ──────────────────────────────────────────────────────────


def test_empty_payload_returns_empty_observation_and_only_dropped_key():
    observation, magnitudes = to_tokens({})
    assert observation == {}
    assert magnitudes == {"_dropped": [], "_canonicalized": []}
