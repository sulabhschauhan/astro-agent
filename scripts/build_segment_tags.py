"""
PERMANENT BUILD SCRIPT. Builds `data/segment_tags_bphs_career3.json`, a
per-segment classification layer over the 135 segments already addressed by
`data/segment_index_bphs_career3.json`.

WHY THIS EXISTS: handing an interpreter all 135 segments at once produces
near-arbitrary citation selection (measured: across 6 identical runs only 2
segments were cited by all 3 runs of an arm, 8+ cited exactly once). The fix
is to narrow the candidate set deterministically before a question is ever
asked. But naive narrowing by placement (lord/house/sign) would silently
drop qualifier and exception rules, since those name no placement at all.
This script tags every segment with a `rule_type` so a future retriever can
narrow to `specific_placement` matches for the chart at hand while ALWAYS
keeping every `general_qualifier` / `exception` / `definitional` segment
regardless of chart. It does not do any narrowing itself -- it only builds
the tag layer that narrowing will later read.

SCHEMA v2 (this revision) -- ENTITY-LEVEL, not relational. v1 tagged
fine-grained relationships (lord-of-house-X IN house-Y) and failed: 28 of
121 `specific_placement` segments came back all-null because OCR damage or
segmenter granularity had merged 2-4 verses into one segment_id, and no
SINGLE relationship could represent a segment naming several placements;
62 of 121 were low confidence. The relationship precision was never the
filter's job -- the filter only needs to DISCARD OBVIOUS NON-MATCHES; an
LLM still reads every surviving segment and makes the real judgement. v2
therefore records WHICH chart entities a segment talks about (houses,
planets, signs, ascendant scope, topics), not how they relate to each
other. This also makes the schema portable to other classical texts
(Phaladeepika, Saravali, Jataka Parijata, ...) without change, since none
of it is BPHS-specific. See `data/palm_rules/README.md`-style precedent:
same "narrow without dropping exceptions" shape as the palm relational-tag
work, applied to a text corpus instead of a vision pipeline.

Does NOT modify `data/segment_index_bphs_career3.json`, any book JSON, or
any existing index, and does NOT re-segment. Makes no OpenAI/Anthropic API
call. Tagging itself is done by Claude Code subagents (fresh, batch-
isolated, no chart/question context) invoked by the orchestrator between
this script's two modes -- this file only prepares subagent inputs and
validates/merges their outputs. Writes at most two things:
`data/segment_tags_bphs_career3.json` (only if every mandatory validation
check in `merge` mode passes) and `diagnostics/latest_run.md` (always,
overwrite mode, per the project's diagnostic-output convention). If
validation fails, the report explains exactly what failed and the tags
artifact is NOT written.

USAGE (two-phase, orchestrator drives the subagent calls in between):

  python scripts/build_segment_tags.py prep [--batches 4] [--work-dir DIR]
      Reads the segment index, strips Devanagari (settled safe, 6-run A/B),
      splits into N batches, and writes one self-contained prompt file plus
      one input-data file per batch under --work-dir. The orchestrator
      sends each prompt file's contents verbatim to a fresh subagent and
      tells it to Write its JSON result to the matching output file path
      named in the prompt.

  python scripts/build_segment_tags.py merge [--batches 4] [--work-dir DIR]
      Reads the N batch output files, validates them (id coverage, allowed
      rule_type values, house range, closed planet/sign/topic lists), and
      -- only if every hard check passes -- writes the merged tags artifact
      and the full report (topic vocabulary usage, rule_type counts vs v1,
      no-entity headline count, house/planet distributions, ascendant_scope
      listing, the always-keep bucket, a targeted re-check of the 6 v1
      failures, a simulated filter pass against a hardcoded chart fact
      block, and measured token spend from the actual prompt/output files
      on disk).

CLOSED VOCABULARIES (stated here, not just in the subagent prompt, so a
future reader of `merge`'s validation code sees the exact contract):
  rule_type: specific_placement | general_qualifier | exception |
             definitional | narrative | unusable
  planets:   Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu
  signs / ascendant_scope: Aries, Taurus, Gemini, Cancer, Leo, Virgo,
             Libra, Scorpio, Sagittarius, Capricorn, Aquarius, Pisces
  houses:    list of int 1-12 (a segment naming more than 8 is FLAGGED in
             the report as over-broad, not auto-rejected -- see check 5)
  topics:    TOPIC_VOCABULARY below (proposed this run, capped at 15,
             printed in the report for approval before anything downstream
             relies on it)
Any value outside these closed sets fails validation and blocks the write
(fail loudly -- a wrong structured condition silently misfiles a rule and
it is never retrieved again).

RETIRED FROM v1 (do not reintroduce): lord_of_house, in_house, aspect_from,
in_sign, ascendant_sign, verse_hint, span_hint. v1 tried to encode WHICH
house a named planet/lord occupies; v2 only encodes THAT a house/planet/
sign was named, deliberately not distinguishing "the 4th lord" (a house
named as a lord-reference) from "in the 3rd" (a house named as a location)
-- both simply go in `houses`. This is the direct fix for the 28 all-null
segments: entity-level tagging does not require resolving a relationship,
only extracting the union of every house/planet/sign mentioned anywhere in
the segment's text, even across several bundled verses.
"""

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

