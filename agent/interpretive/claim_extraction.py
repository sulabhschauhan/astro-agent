"""
agent/interpretive/claim_extraction.py
S69 F-H Stage 1 -- per-feature claim extraction directly from gated chunks.

CITATION: CLAUDE.md S69 queue's F-H entry (two-stage extract-then-voice
redesign, PRIMARY fix-forward for Ring 3 pass 4's architectural grounding
ruling -- single-call generation composes from the model's pretraining
prior first, retrieved doctrine second, making citations decorative).
`diagnostics/fh_stage1_probe_S69.md` is the pre-implementation probe this
module now productionizes: 12-cell matrix (3 frozen pass-4 runs x 2 models
x 2 temperatures) measured against the SAME frozen inputs pass 4 already
scored. Result LOCKED from that probe: model=gpt-4o-mini, temperature=0
(SC-1/2/3/5 PASS in all 12 cells at every model/temp combination tried,
so the cheaper/faster model was not a quality tradeoff here). The probe's
SC-4 finding -- 12/12 cells FAILED to extract a fate-line claim
referencing the rises-from-life-line precondition, because "barely
visible" never confirms where the line rises from -- is NOT treated as a
defect to force past: this module's extractor may legitimately decline a
conditional claim upstream (empty claims list, or E-4 marking a claim
excluded_from_voice), and E-4 below is this module's own deterministic,
Python-owned analog of that same conservatism, not a workaround for it.
ACCEPTED DEVIATION, 3-place registration (CLAUDE.md's own convention):
this module docstring + the E-4 code comment are places 2 and 3; place 1
(the CLAUDE.md Known-Source-Divergences entry itself) is NOT added here --
that is the F-H close-out prompt's job, flagged in this prompt's own
report to diagnostics/latest_run.md, not done silently in this file.

RETIRES accepted gaps (a) (V-2 anchor legality was union-only across all
gated features) and (f) (a chunk gated under two features could get
credit for either) from `palm_reading.py`'s own accepted-gap register --
E-1 below checks legality per-feature, against ONLY the chunk_id set this
module itself offered that feature's extraction call, never a
whole-reading union. This is the module-contract-level fix those two gaps
were deferred pending; the close-out prompt still owns updating
palm_reading.py's own docstring/CLAUDE.md text once wiring lands.

SCOPE: this module knows nothing about palm_reading.py's retrieval,
support-gate, or Ring 1/voice-generation machinery -- it is a pure
extraction stage, callable independently, wired in a LATER prompt. It
does not import palm_reading (avoids a circular import once that wiring
lands: palm_reading.py will need to import THIS module, so the reverse
import must never exist) and does not import agent.infra.calc_router,
agent.infra.orchestrator, or agent.infra.chart_profile, matching the
project's existing upload-triggered-artifact scope lock.
"""

from __future__ import annotations

import itertools
import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openai import OpenAI

# ─── LLM call configuration ─────────────────────────────────────────────

# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
# Justification: fh_stage1_probe_S69.md's locked result -- gpt-4o-mini at
# temperature=0 passed SC-1/2/3/5 in every one of the probe's 12 cells,
# identically to gpt-4o's results at the same criteria; no quality
# tradeoff was observed for the cheaper/faster model on this extraction
# task. Scope guard: this module's extraction call site only. Revisit
# trigger: pass-5 evidence that gpt-4o-mini underperforms gpt-4o on a
# metric the probe didn't measure.
_EXTRACTION_MODEL = "gpt-4o-mini"
_EXTRACTION_TEMPERATURE = 0

# Same value as palm_reading._READING_TIMEOUT_SECONDS -- duplicated, NOT
# imported, to avoid a circular import (palm_reading.py will import THIS
# module once wired; this module must never import palm_reading back).
# Re-sync by hand if palm_reading.py's own timeout is ever revisited.
_EXTRACTION_TIMEOUT_SECONDS = 30.0

# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
# Justification: fh_stage1_probe_S69.md's pooled overlap distribution
# across all 12 cells / 73 extracted claims -- min=0.50, p25=median=p75=
# max=1.00: the overwhelming majority of genuine extractions restate
# their cited chunk almost word-for-word, with the single pooled minimum
# observed at 0.50. UNLIKE the 0.30 support-score floor in palm_reading.py
# (which sits between a measured negative-control ceiling of 0.2192 and a
# measured minimum genuine score of 0.3954), this probe never measured a
# genuinely-fabricated claim's overlap score -- there is no noise ceiling
# to sit above here, only a pooled minimum-observed-GENUINE value to sit
# below. 0.40 sits with a conservative 0.10 margin below that pooled
# minimum -- narrower certainty than the support-gate precedent, and
# explicitly flagged as such, not silently presented as equally proven.
# Scope guard: applies ONLY to a claim_text vs. its own cited chunk's
# text, never cross-chunk. Revisit trigger: pass-5 evidence, or a future
# probe that actually measures fabricated-claim overlap (would let this
# floor graduate to the same two-sided justification the 0.30 floor has).
_PARAPHRASE_OVERLAP_FLOOR = 0.40

_VALID_VALENCE = frozenset({"supports", "corrective", "conditional"})


# ─── Content-word overlap -- transplanted verbatim from ──────────────────
# scripts/probe_fh_stage1_extraction.py's _STOPWORDS / _WORD_PATTERN /
# _content_words / _overlap_ratio (the same probe that measured the
# pooled distribution _PARAPHRASE_OVERLAP_FLOOR is set from) -- same
# method, not re-derived, so the floor and the measurement it was set
# from stay comparable.
_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "of", "in", "on", "at", "to", "for",
    "with", "by", "is", "are", "was", "were", "be", "been", "being", "this",
    "that", "these", "those", "it", "its", "as", "from", "into", "which",
    "who", "whom", "your", "you", "their", "his", "her", "he", "she", "they",
    "not", "no", "than", "then", "so", "such", "if", "when", "while",
    "suggests", "suggest", "indicates", "indicate", "may", "might", "also",
})
_WORD_PATTERN = re.compile(r"[a-z]+")


def _content_words(text: str) -> set[str]:
    return {w for w in _WORD_PATTERN.findall(text.lower()) if w not in _STOPWORDS}


def _overlap_ratio(a: str, b: str) -> float:
    wa, wb = _content_words(a), _content_words(b)
    if not wa or not wb:
        return 0.0
    shared = len(wa & wb)
    return shared / min(len(wa), len(wb))


# ─── Extraction system prompt -- transplanted verbatim from ──────────────
# scripts/probe_fh_stage1_extraction.py's _EXTRACTION_SYSTEM_PROMPT. This
# EXACT text is what fh_stage1_probe_S69.md validated (SC-1/2/3/5 PASS in
# all 12 cells) -- redrafting it here, even lightly, would mean shipping
# an untested prompt under a tested one's name. Do not edit without a new
# probe run.
_EXTRACTION_SYSTEM_PROMPT = """You are a claim-extraction engine for a palmistry RAG pipeline. You are given ONE observed hand feature, its confirmed physical observation(s) from a photographed hand, and a small set of retrieved reference passages ("chunks"), each labeled with a chunk_id.

Your ONLY job: for each provided chunk, decide whether it states doctrine (a meaning or interpretation) that applies to this feature, and if so extract it as a claim.

STRICT RULES:
1. Paraphrase-or-nothing: every claim must restate doctrine LITERALLY PRESENT in exactly ONE of the provided chunks. Never invent doctrine, even if you recall real palmistry teaching from training -- if no provided chunk states it, it does not go in a claim.
2. If a chunk's stated doctrine actually REJECTS or CONTRADICTS the natural inference the confirmed observation would suggest, extract it anyway, with valence="corrective".
3. If a chunk's doctrine only holds under a precondition (e.g. "if the line rises from X..."), use valence="conditional" and populate condition_text with that precondition (verbatim or lightly paraphrased). condition_text must be null for any other valence.
4. Otherwise, if a chunk directly and positively supports the observation, use valence="supports".
5. Never merge two chunks into one claim -- one claim cites exactly one chunk_id.
6. If NONE of the provided chunks state doctrine for this feature, return an empty claims list. Do not force a claim.
7. Discuss only the given feature -- do not reference any other palm feature.

Respond with a single JSON object, no prose outside it, matching exactly:
{"feature": "<given feature name, copied exactly>", "claims": [{"claim_id": "C1", "chunk_id": "<must exactly match a provided chunk_id>", "claim_text": "<paraphrase>", "valence": "supports|corrective|conditional", "condition_text": "<precondition or null>", "observation_basis": "<the confirmed observation clause this claim applies to>"}]}"""


