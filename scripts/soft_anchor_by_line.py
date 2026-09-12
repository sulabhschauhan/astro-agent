"""Per-(line, term) soft-anchor scan over the whole Cheiro corpus.

REPORT-ONLY. Pure Python + regex. No LLM, no network, no source edits.

PURPOSE
-------
A soft/relative rule term ("short", "sloping", "high") is only usable if we know
what it is measured AGAINST. This script finds, for a single STATED LINE, every
sentence in the book where that line co-occurs with a soft term, and lists every
OTHER line/landmark named in the same sentence -- those are the CANDIDATE
reference features the term may be benchmarked against.

The script deliberately does NOT decide which line a term describes when more
than one line is named in the sentence. Such sentences are flagged
AMBIGUOUS-SUBJECT for a human ruling.

SCOPE THIS RUN: STATED LINE = Line of Head (head line only). Other lines are
later runs of the same shape -- change ``STATED_LINE_KEY`` / ``--line``.

INPUT   data/cheiro/cheiro_clean_v1.json   (all pages, in page order)
        data/ontology_registry.json        (canonical feature names + synonyms)
        data/palm_rules/palm_rules_head_heart_v1.json  (soft antecedent values)
OUTPUT  diagnostics/latest_run.md          (TRUNCATED and rewritten each run)

TEXT NORMALISATION (applied identically to the matched text and the quoted
text, so quotes stay verbatim modulo these two documented steps):
  1. Line-wrap de-hyphenation: the OCR soft-wrap character U+00AC followed by a
     newline is removed (all 376 occurrences in this corpus are line wraps), as
     is ``-\\n`` between two lowercase letters.
  2. Whitespace runs collapse to a single space (required for markdown table
     rendering; no characters are dropped).
No other character is altered, inserted, or removed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = REPO_ROOT / "data" / "cheiro" / "cheiro_clean_v1.json"
REGISTRY_PATH = REPO_ROOT / "data" / "ontology_registry.json"
HEAD_RULES_PATH = REPO_ROOT / "data" / "palm_rules" / "palm_rules_head_heart_v1.json"
REPORT_PATH = REPO_ROOT / "diagnostics" / "latest_run.md"

STATED_LINE_KEY = "Line of Head"

# --------------------------------------------------------------------------
# STATED-LINE prose forms.
#
# Measured against the corpus before selection (whitespace-collapsed counts):
#   "line of head"      120 hits   -> used
#   "head-line"           8 hits   -> used
#   "line of the head"    0 hits   -> included anyway, costs nothing
#   "the head line"       0 hits   -> included anyway, costs nothing
#   "headline"            0 hits   -> included anyway, costs nothing
# Registry synonyms "Natural" / "Cerebral" for Line of Head are NOT used as
# detectors: "natural" is an ordinary English word and would flood the scan.
# --------------------------------------------------------------------------
STATED_LINE_FORMS: dict[str, list[str]] = {
    "Line of Head": [
        r"\bline\s+of\s+(?:the\s+)?head\b",
        r"\bhead[-\s]?lines?\b",
        r"\bheadlines?\b",
    ],
    # Later runs: same shape, one entry per stated line.
    "Line of Heart": [
        r"\bline\s+of\s+(?:the\s+)?heart\b",
        r"\bheart[-\s]?lines?\b",
    ],
    "Line of Life": [
        r"\bline\s+of\s+(?:the\s+)?life\b",
        r"\blife[-\s]?lines?\b",
    ],
    "Line of Fate": [
        r"\bline\s+of\s+(?:the\s+)?fate\b",
        r"\bfate[-\s]?lines?\b",
        r"\bline\s+of\s+destiny\b",
    ],
}

# --------------------------------------------------------------------------
# SOFT TERMS.
#
# Block A: the ten relative/soft terms named in the task.
# Block B: additional soft values actually carried by Line of Head antecedents
#          in palm_rules_head_heart_v1.json (see the report's own term-set
#          section for the enumeration and the exclusion reasoning).
# --------------------------------------------------------------------------
TERMS: dict[str, str] = {
    # -- Block A: task-specified ------------------------------------------
    "high": r"\bhigh(?:er|est)?\b",
    "low": r"\blow(?:er|est)?\b",
    "short": r"\bshort(?:er|est)?\b",
    "long": r"\blong(?:er|est)?\b",
    "sloping": r"\bslop(?:e|es|ed|ing)\b",
    "straight": r"\bstraight(?:er|est)?\b",
    "curved": r"\bcurv(?:e|es|ed|ing|ature)\b",
    "chained": r"\bchain(?:s|ed|ing)?\b",
    "broken": r"\b(?:broke|broken|break|breaks|breaking)\b",
    "forked": r"\bfork(?:s|ed|ing)?\b",
    # -- Block B: added from head-rule antecedents -------------------------
    "clear": r"\bclear(?:er|est|ly)?\b",
    "downward": r"\bdownwards?\b",
    "distant": r"\bdistan(?:t|ce)\b",
    "medium": r"\bmedium\b",
    "touching": r"\btouch(?:es|ed|ing)?\b",
}

TERM_BLOCK_A = [
    "high", "low", "short", "long", "sloping",
    "straight", "curved", "chained", "broken", "forked",
]
TERM_BLOCK_B = ["clear", "downward", "distant", "medium", "touching"]

# Head-line antecedent values judged NOT soft (presence/count or already-hard
# relational), recorded so the exclusion is auditable rather than silent.
EXCLUDED_ANTECEDENT_VALUES = {
    "islanded": "presence-type (an island is present or absent) -- hard, not graded",
    "branched": "presence-type (a branch is present or absent) -- hard, not graded",
    "double": "count-type (two lines) -- hard, not graded",
    "rising_from_Line_of_Life": "already an explicit hard relational target",
    "rising_from_Mount_of_Mars": "already an explicit hard relational target",
    "reaching_Line_of_Heart": "already an explicit hard relational target",
    "terminating_on_Mount": "already an explicit hard relational target",
    "terminating_on_Mount_of_Jupiter": "already an explicit hard relational target",
    "terminating_on_Mount_of_Moon": "already an explicit hard relational target",
    "running_through_Square": "already an explicit hard relational target",
    "under_Mount_of_Saturn": "already an explicit hard relational target",
}

# Ambiguous single-word registry synonyms never used as prose detectors.
BLOCKED_SYNONYMS = {
    "Natural", "Vital", "Cerebral", "Mensal", "Saturnian",
    "Lowest Type", "Useful Hand", "Nervous Active Type", "Knotty Hand",
    "Artistic Type", "Idealistic Hand", "Passion Mount",
    "Mark of Preservation", "Spear Head", "Sister Health Line",
}

# Abbreviations that end in a period but do not end a sentence.
ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "st", "prof", "rev", "hon", "messrs",
    "fig", "figs", "plate", "plates", "chap", "chapter", "no", "nos",
    "vol", "vols", "p", "pp", "etc", "cf", "viz", "ie", "eg",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sept", "sep",
    "oct", "nov", "dec",
}
ROMAN_RE = re.compile(r"^[ivxlcdm]+$", re.IGNORECASE)

# --------------------------------------------------------------------------
# Anaphoric-subject detection (the p160 problem, second form).
#
# p160: "When, however, it lies high on the hand, and the space is narrowed by
# the line of head being too close..." -- the subject is "it" (the HEART line,
# carried over from the previous sentence) and the head line appears only as the
# REFERENCE. Naming-based detection alone would call this PURE-RELATIVE and
# silently attribute "high" to the wrong line. If an anaphoric subject cue
# appears BEFORE the stated line is named, the subject is undetermined and the
# row is flagged for a human, never resolved here.
# --------------------------------------------------------------------------
ANAPHOR_RE = re.compile(
    r"\b(?:it|they|this\s+line|that\s+line|these\s+lines|those\s+lines"
    r"|such\s+a\s+line|the\s+same\s+line)\b",
    re.IGNORECASE,
)

# ADJACENCY GUARD for the anaphoric trigger.
#
# A term sitting inside the stated line's own noun phrase ("a SLOPING line of
# head", "the SLOPING head-line") unambiguously modifies the stated line, no
# matter what pronoun appeared earlier in the sentence -- so an unrelated
# anaphor ("...the money it brings...where the man with the sloping head-line")
# must not flag it. If the gap between the term match and the nearest
# stated-line mention is at or below this many characters, the anaphoric
# trigger is suppressed for that term.
#
# JUSTIFICATION: set from the 19 flagged sentences this run actually produced,
# not a guess. At 30 the four observed false positives clear (p118 gap=1,
# p145 gap=1, p151 gap=1, p223 gap=1, all "sloping line of head"; p149 gap=25,
# p169 gap=1, p149-downward gap=10) while both true positives stay flagged
# (p160 "it lies high ... line of head" and p160 "so low that it droops down
# toward the line of head", gap=32).
# SCOPE GUARD: suppresses ONLY the anaphoric trigger. The "second line named"
# trigger is never suppressed by adjacency -- p147 ("line of head is so high
# ... line of heart", gap=4) stays flagged on the naming trigger alone.
# TUNING NOTE: the closest true positive (32) and the widest false positive
# (25) are only 7 characters apart, so this value is PROVISIONAL on head-line
# evidence only. Re-measure it on the heart-line and life-line runs before
# trusting it as a general constant; if those runs put a true positive under
# 30, drop the adjacency guard rather than tightening the number.
_ANAPHOR_ADJACENCY_CHARS = 30

# Expletive "it", which has no antecedent and so is not an anaphoric subject.
EXPLETIVE_RE = re.compile(
    r"\bit\s+(?:will\s+be|is|was|would\s+be|has\s+been|have\s+been|may\s+be|must\s+be|"
    r"can\s+be|should\s+be|need\s+hardly\s+be)\s+"
    r"(?:remembered|seen|noted|observed|found|said|stated|understood|admitted|"
    r"necessary|useless|impossible|possible|evident|obvious|clear|well|true)\b",
    re.IGNORECASE,
)


class ScanError(RuntimeError):
    """Raised for any unrecoverable input problem, with an actionable message."""


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------
def load_json(path: Path, what: str):
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        raise ScanError(f"{what} not found at {path} -- cannot scan.") from exc
    except PermissionError as exc:
        raise ScanError(f"{what} at {path} is not readable: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ScanError(
            f"{what} at {path} is not valid JSON (line {exc.lineno}, col {exc.colno}): {exc.msg}"
        ) from exc
    except OSError as exc:
        raise ScanError(f"Could not read {what} at {path}: {exc}") from exc


# --------------------------------------------------------------------------
# Text assembly: whole book, in page order, with a per-character page map.
# --------------------------------------------------------------------------
def build_book_text(pages: list[dict]) -> tuple[str, list[int], dict]:
    """Concatenate every page in page order; return (text, page_of_char, stats).

    ``page_of_char[i]`` is the page_ref that character ``i`` came from, so a
    sentence's page (and any page straddle) is recoverable from its offsets.
    """
    if not isinstance(pages, list) or not pages:
        raise ScanError(
            f"Corpus at {CORPUS_PATH} is empty or not a JSON list of page objects."
        )

    ordered = []
    for idx, page in enumerate(pages):
        if not isinstance(page, dict):
            raise ScanError(f"Corpus entry #{idx} is {type(page).__name__}, expected an object.")
        if "page_ref" not in page:
            raise ScanError(f"Corpus entry #{idx} has no 'page_ref' key: keys={sorted(page)}")
        ordered.append(page)
    ordered.sort(key=lambda p: p["page_ref"])

    raw_chars: list[str] = []
    raw_pages: list[int] = []
    pages_with_text = 0
    for page in ordered:
        text = page.get("text") or ""
        if text.strip():
            pages_with_text += 1
        ref = page["page_ref"]
        raw_chars.extend(text)
        raw_pages.extend([ref] * len(text))
        raw_chars.append("\n")          # page separator: never fuse two pages' words
        raw_pages.append(ref)

    # Step 1 -- de-hyphenate OCR line wraps.
    dewrapped: list[str] = []
    dewrapped_pages: list[int] = []
    wraps_joined = 0
    i = 0
    n = len(raw_chars)
    while i < n:
        ch = raw_chars[i]
        nxt = raw_chars[i + 1] if i + 1 < n else ""
        if ch == "¬" and nxt == "\n":
            wraps_joined += 1
            i += 2
            continue
        if (
            ch == "-"
            and nxt == "\n"
            and dewrapped
            and dewrapped[-1].isalpha()
            and dewrapped[-1].islower()
            and i + 2 < n
            and raw_chars[i + 2].isalpha()
            and raw_chars[i + 2].islower()
        ):
            wraps_joined += 1
            i += 2
            continue
        dewrapped.append(ch)
        dewrapped_pages.append(raw_pages[i])
        i += 1

    # Step 2 -- collapse whitespace runs to one space.
    out_chars: list[str] = []
    out_pages: list[int] = []
    prev_space = False
    for ch, ref in zip(dewrapped, dewrapped_pages):
        if ch.isspace():
            if not prev_space:
                out_chars.append(" ")
                out_pages.append(ref)
                prev_space = True
            continue
        out_chars.append(ch)
        out_pages.append(ref)
        prev_space = False

    stats = {
        "pages_total": len(ordered),
        "pages_with_text": pages_with_text,
        "wraps_joined": wraps_joined,
        "chars": len(out_chars),
        "page_min": ordered[0]["page_ref"],
        "page_max": ordered[-1]["page_ref"],
    }
    return "".join(out_chars), out_pages, stats


# --------------------------------------------------------------------------
# Sentence splitting
# --------------------------------------------------------------------------
_SENT_END_RE = re.compile(r'[.!?]["\'’”\)]*\s')


def split_sentences(text: str) -> list[tuple[int, int]]:
    """Return (start, end) offsets of each sentence in ``text``.

    Splits on terminal punctuation followed by whitespace, guarded against
    abbreviations, single-letter initials and roman numerals ("Plate XIII.",
    "CHAPTER VII.") which are dense in this corpus.
    """
    spans: list[tuple[int, int]] = []
    start = 0
    for match in _SENT_END_RE.finditer(text):
        end = match.end()

        # A sentence only ends if what follows starts one. "(Plate XIII.) relates
        # principally to..." must NOT split; "...HEAD. The line of head..." must.
        nxt = text[end:end + 1]
        if nxt and not (nxt.isupper() or nxt.isdigit() or nxt in "\"'“‘"):
            continue

        preceding = text[start:match.start()]
        raw_token = re.split(r"[\s(\[]", preceding)[-1] if preceding else ""
        # A token closing a parenthetical ("XIX.)") ends its sentence -- the
        # abbreviation/roman guard must not swallow it.
        closes_bracket = raw_token.endswith((")", "]", "}"))
        token = raw_token.strip(".,;:\"'()[]").lower()
        if not closes_bracket and (
            token in ABBREVIATIONS
            or (len(token) == 1 and token.isalpha())
            or ROMAN_RE.match(token)
        ):
            continue
        sentence = text[start:end].strip()
        if sentence:
            spans.append((start, end))
        start = end
    tail = text[start:].strip()
    if tail:
        spans.append((start, len(text)))
    return spans


# --------------------------------------------------------------------------
# Landmark vocabulary, built from the ontology registry
# --------------------------------------------------------------------------
@dataclass
class Landmark:
    name: str
    kind: str           # LINE | MOUNT | MARK | FINGER | HAND | REGION
    pattern: re.Pattern


def _pat(*alts: str) -> re.Pattern:
    return re.compile("|".join(f"(?:{a})" for a in alts), re.IGNORECASE)


def build_landmarks(registry: dict) -> list[Landmark]:
    features = registry.get("features")
    if not isinstance(features, dict):
        raise ScanError(
            f"Registry at {REGISTRY_PATH} has no 'features' object "
            f"(top-level keys: {sorted(registry)})."
        )
    synonyms = registry.get("synonyms", {})
    landmarks: list[Landmark] = []

    def add(name: str, kind: str, *alts: str) -> None:
        landmarks.append(Landmark(name, kind, _pat(*alts)))

    # -- lines: "line of X" and "X line" / "X-line" ------------------------
    for name in features.get("lines", []):
        alts: list[str] = []
        if name.lower().startswith("line of "):
            stem = re.escape(name[len("line of "):])
            alts.append(rf"\bline\s+of\s+(?:the\s+)?{stem}\b")
            alts.append(rf"\b{stem}[-\s]?lines?\b")
        else:
            alts.append(rf"\b{re.escape(name)}\b")
        for syn in synonyms.get(name, []):
            if syn in BLOCKED_SYNONYMS or " " not in syn:
                continue
            alts.append(rf"\b{re.escape(syn)}\b")
        add(name, "LINE", *alts)

    # -- mounts: "mount of X" and "X mount" --------------------------------
    for name in features.get("mounts", []):
        alts = []
        if name.lower().startswith("mount of "):
            stem = re.escape(name[len("mount of "):])
            alts.append(rf"\bmounts?\s+of\s+(?:the\s+)?{stem}\b")
            alts.append(rf"\b{stem}\s+mounts?\b")
        else:
            alts.append(rf"\b{re.escape(name)}\b")
        for syn in synonyms.get(name, []):
            if syn in BLOCKED_SYNONYMS or " " not in syn:
                continue
            alts.append(rf"\b{re.escape(syn)}\b")
        add(name, "MOUNT", *alts)

    # -- fingers / thumb ----------------------------------------------------
    for group in ("fingers", "thumb"):
        for name in features.get(group, []):
            alts = [rf"\b{re.escape(name)}s?\b"]
            for syn in synonyms.get(name, []):
                if syn in BLOCKED_SYNONYMS:
                    continue
                alts.append(rf"\b{re.escape(syn)}s?\b")
            add(name, "FINGER", *alts)

    # -- hand shapes --------------------------------------------------------
    for name in features.get("hand_shapes", []):
        alts = [rf"\b{re.escape(name)}s?\b"]
        for syn in synonyms.get(name, []):
            if syn in BLOCKED_SYNONYMS:
                continue
            alts.append(rf"\b{re.escape(syn)}s?\b")
        add(name, "HAND", *alts)

    # -- marks and regions from the relation-target registry ---------------
    seen = {lm.name for lm in landmarks}
    mark_names = {
        "Star", "Cross", "Square", "Island", "Circle", "Spot", "Grille",
        "Triangle", "La Croix Mystique", "Tassel", "Fork", "Tripod", "Bar", "Dot",
    }
    region_names = {
        "Quadrangle", "Hollow of Hand", "Wrist", "Back of Hand", "Skin",
        "Percussion", "Base of Thumb", "Palm", "Left Palm", "Right Palm",
        "Junction of First and Second Fingers",
    }
    for name in registry.get("relation_target_registry", []):
        if name in seen:
            continue
        if name in mark_names:
            kind = "MARK"
        elif name in region_names:
            kind = "REGION"
        else:
            continue
        alts = [rf"\b{re.escape(name)}s?\b"]
        for syn in synonyms.get(name, []):
            if syn in BLOCKED_SYNONYMS:
                continue
            alts.append(rf"\b{re.escape(syn)}s?\b")
        add(name, kind, *alts)
        seen.add(name)

    return landmarks


def find_landmarks(sentence: str, landmarks: list[Landmark]) -> list[tuple[str, str, int, int]]:
    """Return [(name, kind, start, end)] for every landmark named in ``sentence``.

    Shorter matches fully contained inside a longer match are dropped, so
    "square hand" does not also register the MARK "Square".
    """
    hits: list[tuple[str, str, int, int]] = []
    for lm in landmarks:
        for m in lm.pattern.finditer(sentence):
            hits.append((lm.name, lm.kind, m.start(), m.end()))

    kept: list[tuple[str, str, int, int]] = []
    for hit in hits:
        _, _, s, e = hit
        contained = any(
            (o_s <= s and e <= o_e) and (o_e - o_s) > (e - s)
            for _, _, o_s, o_e in hits
        )
        if not contained:
            kept.append(hit)

    dedup: dict[str, tuple[str, str, int, int]] = {}
    for hit in sorted(kept, key=lambda h: h[2]):
        dedup.setdefault(hit[0], hit)
    return list(dedup.values())


# --------------------------------------------------------------------------
# Scan
# --------------------------------------------------------------------------
@dataclass
class Row:
    term: str
    page_label: str
    stated_confirmed: str
    references: list[tuple[str, str]]
    sentence: str
    status: str
    line_refs: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


def page_label(page_of_char: list[int], start: int, end: int) -> str:
    p_start = page_of_char[start]
    p_end = page_of_char[min(end, len(page_of_char)) - 1]
    return f"p{p_start}" if p_start == p_end else f"p{p_start}-{p_end}"


def scan(
    text: str,
    page_of_char: list[int],
    stated_key: str,
    landmarks: list[Landmark],
) -> tuple[list[Row], dict]:
    stated_patterns = [re.compile(p, re.IGNORECASE) for p in STATED_LINE_FORMS[stated_key]]
    term_patterns = {t: re.compile(p, re.IGNORECASE) for t, p in TERMS.items()}
    other_landmarks = [lm for lm in landmarks if lm.name != stated_key]

    spans = split_sentences(text)
    rows: list[Row] = []
    stated_sentences = 0

    for s_start, s_end in spans:
        sentence = text[s_start:s_end].strip()
        if not sentence:
            continue

        stated_hits = []
        for pat in stated_patterns:
            stated_hits.extend((m.start(), m.end(), m.group(0)) for m in pat.finditer(sentence))
        if not stated_hits:
            continue
        stated_sentences += 1

        matched_terms = {t: list(p.finditer(sentence)) for t, p in term_patterns.items()}
        matched_terms = {t: ms for t, ms in matched_terms.items() if ms}
        if not matched_terms:
            continue

        found = find_landmarks(sentence, other_landmarks)
        label = page_label(page_of_char, s_start, s_end)
        stated_forms = sorted({h[2].lower() for h in stated_hits})

        # Anaphoric subject appearing before the stated line is first named?
        first_stated = min(h[0] for h in stated_hits)
        expletive_spans = [(m.start(), m.end()) for m in EXPLETIVE_RE.finditer(sentence)]
        anaphor_before_stated = any(
            m.start() < first_stated
            and not any(e_s <= m.start() < e_e for e_s, e_e in expletive_spans)
            for m in ANAPHOR_RE.finditer(sentence)
        )

        for term, term_matches in matched_terms.items():
            term_spans = [(m.start(), m.end()) for m in term_matches]
            # A landmark whose span overlaps the term's own match is not an
            # independent reference (e.g. term "forked" over the MARK "Fork").
            refs = [
                (name, kind)
                for name, kind, l_s, l_e in found
                if not any(l_s < t_e and t_s < l_e for t_s, t_e in term_spans)
            ]
            line_refs = [name for name, kind in refs if kind == "LINE"]

            # Is this term lexically attached to the stated line's own noun
            # phrase? If so the anaphoric trigger does not apply to it.
            gap = min(
                (
                    max(t_s - h_e, h_s - t_e, 0)
                    for t_s, t_e in term_spans
                    for h_s, h_e, _ in stated_hits
                ),
                default=10 ** 6,
            )
            term_attached_to_stated = gap <= _ANAPHOR_ADJACENCY_CHARS

            reasons: list[str] = []
            if line_refs:
                reasons.append("second line named in sentence")
            if anaphor_before_stated and not term_attached_to_stated:
                reasons.append("anaphoric subject precedes the stated line")

            if reasons:
                status = "AMBIGUOUS-SUBJECT"
            elif refs:
                status = "ANCHOR-CANDIDATE"
            else:
                status = "PURE-RELATIVE"

            rows.append(
                Row(
                    term=term,
                    page_label=label,
                    stated_confirmed=f"YES ({', '.join(stated_forms)})",
                    references=refs,
                    sentence=sentence,
                    status=status,
                    line_refs=line_refs,
                    reasons=reasons,
                )
            )

    return rows, {"stated_sentences": stated_sentences, "sentences_total": len(spans)}


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------
def md_cell(value: str) -> str:
    return value.replace("|", "\\|")


def render_report(
    stated_key: str,
    rows: list[Row],
    text_stats: dict,
    scan_stats: dict,
    landmarks: list[Landmark],
    head_values: Counter,
) -> str:
    by_term: dict[str, list[Row]] = {t: [] for t in TERMS}
    for row in rows:
        by_term[row.term].append(row)

    out: list[str] = []
    w = out.append

    w(f"# Soft-term anchor scan -- STATED LINE = {stated_key}")
    w("")
    w("Report-only. Pure Python + regex, no LLM, no network, no source edits.")
    w(f"Generated by `scripts/soft_anchor_by_line.py` over `{CORPUS_PATH.relative_to(REPO_ROOT).as_posix()}`.")
    w("")
    w("## 0. Scan parameters and provenance")
    w("")
    w(f"- Corpus pages read: **{text_stats['pages_total']}** "
      f"(page_ref {text_stats['page_min']}-{text_stats['page_max']}), "
      f"of which **{text_stats['pages_with_text']}** carry text. "
      "ALL pages concatenated in page order; nothing filtered.")
    w(f"- Characters after normalisation: {text_stats['chars']:,}. "
      f"Sentences split: {scan_stats['sentences_total']:,}.")
    w(f"- OCR line-wraps rejoined (U+00AC + newline, and `-\\n` between lowercase letters): "
      f"**{text_stats['wraps_joined']}**.")
    w("- Whitespace runs collapsed to a single space (needed for table rendering). "
      "No other character altered -- quotes are verbatim modulo these two documented steps.")
    w(f"- Sentences naming the stated line at all: **{scan_stats['stated_sentences']}**.")
    w(f"- Landmark vocabulary size: **{len(landmarks)}** features "
      f"({', '.join(f'{k}={v}' for k, v in sorted(Counter(l.kind for l in landmarks).items()))}).")
    w("")
    w("### Stated-line prose forms used")
    w("")
    for p in STATED_LINE_FORMS[stated_key]:
        w(f"- `{p}`")
    w("")
    w("Corpus-measured hit counts before selection (whitespace-collapsed): "
      "`line of head` = 120, `head-line` = 8, `line of the head` = 0, "
      "`the head line` = 0, `headline` = 0. "
      "Registry synonyms **Natural** and **Cerebral** were deliberately NOT used as detectors: "
      "\"natural\" is an ordinary English word and would flood the scan with false subjects.")
    w("")
    w("### Term set")
    w("")
    w("**Block A -- the ten relative/soft terms named in the task:** "
      + ", ".join(f"`{t}`" for t in TERM_BLOCK_A) + ".")
    w("")
    w("**Block B -- ADDED, because Line of Head antecedents in "
      "`data/palm_rules/palm_rules_head_heart_v1.json` carry them as soft values:** "
      + ", ".join(f"`{t}`" for t in TERM_BLOCK_B) + ".")
    w("")
    w("Observed Line-of-Head antecedent `attribute = value` pairs in that file "
      "(validated + parked), which is what Block B was derived from:")
    w("")
    w("| attribute = value | count | in scan? |")
    w("|---|---|---|")
    for (attr, val), cnt in sorted(head_values.items()):
        low = str(val).lower()
        if low in TERMS:
            mark = f"YES (`{low}`)"
        elif low in {"none", "null"}:
            mark = "n/a (wildcard / target-only antecedent)"
        elif low in EXCLUDED_ANTECEDENT_VALUES:
            mark = f"no -- {EXCLUDED_ANTECEDENT_VALUES[low]}"
        else:
            mark = "no -- not a graded/relative value"
        w(f"| `{attr}` = `{val}` | {cnt} | {mark} |")
    w("")
    w("Excluded on purpose (recorded so the call is auditable, not silent): "
      "`islanded` / `branched` / `double` are presence- or count-type (the mark is there or it "
      "is not -- nothing to benchmark), and every `rising_from_*` / `terminating_on_*` / "
      "`reaching_*` / `running_through_*` / `under_*` value is ALREADY an explicit hard "
      "relational target, so it needs no anchor discovery.")
    w("")
    w("### Status definitions (mechanical, no judgement applied)")
    w("")
    w("- **AMBIGUOUS-SUBJECT** -- which line the term actually describes is NOT decidable "
      "mechanically, so the row is flagged, never resolved. **Sulabh rules these.** Two "
      "independent triggers, either of which is sufficient:")
    w("  1. *second line named in sentence* -- another LINE is named alongside the stated line.")
    w("  2. *anaphoric subject precedes the stated line* -- the sentence's subject is a pronoun "
      "or back-reference (`it`, `they`, `this line`, `that line`, `such a line`, `the same "
      "line`) occurring BEFORE the stated line is first named, so the stated line may be the "
      "REFERENCE rather than the subject. This is the p160 case: *\"When, however, it lies high "
      "on the hand, and the space is narrowed by the line of head being too close...\"* -- the "
      "subject is the heart line carried over from the previous sentence, and naming-based "
      "detection alone would have mis-attributed `high` to the head line. Expletive `it` "
      "(\"it will be remembered\", \"it is evident\") is excluded as having no antecedent, and "
      f"so is any term sitting within **{_ANAPHOR_ADJACENCY_CHARS} characters** of the stated "
      "line itself (\"a *sloping* line of head\" modifies the head line whatever pronoun came "
      "earlier) -- see the script's `_ANAPHOR_ADJACENCY_CHARS` justification/scope-guard/tuning "
      "note. That suppression applies to trigger 2 ONLY; trigger 1 is never suppressed.")
    w("- **ANCHOR-CANDIDATE** -- the sentence names at least one reference landmark, and none "
      "of them is a competing LINE (mounts, marks, fingers, hand types, regions). The named "
      "landmark(s) are the candidate benchmark the term may be measured against.")
    w("- **PURE-RELATIVE** -- the stated line and the term appear with NO reference landmark at "
      "all in the sentence. No benchmark exists in the text; the term is the LLM's call.")
    w("- A landmark whose match overlaps the term's own match is not counted as an independent "
      "reference (e.g. term `forked` matching the MARK `Fork`).")
    w("")

    # ---- 1. grid summary ------------------------------------------------
    w("## 1. Grid summary")
    w("")
    w("| term | block | #anchor-candidate sentences | #ambiguous-subject | #pure-relative | total |")
    w("|---|---|---|---|---|---|")
    tot_a = tot_b = tot_p = tot_t = 0
    for term in TERMS:
        trows = by_term[term]
        n_anchor = sum(1 for r in trows if r.status == "ANCHOR-CANDIDATE")
        n_amb = sum(1 for r in trows if r.status == "AMBIGUOUS-SUBJECT")
        n_pure = sum(1 for r in trows if r.status == "PURE-RELATIVE")
        block = "A" if term in TERM_BLOCK_A else "B"
        w(f"| {term} | {block} | {n_anchor} | {n_amb} | {n_pure} | {len(trows)} |")
        tot_a += n_anchor
        tot_b += n_amb
        tot_p += n_pure
        tot_t += len(trows)
    w(f"| **TOTAL** | | **{tot_a}** | **{tot_b}** | **{tot_p}** | **{tot_t}** |")
    w("")
    w("Rows are one per (term, sentence). A sentence containing two different terms produces "
      "two rows, one per term -- counts are per-term, not per-sentence.")
    w("")
    amb_rows = [r for r in rows if r.status == "AMBIGUOUS-SUBJECT"]
    r_named = sum(1 for r in amb_rows if "second line named in sentence" in r.reasons)
    r_anaph = sum(1 for r in amb_rows if "anaphoric subject precedes the stated line" in r.reasons)
    r_both = sum(1 for r in amb_rows if len(r.reasons) == 2)
    w(f"Ambiguous-subject rows by trigger: second line named = **{r_named}**, "
      f"anaphoric subject precedes stated line = **{r_anaph}** "
      f"(**{r_both}** row(s) hit both triggers).")
    w("")
    terms_zero = [t for t in TERMS if not by_term[t]]
    if terms_zero:
        w(f"Terms with **no** co-occurring sentence at all for this line: "
          + ", ".join(f"`{t}`" for t in terms_zero) + ".")
        w("")
    terms_pure_only = [t for t in TERMS if by_term[t] and all(r.status == "PURE-RELATIVE" for r in by_term[t])]
    if terms_pure_only:
        w("Terms that are **PURE-RELATIVE throughout** (no reference landmark ever appears "
          "alongside them for this line -- no benchmark exists in the source): "
          + ", ".join(f"`{t}`" for t in terms_pure_only) + ".")
        w("")

    # ---- 2. full candidate rows ----------------------------------------
    w("## 2. Full candidate rows, grouped by term")
    w("")
    for term in TERMS:
        trows = by_term[term]
        w(f"### `{term}` ({'block A' if term in TERM_BLOCK_A else 'block B'}) -- {len(trows)} row(s)")
        w("")
        if not trows:
            w("_No sentence in the book names the stated line together with this term._")
            w("")
            continue
        w("| term | page_ref | stated line confirmed | reference landmark(s) | status | verbatim sentence |")
        w("|---|---|---|---|---|---|")
        for r in sorted(trows, key=lambda x: (int(re.findall(r"\d+", x.page_label)[0]), x.sentence)):
            refs = "; ".join(f"{n} [{k}]" for n, k in r.references) or "-- none --"
            w(
                f"| {r.term} | {r.page_label} | {md_cell(r.stated_confirmed)} | "
                f"{md_cell(refs)} | {r.status} | {md_cell(r.sentence)} |"
            )
        w("")

    # ---- 3. ambiguous-subject list -------------------------------------
    amb = [r for r in rows if r.status == "AMBIGUOUS-SUBJECT"]
    w("## 3. AMBIGUOUS-SUBJECT sentences -- for human ruling")
    w("")
    w("Each of these hit at least one ambiguity trigger: another LINE is named alongside the "
      "stated line, and/or an anaphoric subject precedes the stated line so the stated line may "
      "be the reference rather than the subject. Which line the term describes is NOT determined "
      "here, by design. Sulabh rules each row.")
    w("")
    if not amb:
        w("_None._")
        w("")
    else:
        by_sentence: dict[tuple[str, str], list[str]] = {}
        for r in amb:
            by_sentence.setdefault((r.page_label, r.sentence), []).append(r.term)
        w(f"**{len(amb)} row(s) across {len(by_sentence)} distinct sentence(s).**")
        w("")
        w("| # | page_ref | term(s) | why flagged | competing line(s) named | verbatim sentence |")
        w("|---|---|---|---|---|---|")
        for i, ((label, sentence), terms) in enumerate(
            sorted(by_sentence.items(), key=lambda kv: int(re.findall(r"\d+", kv[0][0])[0])), 1
        ):
            same = [r for r in amb if (r.page_label, r.sentence) == (label, sentence)]
            lines = sorted({ln for r in same for ln in r.line_refs})
            why = sorted({reason for r in same for reason in r.reasons})
            w(
                f"| {i} | {label} | {', '.join(sorted(set(terms)))} | "
                f"{md_cell('; '.join(why))} | {md_cell('; '.join(lines) or '-- none --')} | "
                f"{md_cell(sentence)} |"
            )
        w("")

    pure = [r for r in rows if r.status == "PURE-RELATIVE"]
    w("## 4. PURE-RELATIVE roll-up")
    w("")
    w(f"**{len(pure)} row(s)** have the stated line and a soft term with no reference landmark "
      "anywhere in the sentence. For these the source supplies no benchmark, so the reading is "
      "the LLM's call -- flagged, not resolved.")
    w("")
    if pure:
        pure_counts = Counter(r.term for r in pure)
        w("| term | pure-relative rows |")
        w("|---|---|")
        for t, c in sorted(pure_counts.items(), key=lambda kv: (-kv[1], kv[0])):
            w(f"| {t} | {c} |")
        w("")

    w("## 5. Scope note")
    w("")
    w("This run covers the HEAD LINE only (validated chapter first). Heart, life and fate lines "
      "are later runs of the identical shape -- `STATED_LINE_FORMS` already carries their prose "
      "forms; pass `--line \"Line of Heart\"` to run one. No source file, rule file or registry "
      "was modified by this run; the only write is this report.")
    w("")
    return "\n".join(out)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def collect_head_antecedent_values(rules: dict, feature: str) -> Counter:
    values: Counter = Counter()
    for key in ("validated_candidates", "parked_pending_relation_target"):
        for rule in rules.get(key, []) or []:
            for ante in rule.get("antecedents", []) or []:
                if ante.get("feature") == feature:
                    values[(ante.get("attribute"), str(ante.get("value")))] += 1
    return values


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--line",
        default=STATED_LINE_KEY,
        choices=sorted(STATED_LINE_FORMS),
        help="Stated line to scan for (default: Line of Head).",
    )
    args = parser.parse_args(argv)

    try:
        pages = load_json(CORPUS_PATH, "Cheiro corpus")
        registry = load_json(REGISTRY_PATH, "Ontology registry")
        rules = load_json(HEAD_RULES_PATH, "Head/heart rule file")

        text, page_of_char, text_stats = build_book_text(pages)
        landmarks = build_landmarks(registry)
        rows, scan_stats = scan(text, page_of_char, args.line, landmarks)
        head_values = collect_head_antecedent_values(rules, args.line)

        report = render_report(args.line, rows, text_stats, scan_stats, landmarks, head_values)

        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            with REPORT_PATH.open("w", encoding="utf-8", newline="\n") as fh:
                fh.write(report)          # "w" truncates -- overwrite-only, never append
        except OSError as exc:
            raise ScanError(f"Could not write report to {REPORT_PATH}: {exc}") from exc

    except ScanError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"stated line      : {args.line}")
    print(f"pages read       : {text_stats['pages_total']} ({text_stats['pages_with_text']} with text)")
    print(f"sentences        : {scan_stats['sentences_total']}")
    print(f"stated-line sents: {scan_stats['stated_sentences']}")
    print(f"rows emitted     : {len(rows)}")
    print(f"  anchor-candidate: {sum(1 for r in rows if r.status == 'ANCHOR-CANDIDATE')}")
    print(f"  ambiguous-subject: {sum(1 for r in rows if r.status == 'AMBIGUOUS-SUBJECT')}")
    print(f"  pure-relative   : {sum(1 for r in rows if r.status == 'PURE-RELATIVE')}")
    print(f"report           : {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
