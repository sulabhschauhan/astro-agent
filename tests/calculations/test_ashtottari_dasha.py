"""Tests for agent/calculations/dashas/ashtottari.py -- Ashtottari dasa.

ORACLE: JHora v8 desktop pull for Sulabh (data/default_user/jhora_sulabh_dashas.md,
"Ashtottari Dasa" section, 2026-10-23), all 8 MDs expanded to antardasa. Moon
sidereal longitude (212.229, Vishakha) is the same frozen value the Narayana
end-to-end test uses (_SULABH["Moon"]); birth is 1988-04-06 00:30 IST
(UTC+5:30) -> 1988-04-05 19:00 UT. No ephemeris: the Moon longitude is given, so
the engine is exercised as a pure function (same style as test_narayana_dasa).

Dates are compared against the JHora oracle with a SPLIT tolerance: MD
boundaries +/-2 days (_TOL_MD_DAYS), AD boundaries +/-5 days (_TOL_AD_DAYS).
JUSTIFICATION: the engine uses the mean-sidereal year (365.256363); JHora dates
AD boundaries by the TRUE sidereal solar arc, which breathes +/-~4 days with the
Sun's speed (measured max 4d here). MDs are whole years anchored to the birth
date and do NOT breathe, so they stay tight -- the tight MD band is the tripwire
for a wrong year-constant (the Vimshottari class). The wider AD band is the
bounded true-solar-arc artifact (S154: a software precision artifact, not
doctrine), capped by physics and never compounded because the engine stops at
AD (no pratyantar -- that is what produced Vimshottari's +/-37d). SCOPE GUARD:
both are date-RENDERING tolerances only -- the lord SEQUENCE is asserted exactly.
TUNING NOTE: tighten the AD band only if a true-solar-arc dating upgrade lands
(which would also reverse the S154 doctrine); never widen either to make a
failing run pass.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import swisseph as swe

from agent.calculations.dashas.ashtottari import (
    AshtottariPeriod,
    compute_ashtottari_bhukti,
    compute_ashtottari_dasha,
    current_ashtottari_period,
    _ASHTOTTARI,
    _count_stars,
    _lord_index_for_star,
)

# ── Sulabh fixtures ──────────────────────────────────────────────────────────
_SULABH_MOON_LON = 212.229                       # sidereal, Vishakha (star 16)
_SULABH_BIRTH_JD = swe.julday(1988, 4, 5, 19.0)  # 1988-04-06 00:30 IST -> UT
_IST = timedelta(hours=5, minutes=30)

_TOL_MD_DAYS = 2  # MD boundaries: tight -- the tripwire for a wrong year-constant.
_TOL_AD_DAYS = 5  # AD boundaries: bounded true-solar-arc artifact (max 4d + 1d). See docstring.

_SEQUENCE = ("Sun", "Moon", "Mars", "Merc", "Sat", "Jup", "Rah", "Ven")
_YEARS = {"Sun": 6, "Moon": 15, "Mars": 8, "Merc": 17,
          "Sat": 10, "Jup": 19, "Rah": 12, "Ven": 21}


def _local_date(jd: float):
    """JD UT -> date in Sulabh's birth-local timezone (IST), matching how the
    facts layer renders boundaries (yogini_facts._local_date_iso)."""
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    utc = datetime(y, m, d, tzinfo=timezone.utc) + timedelta(hours=h)
    return (utc + _IST).date()


def _date(iso: str):
    return datetime.strptime(iso, "%Y-%m-%d").date()


def _assert_near(jd: float, iso: str, label: str, tol: int = _TOL_MD_DAYS):
    delta = abs((_local_date(jd) - _date(iso)).days)
    assert delta <= tol, (
        f"{label}: engine {_local_date(jd)} vs oracle {iso} differ by {delta}d "
        f"(> {tol}d tolerance)"
    )


# ── MD oracle: all 8 Mahadashas (lord, start, end) from JHora ────────────────
_MD_ORACLE = [
    ("Mars", "1980-06-06", "1988-06-06"),
    ("Merc", "1988-06-06", "2005-06-06"),
    ("Sat",  "2005-06-06", "2015-06-07"),
    ("Jup",  "2015-06-07", "2034-06-07"),
    ("Rah",  "2034-06-07", "2046-06-07"),
    ("Ven",  "2046-06-07", "2067-06-07"),
    ("Sun",  "2067-06-07", "2073-06-07"),
    ("Moon", "2073-06-07", "2088-06-07"),
]


def _sulabh_mds():
    return compute_ashtottari_dasha(_SULABH_MOON_LON, _SULABH_BIRTH_JD)


def test_sulabh_md_count_and_sequence():
    mds = _sulabh_mds()
    assert len(mds) == 8
    assert [p.lord for p in mds] == [lord for lord, _s, _e in _MD_ORACLE]
    # start lord Mars, seed MD begins pre-birth (full span, not truncated).
    assert mds[0].lord == "Mars"
    assert mds[0].begin_jd < _SULABH_BIRTH_JD < mds[0].end_jd


@pytest.mark.parametrize("i", range(8))
def test_sulabh_md_dates_vs_jhora(i):
    md = _sulabh_mds()[i]
    lord, start, end = _MD_ORACLE[i]
    assert md.lord == lord
    _assert_near(md.begin_jd, start, f"MD {lord} start")
    _assert_near(md.end_jd, end, f"MD {lord} end")


def test_sulabh_mds_are_contiguous():
    mds = _sulabh_mds()
    for a, b in zip(mds, mds[1:]):
        assert a.end_jd == b.begin_jd  # no gaps / overlaps


# ── AD oracle: the three hardest MDs (balance / live / longest span) ─────────
# (lord, start) per antardasa, time order. End of the last AD == MD end.
_AD_ORACLE = {
    # Mars MD -- the balance MD (pre-birth start, running AD at birth = Moon).
    "Mars": ([
        ("Mars", "1980-06-06"), ("Merc", "1981-01-09"), ("Sat", "1982-04-12"),
        ("Jup", "1983-01-09"), ("Rah", "1984-06-06"), ("Ven", "1985-04-26"),
        ("Sun", "1986-11-18"), ("Moon", "1987-04-26"),
    ], "1988-06-06"),
    # Jupiter MD -- the current/live MD (19y span).
    "Jup": ([
        ("Jup", "2015-06-07"), ("Rah", "2018-10-13"), ("Ven", "2020-11-21"),
        ("Sun", "2024-08-01"), ("Moon", "2025-08-22"), ("Mars", "2028-04-09"),
        ("Merc", "2029-09-08"), ("Sat", "2032-09-05"),
    ], "2034-06-07"),
    # Venus MD -- the longest lord (21y), maximum absolute AD drift.
    "Ven": ([
        ("Ven", "2046-06-07"), ("Sun", "2050-07-08"), ("Moon", "2051-09-09"),
        ("Mars", "2054-08-09"), ("Merc", "2056-02-25"), ("Sat", "2059-06-18"),
        ("Jup", "2061-05-27"), ("Rah", "2065-02-05"),
    ], "2067-06-07"),
}


@pytest.mark.parametrize("md_lord", list(_AD_ORACLE))
def test_sulabh_antardasha_vs_jhora(md_lord):
    md = next(p for p in _sulabh_mds() if p.lord == md_lord)
    ads = compute_ashtottari_bhukti(md)
    expected, md_end = _AD_ORACLE[md_lord]

    assert [a.lord for a in ads] == [lord for lord, _s in expected], (
        f"{md_lord} MD: AD sequence mismatch"
    )
    for a, (lord, start) in zip(ads, expected):
        _assert_near(a.begin_jd, start, f"{md_lord} MD / {lord} AD start", _TOL_AD_DAYS)
    # ADs nest exactly inside the MD: first begins at MD start, last ends at MD end.
    assert ads[0].begin_jd == md.begin_jd
    assert ads[-1].end_jd == md.end_jd
    _assert_near(ads[-1].end_jd, md_end, f"{md_lord} MD / last AD end", _TOL_AD_DAYS)


def test_sulabh_running_period_today_is_jupiter_moon():
    # 2026-10-23: Jupiter MD (2015-2034) / Moon AD (2025-08-22 - 2028-04-09).
    today_jd = swe.julday(2026, 10, 23, 12.0)
    mds = _sulabh_mds()
    cur_md = current_ashtottari_period(mds, today_jd)
    assert cur_md is not None and cur_md.lord == "Jup"
    cur_ad = current_ashtottari_period(compute_ashtottari_bhukti(cur_md), today_jd)
    assert cur_ad is not None and cur_ad.lord == "Moon"


# ── Structural / proportional invariants ─────────────────────────────────────
def test_md_lengths_match_nominal_years():
    for p in _sulabh_mds():
        span_years = (p.end_jd - p.begin_jd) / 365.256363
        assert abs(span_years - _YEARS[p.lord]) < 1e-6


def test_bhukti_proportions_sum_to_md_span():
    md = next(p for p in _sulabh_mds() if p.lord == "Jup")
    ads = compute_ashtottari_bhukti(md)
    total = sum(a.end_jd - a.begin_jd for a in ads)
    assert abs(total - (md.end_jd - md.begin_jd)) < 1e-6
    # each AD proportional to its lord's share of 108 (last pinned, so skip it)
    span = md.end_jd - md.begin_jd
    for a in ads[:-1]:
        assert abs((a.end_jd - a.begin_jd) - span * _YEARS[a.lord] / 108) < 1e-6


# ── Nakshatra->lord map (incl. Rahu's wrapping block) ────────────────────────
@pytest.mark.parametrize("star,expected_lord", [
    (6, "Sun"), (9, "Sun"), (10, "Moon"), (16, "Mars"), (17, "Merc"),
    (22, "Sat"), (25, "Jup"), (26, "Rah"), (27, "Rah"), (1, "Rah"), (2, "Rah"),
    (3, "Ven"), (5, "Ven"),
])
def test_lord_index_for_star(star, expected_lord):
    assert _ASHTOTTARI[_lord_index_for_star(star)][0] == expected_lord


def test_count_stars_wrap():
    assert _count_stars(13, 16) == 4   # Mars block
    assert _count_stars(26, 2) == 4    # Rahu wrapping block (26,27,1,2)


def test_star_spans_tile_all_27_once():
    owned = [_ASHTOTTARI[_lord_index_for_star(s)][0] for s in range(1, 28)]
    assert len(owned) == 27 and all(owned)


# ── Balance edges ────────────────────────────────────────────────────────────
def test_balance_at_block_start_begins_near_birth():
    # Moon at the very start of Sun's block (star 6 -> 66.667 deg): ~0 elapsed,
    # so the seed (Sun) MD begins essentially at birth.
    birth = swe.julday(2000, 1, 1, 0.0)
    mds = compute_ashtottari_dasha(5 * (360.0 / 27.0) + 1e-6, birth)
    assert mds[0].lord == "Sun"
    assert abs(mds[0].begin_jd - birth) < 2.0  # within ~2 days of birth


# ── Error handling ───────────────────────────────────────────────────────────
@pytest.mark.parametrize("bad", [-0.1, 360.0, 400.0])
def test_bad_moon_longitude_raises(bad):
    with pytest.raises(ValueError):
        compute_ashtottari_dasha(bad, _SULABH_BIRTH_JD)


def test_n_cycles_below_one_raises():
    with pytest.raises(ValueError):
        compute_ashtottari_dasha(_SULABH_MOON_LON, _SULABH_BIRTH_JD, n_cycles=0)


def test_bad_star_number_raises():
    with pytest.raises(ValueError):
        _lord_index_for_star(28)


def test_bhukti_bad_lord_raises():
    bogus = AshtottariPeriod(lord="Pluto", begin_jd=0.0, end_jd=1.0, years=1)
    with pytest.raises(ValueError):
        compute_ashtottari_bhukti(bogus)


def test_two_cycles_projects_16_mds():
    mds = compute_ashtottari_dasha(_SULABH_MOON_LON, _SULABH_BIRTH_JD, n_cycles=2)
    assert len(mds) == 16
    assert [p.lord for p in mds[:8]] == [p.lord for p in mds[8:]]
