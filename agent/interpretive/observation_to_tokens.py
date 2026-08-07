"""
agent/interpretive/observation_to_tokens.py
Pure adapter: converts a palm-vision observation payload into the
(observation, magnitudes) inputs agent.interpretive.palm_rules_table.match()
consumes. No calls into palm_reading.py or any runtime module -- this file
is dependency-free (stdlib json + pathlib only) and importable in isolation,
same standalone posture palm_rules_table.py and palm_vocab.py already take.

CONTRACT (see to_tokens() below):
    to_tokens(vision_payload) -> (observation, magnitudes)
    observation: {feature: {attribute: value}} -- every (feature, attribute,
        value) triple is validated against data/ontology_registry.json;
        anything not in the registry is silently DROPPED from observation
        and recorded in magnitudes["_dropped"] (never coerced, never
        invented).
    magnitudes: {feature: {attribute: float_confidence}} -- an UNFILTERED
        passthrough of whatever confidence each vision_payload entry
        supplies (default 1.0 if absent). Deliberately NOT gated by
        registry validity -- see "Design decision: magnitudes are
        unfiltered" below. Also carries two always-present diagnostic
        list keys: magnitudes["_dropped"] (invalid (feature, attribute,
        value) triples rejected by the registry) and
        magnitudes["_canonicalized"] (line-feature-only Thickness -> Width
        canonicalization actions -- see _canonicalize_thickness_to_width()
        below; empty list when no canonicalization fired).

VISION_PAYLOAD SHAPE (not specified upstream anywhere at time of writing --
no producer of "the palm-vision observation payload" exists yet in this
codebase; this is the shape this adapter defines and requires):
    {
        "<Feature Name>": {
            "<Attribute Name>": {"value": "<token>", "confidence": <float>},
            ...
        },
        ...
    }
"confidence" is optional per entry (defaults to 1.0). "value" is required;
its absence raises (see to_tokens()'s try/except).

=== Discrepancies discovered against this task's own stated contract ===
(flagged per project convention -- verify prompts against code, don't
silently paper over a mismatch)

1. Registry version mismatch. The task text says "ontology_registry.json
   (v1.3.0)". The actual file on disk (data/ontology_registry.json) states
   `"meta": {"version": "1.2.0"}`. Proceeding against the REAL file (1.2.0)
   since that's what exists on disk -- there is no v1.3.0 file anywhere in
   the repo (confirmed: only one ontology_registry.json exists). Not a
   STOP-worthy case (that gate was scoped explicitly to the match()
   signature, which was verified to match exactly), but surfaced here for
   Sulabh's awareness.

2. The registry's own `meta` block is internally inconsistent with its own
   content and is NOT used by this adapter for anything. Measured directly:
   meta claims total_features=84, but the `features` dict's category lists
   flatten to 69 entries (68 distinct after de-duplication). meta claims
   total_attributes=19, but `attributes` flattens to 63 entries (42
   distinct). meta claims total_values=293, but `values` flattens to 274
   entries (212 distinct). This adapter derives its valid-token sets
   exclusively from the actual `features` / `attributes` / `values` /
   `attribute_feature_mapping` arrays, never from the `meta` counts, which
   this measurement shows cannot be trusted as a cross-check.

3. No explicit attribute -> value-category linkage exists in the registry.
   Category names in `values` (e.g. "depth_values", "shape_values") do not
   map 1:1 onto `attributes` category names, and several real,
   Sulabh-verified rules need cross-category value use to validate at all
   -- e.g. HL_006 (Quadrangle/Breadth="narrow") requires "narrow" (found
   under shape_values / palm_shape_values / hand_size_values) to be valid
   for the "Breadth" attribute, even though no "breadth_values" category
   exists. Given the registry provides no authoritative narrower binding,
   this adapter treats the FLATTENED UNION of every values-category list as
   the valid value pool for ANY attribute that is itself valid for the
   observed feature (per `attribute_feature_mapping`) -- the only reading
   of this registry's actual structure that does not incorrectly reject
   real verified production rules. A stricter per-attribute value binding
   would need the registry itself to add that linkage; not invented here.

4. Registry `synonyms` are NOT treated as valid feature tokens by this
   adapter -- only canonical feature names (the strings actually listed
   under `features`) validate. All 43 real validated_candidates rules in
   data/palm_rules_head_heart_v1.json use canonical names exclusively (e.g.
   "Line of Heart", never "Mensal"), so this loses no real coverage, and
   avoids adding an unrequested synonym-resolution/normalization step this
   task's contract never asked for.

5. Gap surfaced, NOT fixed here (out of this adapter's scope): three real
   verified rules -- H_018, H_019, H_020 -- use antecedent
   feature="Hand", attribute="Type" (values "square"/"spatulate"/
   "philosophic"). Neither "Hand" nor "Type" exist anywhere in
   ontology_registry.json's schema -- the registry instead encodes hand
   type as whole FEATURE names (e.g. "Square Hand") under the
   `hand_shapes` category, with no separate "Type" attribute at all. Any
   vision_payload entry shaped like {"Hand": {"Type": {...}}} will always
   be dropped by this adapter (correctly, per the registry as it actually
   is) -- meaning H_018/H_019/H_020 can never fire through this validated
   pipeline as currently modeled by either side. This is a genuine
   modeling mismatch between palm_rules_table.py's real rule data and
   ontology_registry.json's schema, not something this pure-adapter task
   is scoped to resolve.
"""