def _build_user_prompt(feature: str, observation_text: str, chunks: list[dict]) -> str:
    obs_block = observation_text.strip() if observation_text and observation_text.strip() else "(none recorded)"
    chunk_block = "\n\n".join(f"[{c['chunk_id']}]\n{c['text']}" for c in chunks)
    return (
        f"FEATURE: {feature}\n\n"
        f"CONFIRMED OBSERVATIONS (from the user's photographed hand(s)):\n- {obs_block}\n\n"
        f"RETRIEVED CHUNKS (use ONLY these -- do not draw on outside knowledge):\n{chunk_block}\n\n"
        f"Extract claims per your instructions."
    )


# E2F step 1: extracts the chunk_id an E-3 (paraphrase-overlap-floor)
# failure names, from the exact message shape _validate_response builds
# at lines 250-252 below (f"...for chunk {chunk_id!r}"). repr() of a str
# quotes with '...' unless the string itself contains a single quote, so
# this pattern assumes the former -- matching every chunk_id this corpus
# actually produces (ingestion-generated, no apostrophes). A failure
# string that doesn't match (E-1/E-2 failures, malformed-JSON, etc.)
# simply contributes no chunk_id to the retry's excluded set.
_E3_CHUNK_ID_PATTERN = re.compile(r"for chunk '([^']+)'$")


# F2c retry correction-instruction pattern, same shape as
# palm_reading.py's own S66 F2c retry ("Your draft failed these checks:
# ...; Rewrite the reading correcting ONLY these issues. Same facts, same
# structure.") -- deterministic-reviewer-only (Python's own E-1/E-2/E-3
# checks below observe the response independently, then hand that
# observation to the model as a correction instruction; this is NOT
# AI-reviewing-AI, CLAUDE.md Working Style #5/#9), same single-retry
# shape, adapted to per-feature extraction instead of whole-reading voice.
#
# E2F step 3a (supersedes step 1's original approach here, which is what
# caused the 2026-07-29 dogfood empty_retry regression): turn 1 (the
# first user message) ALWAYS presents the full, unfiltered `chunks` list
# -- this must match what attempt 1 actually saw, because turn 2 (the
# prior assistant response, echoed back verbatim as `prior_raw`) may
# cite a chunk that would otherwise vanish from turn 1's own presented
# list, producing an incoherent conversation history (turn 2 references
# a chunk turn 1 never showed) that reliably drove the model to decline
# rather than resolve the contradiction. Retry-pool discipline is
# instead enforced ONLY via turn 3's correction instruction, which names
# any E-3-excluded chunk_ids explicitly and tells the model not to cite
# them -- discipline by instruction, not by rewriting history. When
# excluded_chunk_ids is empty (a non-E-3 failure -- E-1/E-2/malformed-
# JSON -- triggered the retry), the OLD "Same chunks, same feature"
# wording stays accurate, since nothing is actually excluded.
def _build_retry_messages(
    feature: str, observation_text: str, chunks: list[dict],
    prior_raw: str, failures: list[str], excluded_chunk_ids: set[str],
) -> list[dict]:
    if excluded_chunk_ids:
        quoted_ids = ", ".join(f"'{cid}'" for cid in sorted(excluded_chunk_ids))
        instruction = (
            "The following chunk(s) failed the overlap check on attempt 1 "
            "and must NOT be cited on this retry: " + quoted_ids + ". "
            "Cite only from the remaining chunks in the list above."
        )
    else:
        instruction = "Same chunks, same feature."
    return [
        {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(feature, observation_text, chunks)},
        {"role": "assistant", "content": prior_raw},
        {
            "role": "user",
            "content": (
                "Your extraction failed these checks: " + "; ".join(failures) + ". "
                "Re-extract claims for this feature, correcting ONLY these issues. "
                + instruction
            ),
        },
    ]


