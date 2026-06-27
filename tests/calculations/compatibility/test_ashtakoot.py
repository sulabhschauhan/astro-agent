"""Tests for agent/calculations/compatibility/ashtakoot.py -- P2.4.2
Ashtakoot composite scorer (end-to-end orchestration over all 8 kootas).

AstroSage reference pair: Sulabh (boy) x Surbhi (girl), same
calculate_chart() derivation path as test_trivial.py / test_sign_lord.py /
test_matrix.py. AC-1 is the end-to-end parity test: all 8 individual
koota scores plus the composite total must match the locked AstroSage
fixture simultaneously (27.5/36, "Preferable", no active doshas).

AC-2/AC-3 reuse the synthetic empirical-lock pairs from P2.4.1c's Nadi
work (Delhi, 12:00, fixed dates) -- "Pair 2" and "Pair 3" in that design
chat's numbering. Delhi is already geocoded in
tests/fixtures/geocoded_locations.json (added in P2.4.1c).

AC-5 (Marginal band): per the implementation prompt, the only listed
real fixture in this band's *neighborhood* ("Pair 1", 1995-02-27 boy x
1995-01-24 girl, Delhi) actually totals 23/36 -- "Preferable", not
Marginal. No prior fixture in this test suite lands in [12.0, 17.5], so
per the prompt's own fallback instruction, a synthetic KootaNatalInfo
pair is constructed directly. Hand-verified before writing the
assertion: boy=(moon_sign=3 Cancer, nak=0 Ashwini) x
girl=(moon_sign=8 Sagittarius half0, nak=6 Punarvasu) ->
Varna 1.0 + Vashya 1.5 + Tara 1.5 + Yoni 2.0 + GrahaMaitri 4.0 +
Gana 6.0 + Bhakoot 0.0 (Cancer-Sagittarius {6,8}, Moon-Jupiter
asymmetric-Friend, STRICT-rejected, same as sign_lord.py's BK-5) +
Nadi 0.0 (both Adi) = 16.0, comfortably inside [12.0, 17.5].

AC-3 NOTE: the implementation prompt's locked oracle total for Pair 3
was "5/36". Originally hand-verified against the 8 sub-scores as they
stood at the time (Varna 1.0, Vashya 1.0, Tara 1.5, Yoni 1.0,
GrahaMaitri 0.5, Gana 1.0, Bhakoot 0.0, Nadi 0.0 -- summing to 6.0) and
provisionally written off as a transcription slip, since Bhakoot and
Nadi both matched their independently-locked values exactly.

Root cause identified: that conclusion was wrong. AstroSage gives 0 for
Manushya x Rakshasa Gana (this pair's actual cell -- Bharani boy is
Manushya, Chitra girl is Rakshasa); classical majority (AstroVed,
AstroBix, multiple other sources) gives 1. _ashtakoot_tables.py's
GANA_SCORE table was corrected to follow AstroSage per the module's
locked three-tier source hierarchy (see that file's Gana section
comment for the full citation). With Gana now 0.0 instead of 1.0, the
total is 5.0, matching the AstroSage oracle exactly -- not a
transcription slip after all, but a genuine table defect on this one
cell, now fixed.
"""

import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import pytest
import swisseph as swe

import agent.calculations.transits.chandrabala as chandrabala_module
import agent.calculations.transits.tarabala as tarabala_module
from agent.calculations.compatibility import _ashtakoot_tables as ak
from agent.calculations.compatibility.ashtakoot import compute_ashtakoot_compatibility
from agent.calculations.compatibility.koota_types import AshtakootResult, KootaNatalInfo
from agent.chart_calculator import _calc_planets, calculate_chart


def _natal_info(name: str, dob: str, tob: str, place: str) -> KootaNatalInfo:
    """Real natal info via calculate_chart() -- identical derivation path to
    test_trivial.py / test_sign_lord.py / test_matrix.py's helper of the
    same name (not imported from there; each test file derives its own
    fixtures per the project's per-module duplication convention).
    """
    chart = calculate_chart(name, dob, tob, place)
    jd_ut = chart["meta"]["jd_ut"]
    asc_lon = chart["meta"]["asc_lon_sidereal"]
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    moon_longitude = _calc_planets(jd_ut, asc_lon)["Moon"]["longitude"]
    moon_sign = chandrabala_module._moon_sign(jd_ut)
    nakshatra = tarabala_module._moon_nakshatra(jd_ut)
    return KootaNatalInfo(
        moon_sign=moon_sign, moon_longitude=moon_longitude, nakshatra=nakshatra
    )


def _sulabh() -> KootaNatalInfo:
    return _natal_info("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")


def _surbhi() -> KootaNatalInfo:
    return _natal_info("Surbhi", "11 Sep 1992", "10:30", "Patna, India")


# ── AC-1: AstroSage end-to-end reference parity ─────────────────────────────

def test_ac1_sulabh_surbhi_astrosage_reference_full_parity():
    result = compute_ashtakoot_compatibility(_sulabh(), _surbhi())

    assert result.total_score == 27.5
    assert result.max_score == 36
    assert result.interpretation == "Preferable"
    assert result.doshas == []

    # All 8 per-koota scores, individually -- proves end-to-end wiring,
    # not just that the sum happens to match.
    assert result.kootas["Varna"].score == 1.0
    assert result.kootas["Vashya"].score == 1.0
    assert result.kootas["Tara"].score == 3.0
    assert result.kootas["Yoni"].score == 1.0
    assert result.kootas["GrahaMaitri"].score == 0.5
    assert result.kootas["Gana"].score == 6.0
    assert result.kootas["Bhakoot"].score == 7.0
    assert result.kootas["Nadi"].score == 8.0


