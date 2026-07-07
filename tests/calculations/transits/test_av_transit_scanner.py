"""Tests for agent/calculations/transits/av_transit_scanner.py --
scan_av_transit_segments() / AvTransitSegment.

Natal tables are Sulabh's, sourced via the same live-pipeline path as
test_av_transit_scorer.py (calculate_chart() ->
compute_bav/compute_sav/compute_bav_contributors) -- transit-planet SIGN
is natal-independent (it's purely the transiting planet's own ephemeris
position), so any natal chart would do for Layers 1-2's structural/anchor
checks; Sulabh's is reused here only for consistency with the sibling
scorer test file, not because the anchors depend on it in any way.
Julian Days come from `swisseph.julday()` -- the same repo-wide convention
already used throughout tests/calculations/transits/test_sade_sati.py.

Layer 1 (Saturn, 1 Jan 2020 -> 1 Jul 2023) -- structural invariants that
must hold regardless of which oracle dates are "correct":
  (a) contiguous tiling: seg[i].end_jd == seg[i+1].start_jd; first
      segment's start == window start; last segment's end == window end.
  (b) adjacency legality of every state change: within one sign,
      kakshya_index changes by exactly +/-1 (forward or retrograde);
      a sign change only happens exactly at the 7->0 (direct motion) or
      0->7 (retrograde) kakshya edge, and only between zodiacally
      adjacent signs (SIGNS order, wrapping Pisces->Aries).
  (c) every segment's score is internally consistent with the segment
      itself: score.kakshya_index == segment.kakshya_index and
      score.transit_sign == segment.sign.
  (d) retrograde evidence, hard-asserted (not informational): at least
      one (sign, kakshya_index) state must occur in 3 or more
      NON-CONSECUTIVE segments -- Saturn's real triple-pass shape through
      a kakshya during 2020-2023 (mirrors sade_sati.py's own documented
      Pisces-Aries-Pisces retrograde-split precedent, one level finer).

Layer 2 (external ingress anchors) -- the four Capricorn/Aquarius
maximal sign runs in the Layer 1 window (Saturn's leading partial
Sagittarius sliver at the very start of the window, 1-24 Jan 2020, is a
window-edge artifact, not a real ingress-bounded run, so it is excluded
from the "four maximal sign-run" count) must each begin within +/-2 days
of a real published sidereal-Saturn ingress date. PROVENANCE (design
review 2026-07-06): Saturn's Lahiri-sidereal ingress into Capricorn on
24 Jan 2020, into Aquarius on 29 Apr 2022, retrograde back into Capricorn
on 12 Jul 2022, and back into Aquarius on 17 Jan 2023 are independently
corroborated by (i) mainstream Vedic-astrology transit-date sources
(e.g. drikpanchang.com's Saturn Transit pages) and (ii) this repo's own
tests/calculations/transits/test_sade_sati.py, whose
expected_macro_start = swe.julday(2020, 1, 24, 0.0) independently pins
the SAME Sagittarius->Capricorn ingress via a completely different code
path (the rising/setting-sign macro-envelope scan, not this scanner).
TOLERANCE (+/-2 days, not inflation): the documented ~57.77-arcsecond
pyswisseph-vs-JHora Lahiri ayanamsa cross-implementation gap (CLAUDE.md
Known Source Divergences) works out to roughly half a day of apparent
ingress-date drift at Saturn's transit rate, plus this scanner's own
1-day scan step (module docstring: "boundary refinement to the day is
sufficient") -- combined, +/-2 days is the natural precision floor, not
a loosened target chosen to make the assertion pass.

Layer 3 -- secondary planets, structural only (no anchor pins):
  (e) Jupiter, 1 Jan 2023 -> 1 Jul 2023: invariants (a)-(c).
  (f) Sun, 1 Feb 2021 -> 1 May 2021: sign-level only -- kakshya_index is
      None on both the segment and its score for every segment; ~3 sign
      runs (Sun's ~30-day/sign cadence over a 3-month window, +/- edge
      effects from the window not aligning to an ingress).
  (g) error path: Moon raises ValueError (fail-closed exclusion,
      delegated to score_av_transit()'s own check).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import pytest
import swisseph as swe

from agent.calculations.ashtakavarga.ashtakavarga import (
    compute_bav,
    compute_bav_contributors,
    compute_sav,
)
from agent.calculations.transits.av_transit_scanner import (
    AvTransitSegment,
    scan_av_transit_segments,
)
from agent.chart_calculator import SIGNS, calculate_chart

_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

# Same literals as test_av_transit_scorer.py's _SULABH_BIRTH_ARGS (which in
# turn matches test_ashtakavarga_cross_charts.py's _BIRTH_ARGS["sulabh"]),
# independently duplicated here per this project's per-module duplication
# convention.
_SULABH_BIRTH_ARGS: tuple[str, str, str, str] = (
    "Sulabh", "6 Apr 1988", "00:30", "Calcutta, India",
)


@pytest.fixture(scope="module")
def sulabh_natal_tables():
    """Sulabh's natal_bav/natal_sav/natal_contributors via the live
    pipeline (network-free: tests/conftest.py's session-scoped geocoder
    patch is already active by the time this module-scoped fixture runs).
    Transit-planet sign detection itself never reads these -- they only
    feed each segment's score_av_transit() call.
    """
    chart = calculate_chart(*_SULABH_BIRTH_ARGS)
    placements = {"Lagna": chart["lagna_chart"]["ascendant"]}
    pp = chart["planetary_positions"]
    for planet in _PLANETS:
        placements[planet] = pp[planet]["sign"]
    bav = compute_bav(placements)
    sav = compute_sav(bav)
    contributors = compute_bav_contributors(placements)
    return bav, sav, contributors


@pytest.fixture(scope="module")
def saturn_segments(sulabh_natal_tables) -> list[AvTransitSegment]:
    bav, sav, contributors = sulabh_natal_tables
    start_jd = swe.julday(2020, 1, 1)
    end_jd = swe.julday(2023, 7, 1)
    return scan_av_transit_segments("Saturn", bav, sav, contributors, start_jd, end_jd)


@pytest.fixture(scope="module")
def jupiter_segments(sulabh_natal_tables) -> list[AvTransitSegment]:
    bav, sav, contributors = sulabh_natal_tables
    start_jd = swe.julday(2023, 1, 1)
    end_jd = swe.julday(2023, 7, 1)
    return scan_av_transit_segments("Jupiter", bav, sav, contributors, start_jd, end_jd)


@pytest.fixture(scope="module")
def sun_segments(sulabh_natal_tables) -> list[AvTransitSegment]:
    bav, sav, contributors = sulabh_natal_tables
    start_jd = swe.julday(2021, 2, 1)
    end_jd = swe.julday(2021, 5, 1)
    return scan_av_transit_segments("Sun", bav, sav, contributors, start_jd, end_jd)


# ── Shared structural-invariant checks (reused across Layers 1 and 3) ──────

def _assert_contiguous_tiling(segments: list[AvTransitSegment], start_jd: float, end_jd: float, label: str):
    assert segments[0].start_jd == start_jd, (
        f"{label}: first segment start {segments[0].start_jd} != window start {start_jd}"
    )
    assert segments[-1].end_jd == end_jd, (
        f"{label}: last segment end {segments[-1].end_jd} != window end {end_jd}"
    )
    for i in range(len(segments) - 1):
        a, b = segments[i], segments[i + 1]
        assert a.end_jd == b.start_jd, (
            f"{label}: gap/overlap between segment {i} (end={a.end_jd}) and "
            f"segment {i + 1} (start={b.start_jd})"
        )


def _assert_adjacency_legal(segments: list[AvTransitSegment], label: str):
    """Every consecutive state change must be one of:
    - same sign, kakshya_index +/-1 (direct or retrograde motion within a sign);
    - sign advances to the zodiacally next sign, iff kakshya_index goes 7->0;
    - sign retreats to the zodiacally previous sign, iff kakshya_index goes 0->7.
    Only meaningful for kakshya-tracked planets (Saturn/Jupiter); a
    kakshya_index of None (Sun/Mars) skips the kakshya-specific checks and
    only requires sign adjacency.
    """
    for i in range(len(segments) - 1):
        a, b = segments[i], segments[i + 1]
        if a.sign == b.sign:
            if a.kakshya_index is not None and b.kakshya_index is not None:
                assert abs(a.kakshya_index - b.kakshya_index) == 1, (
                    f"{label}: segment {i}->{i + 1} same sign {a.sign!r} but "
                    f"kakshya_index jumped {a.kakshya_index} -> {b.kakshya_index} "
                    f"(must change by exactly +/-1)"
                )
            continue

        ai, bi = SIGNS.index(a.sign), SIGNS.index(b.sign)
        forward = (bi - ai) % 12 == 1
        backward = (ai - bi) % 12 == 1
        assert forward or backward, (
            f"{label}: segment {i}->{i + 1} sign change {a.sign!r} -> "
            f"{b.sign!r} is not between zodiacally adjacent signs"
        )
        if a.kakshya_index is not None and b.kakshya_index is not None:
            if forward:
                assert a.kakshya_index == 7 and b.kakshya_index == 0, (
                    f"{label}: segment {i}->{i + 1} direct sign change "
                    f"{a.sign!r} -> {b.sign!r} must occur at kakshya 7->0, "
                    f"got {a.kakshya_index} -> {b.kakshya_index}"
                )
            else:
                assert a.kakshya_index == 0 and b.kakshya_index == 7, (
                    f"{label}: segment {i}->{i + 1} retrograde sign change "
                    f"{a.sign!r} -> {b.sign!r} must occur at kakshya 0->7, "
                    f"got {a.kakshya_index} -> {b.kakshya_index}"
                )


def _assert_score_consistency(segments: list[AvTransitSegment], label: str):
    for i, seg in enumerate(segments):
        assert seg.score.kakshya_index == seg.kakshya_index, (
            f"{label}: segment {i} kakshya_index {seg.kakshya_index} != "
            f"score.kakshya_index {seg.score.kakshya_index}"
        )
        assert seg.score.transit_sign == seg.sign, (
            f"{label}: segment {i} sign {seg.sign!r} != "
            f"score.transit_sign {seg.score.transit_sign!r}"
        )


# ── Layer 1: Saturn structural invariants ──────────────────────────────────

def test_saturn_a_contiguous_tiling(saturn_segments):
    _assert_contiguous_tiling(
        saturn_segments, swe.julday(2020, 1, 1), swe.julday(2023, 7, 1), "Saturn"
    )


def test_saturn_b_adjacency_legal(saturn_segments):
    _assert_adjacency_legal(saturn_segments, "Saturn")


def test_saturn_c_score_consistency(saturn_segments):
    _assert_score_consistency(saturn_segments, "Saturn")


def test_saturn_d_retrograde_triple_pass(saturn_segments):
    """Hard assert (not informational): at least one (sign, kakshya_index)
    state must recur across 3+ NON-CONSECUTIVE segments in this window --
    Saturn's real retrograde-oscillation shape through Capricorn during
    2020-2023 (mirrors sade_sati.py's documented triple-pass precedent one
    level finer, at the kakshya rather than sign level).
    """
    from collections import Counter

    counts = Counter((seg.sign, seg.kakshya_index) for seg in saturn_segments)
    max_state, max_count = counts.most_common(1)[0]
    assert max_count >= 3, (
        f"expected at least one (sign, kakshya_index) state to recur in "
        f"3+ non-consecutive segments (retrograde triple-pass evidence), "
        f"but the most-repeated state {max_state} only occurred "
        f"{max_count} time(s)"
    )


# ── Layer 2: external ingress anchors ──────────────────────────────────────

# PROVENANCE + TOLERANCE justification: see module docstring.
_ANCHOR_SIGN_SEQUENCE = ("Capricorn", "Aquarius", "Capricorn", "Aquarius")
_ANCHOR_DATES = (
    (2020, 1, 24),
    (2022, 4, 29),
    (2022, 7, 12),
    (2023, 1, 17),
)
_ANCHOR_TOLERANCE_DAYS = 2.0


def _collapse_sign_runs(segments: list[AvTransitSegment]) -> list[tuple[str, float, float]]:
    runs: list[tuple[str, float, float]] = []
    for seg in segments:
        if runs and runs[-1][0] == seg.sign:
            runs[-1] = (runs[-1][0], runs[-1][1], seg.end_jd)
        else:
            runs.append((seg.sign, seg.start_jd, seg.end_jd))
    return runs


def test_saturn_layer2_ingress_anchors(saturn_segments):
    all_runs = _collapse_sign_runs(saturn_segments)
    # Excludes the leading partial Sagittarius sliver (1-24 Jan 2020) --
    # a window-edge artifact bounded on the left by the scan window's own
    # start_jd, not a real ingress -- see module docstring.
    cp_aq_runs = [r for r in all_runs if r[0] in ("Capricorn", "Aquarius")]

    assert [r[0] for r in cp_aq_runs] == list(_ANCHOR_SIGN_SEQUENCE), (
        f"expected exactly 4 maximal Capricorn/Aquarius sign runs in "
        f"sequence {_ANCHOR_SIGN_SEQUENCE}, got {[r[0] for r in cp_aq_runs]}"
    )

    for (sign, run_start_jd, _run_end_jd), (year, month, day) in zip(cp_aq_runs, _ANCHOR_DATES):
        anchor_jd = swe.julday(year, month, day)
        diff_days = abs(run_start_jd - anchor_jd)
        assert diff_days <= _ANCHOR_TOLERANCE_DAYS, (
            f"{sign} run start (jd={run_start_jd}) is {diff_days:.2f} days "
            f"from the {year}-{month:02d}-{day:02d} anchor (jd={anchor_jd}), "
            f"exceeding the +/-{_ANCHOR_TOLERANCE_DAYS}-day tolerance"
        )


# ── Layer 3: secondary planets, structural only ────────────────────────────

def test_jupiter_e_structural_invariants(jupiter_segments):
    _assert_contiguous_tiling(
        jupiter_segments, swe.julday(2023, 1, 1), swe.julday(2023, 7, 1), "Jupiter"
    )
    _assert_adjacency_legal(jupiter_segments, "Jupiter")
    _assert_score_consistency(jupiter_segments, "Jupiter")


def test_sun_f_sign_level_only_no_kakshya(sun_segments):
    for i, seg in enumerate(sun_segments):
        assert seg.kakshya_index is None, (
            f"Sun segment {i}: kakshya_index should be None (sign-level "
            f"only), got {seg.kakshya_index}"
        )
        assert seg.score.kakshya_index is None, (
            f"Sun segment {i}: score.kakshya_index should be None "
            f"(sign-level only), got {seg.score.kakshya_index}"
        )


def test_sun_f_contiguous_tiling(sun_segments):
    _assert_contiguous_tiling(
        sun_segments, swe.julday(2021, 2, 1), swe.julday(2021, 5, 1), "Sun"
    )


def test_sun_f_approximately_three_sign_runs(sun_segments):
    """Sun moves ~1 sign/month; a 3-month window yields ~3 sign runs, plus
    up to one extra partial run at each edge if the window doesn't align
    exactly to an ingress -- so 3-5, not an exact 3, is the honest bound.
    """
    runs = _collapse_sign_runs(sun_segments)
    assert 3 <= len(runs) <= 5, (
        f"expected ~3 sign runs (3-5 allowing for window-edge partial "
        f"runs) for Sun over a 3-month window, got {len(runs)}: "
        f"{[r[0] for r in runs]}"
    )


# ── Layer 3(g): error path ──────────────────────────────────────────────────

def test_moon_raises_value_error(sulabh_natal_tables):
    bav, sav, contributors = sulabh_natal_tables
    start_jd = swe.julday(2021, 2, 1)
    end_jd = swe.julday(2021, 5, 1)
    with pytest.raises(ValueError, match="excluded from V1"):
        scan_av_transit_segments("Moon", bav, sav, contributors, start_jd, end_jd)


def test_end_jd_not_after_start_jd_raises_value_error(sulabh_natal_tables):
    bav, sav, contributors = sulabh_natal_tables
    jd = swe.julday(2021, 2, 1)
    with pytest.raises(ValueError, match="must be > start_jd"):
        scan_av_transit_segments("Saturn", bav, sav, contributors, jd, jd)


def test_window_exceeding_40_year_cap_raises_value_error(sulabh_natal_tables):
    bav, sav, contributors = sulabh_natal_tables
    start_jd = swe.julday(2020, 1, 1)
    end_jd = start_jd + 41 * 365.25
    with pytest.raises(ValueError, match="40-year cap"):
        scan_av_transit_segments("Saturn", bav, sav, contributors, start_jd, end_jd)