try:
    import tiktoken

    _ENC = tiktoken.get_encoding("cl100k_base")
except Exception:  # pragma: no cover - tiktoken is expected to be installed
    _ENC = None

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO_ROOT / "data" / "segment_index_bphs_career3.json"
OUTPUT_PATH = REPO_ROOT / "data" / "segment_tags_bphs_career3.json"
DIAG_PATH = REPO_ROOT / "diagnostics" / "latest_run.md"
DEFAULT_WORK_DIR = REPO_ROOT / "diagnostics" / "_segment_tags_work"

TAGGER_VERSION = "segtag-2.0"

RULE_TYPES = [
    "specific_placement",
    "general_qualifier",
    "exception",
    "definitional",
    "narrative",
    "unusable",
]
ALWAYS_KEEP_TYPES = {"general_qualifier", "exception", "definitional"}

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
ENTITY_FIELDS = ["houses", "planets", "signs", "ascendant_scope", "topics"]
MAX_HOUSES_SOFT_LIMIT = 8

# Proposed this run from what is actually observed across the 135 BPHS
# career-chapter segments (bhava-lord placement effects, yoga chapter,
# planetary classification). Capped at 15 per the instructing prompt.
# PRINTED IN THE REPORT FOR APPROVAL -- treat as provisional until then.
TOPIC_VOCABULARY = [
    "wealth_finance",
    "career_profession",
    "marriage_spouse",
    "progeny_children",
    "father_paternal",
    "mother_maternal",
    "siblings",
    "health_longevity",
    "royal_status_fame",
    "character_conduct",
    "religion_spirituality",
    "education_learning",
    "yoga_combination",
    "planetary_classification",
    "general_method",
]

# v1 comparison baseline (this run's own predecessor), hardcoded so the
# report can diff against it without re-reading the old artifact.
V1_RULE_TYPE_COUNTS = {
    "specific_placement": 121,
    "general_qualifier": 8,
    "exception": 0,
    "definitional": 1,
    "narrative": 3,
    "unusable": 2,
}
V1_NO_ENTITY_COUNT = 28  # all-conditions-null specific_placement segments
V1_LOW_CONFIDENCE_COUNT = 62
V1_ALWAYS_KEEP_SEGMENTS = 9
V1_ALWAYS_KEEP_TOKENS = 3602

SANITY_CHECK_IDS = [
    "bphs1_ch24#36",
    "bphs1_ch34#5",
    "bphs1_ch34#19",
    "bphs1_ch24#76",
    "bphs1_ch21#5",
]

# The 6 segments v1's specific_placement pass returned entirely null for
# (report §4 of the v1 run). Re-checked here under the new entity schema.
V1_FAILED_IDS = [
    "bphs1_ch24#29",
    "bphs1_ch24#35",
    "bphs1_ch24#50",
    "bphs1_ch24#61",
    "bphs1_ch24#71",
    "bphs1_ch24#90",
]

# Hardcoded chart facts for the simulated-filter step (report §9), lifted
# verbatim from diagnostics/_spike2_fact_block.txt (Sulabh, born 6 Apr 1988,
# 00:30 IST, Calcutta) -- NOT recomputed here, per the instructing prompt.
CHART_ASCENDANT_SIGN = "Sagittarius"
# Houses occupied by a graha (from the fact block's PLANETARY POSITIONS
# block): Sun 4, Moon 12, Mars 2, Mercury 4, Jupiter 5, Venus 6, Saturn 1,
# Rahu 3, Ketu 9. This is the literal, unambiguous "house N" fact the block
# states -- houses 7, 8, 10, 11 are NOT occupied by any graha and are
# deliberately excluded (using "all 12 houses always exist" would make the
# house dimension match everything and filter nothing).
CHART_OCCUPIED_HOUSES = {1, 2, 3, 4, 5, 6, 9, 12}
# All 9 canonical grahas are present in every real chart by definition --
# this makes the "planets" filter dimension trivially true for ANY segment
# naming ANY planet. Kept literal (not narrowed to "planets in a notable
# dignity" or similar) because the instructing prompt says measure and
# report, not tune; the report calls this triviality out explicitly.
CHART_PLANETS = set(PLANETS)
# Signs occupied by a graha, plus the ascendant sign and Moon-sign (both
# already members of the occupied-sign set here, listed for completeness):
# Pisces(Sun,Mercury), Scorpio(Moon), Capricorn(Mars), Aries(Jupiter),
# Taurus(Venus), Sagittarius(Saturn, also Lagna), Aquarius(Rahu), Leo(Ketu).
CHART_SIGNS = {"Pisces", "Scorpio", "Capricorn", "Aries", "Taurus", "Sagittarius", "Aquarius", "Leo"}

