"""
tests/test_app_dogfood_capture.py
AppTest smoke coverage for S66 F5's opt-in dogfood capture log
(frontend/app.py's _DOGFOOD_CAPTURE flag / _capture_dogfood_run()).

Load-time smoke tests only -- no palm upload or generation is simulated,
so these never trigger a real OpenAI call (describe_palm_image /
generate_palm_reading are only reachable behind file-uploader / button
state this harness doesn't drive). Real vision/generation coverage lives
in test_palm_endtoend.py's @pytest.mark.integration tests.

S67 SCHEMA UPDATE: _capture_dogfood_run()'s markdown schema (retry_used,
per-source "feature" tags, feature_support verdicts) is now covered
directly below via a bare `import frontend.app` + monkeypatched
_DOGFOOD_LOG_PATH (a tmp_path, never the real gitignored log) -- AppTest
only drives simulated widget interactions and has no way to call an
internal helper function with a synthetic PalmReadingResult and inspect
its return, so this is a deliberate SECOND, direct-import test style
alongside the AppTest-based load smoke tests above it in this file. The
bare import does print noisy "missing ScriptRunContext... bare mode"
warnings (confirmed harmless -- Streamlit's own message -- before relying
on this) but does not raise; frontend/app.py's module-level code (up to
and including `st.set_page_config`) executes once and is safe to import
directly for this purpose.

S70 P6a SCHEMA UPDATE: same direct-import style, covering the two-stage
(S69 F-H) pipeline's additions to _capture_dogfood_run() -- the new
claims_inventory section (reading.claims, full Stage-1 inventory incl.
excluded_from_voice claims), stage1_retry_features / stage2_retry_used
(alongside the existing COMPAT retry_used), and validation_failures. Also
covers removal of the retired "valid_chunk_ids_count: unavailable" line
(closed by claims_inventory's per-claim chunk_id).

S70 P6b: the two-mode Stage-1 checkpoint (DOGFOOD path blocks on ack/
decline against a PalmReadingPrep; END-USER path is unchanged, generate_
palm_reading() called synchronously). AppTest CANNOT drive a file upload
or button state deep enough to reach the palm-generation button, the
checkpoint panel, or Ack/Decline -- those all sit behind file-uploader /
confirm-button state this harness has no way to simulate (same
limitation the S67 note above already documents for generate_palm_
reading()). Coverage here is therefore: (a) 2 AppTest load-smoke tests
(flag on/off), confirming the new checkpoint code path doesn't break
module-level execution or write to the log without a real generation --
placed directly alongside the pre-existing 2 AppTest tests near the top
of this file, NOT next to the P6b direct-import tests further down,
because an AppTest.from_file() run placed AFTER any bare `import
frontend.app as app` (used throughout the S67/P6a direct-import tests
below) leaks dirty Streamlit widget/form state into the next AppTest run
and spuriously fails it -- confirmed unrelated to any P6b production
code by isolating the same test (passes alone, fails only in that file
position); (b) direct-import tests for the new module-level helper
_capture_checkpoint_declined(), same style as _capture_dogfood_run()'s
S67/P6a tests above. End-to-end checkpoint ack/decline simulation is
NOT attempted here -- it would need a Streamlit-level integration harness
this test file doesn't have.
"""
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.interpretive.claim_extraction import Claim
from agent.interpretive.palm_reading import PalmReadingPrep, PalmReadingResult, ValidationReport

_ROOT     = Path(__file__).parent.parent
_APP_PATH = _ROOT / "frontend" / "app.py"
_LOG_PATH = _ROOT / "diagnostics" / "dogfood_capture.md"


def _log_snapshot():
    """(mtime, content) if the gitignored log already exists locally, else None."""
    if _LOG_PATH.exists():
        return _LOG_PATH.stat().st_mtime_ns, _LOG_PATH.read_bytes()
    return None


def test_app_loads_with_dogfood_capture_flag_off(monkeypatch):
    monkeypatch.delenv("ASTRO_DOGFOOD_CAPTURE", raising=False)
    at = AppTest.from_file(str(_APP_PATH))
    at.run()
    assert not at.exception, [str(e) for e in at.exception]


def test_app_loads_with_dogfood_capture_flag_on_writes_nothing_without_generation(monkeypatch):
    monkeypatch.setenv("ASTRO_DOGFOOD_CAPTURE", "1")
    before = _log_snapshot()

    at = AppTest.from_file(str(_APP_PATH))
    at.run()
    assert not at.exception, [str(e) for e in at.exception]

    after = _log_snapshot()
    assert after == before, (
        "flag-on load with no palm-reading generation must not write to "
        "diagnostics/dogfood_capture.md"
    )


# S70 P6b: kept adjacent to the two AppTest smoke tests above (NOT moved
# to the P6b section further down this file) -- ordering matters here.
# Placing an AppTest.from_file() run AFTER any of this file's bare
# `import frontend.app as app` direct-import tests (used throughout the
# S67/P6a sections below) leaks dirty Streamlit widget/form state into
# the next AppTest run and spuriously fails it (`st.button() can't be
# used in an st.form()`, confirmed unrelated to any P6b code change --
# reproduces identically in isolation-passes-together-fails order).
def test_app_loads_with_checkpoint_code_and_dogfood_flag_off(monkeypatch):
    """The new palm_prep session-state default and checkpoint-panel gate
    must not break module-level load when the flag is off (palm_prep
    stays None, so the blocking panel's `if` never renders anything)."""
    monkeypatch.delenv("ASTRO_DOGFOOD_CAPTURE", raising=False)
    at = AppTest.from_file(str(_APP_PATH))
    at.run()
    assert not at.exception, [str(e) for e in at.exception]


