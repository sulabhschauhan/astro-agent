"""
THROWAWAY AUDIT SCRIPT. Not permanent, not imported by anything, safe to
delete after the report is read. Answers ONE question: of the 100 units
in data/domain_tags_bphs.json, which were tagged from TEXT versus from
TITLE, and what would a proper text re-read of the title-inferred ones
cost?

NO LLM CALLS. NO OpenAI/Anthropic API. NO subagents. Reads two existing
JSON artifacts plus the human-transcribed PASS_LOG comments already
committed in scripts/build_domain_tags.py; does no writing to any data
artifact or product code.

Run with: PYTHONIOENCODING=utf-8 python scripts/audit_tag_coverage.py
"""

import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
CHAPTER_INDEX_PATH = REPO_ROOT / "data" / "chapter_index_bphs.json"
DOMAIN_TAGS_PATH = REPO_ROOT / "data" / "domain_tags_bphs.json"
RUNS_DIR = REPO_ROOT / "diagnostics" / "runs"
LATEST_PATH = REPO_ROOT / "diagnostics" / "latest_run.md"

DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]+")  # settled-safe range, per CLAUDE.md


def strip_devanagari(text):
    """Byte-for-byte the same normalisation as agent/astro/payload_builder.py's
    strip_devanagari, reproduced here so this throwaway script has zero
    import dependency on product code."""
    text = DEVANAGARI_RE.sub("", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def devanagari_char_pct(text):
    if not text:
        return 0.0
    dv_chars = sum(len(m) for m in DEVANAGARI_RE.findall(text))
    return 100.0 * dv_chars / len(text)


try:
    import tiktoken
    _ENC = tiktoken.get_encoding("cl100k_base")
    TOKEN_METHOD = "tiktoken cl100k_base"

    def count_tokens(text):
        return len(_ENC.encode(text))
except ImportError:
    TOKEN_METHOD = "chars/4 fallback (tiktoken NOT available)"

    def count_tokens(text):
        return len(text) // 4


# ---------------------------------------------------------------------
# Hand-transcribed from scripts/build_domain_tags.py's own PASS_LOG list
# and its inline pass-comments (lines ~100-1572), verbatim facts, not
# inferred. Each unit_id appears in exactly one pass. Self-checked below
# against data/chapter_index_bphs.json's actual 100 unit_ids.
#
# READ_METHOD values, taken directly from the script's own notes:
#   FULL_PRIOR_READ         -- pass 0, re-tagged from a full read already
#                              done earlier in that conversation; no new
#                              reading in this run, but the underlying
#                              judgment was formed from full source text.
#   FULL                    -- unit's segments read in full, this run.
#   TRUNCATED_DUMP          -- each segment capped ~320 chars (header +
#                              main clause); still real corpus text, not
#                              a title.
#   REPRESENTATIVE_SAMPLED  -- one sibling segment (or one chapter in the
#                              same cluster) read in full/truncated, its
#                              domain profile then applied to structurally
#                              near-identical segments without individually
#                              reading each one. Disclosed in the script's
#                              own comments (ch62/ch63/ch64, ch81).
# NONE of the 9 passes describe tagging any unit from its title alone.
# ---------------------------------------------------------------------
PASS_UNITS = {
    "0": ("FULL_PRIOR_READ", [
        "bphs1_ch21", "bphs1_ch24", "bphs1_ch34", "bphs1_ch27", "bphs1_ch43",
        "bphs2_ch66", "bphs1_ch4", "bphs2_ch83",
    ]),
    "1": ("FULL", [
        "bphs1_frontmatter", "bphs1_ch1", "bphs1_ch2", "bphs1_ch3", "bphs1_ch5",
    ]),
    "2": ("FULL", [
        "bphs1_ch8", "bphs1_ch10", "bphs1_ch15", "bphs1_ch22", "bphs1_ch23",
        "bphs1_ch28", "bphs1_ch37", "bphs1_ch40", "bphs1_ch42", "bphs1_gap38",
        "bphs1_backmatter",
        "bphs2_ch65", "bphs2_ch67", "bphs2_ch68", "bphs2_ch69", "bphs2_ch71",
        "bphs2_ch75", "bphs2_ch85", "bphs2_ch86", "bphs2_ch87", "bphs2_ch88",
        "bphs2_ch89", "bphs2_ch90", "bphs2_ch94", "bphs2_ch95", "bphs2_ch96",
        "bphs2_ch97", "bphs2_gap91",
    ]),
    "3": ("TRUNCATED_DUMP", [
        "bphs1_ch6", "bphs1_ch7", "bphs1_ch9", "bphs1_ch11", "bphs1_ch12",
        "bphs1_ch13", "bphs1_ch14", "bphs1_ch16", "bphs1_ch17", "bphs1_ch18",
        "bphs1_ch19", "bphs1_ch20", "bphs1_ch25", "bphs1_ch26", "bphs1_ch29",
    ]),
    "4": ("TRUNCATED_DUMP", [
        "bphs1_ch30", "bphs1_ch31", "bphs1_ch32", "bphs1_ch33", "bphs1_ch35",
        "bphs1_ch36", "bphs1_ch39", "bphs1_ch41", "bphs1_ch44", "bphs1_ch45",
    ]),
    "5": ("TRUNCATED_DUMP", ["bphs2_frontmatter"] + [f"bphs2_ch{n}" for n in range(46, 61)]),
    "6a": ("FULL", ["bphs2_ch61"]),
    "6b": ("REPRESENTATIVE_SAMPLED", ["bphs2_ch62", "bphs2_ch63", "bphs2_ch64"]),
    "7": ("TRUNCATED_DUMP", [
        "bphs2_ch70", "bphs2_ch72", "bphs2_ch73", "bphs2_ch74", "bphs2_ch76",
        "bphs2_ch77", "bphs2_ch78", "bphs2_ch79",
    ]),
    "8a": ("TRUNCATED_DUMP", ["bphs2_ch80", "bphs2_ch82", "bphs2_ch84", "bphs2_ch92", "bphs2_ch93"]),
    "8b": ("REPRESENTATIVE_SAMPLED", ["bphs2_ch81"]),
}

DOMAINS_16 = [
    "career", "marriage", "wealth", "children", "health", "education",
    "longevity", "travel", "property", "parents", "siblings",
    "spirituality", "enemies_conflict", "timing_dasha",
    "technique_method", "planetary_nature",
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    lines = []
    p = lines.append

    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%dT%H%M%SZ")

    chapter_index = load_json(CHAPTER_INDEX_PATH)
    domain_tags = load_json(DOMAIN_TAGS_PATH)

    ci_units = {u["unit_id"]: u for u in chapter_index["units"]}
    dt_units = {u["unit_id"]: u for u in domain_tags["units"]}
    ci_ids = set(ci_units)
    dt_ids = set(dt_units)

    # ---- self-check: hand-transcribed PASS_UNITS must exactly cover the
    # real 100-unit corpus. Abort loudly, write nothing, if not. ----
    pass_of_unit = {}
    read_method_of_unit = {}
    for pass_label, (method, uids) in PASS_UNITS.items():
        for uid in uids:
            if uid in pass_of_unit:
                print(f"FATAL: unit_id {uid!r} appears in both pass "
                      f"{pass_of_unit[uid]!r} and {pass_label!r} -- PASS_UNITS "
                      f"transcription error. Aborting, no report written.")
                sys.exit(1)
            pass_of_unit[uid] = pass_label
            read_method_of_unit[uid] = method

    pass_ids = set(pass_of_unit)
    if pass_ids != ci_ids:
        missing = ci_ids - pass_ids
        extra = pass_ids - ci_ids
        print("FATAL: PASS_UNITS transcription does not match "
              "data/chapter_index_bphs.json's 100 unit_ids.")
        print(f"  missing from PASS_UNITS ({len(missing)}): {sorted(missing)}")
        print(f"  in PASS_UNITS but not in chapter_index ({len(extra)}): {sorted(extra)}")
        print("Aborting, no report written.")
        sys.exit(1)
    if dt_ids != ci_ids:
        missing = ci_ids - dt_ids
        extra = dt_ids - ci_ids
        print("FATAL: data/domain_tags_bphs.json unit_ids do not match "
              "data/chapter_index_bphs.json's 100 unit_ids.")
        print(f"  missing from domain_tags ({len(missing)}): {sorted(missing)}")
        print(f"  extra in domain_tags ({len(extra)}): {sorted(extra)}")
        print("Aborting, no report written.")
        sys.exit(1)

    # ---- per-segment confidence rollup per unit ----
    seg_by_unit = {}
    for s in domain_tags["segments"]:
        seg_by_unit.setdefault(s["unit_id"], []).append(s)

    conf_counts = {}
    for uid in ci_ids:
        segs = seg_by_unit.get(uid, [])
        n_high = sum(1 for s in segs if s["confidence"] == "high")
        n_low = sum(1 for s in segs if s["confidence"] == "low")
        n_other = sum(1 for s in segs if s["confidence"] not in ("high", "low"))
        conf_counts[uid] = (n_high, n_low, n_other, len(segs))

    all_conf_values = {s["confidence"] for s in domain_tags["segments"]}

    # ---- token / char measurements from raw chapter_index text ----
    raw_tok = {}
    stripped_tok = {}
    raw_chars = {}
    dv_pct = {}
    for uid, u in ci_units.items():
        text = u.get("text") or ""
        raw_tok[uid] = count_tokens(text)
        stripped = strip_devanagari(text)
        stripped_tok[uid] = count_tokens(stripped)
        raw_chars[uid] = len(text)
        dv_pct[uid] = devanagari_char_pct(text)

    corpus_raw_tok = sum(raw_tok.values())
    corpus_stripped_tok = sum(stripped_tok.values())

    # =====================================================================
    p("# Tag Coverage Audit -- TEXT_READ vs TITLE_INFERRED")
    p("")
    p(f"Generated: {now.isoformat()}")
    p(f"Token counting method: {TOKEN_METHOD}")
    p(f"Inputs: `data/chapter_index_bphs.json` (100 units), "
      f"`data/domain_tags_bphs.json` ({domain_tags['segment_count']} segments, "
      f"{len(dt_units)} units)")
    p("")
    p("## Prediction (stated before running)")
    p("")
    p("Expected TITLE_INFERRED units to be the short Devanagari-heavy ritual "
      "chapters, a minority of tokens despite being ~30% of units. If they "
      "turned out token-heavy, that was to be reported loudly.")
    p("")

    # ---------------------------------------------------------------
    p("## HEADLINE FINDING -- the requested field does not exist")
    p("")
    p("`data/domain_tags_bphs.json` segments carry exactly one distinguishing "
      f"field: `confidence`, values observed = `{sorted(all_conf_values)}` "
      "(no `med`, despite the task brief's assumption of high/med/low). "
      "Unit records carry no confidence or provenance field at all. Neither "
      "field records TEXT_READ vs TITLE_INFERRED, and `confidence` does not "
      "line up with that axis either -- it is a domain-judgment-quality "
      "signal, and per `scripts/build_domain_tags.py`'s own inline pass "
      "comments, `low` is assigned for at least two different reasons: "
      "(a) genuine uncertainty in a domain call made from full text, and "
      "(b) the segment was read via a truncated dump rather than in full.")
    p("")
    p("Going further, up the actual authoring record "
      "(`scripts/build_domain_tags.py`'s module docstring + its own "
      "`PASS_LOG`, lines ~13-38 and ~1543-1572): every one of the 9 tagging "
      "passes describes reading real corpus text -- full, truncated-dump "
      "(~320 chars/segment), or representative-sampling of one segment's "
      "read applied to structurally identical siblings within the SAME "
      "unit/cluster. Pass 5's own note states this explicitly: "
      "\"confirmed timing_dasha as the mandatory cross-cutting tag for this "
      "whole cluster by direct reading of ch46-ch60's actual content "
      "(**not assumed from titles alone**)\". No pass anywhere describes "
      "tagging a unit from `title_raw` alone.")
    p("")
    p("**Per this task's own instruction (\"If NO field distinguishes them, "
      "say so and STOP -- do not guess, do not infer from title "
      "similarity\"): STOPPING on the TEXT_READ/TITLE_INFERRED split. "
      "It does not exist in this artifact. Zero of the 100 units are "
      "TITLE_INFERRED.**")
    p("")
    p("Sections 1-4 below are therefore reported against the nearest "
      "signal the artifact's own build record actually carries -- "
      "`READ_METHOD` (FULL_PRIOR_READ / FULL / TRUNCATED_DUMP / "
      "REPRESENTATIVE_SAMPLED), hand-transcribed from `PASS_LOG` and "
      "self-checked below to cover all 100 units exactly once -- plus the "
      "real `confidence` field. **This is not the requested TEXT_READ vs "
      "TITLE_INFERRED split; it is reported instead of guessing, and is "
      "labelled as a substitute throughout.**")
    p("")
    p("Self-check: PASS_UNITS transcription covers all 100 unit_ids exactly "
      "once, matching `chapter_index_bphs.json` and `domain_tags_bphs.json` "
      "-- PASS.")
    p("")

    # ---------------------------------------------------------------
    p("## 1. Coverage split (substitute axis: READ_METHOD)")
    p("")
    method_counts = {}
    for uid in ci_ids:
        method_counts[read_method_of_unit[uid]] = method_counts.get(read_method_of_unit[uid], 0) + 1
    p("| READ_METHOD | unit count |")
    p("|---|---|")
    for m in ["FULL", "FULL_PRIOR_READ", "TRUNCATED_DUMP", "REPRESENTATIVE_SAMPLED"]:
        p(f"| {m} | {method_counts.get(m, 0)} |")
    p("")
    p("Per-unit detail:")
    p("")
    p("| unit_id | title | segments | n_high | n_low | domains | READ_METHOD | pass |")
    p("|---|---|---|---|---|---|---|---|")
    for uid in sorted(ci_ids, key=lambda x: (x.split("_")[0], ci_units[x].get("chapter_number") is None, ci_units[x].get("chapter_number") or 0, x)):
        u = ci_units[uid]
        title = u.get("title_raw") or f"({u.get('kind', 'untitled')})"
        n_high, n_low, n_other, n_segs = conf_counts[uid]
        domains = ", ".join(dt_units[uid]["domains"]) or "(none)"
        p(f"| {uid} | {title} | {n_segs} | {n_high} | {n_low} | {domains} | "
          f"{read_method_of_unit[uid]} | {pass_of_unit[uid]} |")
    p("")

    # ---------------------------------------------------------------
    p("## 2. The re-read bill (substitute axis, since TITLE_INFERRED is empty)")
    p("")
    p("Reported per READ_METHOD group instead of TEXT_READ/TITLE_INFERRED. "
      "Figures are tiktoken cl100k_base counts on `chapter_index_bphs.json`'s "
      "raw `text` field (Devanagari included) and on that same text after "
      "`strip_devanagari`.")
    p("")
    p("| READ_METHOD | units | raw tokens | stripped tokens | raw/stripped ratio |")
    p("|---|---|---|---|---|")
    for m in ["FULL", "FULL_PRIOR_READ", "TRUNCATED_DUMP", "REPRESENTATIVE_SAMPLED"]:
        uids = [u for u in ci_ids if read_method_of_unit[u] == m]
        if not uids:
            continue
        r = sum(raw_tok[u] for u in uids)
        s = sum(stripped_tok[u] for u in uids)
        ratio = (r / s) if s else float("nan")
        p(f"| {m} | {len(uids)} | {r} | {s} | {ratio:.2f} |")
    r_all = corpus_raw_tok
    s_all = corpus_stripped_tok
    p(f"| **ALL 100 UNITS** | 100 | {r_all} | {s_all} | {(r_all / s_all):.2f} |")
    p("")
    p("There is no TITLE_INFERRED row: nothing to re-read, because nothing "
      "was tagged from title. The REPRESENTATIVE_SAMPLED row (4 units: "
      "bphs2_ch62/ch63/ch64/ch81) is the closest thing to reduced-effort "
      "tagging that exists, and even that was extended from a full/"
      "truncated read of a structurally-identical sibling in the same "
      "cluster, not from a title.")
    p("")

    # ---------------------------------------------------------------
    p("## 3. Devanagari concentration")
    p("")
    p("Per unit, Devanagari characters as % of total raw characters. Top 10:")
    p("")
    top10 = sorted(ci_ids, key=lambda u: -dv_pct[u])[:10]
    p("| unit_id | title | raw chars | Devanagari % | READ_METHOD |")
    p("|---|---|---|---|---|")
    for uid in top10:
        u = ci_units[uid]
        title = u.get("title_raw") or f"({u.get('kind', 'untitled')})"
        p(f"| {uid} | {title} | {raw_chars[uid]} | {dv_pct[uid]:.1f}% | "
          f"{read_method_of_unit[uid]} |")
    p("")
    corpus_dv_pct = 100.0 * sum(
        len(m) for u in ci_ids for m in DEVANAGARI_RE.findall(ci_units[u]["text"] or "")
    ) / sum(raw_chars.values())
    p(f"Corpus-wide Devanagari share of raw characters: {corpus_dv_pct:.1f}%.")
    p("")

    # ---------------------------------------------------------------
    p("## 4. Selection bloat by domain")
    p("")
    p("Domain tokens are `domain_tags_bphs.json`'s own `per_domain[domain].tokens` "
      "field (word-count `approx_tokens` on Devanagari-stripped segment text -- "
      "NOT tiktoken; this is the same unit production selection already uses, "
      "reused as-is rather than recomputed). Corpus total is the sum of all "
      "100 units' `tokens` field in the same artifact.")
    p("")
    corpus_dt_tokens = sum(u["tokens"] for u in dt_units.values())
    p(f"Corpus total (domain_tags `tokens` field, all 100 units): {corpus_dt_tokens}")
    p("")
    p("| domain | total tokens | % of corpus | FULL+FULL_PRIOR tokens | "
      "TRUNCATED_DUMP tokens | REPRESENTATIVE_SAMPLED tokens |")
    p("|---|---|---|---|---|---|")
    domain_totals = []
    for d in DOMAINS_16:
        total = sum(u["per_domain"][d]["tokens"] for u in dt_units.values())
        full_tok = sum(
            u["per_domain"][d]["tokens"] for uid, u in dt_units.items()
            if read_method_of_unit[uid] in ("FULL", "FULL_PRIOR_READ")
        )
        trunc_tok = sum(
            u["per_domain"][d]["tokens"] for uid, u in dt_units.items()
            if read_method_of_unit[uid] == "TRUNCATED_DUMP"
        )
        rep_tok = sum(
            u["per_domain"][d]["tokens"] for uid, u in dt_units.items()
            if read_method_of_unit[uid] == "REPRESENTATIVE_SAMPLED"
        )
        domain_totals.append((d, total, full_tok, trunc_tok, rep_tok))
    for d, total, full_tok, trunc_tok, rep_tok in sorted(domain_totals, key=lambda x: -x[1]):
        pct = 100.0 * total / corpus_dt_tokens if corpus_dt_tokens else 0.0
        p(f"| {d} | {total} | {pct:.1f}% | {full_tok} | {trunc_tok} | {rep_tok} |")
    p("")

    # ---------------------------------------------------------------
    p("## Deviation from prediction")
    p("")
    p("The prediction assumed a TITLE_INFERRED category would exist and "
      "asked to flag loudly if it turned out token-heavy. The actual "
      "deviation is larger than that: **the category does not exist at "
      "all** -- 0 of 100 units, 0 tokens. Every unit's tag was assigned "
      "from real corpus text, at one of three read depths (full, "
      "truncated-dump, or representative-sampling from a sibling segment's "
      "read). The REPRESENTATIVE_SAMPLED group (4 units, "
      f"{sum(raw_tok[u] for u in ci_ids if read_method_of_unit[u] == 'REPRESENTATIVE_SAMPLED')} "
      "raw tokens) is the only group tagged without a full per-segment "
      "read, and it is a small share of the corpus, consistent with the "
      "original prediction's shape even though the labelled category "
      "itself was wrong.")
    p("")

    report_text = "\n".join(lines) + "\n"

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_path = RUNS_DIR / f"{ts}_audit_tag_coverage.md"
    with open(run_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    shutil.copyfile(run_path, LATEST_PATH)

    print(f"Wrote {run_path}")
    print(f"Copied to {LATEST_PATH}")
    print("")
    print("=" * 70)
    print("SUMMARY (see diagnostics/latest_run.md for full tables)")
    print("=" * 70)
    print("TEXT_READ vs TITLE_INFERRED: NO SUCH FIELD EXISTS. 0/100 units "
          "were tagged from title alone -- confirmed from build_domain_tags.py's "
          "own PASS_LOG, every unit was read from real text (full, truncated, "
          "or representative-sampled from a sibling read).")
    print(f"Corpus raw tokens (tiktoken): {corpus_raw_tok}")
    print(f"Corpus Devanagari-stripped tokens (tiktoken): {corpus_stripped_tok}")
    print(f"Corpus-wide Devanagari share of raw chars: {corpus_dv_pct:.1f}%")


if __name__ == "__main__":
    main()
