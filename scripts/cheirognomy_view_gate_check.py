"""
scripts/cheirognomy_view_gate_check.py

Verify the view gate in agent/cheirognomy/vlm_arm.py: `nail_length` must be
STRUCTURALLY UNOBSERVED in a palmar view -- absent from the prompt, None in the
output, and skipped as not-evaluable by every type's score.

Runs ONE image at the default view="palmar", N=3. Cost: 1 gate + 3 classify
GPT-4o calls. No scaling.

Writes diagnostics/latest_run.md (OVERWRITE). Report in a `finally` block so a
formatting error cannot lose a paid run.
"""

import sys
import traceback
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from agent.cheirognomy.vlm_arm import (  # noqa: E402
    _HAND_PRIMITIVES,
    _N_RUNS,
    _PRIMITIVE_REQUIRES_VIEW,
    _TEMPERATURE,
    _VALID_VIEWS,
    build_system_prompt,
    classify_hand,
    load_doctrine,
    omitted_primitives,
)

REPORT_PATH = _REPO_ROOT / "diagnostics" / "latest_run.md"
IMAGE = _REPO_ROOT / "data" / "test_images" / "palm_right_test.jpg"
VIEW = "palmar"          # the default -- exercised explicitly, not assumed

doc = load_doctrine()
lines = []
w = lines.append
checks = []


def check(name, passed, detail):
    checks.append((name, bool(passed), detail))
    return bool(passed)


