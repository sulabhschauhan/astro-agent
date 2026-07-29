"""
scripts/build_golden_fixtures_S80.py
S80 U0 — read-only golden fixture generator. Run manually; NEVER invoked from
CI or the pytest suite. Emits tests/fixtures/golden_S80.json (4 Cheiro
fixtures + 1 Path-C-boundary fixture) and tests/fixtures/native_coverage_S80.json
(a per-PDF native-text-coverage census), snapshotting today's PDF-native-text-
layer vs. live-corpus quality gap (see CLAUDE.md S79: diagnostics/
native_text_probe_S79.md, r1_p0_page_triage_S79.md).

Reads ONLY: the source PDFs via pdfplumber's own extract_text() (never
rasterizes, never runs Tesseract) and the live ChromaDB collection
(data/chroma_db) via a metadata/document read (collection.get(), no
embedding API call). Never imports pdf_processor.py, chunker.py, embedder.py,
or query_engine.py — this script must not exercise or depend on any part of
the ingestion/retrieval pipeline it is here to catch defects in.

INDEXING CONVENTION (verified independently against this repo's live state,
not assumed off any one diagnostic file): "page N" = 1-indexed, project
convention, matching pdf_processor.py's `page_num` (chunk_id = f"{book}_p{page_num}"),
which is also exactly ChromaDB's `page_ref` metadata field. In pdfplumber
terms, project page N == pdf.pages[N - 1] (0-indexed). This is the SAME
convention diagnostics/native_text_probe_S79.md (commit 3178fdc) validated
with a worked example.

VERIFIED DEVIATIONS FROM THE INSTRUCTING PROMPT — found by re-deriving every
fixture fact directly against the live PDF/chroma state rather than trusting
prior diagnostic prose at face value:

  1. diagnostics/r1_p0_page_triage_S79.md (commit 181965d) — its "Full Metrics
     Table" and "TARGETED SUB-REPORT" page-number COLUMN is uniformly OFF BY
     ONE HIGH relative to the project convention above (e.g. its row "158"
     shows "Plate XVIII.", which is actually project-convention page 157).
     Its own "printed_page_no" column, however, is read directly off each
     page's footer text and is NOT affected by this bug — confirmed by
     cross-checking specific printed folios against independently-fetched
     native text (folio 98 -> CHAPTER X / project p156; folio 125 -> CHAPTER
     XIX / project p191). This generator's own self-checks below exist
     precisely to catch a recurrence of this class of bug in THIS script.

  2. Cheiro project p156's native text contains "rnensal", NOT "mensal" —
     reproduced independently via a direct pdfplumber call, not read off a
     diagnostic transcript. This is a real ligature-merge artifact already
     baked into the archive.org-embedded NATIVE text layer itself (not
     something Tesseract introduced) — "mensal" is actually what the LIVE
     CORPUS (Tesseract OCR) has for this word; native has "rnensal". Fixture
     1's native_text field and tests/test_golden_fixtures_S80.py's "PRESERVE
     case" assertion both use the true, verified token.

  3. Cheiro project p90 is NO LONGER a "mixed-classified, corpus text ''"
     case — live ChromaDB has 3 non-empty chunks for page_ref=90 (923 + 613
     + 910 chars), diverged from the stale data/progress/
     cheiroslanguageo00chei_1.json snapshot (page_type="mixed", text="")
     that an earlier diagnostic pass was read from; the corpus has clearly
     been re-ingested since that snapshot was written. Of this book's 5
     originally page_type="mixed" pages ([19, 20, 90, 191, 220] per that
     progress file), only page_ref 19 and 191 still show ZERO live chunks
     today (verified via a live collection.get() call). Fixture 4 uses
     project p191 (CHAPTER XIX, 1706 native chars, clean chapter-opening
     prose) instead of p90.

  4. F5 FALSIFIED, not merely unverified: a corpus-wide scan of EVERY page of
     all 22 PDFs in data/pdfs/ found ZERO U+0900-U+097F (Devanagari)
     codepoints anywhere in any native text layer, corpus-wide — not just in
     the "Jyotish_Lal Kitab_B.M. Gosvami" book (an English translation
     edition), but in literally every book, including the ones whose native
     layer is otherwise substantial. The originally-specified "LAL KITAB
     Devanagari-orphan" defect class does not exist in this corpus to
     fixture. Per design-chat ruling (S80 U0 amendment), this fixture is
     REPLACED by a Path-C-boundary case instead (see (5) below); the
     Devanagari discovery code path has been REMOVED, not merely disabled.

  5. Fixture 5 (REPLACED): a Path-C-boundary case, not a Devanagari case.
     "Path C" = a future native-text-extraction repair (aligning corpus
     chunks against the PDF's own native text layer) — for a page where
     native_char_count == 0, Path C has no source to align the corpus
     against; it is structurally out of scope for that repair, regardless of
     how much (possibly Tesseract-OCR'd) text the live corpus holds for that
     page. Selected by rule, not hardcoded: from the book(s) tied for the
     LOWEST native chars-per-page average across the full census (see
     `_build_native_coverage_census()`), take the single page with the
     highest live corpus chunk char total where native_char_count == 0.
     Six books tied exactly at a 0.0 average (every page has zero native
     text: Deva-keralam, Hasta Samudrika Shastra, Jataka Parijata,
     Phaladeepika, Saravali, Sarvartha-Chintamani) — the tie is broken by
     searching across all six for the single globally-best-populated page,
     not by an additional arbitrary rule.

No repair logic anywhere in this file — it captures the defect as it exists
today. The fix lands at a future U-numbered prompt.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import chromadb
import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "data" / "pdfs"
CHROMA_DIR = str(ROOT / "data" / "chroma_db")
COLLECTION_NAME = "astro_chunks"
FIXTURES_OUTPUT_PATH = ROOT / "tests" / "fixtures" / "golden_S80.json"
CENSUS_OUTPUT_PATH = ROOT / "tests" / "fixtures" / "native_coverage_S80.json"
PROGRESS_DIR = ROOT / "data" / "progress"

CHEIRO_PDF = PDF_DIR / "cheiroslanguageo00chei_1.pdf"
CHEIRO_BOOK = "cheiroslanguageo00chei_1"


def _sha256_file(path: Path) -> str:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as exc:
        raise RuntimeError(f"sha256 failed for {path}: {exc}") from exc


def _native_text(pdf: "pdfplumber.PDF", page_index: int) -> str:
    try:
        return pdf.pages[page_index].extract_text() or ""
    except Exception as exc:
        raise RuntimeError(
            f"pdfplumber extract_text() failed at page_index={page_index}: {exc}"
        ) from exc


def _get_collection():
    try:
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        return client.get_or_create_collection(
            name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )
    except Exception as exc:
        raise RuntimeError(f"ChromaDB collection open failed: {exc}") from exc


def _get_corpus_chunks(collection, book_name: str, page_ref: int, page_index_for_error: int) -> list[dict]:
    try:
        res = collection.get(
            where={"$and": [{"book_name": {"$eq": book_name}}, {"page_ref": {"$eq": page_ref}}]},
            include=["documents"],
        )
        return [
            {"chunk_id": cid, "text": doc, "char_count": len(doc)}
            for cid, doc in zip(res["ids"], res["documents"])
        ]
    except Exception as exc:
        raise RuntimeError(
            f"ChromaDB read failed for book={book_name!r} page_index={page_index_for_error}: {exc}"
        ) from exc


def _classify_page_label(book_name: str, page_ref: int, chunks: list[dict]) -> str:
    """Whatever the current pipeline assigned: prefer live chroma metadata
    (page_type, present on any live chunk for this page); fall back to the
    book's data/progress/<book>.json snapshot for pages with zero live
    chunks (that page-level record still carries pdf_processor's original
    page_type classification even when no sub-chunk survived to ChromaDB)."""
    try:
        if chunks:
            collection = _get_collection()
            res = collection.get(
                where={"$and": [{"book_name": {"$eq": book_name}}, {"page_ref": {"$eq": page_ref}}]},
                include=["metadatas"],
            )
            metas = res.get("metadatas") or []
            if metas and metas[0].get("page_type"):
                return metas[0]["page_type"]

        progress_path = PROGRESS_DIR / f"{book_name}.json"
        if progress_path.exists():
            with open(progress_path, "r", encoding="utf-8") as f:
                pages = json.load(f)
            for p in pages:
                if p.get("page_ref") == page_ref:
                    return p.get("page_type", "unknown")
        return "unknown"
    except Exception as exc:
        return f"unknown (lookup failed: {exc})"


def _build_cheiro_fixture(pdf, collection, page_num: int, printed_folio, must_contain: list[str], notes: str) -> dict:
    page_index = page_num - 1
    native_text = _native_text(pdf, page_index)
    chunks = _get_corpus_chunks(collection, CHEIRO_BOOK, page_num, page_index)
    for token in must_contain:
        if token not in native_text:
            raise AssertionError(
                f"SELF-CHECK FAILED: Cheiro p{page_num} native text does not contain {token!r}"
            )
    return {
        "page_index": page_index,
        "printed_folio_if_known": printed_folio,
        "source_pdf_sha256": _sha256_file(CHEIRO_PDF),
        "native_text": native_text,
        "native_char_count": len(native_text),
        "corpus_chunks": chunks,
        "classify_page_label": _classify_page_label(CHEIRO_BOOK, page_num, chunks),
        "notes": notes,
    }


# ─── Native-text coverage census + Path-C-boundary fixture discovery ──────


def _scan_pdf_native_pages(path: Path) -> list[int]:
    """Per-page native char counts for one PDF. Raises with page_index in
    the message on any single-page extraction failure."""
    try:
        pdf = pdfplumber.open(path)
    except Exception as exc:
        raise RuntimeError(f"pdfplumber.open failed for {path.name}: {exc}") from exc
    try:
        counts = []
        for idx, page in enumerate(pdf.pages):
            try:
                text = page.extract_text() or ""
            except Exception as exc:
                raise RuntimeError(
                    f"pdfplumber extract_text() failed for {path.name} page_index={idx}: {exc}"
                ) from exc
            counts.append(len(text))
        return counts
    finally:
        pdf.close()


def _build_native_coverage_census() -> dict[str, dict]:
    """One row per PDF in data/pdfs/*.pdf. book_name = filename stem
    (matches pdf_processor.py's own Path(pdf_path).stem convention, and
    therefore ChromaDB's book_name for ingested books)."""
    census: dict[str, dict] = {}
    for path in sorted(PDF_DIR.glob("*.pdf")):
        book_name = path.stem
        sha = _sha256_file(path)
        try:
            per_page_counts = _scan_pdf_native_pages(path)
        except RuntimeError as exc:
            census[book_name] = {
                "book_name": book_name,
                "source_pdf_sha256": sha,
                "page_count": 0,
                "pages_with_native_text": 0,
                "pages_with_zero_native": 0,
                "total_native_chars": 0,
                "native_chars_per_page_mean": None,
                "path_c_eligible": None,
                "notes": f"PDF unreadable: {exc}",
                "_per_page_counts": [],
            }
            continue

        page_count = len(per_page_counts)
        pages_with_native = sum(1 for c in per_page_counts if c > 0)
        pages_with_zero = page_count - pages_with_native
        total_chars = sum(per_page_counts)
        mean = (total_chars / page_count) if page_count > 0 else None
        eligible = (pages_with_native / page_count) if page_count > 0 else None
        note = "" if page_count > 0 else "pdfplumber reports 0 pages for this file (malformed page tree)."

        census[book_name] = {
            "book_name": book_name,
            "source_pdf_sha256": sha,
            "page_count": page_count,
            "pages_with_native_text": pages_with_native,
            "pages_with_zero_native": pages_with_zero,
            "total_native_chars": total_chars,
            "native_chars_per_page_mean": mean,
            "path_c_eligible": eligible,
            "notes": note,
            "_per_page_counts": per_page_counts,  # stripped before writing census file
        }
    return census


def _find_path_c_boundary_fixture(census: dict[str, dict], collection) -> dict | None:
    """From the book(s) tied for the lowest native_chars_per_page_mean
    (excluding books with page_count == 0, where the mean is undefined),
    find the single page across all tied books with the highest live
    corpus chunk char total, where native_char_count == 0 for that page.
    Returns None if no qualifying page exists anywhere among the tied books
    (e.g. none of them are actually ingested / have any live corpus text)."""
    eligible_books = {b: row for b, row in census.items() if row["page_count"] > 0}
    if not eligible_books:
        return None
    min_mean = min(row["native_chars_per_page_mean"] for row in eligible_books.values())
    tied_books = [b for b, row in eligible_books.items() if row["native_chars_per_page_mean"] == min_mean]

    best: dict | None = None
    for book_name in tied_books:
        try:
            res = collection.get(
                where={"book_name": {"$eq": book_name}}, include=["documents", "metadatas"]
            )
        except Exception as exc:
            raise RuntimeError(f"ChromaDB read failed while scanning book={book_name!r}: {exc}") from exc

        per_page_native = census[book_name]["_per_page_counts"]
        totals_by_page_ref: dict[int, int] = {}
        for doc, meta in zip(res["documents"], res["metadatas"]):
            page_ref = meta.get("page_ref")
            if page_ref is None:
                continue
            totals_by_page_ref[page_ref] = totals_by_page_ref.get(page_ref, 0) + len(doc)

        for page_ref, corpus_chars in totals_by_page_ref.items():
            page_index = page_ref - 1
            native_chars = per_page_native[page_index] if 0 <= page_index < len(per_page_native) else None
            if native_chars != 0:
                continue  # only interested in native_char_count == 0 pages
            if best is None or corpus_chars > best["_corpus_chars"]:
                best = {"_corpus_chars": corpus_chars, "book_name": book_name, "page_ref": page_ref}

    if best is None:
        return None

    book_name, page_ref = best["book_name"], best["page_ref"]
    page_index = page_ref - 1
    chunks = _get_corpus_chunks(collection, book_name, page_ref, page_index)
    pdf_path = PDF_DIR / f"{book_name}.pdf"
    return {
        "book_name": book_name,
        "page_index": page_index,
        "printed_folio_if_known": None,
        "source_pdf_sha256": census[book_name]["source_pdf_sha256"],
        "native_text": "",
        "native_char_count": 0,
        "corpus_chunks": chunks,
        "classify_page_label": _classify_page_label(book_name, page_ref, chunks),
        "book_native_chars_per_page_mean": census[book_name]["native_chars_per_page_mean"],
        "book_path_c_eligible": census[book_name]["path_c_eligible"],
        "notes": (
            f"PATH-C-BOUNDARY case (replaces the falsified Devanagari fixture 5 -- "
            f"see module docstring deviation (4)/(5)). book={book_name!r} tied at "
            f"the corpus-wide lowest native_chars_per_page_mean "
            f"({census[book_name]['native_chars_per_page_mean']}); this specific "
            f"page has native_char_count==0 but {best['_corpus_chars']} live corpus "
            f"chars (Tesseract OCR only, no native text to align against -- Path C "
            f"is structurally inapplicable to this page)."
        ),
    }


def _run_mandatory_self_checks(pdf, collection) -> list[dict]:
    """Fail loudly (raise) on any violation, BEFORE any output is written.
    These specifically catch a recurrence of the 181965d off-by-one."""
    checks = []

    page_count = len(pdf.pages)
    checks.append(("Cheiro page count == 310", 310, page_count, page_count == 310))

    p157_text = _native_text(pdf, 157 - 1)
    checks.append((
        'Cheiro p157 native contains "Plate XVIII"',
        "present", "present" if "Plate XVIII" in p157_text else "ABSENT",
        "Plate XVIII" in p157_text,
    ))

    p158_text = _native_text(pdf, 158 - 1)
    checks.append((
        "Cheiro p158 native char_count == 0",
        0, len(p158_text), len(p158_text) == 0,
    ))

    p156_text = _native_text(pdf, 156 - 1)
    checks.append((
        'Cheiro p156 native contains "CHAPTER X"',
        "present", "present" if "CHAPTER X" in p156_text else "ABSENT",
        "CHAPTER X" in p156_text,
    ))

    failed = [c for c in checks if not c[3]]
    if failed:
        lines = "\n".join(f"  - {name}: expected {exp!r}, got {obs!r}" for name, exp, obs, ok in failed)
        raise AssertionError(f"MANDATORY SELF-CHECK(S) FAILED — refusing to write output:\n{lines}")

    return [{"assertion": name, "expected": exp, "observed": obs, "status": "PASS"} for name, exp, obs, ok in checks]


def main() -> int:
    try:
        if not CHEIRO_PDF.exists():
            raise RuntimeError(f"Cheiro PDF not found at {CHEIRO_PDF} — cannot build fixtures.")

        collection = _get_collection()

        with pdfplumber.open(CHEIRO_PDF) as pdf:
            self_check_results = _run_mandatory_self_checks(pdf, collection)

            fixtures = {
                "cheiro_p156_chapter_x": _build_cheiro_fixture(
                    pdf, collection, 156, printed_folio=98,
                    must_contain=["CHAPTER X"],
                    notes=(
                        'Clean native chapter opening. Corpus (Tesseract OCR) corrupts '
                        '"heart" -> "hne" in at least one sub-chunk (see corpus_chunks). '
                        'Native text itself contains "rnensal" (NOT "mensal") for the '
                        'word Cheiro spells "mensal" downstream in the corpus -- a real '
                        'archive.org-native ligature artifact, independently verified; '
                        'see module docstring deviation (2).'
                    ),
                ),
                "cheiro_p157_plate_xviii": _build_cheiro_fixture(
                    pdf, collection, 157, printed_folio=None,
                    must_contain=["Plate XVIII"],
                    notes="Plate page, minimal native text, label only.",
                ),
                "cheiro_p158_plate_verso": _build_cheiro_fixture(
                    pdf, collection, 158, printed_folio=None,
                    must_contain=[],
                    notes="Plate verso, zero native text (genuinely blank page image).",
                ),
                "cheiro_p191_mixed_empty_corpus": _build_cheiro_fixture(
                    pdf, collection, 191, printed_folio=125,
                    must_contain=["CHAPTER XIX"],
                    notes=(
                        "SUBSTITUTED for the originally-specified p90 -- see module "
                        "docstring deviation (3). page_type='mixed' at ingestion time; "
                        "pdf_processor.py discards OCR text for mixed pages by "
                        "construction (text='' regardless of what Tesseract read), so "
                        "this page has zero live corpus chunks despite 1706 chars of "
                        "clean native prose (CHAPTER XIX, THE CROSS)."
                    ),
                ),
            }

        print("Building native-text coverage census across all PDFs (slow — full corpus scan)...")
        census = _build_native_coverage_census()

        path_c_fixture = _find_path_c_boundary_fixture(census, collection)
        if path_c_fixture is not None:
            fixtures["path_c_boundary_page"] = path_c_fixture
        else:
            print(
                "NOTE: no Path-C-boundary page found among the lowest-native-average "
                "books (none had any live corpus text) — shipping 4 fixtures, not 5.",
                file=sys.stderr,
            )

        output = {
            "generated_by": "scripts/build_golden_fixtures_S80.py",
            "self_check_results": self_check_results,
            "fixtures": fixtures,
        }
        FIXTURES_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        FIXTURES_OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {FIXTURES_OUTPUT_PATH} ({FIXTURES_OUTPUT_PATH.stat().st_size} bytes)")
        for c in self_check_results:
            print(f"  [PASS] {c['assertion']}")

        census_output = [
            {k: v for k, v in row.items() if not k.startswith("_")}
            for row in census.values()
        ]
        CENSUS_OUTPUT_PATH.write_text(json.dumps(census_output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {CENSUS_OUTPUT_PATH} ({CENSUS_OUTPUT_PATH.stat().st_size} bytes)")

        return 0

    except Exception as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
