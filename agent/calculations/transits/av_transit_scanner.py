"""Ashtakavarga transit scanner -- ephemeris-driven segment scan on top of
av_transit_scorer.py's pure per-instant scorer.

Purpose: scan_av_transit_segments() walks a date window and returns
ordered AvTransitSegment records, each covering one contiguous span where
(sign, kakshya_index) held steady, scored once via
agent.calculations.transits.av_transit_scorer.score_av_transit(). This is
the ephemeris layer score_av_transit() itself deliberately does not have
(that module takes precomputed transit position -- see its own
docstring); this module is where the swe/helpers/ephemeris.py calls
actually happen.

NOT a convergence layer: this scanner has NO knowledge of dashas. Per
score_av_transit()'s own USAGE CONSTRAINT (PVR ch. 25.5.2 verbatim -- "can
only be used to fine-tune a prediction to a few days", never in a
vacuum), nesting these segments inside a dasha envelope is a future
convergence layer's job. This module only answers "what did Ashtakavarga
say about this planet, day by day, over this window" -- nothing here
reads or reasons about dasha boundaries.

PLANET SCOPE: identical to score_av_transit()'s (Saturn/Jupiter get
kakshya_index; Sun/Mars are sign-level only, kakshya_index always None;
Moon/Mercury/Venus raise ValueError). Delegates the planet-identity/
exclusion check to score_av_transit() itself (see
_validate_transit_planet) rather than duplicating either the planet lists
or the ValueError wording -- same reuse pattern as ashtakavarga.py's
compute_bav_contributors delegating to compute_bav. Separately imports
score_av_transit()'s _KAKSHYA_PLANETS (which planets get a kakshya_index
at all) and _KAKSHYA_WIDTH_DEG (the 3.75-degree division width) so this
module's own daily state-detection loop can never drift from
score_av_transit()'s CITATION (e) convention.

MECHANICS:
  - Sidereal longitudes come ONLY from helpers/ephemeris.py's
    sidereal_longitude() (CLAUDE.md ephemeris-consolidation lock) -- no
    raw swe.calc_ut() call in this module.
  - State function per day: (sign, kakshya_index) for Saturn/Jupiter,
    (sign, None) for Sun/Mars. kakshya_index = floor(degrees_in_sign /
    3.75), half-open [start, end) -- same convention as
    score_av_transit()'s CITATION (e); reuses that module's
    _KAKSHYA_WIDTH_DEG constant so the two can never drift apart.
  - Segmentation: daily-step scan, adapted from sade_sati.py's
    _find_segments pattern (see _daily_state_segments below) but WITHOUT
    that function's sub-day bisection refinement -- boundary refinement
    to the day is sufficient here. Rationale: the fastest kakshya dwell
    this module ever scores is Jupiter's (~45 days per kakshya; Saturn's
    is ~112 days), and this scanner's whole purpose is to nest inside a
    dasha envelope on the order of a mahadasha (V1 cap: 40y, realistic
    use: up to ~20y) -- a 1-day edge error on a 45-112 day dwell is noise
    against that envelope, not a precision loss worth a bisection pass.
  - Retrograde re-entries are NOT merged or deduplicated: a planet that
    transits a sign/kakshya, retrogrades out, and later re-enters produces
    SEPARATE AvTransitSegment records for each pass, even though the
    (sign, kakshya_index) state repeats. This is correct and required --
    each pass is a distinct transit event with its own start/end and (via
    the midpoint re-sample) potentially its own score. Saturn is the
    starkest case: sade_sati.py already documents Saturn's
    Pisces-Aries-Pisces retrograde oscillation at Sade Sati phase
    boundaries as mainline behavior, not an edge case -- this scanner
    inherits that same triple-pass-style shape at the kakshya level for
    Saturn/Jupiter. The daily contiguous-run grouping below only merges
    ADJACENT days sharing a state; a gap of even one day with a different
    state starts a brand-new segment.
  - Each segment's score comes from exactly one score_av_transit() call,
    sampled at the segment's midpoint JD -- this module never reimplements
    bav_band/sav_band/verdict/intensity logic; only the (sign,
    kakshya_index) state-detection loop and its own 3.75-degree floor
    division live here.

VALIDATION:
  - end_jd must be > start_jd.
  - Window is capped at 40 years (scope guard: V1 dasha envelopes never
    exceed a single mahadasha, ~20y at most, so 40y leaves a 2x margin;
    tuning note: raise this cap only if a future phase needs multi-dasha
    scans in one call -- until then a wider window is very likely a
    caller bug, not a real use case, and this fails closed rather than
    silently running an expensive multi-decade daily scan).
"""

