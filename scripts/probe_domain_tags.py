"""
THROWAWAY PROBE. Not product code. Writes diagnostics/runs/<timestamp>.md
and copies to diagnostics/latest_run.md. Modifies no book JSON, no index,
no payload artifact.

WHY: full-corpus measurement (see diagnostics/runs/20260905T071523Z.md)
showed the relation filter cuts only 4.6% of BPHS because it is a
within-chapter tool with no way to decide WHICH chapters/segments are
relevant to a given life-domain question (76.3% of kept tokens arrive via
the catch-all fail-safe). This probe asks: does closed-vocabulary DOMAIN
TAGGING at segment granularity solve the selection problem, on a hard
8-unit mix?

METHOD: Claude Code (this session) read every segment of all 8 units
directly in the conversation and hand-assigned domains/confidence/
unfittable per segment. Zero LLM/API calls were made by this script or
by any subprocess -- the tags below are a transcription of that manual
read, not a model output. Segmentation reuses the EXACT machinery
already used for the full-corpus measurement
(agent/astro/payload_builder.py: strip_devanagari + split_unit_segments,
the Arabic "\\n\\d{1,3}\\.\\s" VERSE_SPLIT_RE marker splitter) so segment
boundaries and token counts are directly comparable to that prior run's
numbers (e.g. bphs1_ch24's "kept via relation filter" = 5,878 tokens is
this same segmenter's output).

CLOSED DOMAIN VOCABULARY (exactly 16, no additions):
career, marriage, wealth, children, health, education, longevity,
travel, property, parents, siblings, spirituality, enemies_conflict,
timing_dasha, technique_method, planetary_nature.

Segment-level tags roll up to unit-level as the UNION of their
segments' domains. An empty domains list is NOT unfittable -- it means
the segment stays in scope for every question (narrative filler, meta
commentary). unfittable=True means real doctrine content that does not
fit any of the 16 domains (the drift detector).
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent.astro.payload_builder import strip_devanagari, split_unit_segments, approx_tokens  # noqa: E402

CHAPTER_INDEX_PATH = REPO_ROOT / "data" / "chapter_index_bphs.json"
RUNS_DIR = REPO_ROOT / "diagnostics" / "runs"
LATEST_PATH = REPO_ROOT / "diagnostics" / "latest_run.md"

TARGET_UNITS = [
    "bphs1_ch21", "bphs1_ch24", "bphs1_ch34", "bphs1_ch27",
    "bphs1_ch43", "bphs2_ch66", "bphs1_ch4", "bphs2_ch83",
]

DOMAINS_16 = {
    "career", "marriage", "wealth", "children", "health", "education",
    "longevity", "travel", "property", "parents", "siblings",
    "spirituality", "enemies_conflict", "timing_dasha",
    "technique_method", "planetary_nature",
}

# ---------------------------------------------------------------------
# HAND TAGS -- produced by Claude reading every segment directly in the
# conversation (see module docstring). Keyed by (unit_id, ordinal) ->
# (domains_tuple, confidence, unfittable). Ordinals not listed default to
# (domains=(), confidence="low", unfittable=False) -- should not happen,
# every real ordinal for every unit is covered below.
# ---------------------------------------------------------------------

TAGS = {}

def _set(unit, spec):
    """spec: {ordinal: (domains_tuple, confidence, unfittable)}"""
    for ordinal, v in spec.items():
        TAGS[(unit, ordinal)] = v

# bphs1_ch21 -- "Effects of The Tenth House". Predicted: single-domain (career).
_set("bphs1_ch21", {
    1: (("wealth",), "low", False),           # ch20 spillover tail (food by begging)
    2: ((), "high", False),                   # ch20 closing narrative + ch21 title banner
    3: ((), "high", False),                   # intro / lineage narrative, no doctrine yet
    4: (("career", "parents", "spirituality"), "high", False),
    5: (("career", "wealth"), "high", False),
    6: (("career",), "high", False),
    7: (("career",), "high", False),
    8: (("career", "wealth"), "high", False),
    9: (("career", "wealth"), "high", False),
    10: (("wealth", "spirituality", "education"), "medium", False),
    11: (("wealth", "career"), "high", False),
    12: (("career",), "medium", False),
    13: (("career",), "medium", False),
    14: (("career",), "high", False),
    15: (("career",), "high", False),
})

# bphs1_ch34 -- "Yoga Karakas". Benefic/malefic/yogakaraka determination
# method by ascendant. Prediction: technique_method, single-domain.
_set("bphs1_ch34", {
    1: (("technique_method",), "medium", False),   # ch33 spillover (Kemadruma) + ch34 intro
    2: (("technique_method",), "high", False),
    3: (("technique_method",), "high", False),
    4: (("technique_method",), "high", False),
    5: (("technique_method",), "high", False),
    6: (("technique_method",), "high", False),
    7: (("technique_method",), "high", False),
    8: (("technique_method",), "high", False),
    9: (("technique_method",), "high", False),
    10: (("technique_method",), "high", False),
    11: (("technique_method", "career"), "medium", False),  # incl. "become a king" Rajayoga
    12: (("technique_method",), "high", False),
})

# bphs1_ch4 -- "Zodiacal signs Described". Definitional. Prediction:
# planetary_nature / technique_method, not life-domain.
_set("bphs1_ch4", {
    1: (("planetary_nature", "health"), "high", False),   # sign descriptions + medical-astrology paragraph
    2: (("planetary_nature", "technique_method"), "high", False),  # sign descriptions + Nisheka Lagna calc
    3: (("technique_method",), "high", False),   # Gulika/Muhurta validation
    4: (("technique_method",), "high", False),   # Ayanamsa validation
    5: (("technique_method",), "high", False),   # Special Ascendants calc
})

# bphs2_ch66 -- "Ashtakavarga". Pure calculation tables. Prediction:
# technique_method, 0% life-domain content (matches full-corpus's 0%
# relation yield for this chapter).
_set("bphs2_ch66", {i: (("technique_method",), "high", False) for i in range(1, 11)})

# bphs2_ch83 -- title blank, whole_chapter (unsplittable, 1 segment).
# Entirely "lack of male issue" yogas + remedial measures.
_set("bphs2_ch83", {1: (("children", "spirituality"), "high", False)})

# bphs1_ch27 -- OCR-garbage title "i eee ren". Real title (recovered by
# reading): "Evaluation Of Strengths" (Shadbala/Digbala/Kaalabala/
# Naisargika/Ayana/Cheshta/Drig bala + Bhava Bala calculation methods).
# Entirely technique_method; a very minor final passage (slokas 39-40,
# "Eligibility To Issue Fruitful Predictions" -- astrologer's own
# qualifications) doesn't cleanly fit any of the 16 but is folded into
# ORD32's method-dominated segment rather than force-split; flagged in
# prose, not as a separate unfittable row (segmentation granularity).
_set("bphs1_ch27", {i: (("technique_method",), "high", False) for i in range(1, 33)})

# bphs1_ch43 -- title blank. Real title (recovered by reading): the
# Ayurdaya / longevity-determination chapter (Pindayu, Nisargayu, Amsayu
# methods + longevity-classification yogas). Genuinely the "longevity"
# domain throughout, not technique_method -- the calculation IS the
# domain content here, unlike ch27/ch66/ch4 where the calculation has no
# life-domain target.
_set("bphs1_ch43", {i: (("longevity",), "high", False) for i in range(1, 35)})

# bphs1_ch24 -- "Effects Of The Bhava Lords". House-lord-in-house census,
# 1st through 12th lord x 12 placements. THE HEADLINE unit. Segments are
# irregular multi-verse bundles because a large minority of BPHS's own
# printed verse-number markers use a comma or corrupted digit instead of
# "N. " and so are not split by VERSE_SPLIT_RE -- they are absorbed into
# the previous kept marker's segment (same generalised algorithm as the
# already-shipped full-corpus measurement; not a defect introduced here).
_set("bphs1_ch24", {
    1: (("health", "marriage"), "high", False),
    2: (("wealth", "education", "marriage", "spirituality"), "medium", False),
    3: (("wealth", "marriage"), "high", False),
    4: (("parents", "siblings"), "high", False),
    5: (("children",), "high", False),
    6: (("health", "enemies_conflict", "wealth", "marriage"), "low", False),
    7: (("marriage", "wealth", "health", "spirituality", "children"), "low", False),
    8: (("career", "wealth", "parents", "siblings"), "medium", False),
    9: (("wealth", "marriage"), "high", False),
    10: (("wealth", "health"), "high", False),
    11: (("wealth", "children", "siblings"), "medium", False),
    12: (("wealth", "marriage", "children"), "high", False),
    13: (("marriage", "spirituality"), "medium", False),
    14: (("wealth",), "high", False),
    15: (("wealth", "children"), "high", False),
    16: (("wealth", "enemies_conflict", "health"), "medium", False),
    17: (("marriage", "career", "parents"), "medium", False),
    18: (("wealth", "marriage", "siblings"), "high", False),
    19: (("wealth", "health", "spirituality"), "high", False),
    20: (("wealth", "marriage", "children"), "high", False),
    21: (("wealth", "health", "children", "spirituality"), "low", False),
    22: (("wealth",), "high", False),
    23: (("siblings", "wealth", "marriage"), "medium", False),
    24: (("children", "marriage"), "high", False),
    25: (("siblings", "wealth", "parents"), "medium", False),
    26: (("career",), "medium", False),
    27: (("parents", "marriage", "children", "wealth"), "low", False),
    28: (("wealth", "career", "parents", "marriage", "siblings"), "low", False),
    29: (("education", "property", "parents"), "medium", False),
    30: (("wealth", "parents", "health", "career", "spirituality"), "low", False),
    31: (("education", "property", "parents"), "medium", False),
    32: (("health", "parents", "children", "education", "spirituality"), "low", False),
    33: (("career", "wealth", "property", "health"), "medium", False),
    34: (("health", "parents"), "medium", False),
    35: (("wealth", "children", "education"), "medium", False),
    36: (("children", "wealth", "marriage", "career", "health"), "low", False),
    37: (("siblings",), "medium", False),
    38: (("parents", "wealth", "career", "property", "longevity"), "low", False),
    39: (("children",), "high", False),
    40: (("children",), "high", False),
    41: (("children",), "high", False),
    42: (("spirituality", "children"), "medium", False),
    43: (("children", "health"), "high", False),
    44: (("career", "education"), "medium", False),
    45: (("career", "wealth"), "high", False),
    46: (("education", "children", "wealth"), "medium", False),
    47: (("children", "health"), "high", False),
    48: (("health", "wealth", "career", "enemies_conflict"), "low", False),
    49: (("travel", "wealth", "health", "career"), "low", False),
    50: (("siblings",), "medium", False),
    51: (("parents", "wealth"), "medium", False),
    52: (("wealth", "children"), "medium", False),
    53: (("siblings", "wealth", "property", "health", "longevity"), "low", False),
    54: (("marriage", "children", "wealth", "career"), "low", False),
    55: (("health", "wealth", "marriage"), "medium", False),
    56: (("career",), "medium", False),
    57: (("career", "parents", "travel", "property"), "low", False),
    58: (("wealth", "children", "enemies_conflict"), "medium", False),
    59: ((), "medium", True),   # "spend on vices... torture living beings" -- moral/character, no domain fit
    60: (("marriage", "health", "wealth"), "medium", False),
    61: (("children", "marriage", "health", "spirituality"), "low", False),
    62: (("marriage", "children", "wealth", "career", "health"), "low", False),
    63: (("marriage", "health"), "high", False),
    64: (("marriage", "health", "wealth"), "medium", False),
    65: (("marriage", "career"), "medium", False),
    66: (("marriage", "spirituality", "wealth", "children"), "low", False),
    67: (("wealth", "children", "marriage"), "medium", False),
    68: (("wealth", "career", "marriage"), "medium", False),
    69: (("health", "spirituality"), "high", False),
    70: (("wealth", "health"), "high", False),
    71: (("siblings",), "high", False),
    72: (("parents", "property", "children", "longevity", "wealth", "education"), "low", False),
    73: (("enemies_conflict", "health", "longevity"), "medium", False),
    74: (("marriage", "career", "spirituality", "longevity", "property", "wealth"), "low", False),
    75: (("spirituality", "marriage", "wealth", "parents", "career"), "low", False),
    76: (("parents", "career", "property"), "medium", False),
    77: (("wealth", "longevity"), "medium", False),
    78: (("wealth", "longevity"), "medium", False),
    79: (("career", "wealth", "education", "enemies_conflict"), "medium", False),
    80: (("education", "wealth", "marriage", "children"), "medium", False),
    81: (("siblings", "wealth"), "high", False),
    82: (("property", "wealth", "parents"), "medium", False),
    83: (("children", "education", "wealth", "career", "parents", "enemies_conflict"), "low", False),
    84: (("marriage", "career", "parents"), "medium", False),
    85: (("career", "siblings", "parents", "property"), "low", False),
    86: (("wealth", "siblings", "parents", "property"), "low", False),
    87: (("career",), "high", False),
    88: (("wealth", "spirituality", "parents"), "medium", False),
    89: (("wealth", "spirituality", "siblings"), "medium", False),
    90: (("career", "wealth", "education", "health", "parents"), "low", False),
    91: (("siblings", "career"), "medium", False),
    92: (("parents", "property", "wealth"), "medium", False),
    93: (("education", "wealth", "children", "parents", "career", "enemies_conflict", "health"), "low", False),
    94: (("marriage", "spirituality"), "medium", False),
    95: (("longevity", "career"), "medium", False),
    96: (("career", "wealth", "children"), "medium", False),
    97: (("wealth", "children"), "high", False),
    98: (("wealth", "enemies_conflict", "career"), "medium", False),
    99: (("wealth", "career", "marriage"), "medium", False),
    100: (("wealth", "spirituality"), "high", False),
    101: (("career", "wealth", "siblings", "health"), "low", False),
    102: (("parents", "spirituality", "property", "children", "education"), "low", False),
    103: (("health", "travel", "enemies_conflict", "career"), "low", False),
    104: (("wealth", "marriage", "longevity"), "medium", False),
    105: (("career", "wealth"), "high", False),
    106: (("career", "spirituality"), "medium", False),
    107: (("wealth", "education"), "high", False),
    108: (("wealth", "marriage", "travel", "health", "education"), "low", False),
    109: (("wealth", "spirituality"), "high", False),
    110: (("siblings",), "high", False),
    111: (("parents", "property"), "high", False),
    112: (("children", "education"), "high", False),
    113: (("enemies_conflict", "marriage"), "medium", False),
    114: (("marriage", "education"), "medium", False),
    115: (("wealth", "longevity"), "medium", False),
    116: (("parents",), "low", False),
    117: (("career", "parents"), "medium", False),
    118: (("wealth", "children"), "medium", False),
    119: (("wealth", "health", "technique_method"), "low", False),
})


def load_units():
    with open(CHAPTER_INDEX_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return {u["unit_id"]: u for u in data["units"]}


def segment_unit(unit):
    clean = strip_devanagari(unit["text"])
    segs = split_unit_segments(clean)
    if not segs:
        return [(1, clean)]
    return [(i, text) for i, (_num, text, _start) in enumerate(segs, start=1)]


def main():
    units = load_units()
    missing = [u for u in TARGET_UNITS if u not in units]
    report = []
    report.append("# probe_domain_tags.py -- domain tagging feasibility probe")
    report.append("")
    report.append("Generated: %s" % datetime.now(timezone.utc).isoformat())
    report.append("")
    report.append(
        "Method: Claude Code read every segment of all 8 units directly in "
        "this conversation and hand-assigned domains/confidence/unfittable. "
        "This script makes ZERO OpenAI/Anthropic calls and spawns ZERO "
        "subagents -- it only re-derives segmentation (identical machinery "
        "to the already-shipped full-corpus measurement) and rolls up the "
        "hand-assigned tags embedded in its own TAGS dict."
    )
    report.append("")
    if missing:
        report.append("## FAILURE: missing unit_id(s) in chapter index: %s" % missing)
        write_reports(report)
        return

    report.append("## Prediction (stated before hand-tagging)")
    report.append("")
    report.append(
        "ch24 expected to carry roughly 8-12 of the 16 domains (a "
        "house-lord census necessarily touches wealth/marriage/children/"
        "career/health/parents/siblings/spirituality at minimum). Expected "
        "single-digit unfittable segments across all 8 units combined (0-5), "
        "concentrated in ch24's bundled multi-verse segments where a stray "
        "moral/character verse doesn't map to a life-domain outcome."
    )
    report.append("")

    seg_cache = {}
    unit_domain_sets = {}
    unit_seg_counts = {}
    unit_tokens = {}
    all_unfittable = []
    low_conf_count = 0
    empty_domain_count = 0
    total_segments = 0

    for uid in TARGET_UNITS:
        unit = units[uid]
        segs = segment_unit(unit)
        seg_cache[uid] = segs
        domains_seen = set()
        tok_total = 0
        for ordinal, text in segs:
            total_segments += 1
            key = (uid, ordinal)
            if key not in TAGS:
                report.append("## FAILURE: no hand tag for %s ordinal %d (untagged segment)" % (uid, ordinal))
                write_reports(report)
                return
            domains, conf, unfit = TAGS[key]
            bad = [d for d in domains if d not in DOMAINS_16]
            if bad:
                report.append("## FAILURE: %s#%d uses domain(s) outside the 16: %s" % (uid, ordinal, bad))
                write_reports(report)
                return
            tok = approx_tokens(text)
            tok_total += tok
            domains_seen.update(domains)
            if conf == "low":
                low_conf_count += 1
            if not domains and not unfit:
                empty_domain_count += 1
            if unfit:
                all_unfittable.append((uid, ordinal, text.strip()[:400]))
        unit_domain_sets[uid] = domains_seen
        unit_seg_counts[uid] = len(segs)
        unit_tokens[uid] = tok_total

    # ---- Section 1: per-unit summary ----
    report.append("## 1. Per-unit segment count, rolled-up domain set, tokens")
    report.append("")
    report.append("| unit_id | segments | tokens (approx, word-count) | rolled-up domain set |")
    report.append("|---|---:|---:|---|")
    for uid in TARGET_UNITS:
        doms = ", ".join(sorted(unit_domain_sets[uid])) or "(none)"
        report.append(
            "| %s | %d | %d | %s |" % (uid, unit_seg_counts[uid], unit_tokens[uid], doms)
        )
    report.append("")

    # ---- Section 2: THE HEADLINE ----
    report.append("## 2. THE HEADLINE -- bphs1_ch24 per-domain segment counts and tokens")
    report.append("")
    ch24_segs = seg_cache["bphs1_ch24"]
    per_domain_segs = {d: [] for d in DOMAINS_16}
    per_domain_tokens = {d: 0 for d in DOMAINS_16}
    for ordinal, text in ch24_segs:
        domains, _conf, _unfit = TAGS[("bphs1_ch24", ordinal)]
        tok = approx_tokens(text)
        for d in domains:
            per_domain_segs[d].append(ordinal)
            per_domain_tokens[d] += tok
    report.append("| domain | segments | tokens (approx) |")
    report.append("|---|---:|---:|")
    for d in sorted(DOMAINS_16, key=lambda d: -per_domain_tokens[d]):
        if not per_domain_segs[d]:
            continue
        report.append("| %s | %d | %d |" % (d, len(per_domain_segs[d]), per_domain_tokens[d]))
    report.append("")
    career_tokens = per_domain_tokens["career"]
    career_segs = len(per_domain_segs["career"])
    ch24_total_tokens = unit_tokens["bphs1_ch24"]
    report.append(
        "**If a career question opened only bphs1_ch24's career-tagged segments: "
        "%d tokens (%d segments), vs. %d tokens for the whole chapter, vs. "
        "5,878 tokens the relation filter currently keeps for this chapter "
        "(diagnostics/runs/20260905T071523Z.md Section 7).**"
        % (career_tokens, career_segs, ch24_total_tokens)
    )
    report.append("")
    reduction_vs_whole = 100.0 * (1 - career_tokens / ch24_total_tokens) if ch24_total_tokens else 0.0
    vs_relation_filter = 100.0 * (career_tokens - 5878) / 5878 if 5878 else 0.0
    report.append(
        "Domain tagging cuts the chapter by %.1f%% for a career-only "
        "question (vs. the whole 12,211-token chapter). Compared to the "
        "existing relation filter's 5,878-token career-flavoured keep "
        "(which is NOT domain-scoped -- it keeps whatever contains a "
        "lord-in-house relation regardless of domain, so it already "
        "over-includes non-career effects and under-includes bundled "
        "career segments the filter's regex doesn't parse as relations), "
        "domain tagging's career-only slice is %s%.1f%% relative to that "
        "figure. The two numbers answer different questions: the relation "
        "filter answers 'what looks like a lord-in-house rule', domain "
        "tagging answers 'what is this rule ABOUT' -- they are not "
        "expected to match, and the comparison is included for scale, not "
        "as an apples-to-apples validation." % (reduction_vs_whole, "+" if vs_relation_filter >= 0 else "", vs_relation_filter)
    )
    report.append("")

    # ---- Section 3: broken-title units ----
    report.append("## 3. Broken-title units: derived domain sets + first 200 chars")
    report.append("")
    for uid, recovered_title in [
        ("bphs1_ch27", "Evaluation Of Strengths (Shadbala/Digbala/Kaalabala/Naisargika/Ayana/Cheshta/Drig Bala + Bhava Bala)"),
        ("bphs1_ch43", "Ayurdaya / longevity determination (Pindayu, Nisargayu, Amsayu + longevity-classification yogas)"),
        ("bphs2_ch83", "Yogas for lack of male issue (curses of serpent/father/mother/brother/maternal uncle/Brahmin/wife/departed soul) + remedial measures"),
    ]:
        unit = units[uid]
        clean_preview = strip_devanagari(unit["text"])[:200].replace("\n", " ")
        doms = ", ".join(sorted(unit_domain_sets[uid])) or "(none)"
        report.append("### `%s` (title_raw=%r)" % (uid, unit["title_raw"]))
        report.append("")
        report.append("Recovered real title/topic (by reading): **%s**" % recovered_title)
        report.append("")
        report.append("Derived domain set: %s" % doms)
        report.append("")
        report.append("First 200 chars (Devanagari-stripped): `%s`" % clean_preview)
        report.append("")

    # ---- Section 4: ch66 / ch4 confirm technique_method / planetary_nature ----
    report.append("## 4. bphs2_ch66 and bphs1_ch4 -- confirm technique_method / planetary_nature, not force-fitted")
    report.append("")
    report.append(
        "bphs2_ch66 (Ashtakavarga): rolled-up domain set = %s. All 10 "
        "segments are Karanaprada/Rekhaprada dot-and-line calculation "
        "tables per planet. Matches the full-corpus measurement's 0%% "
        "relation yield for this chapter -- confirmed here as genuinely "
        "technique-only content, not a filter blind spot."
        % (", ".join(sorted(unit_domain_sets["bphs2_ch66"])) or "(none)")
    )
    report.append("")
    report.append(
        "bphs1_ch4 (Zodiacal Signs Described): rolled-up domain set = %s. "
        "Sign descriptions (planetary_nature) plus Nisheka Lagna / Gulika / "
        "Ayanamsa / Bhava Lagna calculation worked examples "
        "(technique_method). One real secondary domain surfaced: a medical-"
        "astrology paragraph (afflicted phlegmatic/windy/bilious sign -> "
        "disease) is genuinely 'health', not force-fitted -- this is the "
        "kind of true secondary tag the vocabulary is meant to catch."
        % (", ".join(sorted(unit_domain_sets["bphs1_ch4"])) or "(none)")
    )
    report.append("")

    # ---- Section 5: unfittable segments ----
    report.append("## 5. Unfittable segments (drift signal)")
    report.append("")
    report.append("Total unfittable segments across all 8 units: **%d**" % len(all_unfittable))
    report.append("")
    if all_unfittable:
        for uid, ordinal, text in all_unfittable:
            report.append("### `%s` ordinal %d" % (uid, ordinal))
            report.append("")
            report.append("```")
            report.append(text)
            report.append("```")
            report.append("")
    else:
        report.append("(none)")
        report.append("")

    # ---- Section 6: confidence / empty-domain counts ----
    report.append("## 6. Confidence and empty-domain counts")
    report.append("")
    report.append("| metric | count | of total segments (%d) |" % total_segments)
    report.append("|---|---:|---:|")
    report.append("| low-confidence tags | %d | %.1f%% |" % (low_conf_count, 100.0 * low_conf_count / total_segments))
    report.append("| empty-domain segments (non-unfittable) | %d | %.1f%% |" % (empty_domain_count, 100.0 * empty_domain_count / total_segments))
    report.append("| unfittable segments | %d | %.1f%% |" % (len(all_unfittable), 100.0 * len(all_unfittable) / total_segments))
    report.append("")
    report.append(
        "Low-confidence concentration: bphs1_ch24's house-lord-census "
        "segments dominate this count -- many segments bundle 2-5 "
        "printed verses into one span (BPHS's own verse-number markers "
        "routinely use a comma or OCR-corrupted digit instead of the "
        "'N. ' form the segmenter keys on, so they don't split; this is "
        "the same absorption behaviour already documented and validated "
        "in scripts/build_segment_index.py's module docstring for its own "
        "Devanagari-marker segmenter -- not a new defect). A bundled "
        "segment genuinely touches 3-5 different house placements at "
        "once, so a single dominant domain often doesn't exist -- low "
        "confidence there is honest, not a tagging failure."
    )
    report.append("")

    # ---- Section 7: projection ----
    report.append("## 7. Projection to all 100 units")
    report.append("")
    report.append(
        "Assumption: this 8-unit sample (%d segments, a deliberately hard "
        "mix spanning a dense life-domain census, three pure-technique "
        "chapters, one definitional chapter, and one whole-chapter "
        "unsplittable unit) required reading and tagging roughly 46,500 "
        "word-count tokens of raw chapter text (Section 1's tokens summed) "
        "directly in-conversation, at a real-token cost documented in "
        "Section 8. Scaling that reading cost linearly by unit count (8 -> "
        "100, x12.5) and by the fact that the full 100-unit corpus is "
        "406,547 real tokens vs. this 8-unit sample's word-count total "
        "(a lower bound on real tokens), a full-corpus tagging pass in "
        "this same manual, in-conversation style would cost on the order "
        "of several hundred thousand to over a million tokens -- "
        "far beyond a single conversation turn, and likely beyond what any "
        "single Claude Code session should attempt without either (a) "
        "batching into many separate sessions/turns, or (b) an automated "
        "tagging pass (LLM API calls, explicitly out of scope for this "
        "probe) with human spot-checking rather than 100%% manual read. "
        "This projection is a rough order-of-magnitude, not a budget "
        "commitment -- the real lesson is that manual segment-level "
        "tagging does not scale past a handful of chapters without "
        "automation, even though it clearly answers the selection "
        "question when done." % total_segments
    )
    report.append("")

    # ---- Section 8: actual token spend ----
    report.append("## 8. Actual token spend")
    report.append("")
    report.append(
        "Not machine-measured (no token-counting instrumentation was wired "
        "into this conversation). Honest estimate based on volume read: "
        "all 8 units' full text was read directly in the conversation "
        "(~46,500 word-count tokens of source text alone, per Section 1's "
        "token column, which under-counts real BPE tokens for OCR-heavy "
        "mixed-script text), plus this session's own reasoning and report "
        "generation. The task's ~60k soft cap was very likely exceeded "
        "once source-text reading alone is counted; the 80k hard-stop "
        "threshold may also have been reached or exceeded. Flagged here "
        "honestly per the task's own instruction, rather than claimed as "
        "under budget without a real measurement."
    )
    report.append("")

    write_reports(report)
    print("Wrote diagnostics/latest_run.md and diagnostics/runs/<timestamp>.md")
    print("Segments tagged: %d across %d units" % (total_segments, len(TARGET_UNITS)))
    print("Unfittable: %d, low-confidence: %d, empty-domain: %d" % (len(all_unfittable), low_conf_count, empty_domain_count))


def write_reports(lines):
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = RUNS_DIR / ("%s.md" % ts)
    text = "\n".join(lines) + "\n"
    with open(run_path, "w", encoding="utf-8") as f:
        f.write(text)
    with open(LATEST_PATH, "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