DEVANAGARI_BLOCK_RE = re.compile(r"[ऀ-ॿ]")
BLANK_RUN_RE = re.compile(r"\n{3,}")


def strip_devanagari(text):
    """Remove Devanagari-block characters; collapse resulting blank-line runs.

    Settled safe by a 6-run A/B (CLAUDE.md task brief) -- character removal
    only, no other rewriting of the English text.
    """
    stripped = DEVANAGARI_BLOCK_RE.sub("", text)
    stripped = BLANK_RUN_RE.sub("\n\n", stripped)
    return stripped.strip()


def token_count(text):
    if _ENC is None:
        return None
    return len(_ENC.encode(text))


def load_index():
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def index_sha256():
    return hashlib.sha256(INDEX_PATH.read_bytes()).hexdigest()


def make_batches(segments, n_batches):
    """Split `segments` (already ordinal-ordered) into n_batches contiguous
    chunks as evenly as possible, e.g. 135/4 -> 34,34,34,33."""
    total = len(segments)
    base = total // n_batches
    remainder = total % n_batches
    batches = []
    idx = 0
    for i in range(n_batches):
        size = base + (1 if i < remainder else 0)
        batches.append(segments[idx: idx + size])
        idx += size
    return batches


PROMPT_TEMPLATE = """You are classifying {n} short passages from Brihat Parasara Hora Sastra
(BPHS), a classical Vedic astrology text, chapter unit(s) on the 10th house
(career). Each passage is a segment with a stable `segment_id`. You are
seeing ONLY this batch of {n} segments -- no chart, no question, no other
batch. Do not try to infer or use any chart context; classify each segment
purely on what it states.

TASK: for every segment, assign a `rule_type` and record WHICH chart
entities (houses, planets, signs) the segment names -- NOT how they relate
to each other. Do not try to resolve "the lord of the 4th" to which house
that lord sits in unless the text states the number directly; both a house
named as a lord-reference ("the 4th lord") and a house named as a location
("in the 3rd") go in the SAME `houses` list, undifferentiated.

RULE_TYPE VALUES (exactly one per segment):
  specific_placement  states a result for a named configuration (e.g. "the
                       10th lord in the 4th", "Saturn in the ascendant").
  general_qualifier    states a principle, method, or scaling rule with NO
                       specific placement (e.g. how strength is judged,
                       full/half/negligible effects, how to weigh multiple
                       results).
  exception            states a condition that REVERSES, weakens, or
                       overrides another rule ("unless", "however", "if
                       afflicted", "but if weak", "will not happen if...").
  definitional         defines a term or lists a classification (natural
                       benefics/malefics, house names, karakas, what a
                       given house/lord/karaka means).
  narrative            commentary, worked examples, translator notes,
                       chapter titles/headers, or text with no rule content.
  unusable             OCR damage too severe to classify with confidence.

ENTITIES to extract for EVERY segment (empty lists are fine and expected):
  houses           sorted list of ints 1-12 -- every house number the
                   segment mentions, in ANY role (lord-of or located-in).
                   If a bundled segment covers several verses, list every
                   house any of them names.
  planets          list, values ONLY from: {planets}
  signs            list, values ONLY from: {signs}
                   -- include a sign only when the segment names it
                   explicitly (not implied by a house number).
  ascendant_scope  list, values ONLY from the same 12 signs -- non-empty
                   ONLY if the segment's rule is stated to apply to one or
                   more SPECIFIC ascendants (e.g. "SAGITTARIUS ASCENDANT:
                   ..."). Empty list means the rule applies generally, to
                   any ascendant. This field is high-value and error-prone
                   -- get it right, do not guess it non-empty.
  topics           list, values ONLY from this CLOSED set (use as many as
                   genuinely apply, do not force one if none fit -- an
                   empty list is valid):
                   {topics}

ANTI-GUESSING RULE (unchanged from prior work on this corpus, enforce it):
Include an entity ONLY if the segment names it. Do NOT infer, do not
complete a pattern, do not resolve "the lord of that house" to a specific
number unless the number is stated. Where OCR damage makes a number
unreadable, omit it and mark the segment low confidence. Over-tagging is
the failure mode here -- pulling in irrelevant entities silently defeats
the whole point of filtering later. If in doubt, leave an entity out and
set confidence "low" rather than guess.

Give a short one-clause `note` per segment stating the reasoning.

INPUT ({n} segments, Devanagari already stripped):
{payload}

OUTPUT: write STRICT JSON ONLY (no markdown fences, no commentary) to this
exact file path, using the Write tool:
{output_path}

JSON shape (segments array MUST contain exactly these {n} segment_ids,
each exactly once, no invented ids, same order as input is fine):
{{"segments": [{{"segment_id": "...", "rule_type": "...",
  "houses": [], "planets": [], "signs": [], "ascendant_scope": [],
  "topics": [], "confidence": "high", "note": "..."}}, ...]}}

After writing the file, reply with ONLY one short confirmation line: batch
segment count written, and how many were tagged confidence="low". Do not
paste the JSON back into your reply.
"""


