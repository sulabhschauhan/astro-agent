"""P7.0 golden-set eval harness -- read-only scorecard runner (Session 49).

Drives every RUNNABLE row of tests/fixtures/golden_qa_sulabh.py's GOLDEN_QA
ledger through the real agent.infra.orchestrator.answer_question() pipeline
and writes a markdown scorecard to diagnostics/. No LLM calls, no network,
no mutation of golden data -- this module only reads GOLDEN_QA and calls the
already-built deterministic pipeline (CLAUDE.md V1 scope: LLM-generated
interpretive Q&A is OUT; this harness never invokes one).

Runnability: a row is RUNNABLE when it is a single question against the
sulabh chart in one of the three pipeline-whitelisted domains
(career/marriage/dasha). Rows batching multiple probes under
domain == "refusal_probe" (the R1-R5 / QUEST1-QUEST2 bundles) are
NON_RUNNABLE_BATCH -- listed in the report, never executed, per the task
spec for this session.

Per-row category (checked in this order -- MATCH first, NON_RUNNABLE_BATCH
rows never reach this classification at all):
  MATCH              -- actual tier equals the golden row's expected_tier.
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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import swisseph as swe

from agent.chart_calculator import calculate_chart
from agent.infra.orchestrator import answer_question
from tests.fixtures.golden_qa_sulabh import GOLDEN_QA

# ─── Baseline reference (CLAUDE.md "Current Session Focus", Session 45 ────
# checkpoint close) -- the full project pytest suite's pass count at the
# point this golden-set harness was built. Recorded in the report header for
# scale context against the golden-set row count; not re-derived by running
# the full suite here (this harness is read-only and Q&A-pipeline-scoped).
_BASELINE_TEST_COUNT = 1769

# Golden-set domain string -> pipeline domain string (calc_router.py /
# chart_profile.py's 3-domain whitelist).
_GOLDEN_DOMAIN_TO_PIPELINE_DOMAIN: dict[str, str] = {
    "career": "career_strength",
    "marriage": "marriage_compatibility",
    "dasha": "current_dasha",
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
_KNOWN_GAPS: dict[str, str] = {
    # CLAUDE.md "Router refuse-heavy posture" lock: calc_router.py requires
    # >=2 keyword hits to route any domain (0.4 floor); single- (or zero-)
    # keyword questions are REFUSED BY DESIGN. This is the lock's own named
    # example ("career potential" -> 1 hit -> refused).
    "sulabh_career_q1": (
        "Router refuse-heavy posture (CLAUDE.md Locked Decisions): scores "
        "a single career keyword hit (\"career\"), below the 2-hit/0.4-floor "
        "requirement -- REFUSED BY DESIGN, the lock's own named example."
    ),
    # Same mechanism as q1, different wording: "profession" is the only
    # career-keyword hit.
    "sulabh_career_q2": (
        "Router refuse-heavy posture (CLAUDE.md Locked Decisions): scores "
        "a single career keyword hit (\"profession\"), below the "
        "2-hit/0.4-floor requirement -- REFUSED BY DESIGN, same mechanism "
        "as the lock's named q1 example."
    ),
    # Same mechanism as q1: "10th house" is the only career-keyword hit.
    "sulabh_career_q3": (
        "Router refuse-heavy posture (CLAUDE.md Locked Decisions): scores "
        "a single career keyword hit (\"10th house\"), below the "
        "2-hit/0.4-floor requirement -- REFUSED BY DESIGN, same mechanism "
        "as the lock's named q1 example."
    ),
    # Same mechanism as q1: "job" is the only career-keyword hit (the
    # additive job->career _STEM_MAP expansion does not add a second
    # DISTINCT keyword-list hit -- "career" itself is not a literal token
    # here, only "job" matches a keyword-list entry).
    "sulabh_career_q4": (
        "Router refuse-heavy posture (CLAUDE.md Locked Decisions): scores "
        "a single career keyword hit (\"job\"), below the 2-hit/0.4-floor "
        "requirement -- REFUSED BY DESIGN, same mechanism as the lock's "
        "named q1 example."
    ),
    # Same mechanism as q1, marriage domain: "mangal dosha" is the only
    # marriage-keyword hit.
    "sulabh_marriage_q7": (
        "Router refuse-heavy posture (CLAUDE.md Locked Decisions): scores "
        "a single marriage keyword hit (\"mangal dosha\"), below the "
        "2-hit/0.4-floor requirement -- REFUSED BY DESIGN, same mechanism "
        "as the lock's named q1 example."
    ),
    # Same mechanism as q1, marriage domain, zero-hit case: no marriage/
    # career/dasha keyword-list entry appears in this question at all
    # ("nadi dosha" is not in _MARRIAGE_KEYWORDS).
    "sulabh_marriage_q8": (
        "Router refuse-heavy posture (CLAUDE.md Locked Decisions): scores "
        "zero keyword hits in any domain -- REFUSED BY DESIGN (a fortiori "
        "the same 2-hit-floor mechanism as the lock's named q1 example)."
    ),
    # Same mechanism as q1, marriage domain: "compatibility" is the only
    # marriage-keyword hit.
    "sulabh_marriage_q9": (
        "Router refuse-heavy posture (CLAUDE.md Locked Decisions): scores "
        "a single marriage keyword hit (\"compatibility\"), below the "
        "2-hit/0.4-floor requirement -- REFUSED BY DESIGN, same mechanism "
        "as the lock's named q1 example."
    ),
    # Two independent, both-documented reasons this cannot MATCH: (1) same
    # router refuse-heavy mechanism as q1 (single hit, "compatibility");
    # (2) CLAUDE.md "V1 scope" lock -- TIER_4_INTERPRETIVE ("LLM-generated
    # interpretive Q&A is OUT for V1") is never produced by this pipeline
    # regardless of routing outcome, so no router tuning could ever make
    # this row MATCH.
    "sulabh_marriage_q10": (
        "Router refuse-heavy posture (CLAUDE.md Locked Decisions): scores "
        "a single marriage keyword hit (\"compatibility\") -- REFUSED BY "
        "DESIGN. Independently also unreachable under the V1 scope lock "
        "(\"LLM-generated interpretive Q&A is OUT; AstroSage paragraph + "
        "palm are the interpretive surface\"): TIER_4_INTERPRETIVE is never "
        "produced by this pipeline, so no amount of router tuning fixes "
        "this row."
    ),
    # CLAUDE.md "P2 order" lock: Muhurta engine exists (transits/chandrabala.py,
    # tarabala.py, panchaka.py per calc_router.py's own
    # _UNBUILT_MODULE_KEYWORDS["muhurta"] comment) but is "not wired to Q&A
    # in V1". TIER_3_MUHURTA is never produced by this pipeline -- this
    # question actually scores zero keyword hits in all 3 whitelisted
    # domains and is refused via the generic confidence-floor path, not via
    # the muhurta keyword trigger, but the conclusion is the same: no
    # router tuning inside the 3-domain whitelist can ever produce
    # TIER_3_MUHURTA.
    "sulabh_dasha_q15": (
        "P2 order lock (CLAUDE.md Locked Decisions: Muhurta engine "
        "P2-ordered but \"not wired to Q&A in V1\"): TIER_3_MUHURTA is "
        "never produced by this pipeline. Observed mechanism this run: "
        "zero keyword hits in any of the 3 whitelisted domains -> refused "
        "via the generic confidence-floor path (same router refuse-heavy "
        "posture as q1), not via a muhurta-specific trigger -- either way, "
        "this row cannot MATCH without a scope change, not a router tune."
    ),
}

# Mismatches this harness has ACTUALLY reproduced that are genuine, un-locked
# product gaps -- distinct from _KNOWN_GAPS above, which is reserved for
# behavior a CLAUDE.md lock explicitly calls correct. A DESIGN_DEBT entry
# means "this is a real gap; it's just not this session's fix," pending an
# explicit design-chat whitelist/scope decision. Same seeding discipline as
# _KNOWN_GAPS: only rows this harness has actually observed, never guessed.
_DESIGN_DEBT: dict[str, str] = {
    # calc_router._UNBUILT_MODULE_KEYWORDS refuses on "sade sati" BEFORE
    # domain classification, but Sade Sati (transits/sade_sati.py) is a
    # BUILT and 4-chart-validated module (CLAUDE.md P2 order: Gochara ->
    # Sade Sati -> ...), not an unbuilt one -- unlike Muhurta (q15, genuinely
    # unbuilt-into-Q&A, KNOWN_GAP above), refusing this is product debt, not
    # a locked decision: no CLAUDE.md lock says a validated module must stay
    # unreachable from Q&A. Pending a design-chat decision on whether/how to
    # add a Sade Sati domain to the Q&A whitelist.
    "sulabh_dasha_q14": (
        "DESIGN DEBT, not a lock: question names \"Sade Sati\", which "
        "calc_router.py's _UNBUILT_MODULE_KEYWORDS refuses outright -- but "
        "sade_sati.py is built and 4-chart validated (CLAUDE.md P2 order), "
        "not unbuilt. Excluding a validated module from the Q&A whitelist "
        "is a real gap pending a design-chat whitelist decision, not "
        "documented-locked behavior."
    ),
}


@dataclasses.dataclass(frozen=True)
class RowResult:
    """One golden-set row's outcome against the live pipeline."""

    id: str
    domain: str
    expected_tier: str
    actual: str                    # AnswerTier value string, or "ERROR", or "N/A (batch)"
    demotion_reason: str | None
    category: str                  # MATCH | DESIGN_DEBT | KNOWN_GAP | NEW_GAP | ERROR | NON_RUNNABLE_BATCH


