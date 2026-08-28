"""
tests/interpretive/test_palm_reading_llm_fallback.py

S109: tests for the LLM-fallback wiring in agent/interpretive/
palm_reading.py -- _assemble_relational_targets_with_fallback,
_log_fallback_audits, and prepare_palm_reading's client-gated wiring.

Lives in its OWN file (mirrors test_palm_reading_rules_engine.py's own
precedent, same "monolith split" rationale that file's docstring cites):
this is a clearly separate concern (LLM-rescue wiring) from that file's
scope (the rule engine itself). Shared fakes imported from
test_palm_reading.py / test_palm_reading_rules_engine.py rather than
re-rolled -- one _FakeClient/_FakeSearch/_observation_response definition
in the suite.

NO live LLM call anywhere here: every client is either a stub or None.

DETERMINISM GATE (hard-abort criterion this task's own instructions
require): proves fallback-OFF (a poison-pill client that would raise if
ever consulted) produces byte-identical targets to the S107
_assemble_relational_targets path, on fixtures where every contact
already resolves deterministically. If this ever fails, S109's wiring
must not ship -- it would mean the fallback changes behavior even when
nothing needs rescuing.
"""

from __future__ import annotations

import json

import pytest

from agent.interpretive import palm_reading, observation_extractor, palm_rules_table, capture_net
from tests.interpretive.test_palm_reading import _FakeClient, _FakeSearch, _chunk
from tests.interpretive.test_palm_reading_rules_engine import _observation_response


# ─── Autouse: redirect capture_net's sink for EVERY test in this file ───────
# prepare_palm_reading now unconditionally wires capture_net.map_fallback_
# audits (S110 capture-net task) whenever the _DETERMINISTIC_RULES_ENABLED
# block runs -- WITHOUT this, several pre-existing tests above (e.g. the
# "resolved" H_028 wiring proof) would silently write into the real
# diagnostics/capture_net/failures.jsonl on every suite run. Autouse so no
# existing test needs editing to stay safe; module-scoped path is fine
# since these tests never assert on this specific file's rows.


@pytest.fixture(autouse=True)
def _redirect_capture_net_sink(tmp_path, monkeypatch):
    monkeypatch.setattr(capture_net, "_CAPTURE_NET_PATH", tmp_path / "_autouse_capture_net" / "failures.jsonl")


# ─── Stub client for the LLM-fallback's own resolutions JSON shape ─────────
# _FakeClient/_FakeCompletions (test_palm_reading.py) is generic enough to
# reuse directly -- it just returns whatever `content` string it's given,
# regardless of call shape, and records every call for assertion.


def _resolutions_client(resolutions: list[str]) -> _FakeClient:
    return _FakeClient(content=json.dumps({"resolutions": resolutions}))


def _poison_client() -> _FakeClient:
    """A client that RAISES if ever consulted -- the determinism gate's
    poison pill. If _assemble_relational_targets_with_fallback ever calls
    this client when every contact in the batch already resolves
    deterministically, the test fails loudly."""
    return _FakeClient(exception=RuntimeError("DETERMINISM GATE VIOLATED -- client should not have been called"))


def _contact(verb, position="at start", target="Line of Life", clarity="clear"):
    return {"target": target, "verb": verb, "position": position, "clarity": clarity}


def _fired_ids(targets: dict) -> list[str]:
    rules = palm_rules_table.load_rule_set()
    fired = palm_rules_table.match({}, {}, rules, targets=targets)
    return sorted(r.rule_id for r in fired)


# ═══════════════════════════════════════════════════════════════════════
# DETERMINISM GATE -- hard abort criterion
# ═══════════════════════════════════════════════════════════════════════


