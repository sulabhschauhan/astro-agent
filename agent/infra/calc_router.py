"""Deterministic question router for the thin-slice answer pipeline, with
a Stage 2 LLM-constrained-classification fallback (Session 49+, P7.1
hybrid router). 4 routable domains as of Session 50/P7.2c: the original
3-domain whitelist (marriage_compatibility, career_strength, current_dasha)
plus sade_sati.

sade_sati is routed differently from the other 3: it never goes through
_DOMAIN_KEYWORDS/_score_domain's floor/margin scoring at all. Instead it
has its own deterministic _BUILT_MODULE_FASTPATH phrase match, checked
immediately after the unbuilt-module/out-of-scope REFUSAL checks and
before domain scoring -- a flagship differentiator (the ONLY module this
pipeline can answer with zero ambiguity, per golden q14) must never
depend on Stage 2/GPT-4o-mini being available or correct. Stage 2 can
still independently classify a question as sade_sati (added to
_STAGE2_VALID_DOMAINS) for questions the fast-path phrase list doesn't
literally catch -- both paths converge on the same _route_to_domain()
sade_sati branch (T1, no demotion, no partner).

Stage 1 (keyword scoring, _score_domain) runs first, always, and short-
circuits on the unbuilt-module-keyword and out-of-scope-keyword REFUSAL
paths before Stage 2 is even reachable. Stage 2 (GPT-4o-mini, constrained
tool-call output, _stage2_classify) fires ONLY when Stage 1 REFUSEs via the
confidence-floor or margin-tie path. Stage 2 is independent classification,
not a second opinion on Stage 1's scores (no anchored judgment, CLAUDE.md
Working Style #9) -- it receives ONLY the raw question text, never Stage 1's
scores or matched keywords. Stage 2 routes ONLY on "high" confidence;
"medium"/"low"/"none", or ANY exception (network, auth, timeout, malformed
output, schema violation), fails CLOSED to the same REFUSAL Stage 1 alone
would have produced -- never a crash, never a guessed domain. Every Stage 2
invocation is logged to diagnostics/calc_router_stage2.log (append-only
JSONL), never to chat (CLAUDE.md Working Style #10).

SCOPE BOUNDARY: this module does not call calculate_chart() or
build_domain_profile() itself -- it classifies a question string into a
domain + tier, nothing more. evaluated_at_jd (build_domain_profile's second
positional arg) must be derived by the future caller/orchestrator from a
swe.julday() conversion of datetime.now(timezone.utc), captured at
approximately the same instant calculate_chart() is invoked -- this mirrors
_calc_dasha()'s own internal `datetime.now(tz=birth_local.tzinfo)` anchor
(agent/chart_calculator.py) and chart_profile.py's build_domain_profile
docstring ("must be the SAME instant the caller used for the dasha lookup").
Not implemented here because route_question() never calls calculate_chart().
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from agent.infra.chart_profile import AnswerTier

# ─── Domain keyword whitelists (Layer A only) ─────────────────────────────

_MARRIAGE_KEYWORDS: tuple[str, ...] = (
    "marriage", "compatibility", "partner", "kundli milan", "ashtakoot",
    "mangal dosha", "7th house", "spouse", "wedding", "relationship",
)

_CAREER_KEYWORDS: tuple[str, ...] = (
    "career", "job", "profession", "work", "business", "10th house",
    "shadbala", "strength", "saturn", "promotion", "success",
)

_DASHA_KEYWORDS: tuple[str, ...] = (
    "dasha", "period", "mahadasha", "antardasha", "current period",
    "running period", "timing", "when", "phase",
)

# av_transit (Session 55 router wiring). Deliberately NOT "transit" --
# _UNBUILT_MODULE_KEYWORDS' bare "transit" keyword already REFUSES before
# domain scoring is reached (P7.0b's "transition"/"transitional" false-
# positive precedent generalizes: a bare "transit" hit is too ambiguous
# with the gochara transit engine to trust as a fast-path signal). "sav"/
# "bav" also excluded -- 3-letter tokens collide too easily with unrelated
# substrings under _keyword_hits' bidirectional containment. Layman timing
# phrasing ("when is my luck good", etc. with no Ashtakavarga-family term)
# is Stage 2's job by design, not fast-path keyword material.
_AV_TRANSIT_KEYWORDS: tuple[str, ...] = (
    "ashtakavarga", "bindu", "kakshya",
)

# arudha_lagna (Session 58 router wiring). Public-image/perception phrasing
# ("public image", "public perception") alongside the literal Jaimini terms
# ("arudha lagna", "arudha pada") -- mirrors av_transit's precedent of
# pairing a technical term list with the layman phrasing Stage 1 can catch
# directly, without requiring Stage 2 for the common case.
_ARUDHA_LAGNA_KEYWORDS: tuple[str, ...] = (
    "arudha lagna", "arudha pada", "public image", "public perception",
)

# upapada_lagna (Session 65 router wiring). A single unambiguous Sanskrit
# term ("upapada") plus its natural bigram ("upapada lagna") -- zero
# collision risk with any other domain's keywords. Deliberately narrower
# than arudha_lagna's keyword set above: NO layman phrasing is added here
# (no "spouse image"/"marriage indicator"-style synonym) -- layman
# reachability is Stage 2's job by design, per the Session 61 Stage 2
# layman-intent prompt expansion convergence lock (CLAUDE.md Locked
# Decisions: "converging Stage 2's classification quality is the locked
# remedy path, router-threshold tuning stays gated on Answer Scorecard
# evidence"). The bigram entry lets a full "upapada lagna" mention clear
# both list entries (2 hits, same >=2-hits-to-route mechanics documented
# on _CONFIDENCE_FLOOR above) while a bare "upapada" mention alone (1 hit)
# still falls through to Stage 2, same as arudha_lagna's own keyword list
# behavior for a bare technical-term mention.
_UPAPADA_LAGNA_KEYWORDS: tuple[str, ...] = (
    "upapada", "upapada lagna",
)

# muhurta_window (Session 64, P7 Muhurta wiring step 4 of 6). Electional-
# astrology terms: the Sanskrit term itself ("muhurta"), its common Hindi/
# Devanagari-transliteration variant ("mahurat"), and layman auspicious-
# timing vocabulary ("auspicious", "shubh", "electional"). Unlike
# sade_sati, this domain is NOT a deterministic fast-path -- it goes
# through the normal _DOMAIN_KEYWORDS/_score_domain floor+margin scoring
# like marriage/career/dasha/av_transit/arudha_lagna/upapada_lagna above,
# because (unlike sade_sati.py's single flagship-differentiator status)
# there is no product reason to bypass Stage 2 for this domain.
# Collision-checked programmatically (diagnostics/latest_run.md) against
# every existing domain's keyword list, _STEM_MAP, _UNBUILT_MODULE_KEYWORDS
# (post-"muhurta"-removal), _OUT_OF_SCOPE_KEYWORDS, and
# _BUILT_MODULE_FASTPATH before wiring -- zero collisions found. "when" (a
# _DASHA_KEYWORDS entry) is NOT a collision risk: Stage 1 scoring tallies
# each domain's keyword hits independently, not from a shared token pool,
# so a question containing both "when" and "muhurta" simply scores both
# domains separately, resolved normally by the floor/margin/Stage-2
# mechanics -- no special-casing needed here.
_MUHURTA_WINDOW_KEYWORDS: tuple[str, ...] = (
    "muhurta", "mahurat", "auspicious", "shubh", "electional",
)

_DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "marriage_compatibility": _MARRIAGE_KEYWORDS,
    "career_strength": _CAREER_KEYWORDS,
    "current_dasha": _DASHA_KEYWORDS,
    "av_transit": _AV_TRANSIT_KEYWORDS,
    "arudha_lagna": _ARUDHA_LAGNA_KEYWORDS,
    "upapada_lagna": _UPAPADA_LAGNA_KEYWORDS,
    "muhurta_window": _MUHURTA_WINDOW_KEYWORDS,
}

# Calculation modules referenced in a question but NOT in the routable
# whitelist -> immediate REFUSAL naming the unbuilt module, checked BEFORE
# domain classification.
#
# "sade sati" REMOVED Session 50/P7.2c (was DESIGN_DEBT per
# golden_harness.py's _DESIGN_DEBT["sulabh_dasha_q14"]: sade_sati.py is
# built and 4-chart validated, unlike the genuinely-unbuilt modules below
# -- refusing it here was product debt, not a locked decision). Now routed
# via _BUILT_MODULE_FASTPATH instead.
# Session 58: "jaimini" removed -- all jaimini/ modules exist as of
# Session 57; unwired-Q&A refusals now go through the router's normal
# "domain not routable" path, not this guard.
# Session 64 (P7 Muhurta wiring step 4 of 6): "muhurta" REMOVED -- same
# precedent as sade_sati/jaimini above: the scorer (transits/chandrabala.py,
# tarabala.py, panchaka.py, muhurta_scorer.py) is now wired to Q&A, routed
# via _DOMAIN_KEYWORDS/_score_domain like any other keyword-scored domain
# (NOT a deterministic fast-path like sade_sati -- see
# _MUHURTA_WINDOW_KEYWORDS's own comment, below, for why).
_UNBUILT_MODULE_KEYWORDS: dict[str, str] = {
    "yoga": "yoga detection",
    "transit": "transit engine (gochara)",
    "gochara": "gochara transit engine",
    "navamsa": "D9 (Navamsa) divisional chart",
    "divisional": "divisional charts (vargas)",
    "d10": "D10 divisional chart",
    "d9": "D9 (Navamsa) divisional chart",
    "varga": "divisional charts (vargas)",
    "chara": "Chara dasha",
    "yogini": "Yogini dasha",
    "ashtottari": "Ashtottari dasha",
    "varshaphal": "Varshaphal annual chart",
}

# Deterministic fast-path for the ONE built-and-validated module this
# pipeline can route with zero ambiguity: sade_sati.py (4-chart validated,
# CLAUDE.md P2 order). Checked AFTER the unbuilt-module/out-of-scope
# REFUSAL checks and BEFORE domain scoring -- same word-boundary regex as
# _UNBUILT_MODULE_KEYWORDS above. This is deliberately NOT folded into
# _DOMAIN_KEYWORDS/_score_domain: the flagship differentiator (golden
# q14) must route with certainty regardless of Stage 2/GPT-4o-mini's
# availability or correctness, not be subject to the same floor/margin
# scoring or Stage-2 fallback the other 3 domains depend on. Stage 2 can
# still independently classify "sade_sati" (see _STAGE2_VALID_DOMAINS)
# for phrasings this literal list doesn't catch.
_BUILT_MODULE_FASTPATH: dict[str, str] = {
    "sade sati": "sade_sati",
    "sadesati": "sade_sati",
    "sadhe sati": "sade_sati",
}

# Minimal, spec-named out-of-scope categories: medical diagnosis, legal
# advice, stock picks. Not exhaustive -- V1 conservative default, see
# THRESHOLD DISCIPLINE note on _CONFIDENCE_FLOOR below for the same caveat
# class (requires dogfooding tuning, not expanded speculatively here).
_OUT_OF_SCOPE_KEYWORDS: tuple[str, ...] = (
    "medical diagnosis", "diagnose", "disease", "cancer", "legal advice",
    "lawsuit", "divorce settlement", "stock pick", "stock tip",
    "buy stock", "sell stock", "stock market", "share market", "bitcoin",
    "cryptocurrency", "crypto", "invest in",
)

# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4):
# _CONFIDENCE_FLOOR / _CONFIDENCE_MARGIN gate which domain (if any) a
# question routes to. Justification: V1 conservative defaults -- false
# ROUTE is worse than false REFUSAL for a deterministic-only pipeline with
# no LLM fallback (Session 23 lock: no LLM synthesis anywhere in this
# pipeline). Scope guard: applies ONLY to the 3-domain whitelist
# (marriage_compatibility / career_strength / current_dasha); does not
# generalize to a future Layer B LLM classifier (Phase 10/V2), which would
# use a different confidence mechanism entirely.
# Re-justified for the S44.3b saturating formula (_score_domain):
# min(matched_keywords, 3) / 3 puts every domain's score on a fixed [0, 1]
# range regardless of that domain's keyword-list length -- a keyword-list
# entry beyond the 3rd match stops being individually punishing, which
# fixed S44.3's flagged issue (11-keyword career list needing 5 hits to
# clear 0.4 under the old matched/total formula). Under the new formula:
# 1 matched keyword -> 0.333, still BELOW floor -- deliberately so; a
# single keyword hit is still not enough to route (same V1-conservative
# stance as before, just no longer scaled by list length). 2 matched
# keywords -> 0.667, clears both floor and margin against any 0-scoring
# competing domain. Practical effect: this router now requires >=2
# distinct keyword-list hits to route ANY domain, regardless of list size.
# Not loosened further unilaterally here -- flagged, not silently patched.
_CONFIDENCE_FLOOR = 0.4
_CONFIDENCE_MARGIN = 0.15

# THRESHOLD DISCIPLINE: 37 days is not tunable here -- it is a direct
# citation of chart_calculator.py's _calc_dasha() DASHA ACCURACY NOTE
# (documented +/-37-day Antardasha drift vs AstroSage). Changing this
# value requires a new cross-oracle study, not a router-local decision.
_DASHA_BOUNDARY_WINDOW_DAYS = 37

# Decision (Session 46, design chat): career stays T2 despite Drik Bala
# being real (28/28 JHora parity). Rationale: residual documented envelopes
# still make exact ranks dishonest for closely-ranked planets; consistent
# with V1 refuse-heavy posture. Revisit T1 promotion when the Ayana Bala
# investigation closes.
_CAREER_DEMOTION_REASON = (
    "Career strength held at Tier 2 (range): residual Shadbala uncertainty "
    "envelopes (±6 Virupa Ayana Bala general; ±59 Virupa Surbhi Kala Bala "
    "chart-specific) can flip close planet rankings; rank within envelope "
    "should be treated as approximate"
)
_DASHA_DEMOTION_REASON = (
    "Antardasha boundaries carry ±37-day drift vs AstroSage; the current "
    "lord itself is reliable, but any date given for its start/end should "
    "be treated as approximate"
)
_DASHA_DEMOTION_REASON_NEAR_BOUNDARY = (
    "Antardasha boundaries carry ±37-day drift vs AstroSage; within that "
    "window of a boundary, the drift can flip which lord is actually "
    "current -- both the current lord's identity and its dates should be "
    "treated as approximate"
)

# ─── Stage 2: LLM-constrained-classification fallback (Session 49+/P7.1) ──

# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
# Justification: gpt-4o-mini matches the model already used at this
# codebase's other LLM classification call site (context_classifier.py's
# Layer 1 gate) -- consistent cost/latency profile, cheap enough to run
# per-REFUSAL at V1's expected query volume. Scope guard: governs ONLY this
# file's Stage 2 fallback call -- each LLM call site in this codebase owns
# its own model constant (no shared "the model" constant exists); do not
# import this into other modules. Revisit trigger: if dogfooding shows
# Stage 2 misclassifying at a rate that matters, evaluate gpt-4o (full)
# before touching the confidence thresholds below.
_STAGE2_MODEL = "gpt-4o-mini"

# THRESHOLD DISCIPLINE. Justification: keeps Stage 2 well under a
# synchronous request-response UX budget (Session 3's SSE-streaming fix was
# itself a response to 6-11s latency complaints elsewhere in this codebase)
# while leaving several seconds of margin over GPT-4o-mini's typical
# sub-2s single-tool-call latency. Scope guard: a per-call timeout on the
# OpenAI SDK request only -- no retry/backoff/circuit-breaker; a single
# timeout is a hard failure -> REFUSAL (never retried in-request). Revisit
# trigger: if diagnostics/calc_router_stage2.log shows repeated timeout
# outcomes at this value, investigate root cause before raising it blindly.
_STAGE2_TIMEOUT_SECONDS = 8.0

# Domain enum Stage 2 is constrained to via tool-call schema. "none" is a
# real member (not Python None) so the schema has an explicit way to say
# "not one of the 4 domains" -- mapped to Python None at the boundary in
# _stage2_classify, never leaked past this module. "sade_sati" added
# Session 50/P7.2c -- Stage 2 can independently classify a question as
# sade_sati even when it doesn't literally match _BUILT_MODULE_FASTPATH's
# phrase list (e.g. a paraphrase that never says "Sade Sati" outright).
# "av_transit" added Session 55 router wiring -- this is the mandatory
# layman-phrasing path (task item 4): a question asking, in plain words,
# when within the current Antardasha a given transit planet's influence is
# actually favorable/unfavorable, with no "Ashtakavarga"/"bindu"/"kakshya"
# term for _AV_TRANSIT_KEYWORDS to catch, still needs a route.
# "muhurta_window" added Session 64 (P7 Muhurta wiring step 4 of 6) --
# unlike sade_sati, this domain is NOT a deterministic fast-path, so its
# only route to Stage 2 is through this set + the system prompt's own
# gloss/negative-instruction below (same mechanism as every other
# keyword-scored domain).
_STAGE2_VALID_DOMAINS: frozenset[str] = frozenset(
    {
        "marriage_compatibility",
        "career_strength",
        "current_dasha",
        "sade_sati",
        "av_transit",
        "arudha_lagna",
        "upapada_lagna",
        "muhurta_window",
        "none",
    }
)
_STAGE2_VALID_CONFIDENCE: frozenset[str] = frozenset({"high", "medium", "low"})

# THRESHOLD DISCIPLINE. Justification: RouteResult.confidence is a float
# (Stage 1's continuous [0, 1] saturating score); Stage 2 only ever returns
# a coarse high/medium/low enum, and only "high" ever routes (item 3 of the
# Stage 2 spec) -- this map exists purely so a routed RouteResult carries a
# well-defined, documented float instead of a magic literal at the call
# site. Scope guard: 1.0/0.5/0.0 are sentinels, NOT calibrated probabilities
# or measured precision/recall figures. Revisit trigger: if a future prompt
# ever allows medium/low to route, this map must be re-justified against
# real accuracy data per domain, not hand-picked, before it's trusted for
# anything beyond a REFUSAL-vs-ROUTE decision.
_STAGE2_CONFIDENCE_MAP: dict[str, float] = {"high": 1.0, "medium": 0.5, "low": 0.0}

# Append-only diagnostic log, one JSON line per Stage 2 invocation -- never
# printed to chat (CLAUDE.md Working Style #10). Project-root-relative so
# it lands next to every other diagnostics/*.md artifact regardless of cwd.
_STAGE2_LOG_PATH = Path(__file__).resolve().parents[2] / "diagnostics" / "calc_router_stage2.log"

_STAGE2_SYSTEM_PROMPT = """\
You are a routing classifier for a Vedic astrology calculation Q&A pipeline.

