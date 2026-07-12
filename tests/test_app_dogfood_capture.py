"""
tests/test_app_dogfood_capture.py
AppTest smoke coverage for S66 F5's opt-in dogfood capture log
(frontend/app.py's _DOGFOOD_CAPTURE flag / _capture_dogfood_run()).

Load-time smoke tests only -- no palm upload or generation is simulated,
so these never trigger a real OpenAI call (describe_palm_image /
generate_palm_reading are only reachable behind file-uploader / button
state this harness doesn't drive). Real vision/generation coverage lives
in test_palm_endtoend.py's @pytest.mark.integration tests.
"""
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).parent.parent))

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
