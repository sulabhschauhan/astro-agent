"""
agent/interpretive/palm_select.py
THE canonical palm interpretation path (VERIFICATION ARCHITECTURE --
fidelity-not-truth, see data/palm_rules/README.md).

Supersedes the two hand-rolled `_HARD_PREREQUISITES` lambda maps in
scripts/smoke_test_palm_llm_select.py and scripts/eval_harness_soft_v1.py.
Those maps hardcoded, per rule id, a prerequisite that the production
matcher already computes from the rule's own antecedents -- a per-rule
label that could be tuned until a target came out right. This module has
no per-rule labels anywhere: an antecedent's class is a pure function of
(attribute, value, relation_target, condition_type).

TWO STEPS, in order (CLAUDE.md Locked Decision #23: "FULLY-HARD rules fire
from the gate; only soft-containing rules reach the LLM"):

  STEP 1 -- HARD GATE. Every rule is projected onto its HARD antecedents
    and that projection is handed to the REAL production match() from
    palm_rules_table.py. match() is imported, never reimplemented, so a
    pass here is a statement about production behaviour rather than about
    a copy of it. Fail-closed: a rule whose hard antecedents cannot be
    satisfied is dropped before the LLM ever sees it, exactly as the
    lambda gates did. A FULLY-HARD rule's projection IS the rule, so
    match() decides it outright and it never reaches the LLM at all.

  STEP 2 -- SOFT SELECT. Rules that survive the gate AND carry at least
    one soft antecedent go to the LLM as WHOLE VERBATIM Cheiro sentences.
    No anchors, no benchmarks, no thresholds, no condition decomposition:
    the model reads the sentence the way a human reader would and judges
    the relative terms ("high", "sloping", "chained") itself. The system
    prompt is carried over VERBATIM from the 5/5-clean smoke test -- this
    module changes what reaches the model, never how it is asked.

VOCABULARY GUARD (CLAUDE.md law #22, the S95 fix): before the LLM call,
every soft antecedent's trigger token is checked against the vocabulary
the pipeline can actually EMIT. A rule that triggers on a word the
hand-state can never supply is a guaranteed silent miss; it is recorded in
`unmatched` and withheld from the LLM pool. It is never sent onward as a
fake fire, and never allowed to fail quietly.

NOT wired into palm_reading.py or frontend/app.py by this module. V1 palm
UI remains gated off (S71 Option Z / S72 _PALM_ENABLED).
"""

from __future__ import annotations

import dataclasses
import json
import logging
from typing import Any, Iterable, Sequence

from agent.interpretive.palm_rules_table import Antecedent, PalmRule, match, resolve_priority

logger = logging.getLogger(__name__)

_MODEL = "gpt-4o"
_TEMPERATURE = 0

HARD, SOFT = "hard", "soft"


# ---------------------------------------------------------------------------
# THE PARTITION -- attribute-class map, applied uniformly. Never per-rule.
# ---------------------------------------------------------------------------

# A landmark / topology fact: one structurally-correct answer exists, and two
# competent readers looking at the same hand agree.
_HARD_ATTRS = frozenset({
    "Starting_Point",   # which landmark the line rises from
    "Ending_Point",     # which landmark it ends on
    "Presence",         # does the feature exist at all
    "Proximity",        # spatial relation to a named landmark
})

# A quality / texture / relative read: reader-dependent by nature. This is
# exactly what the whole-sentence LLM step exists to judge.
_SOFT_ATTRS = frozenset({
    "Depth",            # non-comparative only; the comparative override wins first
    "Width",
    "Color",
    "Continuity",       # chained / broken / forked / islanded / barred / clear
    "Direction",
    "Slope",
    "Slope_Magnitude",
    "Curve",
    "Clarity",
    "Length",           # short / long -- relative extent, described in prose
})

# Position is VALUE-SPLIT: a landmark-shaped value names a place (hard), a
# height-shaped value is a judgment relative to the palm.
_POSITION_LANDMARK_PREFIXES = ("under_", "terminating_on_", "running_through_")

