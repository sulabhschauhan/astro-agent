"""
muntha_resolved_bhav_check.py
Standalone (non-pytest) validation: run calculate_muntha() with
astrosage_parsed_data fixtures for all 4 reference charts and check that
resolved_bhav matches AstroSage's printed Muntha bhav.

Same astrosage_parsed_data fixtures as mudda_dasha_validation_check.py:
  Sulabh   -> Virgo/2026     Sheridan -> Pisces/2026
  David    -> Cancer/2026    Surbhi   -> None (computed fallback)

Run from the repo root:
    python tests/manual/muntha_resolved_bhav_check.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.chart_calculator import (
    build_varshaphal_chart,
    calculate_chart,
    calculate_muntha,
)

TARGET_YEAR = 2026

CHARTS = [
    {
        "name": "Sulabh",
        "dob": "6 April 1988", "tob": "00:30", "place": "Calcutta, India",
        "astrosage_parsed_data": {"varshaphal_lagna": "Virgo", "varsha_year": 2026},
        "expected_bhav": 6,
    },
    {
        "name": "Surbhi",
        "dob": "11 Sep 1992", "tob": "10:30", "place": "Patna, India",
        "astrosage_parsed_data": None,
        "expected_bhav": 2,
    },
    {
        "name": "Sheridan",
        "dob": "27 May 1984", "tob": "08:00", "place": "Durban, South Africa",
        "astrosage_parsed_data": {"varshaphal_lagna": "Pisces", "varsha_year": 2026},
        "expected_bhav": 9,
    },
    {
        "name": "David",
        "dob": "19 Jan 1976", "tob": "22:00", "place": "London, UK",
        "astrosage_parsed_data": {"varshaphal_lagna": "Cancer", "varsha_year": 2026},
        "expected_bhav": 5,
    },
]

rows = []
failures = []

for c in CHARTS:
    try:
        natal = calculate_chart(c["name"], c["dob"], c["tob"], c["place"])
        varshaphal = build_varshaphal_chart(natal, TARGET_YEAR)
        muntha = calculate_muntha(natal, varshaphal, TARGET_YEAR, c["astrosage_parsed_data"])
    except (ValueError, RuntimeError) as exc:
        print(f"FAIL: {c['name']} raised: {exc}")
        failures.append(c["name"])
        continue

    rows.append({
        "name":         c["name"],
        "muntha_sign":  muntha["muntha_sign"],
        "resolved_bhav": muntha["resolved_bhav"],
        "expected_bhav": c["expected_bhav"],
        "bhav_source":  muntha["bhav_source"],
        "bhav_bs":      muntha["bhav_boundary_sensitive"],
        "bhav_primary": muntha["bhav_primary"],
        "ambiguous":    muntha["ambiguous"],
    })

header = (f"{'Name':<10} {'Muntha sign':<14} {'resolved_bhav/exp':<18} "
          f"{'Match':<6} {'bhav_source':<11} {'bhav_boundary_sensitive':<23} "
          f"{'bhav_primary (legacy)':}")
print(header)
print("-" * len(header))

mismatches = 0
for r in rows:
    match = "YES" if r["resolved_bhav"] == r["expected_bhav"] else "NO"
    if match == "NO":
        mismatches += 1
    ambig_note = f" (alt={r['bhav_primary']})" if r["ambiguous"] else ""
    print(f"{r['name']:<10} {r['muntha_sign']:<14} "
          f"{r['resolved_bhav']}/{r['expected_bhav']:<15} "
          f"{match:<6} {r['bhav_source']:<11} {str(r['bhav_bs']):<23} "
          f"{r['bhav_primary']}{ambig_note}")

print()
total = len(rows)
print(f"resolved_bhav match: {total - mismatches}/{total}")
if failures:
    print(f"{len(failures)} chart(s) failed to compute: {failures}")
    sys.exit(1)
if mismatches:
    print("MISMATCH(ES) above -- check muntha_sign and resolved Lagna sign.")
    sys.exit(1)
print("All resolved_bhav values match AstroSage expected.")
