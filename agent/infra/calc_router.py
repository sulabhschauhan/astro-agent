"""Deterministic 3-domain question router for the thin-slice answer pipeline.

Maps a user question string to a DomainChartProfile-compatible domain name
plus an AnswerTier, using Layer A keyword pattern matching ONLY. No GPT/LLM
classification anywhere in this file -- that is Layer B fallback, explicitly
out of scope for V1's 3-domain whitelist (Phase 10 / V2, not S44.3).

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

import re
from dataclasses import dataclass
from datetime import datetime, timezone

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

_DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "marriage_compatibility": _MARRIAGE_KEYWORDS,
    "career_strength": _CAREER_KEYWORDS,
    "current_dasha": _DASHA_KEYWORDS,
}

# Calculation modules referenced in a question but NOT in the 3-domain
# whitelist -> immediate REFUSAL naming the unbuilt module, checked BEFORE
# domain classification. "muhurta" gets its own message: the scorer exists
# (transits/chandrabala.py, tarabala.py, panchaka.py) but is not wired to
# Q&A in V1 -- distinct from the other keywords, which name modules that
# are either unbuilt or simply out of this pipeline's 3-domain scope.
_UNBUILT_MODULE_KEYWORDS: dict[str, str] = {
    "yoga": "yoga detection",
    "transit": "transit engine (gochara/sade sati)",
    "gochara": "gochara transit engine",
    "sade sati": "Sade Sati transit engine",
    "ashtakavarga": "Ashtakavarga (BAV/SAV)",
    "navamsa": "D9 (Navamsa) divisional chart",
    "divisional": "divisional charts (vargas)",
    "d10": "D10 divisional chart",
    "d9": "D9 (Navamsa) divisional chart",
    "varga": "divisional charts (vargas)",
    "jaimini": "Jaimini karakas/arudha/padas",
    "chara": "Chara dasha",
    "yogini": "Yogini dasha",
    "ashtottari": "Ashtottari dasha",
    "varshaphal": "Varshaphal annual chart",
    "muhurta": "Muhurta scorer (module exists but is not wired to Q&A in V1)",
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

_CAREER_DEMOTION_REASON = (
    "Drik Bala stubbed at 0.0 (±20 Virupa envelope); planet rank "
    "within envelope should be treated as approximate"
)
_DASHA_DEMOTION_REASON = (
    "Antardasha boundaries carry ±37-day drift vs AstroSage; current "
    "lord is reliable except near period boundaries"
)


@dataclass(frozen=True)
class RouteResult:
    """Output of route_question() -- classification only, no side effects."""

    domain: str | None          # None on REFUSAL
    tier: AnswerTier            # always set
    confidence: float           # 0.0 on REFUSAL
    demotion_reason: str | None # set on REFUSAL or T1->T2 demotion
    requires_partner: bool      # True only for marriage domain


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


def route_question(
    question: str,
    has_partner_data: bool = False,
    *,
    chart_data: dict | None = None,
) -> RouteResult:
    """Classify question -> domain + tier. No side effects.

    chart_data is optional and only consulted for the current_dasha
    boundary-proximity warning (see module docstring for why route_question
    cannot derive it itself). Callers with no chart_data yet still get a
    correct domain/tier classification, just without the boundary warning.
    """
    question_lower = question.lower()

    # REFUSAL triggers checked BEFORE domain classification.
    for keyword, module_name in _UNBUILT_MODULE_KEYWORDS.items():
        if keyword in question_lower:
            return RouteResult(
                domain=None,
                tier=AnswerTier.REFUSAL,
                confidence=0.0,
                demotion_reason=(
                    f"question references {module_name}, which is not in "
                    f"the 3-domain whitelist (marriage_compatibility, "
                    f"career_strength, current_dasha)"
                ),
                requires_partner=False,
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
        return RouteResult(
            domain=None,
            tier=AnswerTier.REFUSAL,
            confidence=0.0,
            demotion_reason="question not classifiable with confidence",
            requires_partner=False,
        )

    if best_domain == "marriage_compatibility":
        if not has_partner_data:
            # HARD GUARD -- not a soft fallback, no attempt to route elsewhere.
            return RouteResult(
                domain=None,
                tier=AnswerTier.REFUSAL,
                confidence=0.0,
                demotion_reason="marriage_compatibility requires partner birth data",
                requires_partner=True,
            )
        return RouteResult(
            domain="marriage_compatibility",
            tier=AnswerTier.TIER_1_EXACT,
            confidence=best_score,
            demotion_reason=None,
            requires_partner=True,
        )

    if best_domain == "career_strength":
        return RouteResult(
            domain="career_strength",
            tier=AnswerTier.TIER_2_RANGE,
            confidence=best_score,
            demotion_reason=_CAREER_DEMOTION_REASON,
            requires_partner=False,
        )

    # current_dasha
    demotion_reason = _DASHA_DEMOTION_REASON
    if chart_data is not None and _near_dasha_boundary(chart_data):
        demotion_reason += (
            " WARNING: evaluation date is within 37-day boundary window "
            "-- current AD lord uncertain."
        )
    return RouteResult(
        domain="current_dasha",
        tier=AnswerTier.TIER_2_RANGE,
        confidence=best_score,
        demotion_reason=demotion_reason,
        requires_partner=False,
    )
