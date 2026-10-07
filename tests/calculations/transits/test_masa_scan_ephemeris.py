"""masa_scan against the real ephemeris. NO SKIPS (see the ingress test's note).

HARDEST CASE FIRST. The window is 2026, chosen because it CONTAINS a real
zero-sankranti lunar month -- the intercalary case -- and because that month's
boundary is a near-coincidence: the Mithuna ingress falls 4.5 hours after the new
moon that opens the following month. Measured on this backend:

    new moon          2026-06-15 02:54 UT
    Mithuna sankranti 2026-06-15 07:23 UT   -> 4.48 h later

4.48 hours is 0.184 degrees of solar motion. Lahiri and Raman ayanamsa differ by
roughly 0.9 degrees, so THIS MONTH'S INTERCALARY STATUS IS AYANAMSA-DEPENDENT: on
Lahiri (what this project uses, and what the output records) the month is
zero-sankranti; a different nirayana convention moves the ingress across the new
moon and it is not. That is a property of the calendar, not a defect, and the
tests below pin the Lahiri answer and the margin that produces it so that any
future change of frame fails loudly instead of quietly renaming a month.
"""
import datetime as _dt
from zoneinfo import ZoneInfo

import swisseph as swe

from agent.calculations.transits import masa_scan

YEAR_START = swe.julday(2026, 1, 1, 0.0)
YEAR_END = swe.julday(2027, 1, 1, 0.0)

DUBAI = dict(tz=ZoneInfo("Asia/Dubai"), latitude=25.2048, longitude=55.2708)
DELHI = dict(tz=ZoneInfo("Asia/Kolkata"), latitude=28.6139, longitude=77.2090)


def _cal():
    return masa_scan.scan_masa_calendar(YEAR_START, YEAR_END)


def test_year_has_thirteen_months_one_of_them_intercalary():
    cal = _cal()
    months = cal["months"]
    assert len(months) == 13            # 12 + the intercalary month
    zero = [m for m in months if m.sankranti_count == 0]
    assert len(zero) == 1
    assert sum(1 for m in months if m.sankranti_count == 1) == 12


def test_the_intercalary_month_is_counted_but_never_named():
    """The engine reports the placement fact and withholds the name, because the
    naming rule is not citable from this project's corpus (masa.py docstring)."""
    zero = [m for m in _cal()["months"] if m.sankranti_count == 0][0]
    assert zero.masa_index is None
    assert zero.name_sa is None
    assert zero.contained_sankranti_rashis == ()
    assert zero.complete is True
    y, mo, d, _ = swe.revjul(zero.start_jd)
    assert (y, mo, d) == (2026, 5, 16)
    y, mo, d, _ = swe.revjul(zero.end_jd)
    assert (y, mo, d) == (2026, 6, 15)


def test_the_near_coincidence_margin_is_what_makes_it_intercalary():
    """Pins the 4.5-hour margin itself. If a future ayanamsa or backend change
    moves the Mithuna ingress across the new moon, this fails BEFORE a month gets
    silently renamed downstream."""
    cal = _cal()
    zero = [m for m in cal["months"] if m.sankranti_count == 0][0]
    after = [jd for (jd, r) in cal["sankrantis"] if jd >= zero.end_jd]
    margin_hours = (min(after) - zero.end_jd) * 24.0
    assert 0.0 < margin_hours < 12.0
    assert 3.5 < margin_hours < 5.5     # measured 4.48


def test_month_names_follow_the_contained_sankranti_not_the_next_one():
    """The month containing the Mesha ingress is Chaitra. An off-by-one naming
    rule (index = rashi + 1) names every month after its successor and would make
    this Vaishakha; that error was in the first draft and was caught by
    measurement, so it is pinned here."""
    named = {m.name_sa: m for m in _cal()["months"] if m.name_sa}
    chaitra = named["Chaitra"]
    assert chaitra.contained_sankranti_rashis == (0,)   # Mesha
    y, mo, d, _ = swe.revjul(chaitra.start_jd)
    assert (y, mo) == (2026, 3)
    assert named["Pausha"].contained_sankranti_rashis == (9,)   # Makara


