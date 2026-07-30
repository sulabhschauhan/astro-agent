"""
test_query_engine.py
Unit tests for ingestion.query_engine._build_where — pure dict-building logic,
no live ChromaDB or OpenAI calls.
"""

import pytest
from chromadb.api.types import validate_where

from ingestion.query_engine import _build_where


def test_book_name_and_page_ref_range_yields_valid_three_clause_and():
    where = _build_where({"book_name": "cheiroslanguageo00chei_1", "page_ref": (85, 92)})
    assert where == {
        "$and": [
            {"book_name": {"$eq": "cheiroslanguageo00chei_1"}},
            {"page_ref": {"$gte": 85}},
            {"page_ref": {"$lte": 92}},
        ]
    }
    validate_where(where)


def test_page_ref_range_alone_yields_two_clause_and():
    where = _build_where({"page_ref": (85, 92)})
    assert where == {
        "$and": [
            {"page_ref": {"$gte": 85}},
            {"page_ref": {"$lte": 92}},
        ]
    }
    validate_where(where)


def test_page_ref_bare_int_preserves_eq_form():
    where = _build_where({"page_ref": 98})
    assert where == {"page_ref": {"$eq": 98}}


def test_page_ref_range_start_greater_than_end_raises():
    with pytest.raises(ValueError):
        _build_where({"page_ref": (92, 85)})


def test_page_ref_range_wrong_length_raises():
    with pytest.raises(ValueError):
        _build_where({"page_ref": (85,)})


def test_page_ref_range_non_int_items_raises():
    with pytest.raises(ValueError):
        _build_where({"page_ref": ("85", "92")})


def test_tuple_value_on_non_page_ref_key_raises_naming_key():
    with pytest.raises(ValueError, match="book_name"):
        _build_where({"book_name": ("a", "b")})


def test_book_name_alone_still_returns_bare_single_clause():
    where = _build_where({"book_name": "cheiroslanguageo00chei_1"})
    assert where == {"book_name": {"$eq": "cheiroslanguageo00chei_1"}}
