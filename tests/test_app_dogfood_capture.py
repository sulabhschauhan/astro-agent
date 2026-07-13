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
"""
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.interpretive.palm_reading import PalmReadingResult, ValidationReport

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


# ─── S67 schema coverage: retry_used / feature tags / support verdicts ─


def _synthetic_reading() -> PalmReadingResult:
    """A realistic post-R1/R3 PalmReadingResult: 2 sources with distinct
    feature tags, 1 supported feature, 2 unsupported (registry order:
    life line, fate line, sun line -- fate/sun both unsupported), and
    retry_used=True, to prove every new capture line reflects the
    ACTUAL field, not a hardcoded placeholder."""
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
    )


def test_capture_dogfood_run_writes_retry_used_line(monkeypatch, tmp_path):
    import frontend.app as app

    log_path = tmp_path / "dogfood_capture.md"
    monkeypatch.setattr(app, "_DOGFOOD_LOG_PATH", log_path)

    app._capture_dogfood_run("LIFE LINE: A long life line.", None, None, _synthetic_reading())

    content = log_path.read_text(encoding="utf-8")
    assert "retry_used: True" in content


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