def test_app_loads_with_checkpoint_code_and_dogfood_flag_on_writes_nothing_without_generation(monkeypatch):
    """Same as the flag-on load smoke test above, extended to cover the
    P6b checkpoint code path: loading alone (no upload/button simulated)
    must not write to the log, on the DOGFOOD path either."""
    monkeypatch.setenv("ASTRO_DOGFOOD_CAPTURE", "1")
    before = _log_snapshot()

    at = AppTest.from_file(str(_APP_PATH))
    at.run()
    assert not at.exception, [str(e) for e in at.exception]

    after = _log_snapshot()
    assert after == before, (
        "flag-on load with no palm-reading generation/checkpoint must not "
        "write to diagnostics/dogfood_capture.md"
    )


# ─── S67 schema coverage: retry_used / feature tags / support verdicts ─


def _synthetic_reading() -> PalmReadingResult:
    """A realistic post-R1/R3 PalmReadingResult: 2 sources with distinct
    feature tags, 1 supported feature, 2 unsupported (registry order:
    life line, fate line, sun line -- fate/sun both unsupported), and
    retry_used=True, to prove every new capture line reflects the
    ACTUAL field, not a hardcoded placeholder.

    S70 P6a: 2 claims (one excluded_from_voice, one clean) exercise the
    new claims_inventory section; stage1_retry_features/stage2_retry_used
    exercise the two-stage retry breakdown alongside the pre-existing
    COMPAT retry_used=True.

    S70 (retry attribution rider): stage2_first_attempt_failures carries
    2 distinct failure strings (not 1) so the capture line's semicolon
    JOIN behavior is actually exercised, not just its presence -- proves
    the captured line reflects this ACTUAL field, not a hardcoded
    placeholder. (Left alongside stage2_retry_used=False -- an
    unrealistic combination in real complete_palm_reading() output, but
    this fixture only needs to prove the CAPTURE line reads whatever
    tuple is on the object; the production invariant between the two
    fields is enforced and tested separately in
    tests/interpretive/test_palm_reading.py.)"""
    claims = (
        Claim(
            claim_id="C1",
            feature="life line",
            chunk_id="cheiroslanguageo00chei_1_p134_c2",
            claim_text="A long, unbroken life line indicates steady vitality.",
            valence="positive",
            condition_text=None,
            observation_basis="visible",
            excluded_from_voice=False,
            exclusion_reason=None,
        ),
        Claim(
            claim_id="C2",
            feature="fate line",
            chunk_id="cheiroslanguageo00chei_1_p200_c1",
            claim_text="A fate line rising from the life line suggests self-made success,\nif its origin can be confirmed.",
            valence="positive",
            condition_text="fate line rises from the life line",
            observation_basis="barely visible",
            excluded_from_voice=True,
            exclusion_reason="precondition unverified",
        ),
    )
    return PalmReadingResult(
        reading_text="Your life line shows steady vitality.\n\nFor major life decisions, I recommend consulting a qualified astrologer or palm reader for a personal reading.",
        sources=(
            {"book": "cheiroslanguageo00chei_1", "page": 134, "score": 0.61, "feature": "life line"},
            {"book": "cheiroslanguageo00chei_1", "page": 135, "score": 0.58, "feature": "life line"},
        ),
        validation=ValidationReport(passed=True, failures=()),
        model="gpt-4o",
        retry_used=True,
        supported_features=("life line",),
        unsupported_features=("fate line", "sun line"),
        claims=claims,
        stage1_retry_features=("life line",),
        stage2_retry_used=False,
        stage2_first_attempt_failures=(
            "exemplar_echo: tells its own story to those",
            "jargon_blacklist: found antardasha",
        ),
    )


def test_capture_dogfood_run_writes_retry_used_line(monkeypatch, tmp_path):
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    app._capture_dogfood_run("LIFE LINE: A long life line.", None, None, _synthetic_reading())

    content = log_path.read_text(encoding="utf-8")
    assert "retry_used: True" in content


def test_capture_dogfood_run_writes_stage2_first_attempt_failures_line(monkeypatch, tmp_path):
    """S70 (retry attribution rider): the new capture line joins
    reading.stage2_first_attempt_failures with "; ", verbatim -- proves
    it reflects the ACTUAL field (2 distinct strings, exercising the join,
    not just presence) rather than a hardcoded placeholder."""
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    app._capture_dogfood_run("LIFE LINE: A long life line.", None, None, _synthetic_reading())

    content = log_path.read_text(encoding="utf-8")
    assert (
        "stage2_first_attempt_failures: exemplar_echo: tells its own story to those; "
        "jargon_blacklist: found antardasha"
    ) in content


