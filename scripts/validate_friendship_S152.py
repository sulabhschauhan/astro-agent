"""S152 oracle harness -- pretty-print computed Pancha-dha maitri for eyeballing
against each reference chart's AstroSage "Friendship Table".

WHY A HARNESS, NOT A TEST: doctrinal correctness of the friendship engine is a
human eyeball check against AstroSage (the oracle), per the 4-reference-chart
protocol -- not a byte assertion. The pytest suite pins the adapter's SHAPE and
its consistency with the engine; THIS proves the engine's VALUES are right.

RUN (on a machine with swisseph + the reference charts), e.g. in a REPL:

    from agent.chart_calculator import calculate_chart
    from scripts.validate_friendship_S152 import report_from_chart
    chart = calculate_chart(...)                 # one reference chart
    print(report_from_chart(chart, "Sulabh"))

Do this for all 4 reference charts (Sulabh, Surbhi, Sheridan, David) and compare
each printed grid to that chart's AstroSage Friendship / Pancha-dha Maitri table.
A mismatch is an ENGINE bug to fix in core/friendship.py -- never a reason to
edit the wiring. Match on all 4 => friendship is validated and safe to trust in
the live reading.

This module imports only the pure friendship adapter (no swisseph), so it loads
anywhere; calculate_chart (which you call to build `chart`) is what needs swisseph.

Python 3.11.
"""
from __future__ import annotations

from agent.astro.friendship_facts import (
    build_friendship_facts, SEVEN_CLASSICAL, COMPOUND_ORDER,
)

_ABBR = {"Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
         "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa"}
# compact cell codes mirroring how tables print the five-fold relation
_CODE = {"Adhimitra": "AF", "Mitra": "F", "Sama": "N", "Satru": "E", "Adhisatru": "AE"}
_LEGEND = "AF=Adhimitra(great friend)  F=Mitra(friend)  N=Sama(neutral)  " \
          "E=Satru(enemy)  AE=Adhisatru(bitter enemy)"


def format_friendship(fr: dict) -> str:
    """Render a friendship fact dict (build_friendship_facts output) as a grid."""
    if not fr or not fr.get("compound"):
        return "(no friendship facts -- engine returned {}; check planet signs)"
    signs = fr.get("signs") or {}
    comp = fr["compound"]
    out = [_LEGEND, ""]
    header = "toward->   " + "  ".join(f"{_ABBR[p]:>2}" for p in SEVEN_CLASSICAL)
    out.append(header)
    for a in SEVEN_CLASSICAL:
        row = [f"{_ABBR[a]} ({signs.get(a, '?')[:3]})".ljust(10)]
        for b in SEVEN_CLASSICAL:
            row.append(f"{'--' if a == b else _CODE[comp[a][b]]:>2}")
        out.append("  ".join(row))
    # explicit per-planet summary, matching the fact-block render
    out.append("")
    gloss = {"Adhimitra": "great friend", "Mitra": "friend", "Sama": "neutral",
             "Satru": "enemy", "Adhisatru": "bitter enemy"}
    bp = fr.get("by_planet") or {}
    for a in SEVEN_CLASSICAL:
        b = bp.get(a) or {}
        parts = [f"{gloss[lab]}: {', '.join(b[lab])}"
                 for lab in COMPOUND_ORDER if b.get(lab)]
        out.append(f"  {a} (in {signs.get(a, '?')}) -- " + "; ".join(parts))
    return "\n".join(out)


def report_from_chart(chart: dict, label: str = "") -> str:
    """Compute friendship for `chart` (calculate_chart output) and format it."""
    head = f"=== Pancha-dha maitri -- {label} ===" if label else "=== Pancha-dha maitri ==="
    return head + "\n" + format_friendship(build_friendship_facts(chart))


if __name__ == "__main__":  # pragma: no cover
    print(__doc__)
