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
any engine file; not wired into any of them by this task. ONE narrow,
deliberate exception: `_mount_feature_from_vision_name` (mount-DEVELOPMENT
parsing section, below `extract_relations`) lazily imports
`palm_reading._SUB_FEATURES` -- function-scoped, same "avoid tight
load-time coupling" precedent as this module's own lazy `openai` import
and `palm_reading.py`'s own lazy import of THIS module -- specifically to
reuse that alias table as the single source of truth for vision-mount-name
-> registry-feature-key mapping (generalization gate: no second,
independently-authored name map). Paid only by callers of that one
function; every other symbol in this module remains import-free of
palm_reading.py.

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
# prose-label-to-canonical-feature mapping). Two of the nineteen have NO
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
    # S96: the 7 remaining registry mounts made emission-reachable. Additive
    # only -- no existing key's mapping changed. Two Cheiro synonyms collapse
    # onto one canonical feature each ("mount of apollo" -> Mount of the Sun,
    # "mount of the moon" -> Mount of Luna); every right-hand side is a
    # verbatim member of ontology_registry.json's features.mounts.
    "mount of saturn": "Mount of Saturn",
    "mount of the sun": "Mount of the Sun",
    "mount of apollo": "Mount of the Sun",
    "mount of mercury": "Mount of Mercury",
    "upper mount of mars": "Upper Mount of Mars",
    "lower mount of mars": "Lower Mount of Mars",
    # S117: `palm_reading._FEATURE_REGISTRY`/`_SUB_FEATURES` spell the two
    # Mars mounts "mount of mars positive"/"mount of mars negative" --
    # a DIFFERENT spelling from this dict's pre-existing S96 "upper mount
    # of mars"/"lower mount of mars" keys above (never previously
    # reconciled). Additive alias only, same canonical feature each --
    # needed so `translate_mount_development` (below) can resolve
    # `extract_mount_development`'s own "mount of mars positive" output
    # key. "mount of mars negative" is NOT added here: Lower Mars is
    # presence-only (extract_mount_development never emits a Development
    # value for it, S117), so no caller needs that key today -- add it
    # only if that ever changes, per the same "additive, no existing key
    # touched" discipline as every other entry in this dict.
    "mount of mars positive": "Upper Mount of Mars",
    "mount of luna": "Mount of Luna",
    "mount of the moon": "Mount of Luna",
    "plain of mars": "Plain of Mars",
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
# consults for any antecedent whose own relation_target is not None. LIVE
# since S92 (H_027, the first directed relational rule) -- as of S97 this
# drives 15 live Line of Fate relational antecedents (ORIGIN/TERMINATION/
# PROXIMITY/BRANCHES_TO) plus the earlier head/heart relational rules; no
# longer a proving-only path.
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
# (PROXIMITY's "<degree> to") is NOT captured by this map -- only the
# target landmark carries signal here. The degree token is separately
# captured as an observation VALUE by extract_relations()'s "proximity"
# strategy branch. S89's "dead axis" finding (model says "medium"
# universally) is RETIRED: the 2026-08-12/13 dogfood showed the vision
# emitting both 'touching' (head->life) and 'medium' (heart/fate->head);
# the degree is captured and live as of 5c step 1 (-> flat observation
# Proximity).
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
    simply fail the registry-membership check in extract_relations."""
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


def merge_relational_targets(
    *target_dicts: dict[str, dict[str, object]]
) -> dict[str, dict[str, object]]:
    """Merges multiple extract_relations()['targets'] outputs (e.g. one per
    hand image) into one targets dict -- cardinality-aware (Pattern D step
    3). For a MULTI attribute (Convergence) whose value is a set, later
    dicts UNION into the running set -- both hands' partners are combined,
    never overwritten. For a SINGLE attribute (Convergence_Location + all
    directional attrs), later args win on a per-(feature, attribute)
    collision -- callers passing (left, right) get right-hand priority on
    conflict, exactly as before this step. Documented as a real behavioral
    choice (there is no established convention for this axis yet), not an
    accident of dict.update order."""
    merged: dict[str, dict[str, object]] = {}
    for targets in target_dicts:
        for feature, attrs in targets.items():
            bucket = merged.setdefault(feature, {})
            for attr, value in attrs.items():
                if _is_multi(attr) and isinstance(value, (set, frozenset)):
                    bucket.setdefault(attr, set()).update(value)
                else:
                    bucket[attr] = value
    return merged


# ─── Convergence targets -- Pattern C step 2a (S98) ──────────────────────
# Parses NEW CONVERGENCE / CONVERGENCE_LOCATION subfields (registry-legal
# since ontology_registry.json's change_log 1.6.0, but not yet emitted by
# any live vision prompt -- that is step 3) into the SAME
# `{feature: {attribute: landmark}}` shape extract_relational_targets
# produces, so step 2b's wiring into merge_relational_targets is a
# one-line addition.
#
# Deliberately duplicates the minimal header/subfield matcher locally
# rather than reusing _RELATIONAL_HEADER / _LINE_HEADER /
# _RELATIONAL_LINE_ALIAS / _RELATIONAL_SUBFIELD above: extract_relational_
# targets must stay byte-identical in BEHAVIOR (15 live Fate rules depend
# on it), not just in source text. "Line of Health" is one of the four
# in-scope Convergence owners per the 1.6.0 canonical_owner_rule, but it
# has no header at all in _LINE_HEADER's alternation (that regex only
# recognizes LIFE/HEAD/HEART/FATE LINE plus the non-line sections) --
# widening the SHARED regex to add "HEALTH LINE" would change extract_
# relational_targets' runtime behavior on any real input containing a
# HEALTH LINE section (today such a line falls through as an ignored
# continuation of whatever feature preceded it; matching it as a header
# would reset current_feature to None instead), even though that
# function's own source line would not change. A fresh, local, narrower
# matcher set avoids that risk entirely and needs no reuse discipline
# with extract_proximity_observations either, since PROXIMITY is not this
# function's concern.

_CONVERGENCE_ATTR = "Convergence"
_CONVERGENCE_LOCATION_ATTR = "Convergence_Location"

# SSOT: every attribute an extractor emits with a relation_target -> the
# vision subfield LABEL it's emitted under. Add a NEW relational attribute
# HERE once; all consumers (vocab_reachability_scan, future fields, the
# Pattern D set-valued Convergence work) derive from this -- no hardcoded
# copies to keep in sync anywhere else.
RELATION_ATTR_TO_FIELD: dict[str, str] = {
    **{attr: label for label, attr in _RELATIONAL_ATTRIBUTE_MAP.items()},  # 4 directional, derived
    _CONVERGENCE_ATTR: "CONVERGENCE",
    _CONVERGENCE_LOCATION_ATTR: "CONVERGENCE_LOCATION",
}
EMITTED_RELATION_ATTRS: frozenset[str] = frozenset(RELATION_ATTR_TO_FIELD)

# Reverse of RELATION_ATTR_TO_FIELD -- subfield LABEL -> attribute. Used by
# extract_relations() (Generalization step 2a, S98) to go from a matched
# subfield ("ORIGIN"/"PROXIMITY"/"TERMINATION"/"BRANCHES_TO"/"CONVERGENCE"/
# "CONVERGENCE_LOCATION") to the attribute it fills, then to that
# attribute's parse STRATEGY via _RELATION_TYPES below.
_RELATIONAL_FIELD_TO_ATTR: dict[str, str] = {v: k for k, v in RELATION_ATTR_TO_FIELD.items()}

# Registry-derived: attribute -> parse strategy ("directional"/"proximity"/
# "symmetric", ontology_registry.json's "relation_types" block, Generalization
# step 1). Bare bracket access -- this key is foundational once declared and
# MUST exist, same convention as every other _REGISTRY-derived constant above.
_RELATION_TYPES: dict[str, str] = dict(_REGISTRY["relation_types"])

# Registry-derived: attribute -> cardinality ("single"/"multi",
# ontology_registry.json's "relation_cardinality" block, Pattern D step 1).
# Same bare-bracket-access convention as _RELATION_TYPES above -- keys match
# 1:1 (asserted at that block's own declaration time, S98).
_RELATION_CARDINALITY: dict[str, str] = dict(_REGISTRY["relation_cardinality"])


def _is_multi(attr: str) -> bool:
    """True if `attr` is declared 'multi' cardinality in relation_cardinality
    (Pattern D) -- Convergence only, today. Everything else (Convergence_
    Location + all directional attrs) is 'single', matched by plain
    equality/overwrite, unchanged from pre-Pattern-D behavior."""
    return _RELATION_CARDINALITY.get(attr) == "multi"


# Registry-derived: feature -> {vision subfield LABEL -> [legal target
# tokens]} (ontology_registry.json's "vision_relational_menus" block,
# Generalization step 1). Carries a stray "_note" top-level key (documentation,
# not a feature) -- harmless here since every lookup is a targeted `.get(
# feature, {})` by real feature name, never a blind iteration over all keys.
# ADVISORY ONLY (see extract_relations()'s docstring point on this): a token
# absent from a feature's menu here is logged, never rejected -- the actual
# accept/reject gate stays relation_target_registry membership everywhere,
# matching this exact codebase's own established precedent for this class of
# check (scripts/vocab_reachability_scan.py's _VISION_ORIGIN_MENU/
# _VISION_TERMINATION_MENU: "never changes a yes/NO verdict").
_VISION_RELATIONAL_MENUS: dict[str, dict[str, list[str]]] = dict(_REGISTRY["vision_relational_menus"])

_CONVERGENCE_RELATIONAL_HEADER = re.compile(r"^([A-Z][A-Z ]*) RELATIONAL:\s*$")

# LIFE/HEAD/HEART/FATE LINE mirror _LINE_HEADER's existing line set;
# HEALTH LINE is added here only (forward-looking -- no live vision prompt
# emits a HEALTH LINE header yet, but it is an in-scope Convergence owner
# per the ontology and must not be silently unreachable once step 3 wires
# vision emission for it).
_CONVERGENCE_LINE_HEADER = re.compile(
    r"^(LIFE LINE|HEAD LINE|HEART LINE|FATE LINE|HEALTH LINE):"
)

_CONVERGENCE_LINE_ALIAS: dict[str, str] = {
    "life line": "Line of Life",
    "head line": "Line of Head",
    "heart line": "Line of Heart",
    "fate line": "Line of Fate",
    "health line": "Line of Health",
}

_CONVERGENCE_SUBFIELD = re.compile(r"^(CONVERGENCE|CONVERGENCE_LOCATION):\s*(.*)$")


def _canonicalize_convergence(emitting_feature: str, target_landmark: str) -> tuple[str, str]:
    """Returns (owner, other) for a convergence between the block's
    emitting feature and its stated target landmark, per ontology_registry.
    json's change_log 1.6.0 canonical_owner_rule: owner = min(A, B) by
    plain string sort, other = the remaining one. Pure string comparison --
    no hardcoded feature list -- because "Line of Life" happens to sort
    after every in-scope owner (Fate/Head/Health/Heart all share the
    common "Line of H"/"Line of F" prefix and are alphabetically earlier
    than "Line of Life"'s "Li"), so Life is naturally never the owner
    without this function needing to special-case it."""
    if emitting_feature <= target_landmark:
        return emitting_feature, target_landmark
    return target_landmark, emitting_feature


# ─── Unified relational parser -- Generalization step 2a (S98) ──────────
# extract_relations() is the sole relational parser -- it originally reproduced
# the combined output of three now-retired functions (extract_relational_
# targets, extract_convergence_targets, extract_proximity_observations;
# retired at Generalization 2c-ii, S98, once a 32-case differential battery
# proved it byte-identical to their combined output -- see commit history)
# into its "targets" and "proximity" keys respectively,
# driven by the registry's "relation_types"/"vision_relational_menus" blocks
# (Generalization step 1) instead of a bespoke per-attribute function each.
# See this module's docstring discrepancy-log convention below for the one
# real design deviation from the task that originally authored this function.
#
# === Deviation from this task's own prompt (flagged per project convention) ===
# The instructing prompt's literal wording for the directional/symmetric
# strategies says to "validate ... against vision_relational_menus[feature]
# [label] when that closed menu exists, else against relation_target_registry".
# Read literally as a REJECTION gate, this would make extract_relations STRICTER
# than the three original functions for any feature/label pair that now has a
# closed menu (ORIGIN/TERMINATION on Head/Heart/Fate; CONVERGENCE/CONVERGENCE_
# LOCATION on Fate/Life) -- none of those closed menus existed before
# Generalization step 1, so no original function has ever consulted one; each
# one only ever checked plain relation_target_registry membership. Implementing
# the menu as a hard gate would therefore REJECT an off-menu-but-registry-legal
# landmark (e.g. Head LINE's ORIGIN emitting the registry-legal "Mount of
# Saturn", which is not in Head's own {Mount of Jupiter, Line of Life, Lower
# Mount of Mars} menu) that every original function currently ACCEPTS --
# failing this task's own stated goal ("PROVEN BYTE-IDENTICAL to the 3
# existing relational extractors") on exactly the "off-menu tokens" battery
# case the task itself requires covering.
#
# Resolved by treating the menu check as ADVISORY ONLY, never a rejection
# gate: the actual accept/reject decision for every strategy stays plain
# relation_target_registry membership (byte-identical to all three original
# functions, unconditionally); when a closed menu exists for the (feature-or-
# emitting-feature, label) pair AND the accepted landmark is not a member of
# that specific menu, an INFO-level caveat is logged and nothing else changes.
# This mirrors an established precedent already in this exact codebase --
# scripts/vocab_reachability_scan.py's own _VISION_ORIGIN_MENU/_VISION_
# TERMINATION_MENU, documented there as "Used ONLY for the soft prompt-menu
# caveat ... never changes a yes/NO verdict." Differential parity (this
# task's real crux) is preserved by construction; the menu consultation the
# prompt asked for still happens, and still has an observable effect (the log
# line), just not a rejection effect.


def _log_off_menu_caveat(feature: str, label: str, value: str) -> None:
    """Advisory-only: logs when an ACCEPTED (registry-legal) value is not a
    member of its feature/label's closed vision_relational_menus entry, if
    one exists. Never called for a value that failed the registry gate --
    see the module-docstring deviation note above for why this never
    changes accept/reject."""
    menu = _VISION_RELATIONAL_MENUS.get(feature, {}).get(label)
    if menu is not None and value not in menu:
        logger.info(
            "observation_extractor.extract_relations: feature=%r label=%r "
            "value=%r is registry-legal but NOT a member of its closed vision "
            "menu %r -- accepted anyway (advisory only, never a rejection gate).",
            feature, label, value, menu,
        )


# ─── Typed RELATIONSHIP parsing -- typed-relationship arc Step 3 (S99) ───
# EMISSION + PARSE-CALL RETIRED (S107): agent/palm_processor.py no longer
# emits "RELATIONSHIP:" lines, and extract_relations no longer calls
# _parse_relationship_value/matches _RELATIONSHIP_SUBFIELD against
# raw_text (see the "TYPED RELATIONSHIP -- RETIRED" paragraph on
# extract_relations' own docstring below for the full account). The
# symbols below this comment SURVIVE as shared infrastructure:
# `_RELATIONSHIP_TOKENS` (imported by contact_mapper.py),
# `_RELATIONSHIP_LINE_HEADER`/`_RELATIONSHIP_LINE_ALIAS` (now driving only
# the CONTACTS tracker, below), and `_store_relationship` (the bridge's
# filing primitive, called from palm_reading._assemble_relational_
# targets). `_RELATIONSHIP_SUBFIELD` is removed (no remaining caller);
# `_parse_relationship_value` is kept only because a non-production probe
# script still imports it -- its own production call site is gone.
#
# Historical framing below (Step 3, S99): originally parsed the "NEW
# RELATIONSHIP: <type> <target> [at <mount>]" lines Step 2
# (agent/palm_processor.py) added to the Head/Heart/Fate/Health/Marriage
# blocks. Fully additive at the time: a distinct header regex, alias map,
# subfield regex, and store function, all local to this section -- none of
# the existing directional/proximity/convergence trackers, regexes, or
# state were touched, so their behavior stayed byte-identical.
#
# HEADER-TEXT FINDING (flagged per project convention -- verify against
# code, don't assume): the pre-existing _CONVERGENCE_LINE_HEADER constant
# above already anticipates a future "HEALTH LINE:" header ("forward-
# looking -- no live vision prompt emits a HEALTH LINE header yet"), but
# Step 2's actual prompt text emits "LINE OF HEALTH:" and "LINE OF
# MARRIAGE:" (verified directly against agent/palm_processor.py, not
# assumed) -- a different string shape, not a superset/subset of the old
# guess. Reusing _CONVERGENCE_LINE_HEADER here would silently never match
# real vision output for Health/Marriage. This section therefore declares
# its OWN local header regex matching what Step 2 actually emits, per the
# same "deliberately duplicates ... locally" precedent _CONVERGENCE_LINE_
# HEADER's own comment block established for exactly this class of risk
# (a shared regex whose behavior must stay byte-identical for existing
# callers must never be widened for a new caller).
_RELATIONSHIP_LINE_HEADER = re.compile(
    r"^(HAND SHAPE|FINGERS|THUMB|LIFE LINE|HEAD LINE|HEART LINE|FATE LINE"
    r"|LINE OF HEALTH|LINE OF MARRIAGE|OTHER LINES|MARKS):"
)
_RELATIONSHIP_LINE_ALIAS: dict[str, str] = {
    "head line": "Line of Head",
    "heart line": "Line of Heart",
    "fate line": "Line of Fate",
    "line of health": "Line of Health",
    "line of marriage": "Line of Marriage",
}
# _RELATIONSHIP_SUBFIELD (matched "^RELATIONSHIP:\s*(.*)$") removed S107
# -- no remaining caller once the sub_typed parse-call block in
# extract_relations was retired.

# Registry-derived, NOT a hardcoded list (DO #3): the 8 typed tokens are
# exactly relation_types' keys minus the pre-existing legacy attrs
# (EMITTED_RELATION_ATTRS: Starting_Point/Position/Branching/Proximity/
# Convergence/Convergence_Location). Adding a 9th typed token to the
# registry in a future step is picked up here automatically, no edit
# needed.
_RELATIONSHIP_TOKENS: frozenset[str] = frozenset(_RELATION_TYPES) - EMITTED_RELATION_ATTRS


def _parse_relationship_value(value: str) -> tuple[str, str, str | None] | None:
    """Splits a RELATIONSHIP subfield's raw value "<type> <target> [at
    <mount>]" into (type_token, target, mount_or_None). Returns None for an
    empty/'none'/'n/a' value (no interaction reported for this line -- same
    "honest absence" convention as every other relational field in this
    module). Raises ValueError if no space separates a type token from a
    target (can't even isolate the two halves) -- the caller wraps this in
    try/except (DO #4) so one malformed line never kills the rest of the
    block. Targets never contain the literal substring " at " (verified
    against every line/mount name in relation_target_registry), so a plain
    first-occurrence split is unambiguous -- mirrors _proximity_landmark's
    identical " to "-split reasoning for PROXIMITY above.

    NO PRODUCTION CALLER as of S107 (RELATIONSHIP emission + the
    extract_relations parse-call path that used to call this are both
    retired) -- kept only because scripts/crossing_pass_second_call_probe.py
    (a non-production scratch script) still imports it directly."""
    value = value.strip()
    if not value or value.lower() in ("none", "n/a"):
        return None
    if " " not in value:
        raise ValueError(
            f"RELATIONSHIP value {value!r} has no <type> <target> split point"
        )
    type_token, rest = value.split(" ", 1)
    rest = rest.strip()
    if " at " in rest:
        target, mount = rest.split(" at ", 1)
        target, mount = target.strip(), mount.strip()
    else:
        target, mount = rest, None
    return type_token, target, mount


def _store_relationship(
    targets: dict[str, dict[str, object]],
    feature: str,
    type_token: str,
    target: str,
    mount: str | None,
) -> None:
    """Files one parsed relational interaction into `targets[feature]
    [type_token]` (Step 3 DO #1/#2). The one filing primitive for BOTH the
    original (now-retired) typed-RELATIONSHIP parse path and its S107
    replacement, `palm_reading._assemble_relational_targets` (CONTACTS ->
    contact_mapper.map_contact -> here) -- cardinality/registry-gate
    behavior is unchanged either way. MULTI cardinality (joins_at_origin/
    meets/cuts/cut_by/touches, per registry relation_cardinality) accumulates
    `target` into a set -- union, never overwrite, the same accumulate-
    don't-overwrite pattern Pattern D established for Convergence. SINGLE
    cardinality (stopped_by/takes_possession_of/branch_in) is scalar: a
    second target for the same (feature, type) is REJECTED, keeping the
    first-seen value, with a warning -- never a silent overwrite.

    LOCATION ("at <mount>", DO #2): stored index-aligned per interaction at
    `targets[feature][f"{type_token}__location"][target] = mount`, so a
    future consumer can look up the specific crossing mount for one
    (type, target) pair. Only populated when this call's line supplied a
    mount AND the (type, target) reading was actually accepted -- a
    duplicate-rejected SINGLE-cardinality line's mount is discarded
    alongside its rejected target, never filed under the surviving first
    reading.

    Fail-closed (DO #3): an unregistered type token or an off-registry
    target/mount is dropped with a log line, never guessed or coerced --
    identical fail-closed posture to every other relational gate in this
    module (relation_target_registry membership)."""
    if type_token not in _RELATIONSHIP_TOKENS:
        logger.info(
            "observation_extractor.extract_relations: dropped RELATIONSHIP "
            "type=%r for feature=%r -- not a registry-legal typed-"
            "relationship token (ontology_registry.json's relation_types).",
            type_token, feature,
        )
        return
    if target not in _RELATION_TARGET_REGISTRY:
        logger.info(
            "observation_extractor.extract_relations: dropped RELATIONSHIP "
            "feature=%r type=%r target=%r -- not in relation_target_registry.",
            feature, type_token, target,
        )
        return

    bucket = targets.setdefault(feature, {})
    if _is_multi(type_token):
        bucket.setdefault(type_token, set()).add(target)
    else:
        if type_token in bucket:
            logger.warning(
                "observation_extractor.extract_relations: duplicate SINGLE-"
                "cardinality RELATIONSHIP type=%r for feature=%r -- keeping "
                "first-seen target=%r, ignoring new target=%r.",
                type_token, feature, bucket[type_token], target,
            )
            return
        bucket[type_token] = target

    if mount is None:
        return
    if mount not in _RELATION_TARGET_REGISTRY:
        logger.info(
            "observation_extractor.extract_relations: dropped RELATIONSHIP "
            "location mount=%r for feature=%r type=%r target=%r -- not in "
            "relation_target_registry.",
            mount, feature, type_token, target,
        )
        return
    loc_key = f"{type_token}__location"
    loc_bucket = bucket.setdefault(loc_key, {})
    if target in loc_bucket and loc_bucket[target] != mount:
        logger.info(
            "observation_extractor.extract_relations: duplicate RELATIONSHIP "
            "location for feature=%r type=%r target=%r -- keeping first-seen "
            "mount=%r, ignoring new mount=%r.",
            feature, type_token, target, loc_bucket[target], mount,
        )
        return
    loc_bucket[target] = mount


# ─── Free-verb CONTACTS parsing -- S104 Step 3 (S107: now the SOLE
# emitted relational-verb channel, RELATIONSHIP retired) ──────────────────
# Parses the "CONTACTS: <target> | <verb> | <position> | <clarity>" lines
# agent/palm_processor.py emits under the Head/Heart/Fate/Health blocks.
# Originally additive alongside a RELATIONSHIP field (Step 3, S99) that
# S107 removed (both its emission and its parse-call path -- see the
# "TYPED RELATIONSHIP -- RETIRED" paragraph in extract_relations' own
# docstring below). Its own subfield regex, vocab sets, parse/store
# functions, and tracker variable stay local to this section -- none of the
# existing directional/proximity/convergence tracker/regex/state are
# touched by this channel, so their behavior (and every rule that reads
# "targets"/"proximity") stays byte-identical. The header event that flips
# `current_feature_contacts` reuses _RELATIONSHIP_LINE_HEADER/
# _RELATIONSHIP_LINE_ALIAS (names kept post-retirement -- CONTACTS appears
# in the exact same blocks RELATIONSHIP used to) rather than adding a new
# header regime.
#
# DELIBERATELY DUMB: the <verb> field is captured 100% verbatim, no
# mapping, no menu check -- Step 4 owns interpreting it. This parser's only
# job is structure (4 pipe-fields) and the two closed side-channels
# (position/clarity), plus the target gate below.
_CONTACTS_SUBFIELD = re.compile(r"^CONTACTS:\s*(.*)$")
_CONTACTS_POSITIONS: frozenset[str] = frozenset({"at start", "mid-course", "at end", "unknown"})
_CONTACTS_CLARITIES: frozenset[str] = frozenset({"faint", "clear"})

# Registry-derived per-feature CONTACTS target set, independently computed
# from the SAME ontology_registry.json SSOT agent.palm_processor.
# _relationship_target_menu draws from (convergence_lines minus `feature`,
# plus every registry mount landmark) -- not imported from palm_processor
# itself (this module builds parsing utilities; palm_processor builds
# vision prompts -- no reverse dependency introduced here). Deliberately
# NARROWER than _RELATION_TARGET_REGISTRY (the registry-wide gate every
# other relational field in this module uses, advisory-only per this
# module's own documented S99 deviation): the CONTACTS prompt field
# explicitly instructs the model to pick from exactly this per-feature
# menu, so an out-of-menu target here is a hallucination to quarantine,
# not an off-menu-but-registry-legal value to accept.
_CONVERGENCE_LINES_FOR_CONTACTS: tuple[str, ...] = tuple(_REGISTRY.get("convergence_lines", []))
_MOUNT_TARGETS_FOR_CONTACTS: frozenset[str] = frozenset(
    t for t in _RELATION_TARGET_REGISTRY if "Mount" in t
)


def _contacts_target_menu(feature: str) -> frozenset[str]:
    """Per-feature legal CONTACTS <target> set -- see the module-section
    comment above for the SSOT/dependency-direction rationale."""
    return frozenset(
        line for line in _CONVERGENCE_LINES_FOR_CONTACTS if line != feature
    ) | _MOUNT_TARGETS_FOR_CONTACTS


def _parse_contacts_value(value: str) -> tuple[str, str, str, str] | None:
    """Splits a CONTACTS subfield's raw value "<target> | <verb> | <position>
    | <clarity>" into its 4 raw pipe-fields (target, verb, position_raw,
    clarity_raw) -- all still unvalidated/unnormalized strings; <verb> is
    returned completely untouched by this function and every caller (Step 4
    owns interpreting it). Returns None for an empty/'none'/'n/a' value
    (explicit no-contacts declaration for this line -- same "honest
    absence" convention as every other relational field in this module).
    Raises ValueError if the pipe-split doesn't yield exactly 4 fields --
    the caller wraps this in try/except (mirrors _parse_relationship_
    value's malformed-line handling) so one garbled line never kills the
    rest of the block."""
    value = value.strip()
    if not value or value.lower() in ("none", "n/a"):
        return None
    parts = [p.strip() for p in value.split("|")]
    if len(parts) != 4:
        raise ValueError(
            f"CONTACTS value {value!r} split into {len(parts)} pipe-field(s) "
            "on '|', expected 4"
        )
    return parts[0], parts[1], parts[2], parts[3]


def _store_contact(
    contacts: dict[str, list[dict[str, str]]],
    feature: str,
    target: str,
    verb: str,
    position_raw: str,
    clarity_raw: str,
) -> None:
    """Files one parsed CONTACTS interaction into `contacts[feature]` (S104
    Step 3) -- a plain append-only list of {target, verb, position,
    clarity} dicts, never deduplicated or accumulated into a set/scalar
    (the free-verb field carries no type token to key on, so two lines
    naming the same target are two distinct observations to keep, unlike
    _store_relationship's set/scalar accumulation by type).

    <target> gate: _contacts_target_menu(feature) (narrower than
    _RELATION_TARGET_REGISTRY -- see that function's docstring). Off-menu
    -> dropped + logged (quarantine), never guessed.

    <position>/<clarity>: normalized to their closed vocab; anything
    off-vocab is stored as 'unknown' rather than dropping the whole
    contact (an unclear position/clarity does not invalidate that a
    contact was reported) -- logged either way, never silently coerced
    without a trace.

    Caller (extract_relations) is responsible for `contacts.setdefault(
    feature, [])` at the point ANY "CONTACTS:" line is seen for `feature`
    -- including a malformed or explicit-'none' line -- so a feature is
    absent from `contacts` ONLY when no CONTACTS line was emitted for it at
    all (the three-state has-contacts/declared-none/missing distinction).
    This function also defensively setdefaults, as a no-op safeguard if
    ever called without that caller-side guarantee."""
    bucket = contacts.setdefault(feature, [])

    if target not in _contacts_target_menu(feature):
        logger.info(
            "observation_extractor.extract_relations: dropped CONTACTS "
            "feature=%r target=%r -- not in this feature's CONTACTS target "
            "menu (quarantined).",
            feature, target,
        )
        return

    position = position_raw.strip().lower()
    if position not in _CONTACTS_POSITIONS:
        logger.info(
            "observation_extractor.extract_relations: CONTACTS feature=%r "
            "target=%r position=%r not in {at start, mid-course, at end, "
            "unknown} -- stored as 'unknown'.",
            feature, target, position_raw,
        )
        position = "unknown"

    clarity = clarity_raw.strip().lower()
    if clarity not in _CONTACTS_CLARITIES:
        logger.info(
            "observation_extractor.extract_relations: CONTACTS feature=%r "
            "target=%r clarity=%r not in {faint, clear} -- stored as "
            "'unknown'.",
            feature, target, clarity_raw,
        )
        clarity = "unknown"

    bucket.append({"target": target, "verb": verb, "position": position, "clarity": clarity})


def extract_relations(raw_text: str) -> dict[str, dict]:
    """Registry-driven unified relational parser. Returns `{"targets":
    {feature: {attribute: landmark}}, "proximity": {feature: {"Proximity":
    {"value": degree, "confidence": 1.0}}}}` -- reproduces, in ONE pass over
    `raw_text`, the exact combined output of:
        merge_relational_targets(extract_relational_targets(raw_text),
                                  extract_convergence_targets(raw_text))
        -> this function's "targets"
        extract_proximity_observations(raw_text)
        -> this function's "proximity"

    Runs the SAME two header-detection state machines the three source
    functions each already use, in parallel within one loop (never a new,
    third header regime): `_RELATIONAL_HEADER`/`_LINE_HEADER`/
    `_RELATIONAL_LINE_ALIAS` (directional + proximity landmark/degree,
    exactly as extract_relational_targets/extract_proximity_observations
    track blocks) and `_CONVERGENCE_RELATIONAL_HEADER`/
    `_CONVERGENCE_LINE_HEADER`/`_CONVERGENCE_LINE_ALIAS` (symmetric
    convergence, exactly as extract_convergence_targets tracks blocks,
    including its Life/Health line support and its own quirk that non-
    relational section headers like "OTHER LINES:"/"MARKS:" do NOT reset
    its tracker -- both trackers are independent state, each reset only by
    its OWN original header logic, so this quirk-for-quirk asymmetry
    between the two channels is preserved exactly as it is when the three
    functions run separately).

    For each matched subfield label, looks up its attribute via
    `_RELATIONAL_FIELD_TO_ATTR` (the reverse of the public
    `RELATION_ATTR_TO_FIELD` SSOT), then its parse strategy via
    `_RELATION_TYPES[attribute]` (ontology_registry.json's "relation_types"
    block):
      - "directional" (Starting_Point/Position/Branching): landmark filed
        into targets if relation_target_registry-legal, else dropped --
        identical gate to extract_relational_targets. See the module
        docstring deviation note above for why `vision_relational_menus` is
        consulted as an advisory caveat only, never narrowing this gate.
      - "proximity" (Proximity): landmark half handled exactly as the
        directional case (registry gate only, no menu -- PROXIMITY's
        landmark is explicitly excluded from vision_relational_menus per
        that block's own "_note"); degree half split via
        `_proximity_degree`/`_proximity_landmark` and validated against
        `_PROXIMITY_DEGREE_VALUES`, filed into "proximity" -- both halves
        processed independently, exactly mirroring the two original
        functions' independence from each other (a dropped landmark never
        suppresses the degree, and vice versa).
      - "symmetric" (Convergence/Convergence_Location): identical
        canonicalization, per-block `pending_location` buffering, and all 5
        fail-closed drops (invalid registry target, self-convergence,
        orphan location, invalid location, empty/'none'/'n/a') as
        extract_convergence_targets -- the vision_relational_menus check
        (when one exists) is consulted keyed by the EMITTING feature,
        pre-canonicalization, as an advisory caveat only (same non-gating
        rule as the directional case).

    Never raises for a missing/malformed relational block or an unparseable
    raw_text -- returns `{"targets": {}, "proximity": {}, "contacts": {}}` in
    that case, same "no signal" convention as all three source functions
    ("contacts" added Step 3, S104 -- see that paragraph below).

    TYPED RELATIONSHIP -- RETIRED (S107): this paragraph is historical.
    Step 3 (S99) originally added a THIRD, fully independent tracker
    (`current_feature_typed`, its own local `_RELATIONSHIP_LINE_HEADER`/
    `_RELATIONSHIP_LINE_ALIAS`/`_RELATIONSHIP_SUBFIELD`) that parsed
    "RELATIONSHIP: <type> <target> [at <mount>]" lines emitted under the
    Head/Heart/Fate/Health/Marriage blocks, filing each typed token into
    `targets[feature][type_token]` via `_store_relationship`. S107 removed
    BOTH the emitted RELATIONSHIP field (`agent/palm_processor.py`) and
    this parse-call path -- H_028/L_026 (the only two live rules that
    keyed on a typed token besides parked FT_016) now fire via the
    CONTACTS channel instead (`palm_reading._assemble_relational_targets`
    -> `contact_mapper.map_contact` (S106-inflection-aware) -> this
    module's own `_store_relationship`, unchanged and still the one
    filing primitive for both the old and new path). `_RELATIONSHIP_
    TOKENS`, `_RELATIONSHIP_LINE_HEADER`/`_RELATIONSHIP_LINE_ALIAS` (now
    driving ONLY the CONTACTS tracker below), and `_store_relationship`
    all survive this retirement as shared symbols -- `_RELATIONSHIP_
    SUBFIELD` and `_parse_relationship_value`'s production call site do
    not (see `contact_mapper.py` and the CONTACTS paragraph below for what
    replaced them).

    FREE-VERB CONTACTS (Step 3, S104 -- originally additive alongside
    typed RELATIONSHIP, now the SOLE relational-verb tracker post-S107
    retirement): parses "CONTACTS: <target> | <verb> | <position> |
    <clarity>" lines under the Head/Heart/Fate/Health blocks Step 2 emits,
    into an ISOLATED return key: `{"targets": ..., "proximity": ...,
    "contacts": {feature: [{"target", "verb", "position", "clarity"}, ...]}}`.
    No rule reads "contacts" directly -- palm_reading._assemble_relational_
    targets (S107) is the one production consumer, mapping each entry
    through contact_mapper.map_contact into the SAME `targets` shape the
    (now-retired) typed RELATIONSHIP path used to produce, via this
    module's own `_store_relationship`. `<verb>` is stored completely
    untouched here, no mapping, no menu check -- contact_mapper owns
    interpreting it. `<target>` is gated against a per-feature menu
    (narrower than `_RELATION_TARGET_REGISTRY`); off-menu is quarantined.
    `<position>`/`<clarity>` normalize to a closed vocab or 'unknown',
    logged either way, never dropping the whole contact over an unclear
    side-field. A feature is present in `contacts` (possibly as `[]`) the
    moment ANY CONTACTS line is seen for it -- valid, malformed, or
    explicit 'none' -- and is absent from the dict ONLY when no CONTACTS
    line was emitted for it at all, so has-contacts / declared-none /
    missing are all distinguishable downstream. See the dedicated section
    above `extract_relations` for the full mechanics.
    """
    if not isinstance(raw_text, str):
        raise TypeError(
            "observation_extractor.extract_relations: raw_text must be a "
            f"str, got {type(raw_text).__name__}"
        )

    targets: dict[str, dict[str, str]] = {}
    proximity: dict[str, dict[str, dict[str, object]]] = {}
    # Isolated namespace, S104 Step 3 -- NO rule reads this key. See the
    # "Free-verb CONTACTS parsing" section above for the full mechanics.
    contacts: dict[str, list[dict[str, str]]] = {}

    # Directional + proximity tracker -- mirrors extract_relational_targets/
    # extract_proximity_observations' shared block-detection exactly.
    current_feature_rel: str | None = None

    # Free-verb CONTACTS tracker -- S104 Step 3, independent of the
    # directional/proximity tracker above, using its OWN local header regex/
    # alias (_RELATIONSHIP_LINE_HEADER/_RELATIONSHIP_LINE_ALIAS -- names
    # retained post-S107-retirement, see that section's own header-text
    # finding comment above) since Health/Marriage's actual header text
    # ("LINE OF HEALTH:"/"LINE OF MARRIAGE:") is not recognized by either
    # existing header regex. (S107 retired the sibling typed-RELATIONSHIP
    # tracker this comment used to distinguish itself from -- CONTACTS was
    # always its own variable, kept separate from that tracker even while
    # both existed, on purpose.)
    current_feature_contacts: str | None = None

    # Symmetric/convergence tracker -- mirrors extract_convergence_targets'
    # own block-detection exactly (independent of the tracker above).
    current_feature_conv: str | None = None
    block_owner: str | None = None
    pending_location: str | None = None
    # Pattern D step 3: per-block convergence count + which owner (if any)
    # currently holds a bound location -- together they gate the location
    # edge case (Convergence_Location binds ONLY when the block has
    # resolved exactly ONE convergence; a location can't be disambiguated
    # across partners once a second convergence lands, so it is dropped,
    # fail-closed, with a warning). Reset at every block boundary alongside
    # the state above.
    conv_count_this_block = 0
    location_owner: str | None = None

    def _flush_conv_block_boundary() -> None:
        nonlocal current_feature_conv, block_owner, pending_location, conv_count_this_block, location_owner
        if pending_location is not None:
            logger.info(
                "observation_extractor.extract_relations: dropped orphan "
                "CONVERGENCE_LOCATION=%r for feature=%r -- no valid "
                "CONVERGENCE resolved in the same block.",
                pending_location, current_feature_conv,
            )
        current_feature_conv = None
        block_owner = None
        pending_location = None
        conv_count_this_block = 0
        location_owner = None

    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            current_feature_rel = None
            current_feature_contacts = None
            _flush_conv_block_boundary()
            continue

        rel_header_matched = False
        header = _RELATIONAL_HEADER.match(stripped)
        if header:
            rel_header_matched = True
            line_label = header.group(1).strip().lower()
            current_feature_rel = _RELATIONAL_LINE_ALIAS.get(line_label)
        else:
            line_header = _LINE_HEADER.match(stripped)
            if line_header:
                rel_header_matched = True
                line_label = line_header.group(1).strip().lower()
                current_feature_rel = _RELATIONAL_LINE_ALIAS.get(line_label)

        conv_header_matched = False
        conv_header = _CONVERGENCE_RELATIONAL_HEADER.match(stripped)
        if conv_header:
            conv_header_matched = True
            _flush_conv_block_boundary()
            line_label = conv_header.group(1).strip().lower()
            current_feature_conv = _CONVERGENCE_LINE_ALIAS.get(line_label)
        else:
            conv_line_header = _CONVERGENCE_LINE_HEADER.match(stripped)
            if conv_line_header:
                conv_header_matched = True
                _flush_conv_block_boundary()
                line_label = conv_line_header.group(1).strip().lower()
                current_feature_conv = _CONVERGENCE_LINE_ALIAS.get(line_label)

        typed_header_matched = False
        typed_header = _RELATIONSHIP_LINE_HEADER.match(stripped)
        if typed_header:
            typed_header_matched = True
            line_label = typed_header.group(1).strip().lower()
            # S107 retired the sibling typed-RELATIONSHIP tracker that
            # used to also flip here -- CONTACTS is now the only consumer
            # of this header event, still reusing the same
            # _RELATIONSHIP_LINE_HEADER/_RELATIONSHIP_LINE_ALIAS names
            # (kept, see the CONTACTS tracker's own comment above for why).
            current_feature_contacts = _RELATIONSHIP_LINE_ALIAS.get(line_label)

        if rel_header_matched or conv_header_matched or typed_header_matched:
            # A header line's text can never also match a subfield regex
            # (disjoint shapes by construction) -- skipping mirrors the
            # `continue` each source function takes after its own header
            # match, with an identical net effect.
            continue

        # --- free-verb CONTACTS subfield (Step 3, S104) ---
        sub_contacts = _CONTACTS_SUBFIELD.match(stripped)
        if sub_contacts and current_feature_contacts is not None:
            # Mark "a CONTACTS line was seen for this feature" regardless of
            # parse outcome (valid / malformed / explicit 'none') -- this is
            # what makes a feature's total ABSENCE from `contacts` mean
            # "no CONTACTS line at all" (MISSING), distinct from "declared
            # none" (present, empty list).
            contacts.setdefault(current_feature_contacts, [])
            raw_contacts_value = sub_contacts.group(1)
            try:
                parsed_contact = _parse_contacts_value(raw_contacts_value)
            except Exception as exc:  # noqa: BLE001 -- malformed line must not kill the rest of the block
                logger.info(
                    "observation_extractor.extract_relations: failed parsing "
                    "CONTACTS value=%r for feature=%r: %s -- quarantined.",
                    raw_contacts_value, current_feature_contacts, exc,
                )
            else:
                if parsed_contact is not None:
                    c_target, c_verb, c_position_raw, c_clarity_raw = parsed_contact
                    _store_contact(
                        contacts, current_feature_contacts, c_target, c_verb,
                        c_position_raw, c_clarity_raw,
                    )

        # --- directional / proximity subfield ---
        sub = _RELATIONAL_SUBFIELD.match(stripped)
        if sub and current_feature_rel is not None:
            field, raw_value = sub.group(1), sub.group(2).strip()
            attr = _RELATIONAL_FIELD_TO_ATTR[field]
            strategy = _RELATION_TYPES[attr]

            landmark = _proximity_landmark(raw_value) if field == "PROXIMITY" else raw_value
            if landmark not in _RELATION_TARGET_REGISTRY:
                logger.info(
                    "observation_extractor.extract_relations: dropped "
                    "feature=%r field=%r landmark=%r -- not in "
                    "relation_target_registry (or 'none'/'n/a').",
                    current_feature_rel, field, landmark,
                )
            else:
                targets.setdefault(current_feature_rel, {})[attr] = landmark
                if strategy == "directional":
                    _log_off_menu_caveat(current_feature_rel, field, landmark)

            if strategy == "proximity":
                # try/except/else mirrors extract_proximity_observations'
                # original try/except-continue + if-continue structure
                # exactly: on exception, ONLY the exception log fires (the
                # "not in {touching, medium, distant}" log is skipped, same
                # as the original's `continue` skipping it); on no
                # exception, the degree is validated and either filed or
                # logged as dropped -- degree=None is not special-cased and
                # falls into the same "not in {...}" drop log as any other
                # invalid degree string, identical to the original.
                try:
                    degree = _proximity_degree(raw_value)
                except Exception as exc:  # noqa: BLE001 -- never a bare traceback for a parse slip
                    logger.info(
                        "observation_extractor.extract_relations: failed "
                        "splitting PROXIMITY value %r for feature=%r: %s",
                        raw_value, current_feature_rel, exc,
                    )
                else:
                    if degree not in _PROXIMITY_DEGREE_VALUES:
                        logger.info(
                            "observation_extractor.extract_relations: dropped "
                            "feature=%r degree=%r -- not in {touching, medium, "
                            "distant} (or 'n/a'/missing).",
                            current_feature_rel, degree,
                        )
                    else:
                        proximity.setdefault(current_feature_rel, {})["Proximity"] = {
                            "value": degree, "confidence": 1.0,
                        }

        # --- symmetric / convergence subfield ---
        sub_conv = _CONVERGENCE_SUBFIELD.match(stripped)
        if sub_conv and current_feature_conv is not None:
            field, raw_value = sub_conv.group(1), sub_conv.group(2).strip()
            value = raw_value.strip()

            if not value or value.lower() in ("none", "n/a"):
                logger.info(
                    "observation_extractor.extract_relations: dropped "
                    "feature=%r field=%r -- empty/none/n-a value.",
                    current_feature_conv, field,
                )
            elif field == "CONVERGENCE":
                if value not in _RELATION_TARGET_REGISTRY:
                    logger.info(
                        "observation_extractor.extract_relations: dropped "
                        "feature=%r CONVERGENCE target=%r -- not in "
                        "relation_target_registry.",
                        current_feature_conv, value,
                    )
                elif value == current_feature_conv:
                    logger.info(
                        "observation_extractor.extract_relations: dropped "
                        "self-convergence for feature=%r.", current_feature_conv,
                    )
                else:
                    _log_off_menu_caveat(current_feature_conv, "CONVERGENCE", value)
                    owner, other = _canonicalize_convergence(current_feature_conv, value)
                    if _is_multi(_CONVERGENCE_ATTR):
                        targets.setdefault(owner, {}).setdefault(_CONVERGENCE_ATTR, set()).add(other)
                    else:
                        targets.setdefault(owner, {})[_CONVERGENCE_ATTR] = other
                    block_owner = owner
                    conv_count_this_block += 1

                    if conv_count_this_block > 1:
                        # Second-or-later convergence in this block: the
                        # location can no longer be attributed to a single
                        # partner -- drop anything already bound or still
                        # pending, fail-closed, warned (never silent).
                        if location_owner is not None:
                            dropped_loc = targets.get(location_owner, {}).pop(_CONVERGENCE_LOCATION_ATTR, None)
                            if dropped_loc is not None:
                                logger.warning(
                                    "observation_extractor.extract_relations: dropped "
                                    "already-bound CONVERGENCE_LOCATION=%r for feature=%r "
                                    "-- block now has %d convergences, location cannot "
                                    "be disambiguated across partners.",
                                    dropped_loc, current_feature_conv, conv_count_this_block,
                                )
                            location_owner = None
                        if pending_location is not None:
                            logger.warning(
                                "observation_extractor.extract_relations: dropped "
                                "buffered CONVERGENCE_LOCATION=%r for feature=%r -- "
                                "block now has %d convergences, location cannot be "
                                "disambiguated across partners.",
                                pending_location, current_feature_conv, conv_count_this_block,
                            )
                            pending_location = None
                    elif pending_location is not None:
                        # First (and so far only) convergence in this block --
                        # normal single-convergence binding, unchanged (F025b).
                        if pending_location not in _RELATION_TARGET_REGISTRY:
                            logger.info(
                                "observation_extractor.extract_relations: dropped "
                                "buffered CONVERGENCE_LOCATION=%r for feature=%r -- "
                                "not in relation_target_registry.",
                                pending_location, current_feature_conv,
                            )
                        else:
                            targets.setdefault(block_owner, {})[_CONVERGENCE_LOCATION_ATTR] = pending_location
                            location_owner = block_owner
                        pending_location = None
            else:  # field == "CONVERGENCE_LOCATION"
                if value not in _RELATION_TARGET_REGISTRY:
                    logger.info(
                        "observation_extractor.extract_relations: dropped "
                        "feature=%r CONVERGENCE_LOCATION=%r -- not in "
                        "relation_target_registry.",
                        current_feature_conv, value,
                    )
                elif conv_count_this_block > 1:
                    # Block already has >1 convergence -- never bind, same
                    # fail-closed rule as the CONVERGENCE-side check above.
                    logger.warning(
                        "observation_extractor.extract_relations: dropped "
                        "CONVERGENCE_LOCATION=%r for feature=%r -- block already "
                        "has %d convergences, location cannot be disambiguated "
                        "across partners.",
                        value, current_feature_conv, conv_count_this_block,
                    )
                else:
                    _log_off_menu_caveat(current_feature_conv, "CONVERGENCE_LOCATION", value)
                    if block_owner is not None:
                        targets.setdefault(block_owner, {})[_CONVERGENCE_LOCATION_ATTR] = value
                        location_owner = block_owner
                    else:
                        pending_location = value

    _flush_conv_block_boundary()  # flush end-of-text: log a still-pending orphan location

    return {"targets": targets, "proximity": proximity, "contacts": contacts}


# ─── Mount DEVELOPMENT grade parsing (S117 vision-emission follow-up) ─────
# Parses the "  DEVELOPMENT (<mount>): <value>" lines agent/palm_processor.py
# emits for the 5 GRADED mounts (Venus/Jupiter/Saturn/the Sun/Upper Mount of
# Mars -- Mercury/Lower Mount of Mars/Luna are presence-only and never carry
# one) into a `{registry_feature: {"Development": value}} `observation dict.
#
# WHY A NEW FUNCTION, NOT extract_relations()/extract_observation(): traced
# both existing closed-vocab paths before writing this (per the instructing
# prompt) and neither is a match --
#   - SLOPE (head/heart) and FATE's BREAK TYPE have NO dedicated regex/line
#     parse anywhere in this codebase. Both ride extract_observation()'s
#     single whole-feature-prose LLM call: the vision line's text is just
#     part of the joined raw_text handed to the extraction model, which
#     independently judges the attribute's value from that prose, guarded
#     post-hoc by `attribute_value_binding` (module docstring point 5). That
#     guard is PER-ATTRIBUTE globally (`_values_for_attribute`), not
#     per-feature -- it cannot express "Venus has a 10-value menu, Jupiter a
#     3-value menu" for the same "Development" attribute at all, which the
#     locked per-mount-menu design requires. (FATE LINE BREAK TYPE's own
#     routing into Continuity is flagged elsewhere in this codebase as
#     "not traced or tested" -- consistent with there being no dedicated
#     parse to trace.)
#   - DEVELOPMENT's line shape ("LABEL (<name>): <value>", self-naming its
#     own feature inline) is structurally closest to this file's OTHER
#     deterministic closed-vocab precedent instead: extract_relations()'s
#     ORIGIN/TERMINATION/PROXIMITY/BRANCHES_TO parsing and (even more so,
#     since DEVELOPMENT needs no surrounding-block context) _store_contact's
#     per-feature target-menu gate ("off-menu -> dropped + logged
#     (quarantine), never guessed" -- copied verbatim below). Pure
#     deterministic regex over the vision model's own raw text, no LLM
#     call, never raises for missing/malformed text -- same contract as
#     extract_relations().
#
# NOT bound into ontology_registry.json's `attribute_value_binding` here
# (bind-LAST discipline -- Step 4, atomic with rule authoring, owns that).
# `_MOUNT_DEVELOPMENT_MENUS` below is a CODE-LOCAL guard scoped only to this
# parse function, not a registry write.

_DEVELOPMENT_LINE = re.compile(r"^DEVELOPMENT \(([^)]+)\):\s*(.+)$")

# Per-mount closed menu, hand-mirrored from agent/palm_processor.py's Step 2
# emission (no shared constant exists there to import from without touching
# that file, which is out of THIS task's one-file scope) -- if that prompt's
# menus ever change, this table must change with them. Keyed by
# palm_reading._FEATURE_REGISTRY's own spelling (not this module's
# capitalized ontology names), since that is the registry key the rules
# layer will eventually read Development observations under (per the
# instructing prompt's own worked examples: "the Sun -> mount of apollo",
# "Upper Mount of Mars -> mount of mars positive"). "not notably developed"
# and "cannot-tell" are present on every menu -- the two mandatory escape
# hatches, never dropped.
_MOUNT_DEVELOPMENT_MENUS: dict[str, frozenset[str]] = {
    "mount of venus": frozenset({
        "well developed", "small", "abnormally large", "full and large",
        "very poor development", "not well developed", "depressed",
        "very high", "not notably developed", "cannot-tell",
    }),
    "mount of jupiter": frozenset({
        "developed", "not notably developed", "cannot-tell",
    }),
    "mount of saturn": frozenset({
        "well developed", "unusually high", "not notably developed", "cannot-tell",
    }),
    "mount of apollo": frozenset({
        "well developed", "not notably developed", "cannot-tell",
    }),
    "mount of mars positive": frozenset({
        "large", "present", "not notably developed", "cannot-tell",
    }),
}


def _mount_feature_from_vision_name(vision_name: str) -> str | None:
    """Maps a DEVELOPMENT line's parenthetical (verbatim vision naming,
    e.g. "the Sun", "Upper Mount of Mars") to its `palm_reading.
    _FEATURE_REGISTRY` key, by reusing `palm_reading._SUB_FEATURES`'
    needle table (S117) -- the SAME needle-substring technique
    `palm_reading._gather_feature_texts` already uses to detect which
    mount a MOUNTS-field clause names, restricted to MOUNTS-flat-label
    entries only (excludes "sun line"'s own "sun" needle, a different
    flat_label, so "the Sun" can never resolve to the sun LINE feature).
    Generalization gate: no second, independently-authored name map.
    Returns None for an unrecognized name (never guessed).

    Lazy, function-scoped import of `palm_reading` -- see module docstring
    for why this is the one deliberate exception to this module's
    standalone contract."""
    from agent.interpretive.palm_reading import _SUB_FEATURES  # local, see module docstring

    name_low = vision_name.strip().lower()
    for feature, flat_label, _bullet_label, needle in _SUB_FEATURES:
        if flat_label == "MOUNTS" and needle in name_low:
            return feature
    return None


def _store_mount_development(
    development: dict[str, dict[str, str]],
    vision_name: str,
    value_raw: str,
) -> None:
    """Files one parsed DEVELOPMENT line into `development[feature]`.
    Mirrors `_store_contact`'s gate-and-log shape exactly: an unrecognized
    mount name, a presence-only mount (no menu at all), or an off-menu
    value are each dropped + logged (quarantined), never guessed or
    coerced. "cannot-tell"/"not notably developed" are ordinary menu
    members here, not special-cased -- they pass straight through like
    any other legal value."""
    feature = _mount_feature_from_vision_name(vision_name)
    if feature is None:
        logger.info(
            "observation_extractor.extract_mount_development: vision mount name "
            "%r does not match any known mount alias -- dropped (quarantined).",
            vision_name,
        )
        return

    menu = _MOUNT_DEVELOPMENT_MENUS.get(feature)
    if menu is None:
        logger.info(
            "observation_extractor.extract_mount_development: feature=%r has no "
            "DEVELOPMENT menu (presence-only mount, never asked a grade question) "
            "-- dropped value %r (quarantined).",
            feature, value_raw,
        )
        return

    value = value_raw.strip()
    if value not in menu:
        logger.info(
            "observation_extractor.extract_mount_development: feature=%r value=%r "
            "not in this mount's closed DEVELOPMENT menu %r -- dropped (quarantined).",
            feature, value, sorted(menu),
        )
        return

    development[feature] = {"Development": value}


def extract_mount_development(raw_text: str) -> dict[str, dict[str, str]]:
    """Parses every "  DEVELOPMENT (<mount>): <value>" line in `raw_text`
    into `{registry_feature: {"Development": value}}`. Pure deterministic
    string parse of the vision model's own raw output -- no LLM call, no
    dependency on `extract_observation`'s closed-vocabulary pool/binding
    (see the section comment above for why). Never raises for missing/
    malformed text -- returns `{}` for "no signal", same convention as
    `extract_relations`.

    Deliberately state-free (no current-feature tracker, unlike
    extract_relations' ORIGIN/TERMINATION parsing): each DEVELOPMENT line
    names its own mount inline, so no surrounding section-header context
    is needed to resolve it.
    """
    if not isinstance(raw_text, str):
        raise TypeError(
            "observation_extractor.extract_mount_development: raw_text must be a "
            f"str, got {type(raw_text).__name__}"
        )

    development: dict[str, dict[str, str]] = {}
    for line in raw_text.splitlines():
        m = _DEVELOPMENT_LINE.match(line.strip())
        if not m:
            continue
        vision_name, value_raw = m.group(1), m.group(2)
        _store_mount_development(development, vision_name, value_raw)
    return development


def translate_mount_development(
    mount_development: dict[str, dict[str, str]]
) -> dict[str, dict[str, str]]:
    """Translates `extract_mount_development`'s own `palm_reading.
    _FEATURE_REGISTRY`-style keys (e.g. "mount of venus", "mount of
    apollo") into the capitalized ontology feature names (e.g. "Mount of
    Venus", "Mount of the Sun") every rule file's antecedents and the
    `observation` dict `palm_rules_table.match()` reads are keyed by --
    reusing `_FEATURE_ALIAS`, the SAME single source of truth
    `_gather_feature_texts`'s own prose-to-ontology mapping and every
    other consumer of this dict already use (generalization gate: no
    second, independently-authored name map). `extract_mount_development`
    itself is left unchanged -- this is a separate, additive translation
    step, not a change to that function's own output contract (which its
    existing tests assert against directly).

    A key with no `_FEATURE_ALIAS` entry (should not happen for any of
    the 5 currently-graded mounts, all covered above) is dropped and
    logged rather than guessed -- same "never guess" posture as every
    other rejection path in this module."""
    translated: dict[str, dict[str, str]] = {}
    for registry_key, attrs in mount_development.items():
        ontology_feature = _FEATURE_ALIAS.get(registry_key)
        if ontology_feature is None:
            logger.info(
                "observation_extractor.translate_mount_development: registry key "
                "%r has no _FEATURE_ALIAS entry -- dropped.", registry_key,
            )
            continue
        translated[ontology_feature] = dict(attrs)
    return translated


# ─── FLAT sub-field parsing (S123 Step 2: dead-flat-field fix reader) ─────
# Parses the vision-prompt's FLAT (non-relational) closed sub-fields --
# "  SLOPE: <value>", "  SLOPE MAGNITUDE: <value>", "  BREAK TYPE: <value>",
# "  LENGTH EXTENT: <value>" -- into `{ontology_feature: {attribute:
# {"value": str, "write_policy": str}}}`. UNWIRED as of this step: no call
# site in this codebase reads this function yet (Step 4 of the same S123
# arc adds the merge that does); registry-only, behaviour-inert until then.
#
# WHY A NEW FUNCTION, NOT extract_relations()/extract_mount_development():
# these sub-fields carry FLAT scalar values (never a relation_target, so
# extract_relations()'s `targets`-dict shape is the wrong shape for them),
# AND -- unlike extract_mount_development()'s "DEVELOPMENT (<mount>):
# <value>" lines, which self-name their own feature inline -- these
# sub-fields do NOT name their own line; they appear as INDENTED
# continuation lines under a line's own header, exactly the same placement
# extract_relations()'s ORIGIN/TERMINATION/PROXIMITY/BRANCHES_TO subfields
# use. So this parser needs a header tracker -- reusing the module's
# EXISTING `_LINE_HEADER` regex and `_RELATIONAL_LINE_ALIAS` map verbatim
# (the same tracker extract_relations()'s directional/proximity parsing
# uses), never a third, independently-authored header regime.
#
# REGISTRY-DRIVEN, NO HARDCODING: the recognised label set, each label's
# menu/escape/attribute/write_policy, and the regex alternation itself are
# all built ONCE at import time from ontology_registry.json's
# `vision_flat_subfields` block (Step 1/1b). Adding a 4th field to that
# registry block requires ZERO code change here -- `_FLAT_SUBFIELD_REGISTRY`/
# `_FLAT_SUBFIELD_LABELS`/`_FLAT_SUBFIELD` all regenerate from whatever the
# block currently declares. The block's own `"_note"` key is documentation,
# not a feature -- skipped explicitly (same "leading underscore = meta, not
# data" convention `vision_relational_menus`'s own `_note`/`_convergence_note`/
# `_location_note` already use elsewhere in the registry).


def _build_flat_subfield_registry() -> dict[str, dict[str, dict[str, object]]]:
    """`{ontology_feature: {LABEL: {"attribute", "menu" (frozenset),
    "escape" (frozenset), "write_policy"}}}`, derived once from
    ontology_registry.json's `vision_flat_subfields` block. Skips any
    feature-level key starting with `"_"` (currently just `"_note"`) --
    documentation, not a parseable feature."""
    raw = _REGISTRY.get("vision_flat_subfields", {})
    registry: dict[str, dict[str, dict[str, object]]] = {}
    for feature, fields in raw.items():
        if feature.startswith("_"):
            continue
        registry[feature] = {
            label: {
                "attribute": spec["attribute"],
                "menu": frozenset(spec["menu"]),
                "escape": frozenset(spec["escape"]),
                "write_policy": spec["write_policy"],
            }
            for label, spec in fields.items()
        }
    return registry


_FLAT_SUBFIELD_REGISTRY: dict[str, dict[str, dict[str, object]]] = _build_flat_subfield_registry()

# Every recognised label across every feature, LONGEST FIRST -- so a regex
# alternation tries "SLOPE MAGNITUDE" before "SLOPE" and can never mis-match
# "SLOPE MAGNITUDE: slight" as "SLOPE:" followed by " MAGNITUDE: slight"
# junk. Sorting by length (not alphabetically) is what guarantees this for
# ANY future label the registry adds, not just today's 4 -- a lexical sort
# would only separate "BREAK TYPE" from "SLOPE" by coincidence of their
# first character, not by construction; length-descending is the only order
# that structurally guarantees a longer label is tried before any label
# that is one of its own prefixes.
_FLAT_SUBFIELD_LABELS: tuple[str, ...] = tuple(sorted(
    {label for fields in _FLAT_SUBFIELD_REGISTRY.values() for label in fields},
    key=len, reverse=True,
))

_FLAT_SUBFIELD: re.Pattern | None = (
    re.compile(r"^(" + "|".join(re.escape(lbl) for lbl in _FLAT_SUBFIELD_LABELS) + r"):\s*(.*)$")
    if _FLAT_SUBFIELD_LABELS else None
)


def _store_flat_subfield(
    result: dict[str, dict[str, dict[str, str]]],
    feature: str,
    label: str,
    value_raw: str,
) -> None:
    """Files one parsed flat-subfield line into `result[feature][attribute]`.
    Three gates, each dropped + logged (quarantine), never coerced or
    guessed -- mirrors `_store_mount_development`'s gate-and-log shape:
      (a) `label` not declared for `feature` in the registry (e.g. "BREAK
          TYPE" seen under HEAD LINE, which only declares SLOPE/SLOPE
          MAGNITUDE)
      (b) `value` is one of this entry's ESCAPE values -- honest silence,
          never written, per vision_flat_subfields's own `_note` semantics
          (i)
      (c) `value` is neither an escape value nor a menu member -- an
          off-menu token, quarantined rather than coerced to the nearest
          legal value

    Comparison is CASE-SENSITIVE on the stripped value, matching
    `_store_mount_development`'s own precedent (no `.lower()` anywhere in
    that function either) -- the vision prompt's own closed-menu wording
    ("exactly one of {upward | downward | straight | ...}") is a verbatim
    contract the model is instructed to reproduce exactly, so a
    case-differing answer is itself signal worth quarantining, not noise to
    normalize away.

    Same label appearing twice under one line's block: LAST occurrence
    WINS (plain dict-key overwrite) -- these are single-valued flat scalar
    attributes with no accumulation semantics, unlike CONTACTS' per-feature
    list."""
    feature_spec = _FLAT_SUBFIELD_REGISTRY.get(feature, {})
    entry = feature_spec.get(label)
    if entry is None:
        logger.info(
            "observation_extractor.extract_flat_subfields: label %r not "
            "declared for feature=%r in vision_flat_subfields -- dropped "
            "(quarantined).",
            label, feature,
        )
        return

    value = value_raw.strip()
    if value in entry["escape"]:
        logger.info(
            "observation_extractor.extract_flat_subfields: feature=%r "
            "label=%r value=%r is an escape value -- honest silence, "
            "dropped (never written).",
            feature, label, value,
        )
        return

    if value not in entry["menu"]:
        logger.info(
            "observation_extractor.extract_flat_subfields: feature=%r "
            "label=%r value=%r not in this field's closed menu %r -- "
            "dropped (quarantined).",
            feature, label, value, sorted(entry["menu"]),
        )
        return

    result.setdefault(feature, {})[entry["attribute"]] = {
        "value": value,
        "write_policy": entry["write_policy"],
    }


def extract_flat_subfields(raw_text: str) -> dict[str, dict[str, dict[str, str]]]:
    """Parses every recognised FLAT closed sub-field line (SLOPE, SLOPE
    MAGNITUDE, BREAK TYPE, LENGTH EXTENT -- as currently declared in
    ontology_registry.json's `vision_flat_subfields` block) into
    `{ontology_feature: {attribute: {"value": str, "write_policy": str}}}`.

    UNWIRED as of S123 Step 2 -- no call site in this codebase reads this
    function yet; Step 4 of the same arc adds the merge that does. Pure
    deterministic string parse of the vision model's own raw output, no LLM
    call -- never raises for missing/malformed text, returns `{}` for "no
    signal" (empty text, no headers, only malformed lines), same convention
    as `extract_mount_development`/`extract_relations`.

    HEADER TRACKING: unlike `extract_mount_development` (state-free -- each
    DEVELOPMENT line self-names its own mount inline), these sub-field lines
    do NOT name their own line; they are INDENTED continuation lines under
    a line's own header ("HEAD LINE:", "HEART LINE:", "FATE LINE:"). Reuses
    the module's EXISTING `_LINE_HEADER` regex + `_RELATIONAL_LINE_ALIAS` map
    verbatim (the same tracker `extract_relations`'s directional/proximity
    parsing uses) -- no third, independently-authored header regime. A
    header `_RELATIONAL_LINE_ALIAS` doesn't map (e.g. "LIFE LINE:", which
    has no vision_flat_subfields entry) sets the tracker to None, so any
    sub-field lines under it are silently ignored -- same mechanism, not a
    special case. A blank line resets the tracker to None (mirrors
    `extract_relations`'s own block-boundary convention). A sub-field line
    seen before ANY header (tracker still None) is likewise silently
    skipped -- consistent with `extract_relations`'s own subfield checks,
    which only proceed `if current_feature_rel is not None`.

    write_policy TRAVELS WITH THE VALUE in the return shape specifically so
    Step 4's merge does not have to re-derive it from the registry a second
    time. Do NOT reuse `merge_relational_targets` for this shape -- that
    function's set/scalar cardinality-aware accumulation is designed for
    `targets`-shaped landmark dicts, not this policy-aware
    authoritative-vs-fill_only value shape; Step 4 needs its own
    policy-aware merge (authoritative overwrites unconditionally, fill_only
    only fills an empty slot), not implemented here.
    """
    if not isinstance(raw_text, str):
        raise TypeError(
            "observation_extractor.extract_flat_subfields: raw_text must be "
            f"a str, got {type(raw_text).__name__}"
        )

    result: dict[str, dict[str, dict[str, str]]] = {}
    if _FLAT_SUBFIELD is None:
        return result

    current_feature: str | None = None
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            current_feature = None
            continue

        header = _LINE_HEADER.match(stripped)
        if header:
            line_label = header.group(1).strip().lower()
            current_feature = _RELATIONAL_LINE_ALIAS.get(line_label)
            continue

        if current_feature is None:
            continue

        m = _FLAT_SUBFIELD.match(stripped)
        if not m:
            continue
        label, value_raw = m.group(1), m.group(2)
        _store_flat_subfield(result, current_feature, label, value_raw)

    return result


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


def _call_llm(
    client, model: str, messages: list[dict], ontology_features: list[str],
    *, capture: dict | None = None, max_tokens_override: int | None = None,
) -> str:
    """Single try/except boundary around the one API call this module ever
    makes. A failure here is re-raised as a RuntimeError naming the whole
    feature batch this call was for -- never swallowed into a silent
    empty result.

    capture: optional out-param dict; when passed, populated with this
        call's `finish_reason` (via getattr, defaulting None for any
        test double that doesn't model it). Kept as an out-param rather
        than widening the return type so the str-only return contract
        stays unchanged for this function's signature in general, even
        though it currently has exactly one caller (the parse-failure
        retry below uses this to log truncation vs malformation).
    max_tokens_override: when set, replaces ASTRO_EXTRACT_MAX_TOKENS for
        this call only -- used by the parse-failure retry to raise the
        cap on a resample without touching the module-wide default.
    """
    start = time.monotonic()
    max_tokens = (
        max_tokens_override if max_tokens_override is not None
        else int(os.getenv("ASTRO_EXTRACT_MAX_TOKENS", "1500"))
    )
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
            # raises ValueError -> the parse-failure retry below (correct); a resample
            # of that retry raises this cap via max_tokens_override.
            max_tokens=max_tokens,
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
    if capture is not None:
        capture["finish_reason"] = getattr(response.choices[0], "finish_reason", None)
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


# ─── Parse-failure guard -- bounded resample on malformed/truncated JSON ─
# `_parse_response` raises ValueError on EITHER a JSONDecodeError or a
# well-formed-but-wrong-shape response. Left unguarded, that raise used to
# escape from inside the dropped-feature retry loop below BEFORE that
# loop's own retry logic ever ran -- a malformed/truncated response crashed
# the whole extraction instead of getting a chance to resample. Real-hand
# dogfood hit this live (manually retrying the same call succeeded).
# Distinct from the dropped-feature guard: that one handles a well-formed
# response that's missing a feature; this one handles a response that
# never parsed as JSON at all.

def _call_llm_and_parse(
    client, model: str, messages: list[dict], ontology_features: list[str],
) -> tuple[dict, dict]:
    """Wraps one `_call_llm` + `_parse_response` pair with a bounded
    resample on ValueError (parse failure). THRESHOLD:
    ASTRO_EXTRACT_PARSE_RETRIES=2 (2 resamples, 3 attempts total for this
    parse-failure path alone) -- absorbs one transient malformation
    without unbounded cost; consistent with this module's other
    ASTRO_EXTRACT_* retry env knobs. Env-overridable.

    Each resample does BOTH, since either truncation or genuine
    malformation could be the cause: (a) raises max_tokens for the retry
    call only, via `max_tokens_override` (the 1500 default cap is the
    likely truncation cause -- 2400 is truncation headroom, not a tuned
    value), (b) appends a corrective instruction asking for complete
    valid JSON. Logs `finish_reason` + `len(raw)` on every parse failure
    at INFO -- this is how truncation (finish_reason=='length') vs
    genuine malformation gets told apart for real, over time.

    On exhaustion, re-raises the SAME ValueError `_parse_response` raised
    (fail-closed, unchanged failure contract -- never fabricates a result;
    whether to degrade gracefully instead of raising is a separate,
    undecided product question, not addressed here)."""
    parse_retries = int(os.getenv("ASTRO_EXTRACT_PARSE_RETRIES", "2"))
    current_messages = messages
    last_exc: ValueError | None = None

    for parse_attempt in range(parse_retries + 1):
        capture: dict[str, object] = {}
        max_tokens_override = (
            int(os.getenv("ASTRO_EXTRACT_PARSE_RETRY_MAX_TOKENS", "2400"))
            if parse_attempt > 0 else None
        )
        raw = _call_llm(
            client, model, current_messages, ontology_features,
            capture=capture, max_tokens_override=max_tokens_override,
        )
        try:
            return _parse_response(raw)
        except ValueError as exc:
            last_exc = exc
            logger.info(
                "observation_extractor.extract_observation: parse failure on attempt "
                "%d/%d for feature batch %s -- finish_reason=%r, len(raw)=%d.",
                parse_attempt + 1, parse_retries + 1, sorted(ontology_features),
                capture.get("finish_reason"), len(raw),
            )
            if parse_attempt < parse_retries:
                current_messages = messages + [{
                    "role": "user",
                    "content": (
                        "Your previous reply was not valid complete JSON. Return a "
                        "single complete, valid JSON object and nothing else."
                    ),
                }]

    raise last_exc


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
        observations_raw, unmapped_raw = _call_llm_and_parse(
            client, model, current_messages, ontology_features,
        )
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
