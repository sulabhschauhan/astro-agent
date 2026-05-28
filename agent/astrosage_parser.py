"""
agent/astrosage_parser.py
Extract named sections from an AstroSage PDF for use as LLM context.
"""

import io
import logging
from typing import Optional

import pdfplumber

logger = logging.getLogger(__name__)

# Section keywords mapped to display names; order determines search priority.
_SECTIONS: list[tuple[str, list[str]]] = [
    ("Varshaphal",         ["varshaphal", "annual predictions"]),
    ("Pratyantar",         ["pratyantar"]),
    ("Muntha",             ["muntha"]),
    ("Sade Sati",          ["sadesati", "sade sati"]),
    ("Favourable Points",  ["favourable points", "lucky"]),
    ("Lal Kitab",          ["lal kitab"]),
    ("Transit Today",      ["transit today"]),
]

# Output order regardless of PDF page order.
_PRIORITY_ORDER = [
    "Varshaphal",
    "Pratyantar",
    "Muntha",
    "Sade Sati",
    "Favourable Points",
    "Transit Today",
    "Lal Kitab",
]

# How many lines to collect after a section header is detected.
_LINES_PER_SECTION = 60


def parse_astrosage_pdf(file_bytes: bytes) -> Optional[str]:
    """
    Extract the 7 target sections from an AstroSage PDF.

    Args:
        file_bytes: Raw PDF bytes (from st.file_uploader or open()).

    Returns:
        Extracted sections joined with double newlines, prefixed with
        "ASTROSAGE PDF DATA:\\n", or None if no sections are found,
        extraction yields < 100 chars, or any exception occurs.
    """
    try:
        full_text = _extract_text(file_bytes)
        if not full_text:
            logger.warning("astrosage_parser: pdfplumber returned no text.")
            return None

        sections = _extract_sections(full_text)
        _log_coverage(sections)

        if not sections:
            return None

        combined = "\n\n".join(
            f"[{name}]\n{content}" for name, content in sections.items()
        )
        if len(combined) < 100:
            logger.warning(
                "astrosage_parser: extracted text too short (%d chars) — returning None.",
                len(combined),
            )
            return None

        return "ASTROSAGE PDF DATA:\n" + combined

    except Exception:
        logger.exception("astrosage_parser: unexpected error parsing PDF.")
        return None


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _extract_text(file_bytes: bytes) -> str:
    """Return all page text from the PDF as a single string."""
    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n".join(pages)


def _extract_sections(full_text: str) -> dict[str, str]:
    """
    Scan full_text line by line. When a section keyword is matched,
    collect up to _LINES_PER_SECTION following lines as the section body.
    Each section is captured at most once (first occurrence wins).
    """
    lines = full_text.splitlines()
    found: dict[str, str] = {}
    active_section: Optional[str] = None
    active_buffer: list[str] = []
    active_remaining = 0

    def _flush():
        if active_section and active_buffer:
            found[active_section] = "\n".join(active_buffer).strip()

    for line in lines:
        line_lower = line.lower()

        # Check if this line opens a new target section.
        matched_name = None
        for display_name, keywords in _SECTIONS:
            if display_name in found:
                continue  # already captured
            if any(kw in line_lower for kw in keywords):
                matched_name = display_name
                break

        if matched_name:
            _flush()
            active_section = matched_name
            active_buffer = [line]
            active_remaining = _LINES_PER_SECTION
        elif active_section and active_remaining > 0:
            active_buffer.append(line)
            active_remaining -= 1
            if active_remaining == 0:
                _flush()
                active_section = None
                active_buffer = []

    _flush()  # capture last open section
    return {name: found[name] for name in _PRIORITY_ORDER if name in found}


def _log_coverage(sections: dict[str, str]) -> None:
    """Log which of the 7 target sections were found and which were missing."""
    all_names = [name for name, _ in _SECTIONS]
    found_names   = [n for n in all_names if n in sections]
    missing_names = [n for n in all_names if n not in sections]
    logger.info(
        "astrosage_parser: found %d/%d sections — %s",
        len(found_names), len(all_names), found_names,
    )
    if missing_names:
        logger.info("astrosage_parser: missing sections — %s", missing_names)