# ── AC-2: Nadi dosha active (Pair 2, both Madhya Nadi) ──────────────────────

def test_ac2_pair2_nadi_dosha_active():
    boy = _natal_info("AC2-Boy", "1995-02-13", "12:00", "Delhi, India")
    girl = _natal_info("AC2-Girl", "1995-03-13", "12:00", "Delhi, India")
    result = compute_ashtakoot_compatibility(boy, girl)

    assert "Nadi_Dosha" in result.doshas
    assert result.kootas["Nadi"].score == 0.0
    assert result.warnings != ()


# ── AC-3: Bhakoot dosha active + Nadi dosha active (Pair 3) ────────────────

def test_ac3_pair3_bhakoot_and_nadi_dosha_verified_total_5_of_36():
    # See module docstring's "AC-3 NOTE" -- the prompt's locked oracle
    # total (5/36) reflects a genuine GANA_SCORE table defect
    # (Manushya x Rakshasa was 1, corrected to 0 to match AstroSage),
    # not a transcription slip; 5.0 is the AstroSage-parity value.
    boy = _natal_info("AC3-Boy", "1995-03-06", "12:00", "Delhi, India")
    girl = _natal_info("AC3-Girl", "1995-02-19", "12:00", "Delhi, India")
    result = compute_ashtakoot_compatibility(boy, girl)

    assert result.total_score == 5.0
    assert result.interpretation == "Not Preferable"
    assert any(d.startswith("Bhakoot_") for d in result.doshas)
    assert "Nadi_Dosha" in result.doshas
    assert result.kootas["Bhakoot"].score == 0.0
    assert result.kootas["Nadi"].score == 0.0
    assert result.kootas["Gana"].score == 0.0


# ── AC-4: Bhakoot dosha cancelled (same-lord case) ──────────────────────────

def test_ac4_aries_scorpio_bhakoot_same_lord_cancelled():
    # Both Mars-lord, (6,8) distance -- same as sign_lord.py's BK-2.
    boy = KootaNatalInfo(moon_sign=0, moon_longitude=15.0, nakshatra=2)
    girl = KootaNatalInfo(moon_sign=7, moon_longitude=225.0, nakshatra=17)
    result = compute_ashtakoot_compatibility(boy, girl)

    assert result.kootas["Bhakoot"].score == 7.0
    assert not any(d.startswith("Bhakoot_") for d in result.doshas)


# ── AC-5: interpretation band -- Marginal ───────────────────────────────────

def test_ac5_synthetic_pair_lands_in_marginal_band():
    # See module docstring for the hand-verified per-koota breakdown
    # (16.5 total, comfortably inside [12.0, 17.5]).
    boy = KootaNatalInfo(moon_sign=3, moon_longitude=100.0, nakshatra=0)
    girl = KootaNatalInfo(moon_sign=8, moon_longitude=250.0, nakshatra=6)
    result = compute_ashtakoot_compatibility(boy, girl)

    assert result.total_score == 16.0
    assert 12.0 <= result.total_score <= 17.5
    assert result.interpretation == "Marginal — consult astrologer"


# ── Structural invariants ───────────────────────────────────────────────────

def test_inv1_ashtakoot_result_is_frozen():
    result = compute_ashtakoot_compatibility(_sulabh(), _surbhi())
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.total_score = 0.0


def test_inv2_kootas_dict_has_exactly_eight_keys_matching_score_weights():
    result = compute_ashtakoot_compatibility(_sulabh(), _surbhi())
    assert set(result.kootas.keys()) == set(ak.KOOTA_SCORE_WEIGHTS.keys())
    assert len(result.kootas) == 8


@pytest.mark.parametrize(
    "boy,girl",
    [
        (_sulabh(), _surbhi()),
        (KootaNatalInfo(0, 15.0, 2), KootaNatalInfo(7, 225.0, 17)),
        (KootaNatalInfo(3, 100.0, 0), KootaNatalInfo(8, 250.0, 6)),
    ],
)
def test_inv3_total_score_equals_sum_of_koota_scores(boy, girl):
    result = compute_ashtakoot_compatibility(boy, girl)
    assert result.total_score == sum(r.score for r in result.kootas.values())


@pytest.mark.parametrize(
    "boy,girl",
    [
        (_sulabh(), _surbhi()),
        (KootaNatalInfo(0, 15.0, 2), KootaNatalInfo(7, 225.0, 17)),
        (KootaNatalInfo(3, 100.0, 0), KootaNatalInfo(8, 250.0, 6)),
    ],
)
def test_inv4_max_score_is_always_36(boy, girl):
    result = compute_ashtakoot_compatibility(boy, girl)
    assert result.max_score == 36


def test_inv5_warnings_contains_nadi_dosha_warning_in_deterministic_order():
    boy = _natal_info("INV5-Boy", "1995-02-13", "12:00", "Delhi, India")
    girl = _natal_info("INV5-Girl", "1995-03-13", "12:00", "Delhi, India")
    result = compute_ashtakoot_compatibility(boy, girl)

    nadi_warning = result.kootas["Nadi"].warnings[0]
    assert nadi_warning in result.warnings

    # Deterministic order: rebuild the expected union in the locked
    # Varna->Vashya->Tara->Yoni->GrahaMaitri->Gana->Bhakoot->Nadi order
    # and assert it's an exact match, not just a containment check.
    expected = tuple(
        w
        for koota_name in (
            "Varna", "Vashya", "Tara", "Yoni",
            "GrahaMaitri", "Gana", "Bhakoot", "Nadi",
        )
        for w in result.kootas[koota_name].warnings
    )
    assert result.warnings == expected


def test_inv5_no_warnings_when_no_dosha_active():
    result = compute_ashtakoot_compatibility(_sulabh(), _surbhi())
    assert result.warnings == ()