def _call_llm(client, messages: list[dict]) -> str:
    """Single try/except boundary around one API call. Raises the
    underlying exception to the caller, which owns retry/fail-closed
    decisions -- this function never swallows errors itself."""
    response = client.chat.completions.create(
        model=_EXTRACTION_MODEL,
        messages=messages,
        temperature=_EXTRACTION_TEMPERATURE,
        timeout=_EXTRACTION_TIMEOUT_SECONDS,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


# ─── Deterministic validators (E-1/E-2/E-3) ──────────────────────────────

_REQUIRED_CLAIM_KEYS = frozenset({"chunk_id", "claim_text", "valence", "condition_text", "observation_basis"})


def _validate_response(
    raw: str, chunk_map: dict[str, str],
) -> tuple[list[dict] | None, list[str], int | None]:
    """Returns (accepted_raw_claims, failures, raw_claim_count).
    accepted_raw_claims is None iff failures is non-empty -- an
    ALL-OR-NOTHING result per feature call (any single claim's E-1/E-2/E-3
    violation rejects the whole response, matching palm_reading.py's own
    F2c precedent of retrying the whole draft, never patching individual
    sentences). raw_claim_count is the PRE-VALIDATION count of items in
    the model's own "claims" list -- observed, not inferred -- and is None
    only when that list itself could not be determined (malformed JSON, or
    a missing/non-list "claims" key). Measurement-only addition: does not
    affect which claims are accepted or which failures are raised."""
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, [f"malformed JSON response: {exc}"], None

    if not isinstance(parsed, dict) or "claims" not in parsed or not isinstance(parsed["claims"], list):
        return None, ["response missing a top-level 'claims' list"], None

    raw_claim_count = len(parsed["claims"])
    failures: list[str] = []
    accepted: list[dict] = []
    for i, raw_claim in enumerate(parsed["claims"]):
        if not isinstance(raw_claim, dict):
            failures.append(f"claims[{i}] is not an object")
            continue
        # E-2 schema: required fields present, valence in the allowed set.
        # claim_id is deliberately NOT required here -- this module always
        # re-keys with its own counter (see extract_claims), never trusting
        # a model-emitted id for uniqueness, so an absent/duplicate
        # model-side claim_id can never itself be a validation failure.
        missing = _REQUIRED_CLAIM_KEYS - set(raw_claim)
        if missing:
            failures.append(f"claims[{i}] missing keys: {sorted(missing)}")
            continue
        if raw_claim["valence"] not in _VALID_VALENCE:
            failures.append(f"claims[{i}] invalid valence: {raw_claim['valence']!r}")
            continue
        # E-1 legality: chunk_id must belong to THIS feature's OWN gated
        # set (never a whole-reading union) -- retires accepted gaps (a)
        # and (f) from palm_reading.py's V-2 anchor-legality register.
        chunk_id = raw_claim["chunk_id"]
        if chunk_id not in chunk_map:
            failures.append(f"claims[{i}] cites chunk_id {chunk_id!r}, not in this feature's own gated set")
            continue
        # E-3 paraphrase floor.
        overlap = _overlap_ratio(raw_claim["claim_text"], chunk_map[chunk_id])
        if overlap < _PARAPHRASE_OVERLAP_FLOOR:
            failures.append(
                f"claims[{i}] claim_text overlap {overlap:.2f} below floor "
                f"{_PARAPHRASE_OVERLAP_FLOOR} for chunk {chunk_id!r}"
            )
            continue
        accepted.append({**raw_claim, "_overlap": overlap})

    if failures:
        return None, failures, raw_claim_count
    return accepted, [], raw_claim_count


# ─── Dataclasses ───────────────────────────────────────────────────────


@dataclass(frozen=True)
class Claim:
    claim_id: str
    feature: str
    chunk_id: str
    claim_text: str
    valence: str
    condition_text: str | None
    observation_basis: str
    excluded_from_voice: bool
    exclusion_reason: str | None


@dataclass(frozen=True)
class ExtractionResult:
    claims: tuple[Claim, ...]
    failed_features: tuple[str, ...]
    diagnostics: dict = field(default_factory=dict)


# ─── E-4: conditional fail-closed ────────────────────────────────────────

_UNVERIFIED_PRECONDITION_REASON = "precondition unverified"


def _apply_e4(
    accepted_raw_claims: list[dict], feature: str, observation_text: str, counter: itertools.count,
) -> tuple[list[Claim], list[dict]]:
    """E-4: valence=conditional OR a populated condition_text (checked
    together, regardless of valence label -- a "supports"/"corrective"
    claim that nonetheless carries a non-null condition_text is treated
    with the SAME suspicion as an explicitly conditional one, since rule 3
    of the system prompt already asks the model to keep condition_text
    null for any other valence; a populated one there is either a real
    unstated precondition or a prompt-compliance slip, and this module
    fails closed on either) -> excluded_from_voice=True,
    exclusion_reason="precondition unverified", UNLESS condition_text is a
    case-insensitive substring of this feature's own confirmed observation
    text. Exact-substring only, no fuzzy matching -- coarse by design;
    direction of error is omission (a real match phrased differently is
    missed and the claim stays excluded), never a false verification."""
    claims: list[Claim] = []
    exclusion_ledger: list[dict] = []
    obs_lower = (observation_text or "").lower()

    for raw_claim in accepted_raw_claims:
        claim_id = f"C{next(counter)}"
        condition_text = raw_claim.get("condition_text")
        valence = raw_claim["valence"]

        excluded = False
        reason = None
        if valence == "conditional" or condition_text is not None:
            if condition_text and condition_text.lower() in obs_lower:
                excluded = False
            else:
                excluded = True
                reason = _UNVERIFIED_PRECONDITION_REASON

        claim = Claim(
            claim_id=claim_id,
            feature=feature,
            chunk_id=raw_claim["chunk_id"],
            claim_text=raw_claim["claim_text"],
            valence=valence,
            condition_text=condition_text,
            observation_basis=raw_claim.get("observation_basis", ""),
            excluded_from_voice=excluded,
            exclusion_reason=reason,
        )
        claims.append(claim)
        if excluded:
            exclusion_ledger.append({
                "claim_id": claim_id, "feature": feature, "chunk_id": claim.chunk_id,
                "reason": reason, "condition_text": condition_text,
            })

    return claims, exclusion_ledger


# ─── Public API ─────────────────────────────────────────────────────────


def extract_claims(
    gated_results: dict[str, list[dict]],
    texts_by_feature: dict[str, str],
    client=None,
) -> ExtractionResult:
    """One extraction call per feature present in `gated_results` with a
    non-empty chunk list (a feature with zero gated chunks is skipped
    entirely -- nothing to extract from, not a failure). Same
    `gated_results` shape palm_reading._apply_support_gate emits: dict
    mapping feature name -> list of chunk dicts (each with at least
    chunk_id/text keys; extra keys like score/page_ref are ignored here).

    F2c semantics, per feature (not per stage): an E-1/E-2/E-3 validation
    failure on a feature's response triggers exactly ONE retry for THAT
    feature only, with the failure list fed back as a correction
    instruction (same pattern as palm_reading.py's own S66 F2c retry).
    Hard cap: 2 LLM calls per feature, no exceptions. A feature whose
    retry ALSO fails validation lands in `failed_features` -- fail-closed:
    zero claims from it survive, and it is the caller's job (a later
    wiring prompt) to treat it as unsupported downstream.

    client: injection seam for tests -- if None, a real OpenAI() client is
    constructed lazily INSIDE this function (never at module import time;
    palm_reading.py's own S65 flag (b) documents the conftest-stubbing
    breakage a module-level import causes, not repeated here).

    Raises:
        RuntimeError: every feature that had gated chunks failed
                      extraction (both calls each) -- nothing extractable
                      at all, matching the Stage-1 fail-closed ruling (no
                      reading is possible from zero surviving claims). A
                      `gated_results` with NO feature having any gated
                      chunks (e.g. every feature declined) is NOT this
                      case -- that returns an empty, non-raising
                      ExtractionResult, since there was nothing to attempt
                      in the first place.
    """
    if client is None:
        from openai import OpenAI  # lazy import -- see docstring
        client = OpenAI()

    counter = itertools.count(1)
    all_claims: list[Claim] = []
    failed_features: list[str] = []
    exclusion_ledger: list[dict] = []
    feature_diagnostics: dict[str, dict] = {}

    # If this is empty (every feature's gated chunk list is empty), the
    # loop below never runs and this function returns an empty, non-
    # raising ExtractionResult -- no LLM call at all. Downstream, this is
    # the root of palm_reading.py's own NOTED BEHAVIOR CHANGE (S69 F-H
    # close-out, CLAUDE.md): the old single-call architecture still made
    # one low-confidence LLM call here; this one makes zero.
    attempted_features = [f for f, chunks in gated_results.items() if chunks]

    for feature in attempted_features:
        chunks = gated_results[feature]
        chunk_map = {c["chunk_id"]: c["text"] for c in chunks}
        observation_text = texts_by_feature.get(feature, "") or ""
        # diag enum reference (no prior enum listing existed in this module
        # before E2F step 1 -- added here as the closest diag-initialization
        # anchor point):
        #   attempt_1_status / attempt_2_status: "not_attempted", "error",
        #     "validation_failed", "validated", "validated_empty",
        #     "skipped_no_viable_chunks" (E2F step 1, new).
        #   attempt_1_raw_count / attempt_2_raw_count: PRE-VALIDATION count
        #     of items in the model's own "claims" list (measurement-only,
        #     see _validate_response's docstring) -- None when no response
        #     was parsed at all (API error, not attempted, or the response
        #     itself was malformed/missing the "claims" key).
        #   final_outcome: "failed_first_no_retry", "failed_both",
        #     "success_first", "success_retry", "empty_first", "empty_retry",
        #     "failed_first_no_viable_retry" (E2F step 1, new).
        # No runtime validation enforces these as a closed set.
        diag: dict = {
            "call_count": 0, "retry_used": False,
            "attempt_2_status": "not_attempted", "attempt_2_claim_count": None,
            "attempt_2_raw_count": None,
        }

        diag["call_count"] += 1
        try:
            raw = _call_llm(client, [
                {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(feature, observation_text, chunks)},
            ])
        except Exception as exc:  # noqa: BLE001 -- one bad call must not crash extract_claims
            failed_features.append(feature)
            diag["status"] = "failed"
            diag["error"] = f"claim_extraction: API call failed for feature {feature!r}: {exc}"
            diag["attempt_1_status"] = "error"
            diag["attempt_1_claim_count"] = 0
            diag["attempt_1_raw_count"] = None
            diag["final_outcome"] = "failed_first_no_retry"
            feature_diagnostics[feature] = diag
            continue

        accepted, failures, raw_claim_count = _validate_response(raw, chunk_map)
        diag["attempt_1_raw_count"] = raw_claim_count

        if failures:
            diag["attempt_1_status"] = "validation_failed"
            diag["attempt_1_claim_count"] = 0
        elif accepted:
            diag["attempt_1_status"] = "validated"
            diag["attempt_1_claim_count"] = len(accepted)
        else:
            diag["attempt_1_status"] = "validated_empty"
            diag["attempt_1_claim_count"] = 0

        if failures:
            diag["first_attempt_failures"] = tuple(failures)
            # E2F step 1: drop any chunk an E-3 failure already named from
            # the retry's own pool -- the root cause this step fixes is the
            # retry being told "same chunks" and re-attempting a claim
            # against the SAME chunk it just failed the overlap floor on
            # (Run 2 evidence: p.88_c0 attempt 1 overlap 0.08, attempt 2
            # still against p.88_c0, overlap 0.20, still below floor, while
            # a validatable chunk sat unused at rank 2). Non-E-3 failures
            # (E-1/E-2/malformed-JSON) contribute no chunk_id here, so the
            # pool is unchanged for those -- matches _E3_CHUNK_ID_PATTERN's
            # own module comment.
            excluded_chunk_ids = {
                match.group(1)
                for f in failures
                if (match := _E3_CHUNK_ID_PATTERN.search(f))
            }
            remaining_chunks = [c for c in chunks if c["chunk_id"] not in excluded_chunk_ids]
            if not remaining_chunks:
                # Every attempt-1 chunk failed E-3 -- no viable chunk left
                # to retry against. Retrying here would only repeat Run 2's
                # exact failure mode (re-attempting against a chunk already
                # known to fail the overlap floor), so the retry call is
                # skipped entirely rather than burning a second LLM call on
                # a pool that cannot pass.
                diag["retry_used"] = False
                diag["attempt_2_status"] = "skipped_no_viable_chunks"
                diag["attempt_2_claim_count"] = None
                diag["final_outcome"] = "failed_first_no_viable_retry"
                diag["status"] = "failed"
                failed_features.append(feature)
                feature_diagnostics[feature] = diag
                continue
            diag["retry_used"] = True
            diag["call_count"] += 1
            try:
                raw = _call_llm(client, _build_retry_messages(
                    feature, observation_text, chunks, raw, failures, excluded_chunk_ids
                ))
            except Exception as exc:  # noqa: BLE001
                failed_features.append(feature)
                diag["status"] = "failed"
                diag["error"] = f"claim_extraction: API retry failed for feature {feature!r}: {exc}"
                diag["first_attempt_failures"] = failures
                diag["attempt_2_status"] = "error"
                diag["attempt_2_claim_count"] = None
                diag["attempt_2_raw_count"] = None
                diag["final_outcome"] = "failed_both"
                feature_diagnostics[feature] = diag
                continue
            accepted, failures, raw_claim_count = _validate_response(raw, chunk_map)
            diag["attempt_2_raw_count"] = raw_claim_count

        if failures:
            failed_features.append(feature)
            diag["status"] = "failed"
            diag["failures"] = failures
            diag["attempt_2_status"] = "validation_failed"
            diag["attempt_2_claim_count"] = 0
            diag["final_outcome"] = "failed_both"
            feature_diagnostics[feature] = diag
            continue

        if diag["retry_used"]:
            diag["attempt_2_status"] = "validated" if accepted else "validated_empty"
            diag["attempt_2_claim_count"] = len(accepted)
            diag["final_outcome"] = "success_retry" if accepted else "empty_retry"
        else:
            diag["final_outcome"] = "success_first" if accepted else "empty_first"

        claims, this_exclusion_ledger = _apply_e4(accepted, feature, observation_text, counter)
        all_claims.extend(claims)
        exclusion_ledger.extend(this_exclusion_ledger)
        diag["status"] = "ok"
        diag["claim_count"] = len(claims)
        diag["overlap_scores"] = [
            {"claim_id": c.claim_id, "chunk_id": c.chunk_id, "overlap": round(a["_overlap"], 3)}
            for c, a in zip(claims, accepted)
        ]
        feature_diagnostics[feature] = diag

    if attempted_features and len(failed_features) == len(attempted_features):
        raise RuntimeError(
            "claim_extraction.extract_claims: all "
            f"{len(attempted_features)} attempted feature(s) failed extraction "
            f"({sorted(failed_features)}) -- nothing extractable, no reading possible."
        )

    diagnostics = {"features": feature_diagnostics, "exclusion_ledger": exclusion_ledger}

    return ExtractionResult(
        claims=tuple(all_claims),
        failed_features=tuple(failed_features),
        diagnostics=diagnostics,
    )