# RULING 1 (Sulabh, no-anchor decision -- SETTLED, not a toggle): a height
# judgment relative to the palm is exactly the reader-dependent read the soft
# path exists for. "high"/"low" are SOFT and MUST NOT be routed through the hard
# gate. Consequence: H_010a and H_010b are MIXED, not FULLY-HARD -- their
# Breadth/Depth half gates, then ONE LLM call judges "so high on the hand" from
# the verbatim sentence.
_POSITION_HEIGHT_CLASS = SOFT

# Attributes named by NEITHER list. Routed by `unruled_policy`, never silently
# defaulted -- forcing them into a bucket is exactly what this module refuses to
# do. Present in the live corpus: Quadrangle.Breadth (4 antecedents),
# Branching as a bare count (5), Hand.Type (3).
_UNRULED = "unruled"

# Ordinal scale used ONLY to satisfy comparative antecedents when the caller has
# not supplied explicit magnitudes. Replaces eval_harness_soft_v1._DEPTH_ORDINAL,
# which this module retires.
#   JUSTIFICATION: ordinal only -- it asserts deep > medium > shallow and nothing
#     more. No spacing, no units, no doctrine claim about what "deep" means.
#   SCOPE GUARD: consulted ONLY for condition_type == "comparative", and only when
#     `magnitudes` does not already carry that (feature, attribute). A caller-
#     supplied magnitude always wins.
#   TUNING NOTE: adding a value here changes which side of a comparative wins, so
#     a new token must be placed by a human, never inferred from prose.
_MAGNITUDE_ORDINALS: dict[str, dict[str, int]] = {
    "Depth": {"shallow": 0, "medium": 1, "deep": 2},
}


class PalmSelectError(RuntimeError):
    """Unrecoverable problem in the select path (bad hand_state shape, engine
    failure). LLM and per-rule problems are recorded, not raised."""


def classify_antecedent(ant: Antecedent, *, unruled_policy: str = "hard") -> str:
    """HARD / SOFT for one antecedent. Structural overrides are checked FIRST,
    in a fixed order, so no attribute-level opinion can override the two facts
    that make an antecedent structurally hard."""
    # Override 1: a directed antecedent names a landmark -- hard whatever
    # attribute carries it.
    if ant.relation_target is not None:
        return HARD
    # Override 2: a comparative is COMPUTED by the engine from magnitudes. This
    # is the "interpreted term" CLAUDE.md #23 forbids the LLM from inferring --
    # compute it and feed it, never ask the model which line is stronger.
    if ant.condition_type == "comparative":
        return HARD

    if ant.attribute == "Position":
        if isinstance(ant.value, str) and ant.value.startswith(_POSITION_LANDMARK_PREFIXES):
            return HARD
        return _POSITION_HEIGHT_CLASS

    if ant.attribute in _HARD_ATTRS:
        return HARD
    if ant.attribute in _SOFT_ATTRS:
        return SOFT

    # Unclassified by the partition spec -- routed by explicit policy.
    if unruled_policy == "hard":
        return HARD
    if unruled_policy == "soft":
        return SOFT
    return _UNRULED  # "decline" -> fail closed, recorded in `unmatched`


# ---------------------------------------------------------------------------
# Hand-state normalisation
# ---------------------------------------------------------------------------

