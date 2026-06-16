"""
mudda_dasha_lagna_nakshatra_check.py
Standalone (non-pytest) diagnostic: for each reference chart, compute the
Varshaphal Lagna's exact ecliptic longitude via the existing
build_varshaphal_chart() pipeline, derive its nakshatra (1-27) and that
nakshatra's Vimshottari lord (standard repeating 9-lord cycle starting from
Ashwini), and compare against AstroSage's observed Mudda Dasha starting lord.

Read-only diagnostic for the Mudda Dasha "starting lord" design question --
does NOT call or modify calculate_mudda_dasha(). Two competing hypotheses
for the starting lord:
  - rashi-sign lord: SIGN_LORDS[Varshaphal Lagna sign] (the "Varshaphal
    Lagna lord" formula independently verified against Sulabh's full
    9-period AstroSage table)
  - nakshatra lord:  Vimshottari lord of the nakshatra the Varshaphal
    Lagna's exact longitude falls in (mirrors how natal Vimshottari dasha
    derives its starting lord from Moon's nakshatra)

Run from the repo root:
    python tests/manual/mudda_dasha_lagna_nakshatra_check.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.chart_calculator import (
    NAKSHATRAS,
    SIGNS,
    SIGN_LORDS,
    _nakshatra,
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

print(f"Mudda Dasha starting-lord diagnostic -- target year {TARGET_YEAR}\n")

for c in CHARTS:
    try:
        natal = calculate_chart(c["name"], c["dob"], c["tob"], c["place"])
        varshaphal = build_varshaphal_chart(natal, TARGET_YEAR)
    except (ValueError, RuntimeError) as exc:
        print(f"FAIL: {c['name']} setup raised: {exc}")
        failures.append(c["name"])
        continue

    lagna_sign = varshaphal["lagna"]
    degree_in_sign = varshaphal["lagna_degree_in_sign"]

    try:
        full_lon = (SIGNS.index(lagna_sign) * 30.0 + degree_in_sign) % 360
        nak_name, _pada, nak_lord = _nakshatra(full_lon)
        nak_number = NAKSHATRAS.index(nak_name) + 1
    except (ValueError, KeyError) as exc:
        print(f"FAIL: {c['name']} nakshatra derivation raised: {exc}")
        failures.append(c["name"])
        continue

    rashi_lord = SIGN_LORDS[lagna_sign]

    rows.append({
        "name": c["name"],
        "lagna_sign": lagna_sign,
        "degree_in_sign": degree_in_sign,
        "nak_name": nak_name,
        "nak_number": nak_number,
        "nak_lord": nak_lord,
        "rashi_lord": rashi_lord,
        "observed_lord": c["observed_lord"],
        "epoch_local": varshaphal["epoch"]["local_datetime"],
    })

# --- table ---
header = (f"{'Name':<10} {'Varsha Lagna':<13} {'Deg-in-sign':>11}  "
          f"{'Nakshatra':<20} {'Nak Lord':<9} {'Rashi Lord':<10}")
print(header)
print("-" * len(header))
for r in rows:
    nak_label = f"{r['nak_name']} ({r['nak_number']})"
    print(f"{r['name']:<10} {r['lagna_sign']:<13} {r['degree_in_sign']:>11.4f}  "
          f"{nak_label:<20} {r['nak_lord']:<9} {r['rashi_lord']:<10}")

print()
print(f"{'Name':<10} {'Nak Lord':<9} {'Observed start':<14} {'Nak Lord Match?'}")
for r in rows:
    status = "YES" if r["nak_lord"] == r["observed_lord"] else "NO"
    print(f"{r['name']:<10} {r['nak_lord']:<9} {r['observed_lord']:<14} {status}")

print("\nComputed Varshaphal epoch (local), for cross-reference against "
      "reference_charts.md:")
for r in rows:
    print(f"  {r['name']:<10} {r['epoch_local']}")

if failures:
    print(f"\n{len(failures)} chart(s) failed: {failures}")
    sys.exit(1)
print("\nDone.")
