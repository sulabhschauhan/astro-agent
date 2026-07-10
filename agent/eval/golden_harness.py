"""P7.0 golden-set eval harness -- read-only scorecard runner (Session 49).

Drives every RUNNABLE row of tests/fixtures/golden_qa_sulabh.py's GOLDEN_QA
ledger through the real agent.infra.orchestrator.answer_question() pipeline
and writes a markdown scorecard to diagnostics/. No LLM calls, no network,
no mutation of golden data -- this module only reads GOLDEN_QA and calls the
already-built deterministic pipeline (CLAUDE.md V1 scope: LLM-generated
interpretive Q&A is OUT; this harness never invokes one).

Runnability: a row is RUNNABLE when it is a single question against the
sulabh chart in one of the four pipeline-whitelisted domains
(career/marriage/dasha/arudha_lagna). Rows batching multiple probes under
domain == "refusal_probe" (the R1-R5 / QUEST1-QUEST2 bundles) are
NON_RUNNABLE_BATCH -- listed in the report, never executed, per the task
spec for this session.

Per-row category (checked in this order -- MATCH first, NON_RUNNABLE_BATCH
rows never reach this classification at all):
  MATCH              -- actual tier equals the golden row's expected_tier,
                        AND route (see below) was "stage1" or "fastpath"
                        -- the deterministic regression floor.
  MATCH_STAGE2        -- actual tier equals expected_tier, but route was
                        "stage2": a live GPT-4o-mini call resolved this
                        row. Correct this run, but LLM-dependent --
                        monitored, not asserted, same variance posture as
                        a STAGE2_VARIABLE KNOWN_GAP row (see _KNOWN_GAPS).
  DESIGN_DEBT        -- mismatch caused by a genuine, un-locked product gap
                        (a built/validated module excluded from the Q&A
                        whitelist) -- seeded in _DESIGN_DEBT, pending a
                        design-chat decision, NOT a documented lock.
  KNOWN_GAP          -- mismatch that traces to an actual CLAUDE.md-cited
                        locked decision -- seeded in _KNOWN_GAPS.
  NEW_GAP            -- mismatch with no seeded explanation; this is the
                        scorecard's real signal and the only category that
                        should worry a reviewer.
  NON_RUNNABLE_BATCH -- multi-probe row, never executed (see above).
  (ERROR is a fifth, orthogonal outcome: the row's answer_question() call
  raised -- reported instead of any of the above.)

Session 55 (route-provenance): every executed row also records `route`
("stage1" | "stage2" | "fastpath") -- which of calc_router.py's paths
actually resolved it. This makes the harness's own output natively
reproduce the route-provenance distinction that
diagnostics/golden_scorecard_20260707_091459_post_av_transit.md carried
as a HAND-annotated overlay (cross-referencing calc_router_stage2.log by
hand against that run's per-row questions) -- that file's own root-cause
note already acknowledged this was manual, ahead of this change: the
harness's built-in MATCH/KNOWN_GAP categories don't distinguish Stage 1
(deterministic keyword scoring) from Stage 2 (live, nondeterministic
GPT-4o-mini fallback) when both can independently resolve a question to
the same correct domain (Session 50/P7.1e's own comment on _KNOWN_GAPS
notes exactly this for q1/q2/q3/q7/q8). `route` is derived by
correlating diagnostics/calc_router_stage2.log (see
`_used_stage2_since()`'s own docstring for why this is a fragile,
best-effort correlation, not a first-class run identifier) -- RouteResult
itself (agent/infra/calc_router.py) carries no route marker of its own
(confirmed by reading its dataclass fields: domain, tier, confidence,
demotion_reason, requires_partner -- nothing else), so there is no
stronger signal available without modifying calc_router.py, which this
change deliberately does not do (golden_harness.py is the ONLY file
Session 55 touches here).

evaluated_at_jd is an explicit, caller-suppliable parameter of
run_golden_eval() recording WHEN this run happened, for the report header.
It is deliberately NOT threaded into answer_question(): that function has no
evaluated_at_jd parameter (orchestrator.py computes its own
swe.julday(datetime.now(timezone.utc)) internally per-call, same as any
other caller), so per-row dasha timing reflects the actual moment each call
executes, not this header value. The header value exists purely so a
scorecard file is self-describing about when its (time-sensitive, dasha-
dependent) results were captured.
"""

from __future__ import annotations

import dataclasses
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import swisseph as swe

