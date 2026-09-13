"""

================================================================
PATH B IS THE PRODUCT (S129 cutover). THIS MODULE IS LIVE.

frontend/app.py:37 imports answer_question from
agent.astro.pipeline. A change here SHIPS TO USERS.
Path A (agent/infra/orchestrator) is retained, tested and intact
as the revert target, but is wired to no UI.
Read docs/ANSWER_PATHS.md before editing or proposing work here.

SUPERSEDES the S128 banner that stood here and said this module
had no non-test caller and shipped nothing. That was true at S128
and false from S129 on.
================================================================

Astro Agent -- FULL ANSWER PIPELINE.

  question -> plan (Stage 1) -> unit+domain selection (Stage 2)
           -> payload build (Stage 3) -> Interpreter/GPT-5 (Stage 4)
           -> Silence gate (Stage 5a) -> answer.

The Calculator (Stage 3.5) supplies the FACT BLOCK the Interpreter reads.
Today that block is the chart's ascendant, its lord->house map, and per-graha
planet positions (house + sign only, S129b). It widens by RESTATING more of
`agent/chart_calculator.py::calculate_chart()` -- never by implementing
`agent/calculations/core/chart_d1.py`, which is a permanent deliberate stub
(P-022). The LLM never computes a chart fact.

Dependency-injected `llm` (planner) and `interpreter_llm` (interpreter) so the
whole chain is testable with stubs and never calls the API in CI.
Python 3.11.
"""
from __future__ import annotations

import time
from typing import Callable, Optional

from agent.astro import planner
from agent.astro import capability_gate
from agent.astro import interpreter as _interp
from agent.astro import silence_gate
from agent.astro import payload_builder

PIPELINE_VERSION = "pipeline-1.2"


_ORDINAL_SUFFIX = {1: 'st', 2: 'nd', 3: 'rd'}


def _ordinal(n: int) -> str:
    """1 -> 1st. 11/12/13 take "th", which is why this is not n % 10 alone."""
    if 11 <= n % 100 <= 13:
        return str(n) + "th"
    return str(n) + _ORDINAL_SUFFIX.get(n % 10, "th")


