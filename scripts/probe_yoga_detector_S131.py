"""
Yoga detector probe (S131). ZERO API cost -- pure arithmetic over a fact block.

DECISION THIS SERVES: if the detector reproduces the desktop-benchmark answer's
yoga rulings for Sulabh's chart -- FIRED and RULED-OUT alike -- the catalogue is
sound enough to wire into the fact block; if any ruling disagrees, it is not.
TOKEN CEILING: none -- no model call is made.

THE ORACLE. `Output.txt` (the Claude-desktop benchmark answer for this same
chart) names six rulings. They are asserted below as expectations, so a future
change to the catalogue that breaks one fails loudly:

    Dharma-Karmadhipati   FIRED      9th lord Sun + 10th lord Mercury, both 4th
    Sarala (VRY)          FIRED      8th lord Moon in the 12th
    1st/4th-5th link      FIRED      Mars (5th lord) aspects Jupiter
    Harsha (VRY)          RULED OUT  6th lord Venus in the 6th, not 8th/12th
    Vimala (VRY)          RULED OUT  12th lord Mars in the 2nd
    Gajakesari            RULED OUT  Moon 12th, Jupiter 5th -- 6 apart

Neecha Bhanga is NOT covered here: it needs dignity, the dispositor and D9,
and lives in its own catalogue module.

    python -m scripts.probe_yoga_detector_S131 [capture.md]

Python 3.11.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent.calculations.yogas.detector import detect_yogas  # noqa: E402

CAPTURE_DIR = REPO_ROOT / "diagnostics" / "qa_capture"

# rule id -> expected `fired`, from Output.txt. See the module docstring.
EXPECTED = {
    "dharma_karmadhipati": True,
    "sarala_yoga": True,
    "kendra_trikona_4_5": True,
    "harsha_yoga": False,
    "vimala_yoga": False,
    "gajakesari_yoga": False,
}


def chart_facts_from(path: Path) -> dict:
    body = path.read_text(encoding="utf-8")
    m = re.search(r"### chart_facts\n```json\n(.*?)\n```",
                  body.split("## TURN ")[1], re.S)
    if not m:
        raise SystemExit(f"no chart_facts block in {path.name}")
    return json.loads(m.group(1))


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    path = Path(argv[0]) if argv else sorted(CAPTURE_DIR.glob("*.md"))[-1]
    facts = chart_facts_from(path)

    report = detect_yogas(facts)
    print(f"capture: {path.name}   detector: {report.detector_version}")
    if report.errors:
        print("ERRORS:", report.errors)

    print(f"\nFIRED ({len(report.fired)}):")
    for v in report.fired:
        print(f"  {v.name}\n      {v.reason}")
    print(f"\nRULED OUT ({len(report.ruled_out)}):")
    for v in report.ruled_out:
        print(f"  {v.name}\n      {v.reason}")

    print("\nAgainst the Output.txt benchmark:")
    got = {v.id: v.fired for v in report.verdicts}
    ok = True
    for rid, want in EXPECTED.items():
        have = got.get(rid)
        mark = "OK " if have == want else "MISMATCH"
        if have != want:
            ok = False
        print(f"  [{mark}] {rid:22s} expected fired={want}  got={have}")

    print("\nRESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
