"""
scripts/cheirognomy_consistency_set.py

BATCH runner over agent/cheirognomy/vlm_arm.py — builds the consistency-set
aggregation that adjudicates the parse-pass findings.

Reuses the module's authored API (`classify_hand`, `compare_hands`) and its
authored derive (`_derive_type`) for the counterfactual analysis. NO scoring
logic is defined here; this file only runs, re-derives, and aggregates.

SAMPLE-BEFORE-SCALE: by default this runs ONLY the 3 curated in-repo test
images, even when pointed at a directory holding more. Sweeping the whole
directory requires an explicit `--all`, so an accidental invocation cannot burn
the full set. Projected cost is printed BEFORE any call is made.

COST: `classify_hand` makes 1 gate call + N classify calls per image, all
GPT-4o. A gate-rejected image costs 1 call and stops there.

Writes diagnostics/latest_run.md (OVERWRITE) and a blind-label template CSV.
The report is written in a `finally` block so spent API calls survive a
formatting error.
"""

import argparse
import csv
import sys
import time
import traceback
from collections import Counter, defaultdict
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from agent.cheirognomy.vlm_arm import (  # noqa: E402
    _DOMINANCE_FLOOR,
    _DOMINANCE_MARGIN,
    _N_RUNS,
    _TEMPERATURE,
    _derive_type,
    _flatten,
    classify_hand,
    load_doctrine,
)

REPORT_PATH = _REPO_ROOT / "diagnostics" / "latest_run.md"
TEMPLATE_PATH = _REPO_ROOT / "diagnostics" / "cheirognomy_labels_TEMPLATE.csv"
DEFAULT_DIR = _REPO_ROOT / "data" / "test_images"

_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}

# The curated sample. Two already-probed palms (the comparison baseline) plus a
# dorsal shot as the guard test. Anything else in the directory is skipped
# unless --all is passed.
_SAMPLE = ("palm_right_test.jpg", "palm_left_test.jpg", "Back Hand.jpeg")

# -- THRESHOLDS (CLAUDE.md Working Style #4) --
#
# _RELIABLE_UNANIMOUS_RATE = 0.80 -- a primitive is tagged RELIABLE when at least
#   this share of populated hands gave it a UNANIMOUS N-of-N majority. 0.80
#   allows one flaky hand in five before the tag flips. Judgment call, NOT
#   measured. SCOPE GUARD: this report's tagging only; nothing in the production
#   path reads it. TUNING NOTE: set it from the observed distribution once the
#   set is large enough to have one.
_RELIABLE_UNANIMOUS_RATE = 0.80
#
# _MIN_HANDS_FOR_TAG = 5 -- below this many populated hands the RELIABLE/FLAKY
#   tag is reported as UNDETERMINED rather than asserted. A 2-hand sample cannot
#   distinguish a flaky primitive from an unlucky one, and stamping a tag on it
#   would manufacture exactly the false confidence this set exists to avoid.
#   SCOPE GUARD/TUNING NOTE: as above.
_MIN_HANDS_FOR_TAG = 5

doc = load_doctrine()

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("directory", nargs="?", default=str(DEFAULT_DIR),
                    help=f"directory of images (default: {DEFAULT_DIR})")
parser.add_argument("--all", action="store_true",
                    help="run EVERY image in the directory, not just the curated sample")
parser.add_argument("--n-runs", type=int, default=_N_RUNS,
                    help=f"self-consistency runs per image (default {_N_RUNS})")
args = parser.parse_args()

image_dir = Path(args.directory)
if not image_dir.is_dir():
    raise SystemExit(f"not a directory: {image_dir}")

found = sorted(p for p in image_dir.iterdir() if p.suffix.lower() in _IMAGE_EXT)
if args.all:
    images = found
    skipped = []
else:
    by_name = {p.name: p for p in found}
    images = [by_name[n] for n in _SAMPLE if n in by_name]
    skipped = [p for p in found if p.name not in _SAMPLE]

if not images:
    raise SystemExit(f"no images to run in {image_dir} (found {len(found)}; sample={_SAMPLE})")

n_runs = args.n_runs
max_calls = len(images) * (1 + n_runs)
print(f"[batch] {len(images)} image(s), N={n_runs} -> up to {max_calls} GPT-4o calls "
      f"({len(images)} gate + {len(images) * n_runs} classify). Skipping {len(skipped)}.",
      flush=True)

lines = []
w = lines.append
results = {}
errors = {}
calls_made = 0

