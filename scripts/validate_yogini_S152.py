"""S152 oracle harness -- print the computed Yogini Mahadasha sequence for
eyeballing against each reference chart's AstroSage "Yogini Dasha" table.

** THIS IS THE GATE, NOT A FORMALITY ** -- the Yogini engine's starting-index
formula `(nakshatra_number + 2) % 8` is oracle-validated on ONLY ONE reference
chart (Sulabh); Surbhi / Sheridan / David are PENDING (see dashas/yogini.py and
yogini_facts' caveat). This harness is how that gets closed. Run it for all 4
charts and compare the first few MDs' LORD + begin/end dates to AstroSage's
Yogini table:
  - match on all 4  -> the formula generalises; Yogini is safe to trust / commit.
  - any mismatch    -> the formula does NOT generalise. Do NOT commit the wiring
                       as a live fact; it is an ENGINE fix in dashas/yogini.py
                       (likely the starting-index formula), never a wiring change.

RUN (on a machine with swisseph + the reference charts), e.g. in a REPL:

    from agent.chart_calculator import calculate_chart
    from scripts.validate_yogini_S152 import report_from_chart
    print(report_from_chart(calculate_chart(...), "Sulabh"))   # repeat for all 4

Note: unlike the friendship harness, this imports the Yogini engine, so it needs
swisseph available (calculate_chart does too).

Python 3.11.
"""
from __future__ import annotations

import datetime as _dt

from agent.astro.yogini_facts import build_yogini_facts


def format_yogini(yog: dict, *, max_rows: int = 12) -> str:
    """Render a yogini fact dict (build_yogini_facts output) as a dated table."""
    mds = (yog or {}).get("mahadashas") or []
    if not mds:
        return "(no Yogini facts -- engine returned {}; check Moon longitude / birth jd_ut)"
    today = _dt.date.today().isoformat()
    out = ["  #  Lord      Yogini      Begin        End          Phase",
           "  -- --------- ----------- ------------ ------------ -------"]
    for i, m in enumerate(mds[:max_rows], 1):
        if m["end"] < today:
            ph = "past"
        elif m["start"] <= today < m["end"]:
            ph = "CURRENT"
        else:
            ph = "future"
        out.append(f"  {i:>2} {m['lord']:<9} {m['yogini']:<11} "
                   f"{m['start']:<12} {m['end']:<12} {ph}")
    if len(mds) > max_rows:
        out.append(f"  ... ({len(mds) - max_rows} more periods)")
    return "\n".join(out)


def report_from_chart(chart: dict, label: str = "") -> str:
    """Compute Yogini MDs for `chart` (calculate_chart output) and format them."""
    head = f"=== Yogini Mahadasha -- {label} ===" if label else "=== Yogini Mahadasha ==="
    return head + "\n" + format_yogini(build_yogini_facts(chart))


if __name__ == "__main__":  # pragma: no cover
    print(__doc__)