def build_prompt(batch, output_path):
    payload_lines = []
    for seg in batch:
        payload_lines.append(f"### {seg['segment_id']}\n{strip_devanagari(seg['text'])}")
    payload = "\n\n".join(payload_lines)
    return PROMPT_TEMPLATE.format(
        n=len(batch),
        planets=", ".join(PLANETS),
        signs=", ".join(SIGNS),
        topics=", ".join(TOPIC_VOCABULARY),
        payload=payload,
        output_path=output_path,
    )


def cmd_prep(args):
    work_dir = Path(args.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    index = load_index()
    segments = index["segments"]
    batches = make_batches(segments, args.batches)

    print(f"Loaded {len(segments)} segments from {INDEX_PATH.name}")
    print(f"Splitting into {args.batches} batches, work dir: {work_dir}")

    for i, batch in enumerate(batches, start=1):
        output_path = work_dir / f"batch_{i}_output.json"
        prompt_path = work_dir / f"batch_{i}_prompt.txt"
        input_path = work_dir / f"batch_{i}_input.json"

        input_path.write_text(
            json.dumps(
                [{"segment_id": s["segment_id"], "text": strip_devanagari(s["text"])} for s in batch],
                ensure_ascii=False, indent=2,
            ),
            encoding="utf-8",
        )
        prompt_text = build_prompt(batch, str(output_path))
        prompt_path.write_text(prompt_text, encoding="utf-8")

        ids = [s["segment_id"] for s in batch]
        tc = token_count(prompt_text)
        print(f"  batch {i}: {len(batch)} segments ({ids[0]}..{ids[-1]}), "
              f"prompt tokens={tc if tc is not None else 'n/a (tiktoken missing)'} "
              f"-> {prompt_path.relative_to(REPO_ROOT)}")

    print("\nNext step (orchestrator): for each batch_i, send batch_i_prompt.txt's "
          "full text verbatim to a fresh subagent, then run `merge` once all "
          "batch_i_output.json files exist.")


def _validate_entry(seg_id, entry, errors, warnings):
    rule_type = entry.get("rule_type")
    if rule_type not in RULE_TYPES:
        errors.append(f"{seg_id}: invalid rule_type {rule_type!r}")

    for field in ENTITY_FIELDS:
        if field not in entry:
            errors.append(f"{seg_id}: missing field {field!r}")
        elif not isinstance(entry.get(field), list):
            errors.append(f"{seg_id}: {field}={entry.get(field)!r} is not a list")

    houses = entry.get("houses") or []
    if isinstance(houses, list):
        for h in houses:
            if not isinstance(h, int) or isinstance(h, bool) or not (1 <= h <= 12):
                errors.append(f"{seg_id}: houses contains invalid value {h!r} (must be int 1-12)")
        if len(houses) > MAX_HOUSES_SOFT_LIMIT:
            warnings.append(
                f"{seg_id}: houses has {len(houses)} entries ({sorted(houses)}) "
                f"> soft limit {MAX_HOUSES_SOFT_LIMIT} -- tag may be over-broad"
            )

    for field in ("planets",):
        for v in entry.get(field) or []:
            if v not in PLANETS:
                errors.append(f"{seg_id}: {field} contains {v!r}, not in closed planet list {PLANETS}")

    for field in ("signs", "ascendant_scope"):
        for v in entry.get(field) or []:
            if v not in SIGNS:
                errors.append(f"{seg_id}: {field} contains {v!r}, not in closed sign list {SIGNS}")

    for v in entry.get("topics") or []:
        if v not in TOPIC_VOCABULARY:
            errors.append(f"{seg_id}: topics contains {v!r}, not in proposed topic vocabulary")

    confidence = entry.get("confidence")
    if confidence not in ("high", "low"):
        errors.append(f"{seg_id}: invalid confidence {confidence!r}")


def cmd_merge(args):
    work_dir = Path(args.work_dir)
    index = load_index()
    segments = index["segments"]
    by_id = {s["segment_id"]: s for s in segments}
    expected_ids = set(by_id.keys())

    errors = []
    warnings = []
    all_entries = {}
    batch_output_files = []
    batch_prompt_files = []

    for i in range(1, args.batches + 1):
        output_path = work_dir / f"batch_{i}_output.json"
        prompt_path = work_dir / f"batch_{i}_prompt.txt"
        batch_output_files.append(output_path)
        batch_prompt_files.append(prompt_path)
        if not output_path.exists():
            errors.append(f"missing subagent output file: {output_path}")
            continue
        try:
            data = json.loads(output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{output_path}: invalid JSON ({e})")
            continue
        entries = data.get("segments")
        if not isinstance(entries, list):
            errors.append(f"{output_path}: top-level 'segments' is not a list")
            continue
        for entry in entries:
            seg_id = entry.get("segment_id")
            if seg_id is None:
                errors.append(f"{output_path}: entry missing segment_id")
                continue
            if seg_id in all_entries:
                errors.append(f"duplicate segment_id across batches: {seg_id}")
                continue
            all_entries[seg_id] = entry

    # Confidence normalization (same rationale as the v1 run): confidence
    # is not spelled out as a hard closed enum in the prompt the way
    # rule_type is, and subagents have previously produced a "medium"
    # value. Confidence doesn't drive rule_type or any entity list, so
    # values outside {"high","low"} are coerced to "low" (conservative
    # side) and recorded, never silently dropped.
    confidence_normalized = []
    for seg_id, entry in all_entries.items():
        original = entry.get("confidence")
        if original not in ("high", "low"):
            confidence_normalized.append((seg_id, original))
            entry["confidence"] = "low"

    got_ids = set(all_entries.keys())
    missing_ids = expected_ids - got_ids
    invented_ids = got_ids - expected_ids
    if missing_ids:
        errors.append(f"missing {len(missing_ids)} segment_ids: {sorted(missing_ids)}")
    if invented_ids:
        errors.append(f"invented {len(invented_ids)} segment_ids not in index: {sorted(invented_ids)}")

    for seg_id, entry in all_entries.items():
        _validate_entry(seg_id, entry, errors, warnings)

    if errors:
        write_failure_report(errors, warnings, batch_output_files)
        print(f"VALIDATION FAILED ({len(errors)} errors). See {DIAG_PATH.relative_to(REPO_ROOT)}. "
              f"Tags artifact NOT written.")
        raise SystemExit(1)

    # All hard checks passed -- merge, in original ordinal order. Houses
    # are sorted + de-duplicated on the way in (list identity doesn't
    # matter downstream, only membership).
    merged_segments = []
    for s in segments:
        entry = all_entries[s["segment_id"]]
        merged_segments.append({
            "segment_id": s["segment_id"],
            "ordinal": s["ordinal"],
            "rule_type": entry["rule_type"],
            "houses": sorted(set(entry.get("houses") or [])),
            "planets": sorted(set(entry.get("planets") or [])),
            "signs": sorted(set(entry.get("signs") or [])),
            "ascendant_scope": sorted(set(entry.get("ascendant_scope") or [])),
            "topics": sorted(set(entry.get("topics") or [])),
            "confidence": entry["confidence"],
            "note": entry.get("note", ""),
        })

    artifact = {
        "source_file": str(OUTPUT_PATH.relative_to(REPO_ROOT)).replace("\\", "/"),
        "generated_by": Path(__file__).name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_segment_index_sha256": index_sha256(),
        "tagger_version": TAGGER_VERSION,
        "tagger": "claude-code-subagent",
        "n_batches": args.batches,
        "segment_count": len(merged_segments),
        "topic_vocabulary": TOPIC_VOCABULARY,
        "segments": merged_segments,
    }
    OUTPUT_PATH.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)} ({len(merged_segments)} segments).")

    write_success_report(by_id, all_entries, batch_output_files, batch_prompt_files,
                          confidence_normalized, warnings)
    print(f"Wrote {DIAG_PATH.relative_to(REPO_ROOT)}.")


