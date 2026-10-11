"""Capability registry + manifest (S150 -- runtime dispatcher foundation).

THE single source of truth for the COMPUTED, non-corpus capabilities the agent
answers directly -- lucky days today; muhurta, graha-into-house transits and
auspicious windows as they migrate onto it. A computed capability is answerable
WITHOUT corpus retrieval: it reads a fact class already in the fact block, and
that fact class is itself computed from a cited rule, so a registered capability
is sourced BY CONSTRUCTION (there is no row without a backing calculation --
the S150 ruling: registration is self-sourcing, not a gate we enforce).

Rendered two ways, both from this ONE list so no second hierarchy can drift
(the P-030 failure class):
  * planner_manifest()      -> the planner prompt. Names each capability + the
                               gloss that triggers it, a closed vocabulary with
                               one definition per term (WS#35).
  * interpreter_manifest()  -> the answering LLM. Tells it which capabilities
                               are AVAILABLE for the chart in hand and which
                               required INPUTS are present or missing, so it
                               answers with full awareness, declines anything
                               NOT listed ("I don't compute that yet" -- never
                               improvises from pop astrology), and asks at most
                               ONE grounded question, only when the answer is
                               impossible without a missing detail. No upsell,
                               ever (S150 ruling: answer the question, do not
                               offer unrequested capabilities).

Corpus domains stay in planner.DOMAINS for now; this registry holds only the
computed capabilities that have no corpus home. Folding both kinds into one
registry is the documented END STATE, deferred to keep the committed pipeline
stable -- the manifests already read planner.DOMAINS alongside this list so the
LLMs see the full surface meanwhile.

LEAF module: stdlib only, imports nothing from agent.* so planner, pipeline and
interpreter can all read it without a cycle. Python 3.11.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Capability:
    """One computed, non-corpus thing the agent can answer directly.

    Attributes:
        id: stable identifier -- what the planner emits and the dispatcher keys
            on. Never user-visible.
        intent_gloss: one line, for the planner prompt: WHEN this capability is
            the right route. The closed-vocabulary definition for this term.
        fact_key: the key this capability reads from the fact block. MUST be a
            member of capability_gate.FACT_BLOCK_PROVIDES (pinned by a test --
            the growth contract: a capability cannot route to a fact the block
            does not carry).
        label: short human name used in the interpreter manifest.
        dated: True when the fact is parametrised by a date/horizon and must be
            composed at answer time (muhurta/ingress class); False for a
            chart-fixed fact read straight from the static store (lucky days).
        needs_chart: True when composing the fact needs the raw chart.
        requires_input: inputs that must be present for the fact to exist
            (e.g. "exact_birth_time", "pdf"); surfaced in the interpreter
            manifest so it can ask for a genuinely missing input.
        interpreter_directive: how to answer from this fact -- always grounding,
            never inventing. Assembled into the interpreter prompt for whichever
            capabilities fired, so the answering LLM is never hand-coded per
            feature.
    """
    id: str
    intent_gloss: str
    fact_key: str
    label: str
    dated: bool = False
    needs_chart: bool = True
    requires_input: tuple[str, ...] = ()
    interpreter_directive: str = ""


# ---------------------------------------------------------------------------
# THE REGISTRY. One row per computed capability. Seeded with the pilot
# (lucky days); muhurta and the dated engines (combustion/ingress/timeline)
# migrate in as further rows, each pointing at a fact class already in
# FACT_BLOCK_PROVIDES. Do NOT add a row whose doctrine is not yet sourced and
# coded (do's/don'ts and remedies wait for Lal Kitab tagging) -- a row with no
# backing fact class is exactly the fabrication this project forbids.
# ---------------------------------------------------------------------------
REGISTRY: tuple[Capability, ...] = (
    Capability(
        id="lucky_days",
        intent_gloss=(
            "the native's lucky / unlucky / auspicious / favourable / "
            "to-be-avoided DAYS OF THE WEEK (e.g. 'which is my luckiest day', "
            "'what days should I avoid')"
        ),
        fact_key="lucky_unlucky",
        label="Lucky & unlucky weekdays",
        dated=False,
        needs_chart=False,
        interpreter_directive=(
            "Answer ONLY from the computed favourable_days / avoid_days in the "
            "fact block -- each already carries the ruling planet and houses "
            "that justify it. Name the days plainly and give the one-line "
            "reason from the fact. Never compute, rank, add or invent a day the "
            "fact block does not list."
        ),
    ),
    Capability(
        id="muhurta",
        intent_gloss=(
            "the best / auspicious DATE or TIME to DO or START something -- to "
            "marry, to buy or move into a house, to start a business or job, to "
            "travel, to hold a ceremony. This is ELECTIONAL -- 'when should I DO "
            "X'. It is NOT 'when will X happen to me' / 'when will I get X' "
            "(that is a prediction and uses the corpus timing, NOT this)."
        ),
        fact_key="muhurta",
        label="Electional timing (muhurta)",
        dated=True,
        needs_chart=True,
        interpreter_directive=(
            "The user asked for a GOOD DATE/TIME TO ACT, not for when an event "
            "will befall them. These windows are COMPUTED -- present the ones "
            "given and NEVER invent or shift a date. Lead with the BEST window; "
            "if a different EARLIEST good window is given, name it too (e.g. 'the "
            "best time is <x>; if you'd rather act sooner, <y> is also strong'). "
            "State favourability plainly -- clearly auspicious (TIER_1) vs "
            "acceptable but weaker (TIER_2) -- and mention any caution limbs in "
            "one short phrase. This is GENERIC favourability only: do NOT claim "
            "it is tailored to the specific event. Answer an electional question "
            "from THESE muhurta windows, NEVER from the dasha/timing ranking. If "
            "the facts say no auspicious window was found in the searched span, "
            "say exactly that and name the span -- do NOT manufacture a date, and "
            "never tell the user a window is 'not available' or 'not pre-computed'."
        ),
    ),
)

_BY_ID: dict[str, Capability] = {c.id: c for c in REGISTRY}
CAPABILITY_IDS: frozenset[str] = frozenset(_BY_ID)


def get(cap_id: str) -> Capability | None:
    """Return the Capability for an id, or None if the id is unknown."""
    return _BY_ID.get(cap_id)


def fact_keys() -> frozenset[str]:
    """The set of fact-block keys every registered capability reads."""
    return frozenset(c.fact_key for c in REGISTRY)


def directives_for(cap_ids) -> list[str]:
    """Interpreter directives for the fired capability ids, in registry order.

    Unknown ids are skipped (the planner validator rejects them upstream; this
    stays defensive so a stray id can never raise at answer time).
    """
    wanted = set(cap_ids or ())
    return [c.interpreter_directive for c in REGISTRY
            if c.id in wanted and c.interpreter_directive]


def planner_manifest() -> str:
    """Closed-vocabulary block for the planner prompt: id -> trigger gloss.

    The planner returns matched ids in `capabilities`; this block is the ONLY
    place those ids are defined, so adding a capability is one registry row.
    """
    lines = [
        "COMPUTED CAPABILITIES -- answered from calculation, not the classical "
        "text. Put an id in `capabilities` when the question asks for one. "
        "Choose ONLY from this closed list:"
    ]
    for c in REGISTRY:
        lines.append(f"  - {c.id}: {c.intent_gloss}")
    return "\n".join(lines)


def interpreter_manifest(available_fact_keys, inputs_present=()) -> str:
    """What the answering LLM can compute for THIS chart, and the input state.

    Args:
        available_fact_keys: fact-block keys that are actually present and
            non-empty for this chart. A capability whose fact_key is present is
            listed as available; otherwise it is listed as unavailable, with any
            missing required input named so the LLM can ask for it.
        inputs_present: inputs the user has supplied this session (e.g.
            "exact_birth_time", "pdf"), used to decide whether an unavailable
            capability is merely missing an input the user could provide.

    The block instructs the LLM to answer ONLY from listed-available
    capabilities (or the cited text), to decline anything not listed with "I
    don't compute that yet", and never to offer a capability the user did not
    ask about.
    """
    present = set(available_fact_keys or ())
    have_inputs = set(inputs_present or ())
    lines = [
        "WHAT YOU CAN COMPUTE FOR THIS CHART. Answer ONLY from a capability "
        "listed 'available' below (or from the cited classical text). For "
        "anything not listed, say plainly you do not compute that yet -- never "
        "improvise an answer. Do NOT offer or suggest a capability the user did "
        "not ask for.",
    ]
    for c in REGISTRY:
        if c.fact_key in present:
            lines.append(f"  - {c.label}: available.")
            continue
        missing = [i for i in c.requires_input if i not in have_inputs]
        if missing:
            lines.append(
                f"  - {c.label}: not computed -- needs {', '.join(missing)}. "
                f"Ask the user for it ONLY if their question cannot be answered "
                f"without it."
            )
        else:
            lines.append(f"  - {c.label}: not available for this chart.")
    return "\n".join(lines)
