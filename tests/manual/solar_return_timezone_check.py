"""
solar_return_timezone_check.py
Standalone (non-pytest) manual check for Task B2: resolve_timezone_offset()
wired into calculate_solar_return()'s local_datetime (and, by inheritance,
build_varshaphal_chart()'s epoch.local_datetime), replacing the hardcoded
IST offset for these display fields.

HARDEST CASE — Sheridan (Durban, South Africa; 27 May 1984, 08:00:00,
29degS 31degE, UTC+2 -- see playbook_export/reference/reference_charts.md
Chart 3):
  - calculate_solar_return(target_year=2026).local_datetime must show a
    UTC+2 offset (~2:2X local, given the documented ~10min epoch drift —
    see calculate_solar_return's CROSS-EPHEMERIS NOTE), NOT the old
    hardcoded +5.5 — a 3.5-hour discriminator.
  - build_varshaphal_chart(target_year=2026): confirm Lagna=Pisces,
    Rasi=Libra against reference_charts.md (unchanged from before B2 —
    confirmation, not a new result).

Run from the repo root:
    python tests/manual/solar_return_timezone_check.py
"""

import sys
from datetime import timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.chart_calculator import (
    build_varshaphal_chart,
    calculate_chart,
    calculate_solar_return,
)

TARGET_YEAR = 2026
failures: list[str] = []

print("Sheridan (Durban, South Africa, 27 May 1984, 08:00:00) — Task B2 check")
print(f"Target year: {TARGET_YEAR}\n")

try:
    natal = calculate_chart("Sheridan", "27 May 1984", "08:00:00", "Durban, South Africa")
except (ValueError, RuntimeError) as exc:
    print(f"FAIL: calculate_chart raised: {exc}")
    sys.exit(1)

print(f"  birth_details lat/lon: {natal['birth_details']['lat']}, "
      f"{natal['birth_details']['lon']}")

try:
    epoch = calculate_solar_return(natal, TARGET_YEAR)
except RuntimeError as exc:
    print(f"FAIL: calculate_solar_return raised: {exc}")
    sys.exit(1)

local_dt = epoch["local_datetime"]
offset = local_dt.utcoffset()
offset_hours = offset.total_seconds() / 3600.0

print(f"  utc_datetime:   {epoch['utc_datetime']}")
print(f"  local_datetime: {local_dt}")
print(f"  local UTC offset: {offset_hours:+.2f}h")

if offset_hours == 2.0:
    print("  PASS: local_datetime offset is UTC+2.0 (Africa/Johannesburg, SAST)")
else:
    print(f"  FAIL: expected UTC+2.0, got UTC{offset_hours:+.2f}")
    failures.append("local_datetime offset")

if local_dt.hour in (2, 3) and local_dt.day in (27, 28) and local_dt.month == 5:
    print(f"  PASS: local_datetime ~2:2X on 27/28 May (got {local_dt.strftime('%d %b %H:%M:%S')})")
else:
    print(f"  FAIL: local_datetime not ~2:2X on 27/28 May "
          f"(got {local_dt.strftime('%d %b %H:%M:%S')})")
    failures.append("local_datetime value")

# Old hardcoded IST (+5.5) would have produced a wall-clock time 3.5h later.
old_ist_equiv = epoch["utc_datetime"].astimezone(timezone(timedelta(hours=5.5)))
print(f"  (for reference, old hardcoded +5.5 IST display would have shown: "
      f"{old_ist_equiv.strftime('%d %b %H:%M:%S')})")

print()
print(f"build_varshaphal_chart({TARGET_YEAR}) — Lagna/Rasi confirmation")

try:
    varshaphal = build_varshaphal_chart(natal, TARGET_YEAR)
except RuntimeError as exc:
    print(f"FAIL: build_varshaphal_chart raised: {exc}")
    sys.exit(1)

checks = [
    ("Lagna", varshaphal["lagna"], "Pisces"),
    ("Rasi", varshaphal["rasi"], "Libra"),
]
for label, got, expected in checks:
    status = "PASS" if got == expected else "FAIL"
    print(f"  {status}: {label} = {got} (expected {expected})")
    if status == "FAIL":
        failures.append(f"varshaphal {label}")

# epoch.local_datetime inherited via build_varshaphal_chart's pass-through
vs_local = varshaphal["epoch"]["local_datetime"]
vs_offset_hours = vs_local.utcoffset().total_seconds() / 3600.0
status = "PASS" if vs_offset_hours == 2.0 else "FAIL"
print(f"  {status}: varshaphal epoch.local_datetime offset = UTC{vs_offset_hours:+.2f} "
      f"(expected UTC+2.0)")
if status == "FAIL":
    failures.append("varshaphal epoch.local_datetime offset")

print()
if failures:
    print(f"{len(failures)} check(s) failed: {failures}")
    sys.exit(1)
print("All checks passed.")