@dataclasses.dataclass(frozen=True)
class GoldenEvalSummary:
    """Counts + report location returned by run_golden_eval()."""

    evaluated_at_jd: float
    baseline_test_count: int
    golden_row_count: int
    runnable_count: int
    non_runnable_batch_count: int
    match_count: int
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


def _run_runnable_row(row: dict[str, Any], sulabh_chart: dict, surbhi_chart: dict) -> RowResult:
    golden_domain = row["domain"]
    expected_tier = row["expected_tier"]

    try:
        if golden_domain == "marriage":
            result = answer_question(
                row["question"],
                sulabh_chart,
                partner_chart_data=surbhi_chart,
                primary_role="boy",
            )
        else:
            result = answer_question(row["question"], sulabh_chart)
    except Exception as exc:  # noqa: BLE001 -- one row's crash must not abort the run
        return RowResult(
            id=row["id"],
            domain=golden_domain,
            expected_tier=expected_tier,
            actual="ERROR",
            demotion_reason=f"{type(exc).__name__}: {exc}",
            category="ERROR",
        )

    actual_tier = result.tier.value
    if actual_tier == expected_tier:
        category = "MATCH"
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
    )


def _non_runnable_row(row: dict[str, Any]) -> RowResult:
    return RowResult(
        id=row["id"],
        domain=row["domain"],
        expected_tier=row["expected_tier"],
        actual="N/A (batch, not executed)",
        demotion_reason=None,
        category="NON_RUNNABLE_BATCH",
    )


