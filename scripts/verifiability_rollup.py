"""Standing verifiability roll-up (S140, Tier 2 instrument).

Reads every qa_capture, extracts each turn's silence-gate stats fail-safe, and
prints the standing first-class / second-class ledger + the P-033 promotion gate
(`caught_miss / typed_silences`) + the second-class backlog. No pipeline call,
no LLM. Nothing here has drop authority -- it is the early-warning a human reads.

Usage:  python scripts/verifiability_rollup.py [qa_capture_dir]
"""
import sys, os, glob, json, re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.astro import verifiability as V

_FENCE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def ledger_blocks(md: str) -> list[dict]:
    """Canonical `### verifiability (S140)` ledger blocks (S140 wiring onward),
    identified by the `ledger_version` key. Used as-is; no re-derivation."""
    out = []
    for m in _FENCE.finditer(md):
        raw = m.group(1)
        if '"ledger_version"' not in raw:
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "ledger_version" in obj:
            out.append(obj)
    return out


def gate_blocks(md: str) -> list[dict]:
    """Every fenced JSON object in the capture that is a silence-gate stats dict.

    Identified by the unambiguous top-level marker `silences_in`. Robust to the
    era variance (pre-S137 blocks lack `predicate_coverage`; they still parse and
    summarize, reporting an unknown claim ledger). A block that does not parse is
    skipped, never guessed.
    """
    out = []
    for m in _FENCE.finditer(md):
        raw = m.group(1)
        if '"silences_in"' not in raw and '"claims_in"' not in raw:
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        # The capture renders the whole GateResult; the ledger fields live under
        # its `stats` subkey. Descend when present, else the object IS the stats.
        stats = obj.get("stats") if isinstance(obj.get("stats"), dict) else obj
        if "silences_in" in stats or "claims_in" in stats:
            out.append(stats)
    return out


def main(argv):
    cap_dir = argv[1] if len(argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "diagnostics", "qa_capture")
    files = sorted(glob.glob(os.path.join(cap_dir, "*.md")))
    ledgers = []
    per_capture = []
    for f in files:
        md = open(f, encoding="utf-8").read()
        # Prefer the canonical ledger block (S140 wiring); fall back to deriving
        # it from the raw gate stats for pre-wiring captures. Never both, so a
        # future capture carrying both blocks is not double-counted.
        canon = ledger_blocks(md)
        if canon:
            ledgers.extend(canon)
            n = len(canon)
        else:
            stats = gate_blocks(md)
            ledgers.extend(V.summarize(s) for s in stats)
            n = len(stats)
        per_capture.append((os.path.basename(f), n))

    agg = V.rollup(ledgers)
    r = agg["rates"]

    print("# Verifiability roll-up (S140)  ledger v%d" % V.LEDGER_VERSION)
    print("captures scanned: %d   turns with a gate ledger: %d "
          "(claims-known %d, claims-unknown/old %d)\n"
          % (len(files), agg["turns"], agg["turns_claims_known"], agg["turns_claims_unknown"]))
    print("CLAIMS (known turns): total=%d  first-class(predicate-decided)=%d  second-class(unevaluable)=%d"
          % (agg["claims_total"], agg["first_class"], agg["second_class"]))
    print("  first_class_pct = %s   typed_share_pct = %s" % (r["first_class_pct"], r["typed_share_pct"]))
    print("SILENCES: in=%d typed=%d caught_miss=%d justified=%d uncheckable=%d fragile_downgraded=%d"
          % (agg["sil_in"], agg["sil_typed"], agg["sil_caught_miss"],
             agg["sil_justified"], agg["sil_uncheckable"], agg["sil_fragile"]))
    print("\nP-033 PROMOTION GATE (measured, no drop authority):")
    print("  caught_miss / typed_silences = %d / %d = %s%%"
          % (agg["sil_caught_miss"], agg["sil_typed"], r["caught_miss_rate_pct"]))
    print("SECOND-CLASS BACKLOG (coverage targets): unevaluable_claims=%d + uncheckable_silences=%d"
          % (agg["second_class"], agg["sil_uncheckable"]))
    print("  uncheckable_rate = %s%%" % r["uncheckable_rate_pct"])
    print("\nper-capture ledger-turns:")
    for name, n in per_capture:
        print("  %-24s %d" % (name, n))
    return agg


if __name__ == "__main__":
    main(sys.argv)
