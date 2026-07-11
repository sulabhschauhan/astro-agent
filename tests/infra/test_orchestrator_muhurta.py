"""End-to-end + router-provenance tests for muhurta_window's staged rollout
closing gate (Session 64, P7 Muhurta wiring): orchestrator.py's
_VALID_DOMAINS now admits "muhurta_window", closing chart_profile builder
(step 1) -> formatter (step 2) -> chart_profile dispatch (step 3) -> router
Stage 1/Stage 2 (step 4) -> orchestrator gate (step 5) -> this test file
(step 6). Adapts test_orchestrator_arudha_lagna.py / test_orchestrator_
upapada.py's 3-layer structure (read both end-to-end before writing this
file), with two domain-specific departures documented below.

WHY muhurta_window differs from the arudha_lagna/upapada_lagna precedent
(both purely-natal T1 domains):

1. WALL-CLOCK COUPLING. muhurta_window is the pipeline's FIRST domain
   where build_domain_profile()'s evaluated_at_jd is genuinely
   LOAD-BEARING (it is the muhurta scan window's own start_jd), not
   "accepted uniformly but genuinely unused" as it is for arudha/upapada/
   av_transit. Consequence for testing:
   - Layer B PINS a fixed JD (the S24 canonical anchor
     swe.julday(2026, 6, 20, 18.5) == 2026-06-20 18:30 UTC, the same
     anchor tests/calculations/transits/test_muhurta_windows.py uses) so
     window values are deterministic and cross-run stable.
   - Layer C calls answer_question(), which samples its OWN
     datetime.now(timezone.utc) for evaluated_at_jd -- so Layer C's window
     boundaries are wall-clock-dependent and CANNOT be byte-compared
     against Layer B's pinned-JD output (unlike arudha/upapada, whose
     Layer C asserts full byte-equality against Layer B). Layer C here is
     STRUCTURAL ONLY by design -- see TestLayerCFullChain's docstring.

2. TIER. muhurta_window resolves TIER_3_MUHURTA (per-window Chandrabala/
   Tarabala/Panchaka composite), the first and only T3 domain -- not
   TIER_1_EXACT like arudha/upapada. Its answer_payload is a windows list
   + summary block, not a flat 4-key natal dict.

MEASURE-FIRST FINDING (reported in diagnostics/latest_run.md before any
assertion was written, per CLAUDE.md Working Style #2/#3):
_MUHURTA_WINDOW_KEYWORDS (calc_router.py) has 5 entries -- "muhurta",
"mahurat", "auspicious", "shubh", "electional" -- under the same
`min(matched_keywords, 3) / 3` saturating formula
test_orchestrator_arudha_lagna.py's own docstring documents. Both
candidate phrasings measured directly against route_question() BEFORE
writing any Layer A test:

    "what is an auspicious muhurta for me this week"
        -> muhurta_window score 0.667 (2 keyword hits: "auspicious" +
           "muhurta"), tier TIER_3_MUHURTA, route "stage1", sentinel
           NEVER invoked (Stage 1 alone)
    "muhurta"
        -> muhurta_window score 0.333 (only the bare "muhurta" token),
           below _CONFIDENCE_FLOOR (0.4) -> route_question enters the
           Stage 2 fallback path -> REFUSAL

LAYER A SINGLE-KEYWORD SEAM -- deliberate DEPARTURE from arudha/upapada's
own Layer A a2 (S50 P7.2e lesson, called out explicitly in this step's
task): arudha/upapada assert the below-floor case by passing a
_RecordingClient as _stage2_client and checking the client recorded 1
call. That relies on _stage2_fallback's own fail-closed except-Exception
NOT eating the recording before it lands -- it happens to work because
the record is appended before the sentinel raises, but it couples the
assertion to _stage2_classify's internal client-call shape. Here we
instead monkeypatch _stage2_fallback ITSELF and assert it was called:
this proves "fell below floor -> Stage 2 fallback path entered" directly
at route_question()'s own branch, WITHOUT depending on the fail-closed
swallow inside _stage2_classify (which, per the task's S50 P7.2e note,
would swallow the signal if we patched _stage2_classify instead). No
real OpenAI call is ever made -- the spy returns a canned REFUSAL and
never delegates to the real fallback.

Layer C's "recording sentinel" is NOT route_question's `_stage2_client`
kwarg -- same reasoning as test_orchestrator_arudha_lagna.py's own module
docstring: orchestrator.py's answer_question() never accepts or threads
that kwarg through to route_question(). The correct seam for a full-chain
spy is monkeypatching calc_router._stage2_classify directly (module-level
function, called only from _stage2_fallback): for a Stage-1-clean
phrasing (this file's whole point) it is never reached, and patching it
to raise both proves non-invocation AND guarantees no accidental live
OpenAI call if a regression ever let Stage 1 fall through.
"""
from __future__ import annotations

