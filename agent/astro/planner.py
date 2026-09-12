"""

================================================================
PATH B / LAB TRACK -- NOT WIRED TO THE PRODUCT (S128 lock).

This module has NO non-test caller. The live answer path is
agent/infra/orchestrator.answer_question, imported by
frontend/app.py:31. Changing this file ships NOTHING to users.
Read docs/ANSWER_PATHS.md before editing or proposing work here.
================================================================

Astro Agent -- STAGE 1: THE PLANNER (a.k.a. the router).

The missing keystone stage. Reads the user's question and says what the
system needs: which of the 16 closed domains, which houses (reasoned,
including derived / bhavat-bhavam), whose chart, and what time scope.

DOCTRINE THIS IMPLEMENTS (S124 locks, ratified in design chat):
  - Contextual, not tabular. No domain->house table, no substring
    out-of-scope guard, no hardcoded "child questions" branch. One LLM
    call reasons about the question; Python only checks the SHAPE of what
    comes back.
  - STRUCTURAL VALIDATION ONLY. house in 1..12, domain in the closed 16,
    whose_chart in the allowed set, time_scope in the allowed set. We
    never check whether the doctrine is *right* -- that is the LLM's job
    and the Interpreter's evidence, not a Python table.
  - Other people's charts resolve onto the USER's own chart via
    bhavat-bhavam derived houses. The system never needs a second birth
    record. `whose_chart` is recorded; `houses` already carries the
    derived result.
  - WIDEN WHEN UNSURE, NEVER NARROW. A planner that is not sure emits
    more domains, not fewer.
  - FAILS LOUD, NOT SILENT. Malformed output -> one retry -> deterministic
    fallback stamped `planner_fallback=True`. Every decision is logged.

WHAT THIS STAGE DOES NOT DO:
  - It does not compute a single chart fact (S124 lock: the LLM never
    computes chart facts).
  - It does not read corpus text. It selects units by tag only.
  - `houses` is RECORDED BUT NOT YET CONSUMED by payload_builder (whose
    relation filter is driven by the chart's own lord->house map, not by
    the planner). Recorded now so the Interpreter and the future silence
    gate can use it; wiring it into selection is a separate decision.

Python 3.11.
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field, asdict
from typing import Callable, Iterable, Optional

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOMAIN_TAGS_PATH = os.path.join(REPO_ROOT, "data", "domain_tags_bphs.json")
CHAPTER_INDEX_PATH = os.path.join(REPO_ROOT, "data", "chapter_index_bphs.json")
DECISION_LOG_PATH = os.path.join(REPO_ROOT, "diagnostics", "planner_decisions.jsonl")

PLANNER_VERSION = "planner-1.0"

# --- closed vocabularies (LOCKED, S124) --------------------------------------
DOMAINS: tuple[str, ...] = (
    "career", "marriage", "wealth", "children", "health", "education",
    "longevity", "travel", "property", "parents", "siblings",
    "spirituality", "enemies_conflict", "timing_dasha",
    "technique_method", "planetary_nature",
)
WHOSE_CHART = ("self", "other")
TIME_SCOPES = ("none", "past", "present", "future", "specific_period")

# THRESHOLD: payload token budget.
#   JUSTIFICATION -- the whole two-book corpus is ~242,571 approx-tokens
#   (measured, S124). `career` alone selects 51,454 (21.2%). A 3-domain
#   question can therefore exceed 100k, past the point where an
#   interpreter call is affordable or attentive.
#   SCOPE GUARD -- advisory only. Going over budget NEVER drops a unit
#   (that would be narrowing, which doctrine forbids); it sets
#   `over_budget=True` and reports the per-unit contribution so a human
#   decides. Nothing downstream reads this number to filter.
#   TUNING NOTE -- re-set from observed interpreter cost/quality once the
#   POC has produced real runs, not from this guess.
DEFAULT_TOKEN_BUDGET = 60_000

# THRESHOLD: hard context ceiling. UNLIKE the budget above, this one BITES.
#   JUSTIFICATION -- gpt-4o's context window is 128,000 real tokens.
#   Reserve 4,000 for the answer and overhead => 124,000 usable input.
#   `approx_tokens` in these artifacts is a WORD COUNT and undercounts the
#   real tokeniser: measured ratio real/approx = 1.33-1.42 across the four
#   POC questions (chars/4 estimate; tiktoken was unavailable in the
#   measuring environment and was NOT silently substituted). Using the
#   worst observed ratio 1.45 for headroom: 124,000 / 1.45 = 85,517,
#   rounded down to 85,000 approx-tokens.
#   SCOPE GUARD -- applies ONLY to the interpreter call. Over the ceiling
#   the pipeline REFUSES and says why; it never truncates the payload,
#   because silently dropping doctrine is exactly the confident-wrong
#   failure this architecture exists to prevent.
#   TUNING NOTE -- re-derive both the 124,000 and the 1.45 from a real
#   tiktoken count on a machine that has the encoding cached, and again
#   whenever the interpreter model changes.
# S126: interpreter locked to GPT-5 (validated 2026-09-10, 0 ghost citations, honest
# refusal, real recall at 105k tokens). Window 128k->400k; ceiling raised to
# (400k real - ~15k output/reasoning reserve) / 1.70 approx-ratio = ~225k approx.
HARD_CONTEXT_CEILING = 225_000
INTERPRETER_CONTEXT_WINDOW = 400_000

# RECALIBRATED S125 against REAL OpenAI `prompt_tokens`, superseding the
# chars/4 estimate that set the original 1.45.
#   ARM A: 48,589 approx -> 80,882 prompt_tokens = 1.664
#   ARM B: 12,864 approx -> 20,736 prompt_tokens = 1.612
# chars/4 itself undercounted the real tokeniser by ~17% on this corpus
# (67,513 estimated vs 80,882 actual), because Devanagari-stripped OCR
# text fragments badly. 1.70 is the worst observed plus headroom.
#   TUNING NOTE: re-derive from `prompt_tokens` on any corpus change; never
#   from chars/4 or from `approx_tokens` again.
APPROX_TO_REAL_RATIO = 1.70

# THRESHOLD: tokens-per-minute cap. ADVISORY, not a refusal.
#   JUSTIFICATION -- measured 2026-09-05: a 68,342-token gpt-4o request was
#   rejected with HTTP 429, "Limit 30000". At this account tier the TPM cap
#   binds long before the context window does, so a payload can be legal
#   for the model and still unservable.
#   SCOPE GUARD -- ADVISORY ONLY. It is account- and model-specific (mini's
#   cap is far higher) and a tier upgrade changes it without a code change,
#   so it warns and never refuses. The context ceiling above is the only
#   hard gate.
#   TUNING NOTE -- re-read from the account's rate-limit dashboard, or from
#   the `x-ratelimit-limit-tokens` response header, whenever a 429 appears.
INTERPRETER_TPM_LIMIT = 30_000

_MAX_LLM_ATTEMPTS = 2  # first call + exactly one retry, then fallback.


class PlannerError(Exception):
    """Planner could not produce a usable plan by any path."""


# ---------------------------------------------------------------------------
# The plan object
# ---------------------------------------------------------------------------
@dataclass
class Plan:
    question: str
    domains: list[str]
    houses: list[int]
    whose_chart: str
    time_scope: str
    in_scope: bool
    reasoning: str
    # provenance -- never inferred downstream, always carried
    source: str = "llm"              # "llm" | "llm_retry" | "fallback"
    planner_fallback: bool = False
    validation_errors: list[str] = field(default_factory=list)
    raw_responses: list[str] = field(default_factory=list)
    planner_version: str = PLANNER_VERSION

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class UnitSelection:
    unit_ids: list[str]
    approx_tokens: int
    over_budget: bool
    token_budget: int
    per_domain_units: dict[str, list[str]]
    per_unit_tokens: dict[str, int]
    corpus_tokens: int

    @property
    def corpus_fraction(self) -> float:
        return (self.approx_tokens / self.corpus_tokens) if self.corpus_tokens else 0.0


# ---------------------------------------------------------------------------
# The one LLM call
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are the PLANNER for a Vedic astrology answering system grounded ONLY in Brihat Parashara Hora Shastra volumes 1 and 2.

Your ONLY job is to read the user's question and state what the system must fetch to answer it. You do NOT answer the question. You do NOT state any astrological conclusion. You do NOT compute or guess any chart fact.

Reason about the question the way a Parashari astrologer would when deciding what to look at:

1. DOMAINS -- which subject areas of the classical text bear on this question. Choose from this closed list, and ONLY this list:
career, marriage, wealth, children, health, education, longevity, travel, property, parents, siblings, spirituality, enemies_conflict, timing_dasha, technique_method, planetary_nature
If a question could plausibly touch several, LIST THEM ALL. Widening is correct; narrowing is a failure. A question that asks "when" always includes timing_dasha.

2. HOUSES -- which houses of the NATIVE'S OWN chart must be examined, as integers 1-12. Reason them out; do not use a fixed subject-to-house table. When the question is about another person, resolve it onto the native's own chart using bhavat-bhavam (house-from-house): e.g. a child's career is the 10th from the 5th, which is the 2nd house of the native's chart. Include the base house as well as the derived one when both are relevant.
WIDEN HERE TOO. Naming only the single most obvious house is a failure, not precision. A classical reading of any life event consults the SUPPORTING houses alongside the primary one -- for marriage that is the 7th but also the 2nd (kutumba/family), the 11th (fulfilment of desire) and often the 8th (mangalya); for career the 10th but also the 1st, 2nd, 6th and 11th. List every house a Parashari would actually look at, not just the textbook headline.

3. WHOSE_CHART -- "self" if the question is about the native, "other" if it is about another person (child, spouse, parent, sibling, colleague). Either way the houses you give are ALWAYS houses of the native's own chart -- the system has only one chart.

4. TIME_SCOPE -- one of: "none" (no time element), "past", "present", "future", "specific_period" (a named year, dasha, or window).

5. IN_SCOPE -- true if Brihat Parashara Hora Shastra volumes 1-2 could address this question at all. false ONLY if the question is genuinely outside classical natal astrology as those books treat it -- for example a request for medical diagnosis or treatment, legal advice, or a factual question with no chart component. Judge the QUESTION'S INTENT, never a word in it: a question naming the sign Cancer, or the 6th house, or a disease-related yoga, is IN SCOPE as astrology. Only a request for actual medical judgement is out of scope.

6. REASONING -- two or three sentences saying why, naming the house derivations explicitly.

Output STRICT JSON only. No markdown fences, no text before or after, exactly this shape:
{"domains": ["..."], "houses": [1], "whose_chart": "self", "time_scope": "none", "in_scope": true, "reasoning": "..."}"""


