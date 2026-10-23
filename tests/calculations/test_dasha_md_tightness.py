"""Cross-engine MAHADASHA-tightness guard (the Vimshottari-class tripwire).

PRINCIPLE: every dated dasha engine's MAHADASHA boundaries must reproduce its
JHora oracle within +/-2 days. A Mahadasha boundary is a whole number of
dasha-years anchored to the birth date; unlike an ANTARDASHA boundary it does
NOT breathe with the Sun's true speed. So a MD boundary that drifts past 2 days
means the engine's YEAR CONSTANT or its balance-at-birth is wrong -- precisely
the latent-defect class that produced Vimshottari's +/-37-day antardasa drift
(CLAUDE.md: "Pratyantar suppressed -- +/-37 day drift, wrong lord").

This test makes "keep MD tight" a CI INVARIANT across the whole dasha family,
not a per-engine promise, so that class of bug cannot ship quietly in ANY engine
-- including a future Vimshottari re-audit. It is deliberately SEPARATE from each
engine's own oracle test: those assert the full table (incl. the breathing AD
band); this one asserts only the non-breathing MD layer, uniformly, across
engines.

Each engine uses a DIFFERENT year constant BY DESIGN -- Ashtottari/Yogini use
the mean-sidereal year (365.256363), Narayana uses the mean-solar year
(365.2425), Vimshottari uses the Julian year (365.25). The invariant is not that
they agree with each other; it is that EACH reproduces its OWN oracle at MD
level, whatever constant it chose. A constant that is wrong for its tradition
surfaces here first.

Oracle: data/default_user/jhora_sulabh_dashas.md (Sulabh's committed JHora v8
pull). Moon/ascendant longitudes are the frozen values from the Narayana and
Ashtottari end-to-end tests (AstroSage D1, Lahiri/KP).

COVERAGE: Ashtottari and Narayana are wired now. Vimshottari and Yogini are
registered as explicit SKIPs with reasons (visible in the run, not silently
absent) -- add them when their blockers clear. This is the growth contract: a
new dated dasha engine adds a row here in the same change.

Python 3.11.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import swisseph as swe

_TOL_MD_DAYS = 2  # MD boundaries do not breathe; tight by design (see module docstring).

# ── Shared Sulabh fixtures ───────────────────────────────────────────────────
# Birth 1988-04-06 00:30 IST (UTC+5:30) -> 1988-04-05 19:00 UT.
_BIRTH_JD_UT = swe.julday(1988, 4, 5, 19.0)
_BIRTH_LDT = datetime(1988, 4, 6, 0, 30, tzinfo=timezone(timedelta(hours=5, minutes=30)))
_IST = timedelta(hours=5, minutes=30)
_MOON_LON = 212.229
_SULABH_LONS = {
    "Sun": 352.520, "Moon": 212.229, "Mars": 275.576, "Mercury": 337.876,
    "Jupiter": 12.561, "Venus": 38.328, "Saturn": 248.843, "Rahu": 328.398,
    "Ketu": 148.398,
}


def _local_date(jd: float):
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    return (datetime(y, m, d, tzinfo=timezone.utc) + timedelta(hours=h) + _IST).date()


# ── Per-engine MD-start extractors (engine -> [(lord/rasi, date)], time order) ─
def _ashtottari_md_starts():
    from agent.calculations.dashas.ashtottari import compute_ashtottari_dasha
    mds = compute_ashtottari_dasha(_MOON_LON, _BIRTH_JD_UT)
    return [(p.lord, _local_date(p.begin_jd)) for p in mds]


def _narayana_md_starts():
    # Narayana returns whole-year lengths (no dates); compose mean-solar dates
    # exactly as narayana_facts does (365.2425 d from the birth local datetime).
    # First cycle only -- that is what the oracle table lists.
    from agent.calculations.dashas.narayana import compute_narayana_dasa
    nd = compute_narayana_dasa("Sagittarius", dict(_SULABH_LONS))
    out, cum = [], 0.0
    for p in nd.periods:
        start = _BIRTH_LDT + timedelta(days=cum * 365.2425)
        if p.cycle == 1:
            out.append((p.rasi, start.date()))
        cum += p.years
    return out


# ── Oracle MD starts (from jhora_sulabh_dashas.md) ───────────────────────────
_ASHTOTTARI_ORACLE = [
    ("Mars", "1980-06-06"), ("Merc", "1988-06-06"), ("Sat", "2005-06-06"),
    ("Jup", "2015-06-07"), ("Rah", "2034-06-07"), ("Ven", "2046-06-07"),
    ("Sun", "2067-06-07"), ("Moon", "2073-06-07"),
]
_NARAYANA_ORACLE = [  # first cycle
    ("Sagittarius", "1988-04-06"), ("Capricorn", "1992-04-06"),
    ("Aquarius", "1993-04-06"), ("Pisces", "1995-04-06"), ("Aries", "2006-04-06"),
    ("Taurus", "2016-04-06"), ("Gemini", "2028-04-06"), ("Cancer", "2036-04-06"),
    ("Leo", "2043-04-07"), ("Virgo", "2048-04-06"), ("Libra", "2053-04-06"),
    ("Scorpio", "2060-04-06"),
]

_ENGINES = [
    pytest.param(_ashtottari_md_starts, _ASHTOTTARI_ORACLE, id="ashtottari"),
    pytest.param(_narayana_md_starts, _NARAYANA_ORACLE, id="narayana"),
    pytest.param(
        None, None, id="vimshottari",
        marks=pytest.mark.skip(
            reason="engine is chart_calculator._calc_dasha (full-chart build, "
                   "Julian year); wire during the Vimshottari year-constant audit"),
    ),
    pytest.param(
        None, None, id="yogini",
        marks=pytest.mark.skip(
            reason="Yogini oracle lives in jhora_sulabh.md + AstroSage validator, "
                   "not jhora_sulabh_dashas.md; wire when the oracle is consolidated"),
    ),
]


@pytest.mark.parametrize("starts_fn,oracle", _ENGINES)
def test_mahadasha_boundaries_within_two_days(starts_fn, oracle):
    got = starts_fn()
    # Sequence exact (a lord/rasi error is never masked by the date tolerance).
    assert [g[0] for g in got[:len(oracle)]] == [o[0] for o in oracle], (
        "MD sequence mismatch"
    )
    # Each MD start within the tight non-breathing band.
    for (name, got_date), (_oname, oracle_iso) in zip(got, oracle):
        oracle_date = datetime.strptime(oracle_iso, "%Y-%m-%d").date()
        delta = abs((got_date - oracle_date).days)
        assert delta <= _TOL_MD_DAYS, (
            f"MD {name}: engine {got_date} vs oracle {oracle_iso} off {delta}d "
            f"(> {_TOL_MD_DAYS}d -- year-constant/balance drift, the Vimshottari class)"
        )