import pytest
import swisseph as swe

from agent.infra import calc_router
from agent.infra.calc_router import RouteResult, route_question
from agent.infra.chart_profile import AnswerTier, build_domain_profile
from agent.infra.orchestrator import answer_question
from agent.infra.result_formatter import format_answer

# Stage-1-clean phrasing (2 keyword hits: "auspicious" + "muhurta"),
# ratified by direct measurement against route_question() -- see module
# docstring. Scores 0.667, clears both _CONFIDENCE_FLOOR (0.4) and
# _CONFIDENCE_MARGIN (0.15) against every other domain's 0.0.
_STAGE1_CLEAN_QUESTION = "what is an auspicious muhurta for me this week"

# Bare single-keyword phrasing -- scores 0.333, below _CONFIDENCE_FLOOR
# (only "muhurta" matches). Pins the below-floor -> Stage-2-fallback path.
_STAGE1_MISS_QUESTION = "muhurta"

# S24 canonical anchor, 2026-06-20 18:30 UTC -- identical to
# tests/calculations/transits/test_muhurta_windows.py's own
# _JD_UT_20260620_1830_UTC. Pins Layer B's scan window so its output is
# deterministic and cross-run stable despite muhurta being wall-clock-
# coupled in the live path (Layer C).
_PINNED_JD = swe.julday(2026, 6, 20, 18.5)
_SCAN_SPAN_DAYS = 7.0  # chart_profile._MUHURTA_SCAN_WINDOW_DAYS (V1 fixed window)

# MuhurtaTier value-strings (result_formatter renders MuhurtaTier.value,
# NOT AnswerTier) -- the per-window "tier" field's valid domain.
_VALID_TIER_VALUES = {"TIER_1", "TIER_2", "TIER_3"}

_SUMMARY_KEYS = {"tier1_window_count", "earliest_tier1_start"}

# Sulabh natal identifiers -- (natal_moon_sign, janma_nakshatra) =
# (7, 15) = Scorpio/Vishakha, the S27 canonical values (also asserted in
# tests/calculations/transits/test_muhurta_windows.py). Explicitly asserted
# in Layer B below, closing step 1's own verify-at-e2e obligation on the
# lagna_chart key semantics.
_SULABH_NATAL = (7, 15)


# ─── Fixtures (mirrors test_orchestrator_arudha_lagna.py's own style) ──────


@pytest.fixture(scope="module")
def sulabh_chart():
    from agent.chart_calculator import calculate_chart
    return calculate_chart("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")


@pytest.fixture(scope="module")
def surbhi_chart():
    from agent.chart_calculator import calculate_chart
    return calculate_chart("Surbhi", "11 Sep 1992", "10:30", "Patna, India")


@pytest.fixture(scope="module")
def sheridan_chart():
    from agent.chart_calculator import calculate_chart
    return calculate_chart("Sheridan", "27 May 1984", "08:00", "Durban, South Africa")


@pytest.fixture(scope="module")
def david_chart():
    from agent.chart_calculator import calculate_chart
    return calculate_chart("David", "19 Jan 1976", "22:00", "London, UK")


# ─── Recording sentinel (Layer A a1) ────────────────────────────────────────
# Mirrors test_orchestrator_arudha_lagna.py's own _RecordingCompletions/
# _RecordingClient pattern (records every call in `.calls`, raises a canned
# exception) -- duplicated rather than imported, per this project's
# per-test-file self-containment convention.


class _RecordingCompletions:
    def __init__(self):
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        raise RuntimeError("sentinel: stage2 should not have been reached")


class _RecordingClient:
    """Records every `.chat.completions.create()` call, then raises --
    proves non-invocation via `.completions.calls == []` directly (not by
    inferring it from the absence of a crash)."""

    def __init__(self):
        self.completions = _RecordingCompletions()
        self.chat = type("_FakeChat", (), {"completions": self.completions})()


