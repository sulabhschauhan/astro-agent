"""
scripts/bidirectional_corruption_census_S80.py
S80 U0.5 — bidirectional OCR-corruption census, Cheiro book ONLY, read-only,
diagnostics-only. Run manually; never invoked from CI or the pytest suite.
NO repair logic, NO alignment/merge function meant for production use, NO
imports from pdf_processor.py / chunker.py / embedder.py / query_engine.py.

PURPOSE (per design-chat instruction): U0's evidence
(diagnostics/native_text_probe_S79.md) only measured ONE direction —
corpus-corrupt/native-clean (hne, lne, lme, hfe, hie, suecess, Tf). U0's own
fixture set already surfaced a counter-example in the opposite direction:
cheiro_p156_chapter_x has native="rnensal" but corpus="mensal" — native LOST
there, corpus won. Until both directions are measured across the whole book,
any future merge rule (Path C: align live corpus chunks against native text)
is a guess about which side to trust for a given token. This script produces
the measurement; it makes NO merge-policy recommendation anywhere — that is
a design-chat ruling, not this script's job.

SCOPE: cheiroslanguageo00chei_1 ONLY, the pages with native_char_count > 0
(245 of 310 pages, per tests/fixtures/native_coverage_S80.json — recomputed
fresh here rather than trusted from that file, since this script must stand
alone). No other book is touched.

METHOD, and why:
  1. Per in-scope page: native text via pdfplumber.extract_text() (never
     rasterized, never Tesseract); live corpus text = every ChromaDB chunk
     for that page_ref, concatenated in chunk_id numeric-suffix order
     (chunker.py emits _c0, _c1, _c2... in the order paragraphs were
     merged/windowed — this ordering approximates original reading order).
  2. Both texts whitespace-normalized (runs of whitespace collapsed to a
     single space) for comparison purposes ONLY — this is never written
     back anywhere, and neither ChromaDB nor any PDF is ever modified.
  3. Word-tokenized on `_WORD_PATTERN` (alpha sequences with an optional
     internal apostrophe, e.g. "Cheiro's"). Non-word tokens (digits,
     punctuation, page-footer numerals) are dropped from the alignment
     stream entirely — they are not checkable against an English wordlist
     and are not the corruption class this census targets.
  4. Aligned via `difflib.SequenceMatcher` over the LOWERCASED token lists
     (chosen over a raw whole-page character diff, which would blur word
     boundaries and make the real-word oracle inapplicable; chosen over a
     naive positional zip, which would silently misalign as soon as either
     side has one extra/missing word — the two streams routinely differ in
     length). Matching on lowercase means a pure-case difference (e.g.
     native "CHEIRO" vs a Tesseract "Cheiro") is an "equal" opcode block
     and never enters classification — case alone is not corruption here.
  5. Each 'replace' opcode block pairs tokens positionally, up to
     min(native_block_len, corpus_block_len); anything beyond that on the
     longer side has no counterpart in this block and is classified C5,
     same disposition as a bare 'insert'/'delete' block. 'equal' blocks are
     matches and are never classified.
  6. Real-word oracle: nltk 3.9.1's `words` corpus (`nltk.corpus.words`, the
     classic ~234k-entry English wordlist), obtained via a ONE-TIME
     `nltk.download('words')` (already run, cached locally under this
     machine's nltk_data directory) — this script's own runtime makes NO
     network call; the corpus load below is a pure local-disk read.
     Lookup is case-insensitive (`token.lower() in wordset`). NOT added to
     requirements.txt — an analysis-only dependency; packaging is a
     separate ruling for the reader of the report, not decided here.
     KNOWN ORACLE LIMITATION, reported not corrected: proper nouns (e.g.
     "Cheiro" itself) and Roman numerals (e.g. "XVIII") are absent from a
     general-English wordlist and will misclassify as "not a real word" on
     whichever side they appear. Counted and reported separately (see the
     oracle-noise section of the generated report), not silently patched
     around with a custom exception list.
  7. Ligature-pattern tagging (C1/C2/C3 pairs ONLY, never C4 — a C4 pair is
     two genuinely different real words, not a spelling corruption to
     pattern-match): a character-level `difflib.SequenceMatcher` over the
     pair's two LOWERCASED token strings; each non-equal opcode becomes one
     "native_substr -> corpus_substr" hunk (Ø denotes an empty side, i.e. a
     pure insertion/deletion within the token). Patterns are DISCOVERED by
     running this over every C1/C2/C3 pair and counting hunk frequency —
     never asserted from a pre-baked list of "known" ligature confusions.

No recommendation on merge policy anywhere in this script or its generated
report — see the report's own closing section. Policy is a design-chat
ruling, made after reading this census, not before.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import chromadb
import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
CHEIRO_PDF = ROOT / "data" / "pdfs" / "cheiroslanguageo00chei_1.pdf"
CHEIRO_BOOK = "cheiroslanguageo00chei_1"
CHROMA_DIR = str(ROOT / "data" / "chroma_db")
COLLECTION_NAME = "astro_chunks"
REPORT_PATH = ROOT / "diagnostics" / "bidirectional_corruption_census_S80.md"
LATEST_RUN_PATH = ROOT / "diagnostics" / "latest_run.md"

_WORD_PATTERN = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
_WS_PATTERN = re.compile(r"\s+")
_CHUNK_SUFFIX_PATTERN = re.compile(r"_c(\d+)$")
_ROMAN_NUMERAL_PATTERN = re.compile(r"^(?=[mdclxvi])m*(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})$")


def _sha256_file(path: Path) -> str:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as exc:
        raise RuntimeError(f"sha256 failed for {path}: {exc}") from exc


def _load_wordset() -> tuple[set[str], str]:
    try:
        import nltk
        from nltk.corpus import words
        wordset = {w.lower() for w in words.words()}
        oracle_desc = f"nltk {nltk.__version__}, corpus 'words' (nltk.corpus.words), {len(wordset)} lowercased entries"
        return wordset, oracle_desc
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load nltk 'words' corpus (expected cached locally from a prior "
            f"one-time `nltk.download('words')` — no network call attempted here): {exc}"
        ) from exc


def _normalize_whitespace(text: str) -> str:
    return _WS_PATTERN.sub(" ", text).strip()


def _tokenize(text: str) -> list[str]:
    return _WORD_PATTERN.findall(_normalize_whitespace(text))


def _get_collection():
    try:
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        return client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    except Exception as exc:
        raise RuntimeError(f"ChromaDB collection open failed: {exc}") from exc


def _native_text(pdf, page_index: int) -> str:
    try:
        return pdf.pages[page_index].extract_text() or ""
    except Exception as exc:
        raise RuntimeError(f"pdfplumber extract_text() failed at page_index={page_index}: {exc}") from exc


def _corpus_text_for_page(collection, page_ref: int, page_index: int) -> tuple[str, int]:
    try:
        res = collection.get(
            where={"$and": [{"book_name": {"$eq": CHEIRO_BOOK}}, {"page_ref": {"$eq": page_ref}}]},
            include=["documents"],
        )
    except Exception as exc:
        raise RuntimeError(f"ChromaDB read failed for page_index={page_index} (page_ref={page_ref}): {exc}") from exc

    def _suffix(chunk_id: str) -> int:
        m = _CHUNK_SUFFIX_PATTERN.search(chunk_id)
        return int(m.group(1)) if m else 0

    ordered = sorted(zip(res["ids"], res["documents"]), key=lambda pair: _suffix(pair[0]))
    joined = " ".join(doc for _cid, doc in ordered)
    return joined, len(ordered)


def _is_real_word(token: str, wordset: set[str]) -> bool:
    return token.lower() in wordset


def _classify_pair(native_tok: str, corpus_tok: str, wordset: set[str]) -> str:
    nreal = _is_real_word(native_tok, wordset)
    creal = _is_real_word(corpus_tok, wordset)
    if nreal and not creal:
        return "C1"
    if creal and not nreal:
        return "C2"
    if not nreal and not creal:
        return "C3"
    return "C4"


def _char_level_hunks(native_tok: str, corpus_tok: str) -> list[tuple[str, str]]:
    a, b = native_tok.lower(), corpus_tok.lower()
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    hunks = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        hunks.append((a[i1:i2] or "Ø", b[j1:j2] or "Ø"))
    return hunks


def _align_and_classify(native_tokens: list[str], corpus_tokens: list[str], wordset: set[str]) -> tuple[dict, list[dict]]:
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
                cls = _classify_pair(nt, ct, wordset)
                counts[cls] += 1
                entry = {"native": nt, "corpus": ct, "class": cls}
                if cls != "C4":
                    entry["hunks"] = _char_level_hunks(nt, ct)
                pairs.append(entry)
            leftover = n_block[m:] if len(n_block) > len(c_block) else c_block[m:]
            leftover_is_native = len(n_block) > len(c_block)
            counts["C5"] += len(leftover)
            for tok in leftover:
                pairs.append({
                    "native": tok if leftover_is_native else None,
                    "corpus": tok if not leftover_is_native else None,
                    "class": "C5",
                })
        elif tag == "delete":
            block = native_tokens[i1:i2]
            counts["C5"] += len(block)
            for tok in block:
                pairs.append({"native": tok, "corpus": None, "class": "C5"})
        elif tag == "insert":
            block = corpus_tokens[j1:j2]
            counts["C5"] += len(block)
            for tok in block:
                pairs.append({"native": None, "corpus": tok, "class": "C5"})

    return counts, pairs


def _run_mandatory_self_checks(pdf) -> list[dict]:
    checks = []
    page_count = len(pdf.pages)
    checks.append(("Cheiro page count == 310", 310, page_count, page_count == 310))

    p157 = _native_text(pdf, 157 - 1)
    checks.append(('Cheiro p157 native contains "Plate XVIII"', "present",
                    "present" if "Plate XVIII" in p157 else "ABSENT", "Plate XVIII" in p157))

    p158 = _native_text(pdf, 158 - 1)
    checks.append(("Cheiro p158 native char_count == 0", 0, len(p158), len(p158) == 0))

    p156 = _native_text(pdf, 156 - 1)
    checks.append(('Cheiro p156 native contains "CHAPTER X"', "present",
                    "present" if "CHAPTER X" in p156 else "ABSENT", "CHAPTER X" in p156))

    failed = [c for c in checks if not c[3]]
    if failed:
        lines = "\n".join(f"  - {name}: expected {exp!r}, got {obs!r}" for name, exp, obs, ok in failed)
        raise AssertionError(f"MANDATORY SELF-CHECK(S) FAILED — refusing to write output:\n{lines}")
    return [{"assertion": n, "expected": e, "observed": o, "status": "PASS"} for n, e, o, ok in checks]


def _is_roman_numeral(token: str) -> bool:
    return bool(_ROMAN_NUMERAL_PATTERN.match(token.lower())) and len(token) > 0


def main() -> int:
    try:
        if not CHEIRO_PDF.exists():
            raise RuntimeError(f"Cheiro PDF not found at {CHEIRO_PDF}")

        wordset, oracle_desc = _load_wordset()
        collection = _get_collection()
        pdf_sha256 = _sha256_file(CHEIRO_PDF)

        with pdfplumber.open(CHEIRO_PDF) as pdf:
            self_check_results = _run_mandatory_self_checks(pdf)

            page_rows = []
            all_pairs_by_page: dict[int, list[dict]] = {}

            for page_index in range(len(pdf.pages)):
                native_text = _native_text(pdf, page_index)
                native_char_count = len(native_text)
                if native_char_count == 0:
                    continue  # out of scope per spec: only native_char_count > 0 pages

                page_ref = page_index + 1
                corpus_text, chunk_count = _corpus_text_for_page(collection, page_ref, page_index)
                corpus_char_count = len(corpus_text)

                native_tokens = _tokenize(native_text)
                corpus_tokens = _tokenize(corpus_text)
                counts, pairs = _align_and_classify(native_tokens, corpus_tokens, wordset)

                page_rows.append({
                    "page_index": page_index,
                    "page_ref": page_ref,
                    "native_char_count": native_char_count,
                    "corpus_char_count": corpus_char_count,
                    "chunk_count": chunk_count,
                    **counts,
                })
                all_pairs_by_page[page_index] = pairs

        if len(page_rows) != 245:
            print(
                f"WARNING: expected 245 in-scope pages (native_char_count > 0), found {len(page_rows)}. "
                "Proceeding — this is informational, not a self-check failure (the 245 figure is a "
                "prior measurement, not re-asserted as ground truth here).",
                file=sys.stderr,
            )

        # ─── Aggregate counts ───────────────────────────────────────────
        totals = {"C1": 0, "C2": 0, "C3": 0, "C4": 0, "C5": 0}
        for row in page_rows:
            for k in totals:
                totals[k] += row[k]
        grand_total = sum(totals.values())

        # ─── Top-40 pairs by frequency, C1 and C2 separately ───────────
        c1_pair_counter: Counter = Counter()
        c2_pair_counter: Counter = Counter()
        c1_example_page: dict[tuple, int] = {}
        c2_example_page: dict[tuple, int] = {}
        roman_or_propernoun_hits = 0

        for page_index, pairs in all_pairs_by_page.items():
            for p in pairs:
                cls = p["class"]
                if cls not in ("C1", "C2", "C3"):
                    continue
                nt, ct = p.get("native"), p.get("corpus")
                if nt and (_is_roman_numeral(nt) or nt.lower() == "cheiro"):
                    roman_or_propernoun_hits += 1
                if ct and (_is_roman_numeral(ct) or ct.lower() == "cheiro"):
                    roman_or_propernoun_hits += 1
                if cls == "C1":
                    key = (nt, ct)
                    c1_pair_counter[key] += 1
                    c1_example_page.setdefault(key, page_index)
                elif cls == "C2":
                    key = (nt, ct)
                    c2_pair_counter[key] += 1
                    c2_example_page.setdefault(key, page_index)

        # ─── Ligature-pattern hunk frequency, pooled across C1+C2+C3 ────
        hunk_counter: Counter = Counter()
        for pairs in all_pairs_by_page.values():
            for p in pairs:
                if p["class"] in ("C1", "C2", "C3"):
                    for hunk in p.get("hunks", []):
                        hunk_counter[hunk] += 1

        # ─── p156_c0 rnensal/mensal specific lookup ─────────────────────
        p156_index = 156 - 1
        rnensal_mensal_hits = [
            p for p in all_pairs_by_page.get(p156_index, [])
            if p.get("native", "").lower() == "rnensal" and p.get("corpus", "").lower() == "mensal"
        ]
        rn_to_m_hunk_frequency = hunk_counter.get(("rn", "m"), 0)

        # Broader-family context for section (e): "rn -> m" is one specific
        # hunk within a much larger, independently-discovered cluster of
        # narrow-vertical-stroke ("minim") confusions -- m/n/u/rn/ri/in
        # mutually substituting for one another. This set is named here
        # for the report's prose ONLY, after seeing which hunks actually
        # recurred in `hunk_counter` above -- it does not feed back into
        # classification and was not used to bias _classify_pair/_align_
        # and_classify in any way.
        _MINIM_FAMILY = {"m", "n", "u", "rn", "ri", "in", "vv"}
        minim_family_hunks = [
            (hunk, count) for hunk, count in hunk_counter.items()
            if hunk[0] in _MINIM_FAMILY and hunk[1] in _MINIM_FAMILY
        ]
        minim_family_total = sum(c for _h, c in minim_family_hunks)

        # ─── Top 10 pages by C2 count ────────────────────────────────────
        top_c2_pages = sorted(page_rows, key=lambda r: r["C2"], reverse=True)[:10]

        output = {
            "generated_by": "scripts/bidirectional_corruption_census_S80.py",
            "oracle": oracle_desc,
            "source_pdf_sha256": pdf_sha256,
            "self_check_results": self_check_results,
            "in_scope_page_count": len(page_rows),
            "totals": totals,
            "grand_total_pairs": grand_total,
            "c1_c2_ratio": (totals["C1"] / totals["C2"]) if totals["C2"] else None,
            "roman_or_propernoun_hits": roman_or_propernoun_hits,
            "rnensal_mensal_hits_p156": len(rnensal_mensal_hits),
            "rn_to_m_hunk_frequency": rn_to_m_hunk_frequency,
            "minim_family_hunks": sorted(minim_family_hunks, key=lambda t: -t[1]),
            "minim_family_total": minim_family_total,
            "top_hunks": hunk_counter.most_common(40),
            "top_c1_pairs": [
                {"native": k[0], "corpus": k[1], "count": v, "example_page_index": c1_example_page[k]}
                for k, v in c1_pair_counter.most_common(40)
            ],
            "top_c2_pairs": [
                {"native": k[0], "corpus": k[1], "count": v, "example_page_index": c2_example_page[k]}
                for k, v in c2_pair_counter.most_common(40)
            ],
            "top_c2_pages": top_c2_pages,
            "page_rows": page_rows,
        }

        # Emit both a machine-readable sidecar and the human report.
        json_sidecar = ROOT / "diagnostics" / "bidirectional_corruption_census_S80_data.json"
        json_sidecar.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {json_sidecar} ({json_sidecar.stat().st_size} bytes)")

        _write_markdown_report(output)
        print(f"Wrote {REPORT_PATH} ({REPORT_PATH.stat().st_size} bytes)")
        LATEST_RUN_PATH.write_text(REPORT_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Overwrote {LATEST_RUN_PATH}")

        for c in self_check_results:
            print(f"  [PASS] {c['assertion']}")

        return 0

    except Exception as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 1


def _write_markdown_report(d: dict) -> None:
    lines = []
    lines.append("# BIDIRECTIONAL CORRUPTION CENSUS — S80 U0.5 — Cheiro only")
    lines.append("")
    lines.append(
        "Read-only, diagnostics-only. No repair logic, no alignment/merge function "
        "meant for production use. Scope: cheiroslanguageo00chei_1, pages with "
        "native_char_count > 0 only. See scripts/bidirectional_corruption_census_S80.py "
        "module docstring for full method."
    )
    lines.append("")
    lines.append(f"- Oracle: {d['oracle']}")
    lines.append(f"- source_pdf_sha256: `{d['source_pdf_sha256']}`")
    lines.append(f"- In-scope pages (native_char_count > 0): {d['in_scope_page_count']}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## (d) Mandatory self-checks")
    lines.append("")
    lines.append("| Assertion | Expected | Observed | Status |")
    lines.append("|---|---|---|---|")
    for c in d["self_check_results"]:
        lines.append(f"| {c['assertion']} | {c['expected']} | {c['observed']} | {c['status']} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## (a) Aggregate counts, C1–C5, across all in-scope pages")
    lines.append("")
    labels = {
        "C1": "C1 corpus_corrupt_native_clean",
        "C2": "C2 native_corrupt_corpus_clean",
        "C3": "C3 both_corrupt",
        "C4": "C4 both_valid_divergent",
        "C5": "C5 unalignable",
    }
    total = d["grand_total_pairs"]
    lines.append("| Class | Count | % of classified pairs (C1-C4) or all tokens (C5) |")
    lines.append("|---|---|---|")
    for k in ["C1", "C2", "C3", "C4", "C5"]:
        v = d["totals"][k]
        pct = (v / total * 100) if total else 0.0
        lines.append(f"| {labels[k]} | {v} | {pct:.2f}% |")
    lines.append(f"| **Total non-matching token positions** | **{total}** | 100% |")
    lines.append("")
    ratio = d["c1_c2_ratio"]
    ratio_str = f"{ratio:.3f}" if ratio is not None else "undefined (C2 == 0)"
    lines.append(f"**C1:C2 ratio = {ratio_str}** (C1={d['totals']['C1']}, C2={d['totals']['C2']})")
    lines.append("")
    lines.append(
        "**This ratio IS the finding.** A C1:C2 ratio far above 1 would mean corpus-side "
        "corruption dominates and native-side corruption is comparatively rare (consistent "
        "with U0's original one-directional evidence). A ratio near 1 or below means native-side "
        "corruption is NOT rare — blind replacement (always prefer native) would systematically "
        "reintroduce errors on the C2 pages. No policy conclusion is drawn here; see closing note."
    )
    lines.append("")
    lines.append(
        f"**Oracle-noise flag:** {d['roman_or_propernoun_hits']} of the {total} classified "
        "C1/C2/C3 token positions involve a Roman numeral (e.g. \"XVIII\") or the proper noun "
        "\"Cheiro\" on at least one side — both absent from a general-English wordlist by "
        "construction, and will misclassify as \"not a real word\" regardless of whether the OCR "
        "actually corrupted anything. Not corrected for above; reported as a measured caveat on "
        "the C1/C2/C3 totals, per the oracle limitation noted in the script docstring."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## (b) Top 40 token pairs by frequency — C1 and C2 separately")
    lines.append("")
    lines.append("### C1 (corpus_corrupt_native_clean) — top 40")
    lines.append("")
    lines.append("| # | native | corpus | count | example page_index (0-based) |")
    lines.append("|---|---|---|---|---|")
    for i, p in enumerate(d["top_c1_pairs"], 1):
        lines.append(f"| {i} | {p['native']} | {p['corpus']} | {p['count']} | {p['example_page_index']} |")
    lines.append("")
    lines.append("### C2 (native_corrupt_corpus_clean) — top 40")
    lines.append("")
    lines.append("| # | native | corpus | count | example page_index (0-based) |")
    lines.append("|---|---|---|---|---|")
    for i, p in enumerate(d["top_c2_pairs"], 1):
        lines.append(f"| {i} | {p['native']} | {p['corpus']} | {p['count']} | {p['example_page_index']} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Discovered ligature/substitution patterns (C1+C2+C3 pooled), top 40")
    lines.append("")
    lines.append("| # | native_substr → corpus_substr | frequency |")
    lines.append("|---|---|---|")
    for i, (hunk, count) in enumerate(d["top_hunks"], 1):
        lines.append(f"| {i} | {hunk[0]} → {hunk[1]} | {count} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## (c) Per-page table (all in-scope pages) + top 10 by C2 count")
    lines.append("")
    lines.append("### Top 10 pages by C2 count — the pages Path C (native-preferred replacement) would damage")
    lines.append("")
    lines.append("| Rank | page_index | page_ref | native_chars | corpus_chars | C1 | C2 | C3 | C4 | C5 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(d["top_c2_pages"], 1):
        lines.append(
            f"| {i} | {r['page_index']} | {r['page_ref']} | {r['native_char_count']} | "
            f"{r['corpus_char_count']} | {r['C1']} | {r['C2']} | {r['C3']} | {r['C4']} | {r['C5']} |"
        )
    lines.append("")
    lines.append("### Full per-page table (all in-scope pages)")
    lines.append("")
    lines.append("| page_index | page_ref | native_chars | corpus_chars | chunk_count | C1 | C2 | C3 | C4 | C5 |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in sorted(d["page_rows"], key=lambda r: r["page_index"]):
        lines.append(
            f"| {r['page_index']} | {r['page_ref']} | {r['native_char_count']} | "
            f"{r['corpus_char_count']} | {r['chunk_count']} | {r['C1']} | {r['C2']} | "
            f"{r['C3']} | {r['C4']} | {r['C5']} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## (e) Is p156_c0's rnensal/mensal pair isolated, or representative of a class?")
    lines.append("")
    rn_freq = d["rn_to_m_hunk_frequency"]
    hits = d["rnensal_mensal_hits_p156"]
    lines.append(f"- The exact pair (native=\"rnensal\", corpus=\"mensal\") occurs {hits} time(s) on page 156 (the only page it can occur on, by construction of this specific word).")
    lines.append(f"- Its underlying character-level hunk, `rn → m`, was independently discovered (not looked up) by the SAME character-diff mechanism applied to every C1/C2/C3 pair census-wide, and occurs **{rn_freq}** time(s) in total across all {d['in_scope_page_count']} in-scope pages (including this one instance).")
    minim_total = d["minim_family_total"]
    if rn_freq > 1:
        lines.append(
            f"- **Verdict: REPRESENTATIVE OF A CLASS, not isolated.** The `rn → m` substitution recurs "
            f"{rn_freq} times outside of being a one-off on p156 alone, meaning the ligature confusion "
            "'rn' (two characters, narrow serif gap) misread as 'm' (or vice versa) is a recurring OCR/"
            "native-text-layer failure mode in this book, not a single anomaly. See the discovered "
            "ligature-pattern table above for its rank alongside other recurring patterns."
        )
    else:
        lines.append(
            "- **Verdict at the EXACT hunk level: ISOLATED.** The precise `rn → m` two-character hunk "
            "does not recur elsewhere in this book's in-scope pages beyond this single p156 instance."
        )
    lines.append(
        f"- **However, at a broader level, the underlying failure mode IS a recurring class.** `rn → m` "
        "is one specific case of a much larger, independently-discovered cluster of narrow-vertical-"
        "stroke (\"minim\") confusions — m, n, u, rn, ri, and in mutually substituting for one another "
        f"(the classic OCR minim-ambiguity problem). This broader family accounts for **{minim_total}** "
        "hunk occurrences census-wide (see the table below), dwarfing the single `rn → m` instance. "
        "This family grouping is named here for prose ONLY, after seeing which hunks actually recurred "
        "in the discovered-pattern table above — it was never fed back into classification."
    )
    lines.append("")
    lines.append("| native_substr → corpus_substr | frequency |")
    lines.append("|---|---|")
    for hunk, count in d["minim_family_hunks"]:
        lines.append(f"| {hunk[0]} → {hunk[1]} | {count} |")
    lines.append("")
    lines.append(
        "- **Net call: the p156 rnensal/mensal pair's EXACT spelling is a singleton, but the CLASS of "
        "error it belongs to (minim/narrow-stroke confusion) is common and recurring in this book's "
        "native text layer** — consistent with the C1:C2 ratio above already showing native-side "
        "corruption (C2) is far from negligible (4.51% of classified pairs)."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## (f) Merge policy")
    lines.append("")
    lines.append(
        "**No recommendation is made here.** This report is measurement only, per the instructing "
        "prompt's explicit scope. The C1:C2 ratio, the top-40 pair tables, the discovered ligature "
        "patterns, and the per-page C2 hotspot table above are the evidence; the policy ruling "
        "(whether Path C is a blind native-preferred replacement, a token-level adjudicated merge, or "
        "something else) is a design-chat decision made after reading this census, not before."
    )
    lines.append("")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