from agent.chart_calculator import calculate_chart
from agent.infra import calc_router
from agent.infra.orchestrator import answer_question
from tests.fixtures.golden_qa_sulabh import GOLDEN_QA

# ─── Baseline reference (CLAUDE.md "Current Session Focus", Session 45 ────
# checkpoint close) -- the full project pytest suite's pass count at the
# point this golden-set harness was built. Recorded in the report header for
# scale context against the golden-set row count; not re-derived by running
# the full suite here (this harness is read-only and Q&A-pipeline-scoped).
_BASELINE_TEST_COUNT = 1769

# Golden-set domain string -> pipeline domain string (calc_router.py /
# chart_profile.py's 4-domain whitelist).
_GOLDEN_DOMAIN_TO_PIPELINE_DOMAIN: dict[str, str] = {
    "career": "career_strength",
    "marriage": "marriage_compatibility",
    "dasha": "current_dasha",
    "arudha_lagna": "arudha_lagna",
}

# Canonical, verified chart-construction data (see tests/infra/test_orchestrator_e2e.py
# fixtures) -- Sulabh is every RUNNABLE row's primary native; Surbhi is the
# fixed partner chart for marriage rows (primary_role="boy" per the task's
# behavioral contract).
_SULABH_BIRTH = ("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")
_SURBHI_BIRTH = ("Surbhi", "11 Sep 1992", "10:30", "Patna, India")