def _default_llm(prompt: str, *, model: str = "gpt-4o", temperature: float = 0.0) -> str:
    """Live OpenAI call. Isolated so tests inject a stub instead.

    Kept deliberately thin: this stage owns routing logic, not transport.
    """
    try:
        from openai import OpenAI
    except ImportError as e:  # pragma: no cover - environment problem, not logic
        raise PlannerError(
            "openai package not installed; pass an llm= callable instead"
        ) from e
    try:
        client = OpenAI()
        resp = client.chat.completions.create(
            model=model,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content or ""
    except Exception as e:
        raise PlannerError(f"LLM call failed: {type(e).__name__}: {e}") from e


# ---------------------------------------------------------------------------
# Structural validation -- SHAPE ONLY, never doctrine
# ---------------------------------------------------------------------------
_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)


def _strip_fences(raw: str) -> str:
    m = _FENCE_RE.match(raw or "")
    return m.group(1) if m else (raw or "")


def validate_plan_object(obj: object) -> tuple[Optional[dict], list[str]]:
    """Check SHAPE ONLY. Returns (normalised_dict | None, errors).

    Deliberately does NOT check whether the houses are doctrinally right
    for the domains. That is not a schema question and hardcoding it here
    would reintroduce the table this architecture removed.
    """
    errors: list[str] = []
    if not isinstance(obj, dict):
        return None, [f"top level is {type(obj).__name__}, expected object"]

    # domains
    domains = obj.get("domains")
    if not isinstance(domains, list) or not domains:
        errors.append("domains must be a non-empty list")
        domains = []
    else:
        bad = [d for d in domains if not isinstance(d, str) or d not in DOMAINS]
        if bad:
            errors.append(f"domains outside closed vocabulary: {bad}")
        # de-dupe, preserve canonical corpus order for stable payloads
        domains = [d for d in DOMAINS if d in set(domains)]

    # houses
    houses = obj.get("houses")
    if not isinstance(houses, list):
        errors.append("houses must be a list")
        houses = []
    else:
        bad_h = [h for h in houses if not isinstance(h, int) or isinstance(h, bool)
                 or not (1 <= h <= 12)]
        if bad_h:
            errors.append(f"houses outside 1-12 or non-integer: {bad_h}")
        houses = sorted({h for h in houses if isinstance(h, int)
                         and not isinstance(h, bool) and 1 <= h <= 12})

    whose = obj.get("whose_chart")
    if whose not in WHOSE_CHART:
        errors.append(f"whose_chart={whose!r} not in {WHOSE_CHART}")

    scope = obj.get("time_scope")
    if scope not in TIME_SCOPES:
        errors.append(f"time_scope={scope!r} not in {TIME_SCOPES}")

    in_scope = obj.get("in_scope")
    if not isinstance(in_scope, bool):
        errors.append(f"in_scope={in_scope!r} must be a boolean")

    reasoning = obj.get("reasoning")
    if not isinstance(reasoning, str) or not reasoning.strip():
        errors.append("reasoning must be a non-empty string")

    if errors:
        return None, errors

    return {
        "domains": domains,
        "houses": houses,
        "whose_chart": whose,
        "time_scope": scope,
        "in_scope": in_scope,
        "reasoning": reasoning.strip(),
    }, []


