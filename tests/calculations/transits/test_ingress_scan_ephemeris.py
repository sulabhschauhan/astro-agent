"""ingress_scan against the real ephemeris. NO SKIPS -- swisseph is a hard
dependency of this project (chart_calculator makes 28 calls), so a missing
swisseph is a broken install, not a reason to pass silently.

House style: assert COUNTS, CONTAINMENT and BANDS, not exact boundary instants.
A boundary shifts by seconds between ephemeris backends (SWIEPH files vs the
Moshier fallback); a count or a day-level containment does not. Every band below
was MEASURED first on this backend and then frozen with margin -- none was
back-fitted to make a failing assert pass.
"""
import swisseph as swe

from agent.calculations.transits import ingress_scan

YEAR_START = swe.julday(2026, 1, 1, 0.0)
YEAR_END = swe.julday(2027, 1, 1, 0.0)


def _civil(jd):
    y, m, d, _ = swe.revjul(jd)
    return (y, m, d)


def test_sun_makes_exactly_twelve_sign_ingresses_in_a_year():
    """The Sun never retrogrades, so twelve is exact, not a band. A thirteenth or
    an eleventh would mean a dropped or duplicated sankranti -- the single input
    the masa calendar is most sensitive to."""
    cs = ingress_scan.scan_divisional_ingresses("sun", YEAR_START, YEAR_END)
    assert len(cs) == 12
    assert sorted(c.to_index for c in cs) == list(range(12))
    assert all(c.to_index == (c.from_index + 1) % 12 for c in cs)
    assert all(cs[i].jd < cs[i + 1].jd for i in range(11))


def test_sun_ingress_dates_contain_known_sankrantis():
    """CONTAINMENT, day-level, against externally datable ingresses: Mesha
    sankranti (solar new year) falls on 14 April 2026 and Makara sankranti on
    14 January 2026. Day-level because the instant moves with the backend."""
    cs = ingress_scan.scan_divisional_ingresses("sun", YEAR_START, YEAR_END)
    by_rashi = {c.to_index: _civil(c.jd) for c in cs}
    assert by_rashi[0] == (2026, 4, 14)    # Mesha
    assert by_rashi[9] == (2026, 1, 14)    # Makara


def test_mercury_retrograde_recrossing_is_found():
    """THE CASE THE WHOLE L0 REDESIGN EXISTS FOR. Mercury re-crosses a sign cusp
    backwards in 2026; a scanner that only compares coarse samples reports the
    forward crossing and loses the pair. Assert a backward crossing exists and
    that the sign is re-entered afterwards."""
    cs = ingress_scan.scan_divisional_ingresses("mercury", YEAR_START, YEAR_END)
    back = [c for c in cs if c.to_index == (c.from_index - 1) % 12]
    assert back, "no retrograde cusp crossing found for Mercury in 2026"
    b = back[0]
    forward_again = [c for c in cs
                     if c.jd > b.jd and c.from_index == b.to_index
                     and c.to_index == b.from_index]
    assert forward_again, "Mercury re-entered no sign after a retrograde crossing"
    assert 10 <= len(cs) <= 18          # measured 14


def test_retrograde_flag_comes_from_motion():
    table = ingress_scan.scan_ingress_table(YEAR_START, YEAR_END)
    back = [e for e in table["events"]
            if e["to_index"] == (e["from_index"] - 1) % 12]
    assert back
    assert all(e["retrograde"] for e in back), \
        "a backward cusp crossing must read retrograde from the speed sign"


def test_ingress_table_covers_every_body_and_records_its_frame():
    t = ingress_scan.scan_ingress_table(YEAR_START, YEAR_END)
    assert t["errors"] == {}
    assert t["scanned"]["ayanamsa"] == "LAHIRI"
    assert t["scanned"]["nirayana"] is True
    assert t["scanned"]["n_divisions"] == 12
    bodies = {e["body"] for e in t["events"]}
    # Saturn legitimately makes no sign ingress in 2026 (~2.5 years per sign), so
    # its ABSENCE is correct and is asserted as such rather than ignored.
    assert "saturn" not in bodies
    assert {"sun", "moon", "mercury", "venus", "mars"} <= bodies
    assert all(e["jd"] <= t2["jd"] for e, t2 in
               zip(t["events"], t["events"][1:]))


def test_per_body_counts_are_in_measured_bands():
    """Measured 2026: moon 161, mercury 14, venus 12, sun 12, mars 8, jupiter 2.
    Bands are wide enough to absorb a backend change and narrow enough that a
    dropped retrograde pair or a doubled crossing fails."""
    t = ingress_scan.scan_ingress_table(YEAR_START, YEAR_END)
    counts: dict[str, int] = {}
    for e in t["events"]:
        counts[e["body"]] = counts.get(e["body"], 0) + 1
    assert 150 <= counts["moon"] <= 172      # ~13.4 sign changes / lunar month
    assert 12 <= counts["mercury"] <= 18
    assert 10 <= counts["venus"] <= 16
    assert 6 <= counts["mars"] <= 12
    assert 1 <= counts["jupiter"] <= 4


def test_nakshatra_division_is_the_same_primitive():
    """n_divisions is a parameter, not a special case: 27 divisions must give the
    27/12 ratio of crossings for the same body and window, within a crossing or
    two of rounding."""
    signs = ingress_scan.scan_divisional_ingresses(
        "sun", YEAR_START, YEAR_END, n_divisions=12)
    naks = ingress_scan.scan_divisional_ingresses(
        "sun", YEAR_START, YEAR_END, n_divisions=27)
    assert len(signs) == 12
    assert 25 <= len(naks) <= 28
    assert all(0 <= c.to_index < 27 for c in naks)


def test_unknown_body_refuses_rather_than_guessing_a_rate():
    """A missing rate bound is a correctness hole, not a default: the prune is
    only valid against a true upper bound, so an unmeasured body must refuse."""
    import pytest
    with pytest.raises(ValueError, match="no measured rate bound"):
        ingress_scan.scan_divisional_ingresses(
            "pluto", YEAR_START, YEAR_END, swe_id=swe.PLUTO)


def test_one_failing_body_does_not_discard_the_others():
    """Per-body isolation: a bad id must cost one body, not the table."""
    bodies = dict(ingress_scan.DEFAULT_BODIES)
    bodies["mars"] = 999_999          # invalid swisseph id
    t = ingress_scan.scan_ingress_table(YEAR_START, YEAR_END, bodies=bodies)
    assert "mars" in t["errors"]
    assert {"sun", "moon", "mercury"} <= {e["body"] for e in t["events"]}
