"""
mudda_dasha_varsha_moon_nakshatra_check.py
Standalone (non-pytest) diagnostic: for each reference chart, take the
Varshaphal epoch jd_ut from the existing build_varshaphal_chart() pipeline,
compute the Moon's sidereal (Lahiri) longitude AT THAT EPOCH, derive its
nakshatra (1-27) and that nakshatra's Vimshottari lord (standard repeating
9-lord cycle starting from Ashwini), and compare against AstroSage's
observed Mudda Dasha starting lord.

Read-only diagnostic for the Mudda Dasha "starting lord" design question --
does NOT call or modify calculate_mudda_dasha(). Third hypothesis for the
starting lord (after rashi-sign lord and Varsha-Lagna-nakshatra lord, see
mudda_dasha_lagna_nakshatra_check.py): the Varshaphal Moon's nakshatra lord
-- mirrors how natal Vimshottari dasha derives its starting lord from the
natal Moon's nakshatra, applied instead to the solar-return chart's Moon.

build_varshaphal_chart()'s own planetary_positions dict only carries
{house, sign, dignity, retrograde} for Moon (no longitude/degree-in-sign),
so this script makes one additional swe.calc_ut() call at the epoch's jd_ut
(already returned by build_varshaphal_chart) to get the exact longitude --
the same Moon longitude build_varshaphal_chart computed internally via
_calc_planets(), just with the longitude retained. The independently
computed sign is cross-checked against build_varshaphal_chart's own
planetary_positions["Moon"]["sign"] as a consistency check.

Run from the repo root:
    python tests/manual/mudda_dasha_varsha_moon_nakshatra_check.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import swisseph as swe

from agent.chart_calculator import (
    NAKSHATRAS,
    SIGNS,
    _nakshatra,
    _sign,
    build_varshaphal_chart,
    calculate_chart,
)

TARGET_YEAR = 2026

CHARTS = [
    {"name": "Sulabh",   "dob": "6 April 1988", "tob": "00:30", "place": "Calcutta, India",     "observed_lord": "Mercury"},
    {"name": "Surbhi",   "dob": "11 Sep 1992",  "tob": "10:30", "place": "Patna, India",         "observed_lord": "Moon"},
    {"name": "Sheridan", "dob": "27 May 1984",  "tob": "08:00", "place": "Durban, South Africa", "observed_lord": "Jupiter"},
    {"name": "David",    "dob": "19 Jan 1976",  "tob": "22:00", "place": "London, UK",           "observed_lord": "Rahu"},
]

rows: list[dict] = []
failures: list[str] = []

print(f"Mudda Dasha starting-lord diagnostic (Varsha Moon) -- target year {TARGET_YEAR}\n")

swe.set_sid_mode(swe.SIDM_LAHIRI)

for c in CHARTS:
    try:
        natal = calculate_chart(c["name"], c["dob"], c["tob"], c["place"])
        varshaphal = build_varshaphal_chart(natal, TARGET_YEAR)
        jd_ut = varshaphal["epoch"]["jd_ut"]
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

    expected_sign = varshaphal["planetary_positions"]["Moon"]["sign"]
    if moon_sign != expected_sign:
        print(f"WARNING: {c['name']} sign mismatch vs build_varshaphal_chart "
              f"(independent calc: {moon_sign}, pipeline: {expected_sign})")

    rows.append({
        "name": c["name"],
        "moon_sign": moon_sign,
        "degree_in_sign": degree_in_sign,
        "nak_name": nak_name,
        "nak_number": nak_number,
        "nak_lord": nak_lord,
        "observed_lord": c["observed_lord"],
    })

# --- table ---
header = (f"{'Name':<10} {'Varsha Moon':<13} {'Deg-in-sign':>11}  "
          f"{'Nakshatra':<20} {'Nak Lord':<9}")
print(header)
print("-" * len(header))
for r in rows:
    nak_label = f"{r['nak_name']} ({r['nak_number']})"
    print(f"{r['name']:<10} {r['moon_sign']:<13} {r['degree_in_sign']:>11.4f}  "
          f"{nak_label:<20} {r['nak_lord']:<9}")

print()
print(f"{'Name':<10} {'Nak Lord':<9} {'Observed start':<14} {'Nak Lord Match?'}")
for r in rows:
    status = "YES" if r["nak_lord"] == r["observed_lord"] else "NO"
    print(f"{r['name']:<10} {r['nak_lord']:<9} {r['observed_lord']:<14} {status}")

if failures:
    print(f"\n{len(failures)} chart(s) failed: {failures}")
    sys.exit(1)
print("\nDone.")
