"""
Astro Agent -- CAPABILITY GATE (Stage 1.5).

PATH B. Step 2 of the S129 cutover. Deterministic, NO LLM.

WHAT PROBLEM THIS SOLVES
------------------------
The fact block the Interpreter reads is currently 13 lines: the ascendant and
the 12 house-lord placements (`pipeline._fact_block`). The calculator can
produce far more -- dasha periods, Shadbala, transits -- but none of it is in
the block, because the `vimshottari` / `chart_d1` calculation stubs are unbuilt
(S125 lock, order item 3).

So a question like "when will I marry?" plans `timing_dasha`, retrieves the
timing chapters, and hands the Interpreter classical dasha doctrine with NO
dasha facts to apply it to. The model can then only do one of two things:
refuse, or reason a date out of the doctrine. gpt-5 refused on the one timing
question measured at S126 -- but that is N=1, and the silence gate CANNOT
catch it if it ever does otherwise: `silence_gate.read_condition` only judges
claims of the shape "the Nth lord is in the Mth" (`silence_gate.py`'s
`_CONDITION_RE`), and it fails open on everything else. An unverifiable dated
claim therefore ships unchecked -- Working Style #5, AI reviewing AI.

This gate closes that by construction. It is asked BEFORE the Interpreter --
before retrieval, even -- whether the facts a planned domain needs are
actually present. If they are not, that domain is dropped from the plan and
the user is told plainly what could not be answered and why. The LLM is never
given the chance to fill a gap it cannot see.

WHY A GATE AND NOT A PROMPT INSTRUCTION
---------------------------------------
"Do not state dates" in the interpreter prompt is an instruction the model may
follow. This is a Python branch that removes the doctrine from the payload. The
project's own standing law -- compute the term and feed it, never make the LLM
bridge two representations (CLAUDE.md Working Style #23) -- points the same way.

FAIL CLOSED, DELIBERATELY
-------------------------
Note the direction of error, because it is the opposite of the retrieval
filters'. `payload_builder`'s filters fail SAFE (keep the segment) because
over-keeping only costs tokens. This gate fails CLOSED (decline the domain)
because over-answering costs a fabricated date. Same project, two different
correct directions -- S125's "a permissive matcher can never be a precision
judge" is the law behind both.

GROWING THIS FILE
-----------------
`FACT_BLOCK_PROVIDES` is the single declaration of what the fact block carries.
When the block widens -- by RESTATING more of `calculate_chart()`, never by
implementing the permanent `chart_d1` stub (P-022) -- add
the new capability key here IN THE SAME CHANGE and the matching requirements
stop firing automatically. A requirement whose `needs` is satisfied is inert;
nothing else has to be edited, and no requirement ever has to be deleted.

Python 3.11.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

__all__ = [
    "CAPABILITY_GATE_VERSION",
    "FACT_BLOCK_PROVIDES",
    "REQUIREMENTS",
    "Requirement",
    "GateVerdict",
    "assess",
]

CAPABILITY_GATE_VERSION = "capability-gate-1.0"

# ---------------------------------------------------------------------------
# What the fact block actually carries TODAY.
#
# Keep this in lockstep with pipeline._fact_block. A key here is a promise that
# the Interpreter can see that class of fact; adding one without widening the
# block is how a fabricated claim gets through.
# ---------------------------------------------------------------------------
FACT_BLOCK_PROVIDES: frozenset[str] = frozenset({
    "ascendant_sign",      # the ascendant line
    "lord_house_map",      # the 12 house-lord placement lines
    "planet_positions",    # per-graha house + sign (S129)
    "house_lords",         # which planet rules each house + groupings (S130)
    "aspects",             # conjunctions, aspects_by_planet, aspected_by (S130)
    "dignity",             # exalted/debilitated/own-sign ONLY, + dispositor (S130)
    "navamsa",             # D9 signs/houses, restated from vargas/navamsa (S130)
    "yogas",               # fired + ruled-out yoga verdicts computed by the
                           # yoga detector over the facts above (S133). Additive
                           # fact class; no REQUIREMENT references it.
    "dasha_periods",       # Vimshottari mahadasha + antardasha, restated from
                           # calculate_chart()['dasha'] by chart_facts._read_dasha
                           # (S141; pratyantar suppressed). Landing this key made the
                           # dasha_timing requirement inert, so it was RETIRED -- see
                           # REQUIREMENTS below.
    "transits",            # per-antardasha Saturn gochara + Sade Sati phase,
                           # computed by agent.astro.transit_facts.build_transit_facts
                           # over the facts above (S142). Additive fact class, same
                           # posture as "yogas" -- no REQUIREMENT references it; it
                           # exists to corroborate WHICH dasha window a dated event
                           # falls in, not to gate any question on its own.
    "shadbala",           # six-fold planetary strength (Shadbala totals),
                           # composed by agent.astro.shadbala_facts. Additive
                           # context; a declared `unfittable` concept
                           # (predicates.py) -- no predicate, no Requirement.
    "ashtakavarga",       # SAV bindus per house + per-planet BAV, composed by
                           # agent.astro.ashtakavarga_facts. Additive house-strength
                           # context; no predicate (unfittable), no Requirement.
    "jaimini",            # Jaimini chara karakas + Arudha/Upapada Lagna, composed
                           # by agent.astro.jaimini_facts. Jaimini concepts
                           # (unfittable) -- no predicate, no Requirement.
    "divisional",         # domain vargas (D10/D7/D2/D30/D12/D3/D24), composed by
                           # agent.astro.divisional_facts. Varga placements
                           # (unfittable) -- no predicate, no Requirement.
    "muhurta",            # generic electional favourability over a bounded forward
                           # scan (Chandrabala+Tarabala+Panchaka + panchanga-shuddhi
                           # limbs), composed by agent.astro.muhurta_facts.
                           # build_muhurta_facts (S147). Additive fact class, same
                           # posture as "divisional": no predicate (unfittable), no
                           # REQUIREMENT. The horizon-completeness check in assess()
                           # is a separate INPUT-side clause, not a fact Requirement.
    "lucky_unlucky",      # favourable / to-be-avoided WEEKDAYS, CALCULATED from the
                           # chart's own house lordships (trikona lord -> favourable,
                           # dusthana-only lord -> avoid; trikona dominates), composed
                           # by agent.astro.lucky_facts.build_lucky_facts (S147).
                           # Additive fact class, same posture as "divisional": no
                           # predicate (unfittable), no REQUIREMENT. Personalised and
                           # computed -- never pulled from the AstroSage PDF.
    "kp_seventh_cusp_sub_lord",  # KP (Krishnamurti Paddhati) 7th-cusp sub-lord,
                           # computed by agent.astro.kp_facts.build_kp_facts over
                           # chart['meta']['house_cusps_kp_sidereal'] (a DIFFERENT
                           # ayanamsha than everything else in the fact block --
                           # see chart_calculator.py's S143 comment). Additive
                           # fact class, same posture as "transits" -- a second
                           # cross-system corroboration for marriage-timing
                           # selection, not a gate on its own.
    "kp_planet_significations",  # KP house significators (Sun..Ketu -> houses
                           # signified), parsed from AstroSage's own printed
                           # "Significators of Houses" table by
                           # agent.calculations.kp.significators.parse_kp_significators,
                           # composed by agent.astro.kp_significator_facts.
                           # build_kp_significator_facts (S143-followup, this
                           # session). Unlike "kp_seventh_cusp_sub_lord", this
                           # fact varies BY WHICH LORD is running (each
                           # antardasha's own lord's significations are tagged
                           # in the dasha timeline), so it can actually
                           # discriminate between two antardashas -- the fixed
                           # cuspal sub-lord fact cannot. Requires a PDF
                           # uploaded this session; {} (absent) whenever none
                           # was -- additive fact class, same posture as
                           # "transits"/"kp_seventh_cusp_sub_lord".
})


@dataclass(frozen=True)
class Requirement:
    """One class of fact a question may need, and what to say when it is absent.

    Attributes:
        id: stable identifier, used in logs and tests. Never user-visible.
        needs: the FACT_BLOCK_PROVIDES key that must be present for the
            triggering questions to be answerable.
        domains: planner domains that require `needs`.
        time_scopes: planner time_scopes that require `needs`. A question can
            trigger on time_scope alone -- "what happens next year" may plan
            only `career`, but it is still asking for a date.
        user_message: layman sentence shown verbatim to the user. States what
            cannot be answered and why, never an apology and never a promise
            about when it will work.
        blocks_whole_answer: True when the requirement is so central that the
            remaining domains cannot carry a useful answer on their own. False
            means "drop this domain, answer the rest, and say what was left
            out" -- the honest-partial path.
    """
    id: str
    needs: str
    user_message: str
    domains: frozenset[str] = field(default_factory=frozenset)
    time_scopes: frozenset[str] = field(default_factory=frozenset)
    blocks_whole_answer: bool = False

    def triggered_by(self, domains: Iterable[str], time_scope: str) -> bool:
        return bool(set(domains) & self.domains) or time_scope in self.time_scopes


# ---------------------------------------------------------------------------
# The requirement register.
#
# EMPTY as of S141. It held ONE entry -- `dasha_timing` -- and that was the last
# fact class any planner domain needed and the block did not carry. Every other
# domain (career, marriage, wealth, children, health, education, longevity,
# travel, property, parents, siblings, spirituality, enemies_conflict,
# planetary_nature) answers from house-lord placements, which is what BPHS's
# house chapters are keyed on. S141 restated the Vimshottari timeline into
# `dasha_periods` (chart_facts._read_dasha -> FACT_BLOCK_PROVIDES above), so
# `dasha_timing`'s `needs` is now provided: the requirement could never fire
# again, and `test_every_requirement_names_a_capability_the_block_does_not_yet_have`
# forbids a satisfied requirement lingering. It was RETIRED. Timing questions are
# now answerable, so the gate declines nothing.
#
# (S136: technique_method was REMOVED from planner.DOMAINS entirely -- a
# methodology question is refused as out of scope before the gate, so no
# requirement could ever fire for it. See planner.DOMAINS and KNOWN_PATTERNS P-030.)
#
# Do NOT add a requirement speculatively. Add one when a real question is
# observed being answered from facts that are NOT in the block -- the register
# is intentionally empty until then. The dataclass and assess() below are kept
# whole for that day.
# ---------------------------------------------------------------------------
REQUIREMENTS: tuple[Requirement, ...] = ()


@dataclass
class GateVerdict:
    """Outcome of assessing one plan against the current fact block.

    Attributes:
        plan: the plan to actually run. Either the original object (untouched)
            or a copy whose `domains` have been narrowed. Never mutated in
            place -- the caller's plan stays intact for the decision log.
        refuse_outright: nothing answerable remains; do not call the Interpreter.
        declined: [(requirement_id, user_message)] for every requirement that
            fired, in register order.
        dropped_domains: sorted domains removed from the plan.
        gate_version: provenance, carried into the pipeline's return dict.
    """
    plan: object
    refuse_outright: bool
    declined: list[tuple[str, str]]
    dropped_domains: list[str]
    gate_version: str = CAPABILITY_GATE_VERSION

    @property
    def messages(self) -> list[str]:
        """Just the user-facing sentences, in order."""
        return [m for _, m in self.declined]


def assess(plan, *, provides: frozenset[str] = FACT_BLOCK_PROVIDES) -> GateVerdict:
    """Narrow `plan` to what the current fact block can actually support.

    Args:
        plan: an agent.astro.planner.Plan (duck-typed: needs .domains and
            .time_scope). Never mutated.
        provides: capability keys the fact block carries. Override in tests to
            simulate a widened block; production always passes the default.

    Returns:
        GateVerdict. `refuse_outright` is True when every planned domain was
        dropped, or when a `blocks_whole_answer` requirement fired.

    Raises:
        TypeError: if `plan` does not expose `domains` and `time_scope` --
            better a loud failure here than a silently ungated answer.
    """
    try:
        domains = list(plan.domains or [])
        time_scope = plan.time_scope
    except AttributeError as e:
        raise TypeError(
            "capability_gate.assess expects a planner.Plan (needs .domains and "
            f".time_scope); got {type(plan).__name__}: {e}"
        ) from e

    declined: list[tuple[str, str]] = []
    dropped: set[str] = set()
    hard_block = False

    for req in REQUIREMENTS:
        if req.needs in provides:
            continue  # the block grew; this requirement is inert
        if not req.triggered_by(domains, time_scope):
            continue
        declined.append((req.id, req.user_message))
        dropped |= set(domains) & req.domains
        hard_block = hard_block or req.blocks_whole_answer

    # -- muhurta needs NO gate clause (S147, Sulabh) ------------------------
    # Earlier this asked for a horizon when muhurta was flagged without one.
    # Superseded: muhurta now DEFAULTS to a 2-year scan from now in the pipeline
    # ("default 2 years unless asked for more"), so the gate never declines a
    # muhurta question for a missing horizon -- it just passes through and the
    # windows are computed.

    if not declined:
        return GateVerdict(plan=plan, refuse_outright=False, declined=[],
                           dropped_domains=[])

    remaining = [d for d in domains if d not in dropped]
    refuse = hard_block or not remaining

    # Copy, never mutate: the original plan is what the decision log recorded,
    # and silently editing it would make that log a lie.
    narrowed = _with_domains(plan, remaining)

    return GateVerdict(
        plan=narrowed,
        refuse_outright=refuse,
        declined=declined,
        dropped_domains=sorted(dropped),
    )


def _with_domains(plan, domains: list[str]):
    """Return a copy of `plan` carrying `domains`, leaving the original alone."""
    import copy
    clone = copy.copy(plan)
    try:
        clone.domains = domains
    except AttributeError as e:  # frozen/slotted Plan -- fall back to deepcopy
        clone = copy.deepcopy(plan)
        try:
            object.__setattr__(clone, "domains", domains)
        except Exception:
            raise TypeError(
                f"cannot narrow domains on a {type(plan).__name__}: {e}"
            ) from e
    return clone