# ─── Shared structural asserter ─────────────────────────────────────────────


def _natal_ids(chart: dict) -> tuple[int, int]:
    """(natal_moon_sign, janma_nakshatra) derived from chart the SAME way
    chart_profile.build_muhurta_profile() derives them -- off lagna_chart's
    "rasi"/"nakshatra" keys (which hold the MOON's sign/nakshatra, not the
    Ascendant's; see chart_profile.py's _koota_natal_info_from_chart
    docstring for the original documented precedent this reuses)."""
    from agent.chart_calculator import SIGNS, NAKSHATRAS
    lagna = chart["lagna_chart"]
    return SIGNS.index(lagna["rasi"]), NAKSHATRAS.index(lagna["nakshatra"])


def _assert_window_structure(payload: dict, *, expected_start_jd: float | None, exact_span: bool) -> None:
    """Structural invariants that hold for ANY chart/JD (no chart-specific
    values pinned here -- window count and per-window tier SEQUENCE are
    deferred value-asserts, see this file's Layer B docstring). Shared by
    Layer B (pinned JD -> expected_start_jd set, exact_span=True) and Layer
    C (wall-clock -> expected_start_jd None, exact_span=False)."""
    windows = payload["windows"]
    assert windows, "windows must be non-empty"

    # first/last coverage -- find_muhurta_windows()'s own contract
    # guarantees windows[0].start_jd == scan start and windows[-1].end_jd ==
    # scan end; with a pinned start we can assert both exactly.
    if expected_start_jd is not None:
        assert windows[0]["start_jd"] == expected_start_jd
        assert windows[-1]["end_jd"] == expected_start_jd + _SCAN_SPAN_DAYS

    # contiguity: no gaps, no overlaps
    for i in range(len(windows) - 1):
        assert windows[i]["end_jd"] == windows[i + 1]["start_jd"], (
            f"gap/overlap at index {i}: {windows[i]['end_jd']} != "
            f"{windows[i + 1]['start_jd']}"
        )

    # per-window: non-zero-width, ascending, valid tier value-string
    for w in windows:
        assert w["start_jd"] < w["end_jd"], f"zero-width window at {w['start_jd']}"
        assert w["tier"] in _VALID_TIER_VALUES, f"invalid tier {w['tier']!r}"

    # total span == the V1 fixed 7-day window
    total_span = windows[-1]["end_jd"] - windows[0]["start_jd"]
    if exact_span:
        assert total_span == _SCAN_SPAN_DAYS
    else:
        assert abs(total_span - _SCAN_SPAN_DAYS) < 1e-6

    # summary block keys present (values are chart/JD-specific -> deferred)
    assert set(payload["summary"].keys()) == _SUMMARY_KEYS


# ─── Layer A: router provenance ─────────────────────────────────────────────


class TestLayerARouterProvenance:
    def test_a1_stage1_clean_phrasing_never_touches_stage2(self):
        client = _RecordingClient()
        result = route_question(_STAGE1_CLEAN_QUESTION, _stage2_client=client)

        assert client.completions.calls == []  # sentinel NEVER invoked
        assert result.domain == "muhurta_window"
        assert result.tier == AnswerTier.TIER_3_MUHURTA
        assert result.confidence == pytest.approx(2 / 3)  # 2 keyword hits, min(2,3)/3
        assert result.route == "stage1"
        assert result.demotion_reason is None
        assert result.requires_partner is False

    def test_a2_single_keyword_enters_stage2_fallback(self, monkeypatch):
        """Below-floor single-keyword phrasing -> route_question enters the
        Stage 2 fallback path. Asserts by monkeypatching _stage2_fallback
        ITSELF (NOT _stage2_classify -- S50 P7.2e: _stage2_classify's own
        fail-closed except-Exception would swallow the signal; see this
        file's module docstring for the full rationale). The spy returns a
        canned REFUSAL and never delegates, so no real OpenAI call is made.
        """
        calls: list[tuple] = []
        canned = RouteResult(
            domain=None,
            tier=AnswerTier.REFUSAL,
            confidence=0.0,
            demotion_reason="question not classifiable with confidence",
            requires_partner=False,
            route="stage2",
        )

        def _spy_fallback(question, best_score, margin, has_partner_data, chart_data, client):
            calls.append((question, best_score, margin))
            return canned

        monkeypatch.setattr(calc_router, "_stage2_fallback", _spy_fallback)

        result = route_question(_STAGE1_MISS_QUESTION)

        assert len(calls) == 1  # Stage 2 fallback path WAS entered
        assert result is canned  # route_question returned the fallback's result
        # pin WHY it fell through: best_score below the confidence floor
        assert calls[0][1] < calc_router._CONFIDENCE_FLOOR