def _escape_md(cell: Any) -> str:
    text = "" if cell is None else str(cell)
    return text.replace("|", "\\|").replace("\n", " ")


def _render_report(
    evaluated_at_jd: float,
    rows: tuple[RowResult, ...],
    counts: dict[str, int],
) -> str:
    lines: list[str] = []
    lines.append("# P7.0 Golden Q&A Scorecard (Session 49)")
    lines.append("")
    lines.append(f"- Run evaluated_at_jd: `{evaluated_at_jd}`")
    lines.append(f"- Baseline pytest suite count (CLAUDE.md checkpoint): {_BASELINE_TEST_COUNT}")
    lines.append(f"- Golden-set row count: {len(rows)}")
    lines.append("")
    lines.append("## Per-row results")
    lines.append("")
    lines.append("| id | domain | expected_tier | actual | demotion_reason | category |")
    lines.append("|---|---|---|---|---|---|")
    for r in rows:
        lines.append(
            f"| {_escape_md(r.id)} | {_escape_md(r.domain)} | {_escape_md(r.expected_tier)} "
            f"| {_escape_md(r.actual)} | {_escape_md(r.demotion_reason)} | {_escape_md(r.category)} |"
        )
    lines.append("")
    lines.append("## Summary counts")
    lines.append("")
    for key in (
        "runnable",
        "non_runnable_batch",
        "match",
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

    sulabh_chart, surbhi_chart = _build_charts()

    rows: list[RowResult] = []
    for row in GOLDEN_QA:
        if _classify_runnability(row) == "RUNNABLE":
            rows.append(_run_runnable_row(row, sulabh_chart, surbhi_chart))
        else:
            rows.append(_non_runnable_row(row))

    counts = {
        "runnable": sum(1 for r in rows if r.category != "NON_RUNNABLE_BATCH"),
        "non_runnable_batch": sum(1 for r in rows if r.category == "NON_RUNNABLE_BATCH"),
        "match": sum(1 for r in rows if r.category == "MATCH"),
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
        f"match={summary.match_count} design_debt={summary.design_debt_count} "
        f"known_gap={summary.known_gap_count} new_gap={summary.new_gap_count} "
        f"error={summary.error_count}"
    )
    print(f"report: {summary.report_path}")
