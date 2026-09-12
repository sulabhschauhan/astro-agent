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
When `chart_d1` or `vimshottari` lands and `pipeline._fact_block` widens, add
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
# ONE entry today. That is not an oversight: every other planner domain
# (career, marriage, wealth, children, health, education, longevity, travel,
# property, parents, siblings, spirituality, enemies_conflict,
# technique_method, planetary_nature) is answerable from house-lord placements
# alone, which is exactly what BPHS's house chapters are keyed on. Only timing
# needs a fact class the block does not carry.
#
# Do NOT add a requirement speculatively. Add one when a real question is
# observed being answered from facts that are not in the block.
# ---------------------------------------------------------------------------
REQUIREMENTS: tuple[Requirement, ...] = (
    Requirement(
        id="dasha_timing",
        needs="dasha_periods",
        domains=frozenset({"timing_dasha"}),
        time_scopes=frozenset({"future", "specific_period"}),
        user_message=(
            "I can't tell you when. The dasha period calculation isn't wired "
            "into the chart facts I can read yet, so any date or timeframe I "
            "gave you would be invented rather than calculated."
        ),
        # Timing is the whole question in "when will I marry?", but it is a
        # rider in "what does my chart say about marriage, and when?". Dropping
        # the domain and answering the rest is the honest middle, so this is
        # False -- assess() escalates to a full refusal only when NOTHING is
        # left to answer from.
        blocks_whole_answer=False,
    ),
)


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
