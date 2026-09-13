"""Interpreter stage: ghost guard, claim cleaning, honest refusal. Stub llm; no API."""
import json
from agent.astro import interpreter as I

PAYLOAD = {"segments": [
    {"segment_id": "ch24_s082", "text": "9th lord in 4th: houses and wealth.", "kept": True},
    {"segment_id": "ch24_s111", "text": "12th lord in 4th: loss of houses.", "kept": True},
    {"segment_id": "ch24_s050", "text": "dropped segment", "kept": False},
], "units": [{"unit_id": "bphs1_ch11", "text": "Judgement of houses."}]}

def _stub(payload_obj):
    def f(system, user, *, model, reasoning_effort):
        return json.dumps(payload_obj), {"prompt_tokens": 10, "completion_tokens": 5, "reasoning_tokens": 2}
    return f

def test_strips_ghost_ids_keeps_real():
    stub = _stub({"claims": [{"statement": "A.", "segment_ids": ["ch24_s082", "ch99_s999"]}],
                  "silent_on": [], "refused": False})
    out = I.interpret("q", "facts", PAYLOAD, llm=stub)
    assert out["ghost_citations"] == ["ch99_s999"]
    assert out["claims"] == [{"statement": "A.", "segment_ids": ["ch24_s082"]}]
    assert out["refused"] is False

def test_claim_with_only_ghost_id_is_dropped():
    stub = _stub({"claims": [{"statement": "A.", "segment_ids": ["ch99_s999"]}], "refused": False})
    out = I.interpret("q", "facts", PAYLOAD, llm=stub)
    assert out["claims"] == [] and out["refused"] is True
    assert out["ghost_citations"] == ["ch99_s999"]

def test_dropped_segment_id_is_not_a_valid_citation():
    stub = _stub({"claims": [{"statement": "A.", "segment_ids": ["ch24_s050"]}], "refused": False})
    out = I.interpret("q", "facts", PAYLOAD, llm=stub)
    assert out["claims"] == [] and out["ghost_citations"] == ["ch24_s050"]

def test_whole_chapter_unit_id_is_a_valid_citation():
    stub = _stub({"claims": [{"statement": "A.", "segment_ids": ["bphs1_ch11"]}], "refused": False})
    out = I.interpret("q", "facts", PAYLOAD, llm=stub)
    assert out["claims"] == [{"statement": "A.", "segment_ids": ["bphs1_ch11"]}]

def test_empty_payload_refuses_without_calling_llm():
    called = []
    def boom(*a, **k): called.append(1); raise AssertionError("must not call")
    out = I.interpret("q", "facts", {"segments": [], "units": []}, llm=boom)
    assert out["refused"] is True and not called

def test_corpus_first_prompt_puts_verses_in_system():
    captured = {}
    def cap(system, user, *, model, reasoning_effort):
        captured["system"] = system; captured["user"] = user
        return json.dumps({"claims": [], "refused": True}), {}
    I.interpret("myq", "myfacts", PAYLOAD, llm=cap)
    assert "9th lord in 4th" in captured["system"]        # verses lead the prompt (cacheable)
    assert "myfacts" in captured["user"] and "myq" in captured["user"]


# ── S130: the citable-id manifest (ghost-citation root cause) ──────────────

def test_manifest_lists_both_id_shapes_and_warns_about_sub_ids():
    """Every ghost in the 2026-09-13 runs came from two address formats in one
    prompt: [ch34_s003] for segments, [bphs2_ch57] for whole chapters. The
    manifest must state both spaces explicitly."""
    from agent.astro import interpreter as I
    payload = {"segments": [{"segment_id": "ch34_s003", "text": "x", "kept": True},
                            {"segment_id": "ch34_s009", "text": "y", "kept": True},
                            {"segment_id": "ch24_s030", "text": "z", "kept": False}],
               "units": [{"unit_id": "bphs2_ch57", "text": "whole chapter text"}]}
    m = I._id_manifest(payload)
    assert "ch34_s003, ch34_s009" in m
    assert "ch24_s030" not in m, "an unkept segment is not citable"
    assert "bphs2_ch57" in m
    assert "NO sub-ids" in m
    assert "COMPLETE" in m


def test_whole_chapters_are_marked_inline_in_the_verse_block():
    from agent.astro import interpreter as I
    payload = {"segments": [{"segment_id": "ch34_s003", "text": "seg", "kept": True}],
               "units": [{"unit_id": "bphs2_ch57", "text": "chap"}]}
    block = I._verse_block(payload)
    assert "[ch34_s003] seg" in block
    assert "[bphs2_ch57] (whole chapter -- no sub-ids) chap" in block


def test_manifest_is_empty_when_nothing_is_citable():
    from agent.astro import interpreter as I
    assert I._id_manifest({"segments": [], "units": []}) == ""


def test_manifest_reaches_the_system_prompt():
    """The manifest is useless if it never ships. Capture the system string."""
    from agent.astro import interpreter as I
    seen = {}

    def stub(system, user, *, model=None, reasoning_effort=None):
        seen["system"] = system
        return ('{"claims": [], "silent_on": [], "refused": true}', {"prompt_tokens": 0})

    payload = {"segments": [{"segment_id": "ch34_s003", "text": "seg", "kept": True}],
               "units": [{"unit_id": "bphs2_ch57", "text": "chap"}]}
    I.interpret("q", "FACTS", payload, llm=stub)
    assert "CITABLE IDS" in seen["system"]
    assert "ch34_s003" in seen["system"]
    assert "bphs2_ch57" in seen["system"]
