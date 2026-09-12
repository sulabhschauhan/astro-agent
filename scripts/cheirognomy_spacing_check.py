"""
scripts/cheirognomy_spacing_check.py

Measure the effect of the inter-finger-spacing MEASUREMENT-SITE directive added
to `build_system_prompt` in agent/cheirognomy/vlm_arm.py: judge each gap at the
LOWER THIRD of the fingers (where they join the palm), not at the tips.

Prompt-instruction change only. The menu {tight, wide}, the keys (1_2/2_3/3_4),
the scorer, and every other primitive are untouched.

Runs ONE image, palmar, N=3. Cost: 1 gate + 3 classify GPT-4o calls. No scaling.

Writes diagnostics/latest_run.md (OVERWRITE). Report in a `finally` block so a
formatting error cannot lose a paid run.
"""

import sys
import traceback
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from agent.cheirognomy.vlm_arm import (  # noqa: E402
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

# PRIOR BASELINE — the two earlier palmar N=3 runs of THIS SAME image, taken
# from their own reports before the directive existed. Recorded verbatim so the
# comparison is against measured history, not memory.
#   run A: the view-gate check (most recent pre-directive run, 4 calls)
#   run B: the original probe (first run of this image)
PRIOR = {
    "view-gate run (immediately prior)": {
        "1_2": ["wide", "wide", "tight"],
        "2_3": ["wide", "wide", "tight"],
        "3_4": ["wide", "wide", "tight"],
    },
    "first probe run": {
        "1_2": ["wide", "tight", "wide"],
        "2_3": ["wide", "tight", "wide"],
        "3_4": ["wide", "tight", "wide"],
    },
}

doc = load_doctrine()
lines = []
w = lines.append


def majority_of(vals):
    obs = [v for v in vals if v is not None]
    if not obs:
        return None, 0, len(vals)
    top = max(set(obs), key=obs.count)
    if [obs.count(v) for v in set(obs)].count(obs.count(top)) > 1:
        return "TIE", obs.count(top), len(vals)
    return top, obs.count(top), len(vals)


try:
    prompt = build_system_prompt(doc, VIEW)
    directive_present = "LOWER THIRD" in prompt
    menu_intact = tuple(doc.menus["inter_finger_spacing"]) == ("tight", "wide")

    print(f"[spacing] {IMAGE.name} view={VIEW} N={_N_RUNS} -> 1 gate + {_N_RUNS} classify",
          flush=True)
    r = classify_hand(IMAGE.read_bytes(), label="right", view=VIEW)
    print(f"[spacing] dominant={r.dominant_type} conf={r.confidence}", flush=True)

    flats = [_flatten(p, doc) for p in r.runs]
    now = {k: [f[f"inter_finger_spacing.{k}"] for f in flats] for k in doc.spacing_keys}

    # =========================================================================
    w("# Cheirognomy — inter-finger spacing measurement-site directive")
    w("")
    w("- **Change: one instruction line in `build_system_prompt`.** Each gap is now judged at "
      "the LOWER THIRD of the fingers, where they join the palm — not at the tips.")
    w("- Rationale: the tip gap is dominated by how far the subject happened to splay their "
      "fingers for the photo; the base gap is set by hand structure and barely moves with pose. "
      "§7 treats spread as a structural signal, so the measurement site is what makes it one.")
    w(f"- Live run: `{IMAGE.name}`, view **{VIEW}**, N={_N_RUNS} at temperature {_TEMPERATURE} "
      f"· **4 GPT-4o calls** (1 gate + {_N_RUNS} classify)")
    w("")
    w("| invariant | state |")
    w("|---|---|")
    w(f"| directive present in prompt | {'yes' if directive_present else '**MISSING**'} |")
    w(f"| menu unchanged | {'yes — ' if menu_intact else '**CHANGED** — '}"
      f"`{list(doc.menus['inter_finger_spacing'])}` |")
    w(f"| keys unchanged | `{list(doc.spacing_keys)}` |")
    w("| scorer / other primitives | untouched (spacing is not a §2 derive criterion) |")
    w("")

    # --- the three runs ------------------------------------------------------
    w("## 1. Spacing — this run")
    w("")
    w("| gap | run 1 | run 2 | run 3 | majority | agreement |")
    w("|---|---|---|---|---|---|")
    for k in doc.spacing_keys:
        vals = now[k]
        maj, votes, total = majority_of(vals)
        cells = " | ".join(f"`{v}`" if v else "_none_" for v in vals)
        w(f"| `{k}` | {cells} | {'`' + str(maj) + '`' if maj else '_none_'} | {votes}/{total} |")
    w("")
    unanimous_now = sum(1 for k in doc.spacing_keys if len(set(now[k])) == 1 and None not in now[k])
    w(f"**Unanimous gaps this run: {unanimous_now}/{len(doc.spacing_keys)}**")
    w("")

    # --- comparison ----------------------------------------------------------
    w("## 2. Compared to the prior runs (same image, same view, no directive)")
    w("")
    w("| run | 1_2 | 2_3 | 3_4 | unanimous gaps |")
    w("|---|---|---|---|---|")
    for name, data in PRIOR.items():
        cells = []
        unan = 0
        for k in ("1_2", "2_3", "3_4"):
            vals = data[k]
            maj, votes, total = majority_of(vals)
            cells.append(f"{', '.join(vals)} -> **{maj}** {votes}/{total}")
            unan += len(set(vals)) == 1
        w(f"| {name} | {cells[0]} | {cells[1]} | {cells[2]} | {unan}/3 |")
    cells, unan = [], 0
    for k in ("1_2", "2_3", "3_4"):
        vals = now[k]
        maj, votes, total = majority_of(vals)
        cells.append(f"{', '.join(str(v) for v in vals)} -> **{maj}** {votes}/{total}")
        unan += len(set(vals)) == 1 and None not in vals
    w(f"| **THIS RUN (with directive)** | {cells[0]} | {cells[1]} | {cells[2]} | **{unan}/3** |")
    w("")
    w("Prior behaviour on this image was **2/3 on every gap, with one run flipping to `tight`** "
      "— and the flip landed on a different run each time (run 3 in the view-gate run, run 2 in "
      "the first probe), i.e. an unstable read rather than a consistent minority view.")
    w("")

    prior_unan = sum(len(set(v)) == 1 for d in PRIOR.values() for v in d.values())
    prior_total = sum(len(d) for d in PRIOR.values())
    w(f"- prior unanimous gaps: **{prior_unan}/{prior_total}** across both runs")
    w(f"- this run: **{unan}/3**")
    w("")
    if unan == 3:
        w("**The three gaps are unanimous this run**, where both prior runs split 2/3 on all "
          "three. n=1 run — this is a single observation, not a demonstrated fix. The honest "
          "read is that it is consistent with the directive helping and does not establish it.")
    elif unan > 0:
        w(f"**Partial: {unan}/3 gaps unanimous**, against 0/3 in both prior runs. Movement in "
          "the expected direction, n=1, not established.")
    else:
        w("**No improvement in unanimity** — the gaps still split. The directive did not "
          "stabilise this read on this image; the instability is not (or not only) a "
          "measurement-site problem.")
    w("")
    changed = [k for k in doc.spacing_keys
               if majority_of(now[k])[0]
               != majority_of(PRIOR["view-gate run (immediately prior)"][k])[0]]
    changed_text = (", ".join(f"`{k}`" for k in changed) if changed
                    else "**no gap** — same majority, only the agreement moved")
    w(f"- majority VALUE changed vs the immediately-prior run on: {changed_text}")
    w("")

    # --- context -------------------------------------------------------------
    w("## 3. Rest of the result (context — spacing does not feed the type)")
    w("")
    w(f"- **dominant_type `{r.dominant_type}`** · confidence {r.confidence} · "
      f"view `{r.view}` · quality_flag `{r.quality_flag}`")
    w(f"- off-menu rejected: {len(r.off_menu_observed)}")
    w(f"- structurally unobserved: {r.structurally_unobserved}")
    w(f"- disagreement flags: {[p for p in r.disagreement_flags] or 'none'}")
    w("")
    w("Spacing is captured under §4 as dual-use and is NOT one of the §2 criteria the scorer "
      "reads, so nothing above changes the derived type. This directive improves a captured "
      "signal, it does not touch classification.")
    w("")
    w("| primitive | run 1 | run 2 | run 3 | majority | agreement |")
    w("|---|---|---|---|---|---|")
    for pth, p in r.primitives.items():
        cells = " | ".join(f"`{f[pth]}`" if f[pth] is not None else "_none_" for f in flats)
        votes = int(round(p["agreement"] * p["runs_total"]))
        maj = f"`{p['value']}`" if p["value"] is not None else "_none_"
        w(f"| `{pth}` | {cells} | {maj} | {votes}/{p['runs_total']} |")
    w("")

    w("## 4. Status")
    w("")
    w("- One file touched: `agent/cheirognomy/vlm_arm.py`, one instruction line in "
      "`build_system_prompt`.")
    w("- Menu, keys, scorer, and all other primitives unchanged.")
    w("- n=1 run against a 2-run prior baseline. Same-image agreement measures determinism at "
      f"temperature {_TEMPERATURE}, not correctness — no oracle says which gap reading is right.")
    w("- No commit — awaiting RATIFIED.")
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
    print(f"[spacing] report -> {REPORT_PATH}", flush=True)
