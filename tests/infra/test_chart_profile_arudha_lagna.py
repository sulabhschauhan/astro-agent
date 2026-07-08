"""Tests for agent/infra/chart_profile.py -- build_arudha_lagna_profile()
(P6->P7 Arudha Lagna domain builder, standalone, not yet wired into
build_domain_profile()/_VALID_DOMAINS/the router).

DEVIATIONS FROM THE ORIGINAL TASK PROMPT (each verified against actual
runtime behavior before being written in, per CLAUDE.md's REVIEW-before-
PROCEED working style -- not silently accepted from the prompt as given):

1. tests/infra/test_chart_profile.py (the file the prompt said to read for
   existing career_strength/current_dasha test conventions) does not exist
   anywhere in this repo. The closest real analog is
   tests/infra/test_orchestrator_e2e.py -- its module-scoped
   calculate_chart() fixture-per-reference-chart style and "standalone test
   function per chart" convention (that file's own Session-20 comment) are
   mirrored here instead.
2. Layer B ("synthetic chart_data dict with Saturn+Rahu placed inside
   Aquarius") does not work against the real implementation:
   build_arudha_lagna_profile() recomputes all 9 planet longitudes ITSELF,
   live, from chart_data['meta']['jd_ut'] via helpers/ephemeris.py -- it
   never reads planet positions out of chart_data, so values "placed" in a
   synthetic dict have no effect. The prompt's own "documented 2022-23
   Saturn+Rahu-in-Aquarius" framing (a direct quote of strength.py's D2
   docstring) also does not hold up empirically: checked directly via
   swisseph, Saturn was in sidereal Aquarius through 2022-23 but Rahu
   (Mean Node) was in Aries/Pisces that whole window; a 1900-2030 scan at
   10-day resolution found no real Saturn+Rahu-both-in-Aquarius overlap at
   all. Resolved via design-chat decision (this session): monkeypatch the
   shared swisseph.calc_ut (the same test seam helpers/ephemeris.py's own
   CONSTRAINT section documents -- every importer's `swe` name late-binds
   to the same module object) to force Saturn/Rahu into Aquarius for this
   one test, real ephemeris for every other planet.

FIXTURE PROVENANCE:
  Layer A: Sulabh AL=Leo is RATIFIED (design chat, this session) against
    PVR Ch.9 counting by hand (Sagittarius->Aries=5, 5 signs from Aries=
    Leo, no step-5 1st/7th exception). Surbhi/Sheridan/David are
    MEASURE-FIRST -- their arudha_sign is printed for ratification, not
    asserted, per this task's own instruction.
  Layer B: no real chart -- monkeypatched swe.calc_ut (see DEVIATIONS #2).
  Layer C: real Sulabh chart_data, mutated per-case (missing/invalid keys).
  Layer D: real Sulabh chart_data, result-shape lock only.
"""

import pytest
import swisseph as swe

from agent.infra.chart_profile import build_arudha_lagna_profile

_CANONICAL_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

# Classical (single) sign lords -- Scorpio/Aquarius deliberately excluded
# (co-lorded, routed through stronger_co_lord; see arudha.py's own
# _CLASSICAL_SIGN_LORDS). Independently duplicated here rather than
# imported, per this project's per-module duplication convention (see
# chart_profile.py's own _AV_TRANSIT_NATAL_PLANETS comment for the
# precedent).
_CLASSICAL_SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn",
    "Pisces": "Jupiter",
}


# ─── Fixtures (mirrors test_orchestrator_e2e.py's own style) ───────────────


@pytest.fixture(scope="module")
def sulabh_chart():
    from agent.chart_calculator import calculate_chart
    return calculate_chart("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")


@pytest.fixture(scope="module")
def surbhi_chart():
    from agent.chart_calculator import calculate_chart
    return calculate_chart("Surbhi", "11 Sep 1992", "10:30", "Patna, India")


@pytest.fixture(scope="module")
def sheridan_chart():
    from agent.chart_calculator import calculate_chart
    return calculate_chart("Sheridan", "27 May 1984", "08:00", "Durban, South Africa")


@pytest.fixture(scope="module")
def david_chart():
    from agent.chart_calculator import calculate_chart
    return calculate_chart("David", "19 Jan 1976", "22:00", "London, UK")


# ─── Layer A: real-chart oracle ─────────────────────────────────────────────


class TestRealChartOracle:
    def test_sulabh_al_is_leo_ratified(self, sulabh_chart):
        result = build_arudha_lagna_profile(sulabh_chart)
        assert result["lagna_sign"] == "Sagittarius"
        assert result["arudha_sign"] == "Leo"
        assert result["lord"] == "Jupiter"
        assert result["co_lord_deciding_step"] is None
        assert result["tier"] == "TIER_1_EXACT"
        assert result["sources"] == ("padas.py",)


