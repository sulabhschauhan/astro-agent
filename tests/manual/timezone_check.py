"""
timezone_check.py
Standalone (non-pytest) manual check for resolve_timezone_offset().

Validates IANA-timezone resolution (timezonefinder) + historical/DST-aware
UTC-offset lookup (zoneinfo) against known cases from
playbook_export/reference/reference_charts.md:
  - London   (Chart 4, David):    19 Jan 1976 / 19 Jan 2026 -> 0.0
  - Durban   (Chart 3, Sheridan): 27 May 1984 / 28 May 2026 -> 2.0
  - Calcutta (Chart 1, Sulabh) / Patna (Chart 2, Surbhi)    -> 5.5

Run from the repo root:
    python tests/manual/timezone_check.py
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.chart_calculator import resolve_timezone_offset

# (label, lat, lon, naive local datetime, expected UTC offset hours)
CASES = [
    ("London 1976-01-19 (Chart 4, David)",
     51.5, -0.1167, datetime(1976, 1, 19, 22, 0, 0), 0.0),
    ("London 2026-01-19 (Chart 4 Varshaphal epoch)",
     51.5, -0.1167, datetime(2026, 1, 19, 17, 38, 20), 0.0),
    ("Durban 1984-05-27 (Chart 3, Sheridan)",
     -29.85, 31.0167, datetime(1984, 5, 27, 8, 0, 0), 2.0),
    ("Durban 2026-05-28 (Chart 3 Varshaphal epoch)",
     -29.85, 31.0167, datetime(2026, 5, 28, 2, 25, 0), 2.0),
    ("Calcutta 1988-04-06 (Chart 1, Sulabh)",
     22.5726, 88.3639, datetime(1988, 4, 6, 0, 30, 0), 5.5),
    ("Patna 1992-09-11 (Chart 2, Surbhi)",
     25.6, 85.1167, datetime(1992, 9, 11, 10, 30, 0), 5.5),
]

if __name__ == "__main__":
    failures = []
    for label, lat, lon, dt, expected in CASES:
        try:
            offset = resolve_timezone_offset(lat, lon, dt)
        except ValueError as exc:
            print(f"FAIL  {label}: {exc}")
            failures.append(label)
            continue
        status = "PASS" if offset == expected else "FAIL"
        print(f"{status}  {label}: got {offset:+.2f}, expected {expected:+.2f}")
        if status == "FAIL":
            failures.append(label)

    if failures:
        print(f"\n{len(failures)}/{len(CASES)} cases failed: {failures}")
        sys.exit(1)
    print(f"\nAll {len(CASES)} cases passed.")
