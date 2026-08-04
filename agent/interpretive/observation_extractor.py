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

5. Closed-vocabulary construction (`_CLOSED_VOCAB`) reuses
   `observation_to_tokens.py`'s own already-documented interpretation of
   `ontology_registry.json` (that module's docstring point 3): the flat
   union of every values-category list is treated as the valid value
   pool for ANY attribute valid for a feature, since the registry
   provides no authoritative narrower attribute -> value-category
   binding and real verified rules need cross-category value use to
   validate at all. Unchanged from the prior version of this module.

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


def _build_closed_vocab() -> dict[str, dict[str, tuple[str, ...]]]:
    """Per ontology feature -> {attribute: (value, ...)}, built once at
    module load. Every attribute's value tuple is the SAME `_ALL_VALUES`
    (see module docstring point 5) -- the dict shape is kept literal
    rather than collapsed to a flat set, since it is what both the
    Python-side fail-closed guard and the per-feature prompt block key
    off of."""
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
    """
    features: dict[str, FeatureObservation] = field(default_factory=dict)
    dropped_disabled: list[str] = field(default_factory=list)
    unmappable_prose_features: list[dict[str, str]] = field(default_factory=list)


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
        blocks.append(
            f"FEATURE: {ontology_feature}\n"
            f"PROSE: {text}\n"
            f"VALID ATTRIBUTES FOR THIS FEATURE: {', '.join(valid_attributes)}"
        )
    return "\n\n".join(blocks) + "\n\nExtract observations per your instructions."


def _call_llm(client, model: str, messages: list[dict], ontology_features: list[str]) -> str:
    """Single try/except boundary around the one API call this module ever
    makes. A failure here is re-raised as a RuntimeError naming the whole
    feature batch this call was for -- never swallowed into a silent
    empty result."""
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
        client = OpenAI()

    ontology_features = [e[1] for e in entries]
    text_by_feature = {e[1]: e[2] for e in entries}
    messages = [
        {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(entries)},
    ]
    raw = _call_llm(client, model, messages, ontology_features)
    observations_raw, unmapped_raw = _parse_response(raw)

    requested = frozenset(ontology_features)

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

    if enabled_features is None:
        dropped_disabled: list[str] = []
    else:
        dropped_disabled = sorted({f for f in ontology_features if f not in enabled_features})

    return ObservationRecord(
        features=features,
        dropped_disabled=dropped_disabled,
        unmappable_prose_features=unmappable_prose_features,
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