# ─── _rules_engine special-case rendering (root-cause fix, this session) ─
#
# Diagnosed this session: stage1_feature_diagnostics["_rules_engine"] rides
# the SAME dict the LLM-extraction per-feature ledger uses, but with an
# entirely different payload shape (observation_record/fired_rule_ids/
# observation/dropped_tokens/suppression_log, not attempt_1_status/
# attempt_2_status). Before this fix, _format_stage1_feature_diagnostics_
# lines' generic .get()-based branch silently rendered a content-free
# "outcome=... attempt_1=unknown/? (raw=?) attempt_2=unknown/? (raw=?)"
# line for it -- never crashing, but never surfacing the real engine
# payload anywhere in the capture either (confirmed against the live
# diagnostics/dogfood_capture.md log, 5 occurrences, all identical).


def _rules_engine_diag() -> dict:
    """A realistic engine_diagnostics dict, same shape
    palm_reading._prepare_claims_from_rules / _prepare_deterministic_prep
    actually produce -- not a hand-trimmed stub, so this test exercises the
    real key set."""
    return {
        "enabled": True,
        "failed": False,
        "final_outcome": "rules_engine_ok",
        "observation": {"Line of Life": {"Length": "long", "Depth": "deep"}},
        "dropped_tokens": [],
        "fired_rule_ids": ["L_001"],
        "surviving_rule_ids": ["L_001"],
        "suppression_log": [],
        "citations": {},
        "dropped_rule_ids": [],
        "claim_features_outside_registry": [],
        "observation_record": {
            "enabled_features": [
                "Line of Fate", "Line of Head", "Line of Heart", "Line of Life",
                "Line of Sun", "Mount of Jupiter", "Mount of Venus", "Thumb",
            ],
            "features": {
                "Line of Life": {
                    "tokens": {
                        "Length": {"value": "long", "confidence": 1.0},
                        "Depth": {"value": "deep", "confidence": 1.0},
                    },
                    "unmapped": [
                        {"quality": "curves around the base of the thumb", "attribute_guess": "Curve"},
                    ],
                    "raw_prose": "deep, long, curves around the base of the thumb, no breaks",
                },
            },
            "dropped_disabled": [],
            "unmappable_prose_features": [],
        },
    }


def test_capture_dogfood_run_renders_rules_engine_observation_record(monkeypatch, tmp_path):
    """The root-cause fix itself: observation_record's per-feature tokens/
    unmapped/raw_prose, plus fired_rule_ids, must now actually reach the
    capture file -- none of this appeared anywhere before this fix."""
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    reading = PalmReadingResult(
        reading_text="Your life line shows steady vitality.",
        sources=(),
        validation=ValidationReport(passed=True, failures=()),
        model="gpt-4o",
        retry_used=False,
        supported_features=("life line",),
        unsupported_features=("fate line",),  # trips the "silence" capture gate
        stage1_feature_diagnostics={"_rules_engine": _rules_engine_diag()},
    )
    app._capture_dogfood_run("LIFE LINE: A long life line.", None, None, reading)

    content = log_path.read_text(encoding="utf-8")
    assert "_rules_engine: outcome=rules_engine_ok failed=False" in content
    assert "fired_rule_ids: ['L_001']" in content
    assert (
        "Line of Life: tokens={'Length': {'value': 'long', 'confidence': 1.0}, "
        "'Depth': {'value': 'deep', 'confidence': 1.0}} "
        "unmapped=[{'quality': 'curves around the base of the thumb', "
        "'attribute_guess': 'Curve'}] "
        'raw_prose="deep, long, curves around the base of the thumb, no breaks"'
    ) in content
    # The old, content-free placeholder line must be GONE, not just
    # supplemented -- this is a replacement, not an addition alongside it.
    assert "attempt_1=unknown/? (raw=?)" not in content


def test_capture_dogfood_run_rules_engine_failed_stage_rendered(monkeypatch, tmp_path):
    """A failed engine run (fail-closed boundary) must show WHERE it broke,
    not just that it broke -- failed_stage is the diagnostic that answers
    "which of the 4 boundaries caught it"."""
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    failed_diag = {
        "enabled": True,
        "failed": True,
        "failed_stage": "rule_matching",
        "error": "RuntimeError: engine exploded",
        "final_outcome": "rules_engine_failed",
        "observation": {},
        "dropped_tokens": [],
        "fired_rule_ids": [],
        "surviving_rule_ids": [],
        "suppression_log": [],
        "observation_record": {
            "enabled_features": [], "features": {}, "dropped_disabled": [],
            "unmappable_prose_features": [],
        },
        "citations": {},
        "dropped_rule_ids": [],
    }
    reading = PalmReadingResult(
        reading_text="Your life line shows steady vitality.",
        sources=(),
        validation=ValidationReport(passed=True, failures=()),
        model="gpt-4o",
        retry_used=False,
        supported_features=(),
        unsupported_features=("fate line",),
        stage1_feature_diagnostics={"_rules_engine": failed_diag},
    )
    app._capture_dogfood_run("LIFE LINE: A long life line.", None, None, reading)

    content = log_path.read_text(encoding="utf-8")
    assert "_rules_engine: outcome=rules_engine_failed failed=True" in content
    assert "failed_stage: rule_matching" in content


