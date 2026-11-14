"""Pure-function tests for the Terra cost + depth harness. No OpenAI, no production
imports beyond the harness module's stdlib-only top level. Run:

    pytest tests/test_terra_cost_validation.py -q
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "scripts"))

from terra_cost_validation import (  # noqa: E402
    compute_cost, bucket_thirds, depth_attribution, _tier_for, TIER_THRESHOLD)

# Synthetic rate card mirroring diagnostics/model_rates.json's shape.
RATES = {
    "_meta": {"service_tier_multipliers": {"standard": 1.0, "flex": 0.5, "fast": 2.0}},
    "models": {
        "gpt-6.1-terra": {
            "short": {"input": 1.0, "cached": 0.05, "cache_write": 1.25, "output": 5.0},
            "long":  {"input": 2.0, "cached": 0.10, "cache_write": 2.50, "output": 7.5},
        }
    },
}


def test_tier_boundary_is_inclusive_at_threshold():
    assert _tier_for(TIER_THRESHOLD) == "short"       # exactly 272k -> short
    assert _tier_for(TIER_THRESHOLD + 1) == "long"    # one over -> long


def test_short_tier_standard():
    c = compute_cost("gpt-6.1-terra", 100_000, 0, 1_000, RATES, "standard")
    # 100k input @ $1 = 0.10 ; 1k output @ $5 = 0.005
    assert c["tier"] == "short"
    assert round(c["usd_total"], 6) == 0.105


def test_long_tier_doubles_input_and_lifts_output():
    c = compute_cost("gpt-6.1-terra", 500_000, 0, 1_000, RATES, "standard")
    # 500k @ $2 = 1.00 ; 1k @ $7.5 = 0.0075
    assert c["tier"] == "long"
    assert round(c["usd_total"], 6) == 1.0075


def test_flex_halves_everything():
    std = compute_cost("gpt-6.1-terra", 500_000, 0, 1_000, RATES, "standard")["usd_total"]
    flex = compute_cost("gpt-6.1-terra", 500_000, 0, 1_000, RATES, "flex")["usd_total"]
    assert round(flex, 6) == round(std * 0.5, 6)


def test_cached_tokens_priced_at_cached_rate():
    c = compute_cost("gpt-6.1-terra", 100_000, 40_000, 0, RATES, "standard")
    # 60k non-cached @ $1 = 0.06 ; 40k cached @ $0.05 = 0.002
    assert round(c["usd_total"], 6) == 0.062


def test_unknown_model_and_tier_raise():
    import pytest
    with pytest.raises(KeyError):
        compute_cost("nope", 1000, 0, 0, RATES, "standard")
    with pytest.raises(KeyError):
        compute_cost("gpt-6.1-terra", 1000, 0, 0, RATES, "warp-speed")


def _payload(seg_texts, unit_texts=()):
    return {"segments": [{"segment_id": f"s{i}", "text": t, "kept": True}
                         for i, t in enumerate(seg_texts)],
            "units": [{"unit_id": f"u{i}", "text": t} for i, t in enumerate(unit_texts)]}


def test_bucket_thirds_splits_in_reading_order():
    # distinct alpha-only tokens (the depth regex ignores digits, by design)
    pl = _payload([f"token{chr(97 + i)} wordword content" for i in range(9)])
    thirds = bucket_thirds(pl)
    labels = [lbl for lbl, _ in thirds]
    assert labels == ["first", "middle", "last"]
    # first third is segs 0-2 (tokena..tokenc); seg 8 (tokeni) is in the last third
    first_tokens = dict(thirds)["first"]
    assert "tokena" in first_tokens and "tokeni" not in first_tokens


def test_depth_attribution_distinguishes_last_third_grounding():
    pl = _payload(["firstword aaaa bbbb", "firstword cccc dddd",   # first third
                   "middleword eeee ffff", "middleword gggg hhhh", # middle
                   "lastword iiii jjjj", "lastword kkkk llll"])     # last
    thirds = bucket_thirds(pl)
    only_last = depth_attribution("the reading rests on iiii and kkkk and llll", thirds)
    assert only_last["last"] > 0 and only_last["middle_last_share"] == 1.0

    only_first = depth_attribution("the reading rests on aaaa and bbbb and cccc", thirds)
    assert only_first["middle"] == 0 and only_first["last"] == 0
    assert only_first["middle_last_share"] == 0.0