# Mismatches this harness has ACTUALLY reproduced on a real run, each tracing
# to a documented CLAUDE.md lock rather than a pipeline defect -- i.e. the
# pipeline is doing exactly what a locked decision says it should. Seeded
# only from observed output (confirmed via a direct route_question()/answer_
# question() run, not guessed) -- never speculatively. Extending this dict
# is a design-chat decision, not something this harness does on its own.
# Contrast with _DESIGN_DEBT below: KNOWN_GAP means "working as locked",
# DESIGN_DEBT means "not locked, a real gap, just not THIS session's fix".
#
# Session 50/P7.1e: q1/q2/q3/q7/q8 deleted from this dict. Stage 2
# (calc_router.py's GPT-4o-mini constrained-classification fallback,
# Session 49+/P7.1) now classifies all 5 at confidence="high" and routes
# them to the correct domain -- verified MATCH in
# diagnostics/golden_scorecard_20260705_075932.md before this deletion.
# Deletion is behavior-neutral: _run_runnable_row only consults this dict
# when actual_tier != expected_tier (see below), so a MATCH row never
# reaches it whether or not an entry exists here.
#
# The 4 remaining entries are all STAGE2_VARIABLE (see each entry): their
# outcome now depends on a live GPT-4o-mini call, which -- unlike Stage 1's
# pure keyword arithmetic -- is not perfectly guaranteed identical across
# runs even at temperature=0. A category flip on one of these 4 rows in a
# future run is expected variance, not automatically a regression: check
# diagnostics/calc_router_stage2.log for that run before treating it as a
# NEW_GAP.
_KNOWN_GAPS: dict[str, str] = {
    "sulabh_career_q4": (
        "STAGE2_VARIABLE: outcome depends on live GPT-4o-mini "
        "classification; a category flip on this row across runs is "
        "expected variance, not automatically a regression -- check "
        "diagnostics/calc_router_stage2.log before treating as NEW_GAP. "
        "Session 50 observed mechanism: Stage 2 classified "
        "career_strength at confidence=\"medium\" -- calc_router routes "
        "ONLY on \"high\" confidence, so this REFUSES via the same "
        "generic path Stage 1 alone would have produced (\"job\" is the "
        "only Stage 1 career-keyword hit, itself below the 2-hit/0.4-floor "
        "requirement)."
    ),
    "sulabh_marriage_q9": (
        "STAGE2_VARIABLE: outcome depends on live GPT-4o-mini "
        "classification; a category flip on this row across runs is "
        "expected variance, not automatically a regression -- check "
        "diagnostics/calc_router_stage2.log before treating as NEW_GAP. "
        "Session 50 observed mechanism: Stage 2 classified "
        "marriage_compatibility at confidence=\"medium\" -- calc_router "
        "routes ONLY on \"high\" confidence, so this REFUSES via the same "
        "generic path Stage 1 alone would have produced (\"compatibility\" "
        "is the only Stage 1 marriage-keyword hit, itself below the "
        "2-hit/0.4-floor requirement)."
    ),
    # Two independent reasons this cannot MATCH -- one STAGE2_VARIABLE, one
    # a hard CLAUDE.md lock. Per this session's design-chat instruction: if
    # a future run's Stage 2 ever classifies this "high" and routes it to
    # marriage_compatibility, that is BENIGN, not a bug -- the koota data
    # layer still matches golden's verified claims. Only this entry's
    # "observed mechanism" sentence would need updating; the underlying
    # KNOWN_GAP conclusion (reason 2 below) is unaffected either way.
    "sulabh_marriage_q10": (
        "STAGE2_VARIABLE: outcome depends on live GPT-4o-mini "
        "classification; a category flip on this row across runs is "
        "expected variance, not automatically a regression -- check "
        "diagnostics/calc_router_stage2.log before treating as NEW_GAP. "
        "Session 50 observed mechanism (reason 1): Stage 2 classified "
        "marriage_compatibility at confidence=\"medium\" -> REFUSAL "
        "(\"compatibility\" is the only Stage 1 hit, below floor). If a "
        "future run's Stage 2 instead classifies \"high\" and routes to "
        "marriage_compatibility: BENIGN -- the koota data layer still "
        "matches golden's verified claims. Reason 2, independent of "
        "Stage 2 entirely: CLAUDE.md V1 scope lock (\"LLM-generated "
        "interpretive Q&A is OUT; AstroSage paragraph + palm are the "
        "interpretive surface\") means TIER_4_INTERPRETIVE is never "
        "produced by this pipeline regardless of routing outcome -- no "
        "amount of router/Stage-2 tuning fixes this row's tier mismatch."
    ),
    # CLAUDE.md "P2 order" lock: Muhurta engine exists (transits/chandrabala.py,
    # tarabala.py, panchaka.py per calc_router.py's own
    # _UNBUILT_MODULE_KEYWORDS["muhurta"] comment) but is "not wired to Q&A
    # in V1". TIER_3_MUHURTA is never produced by this pipeline regardless
    # of Stage 1 or Stage 2 routing outcome -- UNLIKE q10 above, a future
    # Stage 2 route here would NOT be benign (see entry below).
    "sulabh_dasha_q15": (
        "STAGE2_VARIABLE: outcome depends on live GPT-4o-mini "
        "classification; a category flip on this row across runs is "
        "expected variance, not automatically a regression -- check "
        "diagnostics/calc_router_stage2.log before treating as NEW_GAP. "
        "Session 50 observed mechanism: Stage 2 classified domain=\"none\" "
        "at confidence=\"high\" -> REFUSAL (Stage 1 scores zero keyword "
        "hits in all 3 whitelisted domains). Independently unreachable "
        "regardless: CLAUDE.md P2 order lock means TIER_3_MUHURTA is "
        "never produced by this pipeline. If a future run's Stage 2 ever "
        "routes this to current_dasha (high confidence): that IS a SOFT "
        "MISROUTE (a Muhurta-intent question answered as a dasha "
        "question) -- flag to design chat, do NOT silently accept it the "
        "way q10's koota-benign case is accepted above."
    ),
}

# Mismatches this harness has ACTUALLY reproduced that are genuine, un-locked
# product gaps -- distinct from _KNOWN_GAPS above, which is reserved for
# behavior a CLAUDE.md lock explicitly calls correct. A DESIGN_DEBT entry
# means "this is a real gap; it's just not this session's fix," pending an
# explicit design-chat whitelist/scope decision. Same seeding discipline as
# _KNOWN_GAPS: only rows this harness has actually observed, never guessed.
# Session 50/P7.2f: sulabh_dasha_q14 entry DELETED -- calc_router.py
# (P7.2c) + orchestrator.py (P7.2d) shipped the sade_sati domain end-to-
# end, and q14 now resolves MATCH (verified in
# diagnostics/golden_scorecard_20260705_085333.md before deleting;
# MATCH is checked before this dict, so the deletion is behavior-neutral).
# Empty for now -- kept (dict + category machinery) as the correct slot
# for the next genuine, un-locked product gap this harness observes.
_DESIGN_DEBT: dict[str, str] = {}