def test_determinism_gate_h028_fixture_zero_calls_byte_identical():
    text = "HEAD LINE: present\n  CONTACTS: Line of Life | joins | at start | clear\n"
    rel = observation_extractor.extract_relations(text)

    poison = _poison_client()
    left_ct, right_ct, audits = palm_reading._assemble_relational_targets_with_fallback(
        rel["contacts"], {}, poison
    )
    deterministic_ref = palm_reading._assemble_relational_targets(rel["contacts"])

    assert len(poison.completions.calls) == 0
    assert left_ct == deterministic_ref
    assert right_ct == {}
    # The contact WAS pre-checked (S108's own defensive re-validation),
    # so it still produces an audit entry -- just with disposition
    # "already_resolved_no_llm_needed" (no LLM was ever consulted for it,
    # per the zero-calls assertion above).
    assert len(audits) == 1
    assert audits[0]["disposition"] == "already_resolved_no_llm_needed"


def test_determinism_gate_l026_fixture_zero_calls_byte_identical():
    text = (
        "HEAD LINE: present\n"
        "  CONTACTS: Line of Heart | joins | at start | clear\n"
        "  CONTACTS: Line of Life | joins | at start | clear\n"
        "\n"
        "HEART LINE: present\n"
        "  CONTACTS: Line of Life | joins | at start | clear\n"
    )
    rel = observation_extractor.extract_relations(text)

    poison = _poison_client()
    left_ct, right_ct, audits = palm_reading._assemble_relational_targets_with_fallback(
        rel["contacts"], {}, poison
    )
    deterministic_ref = palm_reading._assemble_relational_targets(rel["contacts"])

    assert len(poison.completions.calls) == 0
    assert left_ct == deterministic_ref
    assert left_ct == {
        "Line of Head": {"joins_at_origin": {"Line of Heart", "Line of Life"}},
        "Line of Heart": {"joins_at_origin": {"Line of Life"}},
    }
    assert right_ct == {}

    fired_with_fallback = _fired_ids(left_ct)
    fired_deterministic = _fired_ids(deterministic_ref)
    assert fired_with_fallback == fired_deterministic == ["H_028", "L_026"]


def test_determinism_gate_both_hands_populated_zero_calls_correct_routing():
    """Proves the (hand, feature) index-alignment is correct when BOTH
    hands carry deterministically-resolvable contacts -- left gets H_028's
    join, right gets an unrelated distinct-verb contact -- and neither
    hand's result leaks into the other's dict."""
    left_text = "HEAD LINE: present\n  CONTACTS: Line of Life | joins | at start | clear\n"
    right_text = "FATE LINE: present\n  CONTACTS: Line of Head | crosses | mid-course | clear\n"
    left_rel = observation_extractor.extract_relations(left_text)
    right_rel = observation_extractor.extract_relations(right_text)

    poison = _poison_client()
    left_ct, right_ct, audits = palm_reading._assemble_relational_targets_with_fallback(
        left_rel["contacts"], right_rel["contacts"], poison
    )

    assert len(poison.completions.calls) == 0
    assert left_ct == {"Line of Head": {"joins_at_origin": {"Line of Life"}}}
    assert right_ct == {"Line of Fate": {"cuts": {"Line of Head"}}}
    # Cross-contamination check: left's join must never appear on right's dict or vice versa.
    assert "Line of Fate" not in left_ct
    assert "Line of Head" not in right_ct


# ═══════════════════════════════════════════════════════════════════════
# FALLBACK-FIRING (stubbed client) -- unit level
# ═══════════════════════════════════════════════════════════════════════


def test_residual_synonym_on_left_hand_rescues_h028_exactly_one_call():
    left_text = "HEAD LINE: present\n  CONTACTS: Line of Life | fuses | at start | clear\n"
    left_rel = observation_extractor.extract_relations(left_text)
    right_rel = observation_extractor.extract_relations("")

    client = _resolutions_client(["merges"])
    left_ct, right_ct, audits = palm_reading._assemble_relational_targets_with_fallback(
        left_rel["contacts"], right_rel["contacts"], client
    )

    assert len(client.completions.calls) == 1
    assert left_ct == {"Line of Head": {"joins_at_origin": {"Line of Life"}}}
    assert "H_028" in _fired_ids(left_ct)

    assert len(audits) == 1
    assert audits[0]["raw_verb"] == "fuses"
    assert audits[0]["llm_canonical_choice"] == "merges"
    assert audits[0]["final_token"] == "joins_at_origin"
    assert audits[0]["disposition"] == "resolved"


