"""
agent/interpretive/observation_extractor.py
Converts the live pipeline's per-feature PROSE (`palm_reading._gather_
feature_texts`'s `{feature: [raw_text, ...]}` shape -- 10 prose labels,
`palm_reading._FEATURE_REGISTRY`) into the structured `vision_payload` dict
`observation_to_tokens.to_tokens()` consumes:
    {feature: {attribute: {"value": <token>, "confidence": <float>}}}

Standalone, dependency-free module (stdlib + a lazily-imported `openai`
client only) -- does NOT import palm_reading.py, palm_rules_table.py, or
any engine file; not wired into any of them by this task.

CONTRACT:
    extract_observation(feature_texts, *, model="gpt-4o-mini") -> dict
    (see the DEVIATION note below for the one addition to this literal
    signature: an optional `client=` keyword.)

=== Discrepancies / deliberate deviations from this task's own prompt ===
(flagged per project convention -- verify prompts against code, don't
silently paper over a mismatch)

1. DEVIATION -- added `client=None` keyword-only parameter, not in the
   task's literal contract. Reason: this codebase's own established
   pattern (`claim_extraction.extract_claims`'s `client` seam) is what
   makes an LLM-calling function testable without a live API key, via a
   LAZY `from openai import OpenAI` import inside the function body --
   `palm_reading.py`'s own S65 flag (b) explicitly documents that a
   MODULE-LEVEL `OpenAI` import defeats conftest-style stubbing and is a
   known anti-pattern to avoid on next touch. Omitting a client seam here
   would either reintroduce that exact anti-pattern or make this module
   untestable without a live API call, contradicting this task's own
   "MOCK the LLM (no live API)" test requirement. Backward compatible:
   any caller using only `feature_texts`/`model` sees the exact contracted
   behavior.

2. The task's own HARDEST CASE example ("head line 'faintly wavy' when no
   such value exists") does NOT hold against the real registry --
   "wavy" IS a real, valid value token in ontology_registry.json (under
   direction_values/shape_values). Verified directly (`'wavy' in
   {v for vs in registry['values'].values() for v in vs}` -> True). The
   test built for this case (test_observation_extractor.py) uses a
   genuinely absent token ("shimmery", confirmed absent from the full
   214-value flattened set) instead, to actually exercise the no-valid-
   token path the task intends.

3. Closed-vocabulary construction reuses `observation_to_tokens.py`'s own
   already-documented interpretation of this registry (that module's
   docstring point 3), rather than inventing an independent one: the
   registry provides NO authoritative attribute -> value-category binding
   (category names like "depth_values"/"shape_values" don't map 1:1 onto
   attribute names like "Depth"/"Breadth", and real verified rules --
   e.g. HL_006's Quadrangle/Breadth="narrow" -- need cross-category value
   use to validate at all). This module therefore treats the FLATTENED
   UNION of every values-category list as the valid value pool for ANY
   attribute valid for a given feature (per attribute_feature_mapping) --
   the SAME interpretation `to_tokens()` already applies. Deliberate, not
   an oversight: whatever this module treats as "valid" should match what
   the actual downstream gate (`to_tokens()`) will accept, or the two
   layers silently disagree about what "closed vocabulary" means. ONE
   CONSEQUENCE worth a reviewer's attention (not fixed here, flagged):
   since the value pool is attribute-independent under this
   interpretation, a token from an entirely unrelated category (e.g. a
   nail value) is technically "valid" for an unrelated attribute like a
   line's Depth -- a real precision cost of the registry's own
   structure, inherited unchanged from `to_tokens()`, not introduced here.

4. Confidence is computed ENTIRELY in Python from source-prose hedge-word
   detection (`_confidence_for_text`), never read from whatever the LLM
   itself may return in a "confidence" field -- the system prompt
   explicitly tells the model to omit it. This is a deliberate reading of
   requirement 4's "parse from prose hedging" + "passthrough only" +
   CLAUDE.md's NO ANCHORED JUDGMENT working-style rule (#9): the LLM's job
   is the independent token-extraction observation; confidence is a
   SEPARATE deterministic Python judgment over the same source text, not
   a self-report bundled into the same call. Coarseness accepted: hedging
   is detected per-FEATURE (scanning that feature's whole joined prose),
   not per-attribute-clause -- there is no finer-grained source signal
   available without a sentence-splitting step this task does not ask for.
   `_HEDGE_CONFIDENCE=0.6` is an UNMEASURED placeholder default (THRESHOLD
   DISCIPLINE, CLAUDE.md Working Style #4): no probe/dogfood evidence sets
   this number. Scope guard: this module's confidence assignment only.
   Tuning note: revisit once real extraction output exists to calibrate
   against.

5. Malformed INDIVIDUAL entries inside an otherwise-valid `"observations"`
   object (an attribute entry that isn't a dict, or is missing "value")
   are DROPPED and logged, not raised -- unlike a JSON-decode failure or a
   missing/malformed top-level "observations" key, which DO raise
   ValueError (requirement 5's "no silent empty-on-error" is read as
   scoped to those two failure classes: the response could not be parsed
   at all, or its top-level shape is unusable). There is no retry loop in
   this module (none was requested) to recover from a whole-response
   failure, so treating one malformed attribute-entry as fatal for the
   entire batch would only lose otherwise-good extractions for no
   recovery benefit -- flagged here for reviewer visibility, not silently
   decided.
"""

