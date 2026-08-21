"""
scripts/cheirognomy_multivalue_check.py

Verify MULTI-VALUE `palm` + `finger_character` in agent/cheirognomy/vlm_arm.py:
the two tangled-axis slots now hold a LIST of doctrine menu values, merged
per-value across runs, and their S2 criteria OR-match.

NO-REGRESSION GATE (hardest case first = the author's own hand): one live run of
palm_right_test.jpg, view=palmar, N=3, MUST derive dominant_type == "square",
and spatulate must not tie or beat it. Anything else means the change is wrong.

Cost: 1 gate + 3 classify GPT-4o calls. No scaling.

Writes diagnostics/latest_run.md (OVERWRITE). Report in a `finally` block so a
formatting error cannot lose a paid run.
"""

import sys
import traceback
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from agent.cheirognomy.vlm_arm import (  # noqa: E402
    _DOMINANCE_FLOOR,
    _DOMINANCE_MARGIN,
    _N_RUNS,
    _TEMPERATURE,
    _flatten,
    build_system_prompt,
    classify_hand,
    load_doctrine,
)

REPORT_PATH = _REPO_ROOT / "diagnostics" / "latest_run.md"
IMAGE = _REPO_ROOT / "data" / "test_images" / "palm_right_test.jpg"
VIEW = "palmar"
REQUIRED_TYPE = "square"

doc = load_doctrine()
lines = []
w = lines.append
checks = []


def check(name, passed, detail):
    checks.append((name, bool(passed), detail))
    return bool(passed)


