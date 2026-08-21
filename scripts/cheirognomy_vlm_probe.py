"""
scripts/cheirognomy_vlm_probe.py

Live probe of agent/cheirognomy/vlm_arm.py on two real hand images.

SPENDS REAL API: 2 gate calls + 6 GPT-4o vision calls total. Two images only, no
scaling. Hardest-first order: right hand, then left.

Runs the module's PUBLIC API as authored -- `classify_hand` / `compare_hands`.
No classify or derive logic is reimplemented here; everything below the call is
formatting and read-only analysis of the returned objects.

CALL BUDGET NOTE: `classify_hand` already performs the gate itself via
`palm_processor.validate_palm_image` and returns a quality_flag result WITHOUT
making any classify call when the gate hard-rejects -- i.e. the "gate once, skip
the 3 runs if rejected" step is already the authored behaviour. Calling the gate
again here would have made 4 gate calls, not 2, so the probe does not pre-gate.

Writes diagnostics/latest_run.md (OVERWRITE, per the diagnostics convention).
The report is written in a `finally` block so spent API calls are never lost to a
formatting error.
"""

import sys
import time
import traceback
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from agent.cheirognomy.vlm_arm import (  # noqa: E402
    _DOMINANCE_FLOOR,
    _DOMINANCE_MARGIN,
    _FINGER_CONSENSUS_MIN,
    _HAND_PRIMITIVES,
    _N_RUNS,
    _TEMPERATURE,
    _flatten,
    classify_hand,
    compare_hands,
    load_doctrine,
)

REPORT_PATH = _REPO_ROOT / "diagnostics" / "latest_run.md"

# Hardest-first: the right hand is the primary capture and the harder read.
IMAGES = [
    ("right", _REPO_ROOT / "data" / "test_images" / "palm_right_test.jpg"),
    ("left", _REPO_ROOT / "data" / "test_images" / "palm_left_test.jpg"),
]

doc = load_doctrine()

lines = []
w = lines.append
results = {}
errors = {}


def fmt(v):
    return f"`{v}`" if v is not None else "_dropped_"


def types_declaring(slot, value):
    """Which S2 types declare `value` in `slot`. Read-only lookup, not derive logic."""
    if value is None:
        return []
    return sorted(n for n, tc in doc.types.items() if tc.criteria.get(slot) == value)


# =============================================================================
# Run
# =============================================================================
w("# Cheirognomy VLM arm — live probe")
w("")
w(f"- Module under test: `agent/cheirognomy/vlm_arm.py` (public API: `classify_hand`, `compare_hands`)")
w(f"- N = **{_N_RUNS}** runs per image at temperature **{_TEMPERATURE}**")
w(f"- Budget spent: **2 gate calls + {_N_RUNS * len(IMAGES)} GPT-4o vision calls** "
  "(the gate is `classify_hand`'s own; it makes zero classify calls on a hard reject)")
w(f"- Thresholds in force: floor `{_DOMINANCE_FLOOR}`, margin `{_DOMINANCE_MARGIN}`, "
  f"finger consensus `{_FINGER_CONSENSUS_MIN}`-of-4")
w("")
w("**How to read the two agreement numbers — they are not the same thing:**")
w("")
w(f"- **Same-image N={_N_RUNS} agreement** measures MODEL DETERMINISM at temperature "
  f"{_TEMPERATURE}. It says how repeatably the model reports the same feature from the same "
  "pixels. It is NOT a correctness measure — there is no type-labeled oracle.")
w("- **Left-vs-right agreement is the stronger signal.** The same person's two hands should "
  "type alike, so disagreement across hands is a real robustness flag, not sampling noise.")
w("")

