"""
tests/test_chart_calculator.py
Pytest tests for chart_calculator.py Varshaphal helpers:
  resolve_house_counting_lagna, calculate_mudda_dasha, calculate_muntha.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.chart_calculator import (
    build_varshaphal_chart,
    calculate_chart,
    calculate_muntha,
)

_TARGET_YEAR = 2026

# (name, dob, tob, place, astrosage_parsed_data,
#  exp_resolved_bhav, exp_bhav_source, exp_bhav_boundary_sensitive)
_MUNTHA_FIXTURES = [
    (
        "Sulabh", "6 April 1988", "00:30", "Calcutta, India",
        {"varshaphal_lagna": "Virgo", "varsha_year": 2026},
        6, "astrosage", False,
    ),
    (
        "Surbhi", "11 Sep 1992", "10:30", "Patna, India",
        None,
        2, "computed", True,
    ),
    (
        "Sheridan", "27 May 1984", "08:00", "Durban, South Africa",
        {"varshaphal_lagna": "Pisces", "varsha_year": 2026},
        9, "astrosage", False,
    ),
    (
        "David", "19 Jan 1976", "22:00", "London, UK",
        {"varshaphal_lagna": "Cancer", "varsha_year": 2026},
        5, "astrosage", False,
    ),
]


def test_calculate_muntha_astrosage_path():
    """
    For all 4 reference charts, verify calculate_muntha()'s three new
    resolved-Lagna fields (resolved_bhav, bhav_source, bhav_boundary_sensitive)
    match AstroSage's published Muntha bhav, and that the three pre-existing
    legacy fields (muntha_sign, bhav_primary, ambiguous / optional bhav_alternate)
    are present and identical to a baseline call without astrosage_parsed_data
    (no regression).
    """
    failures: list[str] = []

    for name, dob, tob, place, apd, exp_rbhav, exp_source, exp_bs in _MUNTHA_FIXTURES:
        natal = calculate_chart(name, dob, tob, place)
        varshaphal = build_varshaphal_chart(natal, _TARGET_YEAR)

        result   = calculate_muntha(natal, varshaphal, _TARGET_YEAR, apd)
        baseline = calculate_muntha(natal, varshaphal, _TARGET_YEAR)

        # --- new fields ---
        if result.get("resolved_bhav") != exp_rbhav:
            failures.append(
                f"{name}: resolved_bhav={result.get('resolved_bhav')!r} != {exp_rbhav!r}"
            )
        if result.get("bhav_source") != exp_source:
            failures.append(
                f"{name}: bhav_source={result.get('bhav_source')!r} != {exp_source!r}"
            )
        if result.get("bhav_boundary_sensitive") != exp_bs:
            failures.append(
                f"{name}: bhav_boundary_sensitive={result.get('bhav_boundary_sensitive')!r} != {exp_bs!r}"
            )

        # --- legacy fields unchanged ---
        for key in ("muntha_sign", "bhav_primary", "ambiguous"):
            if result.get(key) != baseline.get(key):
                failures.append(
                    f"{name}: legacy '{key}' changed: {result.get(key)!r} != {baseline.get(key)!r}"
                )
        # bhav_alternate: presence and value must match baseline
        baseline_has_alt = "bhav_alternate" in baseline
        result_has_alt   = "bhav_alternate" in result
        if baseline_has_alt != result_has_alt:
            failures.append(
                f"{name}: 'bhav_alternate' presence changed "
                f"(baseline={baseline_has_alt}, result={result_has_alt})"
            )
        elif baseline_has_alt and result["bhav_alternate"] != baseline["bhav_alternate"]:
            failures.append(
                f"{name}: legacy 'bhav_alternate' changed: "
                f"{result['bhav_alternate']!r} != {baseline['bhav_alternate']!r}"
            )

    assert not failures, "calculate_muntha astrosage_path failures:\n" + "\n".join(failures)