def write_failure_report(errors, warnings, batch_output_files):
    lines = []
    lines.append("# build_segment_tags.py -- VALIDATION FAILED")
    lines.append("")
    lines.append(f"Run: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append("Tags artifact NOT written. Errors:")
    lines.append("")
    for e in errors:
        lines.append(f"- {e}")
    if warnings:
        lines.append("")
        lines.append("Warnings (non-blocking, would still be reported on a clean run):")
        for w in warnings:
            lines.append(f"- {w}")
    lines.append("")
    lines.append("Batch output files checked:")
    for p in batch_output_files:
        lines.append(f"- {p} (exists={p.exists()})")
    DIAG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _fmt_list(vals):
    return ", ".join(str(v) for v in vals) if vals else "(none)"


def write_success_report(by_id, all_entries, batch_output_files, batch_prompt_files,
                          confidence_normalized=None, warnings=None):
    confidence_normalized = confidence_normalized or []
    warnings = warnings or []
    lines = []
    lines.append("# build_segment_tags.py -- run report (schema v2, entity-level)")
    lines.append("")
    lines.append(f"Run: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"Segments tagged: {len(all_entries)} / {len(by_id)}")
    lines.append(f"Closed planet list: {_fmt_list(PLANETS)}")
    lines.append(f"Closed sign list (also used for ascendant_scope): {_fmt_list(SIGNS)}")
    lines.append("")

    if confidence_normalized:
        lines.append(f"NOTE: {len(confidence_normalized)} segments arrived with a confidence value "
                      "outside the {high,low} spec, normalized to \"low\" (conservative side), not "
                      "re-tagged. Full list:")
        lines.append("")
        for seg_id, original in sorted(confidence_normalized):
            lines.append(f"- {seg_id}: {original!r} -> \"low\"")
        lines.append("")

    if warnings:
        lines.append(f"NOTE: {len(warnings)} soft warnings (check 5, >{MAX_HOUSES_SOFT_LIMIT} houses on "
                      "one segment) -- flagged, not auto-fixed, write proceeded:")
        lines.append("")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    # 1. Proposed topic vocabulary + per-topic counts.
    lines.append("## 1. Proposed closed topic vocabulary (APPROVAL NEEDED)")
    lines.append("")
    lines.append(f"{len(TOPIC_VOCABULARY)} topics (cap was 15), proposed from what is actually observed "
                  "in these 135 segments. Every segment's topics list was validated against exactly this "
                  "set (unknown topic values are a hard validation failure, per check 4).")
    lines.append("")
    lines.append("| topic | segment count |")
    lines.append("|---|---|")
    for topic in TOPIC_VOCABULARY:
        n = sum(1 for e in all_entries.values() if topic in (e.get("topics") or []))
        lines.append(f"| {topic} | {n} |")
    no_topic = sum(1 for e in all_entries.values() if not (e.get("topics") or []))
    lines.append(f"| *(no topic tagged)* | {no_topic} |")
    lines.append("")

    # 2. Counts per rule_type, vs v1.
    lines.append("## 2. Counts per rule_type (vs v1)")
    lines.append("")
    lines.append("| rule_type | v2 count | v2 low confidence | v1 count |")
    lines.append("|---|---|---|---|")
    for rt in RULE_TYPES:
        ids = [sid for sid, e in all_entries.items() if e["rule_type"] == rt]
        low = [sid for sid in ids if all_entries[sid]["confidence"] == "low"]
        lines.append(f"| {rt} | {len(ids)} | {len(low)} | {V1_RULE_TYPE_COUNTS.get(rt, 'n/a')} |")
    total_low = sum(1 for e in all_entries.values() if e["confidence"] == "low")
    lines.append(f"| **total** | **{len(all_entries)}** | **{total_low}** | **135** |")
    lines.append("")

    # 3. HEADLINE -- segments with no entities at all.
    lines.append("## 3. HEADLINE -- segments with NO entities (empty houses+planets+signs)")
    lines.append("")
    no_entity_ids = sorted(
        [sid for sid, e in all_entries.items()
         if not (e.get("houses") or []) and not (e.get("planets") or []) and not (e.get("signs") or [])],
        key=lambda sid: by_id[sid]["ordinal"],
    )
    lines.append(f"v2 count: {len(no_entity_ids)}  (v1 comparable failure count: {V1_NO_ENTITY_COUNT})")
    lines.append("")
    if not no_entity_ids:
        lines.append("None.")
    else:
        for sid in no_entity_ids:
            e = all_entries[sid]
            lines.append(f"### {sid}  [{e['rule_type']}, confidence={e['confidence']}]")
            lines.append(f"note: {e.get('note', '')}")
            lines.append("")
            lines.append("```")
            lines.append(strip_devanagari(by_id[sid]["text"]))
            lines.append("```")
            lines.append("")
    lines.append("")

    # 4. Distribution: houses per segment, planets per segment.
    lines.append("## 4. Entity-count distribution")
    lines.append("")
    lines.append("| houses tagged | segment count | planets tagged | segment count |")
    lines.append("|---|---|---|---|")
    house_buckets = {"0": 0, "1": 0, "2": 0, "3": 0, "4-8": 0, ">8": 0}
    planet_buckets = {"0": 0, "1": 0, "2": 0, "3": 0, "4-8": 0, ">8": 0}

    def bucket_key(n):
        if n == 0:
            return "0"
        if n == 1:
            return "1"
        if n == 2:
            return "2"
        if n == 3:
            return "3"
        if 4 <= n <= 8:
            return "4-8"
        return ">8"

    for e in all_entries.values():
        house_buckets[bucket_key(len(e.get("houses") or []))] += 1
        planet_buckets[bucket_key(len(e.get("planets") or []))] += 1
    for key in ("0", "1", "2", "3", "4-8", ">8"):
        lines.append(f"| {key} | {house_buckets[key]} | {key} | {planet_buckets[key]} |")
    lines.append("")

    # 5. ascendant_scope non-empty listing.
    lines.append("## 5. Segments with non-empty ascendant_scope (highest-value, most error-prone field)")
    lines.append("")
    scoped_ids = sorted(
        [sid for sid, e in all_entries.items() if e.get("ascendant_scope")],
        key=lambda sid: by_id[sid]["ordinal"],
    )
    lines.append(f"{len(scoped_ids)} segments.")
    lines.append("")
    if not scoped_ids:
        lines.append("None.")
    else:
        for sid in scoped_ids:
            e = all_entries[sid]
            lines.append(f"### {sid}  ascendant_scope: {_fmt_list(e['ascendant_scope'])}  "
                          f"[{e['rule_type']}, confidence={e['confidence']}]")
            lines.append(f"note: {e.get('note', '')}")
            lines.append("")
            lines.append("```")
            lines.append(strip_devanagari(by_id[sid]["text"]))
            lines.append("```")
            lines.append("")
    lines.append("")

    # 6. Confidence, vs v1.
    lines.append("## 6. Confidence (vs v1)")
    lines.append("")
    lines.append(f"v2 low confidence: {total_low} / {len(all_entries)}  "
                  f"(v1: {V1_LOW_CONFIDENCE_COUNT} / 135)")
    lines.append("")

    # 7. Targeted re-check of the 6 v1 failures.
    lines.append("## 7. Targeted re-check -- the 6 segments that failed in v1")
    lines.append("")
    for sid in V1_FAILED_IDS:
        if sid not in all_entries:
            lines.append(f"### {sid}  -- NOT FOUND in tagged output")
            lines.append("")
            continue
        e = all_entries[sid]
        lines.append(f"### {sid}")
        lines.append(f"rule_type: {e['rule_type']}  confidence: {e['confidence']}")
        lines.append(f"houses: {_fmt_list(e.get('houses'))}")
        lines.append(f"planets: {_fmt_list(e.get('planets'))}")
        lines.append(f"signs: {_fmt_list(e.get('signs'))}")
        lines.append(f"ascendant_scope: {_fmt_list(e.get('ascendant_scope'))}")
        lines.append(f"topics: {_fmt_list(e.get('topics'))}")
        lines.append(f"note: {e.get('note', '')}")
        lines.append("")
        if sid in by_id:
            lines.append("```")
            lines.append(strip_devanagari(by_id[sid]["text"]))
            lines.append("```")
        lines.append("")
    lines.append("")

    # 8. Always-keep bucket, re-confirmed vs v1.
    always_keep_ids = [sid for sid, e in all_entries.items() if e["rule_type"] in ALWAYS_KEEP_TYPES]
    always_keep_ids_ordered = sorted(always_keep_ids, key=lambda sid: by_id[sid]["ordinal"])
    bucket_stripped_text = "\n\n".join(strip_devanagari(by_id[sid]["text"]) for sid in always_keep_ids_ordered)
    bucket_tokens = token_count(bucket_stripped_text)

    lines.append("## 8. Always-keep bucket (general_qualifier + exception + definitional), vs v1")
    lines.append("")
    lines.append(f"v2: {len(always_keep_ids_ordered)} segments, "
                  f"{bucket_tokens if bucket_tokens is not None else 'n/a'} stripped tokens")
    lines.append(f"v1: {V1_ALWAYS_KEEP_SEGMENTS} segments, {V1_ALWAYS_KEEP_TOKENS} stripped tokens")
    if len(always_keep_ids_ordered) != V1_ALWAYS_KEEP_SEGMENTS:
        lines.append(f"MOVED from v1 -- rule_type assignment for one or more segments changed between "
                      f"runs (schema change does not itself change rule_type, so any delta here reflects "
                      f"genuine re-classification, not a schema artifact). IDs this run: "
                      f"{sorted(always_keep_ids_ordered)}")
    else:
        lines.append("Segment count unchanged from v1.")
    lines.append("")

    # 9. SIMULATED FILTER.
    lines.append("## 9. Simulated filter (hardcoded Sulabh chart facts, not recomputed)")
    lines.append("")
    lines.append(f"CHART_ASCENDANT_SIGN = {CHART_ASCENDANT_SIGN!r}")
    lines.append(f"CHART_OCCUPIED_HOUSES = {sorted(CHART_OCCUPIED_HOUSES)}  "
                  "(houses with a graha physically present, from PLANETARY POSITIONS -- NOT all 12)")
    lines.append(f"CHART_PLANETS = {sorted(CHART_PLANETS)}  "
                  "(all 9 canonical grahas -- every real chart has all 9, so this dimension is TRIVIALLY "
                  "true for any segment naming any planet; called out here, not tuned away)")
    lines.append(f"CHART_SIGNS = {sorted(CHART_SIGNS)}  (signs occupied by a graha, incl. Lagna/Moon sign)")
    lines.append("")
    lines.append("Filter rule: a segment survives if rule_type is in the always-keep set, OR its houses "
                  "intersect CHART_OCCUPIED_HOUSES, OR its planets intersect CHART_PLANETS, OR its signs "
                  "intersect CHART_SIGNS, OR CHART_ASCENDANT_SIGN is in its ascendant_scope.")
    lines.append("")

    def survives(e):
        if e["rule_type"] in ALWAYS_KEEP_TYPES:
            return True, "always-keep rule_type"
        reasons = []
        if set(e.get("houses") or []) & CHART_OCCUPIED_HOUSES:
            reasons.append("house overlap")
        if set(e.get("planets") or []) & CHART_PLANETS:
            reasons.append("planet overlap")
        if set(e.get("signs") or []) & CHART_SIGNS:
            reasons.append("sign overlap")
        if CHART_ASCENDANT_SIGN in (e.get("ascendant_scope") or []):
            reasons.append("ascendant_scope match")
        return (len(reasons) > 0), (", ".join(reasons) if reasons else "no match")

    survivor_ids = []
    for sid, e in all_entries.items():
        ok, _ = survives(e)
        if ok:
            survivor_ids.append(sid)
    survivor_ids = sorted(survivor_ids, key=lambda sid: by_id[sid]["ordinal"])
    survivor_text = "\n\n".join(strip_devanagari(by_id[sid]["text"]) for sid in survivor_ids)
    survivor_tokens = token_count(survivor_text)

    lines.append(f"Surviving: {len(survivor_ids)} / {len(all_entries)} segments, "
                 f"{survivor_tokens if survivor_tokens is not None else 'n/a'} stripped tokens "
                 f"(of {token_count(chr(10).join(strip_devanagari(s['text']) for s in by_id.values()))} total).")
    lines.append("")
    lines.append("Named-segment check (any drop is a filter failure, reported not tuned):")
    lines.append("")
    lines.append("| segment_id | survives | reason |")
    lines.append("|---|---|---|")
    for sid in ["bphs1_ch24#76", "bphs1_ch21#5", "bphs1_ch34#19", "bphs1_ch34#5", "bphs1_ch24#36"]:
        if sid not in all_entries:
            lines.append(f"| {sid} | N/A | not found in tagged output |")
            continue
        ok, reason = survives(all_entries[sid])
        lines.append(f"| {sid} | {'YES' if ok else '**NO -- FILTER FAILURE**'} | {reason} |")
    lines.append("")

    # 10. Actual token spend, measured from files on disk.
    lines.append("## 10. Actual token spend (measured, cl100k_base)")
    lines.append("")
    lines.append("Prompt files sent verbatim to subagents + their JSON output files, "
                  "as written to disk. Excludes orchestrator-side overhead (the Agent "
                  "tool call itself, the one-line confirmation replies).")
    lines.append("")
    lines.append("| batch | prompt tokens | output tokens |")
    lines.append("|---|---|---|")
    total_prompt_tok = 0
    total_output_tok = 0
    for i, (pp, op) in enumerate(zip(batch_prompt_files, batch_output_files), start=1):
        pt = token_count(pp.read_text(encoding="utf-8")) if pp.exists() else None
        ot = token_count(op.read_text(encoding="utf-8")) if op.exists() else None
        if pt is not None:
            total_prompt_tok += pt
        if ot is not None:
            total_output_tok += ot
        lines.append(f"| {i} | {pt if pt is not None else 'n/a'} | {ot if ot is not None else 'n/a'} |")
    lines.append(f"| **total** | **{total_prompt_tok}** | **{total_output_tok}** |")
    lines.append(f"| **grand total** | | **{total_prompt_tok + total_output_tok}** |")
    lines.append("")

    DIAG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_prep = sub.add_parser("prep", help="Build per-batch prompt + input files.")
    p_prep.add_argument("--batches", type=int, default=4)
    p_prep.add_argument("--work-dir", type=str, default=str(DEFAULT_WORK_DIR))
    p_prep.set_defaults(func=cmd_prep)

    p_merge = sub.add_parser("merge", help="Validate + merge subagent outputs, write artifact + report.")
    p_merge.add_argument("--batches", type=int, default=4)
    p_merge.add_argument("--work-dir", type=str, default=str(DEFAULT_WORK_DIR))
    p_merge.set_defaults(func=cmd_merge)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