def test_residual_unclear_stays_silent_h028_does_not_fire():
    left_text = "HEAD LINE: present\n  CONTACTS: Line of Life | wobbles | at start | clear\n"
    left_rel = observation_extractor.extract_relations(left_text)

    client = _resolutions_client(["unclear"])
    left_ct, right_ct, audits = palm_reading._assemble_relational_targets_with_fallback(
        left_rel["contacts"], {}, client
    )

    assert len(client.completions.calls) == 1
    assert left_ct == {}  # nothing filed -- honest silence
    assert "H_028" not in _fired_ids(left_ct)
    assert audits[0]["disposition"] == "llm_unclear"
    assert audits[0]["final_token"] is None


def test_mixed_deterministic_and_synonym_across_hands_exactly_one_call():
    """One deterministic contact (left, 'joins') + one genuine synonym
    (right, 'severs' -> 'cuts') -- the resolver's own internal re-check
    means only the genuinely-unresolved one enters the LLM batch, but
    this must still cost exactly ONE call for the whole reading."""
    left_text = "HEAD LINE: present\n  CONTACTS: Line of Life | joins | at start | clear\n"
    right_text = "FATE LINE: present\n  CONTACTS: Line of Head | severs | unknown | clear\n"
    left_rel = observation_extractor.extract_relations(left_text)
    right_rel = observation_extractor.extract_relations(right_text)

    client = _resolutions_client(["cuts"])
    left_ct, right_ct, audits = palm_reading._assemble_relational_targets_with_fallback(
        left_rel["contacts"], right_rel["contacts"], client
    )

    assert len(client.completions.calls) == 1
    assert left_ct == {"Line of Head": {"joins_at_origin": {"Line of Life"}}}
    assert right_ct == {"Line of Fate": {"cuts": {"Line of Head"}}}

    dispositions = {a["raw_verb"]: a["disposition"] for a in audits}
    assert dispositions["joins"] == "already_resolved_no_llm_needed"
    assert dispositions["severs"] == "resolved"


def test_residual_join_family_synonym_unusable_position_stays_silenced_and_logged(caplog):
    """position_unresolved (S109 amendment, ratified): the LLM DOES
    resolve a valid join-family canonical verb ("fuses" -> "merges"), but
    the vision model reported no usable position ("unknown", not "at
    start"/"mid-course"/"at end") -- the deterministic position-split
    still cannot choose joins_at_origin vs meets, so the token stays
    honestly None. Logged for visibility/measurement only (this is the
    behavior the amendment adds) -- never fired, never triggers a second
    vision call to recover a position."""
    left_text = "HEAD LINE: present\n  CONTACTS: Line of Life | fuses | unknown | clear\n"
    left_rel = observation_extractor.extract_relations(left_text)

    client = _resolutions_client(["merges"])
    with caplog.at_level("WARNING"):
        left_ct, right_ct, audits = palm_reading._assemble_relational_targets_with_fallback(
            left_rel["contacts"], {}, client
        )
        palm_reading._log_fallback_audits(audits)

    assert len(client.completions.calls) == 1  # one LLM call, no second call to recover position
    assert left_ct == {}  # no token filed -- honest silence
    assert "H_028" not in _fired_ids(left_ct)

    assert len(audits) == 1
    assert audits[0]["disposition"] == "position_unresolved"
    assert audits[0]["final_token"] is None
    assert audits[0]["llm_canonical_choice"] == "merges"

    audit_lines = [r.message for r in caplog.records if "S109 fallback audit" in r.message]
    assert len(audit_lines) == 1
    assert "raw_verb='fuses'" in audit_lines[0]
    assert "llm_choice='merges'" in audit_lines[0]
    assert "final_token=None" in audit_lines[0]
    assert "disposition='position_unresolved'" in audit_lines[0]


