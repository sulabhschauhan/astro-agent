"""
agent/interpretive/observation_extractor.py
Converts the live pipeline's per-feature PROSE (`palm_reading._gather_
feature_texts`'s `{feature: [raw_text, ...]}` shape -- 10 prose labels,
`palm_reading._FEATURE_REGISTRY`) into an `ObservationRecord`: a CAPTURE-
COMPLETE structured record of everything the LLM observed, with
FILTERING (ontology-vocabulary validity, feature enablement) applied as
explicit, separately-inspectable steps rather than baked into silent
drops.

Standalone, dependency-free module (stdlib + a lazily-imported `openai`
client only) -- does NOT import palm_reading.py, palm_rules_table.py, or
any engine file; not wired into any of them by this task.

CONTRACT:
    extract_observation(feature_texts, *, enabled_features=None,
                         model="gpt-4o-mini") -> ObservationRecord
    to_vision_payload(record, enabled_features=None) -> dict
        (the {feature: {attribute: {value, confidence}}} shape
        `observation_to_tokens.to_tokens()` consumes -- unchanged seam)

WHY THIS RESTRUCTURE (per the instructing prompt): the prior version only
ever emitted tokens that matched a closed-vocabulary value and silently
dropped everything else -- both real observations the LLM made that just
didn't happen to hit an ontology token (e.g. life-line "curves around
the base of the thumb"), and any LLM protocol violation (out-of-
vocabulary emission). A silent result was undiagnosable: "the LLM didn't
see it" and "the extractor dropped it" were indistinguishable from the
caller's side. This version captures BOTH categories -- valid tokens
(`tokens`) and everything else the LLM reported but couldn't be
tokenized (`unmapped`) -- and keeps feature enablement (`enabled_features`)
as a separate, later filtering step over the SAME fully-captured record,
via `dropped_disabled` + the `to_vision_payload` adapter.

=== Discrepancies / deliberate deviations from this task's own prompt ===
(flagged per project convention -- verify prompts against code, don't
silently paper over a mismatch)

1. DEVIATION -- kept the `client=None` keyword-only parameter from the
   prior version, not in this task's literal contract either. Same
   reason as before: this codebase's established `client=` injection
   seam (`claim_extraction.extract_claims`) is what makes an LLM-calling
   function testable without a live API key via a LAZY `from openai
   import OpenAI` import inside the function body -- `palm_reading.py`'s
   own S65 flag (b) documents a module-level `OpenAI` import as a known
   anti-pattern. Omitting this seam would make this task's own "MOCK the
   LLM" test requirement impossible to satisfy. Backward compatible for
   any caller using only `feature_texts`/`enabled_features`/`model`.

2. Python-side fold-in of rejected `observations` entries into
   `unmapped`, not just silent drop. The task's `unmapped` contract
   describes qualities the LLM reports via a NEW dedicated response
   field for things it could not tokenize -- that is the PRIMARY path
   into `unmapped` here. But per rule 1's "fail-closed there" (never
   coerce a near-miss `observations` entry into a token), a value that
   fails the closed-vocabulary guard, an attribute that isn't valid for
   the feature, or a malformed entry shape must still never enter
   `tokens`. Rather than reintroduce the OLD silent-drop-and-log-only
   behavior for THIS class of rejection (which would recreate exactly
   the undiagnosability problem this restructure exists to fix), these
   rejects are ALSO folded into that feature's `unmapped` list (with
   `attribute_guess` set to whatever attribute key the LLM associated
   with the rejected value, however invalid). This is an interpretation
   choice beyond the task's literal wording, made to keep "capture is
   total" true for BOTH the new dedicated-field path and the pre-
   existing rejection path, rather than leaving the old path as a silent
   exception to the new rule.

3. Unmappable PROSE features (`fingers`, `markings/other features` --
   the two `_FEATURE_ALIAS` entries with no ontology counterpart at all)
   are recorded in a SEPARATE `ObservationRecord.unmappable_prose_features`
   list, not merged into `dropped_disabled`. The task's rule 4 says to
   "LOG them in dropped_disabled-style record" -- read here as "give them
   the same visibility treatment," not "put them in the literal same
   list," because the two exclusion reasons are categorically different:
   `dropped_disabled` is ontology features the allow-list excluded
   AFTER a real extraction attempt; these two never had an ontology
   feature to extract into at all (no VALID ATTRIBUTES list exists for
   them, so they are never sent to the LLM, and never gain a `raw_prose`
   captured under an ontology-feature key). Conflating the two would let
   a caller mistake "not sent to the LLM this call" for "sent, extracted,
   and only withheld downstream," which are different failure classes a
   reviewer needs to tell apart.

4. `attribute_guess` (both LLM-reported and Python-folded-in) is NOT
   validated against the feature's real VALID ATTRIBUTES list -- it is
   coerced to `None` only if it isn't a string at all, never checked for
   membership. It is a diagnostic hint, never consumed by `to_tokens()`
   or anything downstream of `to_vision_payload`; validating it would add
   a rejection path for a field whose entire purpose is showing what the
   model GUESSED, including wrong guesses.

5. Closed-vocabulary construction (`_CLOSED_VOCAB`) is now BINDING-AWARE,
   with the flat pool as the fallback. The registry's
   `attribute_value_binding` block (added 2026-08-08) names, per
   attribute, the narrow value set that attribute may take. For any
   attribute that HAS a binding, both the Python guard (`_CLOSED_VOCAB`)
   and the per-feature prompt block (`_build_user_prompt`'s VALUE
   CONSTRAINTS line) use that narrow set. For any attribute WITHOUT a
   binding, behavior is byte-identical to the prior version: the flat
   union of every values-category list (`_ALL_VALUES`) is the valid pool,
   per `observation_to_tokens.py`'s own docstring point 3, since the
   registry supplies no narrower binding for it and real verified rules
   need cross-category value use to validate at all.

   WHY: the flat pool let a generic near-token win over the specific one
   when both live in the same category. Measured (dogfood
   2026-08-08T23:10:58, Athira): head-line prose "...slightly sloping
   downward toward the wrist..." -> the model emitted Slope="sloping",
   the flat guard accepted it, and H_026 (antecedent Slope="downward",
   exact match) never fired. `attribute_value_binding.Slope =
   [upward, downward, straight]` removes "sloping" from Slope's legal
   set in BOTH the prompt and the guard, leaving "downward" as the only
   legal Slope token the prose supports.

   The GLOBAL ALLOWED VALUE VOCABULARY block in the system prompt is
   deliberately left as the full flat pool -- it is the vocabulary for
   every UNBOUND attribute, and the per-attribute VALUE CONSTRAINTS line
   overrides it only for the bound ones, so unbound-attribute guidance is
   unchanged.

6. Confidence is computed ENTIRELY in Python from source-prose hedge-word
   detection (`_confidence_for_text`), never read from the LLM's own
   output -- the system prompt tells the model to omit it. Deliberate
   reading of CLAUDE.md's NO ANCHORED JUDGMENT rule (#9): token
   extraction is the LLM's independent observation; confidence is a
   SEPARATE deterministic Python judgment over the same source text.
   Coarseness accepted: hedging is detected per-FEATURE (the whole
   feature's joined prose), not per-attribute-clause. `_HEDGE_CONFIDENCE
   =0.6` remains an UNMEASURED placeholder (THRESHOLD DISCIPLINE,
   CLAUDE.md Working Style #4) -- unchanged from the prior version, not
   re-derived by this restructure.

7. Top-level response parsing keeps an ASYMMETRIC raise policy: a
   JSON-decode failure or a missing/malformed top-level `"observations"`
   object still raises ValueError (unrecoverable -- nothing in this call
   can be trusted). A missing or malformed top-level `"unmapped"` object
   does NOT raise -- it is treated as empty and logged. Rationale: the
   NEW `unmapped` field is additive diagnostic surface; an older or
   partially-compliant LLM response that only returns `"observations"`
   should still produce a usable (if less diagnostic) record rather than
   fail the whole batch over the field this restructure is adding.

8. This is a BREAKING return-type change (`ObservationRecord`, not the
   old `vision_payload` dict) that `palm_reading._prepare_claims_from_
   rules` still calls expecting the OLD dict contract directly (it
   passes `extract_observation(...)`'s return straight into
   `observation_to_tokens.to_tokens()`, which requires a dict). Per this
   task's own explicit instruction, `palm_reading.py` is NOT touched
   here -- this is a report-first restructure of this module only. The
   integration break is real and immediate on the deterministic
   rule-engine path (`_DETERMINISTIC_RULES_ENABLED=True`): `to_tokens()`
   will raise `ValueError` on a non-dict input, which
   `_prepare_claims_from_rules`'s own broad `except Exception` catches
   and turns into its existing fail-closed zero-claims behavior -- so
   nothing crashes, but the deterministic path silently produces zero
   claims until a follow-up task rewires that call site through
   `to_vision_payload()`. Flagged here, not fixed here.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openai import OpenAI  # noqa: F401

logger = logging.getLogger(__name__)

_DEFAULT_REGISTRY_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "ontology_registry.json"
)

_REGISTRY = json.loads(_DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8"))

# attribute -> frozenset of feature names that attribute is valid for.
# Straight from the registry's own attribute_feature_mapping.
_ATTRIBUTE_FEATURE_MAP: dict[str, frozenset[str]] = {
    attribute: frozenset(features)
    for attribute, features in _REGISTRY["attribute_feature_mapping"].items()
}

# Flattened, sorted union of every values-category list -- see module
# docstring point 5 for why this is a flat, attribute-independent pool
# rather than a per-attribute split.
_ALL_VALUES: tuple[str, ...] = tuple(sorted(
    {value for value_list in _REGISTRY["values"].values() for value in value_list}
))
_ALL_VALUES_SET: frozenset[str] = frozenset(_ALL_VALUES)

_ALL_ONTOLOGY_FEATURES: frozenset[str] = frozenset(
    f for category in _REGISTRY["features"].values() for f in category
)


def _load_attribute_value_binding() -> dict[str, tuple[str, ...]]:
    """attribute -> narrow tuple of the ONLY values that attribute may
    take, from the registry's OPTIONAL `attribute_value_binding` block
    (module docstring point 5). An attribute absent from this map falls
    back to `_ALL_VALUES` everywhere -- the block is additive, and a
    registry without it reproduces the pre-binding behavior exactly.

    Fail-closed on a MALFORMED block (present but not an object, or an
    entry that isn't a non-empty list of strings) rather than silently
    dropping the narrowing: a binding that quietly reverts to the flat
    pool is exactly the undiagnosable-silence class this module exists to
    remove. A binding value that isn't in the global value pool is
    LOGGED, not rejected -- it stays legal for that attribute (the
    per-attribute VALUE CONSTRAINTS prompt line still names it), but it
    would never appear in the GLOBAL ALLOWED VALUE VOCABULARY block, so
    the mismatch is worth surfacing.
    """
    raw = _REGISTRY.get("attribute_value_binding")
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError(
            "observation_extractor: ontology_registry.json's "
            "'attribute_value_binding' is present but is not an object "
            f"(got {type(raw).__name__}) -- refusing to fall back silently "
            "to the flat value pool."
        )
    binding: dict[str, tuple[str, ...]] = {}
    for attribute, values in raw.items():
        if (
            not isinstance(values, list)
            or not values
            or not all(isinstance(v, str) and v for v in values)
        ):
            raise ValueError(
                "observation_extractor: ontology_registry.json's "
                f"'attribute_value_binding[{attribute!r}]' must be a non-empty "
                f"list of strings -- got {values!r}."
            )
        orphans = [v for v in values if v not in _ALL_VALUES_SET]
        if orphans:
            logger.info(
                "observation_extractor: attribute_value_binding[%r] names value(s) "
                "%r absent from the registry's global value pool -- kept as legal "
                "for this attribute, but they are not in the GLOBAL ALLOWED VALUE "
                "VOCABULARY prompt block.", attribute, orphans,
            )
        binding[attribute] = tuple(values)
    return binding


try:
    _ATTRIBUTE_VALUE_BINDING: dict[str, tuple[str, ...]] = _load_attribute_value_binding()
except ValueError:
    raise
except Exception as exc:  # noqa: BLE001 -- re-raised immediately, named, not swallowed
    raise RuntimeError(
        "observation_extractor: failed to read 'attribute_value_binding' from "
        f"{_DEFAULT_REGISTRY_PATH}: {exc}"
    ) from exc


def _values_for_attribute(attribute: str) -> tuple[str, ...]:
    """The legal value tuple for `attribute`: its narrow binding if the
    registry declares one, else the flat `_ALL_VALUES` pool (module
    docstring point 5). Single source of truth for BOTH the Python guard
    (`_build_closed_vocab`) and the prompt (`_build_user_prompt`), so the
    two can never disagree about what a bound attribute may emit."""
    return _ATTRIBUTE_VALUE_BINDING.get(attribute, _ALL_VALUES)


def _build_closed_vocab() -> dict[str, dict[str, tuple[str, ...]]]:
    """Per ontology feature -> {attribute: (value, ...)}, built once at
    module load. An attribute's value tuple is its narrow
    `attribute_value_binding` set when the registry declares one, else
    the flat `_ALL_VALUES` (see module docstring point 5) -- the dict
    shape is what both the Python-side fail-closed guard and the
    per-feature prompt block key off of."""
    vocab: dict[str, dict[str, tuple[str, ...]]] = {}
    for feature in _ALL_ONTOLOGY_FEATURES:
        attrs = {
            attribute: _values_for_attribute(attribute)
            for attribute, features in _ATTRIBUTE_FEATURE_MAP.items()
            if feature in features
        }
        if attrs:
            vocab[feature] = attrs
    return vocab


_CLOSED_VOCAB: dict[str, dict[str, tuple[str, ...]]] = _build_closed_vocab()

# The 10 palm_reading._FEATURE_REGISTRY prose labels -> canonical
# ontology_registry.json feature token. Hardcoded (not derived from the
# registry's `synonyms` block, which covers a different vocabulary --
# alternate NAMES for the same canonical feature, not this module's
# prose-label-to-canonical-feature mapping). Two of the ten have NO
# ontology counterpart and map to None -- captured as unmappable prose
# (see `ObservationRecord.unmappable_prose_features`), never raised:
#   - "fingers": the registry only models individual First/Second/Third/
#     Fourth Finger features (`features["fingers"]`), no generic plural
#     "Fingers" feature to hold a whole-hand finger observation.
#   - "markings/other features": the registry models individual sign
#     types (Star, Cross, Island, Square, ... under `features["signs"]`),
#     no generic "Markings"/"Other Features" feature exists to map onto.
_FEATURE_ALIAS: dict[str, str | None] = {
    "life line": "Line of Life",
    "head line": "Line of Head",
    "heart line": "Line of Heart",
    "fate line": "Line of Fate",
    "sun line": "Line of Sun",
    "thumb": "Thumb",
    "fingers": None,
    "mount of venus": "Mount of Venus",
    "mount of jupiter": "Mount of Jupiter",
    "markings/other features": None,
}


def all_aliased_features() -> frozenset[str]:
    """Every ontology feature this module can ever produce a token for --
    the non-None value set of `_FEATURE_ALIAS` (Line of Life/Head/Heart/
    Fate/Sun, Thumb, Mount of Venus, Mount of Jupiter). A caller that wants
    to unblock every LLM-observable feature into `extract_observation`'s
    `enabled_features` allow-list (rather than a narrower, e.g. rule-
    derived, allow-list) should derive it from here, never hardcode the
    list at the call site -- this is the single source of truth for what
    the extraction call can produce, and stays correct if `_FEATURE_ALIAS`
    ever grows a new mapped feature."""
    return frozenset(f for f in _FEATURE_ALIAS.values() if f is not None)


# ─── Relational targets -- directed antecedent parsing (S89 -> S90 wiring) ──
# Parses the vision RELATIONAL block palm_processor.describe_palm_image
# emits for HEAD/HEART/FATE (ORIGIN / PROXIMITY <degree> to <landmark> /
# TERMINATION / BRANCHES_TO) into the `{feature: {attribute: landmark}}`
# shape palm_rules_table.match()'s `targets` param already accepts and
# consults for any antecedent whose own relation_target is not None. INERT
# on the currently-loaded rule set: no loaded rule sets a relation_target,
# so this dict is built and threaded through but never actually consulted
# yet -- proving the vision->extractor->engine path ahead of the migration
# that will add the first directed rule.
#
# Deliberately separate from extract_observation()'s LLM-mediated token
# extraction: this is a pure deterministic string parse of the vision
# model's OWN raw output, no LLM call, no closed-vocabulary value/pool/
# binding involved (module docstring point 5 governs VALUES only; this
# governs relation_target landmarks, a disjoint axis on the SAME line
# attributes -- Starting_Point/Position/Proximity/Branching already exist
# in the registry's line_attributes for VALUE emission elsewhere).

_RELATION_TARGET_REGISTRY: frozenset[str] = frozenset(
    _REGISTRY.get("relation_target_registry", [])
)

# HEAD/HEART/FATE line -> ontology feature, narrowed from _FEATURE_ALIAS
# (single source of truth) to the 3 features palm_processor's RELATIONAL
# block actually emits -- life/sun lines and every non-line feature never
# carry a RELATIONAL block, so they are intentionally absent here even
# though _FEATURE_ALIAS maps them too.
_RELATIONAL_LINE_ALIAS: dict[str, str] = {
    "head line": _FEATURE_ALIAS["head line"],
    "heart line": _FEATURE_ALIAS["heart line"],
    "fate line": _FEATURE_ALIAS["fate line"],
}

# RELATIONAL sub-field label -> the line_attribute it targets. Degree
# (PROXIMITY's "<degree> to") is NOT captured by this map -- S89 finding:
# proximity_degree is a dead axis (model says "medium" universally, no
# signal); only the target landmark carries signal here. The degree token
# is separately captured as an observation VALUE (not routed through this
# map, not bound to any registry attribute yet) by
# extract_proximity_observations() below -- captured deterministically in
# case it later proves to carry signal on some feature/hand, but S89's
# dead-axis finding stands unless re-measured.
_RELATIONAL_ATTRIBUTE_MAP: dict[str, str] = {
    "ORIGIN": "Starting_Point",
    "PROXIMITY": "Proximity",
    "TERMINATION": "Position",
    "BRANCHES_TO": "Branching",
}

_RELATIONAL_HEADER = re.compile(r"^([A-Z][A-Z ]*) RELATIONAL:\s*$")

# Second, inline format: the primary line/section headers themselves
# (e.g. "HEAD LINE: present, deep"), for vision output that places
# ORIGIN/TERMINATION/etc. directly under the line's own header instead of
# a separate "<LINE> RELATIONAL:" block. Disjoint from _RELATIONAL_SUBFIELD's
# label set (ORIGIN/PROXIMITY/TERMINATION/BRANCHES_TO/SLOPE) by construction
# -- none of those subfield words appear in this alternation -- so a
# subfield line can never be mistaken for a section header or vice versa.
_LINE_HEADER = re.compile(
    r"^(HAND SHAPE|FINGERS|THUMB|LIFE LINE|HEAD LINE|HEART LINE|FATE LINE"
    r"|OTHER LINES|MARKS):"
)

_RELATIONAL_SUBFIELD = re.compile(
    r"^(ORIGIN|PROXIMITY|TERMINATION|BRANCHES_TO):\s*(.*)$"
)


def _proximity_landmark(value: str) -> str:
    """PROXIMITY's raw value is '<degree> to <landmark>' -- returns just
    the landmark half, dropping the degree (see module note above). A
    value with no ' to ' separator (malformed) is returned as-is and will
    simply fail the registry-membership check in
    extract_relational_targets."""
    if " to " in value:
        return value.split(" to ", 1)[1].strip()
    return value.strip()


# Closed set for the degree half of PROXIMITY ("<degree> to <landmark>") --
# the vision prompt's own contract (agent/palm_processor.py) states degree
# is exactly one of {touching, medium, distant, n/a}. 'n/a' is deliberately
# excluded here: it means "no proximity relation applies", not an observed
# degree value -- honest silence, not a token to emit.
_PROXIMITY_DEGREE_VALUES: frozenset[str] = frozenset({"touching", "medium", "distant"})


def _proximity_degree(value: str) -> str | None:
    """PROXIMITY's raw value is '<degree> to <landmark>' -- returns just
    the degree half (mirrors _proximity_landmark, which returns the
    landmark half). Returns None if there's no ' to ' separator (malformed
    -- unlike _proximity_landmark's as-is fallback, a degree half that
    can't be isolated can't be validated against the closed set below, so
    there is nothing safe to return)."""
    if " to " in value:
        return value.split(" to ", 1)[0].strip()
    return None


def extract_relational_targets(raw_text: str) -> dict[str, dict[str, str]]:
    """Parses ONE vision description string's HEAD/HEART/FATE LINE
    RELATIONAL blocks into `{ontology_feature: {attribute: landmark}}` --
    the shape palm_rules_table.match()'s `targets` param consumes. Accepts
    either the separate "<LINE> RELATIONAL:" header format or the inline
    format (subfields directly under the line's own "<LINE>:" header).

    Fail-closed per landmark, not per call: a landmark that is 'none',
    'n/a', empty, malformed, or simply not a `relation_target_registry`
    member is DROPPED (that attribute key is omitted entirely) rather
    than coerced to a nearest match or a sentinel -- mirroring
    _build_features_from_response's closed-vocabulary discipline for
    VALUE tokens, applied here to relation targets instead. A feature
    with no accepted landmarks at all is simply absent from the returned
    dict. Does NOT emit any observation VALUE token -- value/pool/binding
    changes belong to the migration this wiring precedes.

    Never raises for a missing/malformed RELATIONAL block (the common
    case for input that doesn't carry one at all -- e.g. hand_detail's
    freeform prose, which never carries this block) -- returns {} in that
    case, same as "no signal" anywhere else in this module.
    """
    if not isinstance(raw_text, str):
        raise TypeError(
            "observation_extractor.extract_relational_targets: raw_text "
            f"must be a str, got {type(raw_text).__name__}"
        )

    targets: dict[str, dict[str, str]] = {}
    current_feature: str | None = None

    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            current_feature = None
            continue

        header = _RELATIONAL_HEADER.match(stripped)
        if header:
            line_label = header.group(1).strip().lower()
            current_feature = _RELATIONAL_LINE_ALIAS.get(line_label)
            continue

        line_header = _LINE_HEADER.match(stripped)
        if line_header:
            line_label = line_header.group(1).strip().lower()
            # .get() returns None for non-relational sections (LIFE LINE,
            # MARKS, etc.) -- this both switches current_feature on for
            # head/heart/fate and resets it on any other section, so a
            # later non-relational section's subfields (e.g. LIFE LINE's
            # own "ORIGIN:") never bleed into the prior relational feature.
            current_feature = _RELATIONAL_LINE_ALIAS.get(line_label)
            continue

        if current_feature is None:
            continue

        sub = _RELATIONAL_SUBFIELD.match(stripped)
        if not sub:
            continue

        field, raw_value = sub.group(1), sub.group(2).strip()
        landmark = _proximity_landmark(raw_value) if field == "PROXIMITY" else raw_value
        if landmark not in _RELATION_TARGET_REGISTRY:
            logger.info(
                "observation_extractor.extract_relational_targets: dropped "
                "feature=%r field=%r landmark=%r -- not in "
                "relation_target_registry (or 'none'/'n/a').",
                current_feature, field, landmark,
            )
            continue

        attribute = _RELATIONAL_ATTRIBUTE_MAP[field]
        targets.setdefault(current_feature, {})[attribute] = landmark

    return targets


def extract_proximity_observations(raw_text: str) -> dict[str, dict[str, dict[str, object]]]:
    """Parses ONE vision description string's HEAD/HEART/FATE LINE
    PROXIMITY subfields (same header detection as extract_relational_targets
    -- both the separate "<LINE> RELATIONAL:" format and the inline
    "<LINE>:" format) into `{ontology_feature: {"Proximity": {"value":
    <degree>, "confidence": 1.0}}}`.

    Deliberately separate from extract_relational_targets: that function
    owns PROXIMITY's landmark half (-> targets[feature]["Proximity"]) and
    is UNCHANGED by this addition -- this function owns the DEGREE half
    only, previously discarded entirely (see the _RELATIONAL_ATTRIBUTE_MAP
    comment above). Does NOT bind attribute_value_binding and does NOT
    touch the registry -- bind-last law, a separate future step.

    Fail-closed per degree, not per call: a degree that is 'n/a', missing
    (no ' to ' separator), or not one of {touching, medium, distant} is
    DROPPED -- no "Proximity" entry is written for that feature, rather
    than invented or coerced. A feature with no accepted degree is simply
    absent from the returned dict.

    Never raises for a missing/malformed PROXIMITY subfield or an
    unparseable raw_text -- returns {} in that case, same as "no signal"
    anywhere else in this module.
    """
    if not isinstance(raw_text, str):
        raise TypeError(
            "observation_extractor.extract_proximity_observations: raw_text "
            f"must be a str, got {type(raw_text).__name__}"
        )

    observations: dict[str, dict[str, dict[str, object]]] = {}
    current_feature: str | None = None

    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            current_feature = None
            continue

        header = _RELATIONAL_HEADER.match(stripped)
        if header:
            line_label = header.group(1).strip().lower()
            current_feature = _RELATIONAL_LINE_ALIAS.get(line_label)
            continue

        line_header = _LINE_HEADER.match(stripped)
        if line_header:
            line_label = line_header.group(1).strip().lower()
            current_feature = _RELATIONAL_LINE_ALIAS.get(line_label)
            continue

        if current_feature is None:
            continue

        sub = _RELATIONAL_SUBFIELD.match(stripped)
        if not sub:
            continue

        field, raw_value = sub.group(1), sub.group(2).strip()
        if field != "PROXIMITY":
            continue

        try:
            degree = _proximity_degree(raw_value)
        except Exception as exc:  # noqa: BLE001 -- never a bare traceback for a parse slip
            logger.info(
                "observation_extractor.extract_proximity_observations: failed "
                "splitting PROXIMITY value %r for feature=%r: %s",
                raw_value, current_feature, exc,
            )
            continue

        if degree not in _PROXIMITY_DEGREE_VALUES:
            logger.info(
                "observation_extractor.extract_proximity_observations: dropped "
                "feature=%r degree=%r -- not in {touching, medium, distant} "
                "(or 'n/a'/missing).",
                current_feature, degree,
            )
            continue

        observations.setdefault(current_feature, {})["Proximity"] = {
            "value": degree, "confidence": 1.0,
        }

    return observations


def merge_relational_targets(
    *target_dicts: dict[str, dict[str, str]]
) -> dict[str, dict[str, str]]:
    """Merges multiple extract_relational_targets() outputs (e.g. one per
    hand image) into one targets dict. Later args win on a per-(feature,
    attribute) collision -- callers passing (left, right) get right-hand
    priority on conflict. Documented as a real behavioral choice (there is
    no established convention for this axis yet), not an accident of
    dict.update order."""
    merged: dict[str, dict[str, str]] = {}
    for targets in target_dicts:
        for feature, attrs in targets.items():
            merged.setdefault(feature, {}).update(attrs)
    return merged


# ─── Confidence -- prose hedge-word detection (module docstring point 6) ──

_HEDGE_WORDS: tuple[str, ...] = (
    "slightly", "somewhat", "possibly", "perhaps", "faintly", "rather",
    "seemingly", "may be", "might be", "appears to be", "a bit", "barely",
)
_HEDGE_CONFIDENCE = 0.6  # UNMEASURED placeholder -- see docstring point 6.
_DEFAULT_CONFIDENCE = 1.0


def _confidence_for_text(text: str) -> float:
    lowered = text.lower()
    if any(hedge in lowered for hedge in _HEDGE_WORDS):
        return _HEDGE_CONFIDENCE
    return _DEFAULT_CONFIDENCE


# ─── The capture-complete record ──────────────────────────────────────


@dataclass
class FeatureObservation:
    """One ontology feature's full captured observation. `tokens` is the
    closed-vocabulary-valid subset (what the old module returned
    entirely); `unmapped` is everything else the LLM reported for this
    feature that didn't become a token (see module docstring point 2 for
    the two paths that feed it); `raw_prose` is always the original
    joined source text, independent of what the LLM returned."""
    tokens: dict[str, dict[str, object]] = field(default_factory=dict)
    unmapped: list[dict[str, object]] = field(default_factory=list)
    raw_prose: str = ""


@dataclass
class ObservationRecord:
    """The full capture for one `extract_observation()` call.

    features: every ontology feature that had non-empty prose this call
        -- ALWAYS fully populated (tokens + unmapped + raw_prose)
        regardless of `enabled_features`; participation is filtered
        downstream, not at capture time (module docstring / task rule 2).
    dropped_disabled: ontology feature names present in `features` that
        `enabled_features` excluded -- empty if `enabled_features` was
        None (no allow-list = nothing excluded).
    unmappable_prose_features: prose feature labels with NO ontology
        counterpart at all (`_FEATURE_ALIAS` -> None) -- see module
        docstring point 3 for why these are kept separate from
        `dropped_disabled` rather than merged into it.
    extraction_retries: incompleteness-guard summary for this call (see
        `_compute_dropped_features` / the retry loop in
        `extract_observation`) -- {"attempts_made": int, "retried": bool,
        "dropped_per_attempt": [{"attempt": int, "dropped": [str, ...]},
        ...], "final_dropped": [str, ...]}. Empty dict when no LLM call
        was made at all (empty `feature_texts`). A caller (e.g. the
        dogfood capture) can attach this verbatim for retry visibility.
    """
    features: dict[str, FeatureObservation] = field(default_factory=dict)
    dropped_disabled: list[str] = field(default_factory=list)
    unmappable_prose_features: list[dict[str, str]] = field(default_factory=list)
    extraction_retries: dict[str, object] = field(default_factory=dict)


# ─── LLM system prompt -- global value vocabulary embedded once ──────────

_GLOBAL_VALUE_TOKENS_BLOCK = ", ".join(_ALL_VALUES)

_EXTRACTION_SYSTEM_PROMPT = f"""You are a structured-observation extraction engine for a palmistry vision pipeline. You are given one or more observed hand features, each with its raw descriptive prose (a vision model's free-text description of a photographed hand) and, for that exact feature, a list of the ONLY attribute names you may report on.

GLOBAL ALLOWED VALUE VOCABULARY (the ONLY value tokens you may ever emit into "observations", for ANY attribute, ANY feature):
{_GLOBAL_VALUE_TOKENS_BLOCK}

Your job has TWO parts for each given feature, read its prose and:
(A) Decide which (attribute, value) pairs it actually states or clearly implies, using ONLY attributes from that feature's own "VALID ATTRIBUTES" list and ONLY values from the GLOBAL ALLOWED VALUE VOCABULARY above -- these go into "observations".
(B) For any OTHER quality the prose actually states that you could NOT represent as a valid (attribute, value) pair -- because no listed value matches it, or it isn't about any of the feature's VALID ATTRIBUTES -- report it into "unmapped" instead of discarding it. Quote or closely paraphrase the prose fragment as "quality". If you can tell which of the feature's VALID ATTRIBUTES this quality is probably about, set "attribute_guess" to that attribute name; otherwise set it to null. Do not repeat in "unmapped" a quality you already represented in "observations".

STRICT RULES:
1. Closed vocabulary only for "observations": a value token must appear VERBATIM in the GLOBAL ALLOWED VALUE VOCABULARY. If the prose describes a quality that does not match any listed value, do NOT force it into "observations" -- put it in "unmapped" instead. Never choose the nearest token, never guess, never invent a token that is not listed.
2. An attribute in "observations" must come from the specific feature's own "VALID ATTRIBUTES" list -- never borrow an attribute listed only for a different feature.
3. If a feature's prose states nothing at all worth reporting (neither a valid observation nor an unmapped quality), omit that feature from both objects, or emit empty entries for it.
4. Do not include a "confidence" field anywhere -- it is computed separately, outside this call.
5. Return ONLY a single JSON object, no prose or markdown outside it, matching exactly:
{{"observations": {{"<feature>": {{"<attribute>": {{"value": "<token>"}}}}}}, "unmapped": {{"<feature>": [{{"quality": "<prose fragment>", "attribute_guess": "<attribute name or null>"}}]}}}}
Empty is a valid response: {{"observations": {{}}, "unmapped": {{}}}}."""


def _build_user_prompt(entries: list[tuple[str, str, str]]) -> str:
    """entries: list of (prose_feature_label, ontology_feature, joined_text)
    -- prose_feature_label is included only for readability, never parsed
    back out of the model's response."""
    blocks = []
    for _prose_feature, ontology_feature, text in entries:
        valid_attributes = sorted(_CLOSED_VOCAB.get(ontology_feature, {}))
        block = (
            f"FEATURE: {ontology_feature}\n"
            f"PROSE: {text}\n"
            f"VALID ATTRIBUTES FOR THIS FEATURE: {', '.join(valid_attributes)}"
        )
        # Per-attribute narrowing, emitted ONLY for attributes the registry
        # actually binds (module docstring point 5). An unbound attribute
        # gets no line here at all, so its guidance stays exactly what it
        # was before bindings existed: the GLOBAL ALLOWED VALUE VOCABULARY
        # block in the system prompt.
        constrained = [a for a in valid_attributes if a in _ATTRIBUTE_VALUE_BINDING]
        if constrained:
            constraint_lines = "; ".join(
                f"{a}: {', '.join(_ATTRIBUTE_VALUE_BINDING[a])}" for a in constrained
            )
            block += (
                "\nVALUE CONSTRAINTS (choose only from these for the named "
                f"attribute, overriding the global vocabulary): {constraint_lines}"
            )
        blocks.append(block)
    return "\n\n".join(blocks) + "\n\nExtract observations per your instructions."


def _call_llm(client, model: str, messages: list[dict], ontology_features: list[str]) -> str:
    """Single try/except boundary around the one API call this module ever
    makes. A failure here is re-raised as a RuntimeError naming the whole
    feature batch this call was for -- never swallowed into a silent
    empty result."""
    start = time.monotonic()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
            response_format={"type": "json_object"},
            # timeout=60s: single-JSON extraction on gpt-4o-mini runs 2-8s typical;
            # 60s catches genuine hangs without false-aborting a slow-but-alive call.
            # Scope guard: env-overridable. Tuning note: log elapsed to calibrate.
            timeout=float(os.getenv("ASTRO_EXTRACT_TIMEOUT_S", "60")),
            # max_tokens=1500: well-formed response for <=10 features is a few hundred
            # tokens; 1500 caps runaway generation. If hit mid-JSON, _parse_response
            # raises ValueError -> existing fail-closed decline path (correct).
            max_tokens=int(os.getenv("ASTRO_EXTRACT_MAX_TOKENS", "1500")),
        )
    except Exception as exc:  # noqa: BLE001 -- re-raised immediately, named, not swallowed
        raise RuntimeError(
            "observation_extractor.extract_observation: LLM call failed for feature "
            f"batch {sorted(ontology_features)}: {exc}"
        ) from exc
    logger.debug(
        "observation_extractor._call_llm: elapsed=%.2fs for feature batch %s",
        time.monotonic() - start, sorted(ontology_features),
    )
    return response.choices[0].message.content