def _normalize_hand_state(hand_state: dict) -> tuple[dict, dict, dict]:
    """Accepts either the explicit 3-bucket shape
    {"observation": ..., "magnitudes": ..., "targets": ...} or a bare
    observation mapping {feature: {attribute: value}}, and returns
    (observation, magnitudes, targets) in the shape match() expects.

    Magnitudes for comparative antecedents are DERIVED from ordinal-mappable
    observation values when the caller has not supplied them explicitly --
    a caller-supplied magnitude is never overwritten.
    """
    if not isinstance(hand_state, dict):
        raise PalmSelectError(
            f"hand_state must be a dict, got {type(hand_state).__name__}"
        )

    if any(k in hand_state for k in ("observation", "magnitudes", "targets")):
        observation = hand_state.get("observation") or {}
        magnitudes = hand_state.get("magnitudes") or {}
        targets = hand_state.get("targets") or {}
    else:
        observation, magnitudes, targets = hand_state, {}, {}

    for name, bucket in (("observation", observation), ("magnitudes", magnitudes), ("targets", targets)):
        if not isinstance(bucket, dict):
            raise PalmSelectError(
                f"hand_state[{name!r}] must be a dict of feature -> "
                f"{{attribute: value}}, got {type(bucket).__name__}"
            )

    # Real hand-states carry scalar side-fields alongside the feature blocks
    # (e.g. the C2 probe's "stronger_line": "head"). They are not features, so
    # they are dropped rather than treated as one -- match() would raise on a
    # str where it expects a mapping. Dropped keys are logged, never silent.
    dropped = [f for f, attrs in observation.items() if not isinstance(attrs, dict)]
    if dropped:
        logger.debug(
            "palm_select: ignoring %d non-feature hand_state key(s): %s",
            len(dropped), ", ".join(sorted(dropped)),
        )
        observation = {f: a for f, a in observation.items() if isinstance(a, dict)}

    derived = {f: dict(attrs) for f, attrs in magnitudes.items()}
    for feature, attrs in observation.items():
        for attribute, value in attrs.items():
            scale = _MAGNITUDE_ORDINALS.get(attribute)
            if scale is None or value not in scale:
                continue
            if attribute in derived.get(feature, {}):
                continue  # caller-supplied magnitude wins
            derived.setdefault(feature, {})[attribute] = scale[value]

    return observation, derived, targets


# ---------------------------------------------------------------------------
# STEP 1 -- the hard gate, via production match()
# ---------------------------------------------------------------------------

def _hard_projection(rule: PalmRule, unruled_policy: str) -> tuple[tuple[Antecedent, ...], tuple[Antecedent, ...], tuple[Antecedent, ...]]:
    """Splits a rule's antecedents into (hard, soft, unruled) without altering
    the rule itself."""
    hard, soft, unruled = [], [], []
    for ant in rule.antecedents:
        cls = classify_antecedent(ant, unruled_policy=unruled_policy)
        (hard if cls == HARD else soft if cls == SOFT else unruled).append(ant)
    return tuple(hard), tuple(soft), tuple(unruled)