def _fact_block(chart_facts: dict) -> str:
    """Render the chart facts the Interpreter is allowed to reason from.

    GROWTH CONTRACT: every class of fact rendered here MUST have a matching key
    in `capability_gate.FACT_BLOCK_PROVIDES`, added in the SAME change.
    `tests/astro/test_capability_gate.py` pins the two together and fails if
    they drift -- that pin is what stops the gate declining a question the
    block can now answer, or the reverse.
    """
    lord_house, asc = payload_builder.parse_lord_house_map(chart_facts)
    lines = ["CHART FACTS (the only chart facts you may use):",
             f"Ascendant sign: {asc}"]

    # House lords. The named form is used when chart_facts carries `house_lords`
    # (S130); the bare form is the pre-S130 shape and stays byte-identical for
    # it, so a legacy chart_facts dict renders exactly as it always did.
    house_lords = chart_facts.get("house_lords") or {}
    for h in range(1, 13):
        hl = house_lords.get(h) or house_lords.get(str(h))
        if hl and hl.get("lord"):
            sign = f" ({hl['sign']})" if hl.get("sign") else ""
            lines.append(f"House {h}{sign}: its lord is {hl['lord']}, "
                         f"and {hl['lord']} sits in house {lord_house[h]}")
        else:
            lines.append(f"House {h}: its lord sits in house {lord_house[h]}")

    # GROUPINGS (S130). Pure regrouping of the twelve lines above -- no new
    # fact, no doctrine, no kendra/trikona labelling (that vocabulary lives in
    # the corpus, not here). It exists because the Interpreter was emitting
    # "the 9th lord in the 4th" and "the 10th lord in the 4th" as unrelated
    # claims across twelve rows and never noticing they name one house. Stating
    # the grouping is Working Style #23: feed the computed term, never ask the
    # model to bridge two representations.
    shared: dict[int, list[int]] = {}
    for h in range(1, 13):
        shared.setdefault(lord_house[h], []).append(h)
    together = [(dest, hs) for dest, hs in sorted(shared.items()) if len(hs) > 1]
    if together:
        lines.append("")
        lines.append("House lords that share a house (they are together there):")
        for dest, hs in together:
            names = ", ".join(_ordinal(h) for h in hs)
            lines.append(f"  the lords of houses {names} are all in house {dest}")

    if house_lords:
        rules: dict[str, list[int]] = {}
        for h in range(1, 13):
            hl = house_lords.get(h) or house_lords.get(str(h))
            if hl and hl.get("lord"):
                rules.setdefault(hl["lord"], []).append(h)
        multi = [(p_, hs) for p_, hs in rules.items() if len(hs) > 1]
        if multi:
            lines.append("")
            lines.append("Planets that rule more than one house:")
            for p_, hs in multi:
                lines.append(f"  {p_} rules houses "
                             + " and ".join(str(h) for h in sorted(hs)))

    # Planet positions (S129). Rendered in the classical Navagraha order that
    # chart_facts fixes, so the block is byte-stable across runs. Absent for a
    # chart_facts dict built from `fact_block_text` -- that legacy shape has no
    # planet data, and its absence is honest, not an error.
    # ASPECTS + CONJUNCTIONS (S130). Restated from calculate_chart(); see
    # chart_facts._read_aspects. `aspected_by` is the half that matters most --
    # it is what answers "is this placement afflicted", a check a benchmark
    # answer for this chart got wrong by eye.
    aspects = chart_facts.get("aspects") or {}
    conj = aspects.get("conjunctions") or []
    by_planet = aspects.get("aspects_by_planet") or {}
    aspected_by = aspects.get("aspected_by") or {}
    if conj or by_planet or aspected_by:
        lines.append("")
        lines.append("Aspects and conjunctions:")
    for c in conj:
        lines.append(f"  {c}")
    for planet, houses in by_planet.items():
        if houses:
            lines.append(f"  {planet} aspects houses "
                         + ", ".join(str(h) for h in houses))
    for planet, sources in aspected_by.items():
        if sources:
            lines.append(f"  {planet} is aspected by " + ", ".join(sources))

    # MUTUAL aspects. Same regrouping justification as the lord groupings
    # above: a one-way aspect and a mutual one carry different doctrinal
    # weight, and asking the model to cross-reference two lists to tell them
    # apart is the bridging failure Working Style #23 forbids. Stated here so
    # it cannot be guessed at.
    mutual = set()
    for planet, sources in aspected_by.items():
        for src in sources:
            if planet in (aspected_by.get(src) or []):
                mutual.add(tuple(sorted((planet, src))))
    if mutual:
        lines.append("")
        lines.append("Planets that aspect EACH OTHER (mutual, not one-way):")
        for a, b in sorted(mutual):
            lines.append(f"  {a} and {b}")
    positions = chart_facts.get("planet_positions") or {}
    if positions:
        lines.append("")
        for planet, pos in positions.items():
            standing = pos.get("dignity")
            mark = f" -- {standing.lower()} there" if standing else ""
            lines.append(
                f"{planet} is in house {pos['house']} ({pos['sign']}){mark}.")

        # DISPOSITOR CHAIN (S130). The lord of the SIGN a planet occupies.
        # Derived only from (sign, lord) pairs already present in house_lords
        # -- no lord table is introduced here. Stated because Neecha Bhanga
        # is a two-step relation (debilitated planet -> its dispositor's own
        # standing) and step two is otherwise a lookup the model has to
        # perform across two separate blocks.
        sign_lord = {}
        for h in range(1, 13):
            hl = house_lords.get(h) or house_lords.get(str(h))
            if hl and hl.get("sign") and hl.get("lord"):
                sign_lord[hl["sign"]] = hl["lord"]
        chain = []
        for planet, pos in positions.items():
            lord = sign_lord.get(pos.get("sign"))
            if not lord or lord == planet:
                continue
            lord_pos = positions.get(lord) or {}
            lord_sign = lord_pos.get("sign")
            lord_dig = lord_pos.get("dignity")
            if not lord_sign:
                continue
            tail = f" -- {lord_dig.lower()} there" if lord_dig else ""
            chain.append(f"  {planet} is in {pos['sign']}, whose lord is {lord}; "
                         f"{lord} is in {lord_sign}{tail}")
        if chain:
            lines.append("")
            lines.append("Each planet's sign-lord (its dispositor):")
            lines.extend(chain)

    # NAVAMSA / D9 (S130). Restated from agent/calculations/vargas/navamsa.py,
    # oracle-clean on 4/4 reference charts since S20 and unwired until now.
    # Carried because a debilitated planet exalted in D9 is one of the
    # classical Neecha Bhanga routes, and it is the ONLY route left open for
    # this chart once the dispositor tests fail.
    nav = chart_facts.get("navamsa") or {}
    nav_places = nav.get("placements") or {}
    if nav_places:
        lines.append("")
        d9l = nav.get("d9_lagna_sign")
        lines.append("In the Navamsa (D9) divisional chart"
                     + (f", whose ascendant is {d9l}:" if d9l else ":"))
        for planet, row in nav_places.items():
            standing = row.get("dignity")
            mark = f" -- {standing.lower()} there" if standing else ""
            lines.append(f"  {planet} is in {row['sign']} "
                         f"(D9 house {row['house']}){mark}")
    return "\n".join(lines)


def _render(kept: list[dict], silent_on: list[str],
            declined_messages: list[str] | None = None) -> str:
    """Assemble the user-facing answer.

    `declined_messages` are the capability gate's plain-language notes about
    what could NOT be answered. They are appended, never interleaved, so the
    user always sees the limit alongside the answer rather than instead of it.
    """
    declined_messages = declined_messages or []
    if not kept:
        msg = "I can't answer this from the classical text and chart facts available."
        parts = [msg]
        if silent_on:
            parts.append("\n".join(f"- {s}" for s in silent_on))
        parts += declined_messages
        return "\n\n".join(parts)
    out = []
    for c in kept:
        cites = " ".join(f"[{i}]" for i in c.get("segment_ids", []))
        out.append(f"- {c['statement']} {cites}".rstrip())
    if silent_on:
        out.append("\nNot addressed: " + "; ".join(silent_on))
    body = "\n".join(out)
    if declined_messages:
        body += "\n\n" + "\n\n".join(declined_messages)
    return body