# ─── Layer B: builder->formatter oracle, PINNED JD (router bypassed, no LLM) ─


class TestLayerBRealChartOracle:
    """PINNED JD makes window values deterministic. Sulabh (hardest case --
    both Janma Tara and Janma Rashi warning paths fire) gets a FULL value
    pin: window count, per-window tier sequence, per-window favorable_count
    sequence, per-window warnings bands, and the summary block. The other 3
    charts get light pins (natal ids + tier1_window_count only), per
    sample-before-scale -- see _assert_chart_structural's own docstring for
    why their window-level detail stays unasserted.

    Table ratified S64 design chat (diagnostics/latest_run.md's "Sulabh
    full window table @ _PINNED_JD" MEASURE-FIRST block). The Janma Tara
    band boundaries (idx 7-8) are independently corroborated by S24's
    Vishakha occupancy scan (verbatim minute match against that scan's own
    output) -- not a fresh, unverified observation.
    """

    # Per-window tier SEQUENCE, Sulabh @ _PINNED_JD (11 windows) -- ratified
    # S64 design chat against diagnostics/latest_run.md's MEASURE-FIRST table.
    _SULABH_TIER_SEQUENCE = [
        "TIER_2", "TIER_1", "TIER_1", "TIER_2", "TIER_1", "TIER_2",
        "TIER_2", "TIER_3", "TIER_2", "TIER_1", "TIER_2",
    ]

    # Per-window favorable_count SEQUENCE, same table/anchor.
    _SULABH_FAVORABLE_COUNT_SEQUENCE = [1, 2, 2, 1, 2, 1, 1, 0, 1, 2, 1]

    # Per-window warnings bands, same table/anchor. idx 7 = Janma Tara only
    # (Vishakha nakshatra occupancy); idx 8 = both bands overlapping (the
    # only window where Janma Tara and Janma Rashi coincide); idx 9-10 =
    # Janma Rashi only (Scorpio moon-sign occupancy persists past the
    # nakshatra band). All other windows clear of both natal warnings.
    _SULABH_WARNINGS_SEQUENCE = {
        7: ("Janma Tara",),
        8: ("Janma Tara", "Janma Rashi"),
        9: ("Janma Rashi",),
        10: ("Janma Rashi",),
    }

    _SULABH_SUMMARY = {
        "tier1_window_count": 4,
        "earliest_tier1_start": "21 Jun 2026 04:01 UTC",
    }

    def test_sulabh_structural_and_natal_ids(self, sulabh_chart):
        """Hardest-case-first: Sulabh has BOTH Janma Rashi (Scorpio) and
        Janma Nakshatra (Vishakha) landing inside the scan window (both
        warning paths exercised in the observed table). Natal ids asserted
        == (7, 15), closing step 1's verify-at-e2e obligation on lagna_chart
        key semantics."""
        assert _natal_ids(sulabh_chart) == _SULABH_NATAL

        profile = build_domain_profile("muhurta_window", sulabh_chart, _PINNED_JD)
        answer = format_answer(profile)

        assert answer.domain == "muhurta_window"
        assert answer.tier == AnswerTier.TIER_3_MUHURTA
        assert answer.demotion_reason is None
        assert answer.sources == ("muhurta_scorer.py",)
        assert answer.stub_caveats == ()
        assert answer.uncertainty_virupa == 0.0
        assert answer.uncertainty_days == 0.0
        _assert_window_structure(
            answer.answer_payload, expected_start_jd=_PINNED_JD, exact_span=True
        )

        windows = answer.answer_payload["windows"]
        assert len(windows) == 11
        assert [w["tier"] for w in windows] == self._SULABH_TIER_SEQUENCE
        assert [w["favorable_count"] for w in windows] == self._SULABH_FAVORABLE_COUNT_SEQUENCE
        for i, w in enumerate(windows):
            # warnings is a tuple[str, ...] end to end (muhurta_scorer.py's
            # MuhurtaWindowScore dataclass field -> chart_profile.py's
            # build_muhurta_profile() passthrough -> result_formatter.py's
            # passthrough; verified by reading, not assumed) -- compare
            # against tuple literals, never list literals.
            assert w["warnings"] == self._SULABH_WARNINGS_SEQUENCE.get(i, ())
        assert answer.answer_payload["summary"] == self._SULABH_SUMMARY

    def _assert_chart_structural(self, chart: dict, *, expected_natal: tuple[int, int], expected_tier1_count: int):
        """Shared light-pin row for the 3 non-Sulabh charts: exact natal ids
        plus tier1_window_count, alongside the same pinned-JD window-
        structure invariants. Window COUNT==11 is observed at this anchor
        for all 4 charts (see diagnostics/latest_run.md), but that is a
        coincidence of this week's transit boundary structure -- NOT an
        invariant -- so it is deliberately NOT asserted here for the non-
        Sulabh charts (Sulabh alone gets the full-table pin above). Full
        per-window tier/favorable_count/warnings sequences stay unasserted
        for these 3 per sample-before-scale."""
        assert _natal_ids(chart) == expected_natal

        profile = build_domain_profile("muhurta_window", chart, _PINNED_JD)
        answer = format_answer(profile)

        assert answer.domain == "muhurta_window"
        assert answer.tier == AnswerTier.TIER_3_MUHURTA
        _assert_window_structure(
            answer.answer_payload, expected_start_jd=_PINNED_JD, exact_span=True
        )
        assert answer.answer_payload["summary"]["tier1_window_count"] == expected_tier1_count

    def test_david_structural(self, david_chart):
        """David tested first among the 3 partial-assert rows per CLAUDE.md
        Working Style #3 (HARDEST CASE first), mirroring the arudha/upapada
        precedent's own ordering."""
        self._assert_chart_structural(david_chart, expected_natal=(4, 9), expected_tier1_count=2)

    def test_surbhi_structural(self, surbhi_chart):
        self._assert_chart_structural(surbhi_chart, expected_natal=(10, 23), expected_tier1_count=3)

    def test_sheridan_structural(self, sheridan_chart):
        self._assert_chart_structural(sheridan_chart, expected_natal=(0, 0), expected_tier1_count=2)