from __future__ import annotations

from dataclasses import dataclass

from agent.calculations.helpers import ephemeris
from agent.calculations.transits.av_transit_scorer import (
    AvTransitScore,
    _KAKSHYA_PLANETS,
    _KAKSHYA_WIDTH_DEG,
    score_av_transit,
)
from agent.chart_calculator import SIGNS

import swisseph as swe

_MAX_WINDOW_YEARS = 40
_YEAR_DAYS = 365.25  # matches sade_sati.py's convention

_PLANET_SWE_ID: dict[str, int] = {
    "Sun": swe.SUN,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
}


@dataclass(frozen=True)
class AvTransitSegment:
    start_jd: float
    end_jd: float
    sign: str
    kakshya_index: int | None   # Saturn/Jupiter only; None for Sun/Mars
    score: AvTransitScore


def _validate_transit_planet(
    transit_planet: str,
    natal_bav: dict[str, dict[str, int]],
    natal_sav: dict[str, int],
    natal_contributors: dict[str, dict[str, frozenset[str]]],
) -> None:
    """Delegates the planet-identity/exclusion check to score_av_transit()
    itself (same reuse pattern as ashtakavarga.py's compute_bav_contributors
    delegating to compute_bav) instead of duplicating its planet lists or
    ValueError wording. "Aries"/0.0 are placeholders -- any in-range
    sign/degree behaves identically for a planet that passes; only the
    exception path (raised or not) matters here. Also incidentally shallow-
    validates that natal_bav/natal_sav/natal_contributors each cover
    "Aries", which they always will if built via
    compute_bav/compute_sav/compute_bav_contributors.
    """
    score_av_transit(transit_planet, "Aries", 0.0, natal_bav, natal_sav, natal_contributors)