def _gate(
    rules: Sequence[PalmRule],
    observation: dict,
    magnitudes: dict,
    targets: dict,
    unruled_policy: str,
    features: frozenset[str],
    vocab: dict,
) -> tuple[list[dict], list[dict], list[dict]]:
    """Runs each rule's HARD PROJECTION through the real production match().

    Returns (survivors, gated_out, hard_side_misses). A survivor carries its own
    soft antecedent tuple so step 2 never has to re-derive the partition.

    Fail-closed by construction: any rule whose hard antecedents match() cannot
    satisfy is dropped here, before the LLM sees it.

    A gate-out is ALSO vocabulary-checked. Without that, a rule dropped because
    its feature can never be emitted (e.g. every Quadrangle rule -- nothing in
    the pipeline ever writes a Quadrangle observation) is indistinguishable from
    a rule that legitimately did not match this hand. That is precisely the
    silent miss law #22 exists to surface, so it is reported as one.
    """
    survivors: list[dict] = []
    gated_out: list[dict] = []
    hard_side_misses: list[dict] = []

    for rule in rules:
        hard, soft, unruled = _hard_projection(rule, unruled_policy)

        # unruled_policy="decline": an unclassifiable antecedent fails closed
        # rather than being forced into a bucket.
        if unruled:
            gated_out.append({
                "rule_id": rule.rule_id,
                "reason": "unruled_antecedent",
                "detail": "; ".join(f"{a.feature}.{a.attribute}" for a in unruled),
            })
            continue

        if hard:
            projection = dataclasses.replace(rule, antecedents=hard)
            try:
                fired = match(observation, magnitudes, [projection], targets)
            except Exception as exc:  # noqa: BLE001 -- engine failure must surface named
                raise PalmSelectError(
                    f"palm_rules_table.match() raised while gating {rule.rule_id}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
            if not fired:
                gated_out.append({
                    "rule_id": rule.rule_id,
                    "reason": "hard_antecedents_unsatisfied",
                    "detail": "; ".join(_label(a) for a in hard),
                })
                # Could this rule EVER have matched? A gate-out on an
                # unreachable token is a silent miss, not a non-match.
                for miss in _check_vocabulary(hard, features, vocab):
                    hard_side_misses.append({
                        "rule_id": rule.rule_id, "blocking": False, **miss,
                    })
                continue
        elif rule.verified is not True:
            # match() enforces verified==True for gated rules; a fully-soft rule
            # never reaches match(), so the same fail-closed check is applied here
            # rather than letting an unverified rule slip through to the LLM.
            gated_out.append({
                "rule_id": rule.rule_id,
                "reason": "unverified",
                "detail": "rule.verified is not True",
            })
            continue
        # else: empty hard projection == NO hard constraint == vacuous pass.
        # NOT a gate-out. match() returns [] for an antecedent-less rule
        # (`if rule.antecedents and ...`), so calling it here would silently
        # gate out every FULLY-SOFT rule in the corpus.

        survivors.append({"rule": rule, "hard": hard, "soft": soft})

    return survivors, gated_out, hard_side_misses


def _label(ant: Antecedent) -> str:
    base = f"{ant.feature}.{ant.attribute}"
    if ant.condition_type == "comparative":
        return f"{base} {ant.comparator} {ant.comparator_feature}"
    if ant.relation_target is not None:
        return f"{base}={ant.value or '*'} -> {ant.relation_target}"
    return f"{base}={ant.value}"


# ---------------------------------------------------------------------------
# VOCABULARY GUARD -- CLAUDE.md law #22
# ---------------------------------------------------------------------------

def _emitted_vocabulary() -> tuple[frozenset[str], dict]:
    """(emittable features, closed vocab) as the live extractor defines them.

    Imported lazily and from observation_extractor deliberately: that module is
    the single source of truth for what the pipeline can produce, so this guard
    stays correct if the alias table or the registry grows. `_CLOSED_VOCAB` is
    private there and has no public accessor; reading it is a considered
    coupling, preferable to duplicating the derivation here where it would drift.
    """
    try:
        from agent.interpretive import observation_extractor as oe
        return oe.all_aliased_features(), oe._CLOSED_VOCAB
    except Exception as exc:  # noqa: BLE001
        raise PalmSelectError(
            "vocabulary guard could not read the emitted vocabulary from "
            f"agent.interpretive.observation_extractor: {type(exc).__name__}: {exc}"
        ) from exc


def _check_vocabulary(antecedents: Iterable[Antecedent], features: frozenset[str], vocab: dict) -> list[dict]:
    """Returns one record per antecedent whose trigger token the pipeline can
    never supply. Empty list == every token is reachable."""
    misses: list[dict] = []
    for ant in antecedents:
        if ant.feature not in features:
            misses.append({
                "antecedent": _label(ant),
                "reason": "feature_not_emittable",
                "detail": (
                    f"{ant.feature!r} is not in observation_extractor."
                    "all_aliased_features() -- no vision prose is ever routed to it"
                ),
            })
            continue
        legal = vocab.get(ant.feature, {}).get(ant.attribute)
        if legal is None:
            misses.append({
                "antecedent": _label(ant),
                "reason": "attribute_illegal_for_feature",
                "detail": f"{ant.attribute!r} is not a legal attribute of {ant.feature!r}",
            })
            continue
        if ant.value is not None and ant.value not in legal:
            misses.append({
                "antecedent": _label(ant),
                "reason": "value_not_in_emitted_pool",
                "detail": f"{ant.value!r} is absent from the emitted value pool for {ant.attribute!r}",
            })
    return misses


# ---------------------------------------------------------------------------
# STEP 2 -- whole-sentence LLM select
# ---------------------------------------------------------------------------

# Carried over VERBATIM from scripts/smoke_test_palm_llm_select.py, which scored
# 5/5 clean with no fabrication. This module changes WHAT reaches the model, not
# HOW it is asked -- do not reword without a fresh 5-run no-fabrication check.
_SYSTEM_PROMPT = (
    "You are a rule-evaluation engine for a palmistry system. You will be given "
    "an observed hand's state and, for each rule, its verbatim Cheiro text, id, "
    "page, and involves-tags. Nothing is decomposed for you.\n\n"
    "For each rule, read its full sentence and decide whether its reading "
    "genuinely applies to THIS hand. A rule applies only if the hand matches "
    "everything the sentence requires -- but read the whole sentence, including "
    "phrases like 'even from the finger itself' or 'and vice versa', before "
    "deciding. Evaluate every rule; do not stop early. Fire all that genuinely "
    "apply. Merge the fired readings into one combined interpretation. Quote "
    "each fired rule verbatim. List a feature as unmatched only if no rule "
    "truly covers it.\n\n"
    "Judge each rule ONLY against features explicitly present in the "
    "hand-state. Never introduce, infer, or assert a feature the hand-state "
    "does not contain. If a rule's applicability depends on a feature that is "
    "not stated in the hand-state, do NOT fire it and do NOT mention it. Your "
    "combined_reading may reference ONLY features present in the hand-state -- "
    "do not add origins, lengths, or qualities that were not given.\n\n"
    "Return strict JSON only, matching this shape: "
    '{"fired": [{"id": "<rule_id>", "quote": "<verbatim substring>", "page": <int>}], '
    '"combined_reading": "<string>", "unmatched_features": ["<feature>", ...]}'
)


def _involves(rule: PalmRule) -> list[str]:
    tags = set()
    for ant in rule.antecedents:
        for feat in (ant.feature, ant.comparator_feature):
            if feat == "Line of Head":
                tags.add("head")
            elif feat == "Line of Heart":
                tags.add("heart")
            elif feat == "Line of Life":
                tags.add("life")
            elif feat == "Quadrangle":
                tags.add("quadrangle")
    return sorted(tags) or ["unknown"]


def _build_user_prompt(candidates: list[PalmRule], hand_state: dict) -> str:
    """Rules go to the model as WHOLE verbatim sentences -- source_quote only.
    No antecedent list, no anchors, no benchmarks, no thresholds: the soft
    judgment is the model's to make from the sentence itself."""
    rules_block = json.dumps(
        [
            {
                "id": r.rule_id,
                "involves": _involves(r),
                "text": r.source_quote,
                "page": r.source_page,
            }
            for r in candidates
        ],
        indent=2, ensure_ascii=False,
    )
    return (
        "RULES:\n" + rules_block + "\n\n"
        "OBSERVED HAND STATE:\n" + json.dumps(hand_state, indent=2, ensure_ascii=False) + "\n\n"
        "Decide which rules genuinely apply to this hand and produce the "
        "combined result."
    )


def _call_llm(client, user_prompt: str, model: str, temperature: float) -> str:
    """Single try/except boundary around one API call (CLAUDE.md #6). Raises
    with meaningful context; select() records it and returns rather than
    propagating a bare vendor exception to the caller."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content
    except Exception as exc:  # noqa: BLE001 -- re-raised named, never swallowed
        raise PalmSelectError(
            f"LLM select call failed (model={model!r}): {type(exc).__name__}: {exc}"
        ) from exc


def _default_client():
    """Imported inside the function, never at module level: a module-level
    `from openai import OpenAI` defeats conftest autouse stubbing (a known
    accepted gap on palm_reading.py -- not repeated here)."""
    try:
        from openai import OpenAI
        return OpenAI()
    except Exception as exc:  # noqa: BLE001
        raise PalmSelectError(
            f"could not construct a default OpenAI client: {type(exc).__name__}: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# PRECEDENCE -- RULING 2, applied to the combined fired set
# ---------------------------------------------------------------------------

def _apply_precedence(result: dict, rules: Sequence[PalmRule]) -> dict:
    """Runs the production resolve_priority() over everything that fired,
    gate-path and LLM-path together.

    Deliberately applied to the COMBINED set: a gate-fired specific rule must be
    able to suppress an LLM-fired general one and vice versa. Splitting the two
    paths would let a general rule survive purely because the specific rule that
    defeats it happened to arrive from the other path.

    RULING 2 makes the subset check corpus-wide inside resolve_priority(), so no
    pair logic lives here -- this function only feeds it and records the outcome.

    RULING 3: the outcome is a DEMOTION, not a deletion. Primary rules go to
    fired_ids/quotes; defeated rules go to result["suppressed"] carrying their
    own claim and verbatim quote. Nothing fires twice, nothing vanishes.

    Note: resolve_priority()'s Tier-0 baseline pass also writes to the same
    suppression log, so a demoted baseline rule surfaces here too -- consistent
    with the same "defeated, not deleted" reading.
    """
    by_id = {r.rule_id: r for r in rules}
    fired = [by_id[rid] for rid in result["fired_ids"] if rid in by_id]
    if len(fired) < 2:
        result["fired_ids"] = sorted(set(result["fired_ids"]))
        result.setdefault("suppressed", [])
        return result

    try:
        survivors, suppression_log = resolve_priority(fired)
    except Exception as exc:  # noqa: BLE001 -- engine failure must surface named
        raise PalmSelectError(
            f"palm_rules_table.resolve_priority() raised on the fired set "
            f"{sorted(result['fired_ids'])}: {type(exc).__name__}: {exc}"
        ) from exc

    surviving_ids = {r.rule_id for r in survivors}

    # RULING 3 -- DEMOTE, never DELETE. A suppressed rule is not primary, so it
    # stays out of fired_ids / quotes / combined_reading (that behaviour is
    # unchanged). But its claim and its verbatim source sentence are carried
    # here, so a defeated reading is auditable rather than silently discarded.
    # Deliberately flat: one subset check, one demotion list -- no defeats/
    # refines tags, no third rule class, no per-rule authoring.
    result["suppressed"] = [
        {
            "suppressed_id": loser,
            "by": winner,
            # PalmRule stores the verbatim sentence as `source_quote`; exposed
            # here under the "quote" key the result contract names.
            "claim": by_id[loser].claim if loser in by_id else None,
            "quote": by_id[loser].source_quote if loser in by_id else None,
        }
        for winner, loser in suppression_log
    ]

    result["quotes"] = [q for q in result["quotes"] if q["rule_id"] in surviving_ids]
    result["fired_ids"] = sorted(surviving_ids)
    return result


# ---------------------------------------------------------------------------
# The canonical entry point
# ---------------------------------------------------------------------------

def select(
    hand_state: dict,
    rules: Sequence[PalmRule],
    *,
    model: str = _MODEL,
    temperature: float = _TEMPERATURE,
    client: Any = None,
    unruled_policy: str = "hard",
) -> dict:
    """Hard gate -> vocabulary guard -> whole-sentence soft select.

    Returns:
        {
          "fired_ids": [rule_id, ...],            # gate-fired + LLM-fired
          "quotes": [{"rule_id", "quote", "page", "via"}, ...],
          "combined_reading": str,                 # "" when no LLM step ran
          "gated_out": [{"rule_id", "reason", "detail"}, ...],
          "unmatched": [{"rule_id", "antecedent", "reason", "detail"}, ...],
          "suppressed": [                                      # RULING 2 + 3
              {"suppressed_id", "by", "claim", "quote"}, ...
          ],
        }

    `suppressed` is additive to the 5 keys the API spec names: precedence is part
    of this path, and a caller needs to distinguish "never fired" from "fired but
    defeated by a more specific rule". Per RULING 3 each entry carries the
    demoted rule's own claim and verbatim sentence, so a defeated reading is
    available for audit and is never silently deleted.

    `unmatched` is the silent-miss surface (CLAUDE.md law #22): a rule listed
    there triggers on a token the pipeline can never emit. It is NOT reported as
    a fire.

    Raises:
        PalmSelectError: malformed hand_state, or the production matcher raised.
        A failed LLM call is recorded under the returned "llm_error" key and
        leaves fired_ids holding the gate-fired rules only -- the deterministic
        half of the result survives an LLM outage.
    """
    if unruled_policy not in ("hard", "soft", "decline"):
        raise PalmSelectError(
            f"unruled_policy must be 'hard', 'soft' or 'decline', got {unruled_policy!r}"
        )

    observation, magnitudes, targets = _normalize_hand_state(hand_state)

    result: dict = {
        "fired_ids": [],
        "quotes": [],
        "combined_reading": "",
        "gated_out": [],
        "unmatched": [],
    }

    # The emitted vocabulary is read once and used by BOTH the hard-side
    # advisory inside the gate and the blocking soft-side guard below.
    features, vocab = _emitted_vocabulary()

    # ---- STEP 1: hard gate, via production match() -----------------------
    survivors, gated_out, hard_misses = _gate(
        rules, observation, magnitudes, targets, unruled_policy, features, vocab,
    )
    result["gated_out"] = gated_out
    # Non-blocking: these rules were already dropped by the gate. The record
    # says WHY they could never have fired, so an unreachable-vocabulary
    # gate-out is never mistaken for a legitimate non-match.
    result["unmatched"].extend(hard_misses)

    # A survivor with NO soft antecedent is FULLY-HARD: match() has already
    # decided it. It fires now and never reaches the LLM (CLAUDE.md #23).
    fully_hard = [s for s in survivors if not s["soft"]]
    soft_bearing = [s for s in survivors if s["soft"]]

    for s in fully_hard:
        rule = s["rule"]
        result["fired_ids"].append(rule.rule_id)
        result["quotes"].append({
            "rule_id": rule.rule_id,
            "quote": rule.source_quote,
            "page": rule.source_page,
            "via": "gate",
        })

    # ---- VOCABULARY GUARD (blocking), before the LLM call ----------------
    candidates: list[PalmRule] = []
    for s in soft_bearing:
        misses = _check_vocabulary(s["soft"], features, vocab)
        if misses:
            # Silent miss surfaced, NOT sent onward as a fake fire.
            for miss in misses:
                result["unmatched"].append({
                    "rule_id": s["rule"].rule_id, "blocking": True, **miss,
                })
            continue
        candidates.append(s["rule"])

    if not candidates:
        return result

    # ---- STEP 2: whole-sentence soft select ------------------------------
    llm_client = client if client is not None else _default_client()
    try:
        raw = _call_llm(llm_client, _build_user_prompt(candidates, hand_state), model, temperature)
        parsed = json.loads(raw)
    except PalmSelectError as exc:
        result["llm_error"] = str(exc)
        return result
    except json.JSONDecodeError as exc:
        result["llm_error"] = f"LLM returned non-JSON content: {exc}"
        return result

    by_id = {r.rule_id: r for r in candidates}
    combined = parsed.get("combined_reading", "")
    result["combined_reading"] = combined if isinstance(combined, str) else ""

    fired = parsed.get("fired", [])
    if not isinstance(fired, list):
        fired = []

    for item in fired:
        # Verbatim-quote guard, unchanged from the proven smoke test: an id
        # outside the candidate pool, or a quote that is not a literal substring
        # of that rule's own source_quote, is a fabrication and is dropped.
        if not isinstance(item, dict):
            result["unmatched"].append({
                "rule_id": None, "antecedent": None,
                "reason": "llm_returned_non_object", "detail": repr(item),
            })
            continue
        rid = item.get("id")
        quote = item.get("quote")
        rule = by_id.get(rid)
        if rule is None:
            result["unmatched"].append({
                "rule_id": rid, "antecedent": None,
                "reason": "llm_fired_id_outside_candidate_pool", "detail": repr(item),
            })
            continue
        if not isinstance(quote, str) or not quote or quote not in rule.source_quote:
            result["unmatched"].append({
                "rule_id": rid, "antecedent": None,
                "reason": "quote_not_verbatim_substring_of_source", "detail": repr(quote),
            })
            continue
        result["fired_ids"].append(rid)
        result["quotes"].append({
            "rule_id": rid, "quote": quote, "page": rule.source_page, "via": "llm",
        })

    return _apply_precedence(result, rules)
