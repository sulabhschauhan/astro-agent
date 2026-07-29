"""
tests/test_golden_fixtures_S80.py
S80 U0 — asserts the Cheiro/corpus quality-gap DEFECT as it exists today,
off a committed fixture snapshot (tests/fixtures/golden_S80.json), never off
live data/pdfs or data/chroma_db (both untracked/gitignored). No network, no
GPT-4o, no embedding calls, no PDF or ChromaDB access anywhere in this file.

CORPUS_STATE below flips at a future U2 prompt once the native-text-extraction
repair lands; the "repaired" branch of each defective-state assertion is
written now, gated off, so U2 flips ONE line here, not this whole file.

Three verified deviations from this file's own originally-instructed fixture
targets (see scripts/build_golden_fixtures_S80.py's module docstring for the
full evidence trail — all independently reproduced against live data, not
assumed):
  - Cheiro p156's native text contains "rnensal", not "mensal" — a real
    archive.org-native ligature artifact, NOT a Tesseract OCR error. The
    PRESERVE-case assertion below checks for the true native token.
  - Cheiro p90 is no longer an empty-corpus page in the live corpus (it was
    re-ingested with real content since an earlier diagnostic snapshot was
    taken); p191 (CHAPTER XIX, "mixed"-classified, currently zero live
    chunks) is used instead, under fixture key "cheiro_p191_mixed_empty_corpus".
  - Fixture 5 was originally specified as a "LAL KITAB Devanagari-orphan"
    case. A corpus-wide scan (all 22 PDFs, every page) found ZERO Devanagari
    codepoints anywhere in any native text layer — that defect class is
    FALSIFIED, not just unverified. Per design-chat ruling, fixture 5 is
    replaced with a Path-C-boundary case instead: a page with
    native_char_count == 0 (no source for a future native-text-alignment
    repair to align against) but non-empty live corpus text, drawn from
    whichever book(s) tie for the corpus-wide lowest native
    chars-per-page average (tests/fixtures/native_coverage_S80.json).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

CORPUS_STATE = "defective"  # flip to "repaired" at U2; do not remove assertions

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "golden_S80.json"
_CENSUS_PATH = Path(__file__).parent / "fixtures" / "native_coverage_S80.json"

# Path C is structurally out of scope for a book whose native-text coverage
# is this thin -- see module docstring. Threshold discipline (CLAUDE.md
# Working Style #4): 0.50 is a deliberately generous ceiling -- the actual
# tied-lowest books measure exactly 0.0 (zero pages with any native text at
# all), so this only needs to separate "structurally ineligible" from
# "partially eligible," not draw a fine line. Scope guard: this constant is
# read only by test_path_c_boundary_book_is_path_c_ineligible below; it must
# never be copied into any production ingestion/repair path.
_PATH_C_INELIGIBLE_CEILING = 0.50


def _load_json(path: Path, generator_hint: str) -> object:
    if not path.exists():
        pytest.fail(
            f"{path} is missing — run `python scripts/build_golden_fixtures_S80.py` "
            f"to generate it ({generator_hint}). This file must NOT skip silently "
            "on a missing fixture.",
            pytrace=False,
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


_DATA = _load_json(
    _FIXTURE_PATH,
    "requires data/pdfs and data/chroma_db present locally; not committed, opt-in, never run in CI",
)
_FIXTURES = _DATA["fixtures"]
_CENSUS = _load_json(_CENSUS_PATH, "same generator, written alongside golden_S80.json")
_CENSUS_BY_BOOK = {row["book_name"]: row for row in _CENSUS}


def _chunk_texts(fixture: dict) -> list[str]:
    return [c["text"] for c in fixture["corpus_chunks"]]


def _joined_corpus_text(fixture: dict) -> str:
    return "".join(_chunk_texts(fixture))


# ─── D. Fixture integrity ────────────────────────────────────────────────


@pytest.mark.parametrize("fixture_key", list(_FIXTURES.keys()))
def test_fixture_integrity_sha256_present(fixture_key):
    """D: every fixture entry must carry a non-empty source_pdf_sha256."""
    fixture = _FIXTURES[fixture_key]
    sha = fixture.get("source_pdf_sha256")
    assert sha, f"{fixture_key}: source_pdf_sha256 missing or empty"
    assert isinstance(sha, str) and len(sha) == 64, (
        f"{fixture_key}: source_pdf_sha256 does not look like a sha256 hex digest: {sha!r}"
    )


# ─── A. NATIVE IS CLEAN — regression guards, must hold in BOTH states ─────


def test_native_p156_contains_line_not_hne():
    """A: native text uses "line", never the corpus's "hne" OCR corruption."""
    native = _FIXTURES["cheiro_p156_chapter_x"]["native_text"]
    assert "line" in native
    assert "hne" not in native