def _parse_response(raw: str) -> tuple[dict, dict]:
    """Raises ValueError, with a raw-response snippet, on EITHER a
    JSON-decode failure or a well-formed-JSON-but-wrong-shape response
    (missing/non-dict top-level "observations" key). A missing/malformed
    top-level "unmapped" key does NOT raise -- see module docstring
    point 7."""
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "observation_extractor.extract_observation: failed to parse LLM response as "
            f"JSON ({exc}); raw response snippet: {raw[:200]!r}"
        ) from exc

    observations = parsed.get("observations") if isinstance(parsed, dict) else None
    if not isinstance(observations, dict):
        raise ValueError(
            "observation_extractor.extract_observation: LLM response is missing a valid "
            f"top-level 'observations' object; raw response snippet: {raw[:200]!r}"
        )

    unmapped_raw = parsed.get("unmapped") if isinstance(parsed, dict) else None
    if not isinstance(unmapped_raw, dict):
        if unmapped_raw is not None:
            logger.info(
                "observation_extractor.extract_observation: top-level 'unmapped' present "
                "but not an object (%r) -- treated as empty.", type(unmapped_raw).__name__,
            )
        unmapped_raw = {}

    return observations, unmapped_raw


# ─── Incompleteness guard -- retry the whole batched call ────────────────
# The batched call sometimes returns partial JSON that silently drops a
# feature with rich input prose (dogfood 2026-08-05T22:09, Athira:
# head/heart/venus/thumb came back empty despite full descriptions). This
# guard detects that class of drop -- distinct from a feature that
# legitimately has nothing to report -- and retries the WHOLE batch (never
# a per-feature call, per the one-call-per-batch contract this module
# already keeps) up to a bounded number of times, keeping whichever
# attempt dropped the fewest features. Fail-open: never raises over an
# incomplete result, never fabricates a token for a feature that stays
# empty after all retries -- honest silence beats a made-up observation.