# NOTE (Session 55): the static stage2_dependent_rows note that used to be
# derived from this dict's keys (_STAGE2_DEPENDENT_ROW_IDS) has been
# replaced by a per-run COMPUTED split in _render_report() (deterministic-
# floor rows vs stage2-routed rows, by actual route-provenance) -- see the
# module docstring's Session 55 note. _KNOWN_GAPS itself is unchanged:
# still the seeded, hand-curated set of MISMATCHES this harness has
# actually observed and traced to a locked decision; still consulted only
# when actual_tier != expected_tier.


@dataclasses.dataclass(frozen=True)
class RowResult:
    """One golden-set row's outcome against the live pipeline."""

    id: str
    domain: str
    expected_tier: str
    actual: str                    # AnswerTier value string, or "ERROR", or "N/A (batch)"
    demotion_reason: str | None
    category: str                  # MATCH | MATCH_STAGE2 | DESIGN_DEBT | KNOWN_GAP | NEW_GAP | ERROR | NON_RUNNABLE_BATCH
    route: str                     # "stage1" | "stage2" | "fastpath" | "n/a" (NON_RUNNABLE_BATCH rows only)


@dataclasses.dataclass(frozen=True)
class GoldenEvalSummary:
    """Counts + report location returned by run_golden_eval()."""

    evaluated_at_jd: float
    baseline_test_count: int
    golden_row_count: int
    runnable_count: int
    non_runnable_batch_count: int
    match_count: int
    match_stage2_count: int
    design_debt_count: int
    known_gap_count: int
    new_gap_count: int
    error_count: int
    report_path: str
    rows: tuple[RowResult, ...]


def _default_evaluated_at_jd() -> float:
    now_utc = datetime.now(timezone.utc)
    hour_decimal = now_utc.hour + now_utc.minute / 60.0 + now_utc.second / 3600.0
    return swe.julday(now_utc.year, now_utc.month, now_utc.day, hour_decimal)


def _classify_runnability(row: dict[str, Any]) -> str:
    """RUNNABLE: single question, sulabh chart, in the 3-domain whitelist.
    NON_RUNNABLE_BATCH: multi-probe rows (domain == "refusal_probe").
    """
    if row["chart"] == "sulabh" and row["domain"] in _GOLDEN_DOMAIN_TO_PIPELINE_DOMAIN:
        return "RUNNABLE"
    return "NON_RUNNABLE_BATCH"


def _build_charts() -> tuple[dict, dict]:
    """Build Sulabh (primary, all rows) and Surbhi (marriage partner) once."""
    sulabh_chart = calculate_chart(*_SULABH_BIRTH)
    surbhi_chart = calculate_chart(*_SURBHI_BIRTH)
    return sulabh_chart, surbhi_chart


def _used_stage2_since(question: str, since: datetime) -> bool:
    """True if `question` triggered a live Stage 2 call at/after `since`.

    FRAGILE BY CONSTRUCTION -- read this before trusting it elsewhere.
    diagnostics/calc_router_stage2.log (calc_router._STAGE2_LOG_PATH) is a
    single shared, append-only JSONL file: every Stage 2 invocation ever
    logged by ANY caller lands here, including tests/infra/
    test_calc_router_stage2.py's fake-client tests (_log_stage2_invocation
    logs unconditionally, regardless of whether the client was a real
    OpenAI client or a test fake) and every prior run of this harness. The
    log schema itself carries no run ID to join against (fields are
    timestamp/question/stage1_best_score/stage1_margin/stage2_domain/
    stage2_confidence/outcome only -- confirmed by reading
    _log_stage2_invocation()) -- so this function correlates purely by (a)
    exact question-text match and (b) a timestamp >= `since`, a wall-clock
    cutoff the caller captures immediately before this run's first row
    executes. This is safe today only because: GOLDEN_QA's runnable-row
    question strings are all mutually unique and don't collide with the
    pytest suite's own fixture questions (verified by inspection); and a
    single golden_harness.py invocation runs its rows sequentially, so no
    concurrent process can append a same-text entry inside this run's own
    window. It would silently misattribute a row if either assumption
    ever broke (a new GOLDEN_QA row reusing existing question text, or a
    second process hitting Stage 2 with an identical question during this
    run). Prefer a real RouteResult-level route marker over this
    correlation if calc_router.py ever adds one (it does not today --
    confirmed by reading RouteResult's fields: domain, tier, confidence,
    demotion_reason, requires_partner).
    """
    log_path = calc_router._STAGE2_LOG_PATH
    if not log_path.exists():
        return False

    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("question") != question:
                continue
            if datetime.fromisoformat(record["timestamp"]) >= since:
                return True
    return False


