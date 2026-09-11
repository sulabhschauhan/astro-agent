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
