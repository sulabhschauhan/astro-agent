"""
agent/interpretive/rule_to_claim.py
Bridges the deterministic rule engine (agent/interpretive/palm_rules_table.py
-- match() + resolve_priority()) to the existing Stage-2 voicer
(agent/interpretive/claim_voicing.py) by turning a SURFACED PalmRule list
into a tuple of claim_extraction.Claim objects the voicer already accepts,
UNCHANGED. Neither palm_reading.py, claim_voicing.py, claim_extraction.py,
nor palm_rules_table.py is edited by this module -- it only imports Claim
and calls voice_claims() as any other caller would.

STEP 0 DISCOVERY (repo wins, not guessed -- see this module's own report
in diagnostics/latest_run.md for the full writeup):

(a) Claim's exact fields (agent/interpretive/claim_extraction.py:310-319,
    a plain frozen dataclass, every field REQUIRED, no defaults):
        claim_id: str                  -- Stage 1's own "C<n>" shape
        feature: str
        chunk_id: str
        claim_text: str
        valence: str                   -- NOT Optional; always required
        condition_text: str | None
        observation_basis: str
        excluded_from_voice: bool
        exclusion_reason: str | None
    claim_voicing.py's own docstring (lines 9-12, 64-66) states explicitly
    it reads ONLY claim_id/claim_text/valence/observation_basis -- it
    "never reads Claim.chunk_id at all", and there is NO source_quote
    field anywhere on Claim. Both facts directly shape STEP 2 below.

(b) chunk_id FORMAT: confirmed by direct inspection of
    ingestion/embedder.py:141 (`ids=[c["chunk_id"] for c in batch]`),
    which is what actually populates ChromaDB's own ids from
    data/chunked_chunks.json's "chunk_id" field at ingest time -- e.g.
    "cheiroslanguageo00chei_1_p160_c0". data/chunked_chunks.json is
    therefore the authoritative chunk source this module resolves
    against, matching the format claim_extraction.py's E-1 validator
    already checks candidate chunk_ids against (gated_results keys, which
    originate from the SAME file via palm_reading.py's retrieval).

IMPORTANT DESIGN CONSEQUENCE OF (a): `observation_basis` is placed
DIRECTLY into the voicer's LLM-facing prompt
(claim_voicing._build_user_prompt: `observation: "{c.observation_basis}"`).
Putting the rule's raw `source_quote` (19th-century book prose) there
would leak book text into a prompt whose own architectural invariant is
"chunk text/chunk_id never appears anywhere in the prompt by
construction" (claim_voicing.py docstring, line 65-66) -- silently
violating a deliberate design guarantee of the module this bridges to.
So `source_quote` is carried in a SEPARATE side-channel return value
(the `citations` dict below), never inside the Claim object itself, and
`observation_basis` instead gets a plain rendering of the rule's own
antecedents (the actual observed condition, safe LLM-facing content).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

from agent.interpretive.palm_rules_table import load_rule_set

if TYPE_CHECKING:
    from agent.interpretive.claim_extraction import Claim
    from agent.interpretive.palm_rules_table import PalmRule

logger = logging.getLogger(__name__)

_CHUNKS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "chunked_chunks.json"
_BOOK_NAME = "cheiroslanguageo00chei_1"

# ─── topic_group -> palm_reading._FEATURE_REGISTRY token ──────────────────
#
# BUG THIS FIXES (see diagnostics/latest_run.md for the full writeup):
# claims_from_rules previously set Claim.feature directly to the rule's
# topic_group ("line_head", "line_life", "line_heart", ...) -- a rule-book
# grouping label, NOT one of palm_reading._FEATURE_REGISTRY's tokens
# ("head line", "life line", "heart line", ...). Every downstream consumer
# that keys on the registry token (_compute_decline_features,
# _build_sources_from_claims, _check_banned_feature_mentions, all in
# palm_reading.py) silently mismatched: gate-supported features got
# declined anyway (zero claims ever matched their registry key) and
# `sources` came back empty even when rules fired and cited real chunks.
# palm_reading.py's own `_prepare_claims_from_rules` docstring flagged this
# exact defect and named this module as the fix site (S69/S70-era
# comment, unedited by this fix per this task's scope: palm_reading.py is
# not touched here).
#
# Every topic_group actually present in data/palm_rules/*.json's
# `validated_candidates` must have an entry here -- enforced fail-closed
# below at module load, not just documented, so a new rule-book chapter
# with a new topic_group can never silently mis-route through this
# mapping's default-less dict lookup.
_TOPIC_GROUP_TO_FEATURE: dict[str, str] = {
    "line_life": "life line",
    "line_head": "head line",
    "line_head_types": "head line",
    "line_head_murder": "head line",
    "line_heart": "heart line",
}


def _assert_topic_groups_mapped(rules: Sequence["PalmRule"]) -> None:
    """Fail-closed guard: every distinct topic_group among `rules` must
    already have a _TOPIC_GROUP_TO_FEATURE entry. Raises ValueError naming
    every unmapped group (not just the first) so a multi-chapter rule-book
    addition surfaces its full mapping gap in one pass. Called at module
    load against the real data/palm_rules/*.json rule set below, and
    directly callable by tests against a synthetic rule set."""
    unmapped = sorted({r.topic_group for r in rules} - _TOPIC_GROUP_TO_FEATURE.keys())
    if unmapped:
        raise ValueError(
            f"rule_to_claim: topic_group(s) {unmapped!r} have no "
            f"_TOPIC_GROUP_TO_FEATURE entry -- add each to that mapping "
            f"before claims_from_rules can route their rules to a "
            f"palm_reading._FEATURE_REGISTRY token."
        )


_assert_topic_groups_mapped(load_rule_set())


def _feature_for_topic_group(topic_group: str) -> str:
    """Single lookup site claims_from_rules calls -- same fail-closed
    ValueError shape as _assert_topic_groups_mapped's module-load guard,
    so a rule reaching this function with an unmapped topic_group (e.g. a
    synthetic rule built directly for a test, bypassing the module-load
    scan above) still fails loud instead of raising a bare KeyError."""
    try:
        return _TOPIC_GROUP_TO_FEATURE[topic_group]
    except KeyError:
        raise ValueError(
            f"rule_to_claim: topic_group {topic_group!r} has no "
            f"_TOPIC_GROUP_TO_FEATURE entry -- add it to that mapping "
            f"before this rule can be routed to a "
            f"palm_reading._FEATURE_REGISTRY token."
        ) from None


# ASSUMPTION (flagged per this task's own instruction, not hardcoded
# silently): valence is a REQUIRED field on Claim (not Optional -- see
# discovery note above), so it cannot be left unset. The rule-book model
# has no neutral/disjunctive valence concept at all (a fired rule asserts
# its claim, full stop; contrast claim_extraction.py's own
# "supports"/"corrective"/"conditional" set, which exists because Stage 1
# extracts from ambiguous, possibly-hedged chunk text) -- so every
# rule-derived Claim gets valence="supports" uniformly. Revisit if a
# future rule-book schema ever introduces a corrective/contradicts rule
# (data/palm_rules_head_heart_v1.json's own schema doesn't have one in
# the 43 validated_candidates as of this session).
_RULE_DERIVED_VALENCE = "supports"


def resolve_chunk_id(source_page: int, chunks_path: Path | str = _CHUNKS_PATH) -> str | None:
    """Returns the chunk_id of the first (lowest chunk-index, by sorted
    chunk_id) NON-EMPTY-text chunk on `source_page` for the Cheiro book,
    or None if no such chunk exists -- fail-closed, never fabricates an
    id. A page that exists only as a diagram (page_type="diagram", empty
    text, e.g. the Plate illustration pages already documented elsewhere
    in this project) has nothing citable, so it resolves to None exactly
    like a genuinely missing page."""
    try:
        chunks = json.loads(Path(chunks_path).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 -- a bad corpus file must not crash the caller
        logger.warning("rule_to_claim.resolve_chunk_id: failed to load %s: %s", chunks_path, exc)
        return None

    candidates = sorted(
        (c for c in chunks if c.get("book_name") == _BOOK_NAME and c.get("page_ref") == source_page),
        key=lambda c: c["chunk_id"],
    )
    for c in candidates:
        if (c.get("text") or "").strip():
            return c["chunk_id"]
    return None


def _render_observation_basis(rule: "PalmRule") -> str:
    """Plain rendering of the rule's OWN antecedents -- the observed
    condition the claim applies to -- safe to place in the voicer's
    LLM-facing prompt (see module docstring's design-consequence note).
    Comparative antecedents (value=None) render their comparator instead."""
    parts = []
    for a in rule.antecedents:
        if a.condition_type == "comparative":
            parts.append(f"{a.feature} {a.attribute} {a.comparator} {a.comparator_feature} {a.attribute}")
        else:
            parts.append(f"{a.feature} {a.attribute}={a.value}")
    return "; ".join(parts)


def claims_from_rules(
    surfaced_rules: Sequence["PalmRule"],
    chunks_path: Path | str = _CHUNKS_PATH,
) -> tuple[tuple["Claim", ...], dict]:
    """One Claim per surfaced rule whose source_page resolves to a real
    chunk_id, numbered C1, C2, ... in surfaced order -- a dropped rule
    (unresolvable page) does NOT consume a claim_id number, so the
    output stays contiguous (no C1, C3 gap). Fail-closed: dropped rules
    are logged, never raise.

    Returns (claims, diagnostics). diagnostics["citations"] maps
    claim_id -> {"rule_id", "chunk_id", "source_page", "source_quote",
    "topic_group"} -- this is where source_quote is actually carried (see
    module docstring: Claim itself has no field for it, and stuffing it
    into observation_basis would leak book text into the voicer's
    prompt); "topic_group" is the rule's own grouping label, kept here for
    the suppression audit even though Claim.feature is now the mapped
    _FEATURE_REGISTRY token, not this raw label (see
    _TOPIC_GROUP_TO_FEATURE).
    diagnostics["dropped_rule_ids"] lists any rule skipped for an
    unresolvable page.
    """
    from agent.interpretive.claim_extraction import Claim  # local import -- avoid import-time coupling

    claims: list[Claim] = []
    citations: dict[str, dict] = {}
    dropped: list[str] = []
    counter = 1

    for rule in surfaced_rules:
        chunk_id = resolve_chunk_id(rule.source_page, chunks_path)
        if chunk_id is None:
            dropped.append(rule.rule_id)
            logger.warning(
                "rule_to_claim.claims_from_rules: rule %r (source_page=%r) has no "
                "resolvable chunk -- dropped, not raised.",
                rule.rule_id, rule.source_page,
            )
            continue

        claim_id = f"C{counter}"
        counter += 1
        claims.append(Claim(
            claim_id=claim_id,
            feature=_feature_for_topic_group(rule.topic_group),
            chunk_id=chunk_id,
            claim_text=rule.claim,
            valence=_RULE_DERIVED_VALENCE,
            condition_text=None,
            observation_basis=_render_observation_basis(rule),
            excluded_from_voice=False,
            exclusion_reason=None,
        ))
        citations[claim_id] = {
            "rule_id": rule.rule_id,
            "chunk_id": chunk_id,
            "source_page": rule.source_page,
            "source_quote": rule.source_quote,
            # Kept for the suppression audit even though Claim.feature is
            # now the mapped registry token, not this -- see
            # _TOPIC_GROUP_TO_FEATURE above for the mapping this discards
            # from Claim.feature itself.
            "topic_group": rule.topic_group,
        }

    diagnostics = {"citations": citations, "dropped_rule_ids": dropped}
    return tuple(claims), diagnostics
