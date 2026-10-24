"""Sub-engine A vs JHora oracle (Sulabh). Planets strict; Lagna accepted within
the DeltaT-explained band (JHora's stale DeltaT; see docs/KNOWN_DIVERGENCES.md)."""
import pytest
import swisseph as swe

from agent.calculations.annual.varsha_pravesh import compute_varsha_pravesh

NATAL = swe.julday(1988, 4, 5, 19.0)
LAT, LON = 22 + 34 / 60, 88 + 21 / 60
LAGNA_RATE = 15.04  # arcsec per second of time
MARGIN = 30.0


def _ist(y, mo, d, h, mi, s):
    return swe.julday(y, mo, d, h + mi / 60 + s / 3600 - 5.5)


def _lon(sign, d, m, s):
    return sign * 30 + d + m / 60 + s / 3600


# year: (pravesh jd, lagna, sun, moon, jupiter); signs 0=Ar
ORACLE = {
    2025: (_ist(2025, 4, 6, 12, 14, 10), _lon(3, 6, 29, 8.46), _lon(11, 22, 30, 56.53), _lon(3, 6, 57, 40.18), _lon(1, 22, 37, 3.83)),
    2026: (_ist(2026, 4, 6, 18, 28, 46), _lon(6, 1, 21, 44.24), _lon(11, 22, 30, 56.53), _lon(7, 12, 28, 6.96), _lon(2, 21, 57, 43.90)),
    2027: (_ist(2027, 4, 7, 0, 26, 57), _lon(8, 21, 55, 51.25), _lon(11, 22, 30, 56.53), _lon(11, 20, 0, 7.68), _lon(3, 22, 49, 1.30)),
}


def _d(a, b):
    return ((a - b + 180) % 360 - 180) * 3600


@pytest.mark.parametrize("year", sorted(ORACLE))
def test_pravesh_vs_jhora(year):
    jd, lagna, sun, moon, jup = ORACLE[year]
    r = compute_varsha_pravesh(NATAL, LAT, LON, year)
    p = r["planets_sid"]
    for name, exp in (("Sun", sun), ("Moon", moon), ("Jupiter", jup)):
        assert abs(_d(p[name], exp)) < 5.0, name
    dt = abs(r["pravesh_jd_ut"] - jd) * 86400
    assert abs(_d(r["ascendant_sid"], lagna)) <= dt * LAGNA_RATE + MARGIN


def test_boundary_flag_on_our_lagna():
    r = compute_varsha_pravesh(NATAL, LAT, LON, 2026)
    assert r["boundary_flag"] is True  # Lagna ~1.4 deg past Vi/Li cusp
    assert compute_varsha_pravesh(NATAL, LAT, LON, 2025)["boundary_flag"] is False