_TRIVIAL_PROSE_MARKERS: tuple[str, ...] = (
    "not clearly visible", "barely visible", "absent", "no other lines",
)


def _is_substantive_prose(text: str) -> bool:
    """True if `text` is long enough and specific enough that SOME
    extraction result (a token or an unmapped quality) is expected for
    it -- as opposed to one of the descriptor's stock "nothing here"
    phrasings. THRESHOLD: 15 chars filters trivial/absent markers
    ("Absent.", "N/A") without excluding a real short observation;
    env-overridable via ASTRO_EXTRACT_MIN_PROSE_CHARS. Tuning note: the
    retry loop below logs every dropped-feature list at INFO level --
    use those logs to recalibrate this threshold or `_TRIVIAL_PROSE_
    MARKERS` if a legitimate short observation starts triggering false
    retries, or a real drop stops being caught."""
    stripped = text.strip()
    min_chars = int(os.getenv("ASTRO_EXTRACT_MIN_PROSE_CHARS", "15"))
    if len(stripped) <= min_chars:
        return False
    lowered = stripped.lower()
    return not any(marker in lowered for marker in _TRIVIAL_PROSE_MARKERS)


def _compute_dropped_features(
    features: dict[str, FeatureObservation],
    ontology_features: list[str],
    text_by_feature: dict[str, str],
) -> list[str]:
    """Ontology features whose input prose was substantive
    (`_is_substantive_prose`) but whose extracted result is completely
    empty (zero tokens AND zero unmapped) -- the signature of a batched
    call silently dropping a feature it should have said SOMETHING
    about, as distinct from a feature that legitimately had nothing to
    report (e.g. "barely visible" prose, correctly empty)."""
    dropped = []
    for feature in ontology_features:
        if not _is_substantive_prose(text_by_feature.get(feature, "")):
            continue
        fobs = features.get(feature)
        if fobs is None or (not fobs.tokens and not fobs.unmapped):
            dropped.append(feature)
    return sorted(dropped)


