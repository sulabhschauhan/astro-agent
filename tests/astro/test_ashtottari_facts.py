"""Tests for agent/astro/ashtottari_facts.build_ashtottari_applicability_facts.

No external oracle exists for applicability (JHora displays the Ashtottari table
regardless), so validation is (a) Sulabh's chart hand-worked to 0/3, and (b)
synthetic charts that flip each criterion. The Sulabh planet values are the
frozen longitudes/houses from the chart (asc Sagittarius, lagna lord Jupiter in
house 5, Rahu in house 3, Sun 352.52 / Moon 212.23). asc_lon_sidereal is set to
a representative Sagittarius degree (the exact natal value is immaterial to the
lagna-nakshatra criterion -- Sagittarius contains no Rahu nakshatra at any degree).

Hand-worked Sulabh verdict (all three NOT met):
  positional      : lagna lord Jupiter in house 5; kendras/trikonas from 5 =
                    {2,5,8,11}+{1,5,9}; Rahu in house 3 -> not in set -> False.
  paksha          : Sun 352.52 / Moon 212.23 -> elong 219.7 -> tithi 18 ->
                    Krishna; birth 00:30 -> night; rule wants night+Shukla or
                    day+Krishna -> False.
  lagna_nakshatra : Sagittarius lagna (Mula/P.Ashadha/U.Ashadha) -> no Rahu
                    nakshatra -> False.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from agent.chart_calculator import NAKSHATRAS
from agent.astro.ashtottari_facts import (
    build_ashtottari_applicability_facts,
    RAHU_NAKSHATRAS,
)

_IST = timezone(timedelta(hours=5, minutes=30))


def _sulabh_chart(local_dt=None, asc_lon=250.0):
    """Sulabh-like calculate_chart() dict (only the fields the composer reads)."""
    return {
        "birth_details": {"place": "Kolkata", "lat": 22.5726, "lon": 88.3639},
        "lagna_chart": {"ascendant": "Sagittarius", "ascendant_lord": "Jupiter"},
        "planetary_positions": {
            "Sun": {"longitude": 352.520, "house": 4},
            "Moon": {"longitude": 212.229, "house": 12},
            "Jupiter": {"longitude": 12.561, "house": 5},
            "Rahu": {"longitude": 328.398, "house": 3},
        },
        "meta": {
            "asc_lon_sidereal": asc_lon,
            "local_datetime": local_dt or datetime(1988, 4, 6, 0, 30, tzinfo=_IST),
        },
    }


# ── Sulabh anchor: 0 of 3 ────────────────────────────────────────────────────
def test_sulabh_zero_of_three():
    r = build_ashtottari_applicability_facts(_sulabh_chart())
    assert r["criteria_evaluated"] == 3
    assert r["criteria_met"] == 0

    pos = r["criteria"]["positional"]
    assert pos["applicable"] is False
    assert pos["lagna_lord"] == "Jupiter"
    assert pos["lagna_lord_house"] == 5
    assert pos["rahu_house"] == 3
    assert pos["rahu_in_lagna"] is False

    pak = r["criteria"]["paksha"]
    assert pak["paksha"] == "Krishna"
    assert pak["birth_period"] == "night"   # real sunrise at Kolkata; 00:30 is night
    assert pak["applicable"] is False

    nak = r["criteria"]["lagna_nakshatra"]
    assert nak["applicable"] is False
    assert nak["lagna_nakshatra"] in ("Mula", "Purva Ashadha", "Uttara Ashadha")


def test_no_collapsed_top_level_verdict():
    # Anchored-judgment guard (Working Style #9): there must be NO single
    # top-level pass/fail; only per-criterion verdicts + a count.
    r = build_ashtottari_applicability_facts(_sulabh_chart())
    assert "applicable" not in r
    assert set(r) == {"criteria", "criteria_met", "criteria_evaluated", "note"}


# ── Per-criterion flips ──────────────────────────────────────────────────────
def test_positional_true_when_rahu_in_trikona_from_lagna_lord():
    # Lagna lord Jupiter in house 5; put Rahu in house 9 (a trikona from 5).
    chart = _sulabh_chart()
    chart["planetary_positions"]["Rahu"]["house"] = 9
    pos = build_ashtottari_applicability_facts(chart)["criteria"]["positional"]
    assert pos["applicable"] is True


def test_positional_true_when_rahu_in_kendra_from_lagna_lord():
    chart = _sulabh_chart()
    chart["planetary_positions"]["Rahu"]["house"] = 8   # 4th from house 5
    pos = build_ashtottari_applicability_facts(chart)["criteria"]["positional"]
    assert pos["applicable"] is True


def test_positional_false_when_rahu_in_lagna_even_if_kendra():
    # Rahu in house 1 is the explicit exception, even though 1 is a trikona-from-1.
    chart = _sulabh_chart()
    chart["lagna_chart"]["ascendant_lord"] = "Jupiter"
    chart["planetary_positions"]["Jupiter"]["house"] = 1   # lord in lagna
    chart["planetary_positions"]["Rahu"]["house"] = 1      # Rahu in lagna
    pos = build_ashtottari_applicability_facts(chart)["criteria"]["positional"]
    assert pos["rahu_in_lagna"] is True
    assert pos["applicable"] is False


def test_lagna_nakshatra_true_in_ardra():
    # asc_lon 70 deg -> Ardra (66.67-80), a Rahu nakshatra.
    r = build_ashtottari_applicability_facts(_sulabh_chart(asc_lon=70.0))
    nak = r["criteria"]["lagna_nakshatra"]
    assert nak["lagna_nakshatra"] == "Ardra"
    assert nak["applicable"] is True


def test_paksha_true_day_birth_krishna():
    # Noon birth (day) + Sun/Moon unchanged (Krishna) -> night/Shukla rule's
    # day+Krishna arm -> applicable.
    chart = _sulabh_chart(local_dt=datetime(1988, 4, 6, 12, 0, tzinfo=_IST))
    pak = build_ashtottari_applicability_facts(chart)["criteria"]["paksha"]
    assert pak["paksha"] == "Krishna"
    assert pak["birth_period"] == "day"
    assert pak["applicable"] is True


def test_paksha_true_night_birth_shukla():
    # Night birth (00:30) + Sun 10 / Moon 100 -> elong 90 -> tithi 7 -> Shukla.
    chart = _sulabh_chart()
    chart["planetary_positions"]["Sun"]["longitude"] = 10.0
    chart["planetary_positions"]["Moon"]["longitude"] = 100.0
    pak = build_ashtottari_applicability_facts(chart)["criteria"]["paksha"]
    assert pak["paksha"] == "Shukla"
    assert pak["birth_period"] == "night"
    assert pak["applicable"] is True


# ── Fail-soft ────────────────────────────────────────────────────────────────
def test_empty_chart_returns_empty():
    assert build_ashtottari_applicability_facts({}) == {}


def test_missing_rahu_drops_only_positional():
    chart = _sulabh_chart()
    del chart["planetary_positions"]["Rahu"]
    r = build_ashtottari_applicability_facts(chart)
    assert "positional" not in r["criteria"]
    assert "paksha" in r["criteria"] and "lagna_nakshatra" in r["criteria"]
    assert r["criteria_evaluated"] == 2


def test_day_night_undetermined_marks_paksha_none():
    chart = _sulabh_chart()
    del chart["birth_details"]["lat"]        # cannot resolve sunrise
    pak = build_ashtottari_applicability_facts(chart)["criteria"]["paksha"]
    assert pak["birth_period"] == "undetermined"
    assert pak["applicable"] is None
    assert pak["paksha"] == "Krishna"        # paksha itself still resolves


def test_undetermined_daynight_not_counted_as_met():
    chart = _sulabh_chart()
    del chart["birth_details"]["lon"]
    r = build_ashtottari_applicability_facts(chart)
    # paksha applicable is None -> not counted; Sulabh's other two are False.
    assert r["criteria_met"] == 0


# ── Reachability contract ────────────────────────────────────────────────────
def test_rahu_nakshatras_exist_in_canonical_list():
    assert all(n in NAKSHATRAS for n in RAHU_NAKSHATRAS)
    assert len(RAHU_NAKSHATRAS) == 3