def answer_question(
    question: str,
    chart_facts: dict,
    *,
    llm: Optional[Callable] = None,
    interpreter_llm: Optional[Callable] = None,
    token_budget: int = planner.DEFAULT_TOKEN_BUDGET,
) -> dict:
    """End-to-end. Never raises for a model/gate problem -- refuses or fails
    open with the reason on the record.

    Stage 1.5 (`capability_gate.assess`) sits between planning and retrieval:
    it narrows the plan to what the fact block can actually support, so a
    question needing facts we do not have is declined in Python rather than
    handed to the Interpreter to guess at. See capability_gate's docstring.
    """
    # Per-stage wall clock. Cheap, always on: the capture needs it and a slow
    # stage is the first thing anyone asks about after a live run.
    _t = time.perf_counter()
    timings: dict[str, float] = {}

    def _lap(stage: str) -> None:
        nonlocal _t
        now = time.perf_counter()
        timings[stage] = round(now - _t, 3)
        _t = now

    plan = planner.plan_question(question, llm=llm)
    _lap("plan")
    verdict = capability_gate.assess(plan)
    _lap("capability_gate")

    if verdict.refuse_outright:
        return {"answer": "\n\n".join(verdict.messages),
                "refused": True,
                "reason": "capability_gate: " + ", ".join(i for i, _ in verdict.declined),
                "plan": plan,
                "declined": verdict.declined,
                "dropped_domains": verdict.dropped_domains,
                "capability_gate_version": verdict.gate_version,
                "trace": {"timings": timings, "payload": {},
                          "plan_before_gate": {"domains": list(plan.domains or []),
                                               "time_scope": plan.time_scope},
                          "gate_refused_outright": True,
                          "refused_at": "capability_gate"},
                "pipeline_version": PIPELINE_VERSION}

    built = planner.build_from_plan(verdict.plan, chart_facts, token_budget=token_budget)
    _lap("select_and_build_payload")
    if built.get("refused"):
        return {"answer": f"(no answer) {built.get('refusal_reason', 'refused')}",
                "refused": True, "reason": built.get("refusal_reason"),
                "plan": built["plan"],
                "declined": verdict.declined,
                "capability_gate_version": verdict.gate_version,
                "trace": {"timings": timings, "payload": built.get("payload") or {},
                          "refused_at": "payload_ceiling"},
                "pipeline_version": PIPELINE_VERSION}

    fact_block = _fact_block(chart_facts)
    interp = _interp.interpret(question, fact_block, built["payload"], llm=interpreter_llm)
    _lap("interpreter")
    gate = silence_gate.apply_silence_gate(interp, built["payload"], chart_facts)
    _lap("silence_gate")

    selection = built.get("selection")
    trace = {
        "timings": timings,
        # The plan the PLANNER produced, before the capability gate narrowed it.
        # `result["plan"]` is the post-gate plan; without this the gate's effect
        # is invisible and a reader mistakes the narrowed plan for Stage 1's own
        # output (observed on the first live capture, S129).
        "plan_before_gate": {"domains": list(plan.domains or []),
                             "houses": list(plan.houses or []),
                             "time_scope": plan.time_scope,
                             "whose_chart": plan.whose_chart,
                             "in_scope": plan.in_scope,
                             "source": plan.source},
        "gate_refused_outright": verdict.refuse_outright,
        "payload": built["payload"],          # carries the full verse text
        "fact_block": fact_block,
        "unit_ids": getattr(selection, "unit_ids", None),
        "per_domain_units": getattr(selection, "per_domain_units", None),
        "corpus_fraction": getattr(selection, "corpus_fraction", None),
        "estimated_real_tokens": built.get("estimated_real_tokens"),
        "over_budget": built.get("over_budget"),
        "tpm_note": built.get("tpm_note"),
        "interpreter_refused": interp.get("refused"),
        "interpreter_raw": interp.get("raw"),
        "gate_error": gate.error,
    }

    return {
        "trace": trace,
        "answer": _render(gate.kept_claims, gate.silent_on, verdict.messages),
        "refused": interp["refused"] and not gate.kept_claims,
        "plan": built["plan"],
        "declined": verdict.declined,
        "dropped_domains": verdict.dropped_domains,
        "capability_gate_version": verdict.gate_version,
        "kept_claims": gate.kept_claims,
        "dropped_claims": gate.dropped_claims,       # precondition-false, removed by the gate
        "silent_on": gate.silent_on,
        "ghost_citations": interp["ghost_citations"],  # must be []
        "gate_stats": gate.stats,
        "usage": interp["usage"],
        "tokens": built["tokens"],
        "model": interp["model"],
        "pipeline_version": PIPELINE_VERSION,
    }