# ═══════════════════════════════════════════════════════════════════════
# WIRING-LEVEL (prepare_palm_reading) -- client-gating + degrade-on-error
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
def rules_engine_on(monkeypatch):
    monkeypatch.setattr(palm_reading, "_DETERMINISTIC_RULES_ENABLED", True)


def test_prepare_palm_reading_client_none_uses_deterministic_path_no_fallback(rules_engine_on, monkeypatch):
    """client=None must take the S107 no-LLM path per hand -- zero
    fallback involvement is structurally guaranteed (no client exists to
    call), but this test also confirms the rules still fire correctly on
    that path post-S109."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))

    observation_json = _observation_response({})
    client = _FakeClient(responses=[(observation_json, None)])

    text = "HEAD LINE: present\n  CONTACTS: Line of Life | joins | at start | clear\n"
    prep = palm_reading.prepare_palm_reading(palm_left=text, palm_right=None, client=client)

    diag = prep.diagnostics["rules_engine"]
    assert "H_028" in diag["fired_rule_ids"]
    # Only the observation-extractor call -- no fallback call was possible
    # since client=None is threaded through _assemble_relational_targets
    # (S107), not _assemble_relational_targets_with_fallback (S109).
    assert len(client.completions.calls) == 1


def test_prepare_palm_reading_client_not_none_wires_fallback_and_fires_h028(rules_engine_on, monkeypatch, caplog):
    """Full wiring proof: a genuine residual synonym on the left hand
    gets rescued through the real prepare_palm_reading() call path (not
    just the unit-level _with_fallback helper), H_028 fires, and the
    audit is logged at WARNING with the documented format."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))

    fallback_json = json.dumps({"resolutions": ["merges"]})
    observation_json = _observation_response({})
    # Call order inside prepare_palm_reading's deterministic block: the
    # S109 fallback assembly runs BEFORE _prepare_claims_from_rules'
    # own observation-extractor call -- responses must be sequenced
    # accordingly.
    client = _FakeClient(responses=[(fallback_json, None), (observation_json, None)])

    text = "HEAD LINE: present\n  CONTACTS: Line of Life | fuses | at start | clear\n"
    with caplog.at_level("WARNING"):
        prep = palm_reading.prepare_palm_reading(palm_left=text, palm_right=None, client=client)

    diag = prep.diagnostics["rules_engine"]
    assert "H_028" in diag["fired_rule_ids"]
    assert len(client.completions.calls) == 2  # fallback + observation extractor, no more

    audit_lines = [r.message for r in caplog.records if "S109 fallback audit" in r.message]
    assert len(audit_lines) == 1
    assert "raw_verb='fuses'" in audit_lines[0]
    assert "llm_choice='merges'" in audit_lines[0]
    assert "final_token='joins_at_origin'" in audit_lines[0]
    assert "disposition='resolved'" in audit_lines[0]