from __future__ import annotations

import json
import logging
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
# docstring point 3 for why this is a flat, attribute-independent pool
# rather than a per-attribute split.
_ALL_VALUES: tuple[str, ...] = tuple(sorted(
    {value for value_list in _REGISTRY["values"].values() for value in value_list}
))
_ALL_VALUES_SET: frozenset[str] = frozenset(_ALL_VALUES)

_ALL_ONTOLOGY_FEATURES: frozenset[str] = frozenset(
    f for category in _REGISTRY["features"].values() for f in category
)


def _build_closed_vocab() -> dict[str, dict[str, tuple[str, ...]]]:
    """Per ontology feature -> {attribute: (value, ...)}, built once at
    module load. Every attribute's value tuple is the SAME `_ALL_VALUES`
    (see module docstring point 3) -- the dict shape is kept literal (per
    this task's own requirement 1 wording) rather than collapsed to a
    flat set, since it is what both the Python-side fail-closed guard and
    the per-feature prompt block key off of."""
    vocab: dict[str, dict[str, tuple[str, ...]]] = {}
    for feature in _ALL_ONTOLOGY_FEATURES:
        attrs = {
            attribute: _ALL_VALUES
            for attribute, features in _ATTRIBUTE_FEATURE_MAP.items()
            if feature in features
        }
        if attrs:
            vocab[feature] = attrs
    return vocab


_CLOSED_VOCAB: dict[str, dict[str, tuple[str, ...]]] = _build_closed_vocab()

# The 10 palm_reading._FEATURE_REGISTRY prose labels -> canonical
# ontology_registry.json feature token. Hardcoded per this task's own
# requirement 2 (not derived from the registry's `synonyms` block, which
# covers a different vocabulary -- alternate NAMES for the same canonical
# feature, not this module's prose-label-to-canonical-feature mapping).
# Two of the ten have NO ontology counterpart and map to None -- SKIPPED
# (logged, never raised), confirmed against the real registry:
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

# ─── Confidence -- prose hedge-word detection (module docstring point 4) ──

_HEDGE_WORDS: tuple[str, ...] = (
    "slightly", "somewhat", "possibly", "perhaps", "faintly", "rather",
    "seemingly", "may be", "might be", "appears to be", "a bit", "barely",
)
_HEDGE_CONFIDENCE = 0.6  # UNMEASURED placeholder -- see docstring point 4.
_DEFAULT_CONFIDENCE = 1.0


def _confidence_for_text(text: str) -> float:
    lowered = text.lower()
    if any(hedge in lowered for hedge in _HEDGE_WORDS):
        return _HEDGE_CONFIDENCE
    return _DEFAULT_CONFIDENCE


# ─── LLM system prompt -- global value vocabulary embedded once ──────────

_GLOBAL_VALUE_TOKENS_BLOCK = ", ".join(_ALL_VALUES)

_EXTRACTION_SYSTEM_PROMPT = f"""You are a structured-observation extraction engine for a palmistry vision pipeline. You are given one or more observed hand features, each with its raw descriptive prose (a vision model's free-text description of a photographed hand) and, for that exact feature, a list of the ONLY attribute names you may report on.

GLOBAL ALLOWED VALUE VOCABULARY (the ONLY value tokens you may ever emit, for ANY attribute, ANY feature):
{_GLOBAL_VALUE_TOKENS_BLOCK}

Your ONLY job: for each given feature, read its prose and decide which (attribute, value) pairs it actually states or clearly implies, using ONLY attributes from that feature's own "VALID ATTRIBUTES" list and ONLY values from the GLOBAL ALLOWED VALUE VOCABULARY above.

STRICT RULES:
1. Closed vocabulary only: a value token must appear VERBATIM in the GLOBAL ALLOWED VALUE VOCABULARY. If the prose describes a quality that does not match any listed value, EMIT NOTHING for it -- do not choose the nearest token, do not guess, do not invent a token that is not listed.
2. An attribute must come from the specific feature's own "VALID ATTRIBUTES" list -- never borrow an attribute listed only for a different feature.
3. If a feature's prose states no matching quality at all, omit that feature entirely from your response (or emit an empty object for it). Do not fabricate an observation to fill a gap.
4. Do not include a "confidence" field -- it is computed separately, outside this call.
5. Return ONLY a single JSON object, no prose or markdown outside it, matching exactly:
{{"observations": {{"<feature>": {{"<attribute>": {{"value": "<token>"}}}}}}}}
Empty is a valid response: {{"observations": {{}}}}."""