def test_capture_dogfood_run_rules_engine_empty_observation_record_shows_none(monkeypatch, tmp_path):
    """No captured features at all (e.g. every prose field blank) renders
    an explicit NONE placeholder rather than a silently empty block --
    same "absence is visible, not silent" convention the rest of this
    capture already follows."""
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    diag = _rules_engine_diag()
    diag["observation_record"]["features"] = {}
    reading = PalmReadingResult(
        reading_text="Your life line shows steady vitality.",
        sources=(),
        validation=ValidationReport(passed=True, failures=()),
        model="gpt-4o",
        retry_used=False,
        supported_features=(),
        unsupported_features=("fate line",),
        stage1_feature_diagnostics={"_rules_engine": diag},
    )
    app._capture_dogfood_run("LIFE LINE: A long life line.", None, None, reading)

    content = log_path.read_text(encoding="utf-8")
    assert "observation_record:\n      NONE" in content


def test_capture_dogfood_run_llm_ledger_entries_unchanged_by_the_fix(monkeypatch, tmp_path):
    """Regression guard: a real LLM-extraction per-feature diag (no
    "observation_record" key) must still render via the pre-existing
    attempt_1/attempt_2 branch, untouched by the new special case, on the
    SAME run that also carries a "_rules_engine" entry -- proves the two
    branches coexist correctly rather than one silently swallowing the
    other."""
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    llm_diag = {
        "final_outcome": "validated_ok",
        "attempt_1_status": "validated_ok",
        "attempt_1_claim_count": 2,
        "attempt_1_raw_count": 2,
        "attempt_2_status": "unknown",
        "attempt_2_claim_count": "?",
        "attempt_2_raw_count": "?",
    }
    reading = PalmReadingResult(
        reading_text="Your life line shows steady vitality.",
        sources=(),
        validation=ValidationReport(passed=True, failures=()),
        model="gpt-4o",
        retry_used=False,
        supported_features=(),
        unsupported_features=("fate line",),
        stage1_feature_diagnostics={
            "life line": llm_diag,
            "_rules_engine": _rules_engine_diag(),
        },
    )
    app._capture_dogfood_run("LIFE LINE: A long life line.", None, None, reading)

    content = log_path.read_text(encoding="utf-8")
    assert "life line: outcome=validated_ok attempt_1=validated_ok/2 (raw=2) attempt_2=unknown/? (raw=?)" in content
    assert "_rules_engine: outcome=rules_engine_ok failed=False" in content


def test_capture_dogfood_run_source_lines_carry_feature_tag(monkeypatch, tmp_path):
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    app._capture_dogfood_run("LIFE LINE: A long life line.", None, None, _synthetic_reading())

    content = log_path.read_text(encoding="utf-8")
    # 2 sources in the synthetic reading -> 2 source lines, each carrying
    # the "feature" tag (both "life line" here).
    assert content.count("feature: life line") == 2
    assert "- cheiroslanguageo00chei_1, p.134 (score: 0.61, feature: life line)" in content
    assert "- cheiroslanguageo00chei_1, p.135 (score: 0.58, feature: life line)" in content


def test_capture_dogfood_run_writes_feature_support_verdicts(monkeypatch, tmp_path):
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    app._capture_dogfood_run("LIFE LINE: A long life line.", None, None, _synthetic_reading())

    content = log_path.read_text(encoding="utf-8")
    assert "### feature_support" in content
    assert "supported_features: ('life line',)" in content
    assert "unsupported_features: ('fate line', 'sun line')" in content


# ─── S70 P6a schema coverage: claims_inventory / two-stage retry fields ─


def test_capture_dogfood_run_writes_claims_inventory(monkeypatch, tmp_path):
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    app._capture_dogfood_run("LIFE LINE: A long life line.", None, None, _synthetic_reading())

    content = log_path.read_text(encoding="utf-8")
    assert "### claims_inventory" in content

    # Clean claim: every field reflects the actual Claim, not a placeholder.
    assert (
        "C1 | life line | cheiroslanguageo00chei_1_p134_c2 | positive | "
        "False | None | None | A long, unbroken life line indicates "
        "steady vitality."
    ) in content

    # Excluded claim: excluded_from_voice/exclusion_reason/condition_text
    # all present, and claim_text's internal newline is flattened to a
    # single space (verbatim otherwise, per P6a's single-line requirement).
    assert (
        "C2 | fate line | cheiroslanguageo00chei_1_p200_c1 | positive | "
        "True | precondition unverified | fate line rises from the life "
        "line | A fate line rising from the life line suggests self-made "
        "success, if its origin can be confirmed."
    ) in content
    # No raw newline survives inside the C2 claim line.
    assert "success,\nif its origin" not in content


def test_capture_dogfood_run_claims_inventory_empty(monkeypatch, tmp_path):
    """S83: unsupported_features carries a single feature so the run fires
    the "silence" gate and reaches the writer (a clean reading now writes
    nothing) -- claims/stage1 diagnostics stay empty as before, so the
    EMPTY placeholder is still exercised on a reachable path."""
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    reading = PalmReadingResult(
        reading_text="Your life line shows steady vitality.",
        sources=(),
        validation=ValidationReport(passed=True, failures=()),
        model="gpt-4o",
        retry_used=False,
        supported_features=(),
        unsupported_features=("fate line",),
    )
    app._capture_dogfood_run("LIFE LINE: A long life line.", None, None, reading)

    content = log_path.read_text(encoding="utf-8")
    assert "### capture_reason" in content
    assert "silence" in content
    assert "### claims_inventory" in content
    assert "claims_inventory: EMPTY" in content