def parse_llm_plan(raw: str) -> tuple[Optional[dict], list[str]]:
    try:
        obj = json.loads(_strip_fences(raw))
    except (json.JSONDecodeError, TypeError) as e:
        return None, [f"response is not valid JSON: {e}"]
    return validate_plan_object(obj)


# ---------------------------------------------------------------------------
# The fallback -- deterministic, LOUD, never silent
# ---------------------------------------------------------------------------
# Only used when the LLM path has failed twice. Deliberately dumb and
# deliberately WIDE: its job is to keep the system answering something
# honest, not to be a second router. Every use is stamped and logged.
#
# NOTE (design chat, S124 follow-on): `agent/infra/calc_router.py` was
# proposed as this fallback. It is NOT used, and that is deliberate --
# calc_router routes to CALCULATION domains (current_dasha,
# marriage_compatibility, muhurta_window...), a different output type in a
# different stage. Mapping it onto the 16 TEXT domains would be a fresh
# hardcoded table, exactly what this architecture removed. calc_router is
# untouched and continues to serve the Calculator stage.
_FALLBACK_GLOSS: dict[str, tuple[str, ...]] = {
    "career": ("career", "job", "work", "profession", "business", "promotion", "office"),
    "marriage": ("marriage", "marry", "spouse", "wife", "husband", "partner", "wedding"),
    "wealth": ("wealth", "money", "rich", "finance", "income", "gain", "prosperity"),
    "children": ("child", "children", "son", "daughter", "progeny", "kids"),
    "health": ("health", "illness", "disease", "sick", "body", "vitality"),
    "education": ("education", "study", "studies", "exam", "degree", "learning", "school"),
    "longevity": ("longevity", "lifespan", "death", "long life", "ayush"),
    "travel": ("travel", "abroad", "foreign", "journey", "relocate", "migration"),
    "property": ("property", "house", "home", "land", "vehicle", "real estate"),
    "parents": ("father", "mother", "parent", "parents"),
    "siblings": ("brother", "sister", "sibling", "siblings"),
    "spirituality": ("spiritual", "moksha", "guru", "religion", "dharma", "temple"),
    "enemies_conflict": ("enemy", "enemies", "litigation", "court", "dispute", "conflict"),
    "timing_dasha": ("when", "dasha", "period", "timing", "year", "antardasha", "time"),
    "technique_method": ("how", "calculate", "method", "varga", "shadbala", "ashtakavarga"),
    "planetary_nature": ("planet", "graha", "saturn", "jupiter", "mars", "venus",
                         "mercury", "sun", "moon", "rahu", "ketu"),
}