def test_prepare_palm_reading_fallback_raises_degrades_to_deterministic_result(rules_engine_on, monkeypatch, caplog):
    """The fallback assembly itself is mocked to raise unexpectedly (a
    scenario the resolver's own fail-closed contract shouldn't normally
    allow, but this proves prepare_palm_reading's OWN degrade-safe
    wrapping holds regardless) -- the reading must still be produced,
    using the deterministic-only result, with the error logged."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))

    def _explode(*args, **kwargs):
        raise RuntimeError("simulated unexpected fallback assembly failure")

    monkeypatch.setattr(palm_reading, "_assemble_relational_targets_with_fallback", _explode)

    observation_json = _observation_response({})
    client = _FakeClient(responses=[(observation_json, None)])

    text = "HEAD LINE: present\n  CONTACTS: Line of Life | joins | at start | clear\n"
    with caplog.at_level("ERROR"):
        prep = palm_reading.prepare_palm_reading(palm_left=text, palm_right=None, client=client)

    # Reading still produced, and the DETERMINISTIC result (H_028 still
    # fires off the base-form "joins", which needed no rescue anyway) --
    # degrade-safe, not degrade-to-broken.
    diag = prep.diagnostics["rules_engine"]
    assert "H_028" in diag["fired_rule_ids"]

    error_lines = [r.message for r in caplog.records if "S109 LLM fallback assembly failed" in r.message]
    assert len(error_lines) == 1
    assert "simulated unexpected fallback assembly failure" in error_lines[0]


# ═══════════════════════════════════════════════════════════════════════
# AUDIT LOGGING FORMAT
# ═══════════════════════════════════════════════════════════════════════


def test_log_fallback_audits_logs_each_fallback_disposition(caplog):
    audits = [
        {"raw_verb": "fuses", "llm_canonical_choice": "merges", "final_token": "joins_at_origin", "disposition": "resolved"},
        {"raw_verb": "wobbles", "llm_canonical_choice": "unclear", "final_token": None, "disposition": "llm_unclear"},
        {"raw_verb": "destroys", "llm_canonical_choice": "obliterates", "final_token": None, "disposition": "hallucination"},
        {"raw_verb": "fuses", "llm_canonical_choice": None, "final_token": None, "disposition": "batch_call_failed"},
        {"raw_verb": "fuses", "llm_canonical_choice": None, "final_token": None, "disposition": "batch_malformed_response"},
        {"raw_verb": "fuses", "llm_canonical_choice": "merges", "final_token": None, "disposition": "position_unresolved"},
    ]
    with caplog.at_level("WARNING"):
        palm_reading._log_fallback_audits(audits)
    audit_lines = [r.message for r in caplog.records if "S109 fallback audit" in r.message]
    assert len(audit_lines) == 6


def test_log_fallback_audits_never_logs_already_resolved_but_does_log_position_unresolved(caplog):
    # S109 amendment: position_unresolved WAS excluded, now ratified as
    # a logged disposition (visibility/measurement only -- no token, no
    # second call). already_resolved_no_llm_needed remains the ONLY
    # disposition that stays silent (purely deterministic, no AI decision).
    audits = [
        {"raw_verb": "joins", "llm_canonical_choice": None, "final_token": "joins_at_origin", "disposition": "already_resolved_no_llm_needed"},
        {"raw_verb": "fuses", "llm_canonical_choice": "merges", "final_token": None, "disposition": "position_unresolved"},
    ]
    with caplog.at_level("WARNING"):
        palm_reading._log_fallback_audits(audits)
    audit_lines = [r.message for r in caplog.records if "S109 fallback audit" in r.message]
    assert len(audit_lines) == 1
    assert "raw_verb='fuses'" in audit_lines[0]
    assert "disposition='position_unresolved'" in audit_lines[0]
    assert "raw_verb='joins'" not in audit_lines[0]


def test_log_fallback_audits_empty_list_logs_nothing(caplog):
    with caplog.at_level("WARNING"):
        palm_reading._log_fallback_audits([])
    assert not any("S109 fallback audit" in r.message for r in caplog.records)


# ═══════════════════════════════════════════════════════════════════════
# CAPTURE-NET WIRING -- hand/feature fix (_assemble_relational_targets_
# with_fallback) + prepare_palm_reading integration (capture_net.
# map_fallback_audits, side by side with _log_fallback_audits). The real
# diagnostics/capture_net/ dir is NEVER touched here -- every test
# monkeypatches capture_net._CAPTURE_NET_PATH into tmp_path.
# ═══════════════════════════════════════════════════════════════════════


def _read_capture_lines(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


@pytest.fixture
def capture_net_tmp_path(tmp_path, monkeypatch):
    out_path = tmp_path / "capture_net" / "failures.jsonl"
    monkeypatch.setattr(capture_net, "_CAPTURE_NET_PATH", out_path)
    return out_path


def test_mixed_dispositions_both_hands_capture_rows_carry_correct_hand_and_feature(capture_net_tmp_path):
    """HARDEST CASE: proves hand/feature ALIGNMENT, not just presence --
    three contacts spread across both hands and three different features,
    resolving to three different dispositions (resolved/llm_unclear/
    hallucination). Each capture-net row must carry the hand+feature of
    ITS OWN contact, never a fixed, swapped, or missing one. Batch order
    (left before right; right's features in text-appearance order Fate
    then Heart) verified directly against extract_relations' dict-
    insertion-order behavior before writing this test."""
    left_text = "HEAD LINE: present\n  CONTACTS: Line of Life | fuses | at start | clear\n"
    right_text = (
        "FATE LINE: present\n  CONTACTS: Line of Head | wobbles | mid-course | clear\n"
        "\n"
        "HEART LINE: present\n  CONTACTS: Line of Head | melts | mid-course | clear\n"
    )
    left_rel = observation_extractor.extract_relations(left_text)
    right_rel = observation_extractor.extract_relations(right_text)

    # fuses(left, Line of Head)  -> merges     -> resolved
    # wobbles(right, Line of Fate) -> unclear  -> llm_unclear
    # melts(right, Line of Heart)  -> obliterates (off-vocabulary) -> hallucination
    client = _resolutions_client(["merges", "unclear", "obliterates"])
    left_ct, right_ct, audits = palm_reading._assemble_relational_targets_with_fallback(
        left_rel["contacts"], right_rel["contacts"], client
    )
    assert len(audits) == 3
    dispositions = {a["raw_verb"]: a["disposition"] for a in audits}
    assert dispositions == {
        "fuses": "resolved", "wobbles": "llm_unclear", "melts": "hallucination",
    }

    reading_id = "test-mixed-reading"
    capture_net.map_fallback_audits(audits, reading_id)

    rows = _read_capture_lines(capture_net_tmp_path)
    assert len(rows) == 3
    by_verb = {r["raw_verb"]: r for r in rows}

    assert by_verb["fuses"]["hand"] == "left"
    assert by_verb["fuses"]["feature"] == "Line of Head"
    assert by_verb["fuses"]["trigger"] == "ai_decision"

    assert by_verb["wobbles"]["hand"] == "right"
    assert by_verb["wobbles"]["feature"] == "Line of Fate"
    assert by_verb["wobbles"]["trigger"] == "silence"

    assert by_verb["melts"]["hand"] == "right"
    assert by_verb["melts"]["feature"] == "Line of Heart"
    assert by_verb["melts"]["trigger"] == "wrong_source"

    for row in rows:
        assert row["reading_id"] == reading_id


def test_prepare_palm_reading_client_none_capture_net_gets_empty_list_no_rows(
    rules_engine_on, monkeypatch, capture_net_tmp_path,
):
    """client=None takes the S107 no-LLM path per hand -- fallback_audits
    stays [] structurally, so capture_net.map_fallback_audits is called
    with an empty list (or not meaningfully at all): no crash, no rows."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))

    observation_json = _observation_response({})
    client = _FakeClient(responses=[(observation_json, None)])

    text = "HEAD LINE: present\n  CONTACTS: Line of Life | joins | at start | clear\n"
    prep = palm_reading.prepare_palm_reading(palm_left=text, palm_right=None, client=client)

    diag = prep.diagnostics["rules_engine"]
    assert "H_028" in diag["fired_rule_ids"]  # reading completed normally
    assert _read_capture_lines(capture_net_tmp_path) == []