from __future__ import annotations

import json
from pathlib import Path

_DEFAULT_REGISTRY_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "ontology_registry.json"
)


def _load_registry(path: Path | str = _DEFAULT_REGISTRY_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


_REGISTRY = _load_registry()

# attribute -> frozenset of feature names that attribute is valid for.
# Authoritative straight from the registry's own attribute_feature_mapping
# -- no guessing needed for this half of the contract.
_ATTRIBUTE_FEATURE_MAP: dict[str, frozenset[str]] = {
    attribute: frozenset(features)
    for attribute, features in _REGISTRY["attribute_feature_mapping"].items()
}

# Flattened union of every values-category list. See module docstring
# point 3 for why this is a flat pool rather than a per-attribute split.
_ALL_VALUES: frozenset[str] = frozenset(
    value for value_list in _REGISTRY["values"].values() for value in value_list
)

# The full valid (feature, attribute, value) triple set, built once at
# module load for O(1) membership checks in to_tokens().
_VALID_TRIPLES: frozenset[tuple[str, str, str]] = frozenset(
    (feature, attribute, value)
    for attribute, features in _ATTRIBUTE_FEATURE_MAP.items()
    for feature in features
    for value in _ALL_VALUES
)


def _is_valid_triple(feature: str, attribute: str, value: object) -> bool:
    if not isinstance(value, str):
        return False
    return (feature, attribute, value) in _VALID_TRIPLES


# Feature set for the Thickness -> Width canonicalization in to_tokens().
# VERIFIED against data/ontology_registry.json: a "Line of " prefix check
# was considered and REJECTED -- 7 of the 17 entries in the registry's own
# "lines" category (Via Lasciva, Girdle of Venus, Ring of Saturn, Ring of
# Solomon, Bracelets, Travel Line, Child Line) do not start with "Line of ".
# Using the registry's "lines" category directly instead, so this set stays
# correct if the registry gains/loses a line feature.
_WIDTH_VALID_FEATURES: frozenset[str] = _ATTRIBUTE_FEATURE_MAP.get("Width", frozenset())
# Intersected with Width's own valid-feature set so canonicalization only
# fires where a Width-keyed rule could ever benefit -- self-maintaining as
# the registry's Width mapping changes (e.g. "Line of Sun"/"Via Lasciva"
# are in "lines" but not in Width's mapping, so a Thickness there stays on
# the normal validation path instead of being renamed to an attribute that
# would just get dropped as invalid for that feature anyway).
_LINE_FEATURES: frozenset[str] = frozenset(_REGISTRY["features"]["lines"]) & _WIDTH_VALID_FEATURES


def _canonicalize_thickness_to_width(
    feature: str,
    attribute_items: list[tuple[str, object]],
    canonicalized: list[dict[str, object]],
) -> list[tuple[str, object]]:
    """Line-feature-only fix for a real extractor collision: Width and
    Thickness are both valid registry attributes for line features, and
    'narrow' is a valid value for both -- so the extractor may emit a
    line's thinness as either, but zero line rules key on Thickness (all 5
    that care -- L_001, HL_013/014/018/020 -- key on Width). Canonicalizing
    Thickness -> Width here, BEFORE the per-attribute validation loop, lets
    that signal reach the rules instead of silently missing every rule by
    one attribute name.

    Width-wins collision handling:
      - both 'Width' and 'Thickness' present: the original 'Width' entry is
        kept untouched; 'Thickness' is dropped entirely (does not reach
        observation or magnitudes).
      - only 'Thickness' present: its key is renamed to 'Width' (value and
        confidence carried over unchanged) so both observation and
        magnitudes record it under 'Width'.
      - non-line features never reach this function (see caller) --
        Thickness stays a real, distinct attribute for Palm/Thumb/Fingers/
        Nails.

    Renaming never turns a valid triple invalid: Width and Thickness share
    the same flat _ALL_VALUES pool (module docstring point 3), so
    (feature, 'Width', v) is valid whenever (feature, 'Thickness', v) was
    -- the rename only changes which attribute name a value is validated
    under, never the value pool itself. (A renamed entry can still end up
    invalid/dropped by the normal _is_valid_triple check below if 'Width'
    itself isn't a registry-valid attribute for this particular line
    feature -- that's the normal validation path doing its job, not a
    canonicalization bug.)

    Every canonicalization action is recorded into `canonicalized` (the
    caller's magnitudes["_canonicalized"] list) so this stays visible in
    the dogfood observation_record, separate from the invalid-triple
    `dropped` channel.
    """
    attribute_names = [name for name, _ in attribute_items]
    has_width = "Width" in attribute_names
    has_thickness = "Thickness" in attribute_names
    if not has_thickness:
        return attribute_items

    result: list[tuple[str, object]] = []
    for attribute, entry in attribute_items:
        if attribute != "Thickness":
            result.append((attribute, entry))
            continue

        value = entry.get("value") if isinstance(entry, dict) else entry
        confidence = entry.get("confidence", 1.0) if isinstance(entry, dict) else 1.0

        if has_width:
            canonicalized.append(
                {
                    "feature": feature,
                    "from": "Thickness",
                    "to": "Width",
                    "action": "dropped_dup",
                    "value": value,
                    "confidence": confidence,
                }
            )
            # Dropped entirely -- deliberately NOT appended to result, so
            # it never reaches observation or magnitudes.
        else:
            canonicalized.append(
                {
                    "feature": feature,
                    "from": "Thickness",
                    "to": "Width",
                    "action": "renamed",
                    "value": value,
                    "confidence": confidence,
                }
            )
            result.append(("Width", entry))

    return result


def to_tokens(vision_payload: dict) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, float] | list]]:
    """See module docstring for the full contract and vision_payload shape.

    Raises:
        ValueError: the payload is malformed -- the error message names the
        specific feature/attribute key that broke, per this task's own
        try/except requirement. A genuinely bad registry file (missing/
        malformed on disk) is NOT caught here -- that's a module-load-time
        failure, same posture as palm_rules_table.load_rules().
    """
    if not isinstance(vision_payload, dict):
        raise ValueError(
            f"observation_to_tokens.to_tokens: vision_payload must be a dict, "
            f"got {type(vision_payload).__name__}"
        )

    observation: dict[str, dict[str, str]] = {}
    magnitudes: dict[str, dict[str, float] | list] = {}
    dropped: list[dict[str, object]] = []
    canonicalized: list[dict[str, object]] = []

    for feature, attributes in vision_payload.items():
        try:
            attribute_items = list(attributes.items())
        except AttributeError as exc:
            raise ValueError(
                f"observation_to_tokens.to_tokens: feature key {feature!r} must map to a "
                f"dict of attributes, got {type(attributes).__name__}"
            ) from exc

        if feature in _LINE_FEATURES:
            attribute_items = _canonicalize_thickness_to_width(feature, attribute_items, canonicalized)

        for attribute, entry in attribute_items:
            try:
                value = entry["value"]
            except (TypeError, KeyError) as exc:
                raise ValueError(
                    f"observation_to_tokens.to_tokens: entry for feature={feature!r}, "
                    f"attribute={attribute!r} is malformed -- expected a dict with a "
                    f"'value' key, got {entry!r}"
                ) from exc
            confidence = entry.get("confidence", 1.0)

            # Design decision: magnitudes are an UNFILTERED passthrough --
            # they're plain confidence floats, not closed-vocabulary
            # tokens, and comparative antecedents (palm_rules_table.py's
            # condition_type == "comparative") read magnitudes for a
            # feature/attribute pair independently of whether any "value"
            # token was ever produced for it. Gating magnitudes by
            # observation validity would silently starve comparative
            # rules of a signal the registry was never meant to police.
            magnitudes.setdefault(feature, {})[attribute] = float(confidence)

            if _is_valid_triple(feature, attribute, value):
                observation.setdefault(feature, {})[attribute] = value
            else:
                dropped.append({"feature": feature, "attribute": attribute, "value": value})

    magnitudes["_dropped"] = dropped
    magnitudes["_canonicalized"] = canonicalized
    return observation, magnitudes