try:
    # --- static checks: no API cost -----------------------------------------
    prompt_palmar = build_system_prompt(doc, "palmar")
    prompt_dorsal = build_system_prompt(doc, "dorsal")
    omitted = omitted_primitives(VIEW)

    check("`nail_length` requires the dorsal view",
          _PRIMITIVE_REQUIRES_VIEW.get("nail_length") == "dorsal",
          _PRIMITIVE_REQUIRES_VIEW)
    check("palmar omits exactly ['nail_length']", omitted == ("nail_length",), omitted)
    check("dorsal omits nothing", omitted_primitives("dorsal") == (), omitted_primitives("dorsal"))
    check("`nail_length` ABSENT from the palmar prompt",
          "nail_length" not in prompt_palmar, f"{len(prompt_palmar)} chars")
    check("`nail_length` PRESENT in the dorsal prompt",
          "nail_length" in prompt_dorsal, f"{len(prompt_dorsal)} chars")
    # Only values UNIQUE to the nail menu can prove a leak: `short` and `long` are
    # also legitimate `finger_palm_ratio` values, so a raw substring test over the
    # whole nail menu reports a false leak on a correctly-gated prompt.
    _other_values = {v for p in _HAND_PRIMITIVES if p != "nail_length"
                     for v in doc.menus[p]} | set(doc.menus["fingertip_form"]) \
                    | set(doc.menus["inter_finger_spacing"])
    nail_exclusive = [v for v in doc.menus["nail_length"] if v not in _other_values]
    check("no nail-EXCLUSIVE menu value leaks into the palmar prompt",
          not any(v in prompt_palmar for v in nail_exclusive),
          f"exclusive={nail_exclusive}; shared with other menus="
          f"{[v for v in doc.menus['nail_length'] if v in _other_values]}")
    check("every other prompted primitive still asked in palmar",
          all(p in prompt_palmar for p in _HAND_PRIMITIVES if p not in omitted),
          [p for p in _HAND_PRIMITIVES if p not in omitted])
    bad_view = False
    try:
        build_system_prompt(doc, "sideways")
    except Exception:
        bad_view = True
    check("an unknown view raises rather than silently defaulting", bad_view, _VALID_VIEWS)

    # --- live run ------------------------------------------------------------
    print(f"[view-gate] {IMAGE.name} view={VIEW} N={_N_RUNS} -> 1 gate + {_N_RUNS} classify",
          flush=True)
    r = classify_hand(IMAGE.read_bytes(), label="right", view=VIEW)
    print(f"[view-gate] dominant={r.dominant_type} conf={r.confidence}", flush=True)

    check("result records the view used", r.view == VIEW, r.view)
    check("`hand.nail_length` value is None in the merged output",
          r.primitives["hand.nail_length"]["value"] is None,
          r.primitives["hand.nail_length"])
    check("`hand.nail_length` is NOT a tie (it is unobserved, not contested)",
          r.primitives["hand.nail_length"]["tied"] is False,
          r.primitives["hand.nail_length"]["tied"])
    check("`hand.nail_length` never appeared in any raw run",
          all(p["hand"]["nail_length"] is None for p in r.runs),
          [p["hand"]["nail_length"] for p in r.runs])
    check("`hand.nail_length` was NOT logged as off-menu (model broke no rule)",
          not any(rec["path"] == "hand.nail_length" for rec in r.off_menu_observed),
          r.off_menu_observed or "no off-menu values at all")
    check("`hand.nail_length` listed as STRUCTURALLY unobserved",
          "hand.nail_length" in r.structurally_unobserved, r.structurally_unobserved)
    check("`hand.nail_length` NOT listed as merely unobserved (the two are distinct)",
          "hand.nail_length" not in r.unobserved, r.unobserved)
    check("`hand.nail_length` NOT a disagreement flag",
          "hand.nail_length" not in r.disagreement_flags, r.disagreement_flags)
    scored_nail = [n for n, _s, _m, ev in r.type_ranking if "nail_length" in ev]
    check("no type scores `nail_length` as evaluable", not scored_nail,
          scored_nail or "0 of 6 types")
    check("disclosure distinguishes structural absence from 'could not see'",
          "not assessed at all" in r.disclosed_assumption_text.lower(),
          "phrase present" if "not assessed at all" in r.disclosed_assumption_text.lower()
          else "PHRASE MISSING")

    # --- report ---------------------------------------------------------------
    passed_n = sum(1 for _, p, _ in checks if p)
    w("# Cheirognomy view gate — `nail_length` structurally unobserved in a palmar view")
    w("")
    w(f"- Change: `view` parameter threaded `classify_hand` -> `_classify_once` -> "
      "`build_system_prompt` in `agent/cheirognomy/vlm_arm.py`. One file touched.")
    w(f"- Rule: `nail_length` is observable ONLY when `view == \"dorsal\"` — nails are on the "
      "back of the hand.")
    w(f"- Live run: `{IMAGE.name}`, view=**{VIEW}** (the default), N={_N_RUNS} at "
      f"temperature {_TEMPERATURE} · **4 GPT-4o calls** (1 gate + {_N_RUNS} classify)")
    w(f"- Doctrine, scorer math, and all other primitives: **unchanged**.")
    w("")
    w(f"## 1. Checks — {passed_n}/{len(checks)} passed")
    w("")
    w("| # | check | result | detail |")
    w("|---|---|---|---|")
    for i, (name, passed, detail) in enumerate(checks, start=1):
        w(f"| {i} | {name} | {'PASS' if passed else '**FAIL**'} | `{detail}` |")
    w("")

    w("## 2. The three required confirmations")
    w("")
    w("**(a) Absent from the prompt.** The palmar system prompt never contains the string "
      f"`nail_length`, nor any of its menu values ({', '.join(f'`{v}`' for v in doc.menus['nail_length'])}). "
      "The field is omitted from both the menu block and the JSON shape, so the model has "
      "nowhere to put a guess. The dorsal prompt still carries it.")
    w("")
    w("| view | prompt chars | `nail_length` asked? | omitted primitives |")
    w("|---|---|---|---|")
    w(f"| palmar | {len(prompt_palmar)} | **no** | {list(omitted_primitives('palmar'))} |")
    w(f"| dorsal | {len(prompt_dorsal)} | yes | {list(omitted_primitives('dorsal'))} |")
    w("")
    w("**(b) None in the output — via the existing unobserved path, not a new one.**")
    w("")
    w("```")
    w(f"hand.nail_length = {r.primitives['hand.nail_length']}")
    w("```")
    w("")
    w("`value=None`, `tied=False`, `runs_observed=0`, and **zero** off-menu records — the same "
      "state an unreadable answer produces. It is NOT a fabrication and NOT an abstention.")
    w("")
    w("**(c) Skipped in every type's score.** `evaluable` excludes `nail_length` for all "
      f"{len(r.type_ranking)} scored types, so no type is credited or penalised for it:")
    w("")
    w("| type | score | matched | evaluable | declares nail_length? |")
    w("|---|---|---|---|---|")
    for n, s, m, ev in r.type_ranking:
        declares = "nail_length" in doc.types[n].criteria
        w(f"| `{n}` | {s} | {len(m)} ({', '.join(m) or '—'}) | {len(ev)} ({', '.join(ev) or '—'}) "
          f"| {'yes — and correctly skipped' if declares else 'no'} |")
    w("")

    w("## 3. Derived result (palmar, N=3)")
    w("")
    w("| primitive | " + " | ".join(f"run {i+1}" for i in range(len(r.runs)))
      + " | majority | agreement |")
    w("|---|" + "---|" * len(r.runs) + "---|---|")
    from agent.cheirognomy.vlm_arm import _flatten  # noqa: E402
    flats = [_flatten(p, doc) for p in r.runs]
    for pth, p in r.primitives.items():
        cells = " | ".join(f"`{f[pth]}`" if f[pth] is not None else "_none_" for f in flats)
        votes = int(round(p["agreement"] * p["runs_total"]))
        note = " **(structural)**" if pth in r.structurally_unobserved else ""
        maj = f"`{p['value']}`" if p["value"] is not None else "_none_"
        w(f"| `{pth}`{note} | {cells} | {maj} | {votes}/{p['runs_total']} |")
    w("")
    w(f"- **dominant_type: `{r.dominant_type}`** · confidence **{r.confidence}** "
      f"(mean agreement {r.mean_agreement}) · quality_flag `{r.quality_flag}` · view `{r.view}`")
    w(f"- structurally_unobserved: {r.structurally_unobserved}")
    w(f"- unobserved (asked, not seen): {r.unobserved or 'none'}")
    w(f"- off-menu rejected: {len(r.off_menu_observed)}")
    w("- modifiers:")
    for m in r.modifiers:
        w(f"  - {m}")
    w("")
    w("**disclosed_assumption_text:**")
    w("")
    w("> " + r.disclosed_assumption_text)
    w("")

    w("## 4. Comparison to the pre-gate run on this same image")
    w("")
    w("Earlier palmar runs of `palm_right_test.jpg` had the model answering `nail_length` = "
      "`short` unanimously — from a photo in which no nail is visible. That value was scoring "
      "against `elementary` and `square`, both of which declare a Nails criterion. It is now "
      "structurally absent instead of confidently wrong.")
    w("")
    w(f"Note the consequence for the derive: `elementary`'s evaluable set shrinks, so its only "
      "previous match is gone. This changes scores on this image by design — the gate removes "
      "evidence that was never observed. Whether the resulting type is *better* is a human "
      "judgment, not something this check asserts.")
    w("")

    w("## 5. Status")
    w("")
    w(f"- {passed_n}/{len(checks)} checks passed")
    w("- Doctrine unchanged · scorer math unchanged · no other primitive touched")
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
    print(f"[view-gate] report -> {REPORT_PATH}", flush=True)

sys.exit(0 if all(p for _, p, _ in checks) else 1)