def test_native_p156_preserve_case_rnensal():
    """A: the PRESERVE case for U2 — whatever native text says for this word
    must survive a future native-text-extraction repair unchanged. Verified
    true token is "rnensal" (a real archive.org-native ligature artifact),
    not "mensal" (which is actually what the CORPUS/Tesseract OCR has here —
    see this file's module docstring and the generator's own docstring)."""
    native = _FIXTURES["cheiro_p156_chapter_x"]["native_text"]
    assert "rnensal" in native


def test_native_p157_contains_plate_xviii():
    """A: native text correctly reads the plate caption."""
    native = _FIXTURES["cheiro_p157_plate_xviii"]["native_text"]
    assert "Plate XVIII" in native


def test_native_p158_char_count_zero():
    """A: p158 is a genuinely blank plate verso at the native-text level."""
    fixture = _FIXTURES["cheiro_p158_plate_verso"]
    assert fixture["native_char_count"] == 0


def test_path_c_boundary_native_char_count_zero():
    """A: permanent invariant, not a defect assertion -- this fixture's whole
    point is that it has no native text to align a future repair against.
    True in both CORPUS_STATE values, since a native-text-alignment repair
    (Path C) cannot change a fact about the PDF's own native text layer."""
    fixture = _FIXTURES["path_c_boundary_page"]
    assert fixture["native_char_count"] == 0


def test_path_c_boundary_corpus_char_count_positive():
    """A: permanent invariant -- the live corpus DOES have text here
    (Tesseract-OCR'd), which is exactly why this page is a genuine
    Path-C-ineligible case rather than a page with nothing at all."""
    fixture = _FIXTURES["path_c_boundary_page"]
    assert len(_joined_corpus_text(fixture)) > 0


def test_path_c_boundary_book_is_path_c_ineligible():
    """A: permanent invariant -- the book this page was drawn from is
    structurally out of scope for a future native-text-alignment repair
    (see native_coverage_S80.json's path_c_eligible field)."""
    fixture = _FIXTURES["path_c_boundary_page"]
    book_row = _CENSUS_BY_BOOK[fixture["book_name"]]
    eligible = book_row["path_c_eligible"]
    assert eligible is not None
    assert eligible < _PATH_C_INELIGIBLE_CEILING


# ─── B/C. CORPUS defect (B) vs its U2-repaired mirror (C) ─────────────────


def test_p156_corpus_state():
    fixture = _FIXTURES["cheiro_p156_chapter_x"]
    corpus_text = _joined_corpus_text(fixture)
    if CORPUS_STATE == "defective":
        # B: corpus (Tesseract OCR) corrupts "line" -> "hne" in at least one sub-chunk.
        assert "hne" in corpus_text
    else:
        # C: mirror, gated off until U2 lands the native-text repair.
        assert "line" in corpus_text
        assert "hne" not in corpus_text
        assert "rnensal" in corpus_text  # native preserve-case still holds post-repair


def test_p191_corpus_state():
    """Substituted for the originally-specified p90 — see module docstring."""
    fixture = _FIXTURES["cheiro_p191_mixed_empty_corpus"]
    corpus_text = _joined_corpus_text(fixture)
    if CORPUS_STATE == "defective":
        # B: mixed-classified page, corpus text is empty today.
        assert corpus_text == ""
    else:
        # C: mirror, gated off until U2 lands the native-text repair.
        assert corpus_text != ""


# ─── Census integrity (native_coverage_S80.json) ──────────────────────────


def test_census_covers_all_pdfs():
    """D-equivalent for the census artifact: every PDF in data/pdfs/ at
    generation time must have exactly one row (verified count, not assumed —
    matches the 22 files present when this suite was last regenerated;
    `ls data/pdfs/*.pdf | wc -l` confirmed directly, not read off an earlier
    truncated `ls | head -20` listing)."""
    assert len(_CENSUS) == 22


@pytest.mark.parametrize("book_name", list(_CENSUS_BY_BOOK.keys()))
def test_census_row_integrity(book_name):
    row = _CENSUS_BY_BOOK[book_name]
    sha = row.get("source_pdf_sha256")
    assert sha, f"{book_name}: source_pdf_sha256 missing or empty"
    assert isinstance(sha, str) and len(sha) == 64
    assert row["pages_with_native_text"] + row["pages_with_zero_native"] == row["page_count"]
