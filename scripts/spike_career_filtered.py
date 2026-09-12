"""
THROWAWAY SPIKE -- career-question filtering method proof.

Builds two payload arms (FULL vs FILTERED) for a fixed career question over
BPHS-1 chapters 21/24/34, using a hardcoded chart and a deterministic
regex-only filter over chapter 24's 113 verse segments. Chapters 21 and 34
are passed whole in both arms (too small to filter, per prior spike).

This script does NOT call any LLM. It only builds payloads and reports the
filter funnel. The actual A/B subagent runs are done separately (Claude Code
subagents), and their JSON outputs are checked with `verify` mode below.

Usage:
  python scripts/spike_career_filtered.py build --out-dir <dir>
  python scripts/spike_career_filtered.py verify --arm full|filtered --json <path> --out-dir <dir>

No book JSON or index is modified -- data/chapter_index_bphs.json and
diagnostics/_spike2_fact_block.txt are read-only inputs.
"""
import argparse
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAPTER_INDEX_PATH = os.path.join(REPO_ROOT, "data", "chapter_index_bphs.json")
FACT_BLOCK_PATH = os.path.join(REPO_ROOT, "diagnostics", "_spike2_fact_block.txt")

# ---------------------------------------------------------------------------
# SETTLED chart (hardcoded, do NOT recompute). key = house N, value = house
# where house N's lord sits. Deliberately includes 7:12 and 11:5 -- the two
# pairs previously verified to be silently dropped without the step-4 rescue.
# ---------------------------------------------------------------------------
CHART_LORD_HOUSE = {1: 1, 2: 2, 3: 3, 4: 4, 5: 2, 6: 6, 7: 12, 8: 12, 9: 9, 10: 4, 11: 5, 12: 6}
ASCENDANT = "Sagittarius"

QUESTION = "What does my chart say about my career?"

DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]+")

ORDINAL_WORDS = {
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6,
    "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10, "eleventh": 11, "twelfth": 12,
}
ASCENDANT_ALIASES = ["ascendant", "asecndant", "lagna"]

# OCR-tolerant "lord" alternation, per task spec: lord|Jord|lor..|100
LORD_WORD = r"(?:lord|Jord|lor..|100)"


def _digit_variants(n):
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(n if n < 20 else n % 10, "th")
    if 10 <= n % 100 <= 20:
        suffix = "th"
    return [f"{n}{suffix}", str(n)]


def house_ref_variants(n):
    """All textual forms this house number can appear as in the source text."""
    variants = list(_digit_variants(n))
    for word, val in ORDINAL_WORDS.items():
        if val == n:
            variants.append(word)
    if n == 1:
        variants.extend(ASCENDANT_ALIASES)
    return variants


def _all_house_ref_alternatives():
    alts = []
    for n in range(1, 13):
        alts.extend(house_ref_variants(n))
    # longest-first so e.g. "11th" isn't shadowed by a stray "1"
    alts = sorted(set(alts), key=len, reverse=True)
    return "|".join(re.escape(a) for a in alts)


HOUSE_REF_ALT = _all_house_ref_alternatives()
_HOUSE_REF_TO_NUM = {}
for _n in range(1, 13):
    for _v in house_ref_variants(_n):
        _HOUSE_REF_TO_NUM[_v.lower()] = _n

RELATION_RE = re.compile(
    rf"\b({HOUSE_REF_ALT})\b\s*{LORD_WORD}\w*\b.{{0,200}}?\bin\s+the\s+\b({HOUSE_REF_ALT})\b",
    re.IGNORECASE | re.DOTALL,
)

VERSE_SPLIT_RE = re.compile(r"\n\s*(\d{1,3})\.\s")


def resolve_house_num(ref_text):
    return _HOUSE_REF_TO_NUM.get(ref_text.strip().lower())


