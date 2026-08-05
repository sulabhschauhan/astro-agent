"""
agent/interpretive/phrase_normalizer.py
Domain-agnostic phrase -> token promotion layer, applied to an already-built
`ObservationRecord` (see agent/interpretive/observation_extractor.py) AFTER
extraction, BEFORE `to_vision_payload`. Promotes surface phrasings the
extractor correctly left in a feature's `unmapped` list -- because no closed-
vocabulary value matched -- into real tokens, using a human-verified lexicon
file (see data/palm_phrase_lexicon_v1.json for the schema this module reads).

Not wired into any pipeline by this task. No palmistry hardcoding: this
module knows nothing about "Line of Life", "Curve", or any other concrete
feature/attribute/token/phrase -- every matchable name and phrase comes from
the lexicon file the caller passes in. Does not import palm_reading.py.

CONTRACT:
    normalize(record: ObservationRecord, lexicon_path: str | Path) -> list[dict]

    Mutates `record` in place: for each lexicon entry whose phrase guard
    matches an `unmapped` quality on one of its `applies_to_features`, adds
    a token to that feature's `tokens[entry["attribute"]]` and removes the
    matched item from `unmapped`. Returns a promotions log -- list of
    {entry_id, feature, attribute, token, matched_quality} -- for the
    diagnostics/capture surface; the return value carries no state the
    caller needs to apply, `record` already reflects every promotion.

MATCH SEMANTICS (per data/palm_phrase_lexicon_v1.json's own
`meta.match_semantics`, replicated here rather than re-derived): a quality
promotes under a lexicon entry iff (a) the quality's feature is present in
`record.features` AND is one of the entry's `applies_to_features`, (b) any
of the entry's `match_any` phrases is a case-insensitive substring of the
quality string, and (c) none of the entry's `must_not_match` phrases is.
The guard is deliberately biased to OVER-BLOCK (leave a real match
unpromoted, stay in `unmapped`) over OVER-PROMOTE (invent a token) -- no
numeric threshold, no fuzzy match, no partial-word matching beyond plain
substring containment.

CONFIDENCE CONVENTION: replicated from observation_extractor.py, not
invented here. `extract_observation` computes one confidence value per
FEATURE (via `_confidence_for_text` over that feature's whole `raw_prose`,
hedge-word detection, module docstring point 6 there) and applies it
uniformly to every token in that feature -- this module reuses the exact
same function over the exact same `raw_prose` for a promoted token, so a
promoted token's confidence is indistinguishable in kind from an
LLM-extracted one for the same feature.

PROVENANCE: a promoted token carries an extra "source": "phrase_lexicon:
<entry_id>" key alongside "value"/"confidence" -- extraction-produced
tokens never carry this key, so a caller/reviewer can always tell a
phrase-promoted token apart from an LLM-extracted one by its presence.

FAIL-CLOSED: lexicon load + apply is wrapped in a single try/except.
A missing lexicon file, or a lexicon whose "entries" list is missing/empty/
not-a-list, is NOT an error -- it returns [] (no promotions, record
unchanged). A lexicon file that exists but fails to read or parse (corrupt
JSON, OS-level read error) raises RuntimeError, naming the path -- never
silently promotes on error, and never returns a partial promotion list from
a half-processed lexicon.

CONFLICT POLICY: if a feature's target attribute already has a token (from
extraction, or from an earlier-processed lexicon entry), a matching entry is
never applied -- the existing token is never overwritten, and the matched
`unmapped` item is left in place (not removed) so it stays visible for
diagnostics. This is logged, not raised: a conflict is an expected,
non-fatal outcome of running the same lexicon against varied prose.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from agent.interpretive.observation_extractor import _confidence_for_text

if TYPE_CHECKING:
    from agent.interpretive.observation_extractor import ObservationRecord

logger = logging.getLogger(__name__)


def _load_lexicon_entries(lexicon_path: str | Path) -> list[dict]:
    """Missing file or missing/malformed "entries" -> [] (no promotion, no
    crash). Corrupt/unreadable file -> RuntimeError (fail-closed, never
    silently promote on error)."""
    path = Path(lexicon_path)
    if not path.exists():
        logger.info(
            "phrase_normalizer.normalize: lexicon path %s does not exist -- no promotions.", path,
        )
        return []

    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"phrase_normalizer.normalize: failed to load/parse lexicon at {path}: {exc}"
        ) from exc

    entries = data.get("entries") if isinstance(data, dict) else None
    if not isinstance(entries, list) or not entries:
        logger.info(
            "phrase_normalizer.normalize: lexicon at %s has no usable 'entries' list -- "
            "no promotions.", path,
        )
        return []
    return entries


def _phrase_guard_matches(quality: str, entry: dict) -> bool:
    lowered = quality.lower()
    match_any = entry.get("match_any")
    must_not_match = entry.get("must_not_match")
    match_any = match_any if isinstance(match_any, list) else []
    must_not_match = must_not_match if isinstance(must_not_match, list) else []

    if not any(isinstance(p, str) and p.lower() in lowered for p in match_any):
        return False
    if any(isinstance(p, str) and p.lower() in lowered for p in must_not_match):
        return False
    return True


def _apply_lexicon(record: "ObservationRecord", entries: list[dict]) -> list[dict]:
    promotions: list[dict] = []

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        entry_id = entry.get("entry_id")
        attribute = entry.get("attribute")
        token = entry.get("token")
        applies_to_features = entry.get("applies_to_features")
        if not (
            isinstance(entry_id, str) and isinstance(attribute, str)
            and isinstance(token, str) and isinstance(applies_to_features, list)
        ):
            logger.info("phrase_normalizer.normalize: skipping malformed lexicon entry %r.", entry)
            continue

        for feature in applies_to_features:
            fobs = record.features.get(feature)
            if fobs is None:
                continue  # feature not present in this record -- nothing to promote

            matched_index = None
            matched_quality = None
            for i, quality_entry in enumerate(fobs.unmapped):
                quality = quality_entry.get("quality") if isinstance(quality_entry, dict) else None
                if isinstance(quality, str) and _phrase_guard_matches(quality, entry):
                    matched_index = i
                    matched_quality = quality
                    break
            if matched_index is None:
                continue

            if attribute in fobs.tokens:
                logger.info(
                    "phrase_normalizer.normalize: conflict -- feature=%r attribute=%r already "
                    "has a token, entry=%r not applied (no overwrite).",
                    feature, attribute, entry_id,
                )
                continue

            confidence = _confidence_for_text(fobs.raw_prose)
            fobs.tokens[attribute] = {
                "value": token,
                "confidence": confidence,
                "source": f"phrase_lexicon:{entry_id}",
            }
            del fobs.unmapped[matched_index]

            promotions.append({
                "entry_id": entry_id,
                "feature": feature,
                "attribute": attribute,
                "token": token,
                "matched_quality": matched_quality,
            })

    return promotions


def normalize(record: "ObservationRecord", lexicon_path: str | Path) -> list[dict]:
    """See module docstring for the full contract. Mutates `record` in
    place; returns the promotions log."""
    try:
        entries = _load_lexicon_entries(lexicon_path)
        if not entries:
            return []
        return _apply_lexicon(record, entries)
    except RuntimeError:
        raise
    except Exception as exc:  # noqa: BLE001 -- fail-closed, never silently promote on error
        raise RuntimeError(
            f"phrase_normalizer.normalize: unexpected error normalizing against lexicon "
            f"{lexicon_path}: {exc}"
        ) from exc