def test_capture_dogfood_run_writes_two_stage_retry_fields(monkeypatch, tmp_path):
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    app._capture_dogfood_run("LIFE LINE: A long life line.", None, None, _synthetic_reading())

    content = log_path.read_text(encoding="utf-8")
    assert "stage1_retry_features: life line" in content
    assert "stage2_retry_used: False" in content


def test_capture_dogfood_run_stage1_retry_features_none_when_empty(monkeypatch, tmp_path):
    """S83: unsupported_features carries a single feature so the run fires
    the "silence" gate and reaches the writer (a clean reading now writes
    nothing) -- stage1_retry_features stays empty as before, so the NONE
    placeholder is still exercised on a reachable path."""
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    reading = PalmReadingResult(
        reading_text="Your life line shows steady vitality.",
        sources=(),
        validation=ValidationReport(passed=True, failures=()),
        model="gpt-4o",
        retry_used=False,
        supported_features=(),
        unsupported_features=("fate line",),
    )
    app._capture_dogfood_run("LIFE LINE: A long life line.", None, None, reading)

    content = log_path.read_text(encoding="utf-8")
    assert "### capture_reason" in content
    assert "silence" in content
    assert "stage1_retry_features: NONE" in content
    assert "stage2_retry_used: False" in content


def test_capture_dogfood_run_writes_validation_failures_line(monkeypatch, tmp_path):
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    reading = PalmReadingResult(
        reading_text="Your life line shows steady vitality.",
        sources=(),
        validation=ValidationReport(passed=False, failures=("V-1: untagged sentence", "V-3: illegal tag")),
        model="gpt-4o",
        retry_used=True,
        supported_features=(),
        unsupported_features=(),
    )
    app._capture_dogfood_run("LIFE LINE: A long life line.", None, None, reading)

    content = log_path.read_text(encoding="utf-8")
    assert "validation_failures: V-1: untagged sentence; V-3: illegal tag" in content


def test_capture_dogfood_run_validation_failures_none_when_empty(monkeypatch, tmp_path):
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    app._capture_dogfood_run("LIFE LINE: A long life line.", None, None, _synthetic_reading())

    content = log_path.read_text(encoding="utf-8")
    assert "validation_failures: NONE" in content


def test_capture_dogfood_run_no_longer_writes_valid_chunk_ids_count(monkeypatch, tmp_path):
    """S70 P6a: the retired accepted-gap (e) line must be gone -- the
    claims_inventory section's per-claim chunk_id closes that gap."""
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    app._capture_dogfood_run("LIFE LINE: A long life line.", None, None, _synthetic_reading())

    content = log_path.read_text(encoding="utf-8")
    assert "valid_chunk_ids_count" not in content


def test_capture_dogfood_run_still_appends_never_overwrites(monkeypatch, tmp_path):
    """Constraint check: two successive captures must both survive in the
    log -- the writer opens in append ("a") mode, never truncates."""
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    app._capture_dogfood_run("LIFE LINE: A long life line.", None, None, _synthetic_reading())
    first_content = log_path.read_text(encoding="utf-8")
    app._capture_dogfood_run("LIFE LINE: A long life line.", None, None, _synthetic_reading())
    second_content = log_path.read_text(encoding="utf-8")

    # 2 captures -> the first run's full text must still be a prefix-ish
    # substring of the log after the second capture (nothing truncated).
    assert first_content in second_content
    assert second_content.count("### feature_support") == 2


# ─── S70 P6b: direct-import coverage for _capture_checkpoint_declined ──


def _synthetic_prep() -> PalmReadingPrep:
    """A realistic post-Stage-1 PalmReadingPrep: same 2 claims as
    _synthetic_reading() (C1 clean, C2 excluded_from_voice with a
    condition_text and an embedded newline in claim_text), plus
    diagnostics carrying stage1_retry_features/stage1_failed_features --
    the two keys _capture_checkpoint_declined() reads directly."""
    claims = (
        Claim(
            claim_id="C1",
            feature="life line",
            chunk_id="cheiroslanguageo00chei_1_p134_c2",
            claim_text="A long, unbroken life line indicates steady vitality.",
            valence="positive",
            condition_text=None,
            observation_basis="visible",
            excluded_from_voice=False,
            exclusion_reason=None,
        ),
        Claim(
            claim_id="C2",
            feature="fate line",
            chunk_id="cheiroslanguageo00chei_1_p200_c1",
            claim_text="A fate line rising from the life line suggests self-made success,\nif its origin can be confirmed.",
            valence="positive",
            condition_text="fate line rises from the life line",
            observation_basis="barely visible",
            excluded_from_voice=True,
            exclusion_reason="precondition unverified",
        ),
    )
    return PalmReadingPrep(
        gated_results={"life line": [], "fate line": []},
        supported_features=("life line",),
        unsupported_features=("fate line", "sun line"),
        claims=claims,
        texts_by_feature={"life line": "LIFE LINE: A long life line."},
        diagnostics={
            "stage1": {},
            "stage1_failed_features": ("sun line",),
            "stage1_retry_features": ("life line",),
        },
    )