def fallback_plan(question: str) -> tuple[dict, list[str]]:
    """Deterministic, widening fallback. Returns (plan_fields, notes)."""
    q = (question or "").lower()
    hits = [d for d, words in _FALLBACK_GLOSS.items()
            if any(w in q for w in words)]
    notes = [f"fallback matched domains: {hits or 'NONE'}"]
    if not hits:
        # Honest silence beats confident-wrong: nothing matched, so we do
        # NOT invent a domain and we do NOT dump the whole corpus.
        return {
            "domains": [],
            "houses": [],
            "whose_chart": "self",
            "time_scope": "none",
            "in_scope": False,
            "reasoning": ("Planner LLM failed and the deterministic fallback "
                          "matched no domain. Refusing rather than guessing."),
        }, notes + ["fallback produced NO domains -> refusal"]
    return {
        "domains": [d for d in DOMAINS if d in set(hits)],
        "houses": [],  # never guessed by the fallback -- houses need reasoning
        "whose_chart": "self",
        "time_scope": "none",
        "in_scope": True,
        "reasoning": ("Deterministic keyword fallback (planner LLM unavailable "
                      "or malformed). Houses NOT derived -- downstream must not "
                      "treat an empty house list as 'no houses relevant'."),
    }, notes


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def plan_question(
    question: str,
    *,
    llm: Optional[Callable[[str], str]] = None,
    log_path: Optional[str] = DECISION_LOG_PATH,
) -> Plan:
    """Plan one question. Never raises for a bad LLM answer -- it falls
    back and stamps the plan. Raises PlannerError only for a caller error
    (empty question).
    """
    if not question or not question.strip():
        raise PlannerError("question is empty")

    call = llm if llm is not None else _default_llm
    raw_responses: list[str] = []
    all_errors: list[str] = []

    for attempt in range(1, _MAX_LLM_ATTEMPTS + 1):
        try:
            raw = call(question)
        except Exception as e:
            all_errors.append(f"attempt {attempt}: LLM call raised "
                              f"{type(e).__name__}: {e}")
            continue
        raw_responses.append(raw)
        fields, errors = parse_llm_plan(raw)
        if fields is not None:
            plan = Plan(
                question=question,
                source="llm" if attempt == 1 else "llm_retry",
                planner_fallback=False,
                validation_errors=all_errors,
                raw_responses=raw_responses,
                **fields,
            )
            _log_decision(plan, log_path)
            return plan
        all_errors.extend(f"attempt {attempt}: {e}" for e in errors)

    fields, notes = fallback_plan(question)
    plan = Plan(
        question=question,
        source="fallback",
        planner_fallback=True,
        validation_errors=all_errors + notes,
        raw_responses=raw_responses,
        **fields,
    )
    _log_decision(plan, log_path)
    return plan