def _run_runnable_row(
    row: dict[str, Any],
    sulabh_chart: dict,
    surbhi_chart: dict,
    run_start: datetime,
) -> RowResult:
    golden_domain = row["domain"]
    expected_tier = row["expected_tier"]
    question = row["question"]

    try:
        if golden_domain == "marriage":
            result = answer_question(
                question,
                sulabh_chart,
                partner_chart_data=surbhi_chart,
                primary_role="boy",
            )
        else:
            result = answer_question(question, sulabh_chart)
    except Exception as exc:  # noqa: BLE001 -- one row's crash must not abort the run
        route = "stage2" if _used_stage2_since(question, run_start) else "stage1"
        return RowResult(
            id=row["id"],
            domain=golden_domain,
            expected_tier=expected_tier,
            actual="ERROR",
            demotion_reason=f"{type(exc).__name__}: {exc}",
            category="ERROR",
            route=route,
        )

    # Route determination: Stage 2 log correlation first (authoritative
    # when present -- see _used_stage2_since()'s own fragility docstring),
    # then fastpath (sade_sati's _BUILT_MODULE_FASTPATH -- the ONLY domain
    # that bypasses Stage 1 scoring entirely today, per calc_router.py's
    # own module docstring; distinguished from a Stage-2-classified
    # "sade_sati" by the log check already having failed to match above),
    # else Stage 1 keyword scoring (including the pre-scoring unbuilt-
    # module/out-of-scope REFUSAL checks, which are still deterministic
    # keyword matching, not Stage 2).
    if _used_stage2_since(question, run_start):
        route = "stage2"
    elif result.domain == "sade_sati":
        route = "fastpath"
    else:
        route = "stage1"

    actual_tier = result.tier.value
    if actual_tier == expected_tier:
        category = "MATCH_STAGE2" if route == "stage2" else "MATCH"
    elif row["id"] in _DESIGN_DEBT:
        category = "DESIGN_DEBT"
    elif row["id"] in _KNOWN_GAPS:
        category = "KNOWN_GAP"
    else:
        category = "NEW_GAP"

    return RowResult(
        id=row["id"],
        domain=golden_domain,
        expected_tier=expected_tier,
        actual=actual_tier,
        demotion_reason=result.demotion_reason,
        category=category,
        route=route,
    )


def _non_runnable_row(row: dict[str, Any]) -> RowResult:
    return RowResult(
        id=row["id"],
        domain=row["domain"],
        expected_tier=row["expected_tier"],
        actual="N/A (batch, not executed)",
        demotion_reason=None,
        category="NON_RUNNABLE_BATCH",
        route="n/a",
    )


def _escape_md(cell: Any) -> str:
    text = "" if cell is None else str(cell)
    return text.replace("|", "\\|").replace("\n", " ")


