"""Soft-term anchor extraction over the WHOLE Cheiro text (VERIFICATION
ARCHITECTURE -- fidelity-not-truth, see data/palm_rules/README.md).

QUESTION: the S95 partition leaves a set of relative/quality terms ("high",
"narrow", "short", ...) that a reader must judge by eye. But Cheiro sometimes
DEFINES a relative term against a checkable landmark in the same sentence
(the canonical example being a head line lying "high" explained in terms of
the space between it and the heart line). Where such a sentence exists, the
term has a potential CODE-COMPUTABLE anchor and does not have to stay a pure
LLM judgment call. Where no such sentence exists anywhere in the book, the
term is genuinely PURE-RELATIVE -- the LLM's call, with no benchmark to
check it against.

This scan surfaces the candidates. It does NOT decide which are real anchors:
every candidate sentence is quoted VERBATIM with its page_ref for Sulabh to
confirm or reject. No ranking, no scoring, no "likely anchor" heuristic --
the script's only judgment is the mechanical one of co-occurrence.

METHOD
  - Reads data/cheiro/cheiro_clean_v1.json and concatenates ALL 310 pages in
    page order into ONE continuous string before sentence-splitting, per the
    project's read-the-whole-chapter-not-a-retrieved-chunk rule. Sentences
    that straddle a page break are therefore recovered intact, and each
    sentence is attributed to the page its FIRST character falls on.
  - Landmark vocabulary is taken verbatim from ontology_registry.json's
    relation_target_registry (58 names). Nothing is invented or aliased:
    "the head line" is NOT matched, only the registry's own "Line of Head".
    See the RECALL FLOOR caveat in the report for what that costs.
  - A candidate anchor = one sentence containing BOTH the soft term and at
    least one landmark name.

Landmark names are reported in two structurally-distinguished groups --
MULTI-WORD registry names ("Mount of Jupiter", "Line of Heart") and
SINGLE-WORD ones ("Palm", "Star", "Bar", "Square") -- because the single-word
half of the registry matches common English and produces weak co-occurrences.
That split is a property of the registry string, not a quality judgment; both
groups are counted in full and neither is dropped.

Pure Python + regex. ZERO LLM calls, zero network. Report-only: writes
diagnostics/latest_run.md (truncate, per CLAUDE.md Diagnostics convention),
touches no other file, makes no commit.
"""
from __future__ import annotations

import bisect
import json
import re
import sys
from collections import Counter
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_BOOK_PATH = _REPO_ROOT / "data" / "cheiro" / "cheiro_clean_v1.json"
_REGISTRY_PATH = _REPO_ROOT / "data" / "ontology_registry.json"
_RULES_PATH = _REPO_ROOT / "data" / "palm_rules" / "palm_rules_head_heart_v1.json"
_REPORT_PATH = _REPO_ROOT / "diagnostics" / "latest_run.md"

# The S95 soft/ambiguous terms named in the task spec.
_PRIMARY_TERMS = (
    "high", "low", "short", "long", "narrow", "wide",
    "sloping", "straight", "chained", "broken", "faded",
)

# Report-rendering cap ONLY. Set to None to dump every candidate sentence.
# Counts are always reported in full; the cap affects how many are QUOTED.
_MAX_QUOTES_PER_GROUP: int | None = 30

# Running-header shape: a page's first line is the chapter title (ends in '.')
# and its second line is the printed page number. Left in place these fuse
# into the page's first real sentence and can manufacture a landmark
# co-occurrence that Cheiro never wrote (e.g. the header "The Line of Head."
# sitting in front of a sentence about something else). Stripped mechanically,
# counted, and reported -- never silently.
_HEADER_TITLE = re.compile(r"^[A-Z][^.\n]{0,48}\.$")
_HEADER_NUMBER = re.compile(r"^\d{1,3}$")

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[\"'(]?[A-Z])")

# A running header that sits MID-page (not on the first two lines) survives the
# strip above and fuses into whatever sentence surrounds it -- e.g. "...straight
# line of head on The Line of Head in Relation to the Seven Types. 9d the
# philosophic hand...". That fused text can inject a landmark name Cheiro did
# not write in that sentence, so a candidate carrying one is FLAGGED for the
# human reader. It is flagged, never dropped: the sentence is still quoted
# verbatim and still counted.
_FUSED_HEADER = re.compile(
    r"(Language of the Hand|The Line of [A-Z]\w+ in Relation|in Relation to the Seven Types)",
    re.IGNORECASE,
)


