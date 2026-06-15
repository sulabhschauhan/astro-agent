"""
muntha_check.py
Standalone (non-pytest) manual check for calculate_muntha().

Sulabh, 2026 Varshaphal:
  - natal Lagna = Sagittarius (index 8), age = 2026 - 1988 = 38
    -> muntha_sign = SIGNS[(8 + 38) % 12] = SIGNS[10] = Aquarius
  - Varshaphal Lagna = Libra (our computed result; AstroSage = Virgo --
    see playbook_export/decisions/ayanamsa-investigation.md, "Muntha
    design implication"), lagna_boundary_sensitive = True
  - bhav_primary (vs Libra)  = ((10 - 6) % 12) + 1 = 5
  - bhav_alternate (vs Virgo, the previous sign, since
    lagna_degree_in_sign < 15) = ((10 - 5) % 12) + 1 = 6

AstroSage's published Muntha = 6th bhav corresponds to bhav_alternate here
-- expected outcome, not a mismatch to chase (documented Libra/Virgo Lagna
boundary case).

Run from the repo root:
    python tests/manual/muntha_check.py
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
failures: list[str] = []

print("Sulabh (Calcutta, India, 6 April 1988) -- Muntha check")
print(f"Target year: {TARGET_YEAR}\n")

try:
    natal = calculate_chart("Sulabh", "6 April 1988", "00:30:00", "Calcutta, India")
    varshaphal = build_varshaphal_chart(natal, TARGET_YEAR)
    muntha = calculate_muntha(natal, varshaphal, TARGET_YEAR)
except (ValueError, RuntimeError) as exc:
    print(f"FAIL: setup raised: {exc}")
    sys.exit(1)

print(f"  natal Lagna: {natal['lagna_chart']['ascendant']}")
print(f"  varshaphal Lagna: {varshaphal['lagna']} "
      f"(degree_in_sign={varshaphal['lagna_degree_in_sign']}, "
      f"boundary_sensitive={varshaphal['lagna_boundary_sensitive']})")
print(f"  muntha: {muntha}\n")

checks = [
    ("muntha_sign", muntha.get("muntha_sign"), "Aquarius"),
    ("bhav_primary", muntha.get("bhav_primary"), 5),
    ("bhav_alternate", muntha.get("bhav_alternate"), 6),
    ("ambiguous", muntha.get("ambiguous"), True),
]
for label, got, expected in checks:
    status = "PASS" if got == expected else "FAIL"
    print(f"  {status}: {label} = {got} (expected {expected})")
    if status == "FAIL":
        failures.append(label)

print()
if failures:
    print(f"{len(failures)} check(s) failed: {failures}")
    sys.exit(1)
print("All checks passed.")
