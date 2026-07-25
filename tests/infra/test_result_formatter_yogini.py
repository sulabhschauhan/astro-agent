"""Tests for agent/infra/result_formatter.py's "yogini_dasha" domain branch
(_format_yogini_dasha(), Session 73/Prompt 5).

All profiles are synthetic DomainChartProfile instances built directly
(frozen dataclass) -- same no-mocks-needed convention as
test_result_formatter_av_transit.py. Mirrors that file's structure, adjusted
to yogini_dasha's actually-verified payload contract (checked directly
against chart_profile.py's committed Commit B branch before writing this
file, NOT against the original task prompt's assumed shape, which differed
in three ways -- see result_formatter.py's own module docstring and
_format_yogini_dasha()'s docstring for the full comparison):

- payload["current_md"] carries only {"lord", "yogini_name", "start_jd",
  "end_jd"} -- no "years" key, so no test here asserts one.
- payload carries no top-level "all_periods" or "sources" key.
- current_md is never None by the time it reaches this branch (chart_
  profile.py's own branch fails closed with RuntimeError first) -- so,
  unlike av_transit's empty-sub_windows never-collapse test, there is no
  "current_md=None" test here; that path is unreachable given the real
  upstream contract, not a defensive case this branch needs to handle.

4 tests:
1. Happy path -- tier/demotion_reason/sources/stub_caveats/uncertainty
   passthrough, current_md fields round-trip, start/end are hand-verifiable
   _format_jd() strings (J2000 epoch anchor, same reference point
   test_result_formatter_av_transit.py's own test 5 uses), and no raw
   start_jd/end_jd/years keys leak into answer_payload.
2. Missing "lord" key -> KeyError (fail-closed, no partial render --
   this file's established convention, see _format_dasha/_format_marriage/
   _format_av_transit).
3. Dispatch: format_answer() routes domain="yogini_dasha" to
   _format_yogini_dasha() -- guards against the branch existing but the
   format_answer() if/elif entry being forgotten.
4. sources tuple is exactly ("yogini",), not read from payload (payload
   carries no "sources" key to read from).
"""
import pytest

from agent.infra.chart_profile import AnswerTier, DomainChartProfile
from agent.infra.result_formatter import _format_yogini_dasha, format_answer

# J2000 epoch anchor -- same hand-verifiable reference point
# test_result_formatter_av_transit.py's own test 5 uses (2451545.0 ->
# "1 Jan 2000" via swe.revjul()).
_J2000_JD = 2451545.0
_J2000_PLUS_4YR_JD = 2451545.0 + 4 * 365.25  # arbitrary, not a real MD span


def _profile(current_md: dict) -> DomainChartProfile:
    return DomainChartProfile(
        domain="yogini_dasha",
        chart_id="Sulabh",
        evaluated_at_jd=_J2000_JD,
        payload={"current_md": current_md},
        stub_caveats=(),
        uncertainty_virupa=0.0,
        uncertainty_days=0.0,
    )


def _current_md(**overrides) -> dict:
    base = {
        "lord": "Mars",
        "yogini_name": "Bhramari",
        "start_jd": _J2000_JD,
        "end_jd": _J2000_PLUS_4YR_JD,
    }
    base.update(overrides)
    return base


def test_happy_path():
    profile = _profile(_current_md())
    answer = _format_yogini_dasha(profile)

    assert answer.domain == "yogini_dasha"
    assert answer.tier == AnswerTier.TIER_2_RANGE
    assert answer.demotion_reason is None
    assert answer.sources == ("yogini",)
    assert answer.stub_caveats == ()
    assert answer.uncertainty_virupa == 0.0
    assert answer.uncertainty_days == 0.0

    current_md = answer.answer_payload["current_md"]
    assert current_md["lord"] == "Mars"
    assert current_md["yogini_name"] == "Bhramari"
    assert isinstance(current_md["start"], str)
    assert isinstance(current_md["end"], str)
    assert current_md["start"] == "1 Jan 2000"  # hand-verifiable J2000 anchor

    # No raw JD floats or the dropped "years" key leak into answer_payload.
    assert set(current_md) == {"lord", "yogini_name", "start", "end"}


def test_missing_lord_key_raises_keyerror():
    current_md = _current_md()
    del current_md["lord"]
    profile = _profile(current_md)

    with pytest.raises(KeyError, match="lord"):
        _format_yogini_dasha(profile)


def test_dispatch_routes_to_format_yogini_dasha():
    profile = _profile(_current_md())
    assert format_answer(profile) == _format_yogini_dasha(profile)


def test_sources_is_exactly_yogini_tuple():
    profile = _profile(_current_md())
    answer = _format_yogini_dasha(profile)
    assert answer.sources == ("yogini",)
