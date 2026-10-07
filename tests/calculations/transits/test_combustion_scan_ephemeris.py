"""Real-ephemeris ratification for combustion_scan (S147), Layer B.

The sibling test tests/astro/test_combustion_scan.py proves the SCANNER LOGIC
against a synthetic ephemeris. THIS test proves the scan agrees with the real
sky, by pinning each combust interval to an independently-sourced solar
conjunction (Sun-planet separation is frame-independent, so a tropical ephemeris
date confirms a Lahiri-sidereal run):

  * Venus inferior conjunction  2026-10-24 04:39 UTC  (derekscope / obliquity)
  * Mercury inferior conjunction 2026-11-04 14:20 UTC (derekscope)
  * Mercury superior conjunction ~2026-12-30 (geometrically pinned: greatest
    elongation W 20 Nov 19.6deg sits in the scan's gap; interval exits 23 Jan,
    which rules out a Jan conjunction -> ~30 Dec)

RATIFICATION DESIGN (why not exact boundaries): the scan's interval EDGES move by
hours between ephemeris backends (Moshier vs bundled Swiss Ephemeris), so exact
start/end asserts would be brittle false-failures. Instead each episode is
asserted by CONJUNCTION-CONTAINMENT (the conjunction is 0deg separation, deep
inside any orb, so containment is backend-stable), the retrograde flag, and a
DURATION BAND wide enough to absorb sub-degree backend differences (observed
durations 10.06 / 11.41 / 47.75 days). Scope guard: the window is pinned to
2026-10-04 + 120d; these constants are specific to that window and nothing else.

House style: swisseph is a hard project dependency (chart_calculator makes 28
swe calls), so -- like every sibling in tests/calculations/ -- this imports it
directly with no skip guard.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import swisseph as swe

from agent.calculations.transits.combustion_scan import (
    scan_combustion_windows, TARAGRAHA_SWE_IDS,
)

# Sample window ratified in design chat (S147): 2026-10-04 00:00 UT + 120 days.
_START_JD = swe.julday(2026, 10, 4, 0.0)
_END_JD = _START_JD + 120.0

# Independently-sourced conjunction moments (UTC), as Julian Days. Containment of
# these is the backend-stable anchor; the hours are exact for the two inferior
# conjunctions and a safe mid-window point for the superior one (true conj ~30 Dec,
# comfortably inside the Dec 06 -> Jan 23 interval wherever in Dec 21-30 it lands).
_VENUS_INFERIOR_JD = swe.julday(2026, 10, 24, 4 + 39 / 60)
_MERCURY_INFERIOR_JD = swe.julday(2026, 11, 4, 14 + 20 / 60)
_MERCURY_SUPERIOR_PROBE_JD = swe.julday(2026, 12, 25, 12.0)


def _intervals():
    swe.set_sid_mode(swe.SIDM_LAHIRI)  # parity with the pipeline; combustion is
    # frame-independent, so this does not change the result -- it guards against a
    # prior test leaving a different ayanamsa mode set on the shared swe module.
    return scan_combustion_windows(_START_JD, _END_JD)["intervals"]


def _containing(intervals, planet, jd):
    """The interval for `planet` whose [start, end) spans `jd`, or None."""
    hits = [iv for iv in intervals
            if iv["planet"] == planet and iv["start_jd"] <= jd < iv["end_jd"]]
    assert len(hits) <= 1, f"overlapping intervals for {planet} at jd={jd}"
    return hits[0] if hits else None


def test_venus_inferior_conjunction_window_is_detected():
    iv = _containing(_intervals(), "venus", _VENUS_INFERIOR_JD)
    assert iv is not None, "no Venus combust interval spans its 24 Oct 2026 inferior conjunction"
    assert iv["retrograde_at_mid"] is True, "Venus is retrograde at inferior conjunction"
    duration = iv["end_jd"] - iv["start_jd"]
    assert 8.0 <= duration <= 13.0, f"Venus combust duration {duration:.2f}d outside 8-13d band"


def test_mercury_inferior_conjunction_window_is_detected():
    iv = _containing(_intervals(), "mercury", _MERCURY_INFERIOR_JD)
    assert iv is not None, "no Mercury combust interval spans its 4 Nov 2026 inferior conjunction"
    assert iv["retrograde_at_mid"] is True, "Mercury is retrograde at inferior conjunction"
    duration = iv["end_jd"] - iv["start_jd"]
    assert 9.0 <= duration <= 14.0, f"Mercury inferior combust duration {duration:.2f}d outside 9-14d band"


def test_mercury_superior_conjunction_window_is_long_and_direct():
    iv = _containing(_intervals(), "mercury", _MERCURY_SUPERIOR_PROBE_JD)
    assert iv is not None, "no Mercury combust interval spans its ~30 Dec 2026 superior conjunction"
    assert iv["retrograde_at_mid"] is False, "Mercury is direct at superior conjunction"
    duration = iv["end_jd"] - iv["start_jd"]
    # superior-conjunction combustion is long (Mercury loiters near aphelion 24 Dec)
    assert 40.0 <= duration <= 54.0, f"Mercury superior combust duration {duration:.2f}d outside 40-54d band"


def test_no_slow_graha_is_combust_in_this_window():
    """Mars, Jupiter, Saturn have no solar conjunction in this 120-day sample, so
    the scan must report none -- a guard against a runaway orb or a merged band."""
    ivs = _intervals()
    for slow in ("mars", "jupiter", "saturn"):
        assert not any(iv["planet"] == slow for iv in ivs), \
            f"{slow} reported combust in a window containing no {slow}-Sun conjunction"


def test_only_the_five_taragrahas_are_scanned():
    assert set(TARAGRAHA_SWE_IDS) == {"mars", "mercury", "jupiter", "venus", "saturn"}
    scanned = scan_combustion_windows(_START_JD, _START_JD + 1.0)["scanned"]["planets"]
    assert set(scanned) == {"mars", "mercury", "jupiter", "venus", "saturn"}