This pipeline can ONLY answer questions in exactly 8 domains:
- marriage_compatibility: Ashtakoot/Guna Milan, Mangal Dosha, spouse or \
partner compatibility. Layman: relationship happiness, partner match. \
Example: "will my marriage be happy".
- career_strength: career/profession/work strength, based on Shadbala \
planetary strength. Layman: job change, career direction/progress, \
professional growth. Examples: "should I change my job this year", "is my \
career going anywhere".
- current_dasha: what Mahadasha/Antardasha period the person is currently \
running (identifying the current Mahadasha/Antardasha LORD only, no
finer timing within it). Layman: what life phase/period the person is in \
now, when a difficult or good period will end, timing of life chapters. \
Examples: "what phase of life am I in right now", "when will my bad time \
end".
- sade_sati: whether the person is currently in Sade Sati (Saturn's ~7.5-year \
transit through the 12th/1st/2nd sign from natal Moon), and/or when the \
current, previous, or next Sade Sati cycle starts or ends.
- av_transit: Ashtakavarga-based transit quality (favorable vs. unfavorable \
sub-windows, from Bindu/Kakshya strength) of a specific transiting planet \
DURING the current Antardasha -- finer-grained timing WITHIN the current \
dasha period, not just which lord is currently running. Layman: how a \
specific planet's transit is playing out right now.
- arudha_lagna: questions about self-image, public perception, reputation, \
how one is seen by others (Jaimini Arudha Lagna). Layman: how others \
perceive the person publicly -- reputation, public image, impression made \
on others. Examples: "how do people see me in public", "what is my public \
reputation", "what impression do I make on others".
- upapada_lagna: Jaimini Upapada Lagna (UL) -- the bhava pada of the \
12th house, a SINGLE-CHART marriage/spouse significator read from ONE \
person's chart alone. Layman: what the person's OWN chart suggests \
about their spouse/marriage, with no second person's chart involved. \
An explicit mention of "upapada" or "UL" routes here EVEN IF the \
question also mentions marriage. A question about matching TWO \
people's charts, couple compatibility, or "are we compatible" is \
marriage_compatibility, NEVER upapada_lagna, regardless of any Jaimini \
term present. Examples: "what does my upapada lagna say about my \
marriage", "what is my upapada".
- muhurta_window: Muhurta (electional astrology) -- finding a favorable/ \
auspicious time-WINDOW, in the near future, to START or DO a specific \
action or event (a composite of Chandrabala, Tarabala, and Panchaka over \
a short scan). Layman: picking a good/auspicious time to begin something. \
Examples: "when is a good time to start something new", "what is an \
auspicious muhurta for me this week", "shubh muhurat for starting my \
business", "is this a good day to sign the papers". Muhurta is \
ELECTIONAL -- choosing WHEN, in the near future, to DO something -- and \
must NEVER be confused with NATAL-timing questions about a life period \
or a transit already in progress: "when will my bad time end" or "what \
phase of life am I in" is current_dasha, NOT muhurta_window; "how is \
[planet]'s transit playing out right now" is av_transit, NOT \
muhurta_window; and "when will I get a job" asks when a future life \
EVENT will happen TO the person (current_dasha/natal-timing territory), \
NOT when to ACT (muhurta_window) -- even though all of these questions \
use the word "when". The deciding question: is the person asking to \
PICK a moment to act (muhurta_window), or asking WHEN something already \
in motion (a period, a transit, a life event) will happen or change \
(current_dasha / av_transit)?

Classify the question into exactly one of these domains, or "none" if it
does not clearly ask about one of these 8 things (for example: health,
travel, gemstones, lucky numbers, or any other topic).

Fortune-telling requests with no computable basis in this pipeline -- \
predicting the unqualified future, fame, lottery outcomes, or death/ \
longevity (e.g. "tell me my future", "what do the stars say about me", \
"will I be famous", "when will I die") -- must be classified domain="none", \
even though they superficially resemble astrology questions.

Call classify_domain with:
- domain: the single best-matching domain, or "none".
- confidence: "high" ONLY if the question clearly and unambiguously asks
  about exactly one of the 8 domains above; "medium" or "low" for any
  ambiguity, a different topic, or a domain this pipeline does not cover.
"""

_STAGE2_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "classify_domain",
        # Session 58: "3 routable domains" was already stale pre-edit
        # (actual count had drifted to 5 with sade_sati/av_transit) --
        # design-chat-flagged pre-existing bug, fixed opportunistically here
        # alongside the arudha_lagna wiring, not a drive-by unrelated change.
        "description": (
            "Classify a Vedic astrology question into one of the pipeline's "
            "8 routable domains, or none."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "enum": sorted(_STAGE2_VALID_DOMAINS)},
                "confidence": {"type": "string", "enum": sorted(_STAGE2_VALID_CONFIDENCE)},
            },
            "required": ["domain", "confidence"],
            "additionalProperties": False,
        },
    },
}


@dataclass(frozen=True)
class RouteResult:
    """Output of route_question() -- classification only, no side effects."""

    domain: str | None          # None on REFUSAL
    tier: AnswerTier            # always set
    confidence: float           # 0.0 on REFUSAL
    demotion_reason: str | None # set on REFUSAL or T1->T2 demotion
    requires_partner: bool      # True only for marriage domain
    # Which mechanism actually resolved this result (Session 72 carry-
    # forward, escalated Session 55/59). "fastpath" is distinct from
    # "stage1": the sade_sati fast-path bypasses _DOMAIN_KEYWORDS/
    # _score_domain entirely (see module docstring), so it is not the
    # same mechanism as Stage 1's floor+margin keyword scoring even
    # though both are LLM-free. "pre_classification" covers the
    # unbuilt-module-keyword and out-of-scope-keyword guards in
    # route_question(), which REFUSE before Stage 1 scoring, the
    # fast-path, or Stage 2 ever run -- no domain-resolution mechanism
    # was engaged at all for these. No default: every construction site
    # must set this explicitly.
    route: Literal["stage1", "stage2", "fastpath", "pre_classification"]


# Irregular/derivational-form -> canonical keyword. S44.3b's suffix-strip
# normalizer (strip trailing s/ed/ing) could not bridge these -- they are
# different-derivation word families, not suffix variants of the same
# stem (e.g. "married" is marry+ed with a spelling change, not
# marriage+suffix; "compatible"/"compatibility" diverge at the 9th
# character, "-ble" vs "-ility"). Seeded with EXACTLY the failures S44.3b's
# smoke tests surfaced -- grows via dogfooding-observed misses only, not
# speculative pre-population. Do not add entries for forms that haven't
# actually been observed failing.
_STEM_MAP: dict[str, str] = {
    "married": "marriage",
    "marry": "marriage",
    "compatible": "compatibility",
    "compat": "compatibility",
    "job": "career",
    "jobs": "career",
    "working": "career",
}


def _normalize_tokens(text: str) -> list[str]:
    """Lowercase alnum tokens, ADDITIVELY expanded with _STEM_MAP hits.

    Additive, not a replacement substitution: a raw token that's a
    _STEM_MAP key (e.g. "job") stays in the token list AND contributes
    its canonical mapped form ("career") as an extra token. This keeps
    "job" able to match the literal "job" keyword while also crediting
    "career" -- replacing the token outright would silently break the
    literal keyword match for no reason. Regular plural/gerund variants
    NOT in the map (e.g. "wedding"/"wed", "jobs"/"job") still match their
    keyword via plain substring containment in _keyword_hits below -- no
    generic stemming needed for those, which is why _STEM_MAP only needs
    to carry the handful of irregular cases a substring check can't reach
    on its own.
    """
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    expanded = list(tokens)
    for tok in tokens:
        mapped = _STEM_MAP.get(tok)
        if mapped is not None:
            expanded.append(mapped)
    return expanded


def _keyword_hits(keyword: str, question_tokens: list[str]) -> bool:
    """True if `keyword` (single- or multi-word) matches the question tokens.

    Multi-word keywords ("mangal dosha", "7th house") match as a
    normalized phrase substring -- word adjacency/order is part of the
    signal for a phrase. Single-word keywords match via bidirectional
    substring containment against each normalized question token (not
    just keyword-in-token) so plain plural/gerund variants match their
    keyword for free (e.g. token "wedding" contains keyword "wed" as a
    literal prefix) without needing a _STEM_MAP entry. Both sides
    guarded to >=3 chars to avoid trivial short-token noise.
    """
    keyword_tokens = _normalize_tokens(keyword)
    if len(keyword_tokens) > 1:
        return " ".join(keyword_tokens) in " ".join(question_tokens)
    kw = keyword_tokens[0]
    if len(kw) < 3:
        return False
    return any(len(tok) >= 3 and (kw in tok or tok in kw) for tok in question_tokens)


def _score_domain(question_tokens: list[str], keywords: tuple[str, ...]) -> float:
    """Saturating score: min(matched_keywords, 3) / 3. See THRESHOLD
    DISCIPLINE comment on _CONFIDENCE_FLOOR/_CONFIDENCE_MARGIN above for
    the re-justification of the unchanged 0.4/0.15 thresholds against
    this formula's [0, 1] range.
    """
    matched = sum(1 for kw in keywords if _keyword_hits(kw, question_tokens))
    return min(matched, 3) / 3


def _near_dasha_boundary(
    chart_data: dict, window_days: int = _DASHA_BOUNDARY_WINDOW_DAYS
) -> bool:
    """True if now (UTC) is within window_days of current_antardasha's start or end.

    Dates come from chart_calculator._fmt()'s "D Mon YYYY" format (day-level
    precision only, no time-of-day) -- comparison is therefore date-level,
    not instant-level.
    """
    current_ad = (chart_data.get("dasha") or {}).get("current_antardasha")
    if not current_ad:
        return False

    try:
        start = datetime.strptime(current_ad["start"], "%d %b %Y")
        end = datetime.strptime(current_ad["end"], "%d %b %Y")
    except (KeyError, ValueError, TypeError) as exc:
        raise RuntimeError(
            f"calc_router._near_dasha_boundary: could not parse "
            f"current_antardasha start/end: {exc}"
        ) from exc

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return (
        abs((now - end).days) <= window_days
        or abs((now - start).days) <= window_days
    )


def _stage2_classify(
    question: str, client: object | None = None
) -> tuple[str | None, str]:
    """Stage 2 LLM-constrained-classification fallback (routing only).

    Independent classification -- receives ONLY the raw question text,
    never Stage 1's scores or matched keywords (CLAUDE.md Working Style #9,
    no anchored judgment: the LLM observes independently, Python does the
    comparing). Constrained tool-call output only -- no free-text parsing,
    no regex extraction of a JSON blob from prose (deliberately not reusing
    context_classifier.py's json.loads(raw-content) pattern).

    `client` is a test-only injection seam (default None). Production
    callers never pass it -- route_question()'s own default threads None
    through here, and the real OpenAI client is constructed lazily below,
    only once Stage 2 has actually fired.

    Returns (domain_or_None, confidence). Raises on ANY failure (network,
    auth, timeout, missing/malformed tool call, schema violation) -- the
    caller (_stage2_fallback) is solely responsible for catching and
    failing REFUSAL; this function never itself returns a fallback value.
    """
    if client is None:
        # Lazy import + construction: must not happen until Stage 2 has
        # actually fired, so Stage 1's pure keyword path never touches
        # OpenAI (import-time key validation would otherwise break
        # offline/keyless runs of the deterministic router).
        from openai import OpenAI

        client = OpenAI()

    response = client.chat.completions.create(
        model=_STAGE2_MODEL,
        messages=[
            {"role": "system", "content": _STAGE2_SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        tools=[_STAGE2_TOOL_SCHEMA],
        tool_choice={"type": "function", "function": {"name": "classify_domain"}},
        temperature=0,
        timeout=_STAGE2_TIMEOUT_SECONDS,
    )

    tool_calls = response.choices[0].message.tool_calls
    if not tool_calls:
        raise ValueError("calc_router._stage2_classify: no tool_calls in response")

    args = json.loads(tool_calls[0].function.arguments)
    domain = args.get("domain")
    confidence = args.get("confidence")
    if domain not in _STAGE2_VALID_DOMAINS or confidence not in _STAGE2_VALID_CONFIDENCE:
        raise ValueError(
            f"calc_router._stage2_classify: schema validation failed -- "
            f"domain={domain!r} confidence={confidence!r}"
        )
    return (None if domain == "none" else domain), confidence


def _log_stage2_invocation(
    question: str,
    stage1_best_score: float,
    stage1_margin: float,
    stage2_domain: str | None,
    stage2_confidence: str,
    outcome: str,
) -> None:
    """Append one JSON line to diagnostics/calc_router_stage2.log.

    Best-effort: a logging failure (e.g. read-only filesystem) must never
    affect routing, so OSError is swallowed here -- this is deliberately a
    separate try/except from _stage2_classify's own, which exists for the
    OpenAI call itself, not for logging it.
    """
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "stage1_best_score": stage1_best_score,
        "stage1_margin": stage1_margin,
        "stage2_domain": stage2_domain,
        "stage2_confidence": stage2_confidence,
        "outcome": outcome,
    }
    try:
        _STAGE2_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_STAGE2_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        pass


def _route_to_domain(
    domain: str,
    confidence: float,
    has_partner_data: bool,
    chart_data: dict | None,
    route: Literal["stage1", "stage2", "fastpath"],
) -> RouteResult:
    """Build the final RouteResult for a resolved domain.

    Shared by Stage 1 (keyword score cleared floor + margin), Stage 2
    (LLM high-confidence fallback), AND the sade_sati deterministic
    fast-path (Session 50/P7.2c) -- the has_partner_data hard guard,
    career's fixed T2 demotion, sade_sati's fixed T1/no-demotion, and
    dasha's ALWAYS-T2 rule (Session 49/P7.0c) apply identically regardless
    of which of the three resolved the domain. `route` has no default:
    since all three callers can reach any of this function's domain
    branches (Session 72 carry-forward tracing), the correct provenance
    value cannot be inferred from the domain alone -- each caller must
    state which mechanism it is.
    """
    if domain == "marriage_compatibility":
        if not has_partner_data:
            # HARD GUARD -- not a soft fallback, no attempt to route elsewhere.
            return RouteResult(
                domain=None,
                tier=AnswerTier.REFUSAL,
                confidence=0.0,
                demotion_reason="marriage_compatibility requires partner birth data",
                requires_partner=True,
                route=route,
            )
        return RouteResult(
            domain="marriage_compatibility",
            tier=AnswerTier.TIER_1_EXACT,
            confidence=confidence,
            demotion_reason=None,
            requires_partner=True,
            route=route,
        )

    if domain == "career_strength":
        return RouteResult(
            domain="career_strength",
            tier=AnswerTier.TIER_2_RANGE,
            confidence=confidence,
            demotion_reason=_CAREER_DEMOTION_REASON,
            requires_partner=False,
            route=route,
        )

    if domain == "sade_sati":
        # T1, no demotion, no partner -- distinct from current_dasha's
        # ALWAYS-T2 rule below: sade_sati's payload (chart_profile.py
        # P7.2a) carries NO mahadasha/antardasha boundary dates, so it
        # never inherits the +/-37-day drift that forces current_dasha's
        # demotion. Tier is a property of the payload's actual claims
        # (Session 49/P7.0c principle), and this payload makes none that
        # carry that drift.
        return RouteResult(
            domain="sade_sati",
            tier=AnswerTier.TIER_1_EXACT,
            confidence=confidence,
            demotion_reason=None,
            requires_partner=False,
            route=route,
        )

    if domain == "av_transit":
        # TIER_2_RANGE, demotion_reason=None -- DEMOTION LOCK (Session 55,
        # orchestrator.py's _VALID_DOMAINS comment): av_transit's own
        # ±37-day-plus-day-level-resolution demotion string is owned
        # entirely by result_formatter.py's _format_av_transit() branch
        # (payload-property principle, same as current_dasha/sade_sati
        # above). Setting a second reason here would make
        # orchestrator._merge_router_demotion() concatenate it onto the
        # formatter's with " | ", duplicating the same ±37-day disclosure
        # under two different wordings -- never do that.
        return RouteResult(
            domain="av_transit",
            tier=AnswerTier.TIER_2_RANGE,
            confidence=confidence,
            demotion_reason=None,
            requires_partner=False,
            route=route,
        )

    if domain == "arudha_lagna":
        # T1, no demotion, no partner -- mirrors sade_sati's pattern above:
        # chart_profile.py's build_arudha_lagna_profile() payload docstring
        # states tier="TIER_1_EXACT" (single deterministic Arudha sign/lord,
        # no uncertainty envelope). NOTE (Session 58): this branch exists so
        # Stage 1's fallthrough never mislabels an arudha_lagna keyword hit
        # as current_dasha (the previous unconditional final block below
        # returns a hardcoded "current_dasha" literal for ANY unhandled
        # domain) -- without this branch, a keyword-scoring win here would
        # silently produce a wrong-domain answer instead of failing safely.
        # orchestrator.py's own _VALID_DOMAINS does NOT yet admit
        # "arudha_lagna" (build_domain_profile()/formatter integration is a
        # separate, later prompt per chart_profile.py's
        # build_arudha_lagna_profile() docstring) -- until that sync lands,
        # a question routed here will fail closed with orchestrator's
        # defensive ValueError, same "_VALID_DOMAINS sync discipline"
        # precedent as av_transit's Session 55 router-then-orchestrator
        # staged rollout.
        return RouteResult(
            domain="arudha_lagna",
            tier=AnswerTier.TIER_1_EXACT,
            confidence=confidence,
            demotion_reason=None,
            requires_partner=False,
            route=route,
        )

    if domain == "upapada_lagna":
        # T1, no demotion, no partner -- mirrors arudha_lagna's branch
        # exactly (Session 65): chart_profile.py's build_upapada_profile()
        # payload docstring states tier="TIER_1_EXACT" (single
        # deterministic UL sign/lord, no uncertainty envelope), and it's a
        # SINGLE-CHART significator, same as arudha_lagna, so
        # requires_partner=False -- never conflate with
        # marriage_compatibility's has_partner_data hard guard above. This
        # branch exists so Stage 1's fallthrough never mislabels an
        # upapada_lagna keyword hit as current_dasha (the unconditional
        # final block below returns a hardcoded "current_dasha" literal
        # for ANY unhandled domain) -- same "silent mis-route" trap
        # arudha_lagna's own branch comment documents above.
        # orchestrator.py's own _VALID_DOMAINS does NOT yet admit
        # "upapada_lagna" -- until that sync lands, a question routed here
        # will fail closed with orchestrator's defensive ValueError, same
        # staged-rollout precedent as arudha_lagna's Session 58 landing.
        return RouteResult(
            domain="upapada_lagna",
            tier=AnswerTier.TIER_1_EXACT,
            confidence=confidence,
            demotion_reason=None,
            requires_partner=False,
            route=route,
        )

    if domain == "muhurta_window":
        # TIER_3_MUHURTA, no demotion, no partner (Session 64, P7 Muhurta
        # wiring step 4 of 6). chart_profile.py's build_muhurta_profile()
        # payload docstring states tier="TIER_3_MUHURTA" -- the pipeline's
        # first and only T3 domain: per-window Chandrabala/Tarabala/
        # Panchaka composite scoring over a fixed 7-day scan carries
        # genuinely dated per-window claims, unlike every T1/T2 domain
        # above, which is why this does NOT fit the "tier = payload
        # property" T1/T2 framing those domains share (see chart_profile.py's
        # own module docstring). requires_partner=False -- single-chart
        # natal-plus-transit calculation, same as every domain here except
        # marriage_compatibility. demotion_reason=None -- same DEMOTION
        # LOCK posture as av_transit's branch above: if this domain ever
        # needs an uncertainty-disclosure string, it belongs to
        # result_formatter.py's _format_muhurta_window(), not this router,
        # to avoid orchestrator._merge_router_demotion()'s " | "
        # double-disclosure trap.
        # orchestrator.py's own _VALID_DOMAINS does NOT yet admit
        # "muhurta_window" -- until that sync lands (step 5), a question
        # routed here will fail closed with orchestrator's defensive
        # ValueError, same staged-rollout precedent as every prior
        # new-domain landing (arudha_lagna Session 58, upapada_lagna
        # Session 65).
        return RouteResult(
            domain="muhurta_window",
            tier=AnswerTier.TIER_3_MUHURTA,
            confidence=confidence,
            demotion_reason=None,
            requires_partner=False,
            route=route,
        )

    if domain == "current_dasha":
        # current_dasha -- ALWAYS TIER_2_RANGE in V1 (design-chat reversal of
        # the Session 45 conditional-demotion behavior, Session 49/P7.0c;
        # exposed by golden-harness rows sulabh_dasha_q11/q12/q13/r4_exact_date,
        # all mid-period and all wrongly resolving TIER_1_EXACT under the old
        # rule). Rationale: the payload always surfaces Mahadasha/Antardasha
        # boundary DATES (chart_profile.py's current_dasha payload), and those
        # dates carry the documented +/-37-day drift vs AstroSage regardless of
        # how far evaluated_at sits from a boundary -- tier is a property of
        # the answer's claims (which always include dated boundaries), not of
        # the evaluation moment. _near_dasha_boundary()/_DASHA_BOUNDARY_WINDOW_DAYS
        # are kept, repurposed below to choose WHICH demotion_reason applies
        # (dates-only vs identity-also-uncertain), not whether to demote.
        if chart_data is None or _near_dasha_boundary(chart_data):
            demotion_reason = _DASHA_DEMOTION_REASON_NEAR_BOUNDARY
        else:
            demotion_reason = _DASHA_DEMOTION_REASON
        return RouteResult(
            domain="current_dasha",
            tier=AnswerTier.TIER_2_RANGE,
            confidence=confidence,
            demotion_reason=demotion_reason,
            requires_partner=False,
            route=route,
        )

    # DEFENSIVE FAIL-CLOSED (Session 58 carry-forward, closed here Session 64
    # P7 Muhurta wiring step 4 of 6, ride-along 2 -- CLAUDE.md-flagged debt:
    # this function previously fell through to a hardcoded "current_dasha"
    # RouteResult for ANY domain string not explicitly branched above,
    # instead of failing loudly. arudha_lagna's own branch comment (above)
    # already documented dodging this trap by adding its own explicit
    # branch rather than relying on the old fallthrough; this raise closes
    # the underlying trap itself for any FUTURE domain added to
    # _DOMAIN_KEYWORDS/_STAGE2_VALID_DOMAINS without a matching branch here
    # -- a caller error (or a forgotten branch) now fails loudly with the
    # offending domain name, never silently mis-routes to current_dasha.
    raise ValueError(f"calc_router._route_to_domain: unknown domain {domain!r}")


def _stage2_fallback(
    question: str,
    best_score: float,
    margin: float,
    has_partner_data: bool,
    chart_data: dict | None,
    client: object | None,
) -> RouteResult:
    """Stage 2 entry point.

    Called ONLY from route_question()'s confidence-floor/margin-tie
    REFUSAL branch -- never from the unbuilt-module-keyword or
    out-of-scope-keyword REFUSAL paths, which return earlier in
    route_question() and never reach here.

    Fails CLOSED: any exception from _stage2_classify (network, auth,
    timeout, malformed/unparseable output, schema violation) is caught
    here, logged, and converted to the same REFUSAL Stage 1 alone would
    have produced -- never propagated to the caller, never falls through
    to a guessed domain.
    """
    try:
        stage2_domain, stage2_confidence = _stage2_classify(question, client=client)
    except Exception as exc:
        _log_stage2_invocation(
            question,
            best_score,
            margin,
            None,
            f"error:{type(exc).__name__}",
            "REFUSAL (stage2_exception: "
            f"{type(exc).__name__}: {exc})",
        )
        return RouteResult(
            domain=None,
            tier=AnswerTier.REFUSAL,
            confidence=0.0,
            demotion_reason="question not classifiable with confidence",
            requires_partner=False,
            route="stage2",
        )

    if stage2_domain is not None and stage2_confidence == "high":
        result = _route_to_domain(
            stage2_domain,
            _STAGE2_CONFIDENCE_MAP["high"],
            has_partner_data,
            chart_data,
            route="stage2",
        )
        outcome = (
            f"ROUTED:{result.domain}"
            if result.domain is not None
            else f"REFUSAL:{result.demotion_reason}"
        )
        _log_stage2_invocation(
            question, best_score, margin, stage2_domain, stage2_confidence, outcome
        )
        return result

    reason = (
        "stage2 domain=none"
        if stage2_domain is None
        else f"stage2 confidence={stage2_confidence!r} (not high)"
    )
    _log_stage2_invocation(
        question,
        best_score,
        margin,
        stage2_domain,
        stage2_confidence,
        f"REFUSAL ({reason})",
    )
    return RouteResult(
        domain=None,
        tier=AnswerTier.REFUSAL,
        confidence=0.0,
        demotion_reason="question not classifiable with confidence",
        requires_partner=False,
        route="stage2",
    )


def route_question(
    question: str,
    has_partner_data: bool = False,
    *,
    chart_data: dict | None = None,
    _stage2_client: object | None = None,
) -> RouteResult:
    """Classify question -> domain + tier. No side effects (beyond an
    append-only diagnostics log line if Stage 2 fires).

    chart_data is optional and only consulted for the current_dasha
    boundary-proximity warning (see module docstring for why route_question
    cannot derive it itself). Callers with no chart_data yet still get a
    correct domain/tier classification, just without the boundary warning.

    `_stage2_client` is a test-only injection seam for Stage 2's OpenAI
    client (default None -> a real client is constructed lazily, only if
    Stage 2 actually fires). Not part of this function's stable public
    contract; production callers (orchestrator.py) never pass it.
    """
    question_lower = question.lower()

    # REFUSAL triggers checked BEFORE domain classification.
    # Word-boundary match (not plain substring) -- golden-harness row
    # sulabh_dasha_r4_exact_date exposed "transition"/"transitional"
    # false-positiving on keyword "transit" under substring containment.
    # `s?` permits the simple plural (e.g. "transits", "vargas") without
    # opening the door to unrelated words that merely start with the
    # keyword (e.g. "characteristics" no longer false-positives on "chara").
    for keyword, module_name in _UNBUILT_MODULE_KEYWORDS.items():
        if re.search(rf"\b{re.escape(keyword)}s?\b", question_lower):
            return RouteResult(
                domain=None,
                tier=AnswerTier.REFUSAL,
                confidence=0.0,
                demotion_reason=(
                    f"question references {module_name}, which is not in "
                    f"the routable whitelist (marriage_compatibility, "
                    f"career_strength, current_dasha, sade_sati)"
                ),
                requires_partner=False,
                route="pre_classification",
            )

    for keyword in _OUT_OF_SCOPE_KEYWORDS:
        if keyword in question_lower:
            return RouteResult(
                domain=None,
                tier=AnswerTier.REFUSAL,
                confidence=0.0,
                demotion_reason=(
                    "question is outside Vedic astrology scope "
                    f"(matched out-of-scope term: {keyword!r})"
                ),
                requires_partner=False,
                route="pre_classification",
            )

    # sade_sati deterministic fast-path (Session 50/P7.2c) -- checked AFTER
    # the unbuilt-module/out-of-scope REFUSAL checks above, BEFORE domain
    # scoring below. Same word-boundary regex as _UNBUILT_MODULE_KEYWORDS.
    # Deliberately bypasses _DOMAIN_KEYWORDS/_score_domain's floor/margin
    # scoring entirely: the flagship differentiator (golden q14) must
    # never depend on Stage 2/GPT-4o-mini being available or correct.
    for keyword, domain in _BUILT_MODULE_FASTPATH.items():
        if re.search(rf"\b{re.escape(keyword)}s?\b", question_lower):
            return _route_to_domain(
                domain, 1.0, has_partner_data, chart_data, route="fastpath"
            )

    # Domain classification.
    question_tokens = _normalize_tokens(question)
    scores = {
        domain: _score_domain(question_tokens, keywords)
        for domain, keywords in _DOMAIN_KEYWORDS.items()
    }
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    best_domain, best_score = ranked[0]
    second_score = ranked[1][1]

    if best_score < _CONFIDENCE_FLOOR or (best_score - second_score) < _CONFIDENCE_MARGIN:
        return _stage2_fallback(
            question,
            best_score,
            best_score - second_score,
            has_partner_data,
            chart_data,
            _stage2_client,
        )

    return _route_to_domain(
        best_domain, best_score, has_partner_data, chart_data, route="stage1"
    )