class ExtractError(RuntimeError):
    """Raised with context when an input cannot be read or parsed."""


def _load_json(path: Path, what: str):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ExtractError(f"could not read {what} at {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ExtractError(f"{what} at {path} is not valid JSON: {exc}") from exc


def load_landmarks() -> list[str]:
    reg = _load_json(_REGISTRY_PATH, "ontology registry")
    names = reg.get("relation_target_registry")
    if not isinstance(names, list) or not names:
        raise ExtractError(
            f"ontology registry at {_REGISTRY_PATH} has no usable "
            "'relation_target_registry' list -- refusing to invent landmark names"
        )
    return list(names)


def load_extra_terms(primary: tuple[str, ...]) -> tuple[list[str], str]:
    """Additional single-word soft terms, DERIVED (not hand-listed) from the
    values that the rule corpus actually uses on soft/ambiguous attributes.
    Returns (terms, provenance_note). Grounding this in values the corpus
    really carries keeps the extra set small and auditable, rather than
    sweeping in ~90 unused registry tokens."""
    soft_attrs = {"Depth", "Width", "Color", "Continuity", "Direction",
                  "Slope", "Slope_Magnitude", "Curve", "Clarity",
                  "Position", "Branching", "Type", "Breadth", "Length", "Presence"}
    data = _load_json(_RULES_PATH, "rule corpus")
    used: set[str] = set()
    for rule in data.get("validated_candidates", []):
        for ant in rule.get("antecedents", []):
            if ant.get("attribute") in soft_attrs and isinstance(ant.get("value"), str):
                used.add(ant["value"])
    extra = sorted(
        v for v in used
        if v.lower() not in primary and "_" not in v and v.isalpha()
    )
    note = (
        "derived from every string value carried by a soft/ambiguous-attribute "
        f"antecedent in {_RULES_PATH.name} ({len(used)} distinct values), keeping "
        "single-word alphabetic tokens not already in the primary list"
    )
    return extra, note


def split_sentences(text: str) -> list[tuple[int, str]]:
    """Returns [(absolute_start_offset, sentence_text)] over the whole book."""
    sentences: list[tuple[int, str]] = []
    pos = 0
    for match in _SENTENCE_SPLIT.finditer(text):
        end = match.start()
        chunk = text[pos:end].strip()
        if chunk:
            sentences.append((pos + (len(text[pos:end]) - len(text[pos:end].lstrip())), chunk))
        pos = match.end()
    tail = text[pos:].strip()
    if tail:
        sentences.append((pos, tail))
    return sentences


def compile_landmark_patterns(names: list[str]) -> list[tuple[str, re.Pattern, bool]]:
    """(name, pattern, is_multiword). Whitespace between words is flexible so
    an OCR line-wrap inside a landmark name cannot defeat the match -- the
    documented 'first\\nfinger' failure mode. The WORDS themselves are the
    registry's own; nothing is aliased."""
    compiled = []
    for name in names:
        parts = [re.escape(w) for w in name.split()]
        pattern = re.compile(r"\b" + r"\s+".join(parts) + r"\b", re.IGNORECASE)
        compiled.append((name, pattern, len(parts) > 1))
    return compiled


def scan_term(term: str, sentences, landmarks) -> dict:
    term_re = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
    # SELF-MATCH GUARD: some soft VALUES are also registry LANDMARK names
    # ("square" is both a shape value and the Square sign). Without this, every
    # sentence containing the term trivially "co-occurs with a landmark" and the
    # anchor count is a pure artifact. The colliding landmark is excluded from
    # detection and named in the report -- never silently dropped.
    self_match = [n for n, _pat, _m in landmarks if n.lower() == term.lower()]
    landmarks = [(n, pat, m) for n, pat, m in landmarks if n.lower() != term.lower()]
    multi_hits: list[dict] = []
    single_hits: list[dict] = []
    bare = 0
    for page_ref, sentence in sentences:
        if not term_re.search(sentence):
            continue
        found_multi = [n for n, pat, is_multi in landmarks if is_multi and pat.search(sentence)]
        found_single = [n for n, pat, is_multi in landmarks if not is_multi and pat.search(sentence)]
        fused = bool(_FUSED_HEADER.search(sentence))
        if found_multi:
            multi_hits.append({"page_ref": page_ref, "sentence": sentence,
                               "landmarks": found_multi + found_single, "fused_header": fused})
        elif found_single:
            single_hits.append({"page_ref": page_ref, "sentence": sentence,
                                "landmarks": found_single, "fused_header": fused})
        else:
            bare += 1
    total_landmark = len(multi_hits) + len(single_hits)
    total = total_landmark + bare
    if total == 0:
        # The word never appears in the book AT ALL -- structurally different
        # from "appears but never beside a landmark", and usually means the
        # token is an EXTRACTOR NORMALIZATION ("islanded") rather than Cheiro's
        # own wording ("full of little islands").
        status = "ABSENT-FROM-BOOK"
    elif total_landmark:
        status = "ANCHOR-CANDIDATE"
    else:
        status = "PURE-RELATIVE"
    return {
        "term": term,
        "multi": multi_hits,
        "single": single_hits,
        "bare": bare,
        "landmark_sentences": total_landmark,
        "total_sentences": total,
        "self_match": self_match,
        "status": status,
    }


def _quote_block(hits: list[dict], label: str) -> list[str]:
    lines: list[str] = []
    if not hits:
        lines.append(f"*{label}: none.*\n")
        return lines
    shown = hits if _MAX_QUOTES_PER_GROUP is None else hits[:_MAX_QUOTES_PER_GROUP]
    lines.append(f"**{label}: {len(hits)} sentence(s)**"
                 + ("" if len(shown) == len(hits)
                    else f" — {len(shown)} quoted below, {len(hits) - len(shown)} omitted for report "
                         "size only (set `_MAX_QUOTES_PER_GROUP = None` to dump all; nothing is filtered "
                         "on content)")
                 + "\n")
    for hit in shown:
        landmarks = ", ".join(hit["landmarks"])
        warn = " ⚠ OCR running-header text fused into this sentence — check the landmark is Cheiro's, not the header's" if hit.get("fused_header") else ""
        lines.append(f"- **p{hit['page_ref']}** [{landmarks}]{warn}")
        lines.append(f"  > {hit['sentence']}")
    lines.append("")
    return lines


def _status_cell(r: dict) -> str:
    if r["status"] == "ANCHOR-CANDIDATE":
        cell = "**ANCHOR-CANDIDATE**"
    elif r["status"] == "ABSENT-FROM-BOOK":
        cell = "**ABSENT-FROM-BOOK**"
    else:
        cell = "PURE-RELATIVE"
    if r.get("self_match"):
        cell += f" ⚠ self-match excluded: {', '.join(r['self_match'])}"
    return cell


def build_report(results, extra_results, landmark_names, corpus_stats, extra_note) -> str:
    lines: list[str] = []
    lines.append("# Latest Run: soft-term anchor extraction over the whole Cheiro text\n")
    lines.append(
        "Report-only. Pure Python + regex — **no LLM call, no network**, no source edit, "
        "nothing committed. The script surfaces candidate anchors and **does not decide "
        "which are real**: every candidate is quoted verbatim with its `page_ref` for "
        "Sulabh to confirm or reject.\n"
    )

    lines.append("## 0. Corpus and method\n")
    lines.append(f"- Source: `data/cheiro/cheiro_clean_v1.json` — **{corpus_stats['pages']} pages** "
                 f"({corpus_stats['text_pages']} carrying text), concatenated in page order into one "
                 f"continuous string of {corpus_stats['chars']:,} characters, then split into "
                 f"**{corpus_stats['sentences']:,} sentences**. Sentences straddling a page break are "
                 "recovered intact; each is attributed to the page its first character falls on.")
    lines.append(f"- OCR repair before splitting: hyphen/`¬` line-wraps rejoined; newlines flattened; "
                 f"**{corpus_stats['headers_stripped']} running headers** (chapter title line + printed "
                 "page-number line) removed so a header cannot manufacture a landmark co-occurrence in "
                 "the page's first sentence.")
    lines.append(f"- Landmark vocabulary: **{len(landmark_names)} names taken verbatim** from "
                 "`ontology_registry.json` → `relation_target_registry`. Nothing invented, nothing aliased.")
    lines.append("- A **candidate anchor** = one sentence containing both the soft term and ≥1 landmark name.")
    lines.append(f"- **{corpus_stats['fused']} candidate sentence(s) carry OCR running-header text fused "
                 "mid-sentence** (a header that sits mid-page survives the leading-line strip). These are "
                 "marked ⚠ in §2 because the fused fragment can inject a landmark name Cheiro did not write "
                 "in that sentence. They are flagged, never dropped — still quoted verbatim, still counted.\n")

    lines.append("> **RECALL FLOOR — read before concluding a term is PURE-RELATIVE.** Because the scan "
                 "matches only the registry's own strings, Cheiro's ordinary prose forms are invisible to "
                 "it: `the head line`, `the line of the head`, `his thumb`, and bare pronoun references "
                 "(`it`, `the line`) all fail to match while naming a real landmark. A PURE-RELATIVE "
                 "verdict therefore means *no registry-form landmark shares a sentence with the term*, "
                 "**not** *Cheiro never anchors this term*. Treat PURE-RELATIVE as a lower bound on "
                 "anchoring, and ANCHOR-CANDIDATE counts as a floor.\n")

    lines.append("## 1. Summary — which terms have a Cheiro anchor to capture\n")
    lines.append("| term | status | landmark sentences | of which multi-word landmark | no-landmark sentences | total |")
    lines.append("|---|---|---|---|---|---|")
    for r in results:
        lines.append(f"| `{r['term']}` | {_status_cell(r)} | {r['landmark_sentences']} | {len(r['multi'])} | "
                     f"{r['bare']} | {r['total_sentences']} |")
    lines.append("")
    anchored = [r["term"] for r in results if r["status"] == "ANCHOR-CANDIDATE"]
    pure = [r["term"] for r in results if r["status"] == "PURE-RELATIVE"]
    absent = [r["term"] for r in results if r["status"] == "ABSENT-FROM-BOOK"]
    lines.append(f"- **Anchor to capture ({len(anchored)}/{len(results)}):** "
                 + (", ".join(f"`{t}`" for t in anchored) or "none"))
    lines.append(f"- **Stays pure-relative — LLM's call, no benchmark ({len(pure)}/{len(results)}):** "
                 + (", ".join(f"`{t}`" for t in pure) or "none"))
    if absent:
        lines.append(f"- **ABSENT FROM THE BOOK ({len(absent)}/{len(results)}):** "
                     + ", ".join(f"`{t}`" for t in absent)
                     + " — the word occurs zero times in 310 pages, so there is nothing to anchor "
                       "*and* nothing to judge. See §1b.")
    lines.append("")

    if extra_results:
        lines.append("### 1a. Additional soft-pool terms (beyond the 11 named in the task)\n")
        lines.append(f"The task asked to include other soft-value-pool terms and say so. These were "
                     f"{extra_note}.\n")
        lines.append("| term | status | landmark sentences | of which multi-word | no-landmark | total |")
        lines.append("|---|---|---|---|---|---|")
        for r in extra_results:
            lines.append(f"| `{r['term']}` | {_status_cell(r)} | {r['landmark_sentences']} | {len(r['multi'])} | "
                         f"{r['bare']} | {r['total_sentences']} |")
        lines.append("")

    absent_all = [r for r in results + extra_results if r["status"] == "ABSENT-FROM-BOOK"]
    selfmatch_all = [r for r in results + extra_results if r.get("self_match")]
    lines.append("### 1b. Two mechanical findings that are not about anchoring\n")
    if absent_all:
        lines.append("**ABSENT FROM THE BOOK** — these rule-corpus values occur **zero times** in the "
                     "whole 310-page text, so they are neither anchorable nor judgeable. They are "
                     "extractor/ontology normalizations, not Cheiro's wording (he writes *\"full of "
                     "little islands\"*, never *\"islanded\"*). Any rule keyed on one of these can only "
                     "match if the vision layer emits the normalized token — the S95 vocabulary-contract "
                     "problem, arriving from the book side:\n")
        for r in absent_all:
            lines.append(f"- `{r['term']}`")
        lines.append("")
    if selfmatch_all:
        lines.append("**SELF-MATCH EXCLUDED** — these terms are ALSO landmark names in "
                     "`relation_target_registry`, so every sentence containing the term would trivially "
                     "\"co-occur with a landmark\". The colliding landmark was excluded from detection "
                     "for that term only; all other landmarks still count:\n")
        for r in selfmatch_all:
            lines.append(f"- `{r['term']}` collides with registry landmark(s) "
                         f"{', '.join(r['self_match'])} — excluded, leaving "
                         f"{r['landmark_sentences']} genuine landmark sentence(s)")
        lines.append("")

    lines.append("## 2. Candidate sentences, verbatim (for Sulabh to confirm)\n")
    lines.append("Each term gets two groups, split by an objective property of the matched registry "
                 "string — **multi-word** landmark names (`Mount of Jupiter`, `Line of Heart`) and "
                 "**single-word** ones (`Palm`, `Star`, `Bar`, `Square`), which collide with ordinary "
                 "English and produce weaker co-occurrences. Both are counted in full; neither is "
                 "dropped, and the split implies no judgment about which sentences are real anchors.\n")
    for r in results + extra_results:
        lines.append(f"### `{r['term']}` — {r['status']}\n")
        if r["status"] == "ABSENT-FROM-BOOK":
            lines.append("The word does not occur anywhere in the 310-page text. Nothing to quote.\n")
            continue
        if r["status"] == "PURE-RELATIVE":
            lines.append(f"No sentence in the book pairs this term with a registry-form landmark "
                         f"({r['bare']} sentence(s) contain the term with no landmark). Subject to the "
                         "RECALL FLOOR caveat above.\n")
            continue
        lines.extend(_quote_block(r["multi"], "Multi-word landmark in the same sentence"))
        lines.extend(_quote_block(r["single"], "Single-word landmark only"))

    lines.append("## 3. What this scan deliberately does NOT do\n")
    lines.append("- It does not decide whether a co-occurrence is a real definition. "
                 "`\"...the line is short, barely reaching the middle of the hand...\"` and "
                 "`\"...a star on the Mount of Jupiter with a long line...\"` are both surfaced; "
                 "only the first is an anchor, and that call is Sulabh's.")
    lines.append("- It does not rank, score, or filter candidates by likelihood.")
    lines.append("- It does not extend the landmark vocabulary to prose forms (see RECALL FLOOR).")
    lines.append("- It writes nothing except this report.\n")
    return "\n".join(lines)


def main() -> None:
    landmark_names = load_landmarks()
    landmarks = compile_landmark_patterns(landmark_names)

    pages = _load_json(_BOOK_PATH, "Cheiro book text")
    if not isinstance(pages, list) or not pages:
        raise ExtractError(f"{_BOOK_PATH} did not contain a non-empty list of pages")
    try:
        pages = sorted(pages, key=lambda p: int(p["page_ref"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise ExtractError(f"could not order pages by numeric page_ref in {_BOOK_PATH}: {exc}") from exc

    chunks: list[str] = []
    starts: list[int] = []
    refs: list = []
    cursor = 0
    headers_stripped = 0
    text_pages = 0
    for page in pages:
        raw = page.get("text") or ""
        lines_ = raw.split("\n")
        if len(lines_) >= 2 and _HEADER_TITLE.match(lines_[0].strip()) and _HEADER_NUMBER.match(lines_[1].strip()):
            lines_ = lines_[2:]
            headers_stripped += 1
        body = "\n".join(lines_)
        body = re.sub(r"[-¬‐-―]\s*\n\s*", "", body)
        body = re.sub(r"\s+", " ", body).strip()
        if body:
            text_pages += 1
        starts.append(cursor)
        refs.append(page.get("page_ref"))
        chunks.append(body)
        cursor += len(body) + 1
    text = " ".join(chunks)

    raw_sentences = split_sentences(text)
    sentences = []
    for offset, sentence in raw_sentences:
        idx = bisect.bisect_right(starts, offset) - 1
        sentences.append((refs[max(idx, 0)], sentence))

    corpus_stats = {
        "pages": len(pages),
        "text_pages": text_pages,
        "chars": len(text),
        "sentences": len(sentences),
        "headers_stripped": headers_stripped,
    }

    results = [scan_term(t, sentences, landmarks) for t in _PRIMARY_TERMS]
    extra_terms, extra_note = load_extra_terms(_PRIMARY_TERMS)
    extra_results = [scan_term(t, sentences, landmarks) for t in extra_terms]

    for r in results + extra_results:
        print(f"{r['term']:12} {r['status']:18} landmark={r['landmark_sentences']:4} "
              f"(multi={len(r['multi'])}) bare={r['bare']}")

    corpus_stats["fused"] = sum(
        1 for r in results + extra_results
        for hit in r["multi"] + r["single"] if hit.get("fused_header")
    )

    report = build_report(results, extra_results, landmark_names, corpus_stats, extra_note)
    try:
        _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        _REPORT_PATH.write_text(report, encoding="utf-8")
    except OSError as exc:
        raise ExtractError(f"could not write report to {_REPORT_PATH}: {exc}") from exc
    print(f"\nWrote report to {_REPORT_PATH}")


if __name__ == "__main__":
    main()
