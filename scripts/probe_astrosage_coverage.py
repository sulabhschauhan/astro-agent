"""
scripts/probe_astrosage_coverage.py

S68 AstroSage-PDF dependency coverage audit -- diagnostics-only, throwaway,
read-only. Two passes over data/pdfs/VedicReport5-24-202610-01-26PM.pdf:

1. Runs the EXISTING agent.astrosage_parser.parse_astrosage_pdf() /
   _extract_sections() unmodified, to report exactly what the current
   7-keyword splitter actually captures from this specific PDF (ground
   truth of current code behavior -- no product code touched).
2. Independently walks the full raw PDF text via pdfplumber directly
   (same library the parser uses, same extract_text() call), page by
   page, to detect ALL-CAPS / Title-Case heading-like lines and report
   a full page-by-page section taxonomy of the ACTUAL document -- this
   is necessarily broader than (1), since the current parser only ever
   looks for 7 specific keywords and silently ignores every other
   section (calculation tables, remedies, numerology, promo noise,
   etc.) that a genuine "full taxonomy" audit needs to see.

No product code changes. Output is a diagnostics report only.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pdfplumber

from agent.astrosage_parser import _extract_sections, parse_astrosage_pdf

_PDF_PATH = Path(__file__).resolve().parent.parent / "data" / "pdfs" / "VedicReport5-24-202610-01-26PM.pdf"
_REPORT_PATH = Path(__file__).resolve().parent.parent / "diagnostics" / "latest_run.md"


def _pass1_existing_splitter(file_bytes: bytes) -> None:
    print("=" * 70)
    print("PASS 1 -- existing parse_astrosage_pdf() / _extract_sections()")
    print("=" * 70)
    result = parse_astrosage_pdf(file_bytes)
    print(f"parse_astrosage_pdf() returned: {'None' if result is None else f'{len(result)} chars'}")

    # Re-derive the raw section dict directly (same call path parse_astrosage_pdf
    # uses internally) so we can report per-section sizes without re-parsing.
    with pdfplumber.open(io_bytes(file_bytes)) as pdf:
        pages_text = [p.extract_text() or "" for p in pdf.pages]
    full_text = "\n".join(pages_text)
    sections = _extract_sections(full_text)
    print(f"\n{len(sections)}/7 target keywords matched:")
    for name, text in sections.items():
        first_words = " ".join(text.split()[:5])
        print(f"  - {name}: {len(text)} chars, first 5 words: {first_words!r}")

    all_keyword_names = ["Varshaphal", "Pratyantar", "Muntha", "Sade Sati",
                          "Favourable Points", "Lal Kitab", "Transit Today"]
    missing = [n for n in all_keyword_names if n not in sections]
    if missing:
        print(f"\nNOT matched by the 7-keyword list: {missing}")


def io_bytes(b: bytes):
    import io
    return io.BytesIO(b)


def _is_heading_like(line: str) -> bool:
    stripped = line.strip()
    if not stripped or len(stripped) > 80:
        return False
    letters = [c for c in stripped if c.isalpha()]
    if len(letters) < 3:
        return False
    upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    # ALL-CAPS heading, or Title Case short line ending without a period
    if upper_ratio > 0.85:
        return True
    words = stripped.split()
    if 1 <= len(words) <= 8 and not stripped.endswith((".", ",", ":")):
        cap_words = sum(1 for w in words if w[:1].isupper())
        if cap_words / len(words) > 0.6:
            return True
    return False


def _pass2_full_taxonomy(file_bytes: bytes) -> list[str]:
    print("\n" + "=" * 70)
    print("PASS 2 -- full page-by-page raw-text heading scan (pdfplumber direct)")
    print("=" * 70)
    lines_out: list[str] = []
    with pdfplumber.open(io_bytes(file_bytes)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            page_lines = text.splitlines()
            headings = [ln.strip() for ln in page_lines if _is_heading_like(ln)]
            first_line = page_lines[0].strip() if page_lines else "(no text extracted)"
            entry = f"p.{i}: first_line={first_line!r}"
            lines_out.append(entry)
            print(entry)
            if headings:
                heading_entry = f"      heading-like lines: {headings}"
                lines_out.append(heading_entry)
                print(heading_entry)
    return lines_out


def main() -> None:
    file_bytes = _PDF_PATH.read_bytes()
    print(f"PDF: {_PDF_PATH.name} ({len(file_bytes)} bytes)")
    _pass1_existing_splitter(file_bytes)
    _pass2_full_taxonomy(file_bytes)


if __name__ == "__main__":
    main()