def _build_features_from_response(
    observations_raw: dict,
    unmapped_raw: dict,
    ontology_features: list[str],
    text_by_feature: dict[str, str],
    requested: frozenset[str],
) -> dict[str, FeatureObservation]:
    """One attempt's (A)+(B) fill of a fresh `{feature: FeatureObservation}`
    map from a single parsed LLM response -- factored out of
    `extract_observation` so the incompleteness-retry loop there can call
    it once per attempt and compare attempts by dropped-feature count."""
    features: dict[str, FeatureObservation] = {
        feature: FeatureObservation(raw_prose=text_by_feature[feature])
        for feature in ontology_features
    }

    # --- (A) observations: valid entries -> tokens; rejects fold into unmapped ---
    # (module docstring point 2 -- fail-closed for `tokens`, but never silently vanish)
    for feature, attrs in observations_raw.items():
        if feature not in requested:
            logger.info(
                "observation_extractor.extract_observation: LLM emitted feature %r in "
                "'observations', not in this call's requested batch -- dropped.", feature,
            )
            continue
        if not isinstance(attrs, dict):
            logger.info(
                "observation_extractor.extract_observation: feature %r's 'observations' "
                "entry is not an object (%r) -- dropped.", feature, type(attrs).__name__,
            )
            continue

        allowed_attributes = _CLOSED_VOCAB.get(feature, {})
        confidence = _confidence_for_text(text_by_feature.get(feature, ""))
        fobs = features[feature]

        for attribute, entry in attrs.items():
            attribute_guess = attribute if isinstance(attribute, str) else None

            if not isinstance(entry, dict) or "value" not in entry:
                fobs.unmapped.append({
                    "quality": f"(malformed LLM entry) {entry!r}",
                    "attribute_guess": attribute_guess,
                })
                logger.info(
                    "observation_extractor.extract_observation: malformed entry for "
                    "feature=%r attribute=%r (%r) -- folded into unmapped.",
                    feature, attribute, entry,
                )
                continue

            value = entry["value"]
            allowed_values = allowed_attributes.get(attribute)
            if allowed_values is None or not isinstance(value, str) or value not in allowed_values:
                fobs.unmapped.append({
                    "quality": value if isinstance(value, str) else repr(value),
                    "attribute_guess": attribute_guess,
                })
                logger.info(
                    "observation_extractor.extract_observation: out-of-vocabulary emission "
                    "feature=%r attribute=%r value=%r -- folded into unmapped.",
                    feature, attribute, value,
                )
                continue

            fobs.tokens[attribute] = {"value": value, "confidence": confidence}

    # --- (B) unmapped: LLM-reported qualities that never matched a token ---
    for feature, qualities in unmapped_raw.items():
        if feature not in requested:
            logger.info(
                "observation_extractor.extract_observation: LLM emitted feature %r in "
                "'unmapped', not in this call's requested batch -- dropped.", feature,
            )
            continue
        if not isinstance(qualities, list):
            logger.info(
                "observation_extractor.extract_observation: feature %r's 'unmapped' entry "
                "is not a list (%r) -- dropped.", feature, type(qualities).__name__,
            )
            continue

        fobs = features[feature]
        for quality_entry in qualities:
            if not isinstance(quality_entry, dict):
                logger.info(
                    "observation_extractor.extract_observation: 'unmapped' entry for "
                    "feature=%r is not an object (%r) -- dropped.",
                    feature, type(quality_entry).__name__,
                )
                continue
            quality = quality_entry.get("quality")
            if not isinstance(quality, str) or not quality.strip():
                logger.info(
                    "observation_extractor.extract_observation: 'unmapped' entry for "
                    "feature=%r has no usable 'quality' string (%r) -- dropped.",
                    feature, quality_entry,
                )
                continue
            attribute_guess = quality_entry.get("attribute_guess")
            if attribute_guess is not None and not isinstance(attribute_guess, str):
                attribute_guess = None
            fobs.unmapped.append({"quality": quality, "attribute_guess": attribute_guess})

    return features


