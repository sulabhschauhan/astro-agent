"""
mudda_dasha_validation_check.py
Standalone (non-pytest) validation: run the new calculate_mudda_dasha()
against all 4 reference charts and compare computed vs AstroSage-derived
expected periods (lord, bhav, period_end date), reporting deltas.

Read-only / diagnostic -- exercises calculate_mudda_dasha() but does not
modify it or any other production function.

Run from the repo root:
    python tests/manual/mudda_dasha_validation_check.py
"""

import re
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.chart_calculator import (
    build_varshaphal_chart,
    calculate_chart,
    calculate_mudda_dasha,
    resolve_house_counting_lagna,
)

TARGET_YEAR = 2026

# Expected periods: (lord, bhav, period_end "Mon D" or "Mon D'YY")
CHARTS = [
    {
        "name": "Sulabh", "dob": "6 April 1988", "tob": "00:30", "place": "Calcutta, India",
        "astrosage_parsed_data": {"varshaphal_lagna": "Virgo", "varsha_year": 2026},
        "expected": [
            ("Mercury", 6, "May28"), ("Ketu", 12, "Jun18"), ("Venus", 8, "Aug18"),
            ("Sun", 7, "Sep5"), ("Moon", 3, "Oct6"), ("Mars", 7, "Oct27"),
            ("Rahu", 6, "Dec21"), ("Jupiter", 10, "Feb8'27"), ("Saturn", 7, "Apr6'27"),
        ],
    },
    {
        "name": "Surbhi", "dob": "11 Sep 1992", "tob": "10:30", "place": "Patna, India",
        "astrosage_parsed_data": None,
        "expected": [
            ("Moon", 3, "Oct12"), ("Mars", 12, "Nov2"), ("Rahu", 8, "Dec27"),
            ("Jupiter", 1, "Feb14'27"), ("Saturn", 9, "Apr13'27"), ("Mercury", 3, "Jun3'27"),
            ("Ketu", 2, "Jun25'27"), ("Venus", 4, "Aug24'27"), ("Sun", 2, "Sep12'27"),
        ],
    },
    {
        "name": "Sheridan", "dob": "27 May 1984", "tob": "08:00", "place": "Durban, South Africa",
        "astrosage_parsed_data": {"varshaphal_lagna": "Pisces", "varsha_year": 2026},
        "expected": [
            ("Jupiter", 4, "Jul15"), ("Saturn", 1, "Sep11"), ("Mercury", 3, "Nov2"),
            ("Ketu", 6, "Nov23"), ("Venus", 4, "Jan23'27"), ("Sun", 3, "Feb10'27"),
            ("Moon", 8, "Mar13'27"), ("Mars", 2, "Apr3'27"), ("Rahu", 12, "May28'27"),
        ],
    },
    {
        "name": "David", "dob": "19 Jan 1976", "tob": "22:00", "place": "London, UK",
        "astrosage_parsed_data": {"varshaphal_lagna": "Cancer", "varsha_year": 2026},
        "expected": [
            ("Rahu", 8, "Mar15"), ("Jupiter", 12, "May3"), ("Saturn", 9, "Jun29"),
            ("Mercury", 7, "Aug20"), ("Ketu", 2, "Sep10"), ("Venus", 7, "Nov10"),
            ("Sun", 7, "Nov29"), ("Moon", 7, "Dec29"), ("Mars", 7, "Jan19'27"),
        ],
    },
]


def _parse_expected_date(s: str) -> date:
    m = re.match(r"([A-Za-z]+)(\d+)(?:'(\d+))?$", s)
    if not m:
        raise ValueError(f"_parse_expected_date: unrecognized format '{s}'")
    month_str, day_str, yr_suffix = m.groups()
    year = TARGET_YEAR if yr_suffix is None else 2000 + int(yr_suffix)
    month = datetime.strptime(month_str, "%b").month
    return date(year, month, int(day_str))


total_mismatches = 0
total_periods = 0

