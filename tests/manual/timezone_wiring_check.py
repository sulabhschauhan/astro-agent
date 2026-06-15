"""
timezone_wiring_check.py
Standalone (non-pytest) manual check for Task B1: resolve_timezone_offset()
wired into to_julian_day() / calculate_chart(), replacing the hardcoded IST
offset.

Two cases:
  1. REGRESSION — Sulabh (Calcutta, India; resolves to UTC+5.5, same as the
     old hardcoded _IST). D1 placements must be unchanged from the
     previously-validated 9/9 reference (data/default_user/kundali_summary.txt).
  2. HARDEST CASE — David (London, UK; 19 Jan 1976, 22:00:00, resolves to
     UTC+0.0 — the first non-IST offset exercised end-to-end). Lagna/Rasi/
     Sun-sign checked against Chart 4 in
     playbook_export/reference/reference_charts.md.

Run from the repo root:
    python tests/manual/timezone_wiring_check.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.chart_calculator import calculate_chart

failures: list[str] = []

# --- Case 1: REGRESSION — Sulabh (Calcutta, IST, offset 5.5) ---------------
print("Case 1: Sulabh (Calcutta, India) — regression vs validated 9/9 D1")

EXPECTED_SULABH_PLANETS = {
    "Sun":     ("Pisces", 4),
    "Moon":    ("Scorpio", 12),
    "Mars":    ("Capricorn", 2),
    "Mercury": ("Pisces", 4),
    "Jupiter": ("Aries", 5),
    "Venus":   ("Taurus", 6),
    "Saturn":  ("Sagittarius", 1),
    "Rahu":    ("Aquarius", 3),
    "Ketu":    ("Leo", 9),
}

try:
    sulabh = calculate_chart("Sulabh", "6 April 1988", "00:30:00", "Calcutta, India")
except (ValueError, RuntimeError) as exc:
    print(f"  FAIL: calculate_chart raised: {exc}")
    failures.append("Sulabh: calculate_chart")
else:
    lag = sulabh["lagna_chart"]
    if (lag["ascendant"], lag["rasi"]) == ("Sagittarius", "Scorpio"):
        print(f"  PASS: Lagna={lag['ascendant']}, Rasi={lag['rasi']}")
    else:
        print(f"  FAIL: Lagna/Rasi = {lag['ascendant']}/{lag['rasi']}, "
              f"expected Sagittarius/Scorpio")
        failures.append("Sulabh: lagna/rasi")

    mismatches = []
    for planet, (exp_sign, exp_house) in EXPECTED_SULABH_PLANETS.items():
        got = sulabh["planetary_positions"][planet]
        if (got["sign"], got["house"]) != (exp_sign, exp_house):
            mismatches.append(
                f"{planet}: got ({got['sign']}, house {got['house']}), "
                f"expected ({exp_sign}, house {exp_house})"
            )
    if mismatches:
        print("  FAIL: planetary placement mismatches:")
        for m in mismatches:
            print(f"    {m}")
        failures.append("Sulabh: planetary placements")
    else:
        print("  PASS: all 9/9 planetary placements unchanged")

print()

# --- Case 2: HARDEST CASE — David (London, UK, 19 Jan 1976, offset 0.0) ----
print("Case 2: David (London, UK, 19 Jan 1976, 22:00:00, offset 0.0)")

try:
    david = calculate_chart("David", "19 Jan 1976", "22:00:00", "London, UK")
except (ValueError, RuntimeError) as exc:
    print(f"  FAIL: calculate_chart raised: {exc}")
    failures.append("David: calculate_chart")
else:
    lag = david["lagna_chart"]
    pp = david["planetary_positions"]

    checks = [
        ("Lagna (ascendant)", lag["ascendant"], "Virgo"),
        ("Rasi (Moon sign)", lag["rasi"], "Leo"),
        ("Sun sign", pp["Sun"]["sign"], "Capricorn"),
        ("Moon sign", pp["Moon"]["sign"], "Leo"),
    ]
    for label, got, expected in checks:
        status = "PASS" if got == expected else "FAIL"
        print(f"  {status}: {label} = {got} (expected {expected})")
        if status == "FAIL":
            failures.append(f"David: {label}")

    print(f"  birth_details lat/lon: {david['birth_details']['lat']}, "
          f"{david['birth_details']['lon']}")
    print(f"  ayanamsha_lahiri: {david['meta']['ayanamsha_lahiri']} "
          f"(reference: 23.52194, cross-ephemeris residual expected)")

print()
if failures:
    print(f"{len(failures)} check(s) failed: {failures}")
    sys.exit(1)
print("All checks passed.")