def extract_observation(
    feature_texts: dict[str, list[str]],
    *,
    enabled_features: set[str] | None = None,
    model: str = "gpt-4o-mini",
    client=None,
) -> ObservationRecord:
    """Converts palm_reading._gather_feature_texts's `{prose_feature:
    [raw_text, ...]}` output into a capture-complete `ObservationRecord`.
    See module docstring for the full contract, deviations, and design
    notes.

    One LLM call for the whole batch (every alias-mapped, non-empty-text
    feature together, regardless of `enabled_features` -- capture is
    total, participation is filtered afterward) -- never one call per
    feature. A `feature_texts` with no mappable, non-empty-text entries
    makes ZERO LLM calls and returns an empty `ObservationRecord`
    directly (empty is a valid, non-raising result).

    enabled_features: allow-list applied AFTER capture -- every feature
        is still extracted into `features` regardless; features not in
        this set are additionally listed in `dropped_disabled`. None
        (default) means no allow-list: nothing is excluded.
    client: injection seam for tests (see module docstring, DEVIATION 1)
        -- if None, a real OpenAI() client is constructed lazily INSIDE
        this function, never at module import time.

    Raises:
        RuntimeError: the LLM call itself failed (network/API error).
        ValueError: the LLM's response could not be parsed as the
                     expected JSON shape (see _parse_response).
    """
    entries: list[tuple[str, str, str]] = []
    unmappable_prose_features: list[dict[str, str]] = []
    for prose_feature, texts in feature_texts.items():
        joined = " ".join(t.strip() for t in (texts or []) if t and t.strip())
        if not joined:
            continue
        ontology_feature = _FEATURE_ALIAS.get(prose_feature)
        if ontology_feature is None:
            logger.info(
                "observation_extractor.extract_observation: prose feature %r has no "
                "ontology counterpart -- captured as unmappable, not tokenized.", prose_feature,
            )
            unmappable_prose_features.append({"prose_feature": prose_feature, "raw_prose": joined})
            continue
        entries.append((prose_feature, ontology_feature, joined))

    if not entries:
        return ObservationRecord(
            features={},
            dropped_disabled=[],
            unmappable_prose_features=unmappable_prose_features,
        )

    if client is None:
        from openai import OpenAI  # lazy import -- see module docstring DEVIATION 1
        client = OpenAI(
            # max_retries=1: worst-case ~2x timeout (~120s), one retry absorbs a
            # transient network blip while still bounding the hang. 0 = hard
            # fail-fast (no blip resilience); 2 = SDK default (~180s, too long
            # for an interactive read). Env-overridable.
            max_retries=int(os.getenv("ASTRO_EXTRACT_MAX_RETRIES", "1")),
        )

    ontology_features = [e[1] for e in entries]
    text_by_feature = {e[1]: e[2] for e in entries}
    messages = [
        {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(entries)},
    ]
    requested = frozenset(ontology_features)

    # Incompleteness guard: retry the whole batch (never per-feature, per
    # the one-call-per-batch contract) up to ASTRO_EXTRACT_INCOMPLETE_
    # RETRIES times if any substantive-prose feature came back completely
    # empty. THRESHOLD: 2 retries (3 attempts total) balances catching a
    # transient partial-JSON response against dogfood latency; env-
    # overridable. Tuning note: `dropped_per_attempt` in the returned
    # `extraction_retries` logs which features triggered each retry --
    # use it to recalibrate. Keeps the attempt with the FEWEST dropped
    # features; never raises solely for incompleteness (fail-open).
    max_retries = int(os.getenv("ASTRO_EXTRACT_INCOMPLETE_RETRIES", "2"))
    dropped_per_attempt: list[dict[str, object]] = []
    best_features: dict[str, FeatureObservation] | None = None
    best_dropped: list[str] | None = None

    # temperature=0 (`_call_llm`) means an IDENTICAL request reliably returns
    # an identical (still-partial) response -- a retry only has a chance of
    # recovering a dropped feature if the INPUT changes. `current_messages`
    # starts as the original request (attempt 1, unchanged) and, after any
    # attempt that drops something, is rebuilt as original `messages` + ONE
    # appended corrective user message naming that attempt's dropped
    # features -- never accumulated across multiple retries (each retry's
    # request is original-plus-one-correction, not a growing conversation).
    current_messages = messages

    for attempt_num in range(1, max_retries + 2):
        raw = _call_llm(client, model, current_messages, ontology_features)
        observations_raw, unmapped_raw = _parse_response(raw)
        attempt_features = _build_features_from_response(
            observations_raw, unmapped_raw, ontology_features, text_by_feature, requested,
        )
        dropped = _compute_dropped_features(attempt_features, ontology_features, text_by_feature)
        dropped_per_attempt.append({"attempt": attempt_num, "dropped": dropped})

        if best_dropped is None or len(dropped) < len(best_dropped):
            best_features = attempt_features
            best_dropped = dropped

        if not dropped:
            break

        if attempt_num <= max_retries:
            logger.info(
                "observation_extractor.extract_observation: attempt %d dropped substantive-"
                "prose features %s -- retrying whole batch with a corrective instruction "
                "(up to %d retries).",
                attempt_num, dropped, max_retries,
            )
            current_messages = messages + [{
                "role": "user",
                "content": (
                    "Your previous response omitted these features that have "
                    f"descriptions: {', '.join(dropped)}. Return a complete JSON "
                    "including an entry for EVERY listed feature. Do not omit any."
                ),
            }]

    features = best_features
    extraction_retries: dict[str, object] = {
        "attempts_made": len(dropped_per_attempt),
        "retried": len(dropped_per_attempt) > 1,
        "dropped_per_attempt": dropped_per_attempt,
        "final_dropped": best_dropped,
    }

    if enabled_features is None:
        dropped_disabled: list[str] = []
    else:
        dropped_disabled = sorted({f for f in ontology_features if f not in enabled_features})

    return ObservationRecord(
        features=features,
        dropped_disabled=dropped_disabled,
        unmappable_prose_features=unmappable_prose_features,
        extraction_retries=extraction_retries,
    )


def to_vision_payload(
    record: ObservationRecord,
    enabled_features: set[str] | None = None,
) -> dict[str, dict[str, dict[str, object]]]:
    """Thin adapter: `ObservationRecord` -> the `{feature: {attribute:
    {value, confidence}}}` shape `observation_to_tokens.to_tokens()`
    consumes -- built ONLY from `tokens` of features in `enabled_features`
    (None = every feature present in `record.features`). Keeps the
    to_tokens() seam unchanged; this is the only place that shape is
    reconstructed.

    A feature with an empty `tokens` dict (nothing valid was ever
    extracted for it, even if `unmapped`/`raw_prose` are populated) is
    omitted from the output entirely -- matches the prior module
    version's behavior, where such a feature never appeared in
    `vision_payload` either.
    """
    payload: dict[str, dict[str, dict[str, object]]] = {}
    for feature, fobs in record.features.items():
        if enabled_features is not None and feature not in enabled_features:
            continue
        if fobs.tokens:
            payload[feature] = dict(fobs.tokens)
    return payload