def _render_report(
    evaluated_at_jd: float,
    rows: tuple[RowResult, ...],
    counts: dict[str, int],
) -> str:
    # Computed per-run (Session 55), replacing the old static
    # _STAGE2_DEPENDENT_ROW_IDS-derived note: split every executed
    # (non-NON_RUNNABLE_BATCH) row by its actual observed route this run,
    # not by a hand-maintained guess of which rows are "expected" to need
    # Stage 2.
    executed = [r for r in rows if r.category != "NON_RUNNABLE_BATCH"]
    deterministic_floor_ids = [r.id for r in executed if r.route in ("stage1", "fastpath")]
    stage2_routed_ids = [r.id for r in executed if r.route == "stage2"]

    lines: list[str] = []
    lines.append("# P7.0 Golden Q&A Scorecard (Session 49)")
    lines.append("")
    lines.append(f"- Run evaluated_at_jd: `{evaluated_at_jd}`")
    lines.append(f"- Baseline pytest suite count (CLAUDE.md checkpoint): {_BASELINE_TEST_COUNT}")
    lines.append(f"- Golden-set row count: {len(rows)}")
    lines.append(
        f"- deterministic_floor_rows ({len(deterministic_floor_ids)}, routed via "
        "Stage 1 keyword scoring or the sade_sati fastpath -- the "
        f"regression floor): {', '.join(deterministic_floor_ids)}"
    )
    lines.append(
        f"- stage2_routed_rows ({len(stage2_routed_ids)}, routed via a live "
        "GPT-4o-mini Stage 2 call this run -- monitored, not asserted; a "
        "category or actual-tier flip on one of these is expected "
        "variance, not automatically a regression -- check "
        f"diagnostics/calc_router_stage2.log before treating as NEW_GAP): "
        f"{', '.join(stage2_routed_ids)}"
    )
    lines.append("")
    lines.append("## Per-row results")
    lines.append("")
    lines.append("| id | domain | expected_tier | actual | route | demotion_reason | category |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in rows:
        lines.append(
            f"| {_escape_md(r.id)} | {_escape_md(r.domain)} | {_escape_md(r.expected_tier)} "
            f"| {_escape_md(r.actual)} | {_escape_md(r.route)} | {_escape_md(r.demotion_reason)} "
            f"| {_escape_md(r.category)} |"
        )
    lines.append("")
    lines.append("## Summary counts")
    lines.append("")
    for key in (
        "runnable",
        "non_runnable_batch",
        "match",
        "match_stage2",
        "design_debt",
        "known_gap",
        "new_gap",
        "error",
    ):
        lines.append(f"- {key}: {counts[key]}")
    lines.append("")
    return "\n".join(lines)


def run_golden_eval(
    evaluated_at_jd: float | None = None,
    output_dir: str | Path = "diagnostics",
) -> GoldenEvalSummary:
    """Run every RUNNABLE GOLDEN_QA row through the live pipeline once.

    Args:
        evaluated_at_jd: JD (UT) recorded in the report header as "when this
            run happened". Caller-supplied per locked architecture; defaults
            to the JD of the actual run moment. NOT passed into
            answer_question() -- see module docstring.
        output_dir: directory the markdown scorecard is written into.

    Returns:
        GoldenEvalSummary with per-category counts and the report path.
    """
    if evaluated_at_jd is None:
        evaluated_at_jd = _default_evaluated_at_jd()

    # Captured before any row executes -- the cutoff _used_stage2_since()
    # uses to scope its (fragile, question-text-keyed) correlation against
    # diagnostics/calc_router_stage2.log to THIS run only.
    run_start = datetime.now(timezone.utc)

    sulabh_chart, surbhi_chart = _build_charts()

    rows: list[RowResult] = []
    for row in GOLDEN_QA:
        if _classify_runnability(row) == "RUNNABLE":
            rows.append(_run_runnable_row(row, sulabh_chart, surbhi_chart, run_start))
        else:
            rows.append(_non_runnable_row(row))

    counts = {
        "runnable": sum(1 for r in rows if r.category != "NON_RUNNABLE_BATCH"),
        "non_runnable_batch": sum(1 for r in rows if r.category == "NON_RUNNABLE_BATCH"),
        "match": sum(1 for r in rows if r.category == "MATCH"),
        "match_stage2": sum(1 for r in rows if r.category == "MATCH_STAGE2"),
        "design_debt": sum(1 for r in rows if r.category == "DESIGN_DEBT"),
        "known_gap": sum(1 for r in rows if r.category == "KNOWN_GAP"),
        "new_gap": sum(1 for r in rows if r.category == "NEW_GAP"),
        "error": sum(1 for r in rows if r.category == "ERROR"),
    }

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_path = out_dir / f"golden_scorecard_{timestamp}.md"
    report_path.write_text(_render_report(evaluated_at_jd, tuple(rows), counts), encoding="utf-8")

    return GoldenEvalSummary(
        evaluated_at_jd=evaluated_at_jd,
        baseline_test_count=_BASELINE_TEST_COUNT,
        golden_row_count=len(GOLDEN_QA),
        runnable_count=counts["runnable"],
        non_runnable_batch_count=counts["non_runnable_batch"],
        match_count=counts["match"],
        match_stage2_count=counts["match_stage2"],
        design_debt_count=counts["design_debt"],
        known_gap_count=counts["known_gap"],
        new_gap_count=counts["new_gap"],
        error_count=counts["error"],
        report_path=str(report_path),
        rows=tuple(rows),
    )


if __name__ == "__main__":
    summary = run_golden_eval()
    print(
        f"runnable={summary.runnable_count} non_runnable_batch={summary.non_runnable_batch_count} "
        f"match={summary.match_count} match_stage2={summary.match_stage2_count} "
        f"design_debt={summary.design_debt_count} "
        f"known_gap={summary.known_gap_count} new_gap={summary.new_gap_count} "
        f"error={summary.error_count}"
    )
    print(f"report: {summary.report_path}")
