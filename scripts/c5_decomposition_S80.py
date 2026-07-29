"""
scripts/c5_decomposition_S80.py
S80 U0.6 -- C5 (unalignable) decomposition, Cheiro only, read-only,
diagnostics-only. Run manually; never invoked from CI or the pytest suite.
NO repair logic, NO new alignment design, NO imports from pdf_processor.py /
chunker.py / embedder.py / query_engine.py.

REUSE, NOT REINVENTION: this script imports directly from the already-
committed scripts/bidirectional_corruption_census_S80.py (CHEIRO_PDF,
CHEIRO_BOOK, _sha256_file, _load_wordset, _get_collection, _native_text,
_corpus_text_for_page, _tokenize, _classify_pair, _is_roman_numeral,
_run_mandatory_self_checks). The one new function below,
`_align_classify_positions`, is a POSITION-ANNOTATED REPLICA of that
module's `_align_and_classify` -- byte-for-byte the same
difflib.SequenceMatcher call over the same lowercased token lists, the same
replace/insert/delete/equal opcode handling, the same block-pairing +
leftover-to-C5 rule. The only addition is a `position` index (this token's
offset into its own native_tokens/corpus_tokens list) plus retaining the
token strings for EVERY non-equal opcode (not just C5) -- needed for
requirement (d)'s edge-vs-mid-page clustering check and requirement (e)'s
augmented-oracle reclassification, neither of which the original function
had a reason to support. Fidelity is verified, not assumed: `main()` below
asserts this replica's own C1-C5 totals exactly match the already-committed
sidecar (diagnostics/bidirectional_corruption_census_S80_data.json) before
any new output is written -- if they diverge even by one token, this script
fails loudly rather than silently reporting on a different algorithm.

WHY THIS PROMPT (U0.6): U0.5's C5 bucket (2,991 "unalignable" positions,
64% of all non-matching tokens) was reported but never inspected -- bulk
size alone says nothing about whether it is boilerplate churn (running
heads, plate captions, single-letter diagram callout labels) or genuine
lost/gained doctrine. This script decomposes it and gives U0.5's own
193-position Roman-numeral/proper-noun oracle-noise caveat a real fix
(requirement (e)), instead of carrying it forward unexamined.

SUBCATEGORY RULES -- DERIVED FROM OBSERVED TOKENS, evaluated in this order,
first match wins (see the generated report's own frequency tables for the
exact evidence each rule was built from; nothing here is a generic/off-the-
shelf taxonomy):
  1. roman_numeral            -- reuses census._is_roman_numeral() as-is.
  2. punctuation_single_char_non_alpha -- any length-1 alpha token. Chosen
     BEFORE the real-word check (a lone "a"/"i" IS technically a real
     dictionary word) because direct inspection of the C5 pool showed
     massive volume (1084 of 2419 C5a tokens, 45%) concentrated in single
     uppercase/lowercase letters -- the empirical signature of this book's
     hand-diagram callout labels (e.g. "(d-d, Plate XX.)", "(e-e, Plate
     XVI.)" -- the hyphen is dropped by _WORD_PATTERN, leaving two lone
     single-letter tokens with no natural corpus counterpart), not genuine
     prose use of "a"/"I". NOTE: true punctuation and bare digits can never
     reach this classifier at all -- `_WORD_PATTERN` (alpha-only) drops
     them before tokenization even starts, so the requested "printed folio
     number (bare digits)" subcategory is reported as a structural 0/0 for
     both sides, not a measured absence.
  3. plate_caption_fragment   -- lowercase token in {"plate", "fig"}.
     Derived directly: "Plate" was C5a's #1 token by distinct-page count
     (47 of 245 pages, 50 total occurrences) and "Fig" also recurred (11
     occurrences) -- both tied to this book's own illustration-callout
     convention ("(e-e, Plate XX.)", "Fig. 1"), confirmed by reading actual
     page text, not assumed from a generic list.
  4. running_head_title_fragment -- lowercase token in {"the", "hand",
     "of", "right", "left", "cheiro", "language"}. Derived from the SAME
     distinct-page-count analysis: "THE"/"HAND"/"OF" recur across 34-39 of
     245 pages each (essentially every other in-scope page) -- far beyond
     what ordinary vocabulary frequency would predict -- matching this
     book's own directly-observed running-head phrase ("Cheiro's Language
     of the Hand.") and its portrait-caption convention ("THE RIGHT HAND
     OF <NAME>", confirmed against diagnostics/r1_p0_page_triage_S79.md's
     own captured plate-caption text). "left"/"cheiro"/"language" are
     included by direct correspondence to that same fixed phrase, not
     independently re-derived by frequency (their standalone frequency is
     lower, but they are unambiguously part of the identical repeating
     phrase already evidenced by the higher-frequency members).
  5. proper_noun               -- lowercase token in a curated set found
     BY SEARCHING the actual C5 pool for this book's known planet/mount
     vocabulary and this book's own portrait-plate caption names (Sheridan/
     David/Sulabh-style external names do not appear here -- these are the
     historical portrait subjects Cheiro's OWN book captions, e.g. "THE
     HAND OF COLONEL ROBERT INGERSOLL", confirmed present verbatim in the
     C5a pool: {jupiter, saturn, mercury, venus, mars, moon, sun, luna,
     lindsay, sarah, bernhardt, twain, sullivan, vivekananda, besant,
     somerset, melba, ingersoll, leslie, stead, chamberlain, arnold,
     leighton, curtiss, parkhurst, higinbotham, beresford, buller, savage,
     lubbock, aberdeen, meyer} -- every single one of these confirmed
     present at least once in the raw C5a token pool before this list was
     written, not asserted a priori.
  6. ordinary_prose_word       -- real dictionary word (nltk 'words'
     corpus, same oracle as U0.5) not matched by any rule above. THE
     SIGNAL BUCKET -- everything else in this taxonomy is boilerplate/
     structural churn by construction; this is the only category that
     could represent genuine lost or gained doctrine.
  7. other_unclassified_nonword_fragment -- NOT one of the 7 categories
     the instructing prompt named; added here for honesty rather than
     force-fitting garbage OCR fragments (e.g. "eee", "cece", "ccc" --
     confirmed present at high frequency in the raw C5b pool) into
     "ordinary prose word" (they are not real words) or any structural
     category (they match no observed structural pattern). Reported
     separately, clearly labeled as an addition beyond the requested 7.

No merge-policy recommendation anywhere in this script or its report.
"""

