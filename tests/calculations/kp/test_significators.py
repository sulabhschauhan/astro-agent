"""
tests/calculations/kp/test_significators.py
Validation (S143-followup, this session) for
agent.calculations.kp.significators.parse_kp_significators, across all 4
reference charts on record (Sulabh, David, Sheridan, Surbhi) -- same
reference-chart set already oracle-anchored elsewhere (test_sade_sati.py,
test_kp_oracle_validation.py).

UNLIKE test_kp_oracle_validation.py (which transcribes its oracle values as
hardcoded literals, since sub_lords.py itself is ephemeris-computed and only
uses the PDF for an offline comparison), this module's function under test
IS a PDF parser -- there is nothing to validate except by actually opening
the real PDF and parsing it. So this suite reads data/pdfs/*.pdf directly
(same 4 files test_kp_oracle_validation.py's docstring already names), and
pins the PARSED RESULT as the regression fixture -- not an independent
"expected" derived some other way, because the AstroSage report itself IS
the oracle here (see significators.py's own docstring: parsing this table is
a restate of AstroSage's own computation, not a new one this suite could
independently re-derive).

Sulabh's own row cross-checks exactly against Output.txt (an independently
authored reference answer, not written with this parser in mind): Mercury
2,3,7,9,12 and Rahu 1,2,3,4 both match exactly -- see kp_significator_facts.py
docstring. That is the actual correctness evidence for this parser; the
fixed literals below are the regression floor once that evidence was in
hand.

TRANSCRIPTION METHOD: page.extract_words() sorted by (top, x0) bounding-box
position, same fix test_kp_oracle_validation.py's own docstring documents
for the neighboring Cuspal Positions table on the identical page -- a naive
linear extract_text() interleaves this page's side-by-side dasha-date grid
into the significator rows.

Python 3.11.
"""
from __future__ import annotations

import os

import pytest

from agent.calculations.kp.significators import parse_kp_significators

# Relative to repo root -- same directory/files test_kp_oracle_validation.py's
# docstring already names for the other KP table on this same PDF page.
_PDF_PATHS = {
    "Sulabh":   "data/pdfs/VedicReport5-24-202610-01-26PM.pdf",
    "David":    "data/pdfs/David Kundli.pdf",
    "Sheridan": "data/pdfs/Sheridan Kundli.pdf",
    "Surbhi":   "data/pdfs/Wife_VedicReport.pdf",
}

# Parsed "Significators of Houses" tables, all 4 reference charts -- see
# module docstring for why these literals ARE the oracle (not an
# independently-derived expectation).
_EXPECTED = {
    "Sulabh": {
        "Sun": (3, 7, 9), "Moon": (1, 3, 4, 8, 10), "Mars": (1, 3, 4, 11, 12),
        "Mercury": (2, 3, 7, 9, 12), "Jupiter": (1, 3, 4, 8), "Venus": (3, 5, 6, 10),
        "Saturn": (2, 8, 12), "Rahu": (1, 2, 3, 4), "Ketu": (3, 8),
    },
    "David": {
        "Sun": (4, 12), "Moon": (8, 11, 12), "Mars": (9, 11, 12),
        "Mercury": (1, 2, 5, 10, 11, 12), "Jupiter": (1, 2, 4, 5, 7, 8, 10),
        "Venus": (1, 2, 3, 5, 10), "Saturn": (5, 6, 10), "Rahu": (2, 4, 7, 8),
        "Ketu": (3, 8),
    },
    "Sheridan": {
        "Sun": (2, 3, 10, 12), "Moon": (2, 6, 10), "Mars": (5, 6, 7, 10, 11),
        "Mercury": (1, 4, 5, 11, 12), "Jupiter": (1, 5, 7, 10, 12),
        "Venus": (1, 3, 5, 12), "Saturn": (5, 8, 9, 12), "Rahu": (2, 10, 12),
        "Ketu": (5, 6, 8, 9),
    },
    "Surbhi": {
        "Sun": (1, 8, 10, 11, 12), "Moon": (2, 4, 9), "Mars": (2, 6, 7, 8),
        "Mercury": (1, 8, 10, 11, 12), "Jupiter": (5, 10),
        "Venus": (1, 4, 8, 9, 11, 12), "Saturn": (3, 4, 9), "Rahu": (2, 8),
        "Ketu": (2, 6, 7, 8),
    },
}


def _repo_root() -> str:
    """tests/calculations/kp/ -> repo root, 3 levels up."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", "..", ".."))


def _read_pdf(relpath: str) -> bytes:
    path = os.path.join(_repo_root(), relpath)
    with open(path, "rb") as f:
        return f.read()


@pytest.fixture(scope="module", params=list(_PDF_PATHS))
def chart_name(request):
    return request.param


def test_parses_all_9_planets_for_every_chart(chart_name):
    got = parse_kp_significators(_read_pdf(_PDF_PATHS[chart_name]))
    assert set(got) == set(_EXPECTED[chart_name]), (
        f"{chart_name}: expected all 9 planets, got keys {sorted(got)}"
    )


def test_significator_houses_match_for_every_chart(chart_name):
    got = parse_kp_significators(_read_pdf(_PDF_PATHS[chart_name]))
    assert got == _EXPECTED[chart_name]


def test_sulabh_mercury_and_rahu_match_output_txt_reference():
    """The actual correctness evidence, not just a regression pin: these two
    rows were independently confirmed against Output.txt (a benchmark answer
    written before this parser existed) in this session's own investigation."""
    got = parse_kp_significators(_read_pdf(_PDF_PATHS["Sulabh"]))
    assert got["Mercury"] == (2, 3, 7, 9, 12)
    assert got["Rahu"] == (1, 2, 3, 4)


def test_empty_bytes_returns_empty_dict():
    assert parse_kp_significators(b"") == {}


def test_garbage_bytes_never_raises():
    assert parse_kp_significators(b"not a pdf at all") == {}


def test_a_real_pdf_without_the_kp_page_returns_empty_dict():
    # BPHS vol 1 has no KP significator page -- exercises the "page not
    # found" branch on a real, valid, non-garbage PDF (not just garbage
    # bytes, which only proves the exception handler works).
    path = os.path.join(_repo_root(), "data", "pdfs", "BPHS - 1 RSanthanam.pdf")
    if not os.path.exists(path):
        pytest.skip("BPHS - 1 RSanthanam.pdf not present in this checkout")
    with open(path, "rb") as f:
        assert parse_kp_significators(f.read()) == {}
