"""
mudda_dasha_natal_moon_nakshatra_check.py
Standalone (non-pytest) diagnostic: for each reference chart, compute the
NATAL Moon's sidereal (Lahiri) longitude via the existing chart-calculation
pipeline (calculate_chart()), derive its nakshatra (1-27) and the
Vimshottari lord whose Mahadasha runs first at birth (standard repeating
9-lord cycle starting from Ashwini), and report age-in-completed-years at
the 2026 Varsha epoch.

Read-only diagnostic -- does NOT call or modify calculate_mudda_dasha(), and
does NOT compute or compare against observed Mudda Dasha starting lords.
Raw natal-dasha-lord / age report only, for a follow-on hypothesis (after
rashi-sign lord, Varsha-Lagna-nakshatra lord, and Varsha-Moon-nakshatra
lord -- see the sibling mudda_dasha_*_check.py scripts in this directory).

calculate_chart() already derives lagna_chart["nakshatra"] /
["nakshatra_lord"] from the natal Moon's longitude internally (moon_nak_lord
via _nakshatra()), but does not expose the longitude or degree-in-sign. This
script makes one additional swe.calc_ut() call at the natal jd_ut (already
returned in calculate_chart()'s meta) to recover the longitude -- the same
Moon longitude calculate_chart() computed internally, just with the
longitude retained. The independently derived sign/nakshatra/lord are
cross-checked against calculate_chart()'s own lagna_chart fields as a
consistency check.

Run from the repo root:
    python tests/manual/mudda_dasha_natal_moon_nakshatra_check.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import swisseph as swe

from agent.chart_calculator import (
    NAKSHATRAS,
    _DATE_FMTS,
    _nakshatra,
    _sign,
    calculate_chart,
)
from datetime import datetime

VARSHA_YEAR = 2026

CHARTS = [
    {"name": "Sulabh",   "dob": "6 April 1988", "tob": "00:30", "place": "Calcutta, India"},
    {"name": "Surbhi",   "dob": "11 Sep 1992",  "tob": "10:30", "place": "Patna, India"},
    {"name": "Sheridan", "dob": "27 May 1984",  "tob": "08:00", "place": "Durban, South Africa"},
    {"name": "David",    "dob": "19 Jan 1976",  "tob": "22:00", "place": "London, UK"},
]

rows: list[dict] = []
failures: list[str] = []

print(f"Natal Moon nakshatra / first-Mahadasha-lord diagnostic -- "
      f"age as of Varsha year {VARSHA_YEAR}\n")

swe.set_sid_mode(swe.SIDM_LAHIRI)

for c in CHARTS:
    try:
        natal = calculate_chart(c["name"], c["dob"], c["tob"], c["place"])
        jd_ut = natal["meta"]["jd_ut"]
    except (ValueError, RuntimeError) as exc:
        print(f"FAIL: {c['name']} setup raised: {exc}")
        failures.append(c["name"])
        continue

    try:
        xx, ret = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
        if ret < 0:
            raise RuntimeError(f"pyswisseph error calculating Moon (retflag={ret})")
        moon_lon = xx[0] % 360
    except Exception as exc:
        print(f"FAIL: {c['name']} Moon longitude calc raised: {exc}")
        failures.append(c["name"])
        continue

    moon_sign = _sign(moon_lon)
    degree_in_sign = moon_lon % 30

    try:
        nak_name, _pada, nak_lord = _nakshatra(moon_lon)
        nak_number = NAKSHATRAS.index(nak_name) + 1
    except (ValueError, KeyError) as exc:
        print(f"FAIL: {c['name']} nakshatra derivation raised: {exc}")
        failures.append(c["name"])
        continue

    # Consistency check against calculate_chart()'s own lagna_chart fields
    expected_sign = natal["lagna_chart"]["rasi"]
    expected_nak = natal["lagna_chart"]["nakshatra"]
    expected_lord = natal["lagna_chart"]["nakshatra_lord"]
    if (moon_sign, nak_name, nak_lord) != (expected_sign, expected_nak, expected_lord):
        print(f"WARNING: {c['name']} mismatch vs calculate_chart() lagna_chart "
              f"(independent: {moon_sign}/{nak_name}/{nak_lord}, "
              f"pipeline: {expected_sign}/{expected_nak}/{expected_lord})")

    birth_year = None
    for fmt in _DATE_FMTS:
        try:
            birth_year = datetime.strptime(c["dob"].strip(), fmt).year
            break
        except ValueError:
            pass
    if birth_year is None:
        print(f"FAIL: {c['name']} unrecognized date format: '{c['dob']}'")
        failures.append(c["name"])
        continue

    age = VARSHA_YEAR - birth_year

    rows.append({
        "name": c["name"],
        "moon_sign": moon_sign,
        "degree_in_sign": degree_in_sign,
        "nak_name": nak_name,
        "nak_number": nak_number,
        "nak_lord": nak_lord,
        "age": age,
    })

# --- table ---
header = (f"{'Name':<10} {'Natal Moon':<13} {'Deg-in-sign':>11}  "
          f"{'Nakshatra':<20} {'1st Maha Lord':<13} {'Age@2026'}")
print(header)
print("-" * len(header))
for r in rows:
    nak_label = f"{r['nak_name']} ({r['nak_number']})"
    print(f"{r['name']:<10} {r['moon_sign']:<13} {r['degree_in_sign']:>11.4f}  "
          f"{nak_label:<20} {r['nak_lord']:<13} {r['age']}")

if failures:
    print(f"\n{len(failures)} chart(s) failed: {failures}")
    sys.exit(1)
print("\nDone.")