def _state_at(jd_ut: float, planet_id: int, has_kakshya: bool) -> tuple[str, int | None]:
    """(sign, kakshya_index) at jd_ut -- kakshya_index is None when
    has_kakshya is False (Sun/Mars). See module CITATION on the 3.75-degree
    half-open convention (shared with score_av_transit()'s CITATION (e)).
    """
    lon = ephemeris.sidereal_longitude(jd_ut, planet_id)
    sign = SIGNS[int(lon / 30.0) % 12]
    if not has_kakshya:
        return (sign, None)
    degrees_in_sign = lon % 30.0
    kakshya_index = min(int(degrees_in_sign // _KAKSHYA_WIDTH_DEG), 7)
    return (sign, kakshya_index)


def _daily_state_segments(
    start_jd: float, end_jd: float, state_fn
) -> list[tuple[float, float, tuple[str, int | None]]]:
    """Daily-resolution scan over [start_jd, end_jd]; groups contiguous
    same-state days into (seg_start_jd, seg_end_jd, state) segments,
    ordered by time. Adapted from sade_sati.py's _find_segments pattern,
    but deliberately without its sub-day bisection refinement -- see
    module docstring's rationale (kakshya dwell floors of ~45-112 days
    make a 1-day edge error negligible against this scanner's intended
    dasha-envelope nesting). seg_end_jd of one segment equals seg_start_jd
    of the next (contiguous tiling, no gaps/overlaps); the final segment's
    seg_end_jd is the window's own end_jd rather than a following day that
    doesn't exist in-window. A run that repeats a state seen earlier in
    the window (retrograde re-entry) is NOT merged with that earlier run
    -- only ADJACENT identical-state days are grouped (see module
    docstring's retrograde note).
    """
    n_days = int(end_jd - start_jd) + 1
    days = [start_jd + i for i in range(n_days)]
    states = [state_fn(d) for d in days]

    segments: list[tuple[float, float, tuple[str, int | None]]] = []
    i = 0
    n = len(days)
    while i < n:
        run_start = i
        current = states[i]
        while i < n and states[i] == current:
            i += 1
        run_end = i - 1
        seg_start = days[run_start]
        seg_end = days[run_end + 1] if run_end + 1 < n else end_jd
        segments.append((seg_start, seg_end, current))
    return segments


def scan_av_transit_segments(
    transit_planet: str,
    natal_bav: dict[str, dict[str, int]],
    natal_sav: dict[str, int],
    natal_contributors: dict[str, dict[str, frozenset[str]]],
    start_jd: float,
    end_jd: float,
) -> list[AvTransitSegment]:
    """Scan [start_jd, end_jd] and return ordered AvTransitSegment records
    for transit_planet's Ashtakavarga transit. See module docstring for
    PLANET SCOPE, MECHANICS, and VALIDATION.

    Args:
        transit_planet: one of "Sun","Mars","Jupiter","Saturn". Moon/
            Mercury/Venus raise ValueError (see score_av_transit()'s
            PLANET SCOPE) -- fail closed, delegated via
            _validate_transit_planet.
        natal_bav, natal_sav, natal_contributors: same contract as
            score_av_transit()'s -- passed through unchanged to each
            per-segment scoring call.
        start_jd, end_jd: Julian Day (UT) window bounds. end_jd must be >
            start_jd; window capped at 40 years (see VALIDATION).

    Returns:
        Ordered list of AvTransitSegment, contiguously tiling
        [start_jd, end_jd] with no gaps or overlaps. Retrograde re-entries
        produce separate segments with repeated (sign, kakshya_index)
        states -- not merged (see module docstring).

    Raises:
        ValueError: transit_planet unknown or excluded (Moon/Mercury/
            Venus); end_jd <= start_jd; window exceeds 40 years; or a
            natal_bav/natal_sav/natal_contributors key is missing
            (delegated to score_av_transit()'s own validation).
        EphemerisError: a pyswisseph calculation failed for
            transit_planet at some jd_ut in the scan window.
    """
    _validate_transit_planet(transit_planet, natal_bav, natal_sav, natal_contributors)

    if not (end_jd > start_jd):
        raise ValueError(f"end_jd ({end_jd}) must be > start_jd ({start_jd})")
    window_years = (end_jd - start_jd) / _YEAR_DAYS
    if window_years > _MAX_WINDOW_YEARS:
        raise ValueError(
            f"scan window spans {window_years:.1f} years, exceeding the "
            f"{_MAX_WINDOW_YEARS}-year cap (scope guard: V1 dasha "
            f"envelopes never exceed a single ~20y mahadasha; a wider "
            f"window is very likely a caller bug, not a real use case)"
        )

    planet_id = _PLANET_SWE_ID[transit_planet]
    has_kakshya = transit_planet in _KAKSHYA_PLANETS

    raw_segments = _daily_state_segments(
        start_jd, end_jd, lambda jd: _state_at(jd, planet_id, has_kakshya)
    )

    segments: list[AvTransitSegment] = []
    for seg_start, seg_end, _state in raw_segments:
        mid_jd = (seg_start + seg_end) / 2.0
        lon = ephemeris.sidereal_longitude(mid_jd, planet_id)
        sign = SIGNS[int(lon / 30.0) % 12]
        degrees_in_sign = lon % 30.0
        score = score_av_transit(
            transit_planet, sign, degrees_in_sign, natal_bav, natal_sav, natal_contributors
        )
        segments.append(
            AvTransitSegment(
                start_jd=seg_start,
                end_jd=seg_end,
                sign=sign,
                kakshya_index=score.kakshya_index,
                score=score,
            )
        )
    return segments