def test_prepare_palm_reading_fallback_assembly_raises_no_capture_rows_no_raise(
    rules_engine_on, monkeypatch, capture_net_tmp_path, caplog,
):
    """The fallback assembly itself raises (mirrors the existing degrade-
    safe test for _log_fallback_audits) -- fallback_audits degrades to
    [], so capture_net receives nothing to write, and the wiring itself
    must not raise despite the upstream failure."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))

    def _explode(*args, **kwargs):
        raise RuntimeError("simulated unexpected fallback assembly failure")

    monkeypatch.setattr(palm_reading, "_assemble_relational_targets_with_fallback", _explode)

    observation_json = _observation_response({})
    client = _FakeClient(responses=[(observation_json, None)])

    text = "HEAD LINE: present\n  CONTACTS: Line of Life | joins | at start | clear\n"
    with caplog.at_level("ERROR"):
        prep = palm_reading.prepare_palm_reading(palm_left=text, palm_right=None, client=client)

    diag = prep.diagnostics["rules_engine"]
    assert "H_028" in diag["fired_rule_ids"]  # reading still completed, deterministic result
    assert _read_capture_lines(capture_net_tmp_path) == []


def test_prepare_palm_reading_capture_net_raising_does_not_break_reading(
    rules_engine_on, monkeypatch, capture_net_tmp_path, caplog,
):
    """Belt-and-suspenders proof: even if capture_net.map_fallback_audits
    itself raises (capture_net.py is already fail-safe internally, but
    this proves prepare_palm_reading's OWN wrapping holds regardless),
    the reading must still complete, a WARNING is logged, and
    _log_fallback_audits' own logging (which runs first, unmodified) is
    unaffected -- the two run side by side, neither gates the other."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))

    def _explode(*args, **kwargs):
        raise RuntimeError("simulated capture-net failure")

    monkeypatch.setattr(capture_net, "map_fallback_audits", _explode)

    fallback_json = json.dumps({"resolutions": ["merges"]})
    observation_json = _observation_response({})
    client = _FakeClient(responses=[(fallback_json, None), (observation_json, None)])

    text = "HEAD LINE: present\n  CONTACTS: Line of Life | fuses | at start | clear\n"
    with caplog.at_level("WARNING"):
        prep = palm_reading.prepare_palm_reading(palm_left=text, palm_right=None, client=client)

    diag = prep.diagnostics["rules_engine"]
    assert "H_028" in diag["fired_rule_ids"]  # reading still completed

    warning_lines = [r.message for r in caplog.records if "capture-net wiring failed" in r.message]
    assert len(warning_lines) == 1
    assert "simulated capture-net failure" in warning_lines[0]

    audit_lines = [r.message for r in caplog.records if "S109 fallback audit" in r.message]
    assert len(audit_lines) == 1  # unaffected by the capture_net failure

    assert _read_capture_lines(capture_net_tmp_path) == []  # the patched function never wrote anything


def test_no_palm_text_leaks_into_capture_net_rows_end_to_end(
    rules_engine_on, monkeypatch, capture_net_tmp_path,
):
    """Reuses the capture_net allow-list guarantee end-to-end through the
    real prepare_palm_reading() call path: a distinctive marker string
    embedded in the raw palm text must never appear in the written
    capture-net file, and none of the raw-text-bearing keys ever appear
    on a written row."""
    chunk = _chunk()
    monkeypatch.setattr(palm_reading, "search", _FakeSearch([chunk]))

    fallback_json = json.dumps({"resolutions": ["merges"]})
    observation_json = _observation_response({})
    client = _FakeClient(responses=[(fallback_json, None), (observation_json, None)])

    secret_marker = "SUPER_SECRET_PALM_DESCRIPTION_MARKER_XYZ"
    text = (
        "HEAD LINE: present\n"
        "  CONTACTS: Line of Life | fuses | at start | clear\n"
        f"NOTES: {secret_marker}\n"
    )
    prep = palm_reading.prepare_palm_reading(palm_left=text, palm_right=None, client=client)
    diag = prep.diagnostics["rules_engine"]
    assert "H_028" in diag["fired_rule_ids"]

    rows = _read_capture_lines(capture_net_tmp_path)
    assert len(rows) == 1  # the one genuine LLM resolution ("resolved" -> ai_decision)
    assert rows[0]["trigger"] == "ai_decision"

    raw_file_text = capture_net_tmp_path.read_text(encoding="utf-8")
    assert secret_marker not in raw_file_text
    forbidden_keys = {"palm_text", "left_palm_description", "palm_left", "image_bytes", "hand_detail"}
    assert forbidden_keys.isdisjoint(rows[0].keys())