try:
    # =========================================================================
    # Run
    # =========================================================================
    t0 = time.time()
    for path in images:
        print(f"[batch] {path.name} ...", flush=True)
        try:
            r = classify_hand(path.read_bytes(), label=path.stem, n_runs=n_runs)
            results[path.name] = r
            calls_made += 1 + len(r.runs)
            print(f"[batch] {path.name}: dominant={r.dominant_type} conf={r.confidence} "
                  f"flag={'SET' if r.quality_flag else 'None'}", flush=True)
        except Exception as exc:                    # noqa: BLE001 - report, never swallow
            errors[path.name] = f"{type(exc).__name__}: {exc}"
            calls_made += 1
            print(f"[batch] {path.name}: ERROR {exc}", flush=True)
    elapsed = round(time.time() - t0, 1)

    populated = {k: v for k, v in results.items() if v.quality_flag is None}
    flagged = {k: v for k, v in results.items() if v.quality_flag is not None}

    # =========================================================================
    # Per-run re-derive + single-primitive counterfactual (NO API cost)
    # =========================================================================
    def as_primitives(flat):
        """`_derive_type` reads only ['value'] on each path — build that shape."""
        return {p: {"value": v} for p, v in flat.items()}

    per_run_types = {}      # image -> [type per run]
    deciding = Counter()    # primitive -> times a single swap flipped the type
    tested_swaps = Counter()
    flip_examples = []

    for name, r in populated.items():
        flats = [_flatten(p, doc) for p in r.runs]
        types = [_derive_type(as_primitives(f), doc)[0] for f in flats]
        per_run_types[name] = types
        for i in range(len(flats)):
            for j in range(len(flats)):
                if i == j or types[i] == types[j]:
                    continue
                for pth in flats[i]:
                    if flats[i][pth] == flats[j][pth]:
                        continue
                    swapped = dict(flats[i])
                    swapped[pth] = flats[j][pth]
                    tested_swaps[pth] += 1
                    new_type = _derive_type(as_primitives(swapped), doc)[0]
                    if new_type != types[i]:
                        deciding[pth] += 1
                        if len(flip_examples) < 12:
                            flip_examples.append(
                                (name, pth, flats[i][pth], flats[j][pth], types[i], new_type))

    # =========================================================================
    # Report
    # =========================================================================
    w("# Cheirognomy consistency set — batch aggregation")
    w("")
    w(f"- Batch over `agent/cheirognomy/vlm_arm.py` · N = **{n_runs}** runs per image at "
      f"temperature **{_TEMPERATURE}**")
    w(f"- Directory: `{image_dir.relative_to(_REPO_ROOT).as_posix()}` · "
      f"{len(found)} image(s) present, **{len(images)} run**, {len(skipped)} skipped "
      f"({'--all' if args.all else 'curated sample'})")
    w(f"- **API spent: {calls_made} GPT-4o calls** "
      f"({len(results) + len(errors)} gate + {sum(len(r.runs) for r in results.values())} classify) "
      f"· wall time {elapsed}s")
    w(f"- Thresholds: floor `{_DOMINANCE_FLOOR}`, margin `{_DOMINANCE_MARGIN}`, "
      f"RELIABLE at `{_RELIABLE_UNANIMOUS_RATE}` unanimity, tag suppressed below "
      f"`{_MIN_HANDS_FOR_TAG}` hands")
    if skipped:
        w(f"- Skipped (not in the curated sample): " + ", ".join(f"`{p.name}`" for p in skipped))
    w("")
    w(f"**SAMPLE-BEFORE-SCALE.** n = **{len(populated)} populated hand(s)** — far below the "
      f"`{_MIN_HANDS_FOR_TAG}` needed to assert a stability tag. Everything below is the "
      "aggregation MACHINERY proven on a sample, plus whatever the sample happens to show. "
      "Distributions are real; the RELIABLE/FLAKY adjudication is NOT yet earned.")
    w("")

    # --- outcome roll-up -----------------------------------------------------
    w("## 1. Per-image outcome")
    w("")
    w("| image | outcome | dominant_type | confidence | per-run type (re-derived, no API cost) |")
    w("|---|---|---|---|---|")
    for path in images:
        name = path.name
        if name in errors:
            w(f"| `{name}` | **ERROR** | — | — | {errors[name]} |")
        elif name in flagged:
            w(f"| `{name}` | **quality_flag** | _none — mutually exclusive_ | — | "
              f"_0 classify runs (gate stopped it)_ |")
        else:
            r = results[name]
            pr = per_run_types[name]
            varies = " **(varies)**" if len(set(pr)) > 1 else ""
            w(f"| `{name}` | populated | `{r.dominant_type}` | {r.confidence} | "
              f"{', '.join(pr)}{varies} |")
    w("")
    for name, r in flagged.items():
        w(f"- `{name}` quality_flag: `{r.quality_flag}`")
    for name, msg in errors.items():
        w(f"- `{name}` error: `{msg}`")
    if flagged or errors:
        w("")

    # --- per-primitive stability --------------------------------------------
    w("## 2. Per-primitive stability across the set (findings 1–3 adjudication data)")
    w("")
    w("Same-image agreement for each primitive, pooled over every populated hand. "
      "`unanimous` = the share of hands where all N runs agreed.")
    w("")
    if populated:
        dist = defaultdict(Counter)
        for r in populated.values():
            for pth, p in r.primitives.items():
                votes = int(round(p["agreement"] * p["runs_total"]))
                key = "TIE" if p["tied"] else f"{votes}/{p['runs_total']}"
                dist[pth][key] += 1
        buckets = sorted({k for c in dist.values() for k in c},
                         key=lambda s: (s == "TIE", s), reverse=True)
        w("| primitive | " + " | ".join(buckets) + " | unanimous | tag |")
        w("|---|" + "---|" * len(buckets) + "---|---|")
        for pth in dist:
            c = dist[pth]
            total = sum(c.values())
            unan = c.get(f"{n_runs}/{n_runs}", 0)
            rate = unan / total if total else 0.0
            if len(populated) < _MIN_HANDS_FOR_TAG:
                tag = f"UNDETERMINED (n={len(populated)})"
            else:
                tag = "RELIABLE" if rate >= _RELIABLE_UNANIMOUS_RATE else "**FLAKY**"
            w(f"| `{pth}` | " + " | ".join(str(c.get(b, 0)) for b in buckets)
              + f" | {unan}/{total} ({rate:.0%}) | {tag} |")
        w("")
        w(f"Provisional read at n={len(populated)} (NOT a verdict — shown so the shape is "
          "visible while the set is grown):")
        prov_flaky = [p for p in dist
                      if (dist[p].get(f"{n_runs}/{n_runs}", 0) / sum(dist[p].values()))
                      < _RELIABLE_UNANIMOUS_RATE]
        w("")
        w("- would-be FLAKY: " + (", ".join(f"`{p}`" for p in prov_flaky) or "_none_"))
        w("- would-be RELIABLE: "
          + (", ".join(f"`{p}`" for p in dist if p not in prov_flaky) or "_none_"))
        w("")
    else:
        w("_No populated hand — nothing to pool._")
        w("")

    # --- type distribution ---------------------------------------------------
    w("## 3. Dominant-type distribution and mixed-rate")
    w("")
    if populated:
        tc = Counter(r.dominant_type for r in populated.values())
        n_pop = len(populated)
        n_mixed = tc.get(doc.fallback_type, 0)
        w("| dominant_type | count | share |")
        w("|---|---|---|")
        for t, c in tc.most_common():
            w(f"| `{t}` | {c} | {c / n_pop:.0%} |")
        w("")
        w(f"**mixed-rate: {n_mixed}/{n_pop} ({n_mixed / n_pop:.0%})**")
        w("")
        if n_mixed:
            w("Of the mixed results — sparse-tie (top two inside the margin, i.e. the "
              "denominator asymmetry blocked separation) vs genuine low-signal (top below the "
              "floor, i.e. nothing matched well enough):")
            w("")
            w("| image | top type | top score | 2nd type | 2nd score | gap | classification |")
            w("|---|---|---|---|---|---|---|")
            for name, r in populated.items():
                if r.dominant_type != doc.fallback_type:
                    continue
                rk = r.type_ranking
                (t1, s1, _, _), (t2, s2, _, _) = rk[0], rk[1]
                gap = round(s1 - s2, 3)
                if s1 < _DOMINANCE_FLOOR:
                    cls = "**genuine low-signal** (top < floor)"
                elif gap < _DOMINANCE_MARGIN:
                    cls = "**SPARSE-TIE** (inside margin)"
                else:
                    cls = "fingers-disagree (S5)"
                w(f"| `{name}` | `{t1}` | {s1} | `{t2}` | {s2} | {gap} | {cls} |")
            w("")
    else:
        w("_No populated hand._")
        w("")

    # --- deciding flips ------------------------------------------------------
    w("## 4. Which primitive is the DECIDING flip?")
    w("")
    w("Counterfactual, computed with the authored `_derive_type` and **zero API cost**: for each "
      "pair of runs that re-derive to different types, swap ONE primitive at a time from run B "
      "into run A and re-derive. A primitive is 'deciding' when that single swap flips the type.")
    w("")
    if deciding or tested_swaps:
        w("| primitive | deciding flips | swaps tested | rate |")
        w("|---|---|---|---|")
        for pth, tested in tested_swaps.most_common():
            d = deciding.get(pth, 0)
            w(f"| `{pth}` | **{d}** | {tested} | {d / tested:.0%} |")
        w("")
        if flip_examples:
            w("Worked examples:")
            w("")
            for name, pth, va, vb, ta, tb in flip_examples:
                w(f"- `{name}` · `{pth}`: `{va}` -> `{vb}` flips `{ta}` -> `{tb}`")
            w("")
    else:
        w("_No pair of runs re-derived to different types on this sample — no flip to attribute. "
          "This is itself a stability result, not a gap in the machinery._")
        w("")

    # --- blind label template ------------------------------------------------
    with TEMPLATE_PATH.open("w", newline="", encoding="utf-8") as fh:
        cw = csv.writer(fh)
        cw.writerow(["image", "human_dominant_type", "human_confidence", "notes"])
        for path in images:
            cw.writerow([path.name, "", "", ""])

    w("## 5. Blind-label template (arm 2)")
    w("")
    w(f"Written to `{TEMPLATE_PATH.relative_to(_REPO_ROOT).as_posix()}` — "
      f"{len(images)} row(s), all label cells EMPTY.")
    w("")
    w("**Fill it BEFORE reading sections 1–4 of this report.** The template is the human "
      "reference arm; labelling after seeing the machine's answer produces agreement that "
      "measures anchoring, not accuracy. That is the AI-reviewing-AI failure this set exists to "
      "avoid (Working Style #5, #9).")
    w("")
    w(f"`human_dominant_type` is one of: "
      + ", ".join(f"`{t}`" for t in sorted(doc.types)) + f", `{doc.fallback_type}`. "
      "`human_confidence` is your own free scale — record it, it is not compared numerically.")
    w("")
    w("```csv")
    w("image,human_dominant_type,human_confidence,notes")
    for path in images:
        w(f"{path.name},,,")
    w("```")
    w("")
    w("NOTE ON THE CEILING: even fully filled, this set is a CONSISTENCY reference, not a truth "
      "oracle — §1 of the rubric says so explicitly. It measures whether the arm agrees with a "
      "human reader, not whether either is right about Cheiro.")
    w("")

    # --- cost projection -----------------------------------------------------
    w("## 6. Projected at-scale cost")
    w("")
    w(f"Per image: **1 gate call + {n_runs} classify calls = {1 + n_runs} GPT-4o calls** "
      f"(a gate-rejected image costs 1 and stops).")
    w("")
    w("The `3 x (#hands)` figure in the sizing request counts only the classify calls — the gate "
      f"is a real GPT-4o call too, so the true multiplier is **{1 + n_runs}x**, "
      f"{(1 + n_runs) / n_runs:.2f}x higher than a classify-only estimate.")
    w("")
    w("| directory size | classify calls | gate calls | **total GPT-4o calls** |")
    w("|---|---|---|---|")
    for size in (3, 10, 25, 50, 100):
        w(f"| {size} hands | {size * n_runs} | {size} | **{size * (1 + n_runs)}** |")
    w("")
    w(f"This run: {len(images)} image(s) -> {calls_made} calls actually spent.")
    w(f"Reaching the `{_MIN_HANDS_FOR_TAG}`-hand tag floor needs "
      f"**{_MIN_HANDS_FOR_TAG * (1 + n_runs)} calls**; a 25-hand set needs "
      f"**{25 * (1 + n_runs)}**. No external data was pulled — the set is in-repo images only.")
    w("")

    w("## 7. Status")
    w("")
    w(f"- populated: {sorted(populated)} · quality-flagged: {sorted(flagged)} · "
      f"errored: {sorted(errors)}")
    w("- No commit — awaiting RATIFIED.")
    w("- Nothing here measures CORRECTNESS. Same-image agreement is model determinism at "
      f"temperature {_TEMPERATURE}; the human arm in §5 is the only non-machine signal, and it "
      "is unfilled.")
    w("")

except Exception:                                   # noqa: BLE001 - never lose a paid run
    w("")
    w("## BATCH CRASHED after spending API calls")
    w("")
    w("```")
    w(traceback.format_exc())
    w("```")
    w("")
    raise
finally:
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[batch] report -> {REPORT_PATH}", flush=True)

sys.exit(1 if errors else 0)