def strip_devanagari(text):
    text = DEVANAGARI_RE.sub("", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def approx_tokens(text):
    """Word-count based approximation, consistent across all counts in this spike."""
    return len(text.split())


def load_chapter_text(chapter_number):
    with open(CHAPTER_INDEX_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    for unit in data["units"]:
        if unit.get("chapter_number") == chapter_number:
            return unit["text"]
    raise ValueError(f"chapter {chapter_number} not found in {CHAPTER_INDEX_PATH}")


def load_fact_block():
    with open(FACT_BLOCK_PATH, "r", encoding="utf-8") as f:
        return f.read()


def split_ch24_segments(clean_text):
    matches = list(VERSE_SPLIT_RE.finditer(clean_text))
    segments = []  # list of (verse_num_str, text)
    if not matches:
        return segments
    # leading preamble (chapter title) gets folded into the first verse segment
    lead = clean_text[: matches[0].start()]
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(clean_text)
        seg_text = clean_text[start:end]
        if i == 0:
            seg_text = lead + seg_text
        verse_num = m.group(1)
        segments.append((verse_num, seg_text.strip()))
    return segments


def assign_segment_ids(segments):
    """verse_num -> id, disambiguating duplicates (OCR-repeated verse numbers)."""
    counts = {}
    ids = []
    for verse_num, _text in segments:
        counts[verse_num] = counts.get(verse_num, 0) + 1
        suffix = "" if counts[verse_num] == 1 else chr(ord("a") + counts[verse_num] - 2)
        ids.append(f"ch24_v{verse_num}{suffix}")
    return ids


def extract_relations(text):
    rels = []
    for m in RELATION_RE.finditer(text):
        a = resolve_house_num(m.group(1))
        b = resolve_house_num(m.group(2))
        if a is not None and b is not None:
            rels.append((a, b))
    return rels


def mentions_lord(text, house_num):
    pat = re.compile(
        rf"\b({'|'.join(re.escape(v) for v in house_ref_variants(house_num))})\b\s*{LORD_WORD}\w*\b",
        re.IGNORECASE,
    )
    return bool(pat.search(text))


def run_filter(seg_ids, seg_texts, chart):
    relations_by_id = {sid: extract_relations(txt) for sid, txt in zip(seg_ids, seg_texts)}
    text_by_id = dict(zip(seg_ids, seg_texts))

    step2_kept = {
        sid for sid, rels in relations_by_id.items()
        if any(chart.get(f) == t for f, t in rels)
    }
    step3_added = {
        sid for sid, rels in relations_by_id.items()
        if len(rels) == 0
    } - step2_kept
    kept_after_3 = step2_kept | step3_added

    rescue_report = {}
    step4_added_total = set()
    for house_num in range(1, 13):
        target = chart[house_num]
        pair = (house_num, target)
        covered = any(
            pair in relations_by_id[sid] for sid in kept_after_3
        )
        if covered:
            rescue_report[house_num] = {"pair": pair, "covered": True, "added": []}
            continue
        rescued = {
            sid for sid in seg_ids
            if mentions_lord(text_by_id[sid], house_num) and sid not in kept_after_3
        }
        rescue_report[house_num] = {"pair": pair, "covered": False, "added": sorted(rescued)}
        step4_added_total |= rescued

    final_kept = kept_after_3 | step4_added_total

    return {
        "relations_by_id": relations_by_id,
        "step2_kept": step2_kept,
        "step3_added": step3_added,
        "kept_after_3": kept_after_3,
        "rescue_report": rescue_report,
        "step4_added_total": step4_added_total,
        "final_kept": final_kept,
    }


def build_payload(blocks):
    """blocks: list of (bracket_id, text) -> single payload string."""
    parts = []
    for bid, text in blocks:
        parts.append(f"[{bid}]\n{text}")
    return "\n\n".join(parts)


def cmd_build(args):
    os.makedirs(args.out_dir, exist_ok=True)

    ch21_raw = load_chapter_text(21)
    ch24_raw = load_chapter_text(24)
    ch34_raw = load_chapter_text(34)

    ch21_clean = strip_devanagari(ch21_raw)
    ch24_clean = strip_devanagari(ch24_raw)
    ch34_clean = strip_devanagari(ch34_raw)

    segments = split_ch24_segments(ch24_clean)
    seg_ids = assign_segment_ids(segments)
    seg_texts = [t for _v, t in segments]

    filt = run_filter(seg_ids, seg_texts, CHART_LORD_HOUSE)

    id_to_text = dict(zip(seg_ids, seg_texts))

    full_blocks = [("ch21", ch21_clean)] + [(sid, id_to_text[sid]) for sid in seg_ids] + [("ch34", ch34_clean)]
    filtered_ids = [sid for sid in seg_ids if sid in filt["final_kept"]]
    filtered_blocks = [("ch21", ch21_clean)] + [(sid, id_to_text[sid]) for sid in filtered_ids] + [("ch34", ch34_clean)]

    full_payload = build_payload(full_blocks)
    filtered_payload = build_payload(filtered_blocks)

    fact_block = load_fact_block()

    tokens = {
        "ch21": approx_tokens(ch21_clean),
        "ch34": approx_tokens(ch34_clean),
        "ch24_full": approx_tokens(ch24_clean),
        "ch24_filtered": approx_tokens("\n\n".join(id_to_text[s] for s in filtered_ids)),
        "fact_block": approx_tokens(fact_block),
        "full_arm_payload": approx_tokens(full_payload),
        "filtered_arm_payload": approx_tokens(filtered_payload),
    }

    # write payloads + fact block + funnel report to out_dir (scratchpad, not repo)
    with open(os.path.join(args.out_dir, "payload_full.txt"), "w", encoding="utf-8") as f:
        f.write(full_payload)
    with open(os.path.join(args.out_dir, "payload_filtered.txt"), "w", encoding="utf-8") as f:
        f.write(filtered_payload)
    with open(os.path.join(args.out_dir, "fact_block.txt"), "w", encoding="utf-8") as f:
        f.write(fact_block)

    funnel = {
        "chart": CHART_LORD_HOUSE,
        "ascendant": ASCENDANT,
        "question": QUESTION,
        "ch24_segment_count": len(seg_ids),
        "all_segment_ids": seg_ids,
        "step2_kept_count": len(filt["step2_kept"]),
        "step2_kept_ids": sorted(filt["step2_kept"]),
        "step3_added_count": len(filt["step3_added"]),
        "step3_added_ids": sorted(filt["step3_added"]),
        "kept_after_3_count": len(filt["kept_after_3"]),
        "rescue_report": {
            str(k): {"pair": list(v["pair"]), "covered": v["covered"], "added": v["added"], "added_count": len(v["added"])}
            for k, v in filt["rescue_report"].items()
        },
        "step4_added_total_count": len(filt["step4_added_total"]),
        "step4_added_total_ids": sorted(filt["step4_added_total"]),
        "final_kept_count": len(filt["final_kept"]),
        "final_kept_ids": sorted(filt["final_kept"], key=lambda s: seg_ids.index(s)),
        "dropped_count": len(seg_ids) - len(filt["final_kept"]),
        "dropped_ids": [s for s in seg_ids if s not in filt["final_kept"]],
        "tokens": tokens,
        "relations_by_id": {k: v for k, v in filt["relations_by_id"].items()},
    }
    with open(os.path.join(args.out_dir, "funnel.json"), "w", encoding="utf-8") as f:
        json.dump(funnel, f, ensure_ascii=False, indent=2, default=list)

    print(f"ch24 segments: {len(seg_ids)}")
    print(f"step2 kept (matched chart): {len(filt['step2_kept'])}")
    print(f"step3 added (no relation, fail-safe): {len(filt['step3_added'])}")
    print(f"kept after step3: {len(filt['kept_after_3'])}")
    print(f"step4 rescue added: {len(filt['step4_added_total'])}")
    print(f"final kept: {len(filt['final_kept'])} / {len(seg_ids)}")
    print(f"tokens: {json.dumps(tokens)}")
    print(f"wrote payloads + funnel.json to {args.out_dir}")


def cmd_verify(args):
    with open(os.path.join(args.out_dir, "funnel.json"), "r", encoding="utf-8") as f:
        funnel = json.load(f)
    all_ids = set(funnel["all_segment_ids"]) | {"ch21", "ch34"}
    if args.arm == "full":
        valid_ids = all_ids
    else:
        valid_ids = set(funnel["final_kept_ids"]) | {"ch21", "ch34"}

    payload_file = os.path.join(args.out_dir, f"payload_{args.arm}.txt")
    with open(payload_file, "r", encoding="utf-8") as f:
        payload_text = f.read()
    block_texts = {}
    for m in re.finditer(r"\[([A-Za-z0-9_]+)\]\n(.*?)(?=\n\n\[[A-Za-z0-9_]+\]\n|\Z)", payload_text, re.DOTALL):
        block_texts[m.group(1)] = m.group(2).strip()

    with open(args.json, "r", encoding="utf-8") as f:
        raw = f.read()
    result = json.loads(raw)

    report = {"arm": args.arm, "claims": []}
    for claim in result.get("claims", []):
        cited = claim.get("segment_ids", [])
        entry = {"statement": claim.get("statement"), "segment_ids": cited, "checks": []}
        for sid in cited:
            valid = sid in valid_ids
            text = block_texts.get(sid, "<NOT FOUND IN PAYLOAD TEXT>")
            entry["checks"].append({"id": sid, "valid_for_arm": valid, "text": text})
        report["claims"].append(entry)

    invalid = [c["id"] for claim in report["claims"] for c in claim["checks"] if not c["valid_for_arm"]]
    report["invalid_ids"] = invalid
    report["claim_count"] = len(report["claims"])

    out_path = os.path.join(args.out_dir, f"verify_{args.arm}_{os.path.basename(args.json)}")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps({"claim_count": report["claim_count"], "invalid_ids": invalid}, ensure_ascii=False))
    print(f"wrote {out_path}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build")
    b.add_argument("--out-dir", required=True)

    v = sub.add_parser("verify")
    v.add_argument("--arm", choices=["full", "filtered"], required=True)
    v.add_argument("--json", required=True)
    v.add_argument("--out-dir", required=True)

    args = ap.parse_args()
    if args.cmd == "build":
        cmd_build(args)
    elif args.cmd == "verify":
        cmd_verify(args)


if __name__ == "__main__":
    main()