def _print_and_check_measure_first_shape(chart_name: str, result: dict) -> None:
    print(
        f"RATIFY BEFORE COMMIT -- {chart_name}: "
        f"lagna_sign={result['lagna_sign']!r} arudha_sign={result['arudha_sign']!r} "
        f"lord={result['lord']!r} co_lord_deciding_step={result['co_lord_deciding_step']!r}"
    )
    assert result["lagna_sign"] in _CANONICAL_SIGNS
    if result["lagna_sign"] in ("Scorpio", "Aquarius"):
        assert result["co_lord_deciding_step"] is not None
    else:
        assert result["lord"] == _CLASSICAL_SIGN_LORDS[result["lagna_sign"]]
        assert result["co_lord_deciding_step"] is None
    assert result["tier"] == "TIER_1_EXACT"
    assert result["sources"] == ("padas.py",)


class TestMeasureFirstShapeOnly:
    # arudha_sign is NOT asserted for these 3 -- printed for ratification
    # only, per this task's own instruction.
    def test_surbhi(self, surbhi_chart):
        result = build_arudha_lagna_profile(surbhi_chart)
        _print_and_check_measure_first_shape("Surbhi", result)

    def test_sheridan(self, sheridan_chart):
        result = build_arudha_lagna_profile(sheridan_chart)
        _print_and_check_measure_first_shape("Sheridan", result)

    def test_david(self, david_chart):
        result = build_arudha_lagna_profile(david_chart)
        _print_and_check_measure_first_shape("David", result)


# ─── Layer B: co-lord fail-closed propagation ───────────────────────────────


class TestCoLordFailClosedPropagation:
    def test_d2_both_resident_propagates_unmodified(self, monkeypatch):
        # See module DEVIATIONS #2: build_arudha_lagna_profile() computes
        # every planet longitude live from chart_data['meta']['jd_ut'], so
        # only a monkeypatched swe.calc_ut can force Saturn+Rahu into the
        # same contested sign. Real ephemeris used for every other planet
        # (delegates to the captured real_calc_ut).
        real_calc_ut = swe.calc_ut

        def fake_calc_ut(jd_ut, planet, flags):
            if planet == swe.SATURN:
                return ([305.0, 0.0, 0.0, 0.0, 0.0, 0.0], 0)  # 5 Aquarius
            if planet == swe.MEAN_NODE:
                return ([315.0, 0.0, 0.0, 0.0, 0.0, 0.0], 0)  # 15 Aquarius
            return real_calc_ut(jd_ut, planet, flags)

        monkeypatch.setattr(swe, "calc_ut", fake_calc_ut)

        chart_data = {
            "meta": {"jd_ut": swe.julday(2000, 1, 1, 0.0)},
            "lagna_chart": {"ascendant": "Aquarius"},
        }
        with pytest.raises(ValueError, match="D2|both"):
            build_arudha_lagna_profile(chart_data)


# ─── Layer C: input contract ─────────────────────────────────────────────


class TestInputContract:
    def test_missing_lagna_chart_key_raises(self, sulabh_chart):
        bad = dict(sulabh_chart)
        del bad["lagna_chart"]
        with pytest.raises(KeyError, match="lagna_chart"):
            build_arudha_lagna_profile(bad)

    def test_missing_ascendant_key_raises(self, sulabh_chart):
        bad = dict(sulabh_chart)
        bad["lagna_chart"] = dict(sulabh_chart["lagna_chart"])
        del bad["lagna_chart"]["ascendant"]
        with pytest.raises(KeyError, match="ascendant"):
            build_arudha_lagna_profile(bad)

    def test_invalid_ascendant_sign_raises_from_padas(self, sulabh_chart):
        bad = dict(sulabh_chart)
        bad["lagna_chart"] = dict(sulabh_chart["lagna_chart"])
        bad["lagna_chart"]["ascendant"] = "Xyz"
        with pytest.raises(ValueError, match="Xyz"):
            build_arudha_lagna_profile(bad)


# ─── Layer D: result-shape lock ─────────────────────────────────────────


class TestResultShape:
    def test_exact_keys_and_types(self, sulabh_chart):
        result = build_arudha_lagna_profile(sulabh_chart)
        assert set(result.keys()) == {
            "arudha_sign", "lagna_sign", "lord", "co_lord_deciding_step",
            "tier", "sources",
        }
        assert isinstance(result["arudha_sign"], str)
        assert isinstance(result["lagna_sign"], str)
        assert isinstance(result["lord"], str)
        assert result["co_lord_deciding_step"] is None or isinstance(
            result["co_lord_deciding_step"], str
        )
        assert isinstance(result["tier"], str)
        assert isinstance(result["sources"], tuple)
        assert all(isinstance(s, str) for s in result["sources"])