from __future__ import annotations

import difflib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bidirectional_corruption_census_S80 as census  # noqa: E402  -- reuse, not reinvention

import pdfplumber  # noqa: E402

ROOT = census.ROOT
REPORT_PATH = ROOT / "diagnostics" / "c5_decomposition_S80.md"
LATEST_RUN_PATH = ROOT / "diagnostics" / "latest_run.md"
SIDECAR_DATA_PATH = ROOT / "diagnostics" / "bidirectional_corruption_census_S80_data.json"

_EDGE_WINDOW = 40  # tokens from either end of the page counted as "edge" for requirement (d)
_SPAN_RADIUS = 7   # ~15-word window (radius*2 + the token itself) for quoted examples

_PLATE_MARKERS = {"plate", "fig"}
_RUNNING_HEAD_MARKERS = {"the", "hand", "of", "right", "left", "cheiro", "language"}
_PROPER_NOUN_SET = {
    "jupiter", "saturn", "mercury", "venus", "mars", "moon", "sun", "luna",
    "lindsay", "sarah", "bernhardt", "twain", "sullivan", "vivekananda", "besant",
    "somerset", "melba", "ingersoll", "leslie", "stead", "chamberlain", "arnold",
    "leighton", "curtiss", "parkhurst", "higinbotham", "beresford", "buller",
    "savage", "lubbock", "aberdeen", "meyer",
}

