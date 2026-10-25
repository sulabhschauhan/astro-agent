"""Unit test for the Varshaphal facts composer. The ephemeris-dependent pravesh
and day/night are monkeypatched so the COMPOSITION (year-lord, Muntha, dasha
seeds) is checked against the 2025 JHora oracle without Swiss-ephemeris files.
"""
import datetime as dt

import agent.astro.varshaphal_facts as vf

# 2025 annual D1 sidereal longitudes (JHora oracle).
_P2025 = {"Sun": 352.5157, "Moon": 96.9617, "Mars": 91.2008, "Mercury": 332.6795,
          "Jupiter": 52.6177, "Venus": 331.3412, "Saturn": 330.9149,
          "Rahu": 332.2419, "Ketu": 152.2419}
_ASC2025 = 96.4857          # Cancer 6.49
_JD2025 = 2460772.0         # arbitrary; only the cycle length matters for dashas


def _chart():
    tz = dt.timezone(dt.timedelta(hours=5, minutes=30))
    return {
        "meta": {
            "jd_ut": 2447257.27,            # natal (value unused by the mock)
            "lat": 22.5667, "lon": 88.35,
            "asc_lon_sidereal": 262.683,    # natal Lagna Sagittarius 22.68
            "local_datetime": dt.datetime(1988, 4, 6, 0, 30, tzinfo=tz),
        },
        "planetary_positions": {"Moon": {"longitude": 212.2322}},  # Visakha, 8.3% left
    }


def _patch(monkeypatch):
    def fake_pravesh(njd, lat, lon, year, cast_lat=None, cast_lon=None):
        jd = _JD2025 + (year - 2025) * 365.25
        return {"pravesh_jd_ut": jd, "ascendant_sid": _ASC2025,
                "planets_sid": dict(_P2025), "boundary_flag": False,
                "cast_place": {"lat": lat, "lon": lon}}
    monkeypatch.setattr(vf, "compute_varsha_pravesh", fake_pravesh)
    monkeypatch.setattr(vf, "_is_night", lambda *a, **k: False)  # 2025 is a day pravesh


def test_year_lord_is_venus_2025(monkeypatch):
    _patch(monkeypatch)
    out = vf.build_varshaphal_facts(_chart(), target_year=2025)
    assert out["year"] == 2025
    assert out["year_lord"]["winner"] == "Venus"
    assert any(c["planet"] == "Venus" and c["aspect"] == "benefic"
               for c in out["year_lord"]["candidates"])


def test_muntha_capricorn(monkeypatch):
    _patch(monkeypatch)
    out = vf.build_varshaphal_facts(_chart(), target_year=2025)
    assert out["muntha"]["sign"] == "Capricorn"


def test_dasha_seeds_match_oracle(monkeypatch):
    _patch(monkeypatch)
    out = vf.build_varshaphal_facts(_chart(), target_year=2025)
    assert out["dashas"]["mudda"][0]["lord"] == "Saturn"
    assert out["dashas"]["yogini"][0]["lord"] == "Mercury"
    assert out["dashas"]["patyayini"][0]["lord"] == "Saturn"


def test_fail_soft_on_missing_meta(monkeypatch):
    _patch(monkeypatch)
    assert vf.build_varshaphal_facts({"meta": {}}, target_year=2025) == {}


def test_target_year_defaults_to_current_solar_year(monkeypatch):
    _patch(monkeypatch)
    # as_of after the April birthday -> same-year pravesh
    out = vf.build_varshaphal_facts(_chart(), as_of=dt.date(2025, 9, 1))
    assert out["year"] == 2025
    # as_of before the birthday -> previous year's pravesh still runs
    out2 = vf.build_varshaphal_facts(_chart(), as_of=dt.date(2025, 2, 1))
    assert out2["year"] == 2024