# ─── Layer C: full answer_question() chain, STRUCTURAL (router incl., no LLM) ─


class TestLayerCFullChain:
    def test_sulabh_full_chain_structural(self, sulabh_chart, monkeypatch):
        """STRUCTURAL, not byte-equal against Layer B -- BY DESIGN:
        answer_question() samples its OWN datetime.now(timezone.utc) for
        evaluated_at_jd (muhurta_window is the first wall-clock-anchored
        domain -- see module docstring), so its scan window starts at "now",
        not at Layer B's _PINNED_JD. The two window lists therefore cannot be
        byte-compared (unlike arudha/upapada's Layer C, which asserts full
        equality). Only the invariants that hold for ANY start instant are
        checked here: domain/tier/route/demotion/sources/stub_caveats, plus
        the shared window-structure asserter (non-empty, contiguous,
        ascending, span 7.0 +/- 1e-6, every per-window tier valid, summary
        keys present).

        Recording sentinel: monkeypatches calc_router._stage2_classify to
        raise (see module docstring for why this, not route_question's
        _stage2_client kwarg, is the correct full-chain seam) -- proves
        Stage 2 never fires for the Stage-1-clean phrasing AND guarantees no
        accidental live OpenAI call.
        """
        def _spy_stage2_classify(question, client=None):
            raise AssertionError(
                "stage2 must not fire for a Stage-1-clean muhurta_window phrasing"
            )

        monkeypatch.setattr(calc_router, "_stage2_classify", _spy_stage2_classify)

        result = answer_question(_STAGE1_CLEAN_QUESTION, sulabh_chart)

        assert result.domain == "muhurta_window"
        assert result.tier == AnswerTier.TIER_3_MUHURTA
        assert result.route == "stage1"
        assert result.demotion_reason is None
        assert result.sources == ("muhurta_scorer.py",)
        assert result.stub_caveats == ()
        assert result.uncertainty_virupa == 0.0
        assert result.uncertainty_days == 0.0
        _assert_window_structure(
            result.answer_payload, expected_start_jd=None, exact_span=False
        )
