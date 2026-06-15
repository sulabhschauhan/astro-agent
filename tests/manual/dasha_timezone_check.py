"""
dasha_timezone_check.py
Standalone (non-pytest) manual check for Task B3: resolve_timezone_offset()
(via the shared _local_datetime() helper) wired into calculate_chart()'s
birth_local, replacing the hardcoded _IST offset used to anchor
_calc_dasha()'s Vimshottari timeline.

Two cases:
  1. REGRESSION -- Sulabh (Calcutta, India; resolves to UTC+5.5, same as the
     old hardcoded _IST). _calc_dasha()'s output must be byte-for-byte
     identical whether anchored on the old utc_dt.astimezone(_IST) or the
     new _local_datetime(utc_dt, lat, lon) -- both resolve to the same
     +5:30 instant for Calcutta, so B3 must not change Sulabh's dasha at
     all.

     Note: kundali_summary.txt's DASHA TIMELINE section reflects AstroSage's
     numbers, which differ from our _calc_dasha() output by ~3-36 days --
     this is the pre-existing, already-documented +-37-day Antardasha drift
     (see _calc_dasha's DASHA ACCURACY NOTE), unrelated to B3. It is not
     used as the regression baseline here.
  2. HARDEST CASE -- David (London, UK; 19 Jan 1976, 22:00:00, resolves to
     UTC+0.0 -- see playbook_export/reference/reference_charts.md Chart 4).
     _calc_dasha()'s public return is relative to "now" (decades past
     David's birth), so this case replicates the i==0 ("first mahadasha")
     branch of _calc_dasha() inline, anchored on birth_local, and checks the
     Ketu -> Venus transition date against AstroSage (Ketu Mahadasha balance
     at birth = 0Y 10M 17D, transition 7 Dec 1976), within +-1 day
     (documented Vimshottari drift tolerance).

Run from the repo root:
    python tests/manual/dasha_timezone_check.py
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import swisseph as swe

from agent.chart_calculator import (
    DASHA_ORDER,
    DASHA_YEARS,
    _IST,
    _NAK_LORDS,
    _add_years,
    _calc_dasha,
    _calc_planets,
    _local_datetime,
    calculate_chart,
    geocode_place,
    to_julian_day,
)

failures: list[str] = []

# --- Case 1: REGRESSION -- Sulabh (Calcutta, IST, offset 5.5) ---------------
print("Case 1: Sulabh (Calcutta, India) -- dasha regression: old _IST anchor "
      "vs new _local_datetime anchor")

try:
    lat, lon = geocode_place("Calcutta, India")
    jd_ut, utc_dt = to_julian_day("6 April 1988", "00:30:00", lat, lon)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    moon_lon = _calc_planets(jd_ut, 0.0)["Moon"]["longitude"]

    birth_ist_old = utc_dt.astimezone(_IST)
    birth_local_new = _local_datetime(utc_dt, lat, lon)
    dasha_old = _calc_dasha(moon_lon, birth_ist_old)
    dasha_new = _calc_dasha(moon_lon, birth_local_new)

    sulabh = calculate_chart("Sulabh", "6 April 1988", "00:30:00", "Calcutta, India")
except (ValueError, RuntimeError) as exc:
    print(f"  FAIL: setup raised: {exc}")
    failures.append("Sulabh: setup")
else:
    print(f"  birth_ist_old   (offset {birth_ist_old.utcoffset()}): {birth_ist_old}")
    print(f"  birth_local_new (offset {birth_local_new.utcoffset()}): {birth_local_new}")
    print(f"  current_mahadasha:  {dasha_new['current_mahadasha']}")
    print(f"  current_antardasha: {dasha_new['current_antardasha']}")

    if dasha_old == dasha_new:
        print("  PASS: _calc_dasha output unchanged (old _IST anchor == new "
              "_local_datetime anchor)")
    else:
        print("  FAIL: _calc_dasha output differs between old and new anchor")
        failures.append("Sulabh: dasha output changed")

    if sulabh["dasha"] == dasha_new:
        print("  PASS: calculate_chart()['dasha'] matches direct _calc_dasha "
              "call (wiring intact)")
    else:
        print(f"  FAIL: calculate_chart()['dasha'] = {sulabh['dasha']}")
        failures.append("Sulabh: calculate_chart dasha mismatch")

print()

# --- Case 2: HARDEST CASE -- David (London, UK, 19 Jan 1976, offset 0.0) ----
print("Case 2: David (London, UK, 19 Jan 1976, 22:00:00) -- first-mahadasha "
      "(birth-anchored)")

EXPECTED_TRANSITION = date(1976, 12, 7)  # AstroSage: Ketu balance 0Y 10M 17D

try:
    lat, lon = geocode_place("London, UK")
    jd_ut, utc_dt = to_julian_day("19 Jan 1976", "22:00:00", lat, lon)
    birth_local = _local_datetime(utc_dt, lat, lon)

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    planets = _calc_planets(jd_ut, 0.0)
    moon_lon = planets["Moon"]["longitude"]
except (ValueError, RuntimeError) as exc:
    print(f"  FAIL: setup raised: {exc}")
    failures.append("David: setup")
else:
    print(f"  birth_local: {birth_local} (offset {birth_local.utcoffset()})")
    print(f"  moon_lon (sidereal): {moon_lon:.6f}")

    # Replicates _calc_dasha's i==0 branch: nakshatra lord at birth starts
    # the first mahadasha, with only the remaining fraction of its full
    # duration.
    nak_size = 360.0 / 27
    nak_idx = int(moon_lon / nak_size) % 27
    nak_lord = _NAK_LORDS[nak_idx]
    elapsed_frac = (moon_lon % nak_size) / nak_size
    remaining_frac = 1.0 - elapsed_frac

    balance_years = DASHA_YEARS[nak_lord] * remaining_frac
    transition = _add_years(birth_local, balance_years)
    next_lord = DASHA_ORDER[(DASHA_ORDER.index(nak_lord) + 1) % 9]

    balance_months = balance_years * 12
    print(f"  nakshatra lord at birth (first mahadasha): {nak_lord}")
    print(f"  balance at birth: {balance_years:.4f}y (~{balance_months:.1f}m)")
    print(f"  {nak_lord} -> {next_lord} transition: "
          f"{transition.day} {transition.strftime('%b')} {transition.year}")

    if nak_lord != "Ketu":
        print(f"  FAIL: expected nakshatra lord at birth = Ketu, got {nak_lord}")
        failures.append("David: nakshatra lord at birth")
    else:
        delta_days = abs((transition.date() - EXPECTED_TRANSITION).days)
        if delta_days <= 1:
            print(f"  PASS: Ketu -> Venus transition matches AstroSage "
                  f"(7 Dec 1976) within {delta_days}d")
        else:
            print(f"  FAIL: Ketu -> Venus transition off by {delta_days}d "
                  f"(expected 7 Dec 1976 +-1d)")
            failures.append("David: Ketu->Venus transition date")

print()
if failures:
    print(f"{len(failures)} check(s) failed: {failures}")
    sys.exit(1)
print("All checks passed.")