def _log_decision(plan: Plan, log_path: Optional[str]) -> None:
    """Append-only decision log. A logging failure must never take down a
    live answer, so it is swallowed after being surfaced on the record.
    """
    if not log_path:
        return
    record = plan.to_dict()
    # raw responses can be long; keep the log readable but auditable
    record["raw_responses"] = [r[:2000] for r in record.get("raw_responses", [])]
    record["logged_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except (OSError, ValueError, TypeError) as e:
        # surfaced, not silent -- but never fatal. ValueError covers embedded
        # NULs in a bad path; a logging problem must never lose an answer.
        print(f"[planner] WARNING: decision log write failed: {e}")


# ---------------------------------------------------------------------------
# Domain -> unit selection (the plan's consumer)
# ---------------------------------------------------------------------------
_TAGS_CACHE: dict[str, dict] = {}


def _load_domain_tags(path: str = DOMAIN_TAGS_PATH) -> dict:
    if path not in _TAGS_CACHE:
        try:
            with open(path, encoding="utf-8") as f:
                _TAGS_CACHE[path] = json.load(f)
        except OSError as e:
            raise PlannerError(f"cannot read domain tags at {path}: {e}") from e
    return _TAGS_CACHE[path]


def select_units(
    plan: Plan,
    *,
    tags_path: str = DOMAIN_TAGS_PATH,
    token_budget: int = DEFAULT_TOKEN_BUDGET,
) -> UnitSelection:
    """Turn planned domains into chapter-index unit_ids.

    A unit is selected if ANY of the planned domains has at least one
    tagged segment in it. Union, never intersection -- widen when unsure.
    Order follows the corpus order in domain_tags, so payload document
    order is stable run to run.
    """
    tags = _load_domain_tags(tags_path)
    units = tags["units"]
    corpus_tokens = sum(u.get("tokens", 0) for u in units)

    selected: list[str] = []
    per_unit_tokens: dict[str, int] = {}
    per_domain_units: dict[str, list[str]] = {d: [] for d in plan.domains}

    for u in units:
        uid = u["unit_id"]
        per_domain = u.get("per_domain", {})
        hit_domains = [d for d in plan.domains
                       if per_domain.get(d, {}).get("segment_count", 0) > 0]
        if not hit_domains:
            continue
        selected.append(uid)
        per_unit_tokens[uid] = u.get("tokens", 0)
        for d in hit_domains:
            per_domain_units[d].append(uid)

    total = sum(per_unit_tokens.values())
    return UnitSelection(
        unit_ids=selected,
        approx_tokens=total,
        over_budget=total > token_budget,
        token_budget=token_budget,
        per_domain_units=per_domain_units,
        per_unit_tokens=per_unit_tokens,
        corpus_tokens=corpus_tokens,
    )


# ---------------------------------------------------------------------------
# Segment-level domain filter (the second half of selection)
# ---------------------------------------------------------------------------
# MEASURED FINDING (this session) that motivates this function:
#   Unit-level selection alone puts 37-48% of the corpus in the payload,
#   because a chapter is selected whole if ANY of its segments carries a
#   planned domain. The relation filter inside payload_builder then cuts
#   only 7-12% at that scale -- it is a WITHIN-CHAPTER tool, exactly as
#   S124 recorded, not a selector. Stacking the per-SEGMENT domain tags on
#   top cuts a further 22-46% (career 90,653 -> 48,589 approx-tokens,
#   37.4% -> 20.0% of corpus), and 0 of 1,129 segment ids failed to
#   resolve, so the tag artifact and payload_builder share one id scheme.
#
# FAIL-SAFE, per the S124 lock: a segment the tags do not know, carry no
# domain for, or mark `unfittable` is KEPT, never dropped. Only a segment
# positively tagged with domains that miss the plan entirely is dropped.
def filter_segments_by_domain(
    payload: dict,
    plan: Plan,
    *,
    tags_path: str = DOMAIN_TAGS_PATH,
) -> dict:
    """Return a NEW payload with `kept` narrowed to the planned domains.

    Never mutates the input. Adds `domain_filter` stats and a per-segment
    `domain_drop_reason` so every drop is auditable.
    """
    if not plan.domains:
        return payload

    tags = _load_domain_tags(tags_path)
    seg_domains = {
        s["segment_id"]: (set(s.get("domains") or []), bool(s.get("unfittable")))
        for s in tags["segments"]
    }
    want = set(plan.domains)

    out = dict(payload)
    new_segments = []
    counts = {"kept_domain_match": 0, "kept_failsafe_untagged": 0,
              "kept_failsafe_unknown_id": 0, "dropped_domain_miss": 0,
              "already_dropped": 0}
    tokens_before = 0
    tokens_after = 0

    for seg in payload.get("segments", []):
        s = dict(seg)
        if not s.get("kept"):
            counts["already_dropped"] += 1
            new_segments.append(s)
            continue
        tokens_before += s.get("tokens", 0)
        entry = seg_domains.get(s["segment_id"])
        if entry is None:
            counts["kept_failsafe_unknown_id"] += 1
            s["domain_filter"] = "failsafe_unknown_id"
        else:
            doms, unfittable = entry
            if not doms or unfittable:
                counts["kept_failsafe_untagged"] += 1
                s["domain_filter"] = "failsafe_untagged"
            elif doms & want:
                counts["kept_domain_match"] += 1
                s["domain_filter"] = "domain_match"
            else:
                counts["dropped_domain_miss"] += 1
                s["kept"] = False
                s["domain_filter"] = "dropped_domain_miss"
                s["domain_drop_reason"] = (
                    f"tagged {sorted(doms)}, plan wanted {sorted(want)}")
                new_segments.append(s)
                continue
        tokens_after += s.get("tokens", 0)
        new_segments.append(s)

    out["segments"] = new_segments
    out["domain_filter"] = {
        "planned_domains": list(plan.domains),
        "counts": counts,
        "segment_tokens_before": tokens_before,
        "segment_tokens_after": tokens_after,
        "segment_cut_pct": (
            round(100 * (1 - tokens_after / tokens_before), 2)
            if tokens_before else 0.0),
        "planner_version": PLANNER_VERSION,
    }
    return out


def payload_tokens(payload: dict) -> int:
    """Approx tokens actually shipped to the interpreter: whole-chapter
    units plus every still-kept segment."""
    whole = sum(u.get("tokens", 0) for u in payload.get("units", []))
    kept = sum(s.get("tokens", 0) for s in payload.get("segments", [])
               if s.get("kept"))
    return whole + kept


def plan_and_build(
    question: str,
    chart_facts: dict,
    *,
    llm: Optional[Callable[[str], str]] = None,
    token_budget: int = DEFAULT_TOKEN_BUDGET,
    log_path: Optional[str] = DECISION_LOG_PATH,
) -> dict:
    """Full Planner stage, end to end.

    question -> plan -> unit selection -> payload_builder -> domain filter.
    Returns {plan, selection, payload, tokens, over_budget}. Does NOT call
    the Interpreter -- that is the next stage and stays separate.
    """
    plan = plan_question(question, llm=llm, log_path=log_path)
    return build_from_plan(plan, chart_facts, token_budget=token_budget)


def build_from_plan(
    plan: Plan,
    chart_facts: dict,
    *,
    token_budget: int = DEFAULT_TOKEN_BUDGET,
) -> dict:
    """Everything `plan_and_build` does AFTER the plan exists.

    Split out (S129) so a caller can interpose a step between planning and
    retrieval -- specifically `capability_gate.assess`, which narrows the
    plan's domains to those the current fact block can actually support
    before a single chapter is selected. `plan_and_build` is unchanged in
    behaviour and remains the entry point for every existing caller.
    """
    from agent.astro import payload_builder  # local: keeps import cost off CI

    if not plan.in_scope or not plan.domains:
        return {"plan": plan, "selection": None, "payload": None,
                "tokens": 0, "over_budget": False,
                "refused": True,
                "refusal_reason": ("out of scope" if not plan.in_scope
                                   else "no domains planned")}

    selection = select_units(plan, token_budget=token_budget)
    payload = payload_builder.build_payload(chart_facts,
                                            unit_ids=selection.unit_ids)
    payload = filter_segments_by_domain(payload, plan)
    tokens = payload_tokens(payload)
    exceeds = tokens > HARD_CONTEXT_CEILING
    est_real = int(tokens * APPROX_TO_REAL_RATIO)
    return {
        "plan": plan,
        "selection": selection,
        "payload": payload,
        "tokens": tokens,
        "estimated_real_tokens": est_real,
        "over_budget": tokens > token_budget,
        "exceeds_context": exceeds,
        "exceeds_tpm": est_real > INTERPRETER_TPM_LIMIT,
        "tpm_note": (
            f"~{est_real:,} real tokens exceeds the measured "
            f"{INTERPRETER_TPM_LIMIT:,} TPM cap; a gpt-4o call will 429. "
            f"Advisory only -- tier-specific, not a refusal."
        ) if est_real > INTERPRETER_TPM_LIMIT else None,
        "refused": exceeds,
        "refusal_reason": (
            f"payload {tokens:,} approx-tokens (~{est_real:,} "
            f"real) exceeds the {HARD_CONTEXT_CEILING:,} ceiling for a "
            f"{INTERPRETER_CONTEXT_WINDOW:,}-token model. NOT truncated -- "
            f"narrow the question or raise the ceiling deliberately."
        ) if exceeds else None,
    }