def test_capture_checkpoint_declined_writes_claims_inventory(monkeypatch, tmp_path):
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    app._capture_checkpoint_declined(_synthetic_prep())

    content = log_path.read_text(encoding="utf-8")
    assert content.startswith("## CHECKPOINT-DECLINED")
    assert "### claims_inventory" in content

    # Clean claim: every field reflects the actual Claim.
    assert (
        "C1 | life line | cheiroslanguageo00chei_1_p134_c2 | positive | "
        "False | None | None | A long, unbroken life line indicates "
        "steady vitality."
    ) in content

    # Excluded claim: excluded_from_voice/exclusion_reason/condition_text
    # present, embedded newline flattened to a single space.
    assert (
        "C2 | fate line | cheiroslanguageo00chei_1_p200_c1 | positive | "
        "True | precondition unverified | fate line rises from the life "
        "line | A fate line rising from the life line suggests self-made "
        "success, if its origin can be confirmed."
    ) in content
    assert "success,\nif its origin" not in content


def test_capture_checkpoint_declined_writes_stage1_diagnostics(monkeypatch, tmp_path):
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    app._capture_checkpoint_declined(_synthetic_prep())

    content = log_path.read_text(encoding="utf-8")
    assert "stage1_retry_features: life line" in content
    assert "stage1_failed_features: sun line" in content


def test_capture_checkpoint_declined_has_no_reading_fields(monkeypatch, tmp_path):
    """A declined checkpoint never reaches Stage 2 -- there is no
    reading_text, no READING (TAGGED), no sources, no ring1_validation,
    because no PalmReadingResult exists for a declined prep."""
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    app._capture_checkpoint_declined(_synthetic_prep())

    content = log_path.read_text(encoding="utf-8")
    assert "### reading_text" not in content
    assert "### READING (TAGGED)" not in content
    assert "### sources" not in content
    assert "### ring1_validation" not in content
    assert "### feature_support" not in content


def test_capture_checkpoint_declined_empty_claims(monkeypatch, tmp_path):
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    prep = PalmReadingPrep(
        gated_results={},
        supported_features=(),
        unsupported_features=(),
        claims=(),
        texts_by_feature={},
        diagnostics={"stage1": {}, "stage1_failed_features": (), "stage1_retry_features": ()},
    )
    app._capture_checkpoint_declined(prep)

    content = log_path.read_text(encoding="utf-8")
    assert "claims_inventory: EMPTY" in content
    assert "stage1_retry_features: NONE" in content
    assert "stage1_failed_features: NONE" in content


def test_capture_checkpoint_declined_still_appends_never_overwrites(monkeypatch, tmp_path):
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    app._capture_checkpoint_declined(_synthetic_prep())
    first_content = log_path.read_text(encoding="utf-8")
    app._capture_checkpoint_declined(_synthetic_prep())
    second_content = log_path.read_text(encoding="utf-8")

    assert first_content in second_content
    assert second_content.count("## CHECKPOINT-DECLINED") == 2


# ─── S83: failure-only capture net ─────────────────────────────────────


def _clean_reading() -> PalmReadingResult:
    """A run with nothing to flag: every feature supported, no retry, Ring
    1 passed clean, and its one claim's chunk sits inside its feature's
    own gated page range."""
    claims = (
        Claim(
            claim_id="C1",
            feature="life line",
            chunk_id="cheiroslanguageo00chei_1_p134_c2",
            claim_text="A long, unbroken life line indicates steady vitality.",
            valence="positive",
            condition_text=None,
            observation_basis="visible",
            excluded_from_voice=False,
            exclusion_reason=None,
        ),
    )
    return PalmReadingResult(
        reading_text="Your life line shows steady vitality.",
        sources=(
            {"book": "cheiroslanguageo00chei_1", "page": 134, "score": 0.61, "feature": "life line"},
        ),
        validation=ValidationReport(passed=True, failures=()),
        model="gpt-4o",
        retry_used=False,
        supported_features=("life line",),
        unsupported_features=(),
        claims=claims,
        stage1_retry_features=(),
        stage2_retry_used=False,
    )


def test_run_had_failure_clean_reading_returns_false_empty():
    import frontend.app as app

    fired, tags = app._run_had_failure(_clean_reading())
    assert (fired, tags) == (False, [])


def test_capture_dogfood_run_writes_nothing_for_clean_reading(monkeypatch, tmp_path):
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    app._capture_dogfood_run("LIFE LINE: A long life line.", None, None, _clean_reading())

    assert not log_path.exists()


def test_run_had_failure_unsupported_features_returns_silence():
    import frontend.app as app

    reading = PalmReadingResult(
        reading_text="Your life line shows steady vitality.",
        sources=(),
        validation=ValidationReport(passed=True, failures=()),
        model="gpt-4o",
        retry_used=False,
        supported_features=(),
        unsupported_features=("fate line",),
    )
    fired, tags = app._run_had_failure(reading)
    assert (fired, tags) == (True, ["silence"])


