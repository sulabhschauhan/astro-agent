"""
scripts/corpus_loss_attribution_S80.py
S80 U2a FINAL -- read-only corpus-loss attribution probe. Supersedes all
earlier image-book / OCR-triage prompts.

Read-only: no repair, no re-ingest, no ChromaDB writes, no chunker/pdf_processor
edits. Local Tesseract only (eng+hin), no API calls, no network.

This script gathers RAW EVIDENCE ONLY and writes it to a JSON dump
(diagnostics/.corpus_loss_attribution_S80_evidence.json, scratch, not part of
the required deliverable) plus prints everything to stdout. The qualitative
judgment calls (Part 1b correctness, Part 3b coherent-vs-interleaved) are made
by a human/reviewer reading this real, verbatim evidence -- not fabricated by
this script -- per the project's NO ANCHORED JUDGMENT rule (CLAUDE.md Working
Style #9): the observation (this script) and the judgment (the final .md,
written separately after reading the printed evidence) are deliberately split.

Module order for context: pdf_processor -> image_extractor -> chunker ->
translator -> embedder -> ChromaDB.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import chromadb
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from pytesseract import Output

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ingestion.pdf_processor import classify_page  # noqa: E402  pure function, read-only import
from ingestion.chunker import strip_devanagari      # noqa: E402  pure function, read-only import

PDF_DIR = ROOT / "data" / "pdfs"
PROGRESS_DIR = ROOT / "data" / "progress"
CHROMA_DIR = str(ROOT / "data" / "chroma_db")
COLLECTION_NAME = "astro_chunks"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "native_coverage_S80.json"
EVIDENCE_PATH = ROOT / "diagnostics" / ".corpus_loss_attribution_S80_evidence.json"

POPPLER_PATH = r"C:\Program Files\poppler-26.02.0\Library\bin"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

LAL_KITAB_BOOK = "Jyotish_Lal Kitab_B.M. Gosvami"
PHALADEEPIKA_BOOK = "Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri"
SARAVALI_BOOK = "Saravali of Kalyana Varma Santhanam R. (Astrology)"
DEVAKERALAM_BOOK = "Deva-keralam"
SARVARTHA_BOOK = "Sarvartha-Chintamani"

EXPECTED_PAGE_COUNTS = {
    LAL_KITAB_BOOK: 778,
    PHALADEEPIKA_BOOK: 473,
    SARAVALI_BOOK: 352,
    DEVAKERALAM_BOOK: 298,
    SARVARTHA_BOOK: 400,
}

DEVANAGARI_LO, DEVANAGARI_HI = "ऀ", "ॿ"  # U+0900-U+097F, same range as chunker.py/translator.py


def devanagari_fraction(text: str) -> float:
    non_ws = [c for c in text if not c.isspace()]
    if not non_ws:
        return 0.0
    return sum(1 for c in non_ws if DEVANAGARI_LO <= c <= DEVANAGARI_HI) / len(non_ws)


def devanagari_count(text: str) -> int:
    return sum(1 for c in text if DEVANAGARI_LO <= c <= DEVANAGARI_HI)


# ---------------------------------------------------------------------------
# Self-checks -- fail loudly, non-zero exit, BEFORE any output is written
# ---------------------------------------------------------------------------

def run_self_checks() -> dict:
    results = []

    try:
        ver = str(pytesseract.get_tesseract_version())
        results.append(("tesseract reachable", "version string", ver, True))
    except Exception as exc:
        print(f"SELF-CHECK FAILED: tesseract not reachable: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        langs = pytesseract.get_languages(config="")
    except Exception as exc:
        print(f"SELF-CHECK FAILED: could not list tesseract langs: {exc}", file=sys.stderr)
        sys.exit(1)
    hin_present = "hin" in langs
    results.append(("'hin' in tesseract --list-langs", True, hin_present, hin_present))
    if not hin_present:
        print(
            f"SELF-CHECK FAILED: 'hin' not in tesseract languages ({langs}) -- "
            "history record (OCR ran eng+hin) is wrong. Aborting.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"SELF-CHECK FAILED: cannot read {FIXTURE_PATH}: {exc}", file=sys.stderr)
        sys.exit(1)
    fixture_by_name = {r["book_name"]: r for r in fixture}

    for book, expected in EXPECTED_PAGE_COUNTS.items():
        row = fixture_by_name.get(book)
        if row is None:
            print(f"SELF-CHECK FAILED: book {book!r} missing from {FIXTURE_PATH.name}", file=sys.stderr)
            sys.exit(1)
        ok = row["page_count"] == expected
        results.append((f"{book} fixture page_count == {expected}", expected, row["page_count"], ok))
        if not ok:
            print(
                f"SELF-CHECK FAILED: {book} fixture page_count {row['page_count']} != {expected}",
                file=sys.stderr,
            )
            sys.exit(1)

        pdf_path = PDF_DIR / f"{book}.pdf"
        try:
            with pdfplumber.open(pdf_path) as pdf:
                actual = len(pdf.pages)
        except Exception as exc:
            print(f"SELF-CHECK FAILED: cannot open {pdf_path}: {exc}", file=sys.stderr)
            sys.exit(1)
        ok2 = actual == expected
        results.append((f"{book} live PDF page_count == {expected}", expected, actual, ok2))
        if not ok2:
            print(f"SELF-CHECK FAILED: {book} live PDF page count {actual} != {expected}", file=sys.stderr)
            sys.exit(1)

    print("=== SELF-CHECKS: ALL PASS ===")
    for name, exp, obs, ok in results:
        print(f"  [PASS] {name}: expected={exp!r} observed={obs!r}")
    return {"tesseract_version": ver, "tesseract_langs": langs, "checks": results}


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def get_collection():
    try:
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        return client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    except Exception as exc:
        raise RuntimeError(f"ChromaDB open failed: {exc}") from exc


def book_corpus_by_page(collection, book_name: str) -> dict:
    try:
        res = collection.get(where={"book_name": {"$eq": book_name}}, include=["documents", "metadatas"])
    except Exception as exc:
        raise RuntimeError(f"ChromaDB read failed for book={book_name!r}: {exc}") from exc
    by_page: dict = {}
    for cid, doc, meta in zip(res["ids"], res["documents"], res["metadatas"]):
        pr = meta.get("page_ref")
        if pr is None:
            continue
        by_page.setdefault(pr, []).append({"chunk_id": cid, "text": doc, "char_count": len(doc)})
    return by_page


def native_pages(pdf_path: Path) -> list:
    try:
        with pdfplumber.open(pdf_path) as pdf:
            out = []
            for idx, page in enumerate(pdf.pages):
                try:
                    out.append(page.extract_text() or "")
                except Exception as exc:
                    print(f"WARN: native extract failed {pdf_path.name} page_index={idx}: {exc}", file=sys.stderr)
                    out.append("")
            return out
    except Exception as exc:
        raise RuntimeError(f"pdfplumber.open failed for {pdf_path}: {exc}") from exc


def load_progress(book_name: str) -> dict:
    path = PROGRESS_DIR / f"{book_name}.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"WARN: progress load failed for {book_name}: {exc}", file=sys.stderr)
        return {}
    out = {}
    for p in data:
        pr = p.get("page_ref")
        if pr is not None:
            out[pr] = p
    return out


def ocr_page(pdf_path: Path, page_num: int):
    """Rasterize ONE page at the pipeline's own DPI (300) and OCR with eng+hin,
    --psm 3 -- exactly pdf_processor.py's pdf_to_images()/ocr_image() config.
    Returns (text, image) or (None, None) on failure (caught, not fatal)."""
    try:
        images = convert_from_path(
            str(pdf_path), dpi=300, first_page=page_num, last_page=page_num, poppler_path=POPPLER_PATH
        )
        image = images[0]
    except Exception as exc:
        print(f"WARN: rasterize failed {pdf_path.name} page={page_num}: {exc}", file=sys.stderr)
        return None, None
    try:
        text = pytesseract.image_to_string(image, lang="eng+hin", config="--psm 3").strip()
    except Exception as exc:
        print(f"WARN: OCR failed {pdf_path.name} page={page_num}: {exc}", file=sys.stderr)
        return None, image
    return text, image


def column_clustering(image, book_name: str, page_num: int) -> dict:
    """Cluster line-start (x0) positions via pytesseract.image_to_data on the
    SAME rasterized image, grouped by (block_num, par_num, line_num), taking
    min(left) per line group. Method: sort line x0 values; find the single
    largest gap; call it bimodal iff that gap exceeds 15% of image width AND
    each side holds at least 20% of the lines. Diagnostic heuristic only, not
    a production threshold -- documented here, not tuned."""
    try:
        data = pytesseract.image_to_data(image, lang="eng+hin", config="--psm 3", output_type=Output.DICT)
    except Exception as exc:
        return {"error": f"image_to_data failed {book_name} p{page_num}: {exc}"}

    lines: dict = {}
    n = len(data["text"])
    for i in range(n):
        txt = data["text"][i]
        if not txt or not txt.strip():
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        left = data["left"][i]
        lines[key] = min(lines.get(key, left), left)

    x0_values = sorted(lines.values())
    width = image.width
    if len(x0_values) < 4:
        return {"method": "insufficient lines for clustering", "n_lines": len(x0_values), "result": "UNDETERMINED"}

    gaps = [(x0_values[i + 1] - x0_values[i], i) for i in range(len(x0_values) - 1)]
    max_gap, split_i = max(gaps)
    left_group = x0_values[: split_i + 1]
    right_group = x0_values[split_i + 1 :]
    frac_left = len(left_group) / len(x0_values)
    frac_right = len(right_group) / len(x0_values)
    bimodal = (max_gap > 0.15 * width) and (frac_left >= 0.20) and (frac_right >= 0.20)

    return {
        "method": "largest-gap split of per-line x0 (min-left), bimodal iff gap>15%%width and each side>=20%% of lines",
        "n_lines": len(x0_values),
        "image_width": width,
        "max_gap_px": max_gap,
        "max_gap_frac_of_width": round(max_gap / width, 4),
        "left_group_n": len(left_group),
        "right_group_n": len(right_group),
        "left_group_x0_range": [left_group[0], left_group[-1]],
        "right_group_x0_range": [right_group[0], right_group[-1]] if right_group else None,
        "result": "BIMODAL" if bimodal else "UNIMODAL",
    }


# ---------------------------------------------------------------------------
# PART 1 -- Jyotish Lal Kitab
# ---------------------------------------------------------------------------

def part1(collection) -> dict:
    print("\n=== PART 1: JYOTISH LAL KITAB ===")
    book = LAL_KITAB_BOOK
    pdf_path = PDF_DIR / f"{book}.pdf"
    native = native_pages(pdf_path)
    corpus = book_corpus_by_page(collection, book)
    progress = load_progress(book)
    page_count = len(native)

    zero_corpus_pages = [p for p in range(1, page_count + 1) if p not in corpus]
    zero_with_native = [p for p in zero_corpus_pages if len(native[p - 1]) > 0]

    print(f"1a. page_count={page_count}")
    print(f"    pages with zero live corpus chunks: {len(zero_corpus_pages)}")
    print(f"    of those, native_char_count > 0: {len(zero_with_native)}")

    # 1b -- top 10 by highest native_char_count among zero-corpus pages
    ranked = sorted(zero_corpus_pages, key=lambda p: len(native[p - 1]), reverse=True)[:10]
    top10 = []
    for p in ranked:
        text = native[p - 1]
        ncc = len(text)
        first60 = " ".join(text.split()[:60])
        cls = classify_page(text)
        if cls == "text":
            branch_quote = (
                'pdf_processor.py process_pdf(), lines 147-157:\n'
                '    if page_type == "text":\n'
                '        chunk = {\n'
                '            "chunk_id": chunk_id,\n'
                '            "text": raw_text,\n'
                '            ...\n'
                '        }\n'
                '-> text is KEPT and flows to chunker.py.'
            )
        else:
            branch_quote = (
                'pdf_processor.py process_pdf(), lines 158-170 (else branch):\n'
                '    else:\n'
                '        img_label = ...\n'
                '        image_path = save_diagram_image(half, book_name, img_label, output_dir)\n'
                '        chunk = {\n'
                '            "chunk_id": chunk_id,\n'
                '            "text": "",            # filled by image_extractor.py later\n'
                '            ...\n'
                '            "page_type": page_type\n'
                '        }\n'
                '-> raw OCR text is DISCARDED at this point regardless of what Tesseract read; '
                'only "diagram" page_type is later eligible for image_extractor.py refill '
                '(image_extractor.extract_diagram_text() filters page_type == "diagram" only, '
                'never "mixed"). embedder.py marks empty-text chunks embedding_status="pending" '
                'and NEVER upserts them to ChromaDB (only "complete" chunks are embedded).'
            )
        recorded_page_type = progress.get(p, {}).get("page_type", "ABSENT-FROM-PROGRESS-JSON")
        row = {
            "page": p,
            "native_char_count": ncc,
            "first_60_words_native": first60,
            "classify_page_on_native_text": cls,
            "source_branch": branch_quote,
            "recorded_page_type_in_progress_json": recorded_page_type,
        }
        top10.append(row)
        print(f"  p{p}: native_char_count={ncc} classify(native)={cls} recorded_page_type={recorded_page_type}")
        print(f"       first60: {first60[:200]}")

    # 1c -- aggregate page_type distribution across ALL zero-corpus pages, from progress json only
    dist = {"text": 0, "diagram": 0, "mixed": 0, "absent": 0, "other": 0}
    per_page_type_examples: dict = {}
    for p in zero_corpus_pages:
        pt = progress.get(p, {}).get("page_type") if p in progress else None
        if pt is None:
            dist["absent"] += 1
            per_page_type_examples.setdefault("absent", []).append(p)
        elif pt in dist:
            dist[pt] += 1
            per_page_type_examples.setdefault(pt, []).append(p)
        else:
            dist["other"] += 1
            per_page_type_examples.setdefault("other", []).append(p)

    print(f"1c. page_type distribution across {len(zero_corpus_pages)} zero-corpus pages: {dist}")

    return {
        "book": book,
        "page_count": page_count,
        "zero_corpus_page_count": len(zero_corpus_pages),
        "zero_corpus_pages": zero_corpus_pages,
        "zero_with_native_count": len(zero_with_native),
        "zero_with_native_pages": zero_with_native,
        "top10": top10,
        "page_type_distribution": dist,
        "page_type_examples": {k: v[:15] for k, v in per_page_type_examples.items()},
    }


# ---------------------------------------------------------------------------
# PART 2 -- Phaladeepika and Saravali strip quantification
# ---------------------------------------------------------------------------

def select_emptiest_pages(collection, book: str, page_count: int, n: int = 5) -> list:
    corpus = book_corpus_by_page(collection, book)
    mid = page_count / 2
    totals = []
    for p in range(1, page_count + 1):
        chars = sum(c["char_count"] for c in corpus.get(p, []))
        totals.append((chars, abs(p - mid), p))
    totals.sort(key=lambda t: (t[0], t[1]))
    return [p for _, _, p in totals[:n]]


def part2(collection) -> dict:
    print("\n=== PART 2: PHALADEEPIKA + SARAVALI STRIP QUANTIFICATION ===")
    out = {}
    for book in (PHALADEEPIKA_BOOK, SARAVALI_BOOK):
        pdf_path = PDF_DIR / f"{book}.pdf"
        page_count = EXPECTED_PAGE_COUNTS[book]
        corpus = book_corpus_by_page(collection, book)
        pages = select_emptiest_pages(collection, book, page_count, n=5)
        print(f"\n-- {book} -- selected pages (emptiest live corpus, tie->mid-book): {pages}")

        rows = []
        for p in pages:
            text, image = ocr_page(pdf_path, p)
            if text is None:
                rows.append({"page": p, "error": "rasterize/OCR failed, skipped"})
                continue

            s1_char = len(text)
            s1_word = len(text.split())
            s1_dev_count = devanagari_count(text)
            s1_dev_frac = devanagari_fraction(text)

            stripped = strip_devanagari(text)
            s2_char = len(stripped)
            chars_removed = s1_char - s2_char

            s3_char = sum(c["char_count"] for c in corpus.get(p, []))

            col = column_clustering(image, book, p) if image is not None else {"error": "no image"}

            row = {
                "page": p,
                "s1_raw_ocr": {
                    "char_count": s1_char,
                    "word_count": s1_word,
                    "devanagari_codepoints": s1_dev_count,
                    "devanagari_fraction": round(s1_dev_frac, 4),
                    "first_20_words": " ".join(text.split()[:20]),
                },
                "s2_post_strip": {
                    "char_count": s2_char,
                    "chars_removed": chars_removed,
                    "first_20_words": " ".join(stripped.split()[:20]),
                },
                "s3_live_corpus_char_count": s3_char,
                "s3_approx_s2": abs(s3_char - s2_char) <= max(5, 0.02 * max(s2_char, 1)),
                "column_clustering": col,
            }
            rows.append(row)
            print(f"  p{p}: S1={s1_char}c/{s1_word}w dev_frac={s1_dev_frac:.3f} "
                  f"S2={s2_char}c removed={chars_removed} S3(corpus)={s3_char} "
                  f"column={col.get('result', col.get('error'))}")

        book_total_removed = sum(r.get("s2_post_strip", {}).get("chars_removed", 0) for r in rows if "error" not in r)
        out[book] = {"page_count": page_count, "selected_pages": pages, "rows": rows,
                     "book_total_chars_removed_sampled": book_total_removed}
    return out


# ---------------------------------------------------------------------------
# PART 3 -- F9 column-interleaving quality check
# ---------------------------------------------------------------------------

def top_populated_pages(collection, book: str, n: int, must_include: list = None) -> list:
    corpus = book_corpus_by_page(collection, book)
    totals = [(sum(c["char_count"] for c in chunks), p) for p, chunks in corpus.items()]
    totals.sort(reverse=True)
    ordered = [p for _, p in totals]
    result = list(must_include or [])
    for p in ordered:
        if p not in result:
            result.append(p)
        if len(result) >= n:
            break
    return result[:n]


def part3(collection) -> dict:
    print("\n=== PART 3: F9 COLUMN-INTERLEAVING QUALITY CHECK ===")
    out = {}

    deva_pages = top_populated_pages(collection, DEVAKERALAM_BOOK, n=5, must_include=[102])
    sarv_pages = top_populated_pages(collection, SARVARTHA_BOOK, n=3)

    for book, pages in ((DEVAKERALAM_BOOK, deva_pages), (SARVARTHA_BOOK, sarv_pages)):
        pdf_path = PDF_DIR / f"{book}.pdf"
        corpus = book_corpus_by_page(collection, book)
        print(f"\n-- {book} -- populated pages selected: {pages}")
        rows = []
        for p in pages:
            chunks = corpus.get(p, [])
            live_text = "\n".join(c["text"] for c in sorted(chunks, key=lambda c: c["chunk_id"]))
            first80 = " ".join(live_text.split()[:80])

            text, image = ocr_page(pdf_path, p)
            col = column_clustering(image, book, p) if image is not None else {"error": "rasterize/OCR failed"}

            row = {
                "page": p,
                "chunk_count": len(chunks),
                "total_corpus_chars": sum(c["char_count"] for c in chunks),
                "first_80_words_live_corpus": first80,
                "column_clustering": col,
            }
            rows.append(row)
            print(f"  p{p}: chunks={len(chunks)} chars={row['total_corpus_chars']} "
                  f"column={col.get('result', col.get('error'))}")
            print(f"       first80: {first80[:300]}")
        out[book] = rows
    return out


# ---------------------------------------------------------------------------
# PART 4 -- source verification
# ---------------------------------------------------------------------------

def read_lines(path: Path, start: int, end: int) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[start - 1 : end])


def part4() -> dict:
    print("\n=== PART 4: SOURCE VERIFICATION ===")
    chunker_path = ROOT / "ingestion" / "chunker.py"
    pdf_proc_path = ROOT / "ingestion" / "pdf_processor.py"
    translator_path = ROOT / "ingestion" / "translator.py"

    strip_devanagari_quote = read_lines(chunker_path, 60, 76)
    language_pdf_processor_quote = read_lines(pdf_proc_path, 147, 170)
    language_chunker_quote = read_lines(chunker_path, 142, 156)
    translator_guard_quote = read_lines(translator_path, 53, 78)
    hindi_books_quote = read_lines(translator_path, 20, 22)
    split_spreads_quote = read_lines(pdf_proc_path, 120, 141)
    process_all_pdfs_quote = read_lines(pdf_proc_path, 225, 229)

    # 4e -- original_hindi counts
    progress_counts = {}
    total_progress = 0
    for path in sorted(PROGRESS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            progress_counts[path.stem] = f"ERROR: {exc}"
            continue
        n = sum(1 for c in data if isinstance(c, dict) and c.get("original_hindi"))
        progress_counts[path.stem] = n
        total_progress += n if isinstance(n, int) else 0

    try:
        collection = get_collection()
        res = collection.get(include=["metadatas"])
        chroma_schema_keys = sorted(res["metadatas"][0].keys()) if res["metadatas"] else []
        chroma_original_hindi_count = sum(1 for m in res["metadatas"] if m.get("original_hindi"))
    except Exception as exc:
        chroma_schema_keys = [f"ERROR: {exc}"]
        chroma_original_hindi_count = None

    print(f"4e. original_hindi in data/progress/*.json: total={total_progress}, per-book={progress_counts}")
    print(f"    ChromaDB metadata schema keys (sample): {chroma_schema_keys}")
    print(f"    ChromaDB original_hindi populated count: {chroma_original_hindi_count}")

    return {
        "strip_devanagari_quote": strip_devanagari_quote,
        "language_pdf_processor_quote": language_pdf_processor_quote,
        "language_chunker_quote": language_chunker_quote,
        "translator_guard_quote": translator_guard_quote,
        "hindi_books_quote": hindi_books_quote,
        "split_spreads_quote": split_spreads_quote,
        "process_all_pdfs_quote": process_all_pdfs_quote,
        "original_hindi_progress_total": total_progress,
        "original_hindi_progress_per_book": progress_counts,
        "chroma_metadata_schema_keys": chroma_schema_keys,
        "chroma_original_hindi_count": chroma_original_hindi_count,
    }


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    try:
        self_check_info = run_self_checks()
        collection = get_collection()

        p1 = part1(collection)
        p2 = part2(collection)
        p3 = part3(collection)
        p4 = part4()

        evidence = {
            "self_checks": self_check_info,
            "part1": p1,
            "part2": p2,
            "part3": p3,
            "part4": p4,
        }
        EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE_PATH.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nWrote raw evidence dump: {EVIDENCE_PATH} ({EVIDENCE_PATH.stat().st_size} bytes)")
        print("This is a SCRATCH evidence file, not the required deliverable. "
              "diagnostics/corpus_loss_attribution_S80.md is composed separately from this evidence.")
        return 0
    except Exception as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