for c in CHARTS:
    print(f"=== {c['name']} ===")
    try:
        natal = calculate_chart(c["name"], c["dob"], c["tob"], c["place"])
        varshaphal = build_varshaphal_chart(natal, TARGET_YEAR)
        mudda = calculate_mudda_dasha(natal, varshaphal, TARGET_YEAR, c["astrosage_parsed_data"])
    except (ValueError, RuntimeError) as exc:
        print(f"FAIL: {c['name']} setup raised: {exc}")
        continue

    header = (f"{'#':<2} {'Lord (got/exp)':<22} {'Bhav (got/exp)':<15} "
              f"{'End (got/exp)':<26} {'Delta(days/bhav)'}")
    print(header)
    print("-" * len(header))

    for i, (period, (exp_lord, exp_bhav, exp_end_str)) in enumerate(zip(mudda, c["expected"]), 1):
        got_lord = period["lord"]
        got_bhav = period["bhav"]
        got_end = datetime.strptime(period["period_end"], "%d %b %Y").date()
        exp_end = _parse_expected_date(exp_end_str)

        lord_label = f"{got_lord}/{exp_lord}"
        bhav_label = f"{got_bhav}/{exp_bhav}"
        end_label = f"{got_end.isoformat()}/{exp_end.isoformat()}"

        delta_days = (got_end - exp_end).days
        delta_bhav = got_bhav - exp_bhav
        total_periods += 1
        if got_lord != exp_lord or delta_days != 0 or delta_bhav != 0:
            total_mismatches += 1
            flag = "  <-- MISMATCH"
        else:
            flag = ""

        print(f"{i:<2} {lord_label:<22} {bhav_label:<15} "
              f"{end_label:<26} {delta_days}d / {delta_bhav}bhav{flag}")
    print()

print(f"Total periods checked: {total_periods}, mismatches: {total_mismatches}")


# ─── Guard test: mismatched-year astrosage_parsed_data (Sulabh) ──────────────
# astrosage_parsed_data carries varshaphal_lagna="Virgo" but varsha_year=2025,
# while target_year=2026. resolve_house_counting_lagna() must reject this
# (year mismatch) and fall back to the computed Lagna (Libra,
# boundary_sensitive=True). calculate_mudda_dasha()'s bhav output should then
# revert to the pre-fix uniform -1 shift (Sulabh's original 0/9 result from
# before this session's fix).
print("\n=== Guard test: Sulabh, astrosage varsha_year=2025 != target_year=2026 ===")

sulabh = CHARTS[0]
try:
    natal = calculate_chart(sulabh["name"], sulabh["dob"], sulabh["tob"], sulabh["place"])
    varshaphal = build_varshaphal_chart(natal, TARGET_YEAR)
except (ValueError, RuntimeError) as exc:
    print(f"FAIL: Sulabh setup raised: {exc}")
    sys.exit(1)

mismatched = {"varshaphal_lagna": "Virgo", "varsha_year": 2025}

try:
    resolved = resolve_house_counting_lagna(varshaphal, mismatched, TARGET_YEAR)
except ValueError as exc:
    print(f"FAIL: resolve_house_counting_lagna raised: {exc}")
    sys.exit(1)

expected_resolved = {"lagna_sign": "Libra", "source": "computed", "boundary_sensitive": True}
if resolved == expected_resolved:
    print(f"PASS: resolve_house_counting_lagna fell back to computed -> {resolved}")
else:
    print("BUG: resolve_house_counting_lagna did NOT fall back as expected "
          "-- mismatched-year AstroSage data may be silently accepted.")
    print(f"     got:      {resolved}")
    print(f"     expected: {expected_resolved}")

try:
    mudda_mismatched = calculate_mudda_dasha(natal, varshaphal, TARGET_YEAR, mismatched)
except (ValueError, RuntimeError) as exc:
    print(f"FAIL: calculate_mudda_dasha raised: {exc}")
    sys.exit(1)

print(f"{'#':<2} {'Lord':<10} {'Bhav (got/exp)':<15} {'Delta bhav'}")
guard_mismatches = 0
for i, (period, (exp_lord, exp_bhav, _exp_end)) in enumerate(zip(mudda_mismatched, sulabh["expected"]), 1):
    got_bhav = period["bhav"]
    delta_bhav = got_bhav - exp_bhav
    flag = "" if delta_bhav == -1 else "  <-- expected uniform -1 shift"
    if delta_bhav != -1:
        guard_mismatches += 1
    print(f"{i:<2} {period['lord']:<10} {got_bhav}/{exp_bhav:<13} {delta_bhav}{flag}")

if guard_mismatches == 0:
    print("PASS: bhav output reverted to pre-fix uniform -1 shift (9/9) -- guard "
          "correctly rejects mismatched-year AstroSage data.")
else:
    print(f"BUG: {guard_mismatches}/9 periods did not show the expected uniform -1 "
          f"shift -- mismatched-year AstroSage data may be silently accepted.")
