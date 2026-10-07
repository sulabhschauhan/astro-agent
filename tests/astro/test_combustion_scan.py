"""Tests for agent/calculations/transits/combustion_scan.py (S147).

The SCANNER LOGIC -- boundary finding, keeping only combust spans, orb selection,
retrograde-from-speed -- is validated against a SYNTHETIC ephemeris (monkeypatched
Sun/planet positions), so these are deterministic hard asserts that need no
ephemeris files. The real-ephemeris intervals are ratified measure-first
(observed on-device against JHora/AstroSage, then frozen as asserts) -- NOT
fabricated here."""
from __future__ import annotations

import swisseph as swe

from agent.calculations.transits import combustion_scan as CS
from agent.calculations.helpers import ephemeris

_SUN_LON = 100.0


def _install_v_separation(monkeypatch, *, down_rate, trough_jd, speed):
    """Synthetic ephemeris: Sun fixed at _SUN_LON; the scanned planet's SEPARATION
    from the Sun is a V -- falling to 0 at trough_jd then rising -- so a single
    clean combust interval forms wherever separation < orb. `speed` fixes the
    sign the predicate reads for retrograde."""
    def fake_lon(jd, pid):
        if pid == swe.SUN:
            return _SUN_LON
        raise AssertionError("only the Sun is read via sidereal_longitude here")

    def fake_pos(jd, pid):
        sep = abs(jd - trough_jd) * down_rate          # V-shaped separation
        lon = (_SUN_LON + sep) % 360.0
        return ephemeris.SiderealPosition(longitude=lon, speed=speed)

    monkeypatch.setattr(ephemeris, "sidereal_longitude", fake_lon)
    monkeypatch.setattr(ephemeris, "sidereal_position", fake_pos)


def test_single_combust_interval_brackets_the_orb_crossing(monkeypatch):
    # Mars, direct orb 17 deg. Separation falls 3 deg/day to 0 at t0+10, rises back.
    t0 = 2460000.0
    _install_v_separation(monkeypatch, down_rate=3.0, trough_jd=t0 + 10, speed=+1.0)
    out = CS.scan_combustion_windows(t0, t0 + 20, planets={"mars": swe.MARS})
    iv = out["intervals"]
    assert len(iv) == 1 and iv[0]["planet"] == "mars"
    # enter: 30-3t=17 -> t=13/3; exit: 3(t-10)=17 -> t=10+17/3
    assert abs(iv[0]["start_jd"] - (t0 + 13 / 3)) < 1e-3
    assert abs(iv[0]["end_jd"] - (t0 + 10 + 17 / 3)) < 1e-3
    assert iv[0]["retrograde_at_mid"] is False


def test_retrograde_speed_narrows_mercury_orb(monkeypatch):
    # Mercury retro orb is 12 (vs 14 direct). Negative speed must select 12,
    # so the combust interval is NARROWER than the direct-orb one would be.
    t0 = 2460000.0
    _install_v_separation(monkeypatch, down_rate=3.0, trough_jd=t0 + 10, speed=-1.0)
    out = CS.scan_combustion_windows(t0, t0 + 20, planets={"mercury": swe.MERCURY})
    iv = out["intervals"]
    assert len(iv) == 1 and iv[0]["retrograde_at_mid"] is True
    # enter at 30-3t=12 -> t=6 ; exit at 3(t-10)=12 -> t=14
    assert abs(iv[0]["start_jd"] - (t0 + 6.0)) < 1e-3
    assert abs(iv[0]["end_jd"] - (t0 + 14.0)) < 1e-3


def test_never_combust_yields_no_intervals(monkeypatch):
    # Separation pinned well outside every orb -> empty.
    monkeypatch.setattr(ephemeris, "sidereal_longitude", lambda jd, pid: _SUN_LON)
    monkeypatch.setattr(
        ephemeris, "sidereal_position",
        lambda jd, pid: ephemeris.SiderealPosition(longitude=_SUN_LON + 40.0, speed=1.0))
    out = CS.scan_combustion_windows(2460000.0, 2460090.0, planets={"saturn": swe.SATURN})
    assert out["intervals"] == []
    assert out["scanned"]["planets"] == ["saturn"]


def test_predicate_orb_boundary_is_strict_less_than(monkeypatch):
    # Jupiter orb 11: sep 10.9 combust, sep 11.1 not; boundary is `< orb`.
    monkeypatch.setattr(ephemeris, "sidereal_longitude", lambda jd, pid: _SUN_LON)

    def pos_at(sep):
        monkeypatch.setattr(
            ephemeris, "sidereal_position",
            lambda jd, pid, _s=sep: ephemeris.SiderealPosition(
                longitude=_SUN_LON + _s, speed=1.0))
    pos_at(10.9)
    assert CS._is_combust_at(2460000.0, "jupiter", swe.JUPITER) is True
    pos_at(11.1)
    assert CS._is_combust_at(2460000.0, "jupiter", swe.JUPITER) is False


def test_default_planets_are_the_five_taragrahas_no_moon():
    assert set(CS.TARAGRAHA_SWE_IDS) == {"mars", "mercury", "jupiter", "venus", "saturn"}
    assert "moon" not in CS.TARAGRAHA_SWE_IDS  # amavasya is the panchanga layer's job


def test_orb_for_mirrors_core_combustion_table():
    # Only Mercury and Venus narrow when retrograde; others keep the direct orb.
    assert CS._orb_for("mercury", retrograde=True) == 12.0
    assert CS._orb_for("mercury", retrograde=False) == 14.0
    assert CS._orb_for("venus", retrograde=True) == 8.0
    assert CS._orb_for("mars", retrograde=True) == 17.0   # no retro override
    assert CS._orb_for("saturn", retrograde=True) == 15.0