def _build_user_prompt(entries: list[tuple[str, str, str]]) -> str:
    """entries: list of (prose_feature_label, ontology_feature, joined_text)
    -- prose_feature_label is included only for readability, never parsed
    back out of the model's response."""
    blocks = []
    for _prose_feature, ontology_feature, text in entries:
        valid_attributes = sorted(_CLOSED_VOCAB.get(ontology_feature, {}))
        blocks.append(
            f"FEATURE: {ontology_feature}\n"
            f"PROSE: {text}\n"
            f"VALID ATTRIBUTES FOR THIS FEATURE: {', '.join(valid_attributes)}"
        )
    return "\n\n".join(blocks) + "\n\nExtract observations per your instructions."


def _call_llm(client, model: str, messages: list[dict], ontology_features: list[str]) -> str:
    """Single try/except boundary around the one API call this module ever
    makes. A failure here is re-raised as a RuntimeError naming the whole
    feature batch this call was for (per this task's requirement 5) --
    never swallowed into a silent empty result."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
            response_format={"type": "json_object"},
        )
    except Exception as exc:  # noqa: BLE001 -- re-raised immediately, named, not swallowed
        raise RuntimeError(
            "observation_extractor.extract_observation: LLM call failed for feature "
            f"batch {sorted(ontology_features)}: {exc}"
        ) from exc
    return response.choices[0].message.content


def _parse_response(raw: str) -> dict:
    """Raises ValueError, with a raw-response snippet, on EITHER a
    JSON-decode failure or a well-formed-JSON-but-wrong-shape response
    (missing/non-dict top-level "observations" key) -- see module
    docstring point 5 for why this boundary, specifically, always raises
    rather than degrading to an empty result."""
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
    return observations


def extract_observation(
    feature_texts: dict[str, list[str]],
    *,
    model: str = "gpt-4o-mini",
    client=None,
) -> dict:
    """Converts palm_reading._gather_feature_texts's `{prose_feature:
    [raw_text, ...]}` output into the `vision_payload` shape
    `observation_to_tokens.to_tokens()` consumes. See module docstring for
    the full contract, deviations, and design notes.

    One LLM call for the whole batch (all mapped, non-empty-text features
    together) -- never one call per feature. A `feature_texts` with no
    mappable, non-empty-text entries makes ZERO LLM calls and returns {}
    directly (empty payload is a valid, non-raising result).

    client: injection seam for tests (see module docstring, DEVIATION 1)
    -- if None, a real OpenAI() client is constructed lazily INSIDE this
    function, never at module import time.

    Raises:
        RuntimeError: the LLM call itself failed (network/API error).
        ValueError: the LLM's response could not be parsed as the
                     expected JSON shape (see _parse_response).
    """
    entries: list[tuple[str, str, str]] = []
    for prose_feature, texts in feature_texts.items():
        joined = " ".join(t.strip() for t in (texts or []) if t and t.strip())
        if not joined:
            continue
        ontology_feature = _FEATURE_ALIAS.get(prose_feature)
        if ontology_feature is None:
            logger.info(
                "observation_extractor.extract_observation: prose feature %r has no "
                "ontology counterpart -- skipped.", prose_feature,
            )
            continue
        entries.append((prose_feature, ontology_feature, joined))

    if not entries:
        return {}

    if client is None:
        from openai import OpenAI  # lazy import -- see module docstring DEVIATION 1
        client = OpenAI()

    ontology_features = [e[1] for e in entries]
    messages = [
        {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(entries)},
    ]
    raw = _call_llm(client, model, messages, ontology_features)
    observations_raw = _parse_response(raw)

    requested = frozenset(ontology_features)
    text_by_feature = {e[1]: e[2] for e in entries}

    vision_payload: dict[str, dict[str, dict[str, object]]] = {}
    for feature, attrs in observations_raw.items():
        if feature not in requested:
            logger.info(
                "observation_extractor.extract_observation: LLM emitted feature %r, not "
                "in this call's requested batch -- dropped.", feature,
            )
            continue
        if not isinstance(attrs, dict):
            logger.info(
                "observation_extractor.extract_observation: feature %r's entry is not an "
                "object (%r) -- dropped.", feature, type(attrs).__name__,
            )
            continue

        allowed_attributes = _CLOSED_VOCAB.get(feature, {})
        confidence = _confidence_for_text(text_by_feature.get(feature, ""))

        for attribute, entry in attrs.items():
            if not isinstance(entry, dict) or "value" not in entry:
                logger.info(
                    "observation_extractor.extract_observation: malformed entry for "
                    "feature=%r attribute=%r (%r) -- dropped.", feature, attribute, entry,
                )
                continue
            value = entry["value"]
            allowed_values = allowed_attributes.get(attribute)
            if allowed_values is None or not isinstance(value, str) or value not in allowed_values:
                logger.info(
                    "observation_extractor.extract_observation: dropped out-of-vocabulary "
                    "emission feature=%r attribute=%r value=%r.", feature, attribute, value,
                )
                continue
            vision_payload.setdefault(feature, {})[attribute] = {
                "value": value, "confidence": confidence,
            }

    return vision_payload