def test_capture_dogfood_run_writes_capture_reason_silence(monkeypatch, tmp_path):
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    reading = PalmReadingResult(
        reading_text="Your life line shows steady vitality.",
        sources=(),
        validation=ValidationReport(passed=True, failures=()),
        model="gpt-4o",
        retry_used=False,
        supported_features=(),
        unsupported_features=("fate line",),
    )
    app._capture_dogfood_run("LIFE LINE: A long life line.", None, None, reading)

    content = log_path.read_text(encoding="utf-8")
    assert content.count("## RUN") == 1
    assert "### capture_reason" in content
    assert "silence" in content


# ─── S119 Step 4: wrong_source across both citation kinds ──────────────
#
# The capture net's wrong_source trigger used to parse claim.chunk_id for
# EVERY claim. Since S119 Step 2 a rule-sourced claim carries
# chunk_id=None, so that parse raised TypeError into a surrounding
# `except Exception: continue` -- the trigger silently stopped evaluating
# rule claims at all. These tests pin both citation kinds.


def _rule_claim(**overrides) -> Claim:
    kwargs = dict(
        claim_id="C1", feature="fate line", rule_id="FT_003", source_page=103,
        source_quote="When the line of fate rises from the wrist, it is a sign of good fortune.",
        claim_text="A fate line rising from the wrist is a sign of extreme good fortune.",
        valence="supports", condition_text=None,
        observation_basis="Line of Fate Slope=straight",
        excluded_from_voice=False, exclusion_reason=None,
    )
    kwargs.update(overrides)
    return Claim.by_rule(**kwargs)


def _reading_with(claims: tuple[Claim, ...]) -> PalmReadingResult:
    """A run clean in every respect EXCEPT whatever the given claims say,
    so any fired tag is attributable to the claims alone."""
    return PalmReadingResult(
        reading_text="A reading.",
        sources=(),
        validation=ValidationReport(passed=True, failures=()),
        model="gpt-4o",
        retry_used=False,
        supported_features=("life line",),
        unsupported_features=(),
        claims=claims,
        stage1_retry_features=(),
        stage2_retry_used=False,
    )


def test_rule_claim_does_not_raise_and_a_clean_citation_is_not_flagged():
    """HARDEST CASE -- the exact silent TypeError. A rule claim reaches the
    trigger with chunk_id=None; it must be evaluated (not swallowed) and,
    being cleanly cited, must NOT be tagged wrong_source.

    Also the coordinate-system trap: this claim's source_page is 103,
    while _FEATURE_PAGE_RANGES["fate line"] is (162, 165). Those are two
    different page-numbering systems (rule files anchor to
    data/cheiro/cheiro_clean_v1.json; the ranges come from the chunk
    corpus' page_ref). Range-checking a rule page would tag wrong_source
    on all 16 fate rules -- this asserts it does not."""
    import frontend.app as app

    claim = _rule_claim()
    assert claim.chunk_id is None
    assert app._FEATURE_PAGE_RANGES["fate line"] == (162, 165)
    assert not (162 <= claim.citation.source_page <= 165)

    fired, tags = app._run_had_failure(_reading_with((claim,)))
    assert (fired, tags) == (False, [])


@pytest.mark.parametrize(
    "broken",
    [
        {"source_page": None},
        {"source_quote": ""},
        {"source_quote": "   "},
    ],
)
def test_rule_claim_with_an_unusable_citation_is_tagged_wrong_source(broken):
    """The rule-claim analogue of "wrong source": the citation cannot
    identify its source at all. A missing page or an empty quote means the
    claim is ungrounded, which is a citation-identity failure -- the same
    class the existing "hallucination" disposition maps to wrong_source
    for."""
    import frontend.app as app

    fired, tags = app._run_had_failure(_reading_with((_rule_claim(**broken),)))
    assert (fired, tags) == (True, ["wrong_source"])


def test_excluded_rule_claim_is_skipped_even_when_its_citation_is_broken():
    """Unchanged precedence: an excluded_from_voice claim never reaches the
    citation check, exactly as before."""
    import frontend.app as app

    claim = _rule_claim(source_page=None, excluded_from_voice=True,
                        exclusion_reason="precondition unverified")
    fired, tags = app._run_had_failure(_reading_with((claim,)))
    assert (fired, tags) == (False, [])


# ─── by-chunk parity: behavior unchanged ───────────────────────────────


def _by_chunk_claim(chunk_id: str, feature: str = "life line") -> Claim:
    return Claim(
        claim_id="C1", feature=feature, chunk_id=chunk_id,
        claim_text="A long, unbroken life line indicates steady vitality.",
        valence="positive", condition_text=None, observation_basis="visible",
        excluded_from_voice=False, exclusion_reason=None,
    )


def test_by_chunk_claim_outside_its_feature_page_range_still_fires_wrong_source():
    """GUARD/PARITY. life line's range is (133, 139); a chunk from p200 is
    out-of-chapter and must still be caught -- this is the retrieval
    failure mode the check exists for, and Step 4 must not weaken it."""
    import frontend.app as app

    assert app._FEATURE_PAGE_RANGES["life line"] == (133, 139)
    fired, tags = app._run_had_failure(
        _reading_with((_by_chunk_claim("cheiroslanguageo00chei_1_p200_c1"),))
    )
    assert (fired, tags) == (True, ["wrong_source"])


