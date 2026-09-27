"""
agent/calculations/kp/significators.py
KP (Krishnamurti Paddhati) house significators -- parsed from AstroSage's own
"Significators of Houses" table (same PDF page as the KP Cuspal Positions
table sub_lords.py's oracle validation already uses, S143).

WHY PARSED, NOT COMPUTED (S143-followup, this session): the real KP
significator hierarchy (occupant of a house / house-lord / occupant's
star-lord / house-lord's star-lord -- 4 levels, with tie-break rules) is a
genuinely separate calculation from anything else in this codebase --
kp/__init__.py already scoped it OUT of S143 on purpose. AstroSage already
computes and PRINTS this table on every report; parsing it is a RESTATE
(same epistemic status as the KP Cuspal Positions table this package already
parses for oracle validation), not a new astrological calculation that would
need its own from-scratch validation/tuning risk.

WHY A SEPARATE PARSER FROM agent/astrosage_parser.py: that module's
_extract_text() uses pdfplumber's linear page.extract_text(), which
interleaves this page's side-by-side blocks (the KP System panel and its
own multi-column Vimshottari dasha-date grid) -- the exact same trap S143
hit and fixed for the KP Cuspal Positions table (see
tests/calculations/kp/test_kp_oracle_validation.py's module docstring).
This module reuses that fix: page.extract_words() sorted by (top, x0)
bounding-box position, never linear text flow.

VALIDATED (this session) against all 4 reference charts (Sulabh, David,
Sheridan, Surbhi) by direct extraction from their own AstroSage PDFs -- see
tests/calculations/kp/test_significators.py for the pinned tables. Sulabh's
own row cross-checked exactly against the independently-authored Output.txt
reference answer (Mercury 2,3,7,9,12; Rahu 1,2,3,4 -- both exact matches,
found BEFORE this module was written, so this isn't curve-fit to make the
parser pass its own fixture).

SCOPE: parses whichever of the 9 classical planets (Rahu/Ketu included, no
Uranus/Neptune/Pluto -- KP's own table stops at Ketu) have a row on this
page. A planet whose row can't be located is simply absent from the
returned dict -- fail-soft throughout, callers must not assume all 9 keys
are present.
"""
from __future__ import annotations

import io
import logging
from typing import Optional

import pdfplumber

logger = logging.getLogger(__name__)

_PLANET_FULL_NAMES = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)


def parse_kp_significators(file_bytes: bytes) -> dict[str, tuple[int, ...]]:
    """Extract the "Significators of Houses" / "Planet House" table from an
    AstroSage PDF's KP System / Nakshatra Nadi page.

    Args:
        file_bytes: Raw PDF bytes (same input shape as
            agent.astrosage_parser.parse_astrosage_pdf, so a caller already
            holding an uploaded PDF's bytes can call both from one read()).

    Returns:
        {"Sun": (3, 7, 9), ...} for whichever of the 9 planets are found.
        {} if the page/table can't be located, or on any parse error --
        never raises (mirrors astrosage_parser.py's fail-soft contract).
    """
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            page = _find_significators_page(pdf)
            if page is None:
                logger.info(
                    "kp.significators: no 'Significators of Houses' page found."
                )
                return {}
            result = _parse_page(page)
            if not result:
                logger.warning(
                    "kp.significators: page found but no planet rows parsed "
                    "-- AstroSage's page layout may have changed."
                )
            return result
    except Exception:
        logger.exception("kp.significators: unexpected error parsing PDF.")
        return {}


def _find_significators_page(pdf) -> Optional[object]:
    for page in pdf.pages:
        text = page.extract_text() or ""
        if "Significators of Houses" in text:
            return page
    return None


def _parse_page(page) -> dict[str, tuple[int, ...]]:
    """Row-then-column reading order (top, then x0) -- NOT linear text flow.
    This page's Vimshottari dasha-date grid sits beside the significator
    block; linear extract_text() interleaves the two, the same trap the
    KP Cuspal Positions table hit in S143."""
    words = page.extract_words()
    words_sorted = sorted(words, key=lambda w: (round(w["top"], 0), w["x0"]))
    texts = [w["text"] for w in words_sorted]

    anchor = None
    for i in range(len(texts) - 1):
        if texts[i] == "Planet" and texts[i + 1] == "House":
            anchor = i + 2
            break
    if anchor is None:
        return {}

    result: dict[str, tuple[int, ...]] = {}
    i = anchor
    while i < len(texts):
        tok = texts[i]
        if tok in _PLANET_FULL_NAMES and tok not in result:
            i += 1
            houses: list[int] = []
            while i < len(texts) and texts[i].isdigit():
                houses.append(int(texts[i]))
                i += 1
            result[tok] = tuple(houses)
        else:
            i += 1
    return result
