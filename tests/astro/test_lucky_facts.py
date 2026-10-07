"""Tests for agent/astro/lucky_facts.py -- CALCULATED lucky/unlucky weekdays (S147).

Pure over chart_facts['house_lords']; no ephemeris, so these run anywhere. The
oracle is Sulabh's own chart (Sagittarius lagna), which the classical rule must
reproduce: Thursday/Tuesday/Sunday favourable, Friday/Monday to avoid."""
from __future__ import annotations

from agent.astro import capability_gate
from agent.astro.lucky_facts import build_lucky_facts, WEEKDAY_LORD


# Whole-Sign house lords for a Sagittarius ascendant (the live reference chart):
# 1 Jup, 2 Sat, 3 Sat, 4 Jup, 5 Mars, 6 Venus, 7 Mer, 8 Moon, 9 Sun, 10 Mer,
# 11 Venus, 12 Mars.
_SAG = {
    1: {"lord": "Jupiter"}, 2: {"lord": "Saturn"}, 3: {"lord": "Saturn"},
    4: {"lord": "Jupiter"}, 5: {"lord": "Mars"}, 6: {"lord": "Venus"},
    7: {"lord": "Mercury"}, 8: {"lord": "Moon"}, 9: {"lord": "Sun"},
    10: {"lord": "Mercury"}, 11: {"lord": "Venus"}, 12: {"lord": "Mars"},
}


def test_capability_gate_declares_lucky_unlucky():
    assert "lucky_unlucky" in capability_gate.FACT_BLOCK_PROVIDES


def test_weekday_lord_table_is_the_classical_seven():
    assert dict(WEEKDAY_LORD) == {
        "Sunday": "Sun", "Monday": "Moon", "Tuesday": "Mars",
        "Wednesday": "Mercury", "Thursday": "Jupiter", "Friday": "Venus",
        "Saturday": "Saturn"}


def test_sagittarius_oracle_reproduces_reference_verdicts():
    """The rule must match the reference chart's known output."""
    out = build_lucky_facts({"house_lords": _SAG})
    assert set(out["favourable_days"]) == {"Thursday", "Tuesday", "Sunday"}
    assert set(out["avoid_days"]) == {"Monday", "Friday"}
    # Wednesday (Mercury 7/10) and Saturday (Saturn 2/3) are neither -> neutral.
    assert out["weekdays"]["Wednesday"]["verdict"] == "neutral"
    assert out["weekdays"]["Saturday"]["verdict"] == "neutral"


def test_trikona_lordship_dominates_a_shared_dusthana():
    """Mars lords 5 (trikona) AND 12 (dusthana); trikona wins -> favourable.
    This is the choice that reproduces Tuesday-favourable; a 'mixed' verdict
    would contradict the reference chart."""
    out = build_lucky_facts({"house_lords": _SAG})
    tue = out["weekdays"]["Tuesday"]
    assert tue["lord"] == "Mars" and tue["houses_ruled"] == [5, 12]
    assert tue["verdict"] == "favourable"


def test_pure_dusthana_lord_is_avoided():
    """Venus lords 6 (dusthana) and 11 (upachaya, not trikona) -> avoid."""
    out = build_lucky_facts({"house_lords": _SAG})
    assert out["weekdays"]["Friday"]["verdict"] == "avoid"


def test_string_and_int_house_keys_agree():
    """pipeline._fact_block tolerates both int and str house keys; so must this."""
    as_str = {str(k): v for k, v in _SAG.items()}
    assert build_lucky_facts({"house_lords": as_str}) == \
        build_lucky_facts({"house_lords": _SAG})


def test_every_weekday_is_classified():
    out = build_lucky_facts({"house_lords": _SAG})
    assert set(out["weekdays"]) == {d for d, _ in WEEKDAY_LORD}
    for day in out["weekdays"]:
        assert out["weekdays"][day]["verdict"] in {"favourable", "avoid", "neutral"}


def test_fail_soft_on_missing_house_lords():
    assert build_lucky_facts({}) == {}
    assert build_lucky_facts(None) == {}
    assert build_lucky_facts({"house_lords": {}}) == {}


def test_partial_house_lords_do_not_raise():
    """A chart missing some lords still classifies the weekdays it can."""
    out = build_lucky_facts({"house_lords": {1: {"lord": "Jupiter"}}})
    assert out["weekdays"]["Thursday"]["verdict"] == "favourable"
    # a lord with no houses -> neutral, never an error
    assert out["weekdays"]["Monday"]["verdict"] == "neutral"


def test_malformed_lord_entries_are_skipped():
    """Entries without a 'lord' key are ignored, not fatal."""
    hl = {1: {"lord": "Jupiter"}, 2: {}, 3: None, 4: {"sign": "Pisces"}}
    out = build_lucky_facts({"house_lords": hl})
    assert out["weekdays"]["Thursday"]["houses_ruled"] == [1]
