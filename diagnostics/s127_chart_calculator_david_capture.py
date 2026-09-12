"""
S127 characterization capture: calculate_chart() public output for David
(the hardest reference chart), captured verbatim for human review before
any regression test is authored.

READ-ONLY probe -- no production file is modified. Reuses the exact
fixture-backed Nominatim stub from tests/conftest.py (same fixture file,
same monkeypatch seam: agent.chart_calculator.Nominatim) so no live
network geocoding call is made and the captured values are reproducible.

David's canonical birth input source: tests/test_chart_calculator.py
_MUNTHA_FIXTURES entry -- "David", "19 Jan 1976", "22:00", "London, UK"
(also cross-referenced in CLAUDE.md's Reference Materials section).
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

import agent.chart_calculator as chart_calculator
from geopy.location import Location

_FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "geocoded_locations.json"
_GEOCODED_LOCATIONS = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


class _FakeNominatim:
    """Same fixture-backed stub as tests/conftest.py's _patch_geocoder."""

    def __init__(self, *args, **kwargs):
        pass

    def geocode(self, query, *, exactly_one=True, timeout=None, **kwargs):
        try:
            data = _GEOCODED_LOCATIONS[query]
        except KeyError:
            raise KeyError(
                f"'{query}' is not in tests/fixtures/geocoded_locations.json."
            ) from None
        location = Location(
            data["address"], (data["latitude"], data["longitude"], 0), data["raw"]
        )
        return location if exactly_one else [location]


# David's canonical input -- verbatim from tests/test_chart_calculator.py
# _MUNTHA_FIXTURES, NOT invented here.
DAVID_INPUT = {
    "name": "David",
    "dob": "19 Jan 1976",
    "tob": "22:00",
    "place": "London, UK",
}

OUT_PATH = REPO_ROOT / "diagnostics" / "latest_run.md"


def main() -> None:
    original_nominatim = chart_calculator.Nominatim
    chart_calculator.Nominatim = _FakeNominatim
    try:
        chart = chart_calculator.calculate_chart(**DAVID_INPUT)
    except Exception as exc:
        error_report = (
            f"# S127 -- calculate_chart() capture FAILED for David\n\n"
            f"Captured at: {datetime.now(timezone.utc).isoformat()}\n\n"
            f"Input: {json.dumps(DAVID_INPUT, indent=2)}\n\n"
            f"Exception: {type(exc).__name__}: {exc}\n"
        )
        OUT_PATH.write_text(error_report, encoding="utf-8")
        raise RuntimeError(
            f"calculate_chart() failed for David's fixture input {DAVID_INPUT!r}: {exc}"
        ) from exc
    finally:
        chart_calculator.Nominatim = original_nominatim

    planetary_positions = chart["planetary_positions"]
    observed_keys_per_planet = {
        planet: sorted(d.keys()) for planet, d in planetary_positions.items()
    }
    all_same_shape = len(set(tuple(v) for v in observed_keys_per_planet.values())) == 1
    no_longitude_leak = all(
        "longitude" not in d for d in planetary_positions.values()
    )

    report_lines = [
        "# S127 -- calculate_chart() characterization capture: David",
        "",
        f"Captured at: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Input (verbatim from tests/test_chart_calculator.py _MUNTHA_FIXTURES)",
        "",
        "```json",
        json.dumps(DAVID_INPUT, indent=2),
        "```",
        "",
        "## Shape check (informational only -- no assertions made)",
        "",
        f"- All 9 planet dicts share identical key set: {all_same_shape}",
        f"- Per-planet keys observed: {sorted(next(iter(observed_keys_per_planet.values())))}"
        if all_same_shape else f"- Per-planet keys observed (MIXED): {observed_keys_per_planet}",
        f"- 'longitude' absent from every planet dict (public contract): {no_longitude_leak}",
        f"- Number of planets returned: {len(planetary_positions)}",
        f"- lagna_chart present: {'lagna_chart' in chart}",
        "",
        "## Full calculate_chart() return value, verbatim",
        "",
        "```python",
        repr(chart),
        "```",
        "",
        "---",
        "",
        "AWAITING HUMAN REVIEW of golden values before locking regression test.",
        "",
    ]
    OUT_PATH.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"Wrote capture to {OUT_PATH}")
    print("AWAITING HUMAN REVIEW of golden values before locking regression test.")


if __name__ == "__main__":
    main()