_ROMAN_DIGITS = [(100, "c"), (90, "xc"), (50, "l"), (40, "xl"), (10, "x"),
                 (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]


def _int_to_roman(n: int) -> str:
    out = []
    for value, sym in _ROMAN_DIGITS:
        while n >= value:
            out.append(sym)
            n -= value
    return "".join(out)


def _augmented_wordset(base: set[str]) -> tuple[set[str], dict]:
    """Requirement (e). Reports which of the task-suggested allowlist words
    were already covered by the base nltk 'words' corpus (checked, not
    assumed) vs. genuinely new."""
    romans = {_int_to_roman(n) for n in range(1, 101)}  # I-C per instruction
    suggested = ["cheiro", "mensal", "hepatica", "rascettes", "luna", "saturnian"]
    already_covered = sorted(w for w in suggested if w in base)
    genuinely_new_words = sorted(w for w in suggested if w not in base)
    augmented = base | romans | set(suggested)
    detail = {
        "roman_numerals_added": len(romans - base),
        "suggested_already_covered": already_covered,
        "suggested_genuinely_new": genuinely_new_words,
    }
    return augmented, detail


def _subcategorize(token: str, wordset: set[str]) -> str:
    if census._is_roman_numeral(token):
        return "roman_numeral"
    if len(token) == 1:
        return "punctuation_single_char_non_alpha"
    low = token.lower()
    if low in _PLATE_MARKERS:
        return "plate_caption_fragment"
    if low in _RUNNING_HEAD_MARKERS:
        return "running_head_title_fragment"
    if low in _PROPER_NOUN_SET:
        return "proper_noun"
    if low in wordset:
        return "ordinary_prose_word"
    return "other_unclassified_nonword_fragment"


def _align_classify_positions(native_tokens: list[str], corpus_tokens: list[str], wordset: set[str]):
    """Position-annotated replica of census._align_and_classify -- see
    module docstring. Returns (counts, pairs) where every pair dict has
    native/corpus/class, and C5 entries additionally carry position/list_len."""
    native_lower = [t.lower() for t in native_tokens]
    corpus_lower = [t.lower() for t in corpus_tokens]
    sm = difflib.SequenceMatcher(None, native_lower, corpus_lower, autojunk=False)

    counts = {"C1": 0, "C2": 0, "C3": 0, "C4": 0, "C5": 0}
    pairs: list[dict] = []

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace":
            n_block = native_tokens[i1:i2]
            c_block = corpus_tokens[j1:j2]
            m = min(len(n_block), len(c_block))
            for k in range(m):
                nt, ct = n_block[k], c_block[k]
                cls = census._classify_pair(nt, ct, wordset)
                counts[cls] += 1
                pairs.append({"native": nt, "corpus": ct, "class": cls})
            leftover_is_native = len(n_block) > len(c_block)
            leftover = n_block[m:] if leftover_is_native else c_block[m:]
            leftover_start = (i1 + m) if leftover_is_native else (j1 + m)
            counts["C5"] += len(leftover)
            for offset, tok in enumerate(leftover):
                pairs.append({
                    "native": tok if leftover_is_native else None,
                    "corpus": tok if not leftover_is_native else None,
                    "class": "C5",
                    "position": leftover_start + offset,
                    "list_len": len(native_tokens) if leftover_is_native else len(corpus_tokens),
                })
        elif tag == "delete":
            block = native_tokens[i1:i2]
            counts["C5"] += len(block)
            for offset, tok in enumerate(block):
                pairs.append({"native": tok, "corpus": None, "class": "C5",
                               "position": i1 + offset, "list_len": len(native_tokens)})
        elif tag == "insert":
            block = corpus_tokens[j1:j2]
            counts["C5"] += len(block)
            for offset, tok in enumerate(block):
                pairs.append({"native": None, "corpus": tok, "class": "C5",
                               "position": j1 + offset, "list_len": len(corpus_tokens)})

    return counts, pairs


def _span_text(tokens: list[str], position: int, radius: int = _SPAN_RADIUS) -> str:
    lo = max(0, position - radius)
    hi = min(len(tokens), position + radius + 1)
    return " ".join(tokens[lo:hi])


def main() -> int:
    try:
        wordset, oracle_desc = census._load_wordset()
        augmented_wordset, augment_detail = _augmented_wordset(wordset)
        collection = census._get_collection()
        pdf_sha256 = census._sha256_file(census.CHEIRO_PDF)

        with pdfplumber.open(census.CHEIRO_PDF) as pdf:
            self_check_results = census._run_mandatory_self_checks(pdf)

            page_rows = []
            c5a_subcat_totals: Counter = Counter()
            c5b_subcat_totals: Counter = Counter()
            page_data: dict[int, dict] = {}  # page_index -> {native_tokens, corpus_tokens, pairs}

            totals_original = {"C1": 0, "C2": 0, "C3": 0, "C4": 0, "C5": 0}

            for page_index in range(len(pdf.pages)):
                native_text = census._native_text(pdf, page_index)
                if len(native_text) == 0:
                    continue
                page_ref = page_index + 1
                corpus_text, chunk_count = census._corpus_text_for_page(collection, page_ref, page_index)

                native_tokens = census._tokenize(native_text)
                corpus_tokens = census._tokenize(corpus_text)
                counts, pairs = _align_classify_positions(native_tokens, corpus_tokens, wordset)

                for k in totals_original:
                    totals_original[k] += counts[k]

                page_c5a_subcat: Counter = Counter()
                page_c5b_subcat: Counter = Counter()
                page_c5a_positions_edge = 0
                page_c5a_positions_mid = 0

                for p in pairs:
                    if p["class"] != "C5":
                        continue
                    is_c5a = p.get("native") is not None
                    tok = p["native"] if is_c5a else p["corpus"]
                    subcat = _subcategorize(tok, wordset)
                    if is_c5a:
                        c5a_subcat_totals[subcat] += 1
                        page_c5a_subcat[subcat] += 1
                        if subcat == "ordinary_prose_word":
                            pos, ln = p["position"], p["list_len"]
                            if pos < _EDGE_WINDOW or pos >= ln - _EDGE_WINDOW:
                                page_c5a_positions_edge += 1
                            else:
                                page_c5a_positions_mid += 1
                    else:
                        c5b_subcat_totals[subcat] += 1
                        page_c5b_subcat[subcat] += 1

                page_rows.append({
                    "page_index": page_index,
                    "page_ref": page_ref,
                    "native_char_count": len(native_text),
                    "corpus_char_count": len(corpus_text),
                    "c5a_total": sum(page_c5a_subcat.values()),
                    "c5b_total": sum(page_c5b_subcat.values()),
                    "c5a_ordinary_prose": page_c5a_subcat.get("ordinary_prose_word", 0),
                    "c5b_ordinary_prose": page_c5b_subcat.get("ordinary_prose_word", 0),
                    "c5a_edge": page_c5a_positions_edge,
                    "c5a_mid": page_c5a_positions_mid,
                })
                page_data[page_index] = {
                    "native_tokens": native_tokens,
                    "corpus_tokens": corpus_tokens,
                    "pairs": pairs,
                }

        # ─── Fidelity check against the already-committed U0.5 sidecar ────
        if not SIDECAR_DATA_PATH.exists():
            raise RuntimeError(f"Expected committed sidecar not found: {SIDECAR_DATA_PATH}")
        with open(SIDECAR_DATA_PATH, "r", encoding="utf-8") as f:
            sidecar = json.load(f)
        recorded_totals = sidecar["totals"]
        if totals_original != recorded_totals:
            raise AssertionError(
                f"REPLICA FIDELITY CHECK FAILED — this script's own C1-C5 totals "
                f"{totals_original} do not match the committed sidecar's {recorded_totals}. "
                "Refusing to write output on an unverified alignment replica."
            )

        # ─── Requirement (a): C5a vs C5b totals ────────────────────────
        c5a_grand_total = sum(c5a_subcat_totals.values())
        c5b_grand_total = sum(c5b_subcat_totals.values())

        # ─── Requirement (b): subcategory tables, both sides ───────────
        # (dicts already built: c5a_subcat_totals, c5b_subcat_totals)

        # ─── Requirement (c): top 10 pages, top 3 quoted spans each side ──
        top_c5a_pages = sorted(page_rows, key=lambda r: r["c5a_ordinary_prose"], reverse=True)[:10]
        top_c5b_pages = sorted(page_rows, key=lambda r: r["c5b_ordinary_prose"], reverse=True)[:10]

        def _quoted_examples(top_pages, side_key, native_side: bool, limit=3):
            examples = []
            for row in top_pages[:limit]:
                pidx = row["page_index"]
                pd = page_data[pidx]
                found = None
                for p in pd["pairs"]:
                    if p["class"] != "C5":
                        continue
                    is_c5a = p.get("native") is not None
                    if is_c5a != native_side:
                        continue
                    tok = p["native"] if is_c5a else p["corpus"]
                    if _subcategorize(tok, wordset) != "ordinary_prose_word":
                        continue
                    found = p
                    break
                if found is None:
                    examples.append({"page_index": pidx, "token": None, "span": "(no ordinary-prose C5 token found on this page)"})
                    continue
                tokens = pd["native_tokens"] if native_side else pd["corpus_tokens"]
                span = _span_text(tokens, found["position"])
                examples.append({"page_index": pidx, "token": found["native"] if native_side else found["corpus"], "span": span})
            return examples

        top_c5a_examples = _quoted_examples(top_c5a_pages, "c5a", native_side=True)
        top_c5b_examples = _quoted_examples(top_c5b_pages, "c5b", native_side=False)

        # ─── Requirement (d): edge vs mid-page clustering, C5a ordinary-prose only ──
        total_edge = sum(r["c5a_edge"] for r in page_rows)
        total_mid = sum(r["c5a_mid"] for r in page_rows)

        # ─── Requirement (e): augmented-oracle C1/C2/C3 delta ──────────
        # Alignment structure is oracle-independent (SequenceMatcher only
        # compares token equality); only classification of already-aligned
        # non-C5 pairs changes. Reclassify the SAME stored pairs, no re-run
        # of SequenceMatcher.
        augmented_totals = {"C1": 0, "C2": 0, "C3": 0, "C4": 0}
        for pd in page_data.values():
            for p in pd["pairs"]:
                if p["class"] == "C5":
                    continue
                new_cls = census._classify_pair(p["native"], p["corpus"], augmented_wordset)
                augmented_totals[new_cls] += 1

        output = {
            "oracle_original": oracle_desc,
            "augment_detail": augment_detail,
            "source_pdf_sha256": pdf_sha256,
            "self_check_results": self_check_results,
            "totals_original": totals_original,
            "c5a_grand_total": c5a_grand_total,
            "c5b_grand_total": c5b_grand_total,
            "c5a_subcat_totals": dict(c5a_subcat_totals),
            "c5b_subcat_totals": dict(c5b_subcat_totals),
            "top_c5a_pages": top_c5a_pages,
            "top_c5b_pages": top_c5b_pages,
            "top_c5a_examples": top_c5a_examples,
            "top_c5b_examples": top_c5b_examples,
            "edge_window": _EDGE_WINDOW,
            "c5a_ordinary_prose_edge": total_edge,
            "c5a_ordinary_prose_mid": total_mid,
            "augmented_totals": augmented_totals,
            "page_rows": page_rows,
        }

        _write_markdown_report(output)
        print(f"Wrote {REPORT_PATH} ({REPORT_PATH.stat().st_size} bytes)")
        LATEST_RUN_PATH.write_text(REPORT_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Overwrote {LATEST_RUN_PATH}")
        for c in self_check_results:
            print(f"  [PASS] {c['assertion']}")
        print("  [PASS] Replica fidelity check vs committed U0.5 sidecar")
        return 0

    except Exception as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 1


def _write_markdown_report(d: dict) -> None:
    lines = []
    lines.append("# C5 DECOMPOSITION — S80 U0.6 — Cheiro only")
    lines.append("")
    lines.append(
        "Read-only, diagnostics-only. No repair logic, no new alignment design (reuses "
        "scripts/bidirectional_corruption_census_S80.py's algorithm via a position-"
        "annotated replica, fidelity-checked against its committed sidecar before this "
        "report was written). See scripts/c5_decomposition_S80.py module docstring for "
        "full subcategory-rule derivation."
    )
    lines.append("")
    lines.append(f"- Base oracle: {d['oracle_original']}")
    lines.append(f"- source_pdf_sha256: `{d['source_pdf_sha256']}`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Ground-truth self-checks")
    lines.append("")
    lines.append("| Assertion | Expected | Observed | Status |")
    lines.append("|---|---|---|---|")
    for c in d["self_check_results"]:
        lines.append(f"| {c['assertion']} | {c['expected']} | {c['observed']} | {c['status']} |")
    lines.append(
        "| Replica fidelity vs committed sidecar (C1-C5 totals) | "
        f"{d['totals_original']} | (matched — see script's own AssertionError guard) | PASS |"
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## (a) C5a vs C5b totals")
    lines.append("")
    c5a_t, c5b_t = d["c5a_grand_total"], d["c5b_grand_total"]
    total_c5 = c5a_t + c5b_t
    lines.append(f"- **C5a (native_only, corpus lost content): {c5a_t}** ({c5a_t/total_c5*100:.2f}% of C5)")
    lines.append(f"- **C5b (corpus_only, native lost content — i.e. what a native-preferred repair would DISCARD): {c5b_t}** ({c5b_t/total_c5*100:.2f}% of C5)")
    lines.append(f"- **C5a:C5b ratio = {c5a_t/c5b_t:.3f}**" if c5b_t else "- C5a:C5b ratio undefined (C5b == 0)")
    lines.append(
        "- Plainly: the vast majority of C5 is native tokens with no corpus counterpart, "
        "not the other way around. Whether that is meaningful depends entirely on "
        "subcategory (b) below — see the ordinary_prose_word row specifically."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## (b) Subcategory tables, both sides")
    lines.append("")
    _SUBCAT_ORDER = [
        "roman_numeral", "printed_folio_number_bare_digits", "plate_caption_fragment",
        "running_head_title_fragment", "proper_noun", "ordinary_prose_word",
        "punctuation_single_char_non_alpha", "other_unclassified_nonword_fragment",
    ]
    lines.append("### C5a (native_only — corpus lost this content)")
    lines.append("")
    lines.append("| Subcategory | Count | % of C5a |")
    lines.append("|---|---|---|")
    for sc in _SUBCAT_ORDER:
        if sc == "printed_folio_number_bare_digits":
            lines.append(f"| {sc} | 0 (structurally impossible — see script docstring rule 2's note) | 0.00% |")
            continue
        v = d["c5a_subcat_totals"].get(sc, 0)
        marker = " **<- THE SIGNAL** " if sc == "ordinary_prose_word" else ""
        lines.append(f"| {sc}{marker} | {v} | {v/c5a_t*100:.2f}% |")
    lines.append("")
    lines.append("### C5b (corpus_only — native lost this content)")
    lines.append("")
    lines.append("| Subcategory | Count | % of C5b |")
    lines.append("|---|---|---|")
    for sc in _SUBCAT_ORDER:
        if sc == "printed_folio_number_bare_digits":
            lines.append(f"| {sc} | 0 (structurally impossible — see script docstring rule 2's note) | 0.00% |")
            continue
        v = d["c5b_subcat_totals"].get(sc, 0)
        marker = " **<- THE SIGNAL** " if sc == "ordinary_prose_word" else ""
        lines.append(f"| {sc}{marker} | {v} | {v/c5b_t*100:.2f}% |")
    lines.append("")
    lines.append(
        f"**Ordinary-prose signal, isolated: C5a={d['c5a_subcat_totals'].get('ordinary_prose_word',0)}, "
        f"C5b={d['c5b_subcat_totals'].get('ordinary_prose_word',0)}.** Everything else in both tables "
        "is boilerplate/structural churn by this taxonomy's own construction (roman numerals, plate "
        "captions, running heads, proper nouns, single-char diagram labels, and non-word OCR garbage)."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## (c) Top 10 pages by ordinary-prose C5 count, both sides")
    lines.append("")
    lines.append("### Top 10 — C5a ordinary-prose (candidate lost doctrine — corpus never captured this native content)")
    lines.append("")
    lines.append("| Rank | page_index | page_ref | c5a_ordinary_prose | native_chars | corpus_chars |")
    lines.append("|---|---|---|---|---|---|")
    for i, r in enumerate(d["top_c5a_pages"], 1):
        lines.append(f"| {i} | {r['page_index']} | {r['page_ref']} | {r['c5a_ordinary_prose']} | {r['native_char_count']} | {r['corpus_char_count']} |")
    lines.append("")
    lines.append("**Top 3, quoted (~15-word span around the divergent token, from NATIVE text):**")
    lines.append("")
    for i, ex in enumerate(d["top_c5a_examples"], 1):
        lines.append(f"{i}. page_index={ex['page_index']}, token=`{ex['token']}` — \"{ex['span']}\"")
    lines.append("")
    lines.append("### Top 10 — C5b ordinary-prose (candidate deletion risk — what a native-preferred repair would discard)")
    lines.append("")
    lines.append("| Rank | page_index | page_ref | c5b_ordinary_prose | native_chars | corpus_chars |")
    lines.append("|---|---|---|---|---|---|")
    for i, r in enumerate(d["top_c5b_pages"], 1):
        lines.append(f"| {i} | {r['page_index']} | {r['page_ref']} | {r['c5b_ordinary_prose']} | {r['native_char_count']} | {r['corpus_char_count']} |")
    lines.append("")
    lines.append("**Top 3, quoted (~15-word span around the divergent token, from CORPUS text):**")
    lines.append("")
    for i, ex in enumerate(d["top_c5b_examples"], 1):
        lines.append(f"{i}. page_index={ex['page_index']}, token=`{ex['token']}` — \"{ex['span']}\"")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"## (d) C5a ordinary-prose: edge-clustered or mid-page? (edge window = first/last {d['edge_window']} tokens)")
    lines.append("")
    edge, mid = d["c5a_ordinary_prose_edge"], d["c5a_ordinary_prose_mid"]
    tot = edge + mid
    if tot:
        lines.append(f"- Edge-window occurrences: {edge} ({edge/tot*100:.2f}%)")
        lines.append(f"- Mid-page occurrences: {mid} ({mid/tot*100:.2f}%)")
        if mid > edge:
            lines.append(
                "- **Majority MID-PAGE.** This does NOT look like a chunk-boundary artifact "
                "(which would cluster at page edges, where chunker.py's paragraph/window "
                "splits happen); it is distributed through the body of the page — consistent "
                "with genuine content loss, not a benign boundary effect. Reported as measured, "
                "no merge-policy conclusion drawn."
            )
        else:
            lines.append(
                "- **Majority EDGE-CLUSTERED.** Consistent with a benign chunk-boundary artifact "
                "(chunker.py's paragraph-merge/sliding-window splits happen at page or chunk "
                "boundaries) rather than genuine mid-page content loss. Reported as measured, no "
                "merge-policy conclusion drawn."
            )
    else:
        lines.append("- No C5a ordinary-prose occurrences to classify (see table (b) above).")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## (e) Augmented-oracle C1/C2/C3 delta (retires the U0.5 193-position caveat)")
    lines.append("")
    ad = d["augment_detail"]
    lines.append(f"- Roman numerals I-C added to the oracle: {ad['roman_numerals_added']} entries (all were absent from the base wordlist).")
    lines.append(f"- Task-suggested allowlist words ALREADY covered by the base nltk 'words' corpus (checked, not assumed — no-ops, added for completeness only): {', '.join(ad['suggested_already_covered']) or '(none)'}")
    lines.append(f"- Task-suggested allowlist words genuinely NEW to the augmented oracle: {', '.join(ad['suggested_genuinely_new']) or '(none)'}")
    lines.append("")
    lines.append("| Class | Original count | Augmented count | Delta |")
    lines.append("|---|---|---|---|")
    orig = d["totals_original"]
    aug = d["augmented_totals"]
    for k in ["C1", "C2", "C3", "C4"]:
        delta = aug[k] - orig[k]
        sign = "+" if delta >= 0 else ""
        lines.append(f"| {k} | {orig[k]} | {aug[k]} | {sign}{delta} |")
    orig_ratio = orig["C1"] / orig["C2"] if orig["C2"] else None
    aug_ratio = aug["C1"] / aug["C2"] if aug["C2"] else None
    lines.append("")
    lines.append(
        f"**C1:C2 ratio, original oracle: {orig_ratio:.3f}** (C1={orig['C1']}, C2={orig['C2']})  \n"
        f"**C1:C2 ratio, augmented oracle: {aug_ratio:.3f}** (C1={aug['C1']}, C2={aug['C2']})"
    )
    lines.append("")
    lines.append(
        "Original counts are NOT replaced above — both rows are shown side by side, per "
        "instruction. Alignment (which tokens got paired at all) is IDENTICAL between the two "
        "runs; only the real-word classification of already-aligned C1-C4 pairs changed."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## (f) Merge policy")
    lines.append("")
    lines.append(
        "**No recommendation is made here.** This report is measurement only, per the "
        "instructing prompt's explicit scope. The C5a/C5b split, the subcategory tables "
        "isolating the ordinary-prose signal, the top-page examples, the edge-vs-mid-page "
        "clustering result, and the augmented-oracle delta above are the evidence; the policy "
        "ruling is a design-chat decision made after reading this census, not before."
    )
    lines.append("")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