def test_every_returned_month_is_complete_and_plausibly_long():
    for m in _cal()["months"]:
        assert m.complete is True
        length = m.end_jd - m.start_jd
        assert 29.0 < length < 30.1     # synodic month, measured 29.28-29.81


def test_months_are_contiguous_and_cover_the_window():
    months = _cal()["months"]
    for a, b in zip(months, months[1:]):
        assert a.end_jd == b.start_jd
    assert months[0].start_jd <= YEAR_START < months[0].end_jd
    assert months[-1].start_jd < YEAR_END <= months[-1].end_jd


def test_over_scan_means_no_edge_month_is_falsely_zero_sankranti():
    """THE FAILURE THE OVER-SCAN EXISTS TO PREVENT: without it the first and last
    months are clipped and report zero sankrantis for a scanning reason. Scanning
    three different windows that share a month must give that month the same name
    every time."""
    windows = [(swe.julday(2026, 2, 1, 0.0), swe.julday(2026, 12, 1, 0.0)),
               (swe.julday(2026, 3, 20, 0.0), swe.julday(2026, 6, 1, 0.0)),
               (YEAR_START, YEAR_END)]
    seen: dict[tuple[int, int, int], str | None] = {}
    for a, b in windows:
        for m in masa_scan.scan_masa_calendar(a, b)["months"]:
            y, mo, d, _ = swe.revjul(m.start_jd)
            key = (y, mo, d)
            if key in seen:
                assert seen[key] == m.name_sa
            seen[key] = m.name_sa
    # the Chaitra window starts mid-month in case 2; it must still be named
    assert "Chaitra" in seen.values()


def test_local_dates_use_the_first_sunrise_after_the_instant():
    """A masa begins on the day of the first SUNRISE after the new moon, not on
    the tz-localised date of the instant. The 2026-10-10 new moon is 15:50 UT =
    19:50 in Dubai, i.e. after that day's sunrise, so the month begins on the
    11th. Naive localisation gives the 10th -- the off-by-one this guards."""
    cal = _cal()
    target = [m for m in cal["months"]
              if swe.revjul(m.start_jd)[:3] == (2026, 10, 10)][0]
    row = masa_scan.resolve_local_dates([target], **DUBAI)[0]
    assert row["start_date"] == "2026-10-11"
    y, mo, d, h = swe.revjul(target.start_jd)
    naive = (_dt.datetime(y, mo, d, tzinfo=_dt.timezone.utc)
             + _dt.timedelta(hours=h)).astimezone(DUBAI["tz"]).date().isoformat()
    assert naive == "2026-10-10" and naive != row["start_date"]


def test_local_dates_are_place_dependent():
    """The instants are global; the dates are not. Two places must be allowed to
    disagree, and the engine must not pretend otherwise by defaulting a place."""
    months = _cal()["months"]
    dubai = masa_scan.resolve_local_dates(months, **DUBAI)
    delhi = masa_scan.resolve_local_dates(months, **DELHI)
    assert [r["start_jd"] for r in dubai] == [r["start_jd"] for r in delhi]
    assert any(a["start_date"] != b["start_date"]
               for a, b in zip(dubai, delhi))


def test_end_date_inclusive_is_the_day_before_the_next_month_starts():
    rows = masa_scan.resolve_local_dates(_cal()["months"], **DUBAI)
    for r in rows:
        end = _dt.date.fromisoformat(r["end_date"])
        assert _dt.date.fromisoformat(r["end_date_inclusive"]) == \
            end - _dt.timedelta(days=1)
    for a, b in zip(rows, rows[1:]):
        assert a["end_date"] == b["start_date"]


def test_result_records_its_ayanamsa():
    """An ingress instant is meaningless without the frame that defines the cusp,
    and this calendar's intercalary month turns on 0.18 degrees of it."""
    s = _cal()["scanned"]
    assert s["ayanamsa"] == "LAHIRI" and s["nirayana"] is True
    assert s["over_scan_days"] > 29.5


def test_inverted_window_raises():
    import pytest
    with pytest.raises(ValueError):
        masa_scan.scan_masa_calendar(YEAR_END, YEAR_START)
