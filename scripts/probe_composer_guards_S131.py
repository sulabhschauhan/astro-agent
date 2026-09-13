"""
Composer guard probe (S131) -- proves Stage 5b's checks fire, at ZERO API cost.

DECISION THIS SERVES: if the enforcing check catches an invented chart fact and
the coverage check restores a silently dropped claim, the composer is safe to
put in front of a real model; else it is not.
TOKEN CEILING: none -- no model call is made. The composer LLM is stubbed.

Real captured claims + a deliberately misbehaving stub composer. Run:

    python -m scripts.probe_composer_guards_S131 [capture.md]

Defaults to the newest file in diagnostics/qa_capture/.

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

from agent.astro import composer, silence_gate as SG  # noqa: E402

CAPTURE_DIR = REPO_ROOT / "diagnostics" / "qa_capture"


def load_turns(path: Path) -> list[tuple[str, SG.GateResult]]:
    """Rebuild a GateResult per turn from a stored capture.

    The capture keeps kept_claims and, in `stats.advisory_detail`, each
    claim's ENFORCED verdict -- enough to reconstruct the verdict list the
    composer reads. The join is positional (advisory_detail is written in
    claim order), not on the truncated statement key.
    """
    body = path.read_text(encoding="utf-8")
    turns: list[tuple[str, SG.GateResult]] = []
    for chunk in body.split("## TURN ")[1:]:
        q = re.search(r"### question\n```\n(.*?)\n```", chunk, re.S)
        g = re.search(r"### silence gate \(Stage 5a\)\n```json\n(.*?)\n```",
                      chunk, re.S)
        if not (q and g):
            continue
        gate_json = json.loads(g.group(1))
        kept = gate_json.get("kept_claims") or []
        detail = (gate_json.get("stats") or {}).get("advisory_detail") or []
        verdicts = [
            SG.ClaimVerdict(
                statement=c.get("statement", ""),
                segment_ids=list(c.get("segment_ids") or []),
                verdict=(detail[i].get("enforced_verdict") if i < len(detail)
                         else SG.UNDETERMINED),
                reason="reconstructed from capture")
            for i, c in enumerate(kept)]
        turns.append((q.group(1).strip(), SG.GateResult(
            kept_claims=kept,
            dropped_claims=gate_json.get("dropped_claims") or [],
            verdicts=verdicts,
            silent_on=gate_json.get("silent_on") or [],
            stats=gate_json.get("stats") or {})))
    return turns


def _stub(*, invent_on=None, uncondition_on=None, omit=None):
    """A composer that misbehaves exactly where asked to."""
    def _llm(system: str, user: str, **_):
        claims = json.loads(user)["claims"]
        blocks = [{"type": "lead", "text": "Here is the short version."}]
        for c in claims:
            cid = c["claim_id"]
            if cid == omit:
                continue
            text = f"Plain rewrite of claim {cid}."
            if cid == invent_on:
                text = "Your Saturn in Aquarius makes this strong."
            if cid == uncondition_on:
                text = "You will overcome obstacles and win."
            blocks.append({"type": "claim", "claim_id": cid, "text": text})
        return json.dumps({"blocks": blocks, "demoted": []}), {"stub": True}
    return _llm


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if argv:
        path = Path(argv[0])
    else:
        caps = sorted(CAPTURE_DIR.glob("*.md"))
        if not caps:
            print(f"no captures in {CAPTURE_DIR}")
            return 2
        path = caps[-1]

    turns = load_turns(path)
    print(f"capture: {path.name}   turns: {len(turns)}")
    if not turns:
        return 2

    for q, gate in turns:
        rows = composer._claim_rows(gate)
        checked = sum(1 for r in rows if r["checked"])
        print(f"  Q: {q[:58]:58s} claims={len(rows)} verified={checked}")

    q, gate = turns[0]
    ok = True

    r = composer.compose(q, gate, llm=_stub())
    print(f"\n[1] clean run            composed={r['composed']} "
          f"rendered={r['claims_rendered']} violations={len(r['violations'])}")
    ok &= r["composed"] and not r["violations"]

    r = composer.compose(q, gate, llm=_stub(invent_on=0))
    fell_back = next(b for b in r["blocks"] if b.get("claim_id") == 0)["text"]
    caught = bool(r["violations"])
    print(f"[2] invented chart fact  caught={caught} "
          f"reverted_to_original={fell_back == gate.verdicts[0].statement}")
    if caught:
        print(f"    -> {r['violations'][0]['why']}")
    ok &= caught and fell_back == gate.verdicts[0].statement

    cond = next((i for i, v in enumerate(gate.verdicts)
                 if composer._is_conditional(v.statement)), None)
    if cond is not None:
        r = composer.compose(q, gate, llm=_stub(uncondition_on=cond))
        flagged = any(a["claim_id"] == cond for a in r["condition_advisory"])
        print(f"[3] condition dropped    advisory_flagged={flagged} "
              f"enforced={bool(r['violations'])}  (advisory by design)")
        ok &= flagged and not r["violations"]

    r = composer.compose(q, gate, llm=_stub(omit=1))
    print(f"[4] claim silently cut   restored={r['unaccounted_restored']} "
          f"rendered={r['claims_rendered']}/{r['claims_in']}")
    ok &= r["unaccounted_restored"] == [1]

    r = composer.compose(q, gate, llm=lambda s, u, **k: ("not json", {}))
    print(f"[5] model returns junk   composed={r['composed']} "
          f"(caller falls back to the existing renderer)")
    ok &= r["composed"] is False

    print("\nRESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