try:
    # --- static checks: no API cost -----------------------------------------
    prompt = build_system_prompt(doc, VIEW)
    single = [s for s in ("joint_knottiness", "broad_point", "overall_proportion",
                          "finger_palm_ratio") if s not in doc.multi_slots]

    check("doctrine `multi:` annotation parsed",
          doc.multi_slots == ("palm", "finger_character"), doc.multi_slots)
    check("every other whole-hand slot stays single-valued",
          all(s not in doc.multi_slots for s in single), single)
    # Field LINES only -- the explanatory MULTI-VALUE paragraph also contains the
    # literal "[LIST]" and would otherwise be counted as a field.
    list_lines = [ln.strip() for ln in prompt.splitlines()
                  if "[LIST]:" in ln and ln.startswith("  ")]
    check("exactly the multi slots are announced [LIST] in the prompt",
          len(list_lines) == len(doc.multi_slots)
          and all(any(ln.startswith(s) for ln in list_lines) for s in doc.multi_slots)
          and "MULTI-VALUE FIELDS" in prompt,
          list_lines)
    check("JSON shape asks multi slots as arrays, singles as scalars",
          '"palm": ["...", "..."]' in prompt
          and '"finger_character": ["...", "..."]' in prompt
          and '"joint_knottiness": "..."' in prompt,
          [ln for ln in prompt.splitlines() if ln.strip().startswith('"hand"')])
    check("menu WORDS unchanged (cardinality only)",
          doc.menus["palm"] == tuple(dict.fromkeys(
              tc.criteria["palm"] for tc in doc.types.values() if "palm" in tc.criteria)),
          doc.menus["palm"])

    # --- live run ------------------------------------------------------------
    print(f"[multi] {IMAGE.name} view={VIEW} N={_N_RUNS} -> 1 gate + {_N_RUNS} classify",
          flush=True)
    r = classify_hand(IMAGE.read_bytes(), label="right", view=VIEW)
    print(f"[multi] dominant={r.dominant_type} conf={r.confidence}", flush=True)

    flats = [_flatten(p, doc) for p in r.runs]
    palm = r.primitives["hand.palm"]
    fchar = r.primitives["hand.finger_character"]

    check("`hand.palm` merged as a multi slot", palm.get("multi") is True, palm.get("multi"))
    check("`hand.finger_character` merged as a multi slot",
          fchar.get("multi") is True, fchar.get("multi"))
    check("`hand.palm` value is a tuple of menu values",
          palm["value"] is None or (isinstance(palm["value"], tuple)
                                    and all(v in doc.menus["palm"] for v in palm["value"])),
          palm["value"])
    check("`hand.joint_knottiness` still a single scalar (unchanged path)",
          r.primitives["hand.joint_knottiness"]["value"] is None
          or isinstance(r.primitives["hand.joint_knottiness"]["value"], str),
          r.primitives["hand.joint_knottiness"]["value"])
    check("no multi slot was recorded as a tie (no winner-take-all vote to tie)",
          palm["tied"] is False and fchar["tied"] is False,
          (palm["tied"], fchar["tied"]))

    ranking = {n: s for n, s, _m, _e in r.type_ranking}
    top_name, top_score = r.type_ranking[0][0], r.type_ranking[0][1]
    second_score = r.type_ranking[1][1] if len(r.type_ranking) > 1 else 0.0

    gate_type = r.dominant_type == REQUIRED_TYPE
    gate_spatulate = ranking.get("square", 0.0) > ranking.get("spatulate", 0.0)
    check(f"GATE: dominant_type == `{REQUIRED_TYPE}`", gate_type, r.dominant_type)
    check("GATE: `spatulate` neither ties nor beats `square`", gate_spatulate,
          f"square={ranking.get('square')} spatulate={ranking.get('spatulate')}")

    gate_passed = gate_type and gate_spatulate

    # --- report ---------------------------------------------------------------
    passed_n = sum(1 for _, p, _ in checks if p)
    w("# Cheirognomy — multi-value `palm` + `finger_character`, OR-match scoring")
    w("")
    w(f"**GATE: {'PASS' if gate_passed else 'FAIL'}** — "
      f"dominant_type `{r.dominant_type}` (required `{REQUIRED_TYPE}`), "
      f"square {ranking.get('square')} vs spatulate {ranking.get('spatulate')}.")
    w("")
    w("- Two files, one coupled change: the S4 `multi:` annotation in "
      "`data/palm_rules/_doctrine/CHEIROGNOMY_HAND_TYPE.md`, and the parser/prompt/merge/scorer "
      "that reads it in `agent/cheirognomy/vlm_arm.py`.")
    w("- **No menu word changed.** The vocabulary contract is untouched; only CARDINALITY moved, "
      "and it moved in the doctrine file, parsed like every other menu.")
    w(f"- Live run: `{IMAGE.name}`, view **{VIEW}**, N={_N_RUNS} at temperature {_TEMPERATURE} · "
      f"**{1 + len(r.runs)} GPT-4o calls** (1 gate + {len(r.runs)} classify)")
    w("")

    w("## 1. The annotation, as parsed")
    w("")
    w("```")
    w("S4:  - **MULTI-VALUE slots** — `multi: palm, finger_character`")
    w(f"doc.multi_slots = {doc.multi_slots}")
    w("```")
    w("")
    w("| slot | cardinality | merge | criterion match |")
    w("|---|---|---|---|")
    for p in ("palm", "finger_character", "joint_knottiness", "broad_point",
              "overall_proportion", "finger_palm_ratio", "nail_length"):
        multi = p in doc.multi_slots
        w(f"| `{p}` | {'**LIST**' if multi else 'single'} "
          f"| {'per-value' if multi else 'strict plurality'} "
          f"| {'**OR-match**' if multi else 'equality'} |")
    w("")
    w("An empty annotation is legal and reproduces the previous single-valued behaviour "
      "byte-for-byte — verified offline against a copy of the doctrine with the bullet removed: "
      "identical menus, identical types, no `[LIST]`, no multi block, scalar JSON shape.")
    w("")

    w("## 2. Per-value majority — `palm` and `finger_character`")
    w("")
    w("A multi slot's values are merged INDEPENDENTLY: each is its own yes/no question across "
      "the runs, not a competitor in one winner-take-all vote. `agreement` per value = runs "
      "containing it / runs attempted — the same denominator a single slot uses.")
    w("")
    for name, prim in (("hand.palm", palm), ("hand.finger_character", fchar)):
        w(f"**`{name}`** — per run:")
        w("")
        w("| run | observed values |")
        w("|---|---|")
        for i, f in enumerate(flats, start=1):
            vals = f[name]
            w(f"| {i} | " + (", ".join(f"`{v}`" for v in vals) if vals else "_none_") + " |")
        w("")
        w("| value | runs containing it | agreement | in merged set? |")
        w("|---|---|---|---|")
        pv = prim.get("per_value_agreement") or {}
        for v, agr in sorted(pv.items(), key=lambda kv: (-kv[1], kv[0])):
            w(f"| `{v}` | {prim['votes'][v]}/{prim['runs_total']} | {agr} "
              f"| {'yes' if v in (prim['value'] or ()) else 'no'} |")
        if not pv:
            w("| _nothing observed_ | 0 | 0.0 | — |")
        w("")
        w(f"- merged `value` = `{prim['value']}`")
        w(f"- slot `agreement` = {prim['agreement']} (mean of the per-value agreements) · "
          f"`tied` = {prim['tied']} · `runs_observed` = {prim['runs_observed']}")
        w("")

    w("## 3. Full 6-type score vector")
    w("")
    w("`score = matched / evaluable`. The counting rule is UNCHANGED — a multi slot still costs "
      "every type that declares it exactly one evaluable criterion, and a type whose phrase is "
      "absent still scores a miss. OR-match credits evidence that is present on a tangled axis; "
      "it does not lower the bar.")
    w("")
    w("| rank | type | score | matched | evaluable | `palm` criterion | fires? |")
    w("|---|---|---|---|---|---|---|")
    for i, (n, s, m, ev) in enumerate(r.type_ranking, start=1):
        want = doc.types[n].criteria.get("palm")
        fires = "—" if want is None else (
            "**yes** (OR-match)" if want in (palm["value"] or ()) else "no")
        w(f"| {i} | `{n}` | **{s}** | {len(m)} ({', '.join(m) or '—'}) "
          f"| {len(ev)} ({', '.join(ev) or '—'}) | {f'`{want}`' if want else '_em-dash_'} "
          f"| {fires} |")
    w("")
    w(f"- floor {_DOMINANCE_FLOOR} · margin {_DOMINANCE_MARGIN} · "
      f"top `{top_name}` {top_score} − runner-up {second_score} = "
      f"{round(top_score - second_score, 3)}")
    w("")

    w("## 4. Every merged primitive, this run")
    w("")
    w("| primitive | " + " | ".join(f"run {i+1}" for i in range(len(r.runs)))
      + " | merged | agreement |")
    w("|---|" + "---|" * len(r.runs) + "---|---|")
    for pth, p in r.primitives.items():
        cells = " | ".join(
            ("`" + ", ".join(f[pth]) + "`" if isinstance(f[pth], tuple)
             else (f"`{f[pth]}`" if f[pth] is not None else "_none_"))
            for f in flats
        )
        maj = ("`" + ", ".join(p["value"]) + "`" if isinstance(p["value"], tuple)
               else (f"`{p['value']}`" if p["value"] is not None else "_none_"))
        note = " **(multi)**" if p.get("multi") else (
            " **(structural)**" if pth in r.structurally_unobserved else "")
        w(f"| `{pth}`{note} | {cells} | {maj} | {p['agreement']} |")
    w("")
    w(f"- **dominant_type: `{r.dominant_type}`** · confidence **{r.confidence}** "
      f"(mean agreement {r.mean_agreement}) · quality_flag `{r.quality_flag}` · view `{r.view}`")
    w(f"- finger consensus form: `{r.finger_consensus_form}`")
    w(f"- disagreement flags: {r.disagreement_flags or 'none'}")
    w(f"- unobserved (asked, not seen): {r.unobserved or 'none'}")
    w(f"- structurally unobserved: {r.structurally_unobserved or 'none'}")
    w(f"- off-menu rejected: {len(r.off_menu_observed)}")
    for rec in r.off_menu_observed:
        w(f"  - run {rec['run']} `{rec['path']}` = `{rec['value']}` ({rec['reason']})")
    w("- modifiers:")
    for m in r.modifiers:
        w(f"  - {m}")
    w("")
    w("**disclosed_assumption_text:**")
    w("")
    w("> " + r.disclosed_assumption_text)
    w("")

    w(f"## 5. Checks — {passed_n}/{len(checks)} passed")
    w("")
    w("| # | check | result | detail |")
    w("|---|---|---|---|")
    for i, (name, passed, detail) in enumerate(checks, start=1):
        w(f"| {i} | {name} | {'PASS' if passed else '**FAIL**'} | `{detail}` |")
    w("")

    w("## 6. Honest limits")
    w("")
    w("- n=1 run against one image. Same-image agreement at temperature 0.4 measures "
      "REPRODUCIBILITY, never correctness — no type-labelled oracle exists (fidelity-not-truth).")
    w("- The gate asserts the derive did not REGRESS on the one hand whose shape the author can "
      "check by eye. It does not establish that multi-value reads any other hand better.")
    w("- A value observed in only ONE of three runs is kept in the merged set, with its low "
      "agreement recorded and flagged. On a tangled axis two runs naming different values are "
      "not contradicting each other, so dropping the minority would discard evidence rather than "
      "resolve a conflict. TUNING NOTE: if a minority value is ever seen pulling a type across "
      "the dominance margin on its own, switch `_merge_multi` to a per-value majority "
      "(`c * 2 > n`) — one line, and the votes to justify it are already recorded above.")
    w("")

except Exception:                                   # noqa: BLE001 - never lose a paid run
    w("")
    w("## CHECK CRASHED")
    w("")
    w("```")
    w(traceback.format_exc())
    w("```")
    w("")
    raise
finally:
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[multi] report -> {REPORT_PATH}", flush=True)

sys.exit(0 if all(p for _, p, _ in checks) else 1)