def test_by_chunk_claim_inside_its_feature_page_range_is_still_clean():
    import frontend.app as app

    fired, tags = app._run_had_failure(
        _reading_with((_by_chunk_claim("cheiroslanguageo00chei_1_p134_c2"),))
    )
    assert (fired, tags) == (False, [])


def test_by_chunk_claim_with_a_malformed_chunk_id_is_still_skipped_not_flagged():
    """Unchanged: an unparseable chunk_id yields no page and is skipped,
    same as the old inline regex's `if match is None: continue`."""
    import frontend.app as app

    fired, tags = app._run_had_failure(_reading_with((_by_chunk_claim("c1"),)))
    assert (fired, tags) == (False, [])


def test_by_chunk_claim_for_a_feature_with_no_page_range_is_skipped():
    """markings/other features has a None range -- nothing to check."""
    import frontend.app as app

    assert app._FEATURE_PAGE_RANGES["markings/other features"] is None
    fired, tags = app._run_had_failure(
        _reading_with((
            _by_chunk_claim("cheiroslanguageo00chei_1_p200_c1",
                            feature="markings/other features"),
        ))
    )
    assert (fired, tags) == (False, [])


def test_mixed_run_flags_only_the_broken_rule_claim():
    """Both kinds in one run: the healthy by-chunk claim and the healthy
    rule claim stay silent; the broken rule claim alone fires."""
    import frontend.app as app

    claims = (
        _by_chunk_claim("cheiroslanguageo00chei_1_p134_c2"),
        _rule_claim(claim_id="C2"),
        _rule_claim(claim_id="C3", rule_id="FT_004", source_quote=""),
    )
    fired, tags = app._run_had_failure(_reading_with(claims))
    assert (fired, tags) == (True, ["wrong_source"])


# ─── claims_inventory renders the citation identity ────────────────────


def test_claims_inventory_renders_the_by_rule_citation_form_not_none(
    monkeypatch, tmp_path
):
    """Was a bare "None" column for every rule claim, which reads as
    missing data rather than as "cited by rule"."""
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    reading = _reading_with((_rule_claim(source_quote=""),))  # broken -> forces a capture
    app._capture_dogfood_run("FATE LINE: Present.", None, None, reading)

    content = log_path.read_text(encoding="utf-8")
    assert "C1 | fate line | rule:FT_003@p103 |" in content
    assert "C1 | fate line | None |" not in content


def test_claims_inventory_by_chunk_column_is_unchanged(monkeypatch, tmp_path):
    """PARITY: a retrieval claim's column is still its chunk_id, verbatim."""
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    reading = _reading_with((_by_chunk_claim("cheiroslanguageo00chei_1_p200_c1"),))
    app._capture_dogfood_run("LIFE LINE: Long.", None, None, reading)

    content = log_path.read_text(encoding="utf-8")
    assert "C1 | life line | cheiroslanguageo00chei_1_p200_c1 |" in content


def test_no_source_quote_reaches_the_dogfood_capture(monkeypatch, tmp_path):
    """CONTAINMENT: citation_ref excludes the quote by construction, so a
    rule claim's book prose cannot enter the capture through the
    inventory column."""
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    quote = "ZZQUOTEZZ When the line of fate rises from the wrist"
    reading = _reading_with((
        _rule_claim(source_quote=quote),
        _rule_claim(claim_id="C2", rule_id="FT_004", source_quote=""),
    ))
    app._capture_dogfood_run("FATE LINE: Present.", None, None, reading)

    assert quote not in log_path.read_text(encoding="utf-8")


def test_stage1_diagnostics_render_surviving_rule_features():
    """S119 Step 3 exposed surviving_rule_features as the authoritative
    jurisdiction record; the capture now surfaces it beside
    surviving_rule_ids, so a reviewer can answer "which features was the
    support gate overruled on?" from the capture alone."""
    import frontend.app as app

    lines = app._format_stage1_feature_diagnostics_lines({
        # "observation_record" is what selects the engine branch of the
        # formatter (see its docstring -- deliberately keyed on the payload
        # shape, not on the "_rules_engine" name), so it must be present.
        "_rules_engine": {
            "final_outcome": "rules_engine_ok",
            "failed": False,
            "observation_record": {"enabled_features": []},
            "fired_rule_ids": ["FT_011"],
            "surviving_rule_ids": ["FT_011"],
            "surviving_rule_features": ["fate line"],
        },
    })
    text = "\n".join(lines)
    assert "surviving_rule_ids: ['FT_011']" in text
    assert "surviving_rule_features: ['fate line']" in text


def test_stage1_diagnostics_tolerate_a_capture_without_the_new_key():
    """Same .get()-defaulted style as every other diagnostics line: an
    older engine block carrying no surviving_rule_features still renders."""
    import frontend.app as app

    lines = app._format_stage1_feature_diagnostics_lines({
        "_rules_engine": {
            "final_outcome": "rules_engine_ok", "failed": False,
            "observation_record": {"enabled_features": []},
        },
    })
    assert "surviving_rule_features: []" in "\n".join(lines)
