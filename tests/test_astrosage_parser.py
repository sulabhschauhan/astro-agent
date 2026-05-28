"""
tests/test_astrosage_parser.py
Unit tests for agent/astrosage_parser.py.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.astrosage_parser import (
    _LINES_PER_SECTION,
    _PRIORITY_ORDER,
    _extract_sections,
    parse_astrosage_pdf,
)


# ─── _extract_sections ────────────────────────────────────────────────────────

def test_extract_sections_empty_text():
    assert _extract_sections("") == {}


def test_extract_sections_no_keywords():
    text = "Some random text\nwith no matching section keywords."
    assert _extract_sections(text) == {}


def test_extract_sections_single_section():
    text = "Varshaphal\n" + "\n".join(f"line {i}" for i in range(10))
    result = _extract_sections(text)
    assert "Varshaphal" in result
    assert "line 0" in result["Varshaphal"]


def test_extract_sections_keyword_case_insensitive():
    # "VARSHAPHAL" must still match the lowercase keyword "varshaphal"
    text = "VARSHAPHAL\nsome prediction text"
    result = _extract_sections(text)
    assert "Varshaphal" in result


def test_extract_sections_alternate_keyword():
    # "annual predictions" is an alias for "Varshaphal"
    text = "Annual Predictions\nsome content here"
    result = _extract_sections(text)
    assert "Varshaphal" in result


def test_extract_sections_respects_priority_order():
    # Text in reverse priority order; output keys must follow _PRIORITY_ORDER
    text = (
        "Lal Kitab\nlk content\n"
        "Sade Sati\nss content\n"
        "Varshaphal\nvp content\n"
    )
    result = _extract_sections(text)
    found_keys = list(result.keys())
    expected_order = [k for k in _PRIORITY_ORDER if k in result]
    assert found_keys == expected_order


def test_extract_sections_repeated_occurrences_merge_or_skip():
    # Repeat with >100-char body is appended (PDF page-break pattern).
    long_body = "repeated prediction content " * 5  # >100 chars
    text_merge = (
        "Varshaphal\nfirst block\n"
        "Pratyantar\npt content\n"
        f"Varshaphal\n{long_body}\n"
    )
    result = _extract_sections(text_merge)
    assert "first block" in result["Varshaphal"]
    assert long_body.strip() in result["Varshaphal"]

    # Repeat with ≤100-char body is NOT appended (bare page-header noise).
    text_skip = (
        "Varshaphal\nfirst block\n"
        "Pratyantar\npt content\n"
        "Varshaphal\nshort repeat\n"
    )
    result2 = _extract_sections(text_skip)
    assert "first block" in result2["Varshaphal"]
    assert "short repeat" not in result2["Varshaphal"]


def test_extract_sections_line_cap():
    # Buffer must not exceed the header line + _LINES_PER_SECTION body lines
    body_lines = [f"transit line {i}" for i in range(_LINES_PER_SECTION + 20)]
    text = "Transit Today\n" + "\n".join(body_lines)
    result = _extract_sections(text)
    captured = result["Transit Today"].splitlines()
    assert len(captured) <= _LINES_PER_SECTION + 1


def test_extract_sections_all_seven_sections():
    text = (
        "Varshaphal\nvp text\n"
        "Pratyantar\npt text\n"
        "Muntha\nmn text\n"
        "Sade Sati\nss text\n"
        "Favourable Points\nfp text\n"
        "Transit Today\ntt text\n"
        "Lal Kitab\nlk text\n"
    )
    result = _extract_sections(text)
    assert set(result.keys()) == {
        "Varshaphal", "Pratyantar", "Muntha",
        "Sade Sati", "Favourable Points", "Transit Today", "Lal Kitab",
    }


# ─── parse_astrosage_pdf ──────────────────────────────────────────────────────

def _mock_pdf(text: str):
    """Return a mock pdfplumber context manager that yields `text` from one page."""
    page = MagicMock()
    page.extract_text.return_value = text
    pdf = MagicMock()
    pdf.pages = [page]
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=pdf)
    ctx.__exit__ = MagicMock(return_value=False)
    return ctx


def test_parse_returns_none_when_no_sections_found():
    with patch("agent.astrosage_parser.pdfplumber.open", return_value=_mock_pdf("nothing relevant here")):
        assert parse_astrosage_pdf(b"fake") is None


def test_parse_returns_none_when_extracted_text_too_short():
    # Keyword matched but body is tiny — combined < 100 chars
    with patch("agent.astrosage_parser.pdfplumber.open", return_value=_mock_pdf("Varshaphal\nshort")):
        assert parse_astrosage_pdf(b"fake") is None


def test_parse_returns_none_when_pdfplumber_yields_no_text():
    # page.extract_text() returns None — _extract_text returns ""
    page = MagicMock()
    page.extract_text.return_value = None
    pdf = MagicMock()
    pdf.pages = [page]
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=pdf)
    ctx.__exit__ = MagicMock(return_value=False)
    with patch("agent.astrosage_parser.pdfplumber.open", return_value=ctx):
        assert parse_astrosage_pdf(b"fake") is None


def test_parse_returns_none_on_pdfplumber_exception():
    with patch("agent.astrosage_parser.pdfplumber.open", side_effect=Exception("corrupt PDF")):
        assert parse_astrosage_pdf(b"bad bytes") is None


def test_parse_returns_prefixed_string_on_success():
    long_body = "prediction line\n" * 10
    text = f"Varshaphal\n{long_body}"
    with patch("agent.astrosage_parser.pdfplumber.open", return_value=_mock_pdf(text)):
        result = parse_astrosage_pdf(b"fake")
    assert result is not None
    assert result.startswith("ASTROSAGE PDF DATA:\n")


def test_parse_output_contains_section_labels():
    long_body = "x\n" * 20
    text = f"Varshaphal\n{long_body}Pratyantar\n{long_body}"
    with patch("agent.astrosage_parser.pdfplumber.open", return_value=_mock_pdf(text)):
        result = parse_astrosage_pdf(b"fake")
    assert "[Varshaphal]" in result
    assert "[Pratyantar]" in result