t0 = time.time()
try:
    for label, path in IMAGES:
        print(f"[probe] {label}: {path.name} ...", flush=True)
        if not path.exists():
            errors[label] = f"image not found: {path}"
            print(f"[probe] {label}: MISSING", flush=True)
            continue
        try:
            image_bytes = path.read_bytes()
        except OSError as exc:
            errors[label] = f"could not read {path}: {exc}"
            continue
        try:
            results[label] = classify_hand(image_bytes, label=label)
            r = results[label]
            print(f"[probe] {label}: dominant={r.dominant_type} conf={r.confidence} "
                  f"flag={r.quality_flag}", flush=True)
        except Exception as exc:                    # noqa: BLE001 - report, never swallow
            errors[label] = f"{type(exc).__name__}: {exc}"
            print(f"[probe] {label}: ERROR {exc}", flush=True)

    elapsed = round(time.time() - t0, 1)

    # =========================================================================
    # Per hand
    # =========================================================================
    for label, path in IMAGES:
        w(f"## Hand: {label.upper()} — `{path.name}`")
        w("")

        if label in errors:
            w(f"**ERROR — no result.** `{errors[label]}`")
            w("")
            continue

        r = results[label]

        if r.quality_flag is not None:
            w(f"**quality_flag SET — nothing else populated (mutually exclusive by contract).**")
            w("")
            w(f"- quality_flag: `{r.quality_flag}`")
            w(f"- dominant_type: `{r.dominant_type}` (none derived)")
            w(f"- classify runs made: **{len(r.runs)}** (the 3 runs are skipped on a gate reject)")
            w("")
            w("> " + r.disclosed_assumption_text)
            w("")
            continue

        w(f"- image_hash `{r.image_hash}` · runs completed **{len(r.runs)}/{_N_RUNS}**")
        w(f"- finger consensus form: **{r.finger_consensus_form or 'NONE — fingers disagree'}**")
        w("")

        # --- raw runs + majority ------------------------------------------------
        flats = [_flatten(p, doc) for p in r.runs]
        w(f"### {label} — all {len(r.runs)} raw runs, majority, agreement")
        w("")
        w("Verbatim menu values only. `_dropped_` = the run answered the unreadable sentinel or "
          "emitted an off-menu value (dropped, never coerced) — it counts against agreement.")
        w("")
        w("| primitive | " + " | ".join(f"run {i+1}" for i in range(len(flats)))
          + " | majority | agreement |")
        w("|---|" + "---|" * len(flats) + "---|---|")
        for pth, p in r.primitives.items():
            cells = " | ".join(fmt(f[pth]) for f in flats)
            agree = f"{int(round(p['agreement'] * p['runs_total']))}/{p['runs_total']}"
            maj = fmt(p["value"]) if not p["tied"] else "**TIE — no majority**"
            w(f"| `{pth}` | {cells} | {maj} | {agree} |")
        w("")

        w(f"- hand_present per run: " + ", ".join(str(p["hand_present"]) for p in r.runs))
        if r.off_menu_observed:
            w(f"- **off-menu values rejected: {len(r.off_menu_observed)}** (never coerced)")
            for rec in r.off_menu_observed:
                w(f"  - run {rec['run']} · `{rec['path']}` = `{rec['value']}` — {rec['reason']}")
        else:
            w("- off-menu values rejected: **0** — every emission was on-menu")
        if r.disagreement_flags:
            w(f"- disagreement flags ({len(r.disagreement_flags)}): "
              + ", ".join(f"`{p}`" for p in r.disagreement_flags))
        else:
            w("- disagreement flags: none")
        if r.unobserved:
            w(f"- never observed ({len(r.unobserved)}): " + ", ".join(f"`{p}`" for p in r.unobserved))
        w("")

        # --- full score vector --------------------------------------------------
        w(f"### {label} — full per-type score vector (all {len(doc.types)} scored types)")
        w("")
        w("`evaluable` = criteria this type declares AND we observed. `score` = matched/evaluable. "
          "A type is never penalised for a criterion the doctrine leaves blank, nor credited for "
          "one we could not see.")
        w("")
        w("| rank | type | score | matched | evaluable | declared |")
        w("|---|---|---|---|---|---|")
        for i, (name, score, matched, evaluable) in enumerate(r.type_ranking, start=1):
            declared = len(doc.types[name].criteria)
            mark = " **<-- dominant**" if name == r.dominant_type else ""
            w(f"| {i} | **{name}**{mark} | {score} | {len(matched)} ({', '.join(matched) or '—'}) "
              f"| {len(evaluable)} ({', '.join(evaluable) or '—'}) | {declared} |")
        w("")

        # --- derived ------------------------------------------------------------
        w(f"### {label} — derived result")
        w("")
        w(f"- **dominant_type: `{r.dominant_type}`**")
        w(f"- confidence: **{r.confidence}** (mean agreement {r.mean_agreement} x dominance clarity; "
          "a self-consistency heuristic, not a probability)")
        w(f"- quality_flag: `{r.quality_flag}`")
        w("- modifiers:")
        for m in r.modifiers:
            w(f"  - {m}")
        if not r.modifiers:
            w("  - _(none)_")
        w("")
        w("**disclosed_assumption_text:**")
        w("")
        w("> " + r.disclosed_assumption_text)
        w("")

    # =========================================================================
    # Cross-hand
    # =========================================================================
    w("## Cross-hand comparison")
    w("")
    w("The two hands are captured INDEPENDENTLY and never merged — Cheiro reads them as "
      "different hands. This section is a robustness check only.")
    w("")
    if "left" in results and "right" in results:
        cmp = compare_hands(results["left"], results["right"])
        if not cmp["comparable"]:
            w(f"**Not comparable** — {cmp['reason']}")
            w("")
        else:
            w(f"- **type agreement: {cmp['type_agreement']}** "
              f"(left `{results['left'].dominant_type}` vs right `{results['right'].dominant_type}`)")
            w(f"- **primitive agreement: {cmp['primitive_agreement']}** "
              f"over {cmp['both_observed']} primitives observed on BOTH hands "
              f"(of {cmp['compared_paths']} compared)")
            w("")
            w("| primitive | left | right | agree |")
            w("|---|---|---|---|")
            for pth, d in cmp["per_primitive"].items():
                mark = {True: "yes", False: "**NO**", None: "_n/a_"}[d["agree"]]
                w(f"| `{pth}` | {fmt(d['left'])} | {fmt(d['right'])} | {mark} |")
            w("")
            w("Reminder: disagreement here is the stronger flag — the same person's hands should "
              "type alike.")
            w("")
    else:
        w("**Not comparable** — at least one hand produced no result "
          f"(missing: {sorted(set(l for l, _ in IMAGES) - set(results))}).")
        w("")

    # =========================================================================
    # Watch items — the parser pass's four structural findings, in real data
    # =========================================================================
    w("## Watch-items — the four structural findings, made observable")
    w("")
    w("Values reported, not judged. These are the parse-pass findings (a)-(d) measured against "
      "real emissions for the first time.")
    w("")
    live = {k: v for k, v in results.items() if v.quality_flag is None}

    # (c) signal collapse
    w("### (c) Do `palm` and `finger_character` vote for the same type?")
    w("")
    w("Both menus are whole verbatim S2 cells, near-1:1 with type identity. If they always "
      "co-vote, the derive step has fewer independent signals than its 5 slots suggest.")
    w("")
    if live:
        w("| hand | run | palm value -> type(s) | finger_character value -> type(s) | same? |")
        w("|---|---|---|---|---|")
        for label, r in live.items():
            for i, payload in enumerate(r.runs, start=1):
                pv = payload["hand"]["palm"]
                fv = payload["hand"]["finger_character"]
                pt, ft = types_declaring("palm", pv), types_declaring("finger_character", fv)
                if not pt or not ft:
                    same = "_n/a (one dropped)_"
                else:
                    same = "**YES — collapsed**" if set(pt) == set(ft) else "no"
                w(f"| {label} | {i} | {fmt(pv)} -> {pt or '—'} | {fmt(fv)} -> {ft or '—'} | {same} |")
        w("")
    else:
        w("_No populated result to measure._")
        w("")

    # (a) spatulate advantage
    w("### (a) Does `spatulate` win or over-rank on its 2-criteria advantage?")
    w("")
    w(f"`spatulate` declares {len(doc.types['spatulate'].criteria)} criteria; `conic` declares "
      f"{len(doc.types['conic'].criteria)}. Normalised scoring makes a 1.0 cheaper for the sparse type.")
    w("")
    if live:
        w("| hand | spatulate rank | spatulate score | evaluable | dominant type | dominant score |")
        w("|---|---|---|---|---|---|")
        for label, r in live.items():
            rank_map = {n: (i, s, m, e) for i, (n, s, m, e) in enumerate(r.type_ranking, start=1)}
            si, ss, _, se = rank_map["spatulate"]
            dom_score = next(s for n, s, _, _ in r.type_ranking if n == r.dominant_type) \
                if r.dominant_type in rank_map else "n/a (fallback)"
            w(f"| {label} | **{si}** of {len(r.type_ranking)} | {ss} | {len(se)} | "
              f"`{r.dominant_type}` | {dom_score} |")
        w("")
    else:
        w("_No populated result to measure._")
        w("")

    # (b) conic/psychic continuum
    w("### (b) Are `conic` and `psychic` near-tied (the `pointed` continuum)?")
    w("")
    w("S2's own note: conic <-> psychic is a proportion continuum. `conic`'s cell maps to both "
      "`conic` and `pointed`, so an observed `pointed` credits both types.")
    w("")
    if live:
        w("| hand | conic | psychic | gap | within margin " + f"({_DOMINANCE_MARGIN})? | "
          "finger consensus |")
        w("|---|---|---|---|---|---|")
        for label, r in live.items():
            sc = {n: s for n, s, _, _ in r.type_ranking}
            gap = round(abs(sc["conic"] - sc["psychic"]), 3)
            w(f"| {label} | {sc['conic']} | {sc['psychic']} | {gap} | "
              f"{'**YES — near-tied**' if gap < _DOMINANCE_MARGIN else 'no'} | "
              f"`{r.finger_consensus_form}` |")
        w("")
    else:
        w("_No populated result to measure._")
        w("")

    # (d) no-fingertip types
    w("### (d) Can `elementary` / `philosophic` score at all, with no fingertip cell?")
    w("")
    w("Neither declares a Fingertips cell, so the only per-finger primitive captured can never "
      "credit them. They are reachable only via palm / finger_character / joints / nails.")
    w("")
    if live:
        w("| hand | type | score | matched | evaluable | rank |")
        w("|---|---|---|---|---|---|")
        for label, r in live.items():
            for i, (n, s, m, e) in enumerate(r.type_ranking, start=1):
                if n in ("elementary", "philosophic"):
                    w(f"| {label} | **{n}** | {s} | {len(m)} ({', '.join(m) or '—'}) | "
                      f"{len(e)} ({', '.join(e) or '—'}) | {i} |")
        w("")
    else:
        w("_No populated result to measure._")
        w("")

    # =========================================================================
    w("## Status")
    w("")
    w(f"- Probe wall time: {elapsed}s")
    w(f"- Hands with a populated result: {sorted(live)} · "
      f"quality-flagged: {sorted(k for k, v in results.items() if v.quality_flag)} · "
      f"errored: {sorted(errors)}")
    w("- No commit — awaiting RATIFIED.")
    w("")
    w("Nothing here measures CORRECTNESS. Same-image agreement measures determinism; cross-hand "
      "agreement measures robustness. Whether the derived type is the right type is a human "
      "judgment this probe cannot make (fidelity-not-truth).")
    w("")

except Exception:                                   # noqa: BLE001 - never lose a paid run
    w("## PROBE CRASHED after spending API calls")
    w("")
    w("```")
    w(traceback.format_exc())
    w("```")
    w("")
    raise
finally:
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[probe] report -> {REPORT_PATH}", flush=True)

sys.exit(1 if errors else 0)
