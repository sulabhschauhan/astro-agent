"""
Astro Agent -- TYPED PRECONDITION PREDICATES (Phase 0, S137).

WHAT THIS REPLACES
------------------
Verification used to ask a claim's ENGLISH PROSE whether it applied to this
chart: `silence_gate._CONDITION_RE` matches "<Nth> lord ... in the <Mth>" and
nothing else, so of the eight fact classes `capability_gate.FACT_BLOCK_PROVIDES`
declares, exactly one was enforceable and a second (planet positions) was
advisory. The other six -- house_lords, aspects, dignity, navamsa, yogas,
ascendant_sign -- had no verifier at all, and every fact-block widening since
S130 added answering power with no verifying power.

That was harmless while UNDETERMINED failed OPEN. The S136 composer flip made
it consequential: on the first live composed run (20260918T193426Z) eight of
twelve claims were demoted as "unverified", and five of those named yogas the
detector had INDEPENDENTLY COMPUTED AS FIRED (adhi, vesi, nipuna,
kendra_trikona_1_5, yogada_gl_mercury). The system computed a fact and then
reported it as doubtful.

The inversion is the bug: the chart is computed exhaustively and deterministically,
so a claim's precondition should be evaluated AGAINST THE FACT BLOCK, not
pattern-matched against its own grammar. This module is that evaluation. It is
the astro-side counterpart of the palm engine's typed `Antecedent` matching
(`agent/interpretive/palm_select.match`), which has worked since S95.

THE THREE-VALUED OUTCOME, AND THE ONE DROP AUTHORITY
----------------------------------------------------
    SATISFIED     the fact block CONFIRMS the precondition
    CONTRADICTED  the fact block REFUTES it
    UNEVALUABLE   no evaluator for this type, or the fact is absent

Only CONTRADICTED may drop a claim. UNEVALUABLE ships, hedged, and is RECORDED.
This is S124's "fail safe means fail to zero, not to something wrong" carried
into verification, where it had never been applied: a filter that cannot judge
must keep, never discard. Nothing downstream may treat UNEVALUABLE as a reason
to drop or demote.

CLOSED VOCABULARY (Working Style #35 / P-030)
---------------------------------------------
`PREDICATES` is closed. Every type carries a gloss and a scope guard, and both
are asserted by test -- a bare token list handed to an LLM is exactly the defect
P-030 records. `unfittable` is the deliberate escape hatch (S124): a precondition
the vocabulary cannot express is DECLARED and measured rather than absorbed, so
a wrong vocabulary shows up as a rate instead of hiding.

DELIBERATELY ABSENT: any degree-level predicate. Exaltation tables carry SIGNS
only and `meta.jd_ut` / `meta.asc_lon_sidereal` are rounded (S130 accepted gap),
so `planet_degree(...)` would look evaluable and be false at the precision it
implies. Sign-level dignity only. Enforced by test.

FAILURE POSTURE: never raises, never CONTRADICTS on missing data. A malformed
predicate, an absent fact class, an unknown graha -- all UNEVALUABLE. The only
route to CONTRADICTED is a fact that is present and disagrees.

Python 3.11.
"""
from __future__ import annotations

import re
from typing import Any, Callable

__all__ = [
    "PREDICATE_VERSION",
    "SATISFIED",
    "CONTRADICTED",
    "UNEVALUABLE",
    "PREDICATES",
    "PREDICATE_FACT_CLASS",
    "evaluate",
    "evaluate_claim",
    "coverage",
]

PREDICATE_VERSION = "predicates-1.2"

SATISFIED = "satisfied"
CONTRADICTED = "contradicted"
UNEVALUABLE = "unevaluable"

_GRAHAS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
           "Rahu", "Ketu")
_SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
          "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
# Sign-level only. `_dignity()` in chart_facts restates the S130 HEAD of the
# dignity vocabulary; friendship tiers stay out (contested), degrees stay out
# (tables are sign-level). Do not widen without widening the fact block first.
_DIGNITIES = ("Exalted", "Debilitated", "Own Sign")


# --------------------------------------------------------------- normalising

def _graha(v: Any) -> str | None:
    if not isinstance(v, str):
        return None
    t = v.strip().title()
    return t if t in _GRAHAS else None


def _sign(v: Any) -> str | None:
    if not isinstance(v, str):
        return None
    t = v.strip().title()
    return t if t in _SIGNS else None


def _dignity(v: Any) -> str | None:
    if not isinstance(v, str):
        return None
    t = " ".join(w.capitalize() for w in v.strip().split())
    return t if t in _DIGNITIES else None


def _house(v: Any) -> int | None:
    """Houses are 1..12. A bool is not a house (bool is an int in Python)."""
    if isinstance(v, bool) or not isinstance(v, (int, str)):
        return None
    try:
        n = int(v)
    except (TypeError, ValueError):
        return None
    return n if 1 <= n <= 12 else None


def _cmp(observed: Any, expected: Any, what: str) -> tuple[str, str]:
    """The only place a CONTRADICTED verdict is produced. Both values must be
    present and comparable; anything else is UNEVALUABLE, never a refutation."""
    if observed is None or expected is None:
        return UNEVALUABLE, f"{what}: not present in the fact block"
    if observed == expected:
        return SATISFIED, f"{what}: {observed}"
    return CONTRADICTED, f"{what}: chart has {observed}, claim needs {expected}"


# ---------------------------------------------------------------- evaluators
# Contract, identical for every evaluator:
#     (pred: dict, facts: dict) -> (verdict, reason)
# Pure, total, never raises. Reads ONE fact class. Testable with a literal dict.

def _ev_lord_in_house(p: dict, f: dict) -> tuple[str, str]:
    h = _house(p.get("lord_of"))
    want = _house(p.get("house"))
    if h is None or want is None:
        return UNEVALUABLE, "lord_in_house: house numbers out of range or absent"
    got = _house((f.get("lord_house_map") or {}).get(h,
                 (f.get("lord_house_map") or {}).get(str(h))))
    return _cmp(got, want, f"the {h}th lord's house")


def _ev_house_lord_is(p: dict, f: dict) -> tuple[str, str]:
    h = _house(p.get("house"))
    want = _graha(p.get("graha"))
    if h is None or want is None:
        return UNEVALUABLE, "house_lord_is: house or graha not recognised"
    row = (f.get("house_lords") or {}).get(h, (f.get("house_lords") or {}).get(str(h)))
    got = _graha((row or {}).get("lord")) if isinstance(row, dict) else None
    return _cmp(got, want, f"the lord of house {h}")


def _planet_row(f: dict, g: str) -> dict:
    row = (f.get("planet_positions") or {}).get(g)
    return row if isinstance(row, dict) else {}


def _ev_planet_in_house(p: dict, f: dict) -> tuple[str, str]:
    g = _graha(p.get("graha"))
    want = _house(p.get("house"))
    if g is None or want is None:
        return UNEVALUABLE, "planet_in_house: graha or house not recognised"
    return _cmp(_house(_planet_row(f, g).get("house")), want, f"{g}'s house")


def _ev_planet_in_sign(p: dict, f: dict) -> tuple[str, str]:
    g = _graha(p.get("graha"))
    want = _sign(p.get("sign"))
    if g is None or want is None:
        return UNEVALUABLE, "planet_in_sign: graha or sign not recognised"
    return _cmp(_sign(_planet_row(f, g).get("sign")), want, f"{g}'s sign")


def _ev_planet_dignity(p: dict, f: dict) -> tuple[str, str]:
    """SIGN-LEVEL ONLY. The fact block omits `dignity` entirely for a planet in
    none of the three head states, so ABSENCE here is a real negative, not a
    coverage hole -- but only when the planet itself is present."""
    g = _graha(p.get("graha"))
    want = _dignity(p.get("dignity"))
    if g is None or want is None:
        return UNEVALUABLE, "planet_dignity: graha or dignity outside the sign-level head"
    row = _planet_row(f, g)
    if not row:
        return UNEVALUABLE, f"planet_dignity: {g} not in the fact block"
    got = _dignity(row.get("dignity"))
    if got is None:
        return CONTRADICTED, f"{g} is in none of Exalted/Debilitated/Own Sign"
    return _cmp(got, want, f"{g}'s dignity")


def _ev_conjunction(p: dict, f: dict) -> tuple[str, str]:
    """Reads the CALCULATOR'S OWN conjunction verdicts rather than re-deriving
    them from shared signs -- re-deriving would be a second implementation of a
    rule the calculator already owns (P-029's sibling: no doctrine restated
    outside its owner). The rows are short generated strings, matched on whole
    graha names only."""
    pair = p.get("grahas")
    if not isinstance(pair, (list, tuple)) or len(pair) != 2:
        return UNEVALUABLE, "conjunction: needs exactly two grahas"
    a, b = _graha(pair[0]), _graha(pair[1])
    if a is None or b is None or a == b:
        return UNEVALUABLE, "conjunction: grahas not recognised or identical"
    rows = ((f.get("aspects") or {}).get("conjunctions"))
    if not isinstance(rows, list):
        return UNEVALUABLE, "conjunction: no conjunction list in the fact block"
    for row in rows:
        if not isinstance(row, str):
            continue
        names = set(re.findall(r"\b(" + "|".join(_GRAHAS) + r")\b", row))
        if {a, b} <= names:
            return SATISFIED, f"{a} conjunct {b}"
    return CONTRADICTED, f"{a} and {b} are not listed as conjunct"


def _ev_aspects_house(p: dict, f: dict) -> tuple[str, str]:
    g = _graha(p.get("graha"))
    want = _house(p.get("house"))
    if g is None or want is None:
        return UNEVALUABLE, "aspects_house: graha or house not recognised"
    by = (f.get("aspects") or {}).get("aspects_by_planet")
    if not isinstance(by, dict) or g not in by:
        return UNEVALUABLE, f"aspects_house: no aspect list for {g}"
    houses = {_house(h) for h in (by.get(g) or [])}
    if want in houses:
        return SATISFIED, f"{g} aspects house {want}"
    return CONTRADICTED, f"{g} aspects {sorted(h for h in houses if h)}, not {want}"


def _ev_aspected_by(p: dict, f: dict) -> tuple[str, str]:
    g = _graha(p.get("graha"))
    src = _graha(p.get("by"))
    if g is None or src is None:
        return UNEVALUABLE, "aspected_by: graha not recognised"
    tbl = (f.get("aspects") or {}).get("aspected_by")
    if not isinstance(tbl, dict):
        return UNEVALUABLE, "aspected_by: no aspected_by table"
    if src in {_graha(x) for x in (tbl.get(g) or [])}:
        return SATISFIED, f"{g} is aspected by {src}"
    return CONTRADICTED, f"{g} is not aspected by {src}"


def _ev_mutual_aspect(p: dict, f: dict) -> tuple[str, str]:
    """A one-way aspect and a mutual one carry different doctrinal weight
    (S130), so this is its own predicate, not a conjunction of two."""
    pair = p.get("grahas")
    if not isinstance(pair, (list, tuple)) or len(pair) != 2:
        return UNEVALUABLE, "mutual_aspect: needs exactly two grahas"
    a, b = _graha(pair[0]), _graha(pair[1])
    if a is None or b is None or a == b:
        return UNEVALUABLE, "mutual_aspect: grahas not recognised or identical"
    tbl = (f.get("aspects") or {}).get("aspected_by")
    if not isinstance(tbl, dict):
        return UNEVALUABLE, "mutual_aspect: no aspected_by table"
    ab = b in {_graha(x) for x in (tbl.get(a) or [])}
    ba = a in {_graha(x) for x in (tbl.get(b) or [])}
    if ab and ba:
        return SATISFIED, f"{a} and {b} aspect each other"
    return CONTRADICTED, f"{a}<-{b}={ab}, {b}<-{a}={ba}; not mutual"


def _navamsa_row(f: dict, g: str) -> dict:
    row = ((f.get("navamsa") or {}).get("placements") or {}).get(g)
    return row if isinstance(row, dict) else {}


def _ev_navamsa_sign(p: dict, f: dict) -> tuple[str, str]:
    g = _graha(p.get("graha"))
    want = _sign(p.get("sign"))
    if g is None or want is None:
        return UNEVALUABLE, "navamsa_sign: graha or sign not recognised"
    return _cmp(_sign(_navamsa_row(f, g).get("sign")), want, f"{g}'s navamsa sign")


def _ev_navamsa_dignity(p: dict, f: dict) -> tuple[str, str]:
    g = _graha(p.get("graha"))
    want = _dignity(p.get("dignity"))
    if g is None or want is None:
        return UNEVALUABLE, "navamsa_dignity: graha or dignity outside the sign-level head"
    row = _navamsa_row(f, g)
    if not row:
        return UNEVALUABLE, f"navamsa_dignity: {g} absent from D9 (D9 is fail-soft)"
    got = _dignity(row.get("dignity"))
    if got is None:
        return CONTRADICTED, f"{g} holds no head dignity in D9"
    return _cmp(got, want, f"{g}'s navamsa dignity")


def _ev_ascendant_is(p: dict, f: dict) -> tuple[str, str]:
    want = _sign(p.get("sign"))
    if want is None:
        return UNEVALUABLE, "ascendant_is: sign not recognised"
    return _cmp(_sign(f.get("ascendant_sign")), want, "the ascendant sign")


def _yoga_ids(f: dict, key: str) -> set[str]:
    rows = (f.get("yogas") or {}).get(key)
    if not isinstance(rows, list):
        return set()
    return {str(r.get("id")) for r in rows if isinstance(r, dict) and r.get("id")}


def _ev_yoga_fired(p: dict, f: dict) -> tuple[str, str]:
    """THE CASE THAT MOTIVATED THIS MODULE. The detector computes fired and
    ruled_out deterministically (S131-S133, validated on two reference charts),
    so a yoga claim is the BEST-verified kind there is -- it was only
    'unverifiable' because nothing could read the verdict."""
    yid = p.get("yoga_id")
    if not isinstance(yid, str) or not yid.strip():
        return UNEVALUABLE, "yoga_fired: no yoga_id"
    yid = yid.strip()
    fired, out = _yoga_ids(f, "fired"), _yoga_ids(f, "ruled_out")
    if yid in fired:
        return SATISFIED, f"{yid} fired"
    if yid in out:
        return CONTRADICTED, f"{yid} was computed and ruled out"
    # Not in either list: the detector does not compute this yoga at all. That
    # is a COVERAGE gap (the wider-BPHS-set item), never a refutation.
    return UNEVALUABLE, f"{yid} is not in the detector's catalogue"


def _ev_yoga_ruled_out(p: dict, f: dict) -> tuple[str, str]:
    """The counterweight half. Lets an answer say what does NOT apply, from the
    20 ruled-out verdicts already computed and today discarded."""
    yid = p.get("yoga_id")
    if not isinstance(yid, str) or not yid.strip():
        return UNEVALUABLE, "yoga_ruled_out: no yoga_id"
    yid = yid.strip()
    fired, out = _yoga_ids(f, "fired"), _yoga_ids(f, "ruled_out")
    if yid in out:
        return SATISFIED, f"{yid} ruled out"
    if yid in fired:
        return CONTRADICTED, f"{yid} actually fired"
    return UNEVALUABLE, f"{yid} is not in the detector's catalogue"


def _ev_unfittable(p: dict, f: dict) -> tuple[str, str]:
    """THE ESCAPE HATCH (S124). Always UNEVALUABLE by construction. Its measured
    RATE is the evidence that the vocabulary above is the right one; a rate that
    climbs means the vocabulary is wrong, not that the claims are."""
    note = str(p.get("note") or "").strip() or "no note given"
    return UNEVALUABLE, f"precondition not expressible in the vocabulary: {note}"


def _ev_any_of(p: dict, f: dict) -> tuple[str, str]:
    """DISJUNCTION (S139). The verse joins its arms with OR: the condition holds
    when ANY ONE arm holds. Each arm is itself a predicate, evaluated by the same
    `evaluate`, so nesting and every leaf type work unchanged.

        SATISFIED    at least one arm SATISFIED
        CONTRADICTED every arm CONTRADICTED (the disjunction is genuinely refuted)
        UNEVALUABLE  no arm holds and not all are refuted (some arm unevaluable)

    This is what a plain list of predicates -- which `evaluate_claim` ANDs --
    cannot express: an OR condition emitted as several ANDed predicates is
    wrongly CONTRADICTED the moment one arm fails, dropping a claim (or
    mislabelling a silence) whose verse is actually satisfied by another arm.
    """
    subs = p.get("any_of")
    if not isinstance(subs, list) or not subs:
        return UNEVALUABLE, "any_of: needs a non-empty list of sub-conditions"
    verdicts = [evaluate(s, f)[0] for s in subs]
    if SATISFIED in verdicts:
        return SATISFIED, "any_of: at least one arm holds"
    if all(v == CONTRADICTED for v in verdicts):
        return CONTRADICTED, "any_of: every arm is refuted"
    return UNEVALUABLE, "any_of: no arm holds and not all arms are refuted"


# ------------------------------------------------------------- the registry
# type -> (evaluator, fact class it reads, gloss, scope guard)
# GLOSS + SCOPE GUARD ARE MANDATORY per Working Style #35. A bare token list is
# the P-030 defect; both fields are asserted present by test.

PREDICATES: dict[str, tuple[Callable[[dict, dict], tuple[str, str]], str, str, str]] = {
    "lord_in_house": (
        _ev_lord_in_house, "lord_house_map",
        "the lord of house N occupies house H",
        "ONLY house-to-house lordship placement; never a planet's own house."),
    "house_lord_is": (
        _ev_house_lord_is, "house_lords",
        "house H is ruled by this graha",
        "ONLY which graha rules a house; says nothing about where it sits."),
    "planet_in_house": (
        _ev_planet_in_house, "planet_positions",
        "this graha occupies house H",
        "ONLY the natal D1 house; use navamsa_sign for D9."),
    "planet_in_sign": (
        _ev_planet_in_sign, "planet_positions",
        "this graha occupies this sign",
        "ONLY the natal D1 sign; use navamsa_sign for D9."),
    "planet_dignity": (
        _ev_planet_dignity, "planet_positions",
        "this graha is Exalted, Debilitated or in its Own Sign",
        "SIGN-LEVEL ONLY. Never a degree, never a friendship tier (both "
        "deliberately outside the fact block, S130)."),
    "conjunction": (
        _ev_conjunction, "aspects",
        "these two grahas are conjunct",
        "ONLY the calculator's own conjunction verdicts; never re-derived "
        "from a shared sign."),
    "aspects_house": (
        _ev_aspects_house, "aspects",
        "this graha casts an aspect on house H",
        "ONLY graha-to-HOUSE; use aspected_by for graha-to-graha."),
    "aspected_by": (
        _ev_aspected_by, "aspects",
        "this graha receives an aspect from that one",
        "ONE-WAY. Use mutual_aspect when the doctrine needs both directions."),
    "mutual_aspect": (
        _ev_mutual_aspect, "aspects",
        "these two grahas aspect each other",
        "BOTH directions required; a one-way aspect is aspected_by."),
    "navamsa_sign": (
        _ev_navamsa_sign, "navamsa",
        "this graha occupies this sign in the D9",
        "ONLY D9. Fail-soft: an absent D9 is UNEVALUABLE, never a refutation."),
    "navamsa_dignity": (
        _ev_navamsa_dignity, "navamsa",
        "this graha holds this dignity in the D9",
        "SIGN-LEVEL ONLY, same head vocabulary as planet_dignity."),
    "ascendant_is": (
        _ev_ascendant_is, "ascendant_sign",
        "the ascendant falls in this sign",
        "ONLY the D1 lagna sign; D9 lagna is not exposed as a predicate."),
    "yoga_fired": (
        _ev_yoga_fired, "yogas",
        "this named yoga fires for this chart",
        "ONLY ids in the detector's catalogue. An id it does not compute is "
        "UNEVALUABLE (coverage), never CONTRADICTED."),
    "yoga_ruled_out": (
        _ev_yoga_ruled_out, "yogas",
        "this named yoga was computed and does NOT fire",
        "Same catalogue constraint as yoga_fired. This is the counterweight "
        "half of the answer, not a negation operator."),
    "unfittable": (
        _ev_unfittable, "",
        "the precondition cannot be expressed in this vocabulary",
        "ESCAPE HATCH. Always UNEVALUABLE. Its RATE is the health metric for "
        "the vocabulary; it is never a way to pass an awkward claim."),
    "any_of": (
        _ev_any_of, "",
        "the condition holds when ANY ONE of these sub-conditions holds (OR)",
        "DISJUNCTION. Use ONLY where the verse literally says 'or'. Arms are "
        "themselves predicates; SATISFIED if any arm holds, CONTRADICTED only "
        "when every arm is refuted. Never a way to widen an AND condition."),
}

PREDICATE_FACT_CLASS: dict[str, str] = {k: v[1] for k, v in PREDICATES.items()}


# --------------------------------------------------------------- evaluation

def evaluate(pred: Any, facts: dict | None) -> tuple[str, str]:
    """One predicate against the fact block. Total: never raises."""
    if not isinstance(pred, dict):
        return UNEVALUABLE, "predicate is not an object"
    ptype = pred.get("type")
    entry = PREDICATES.get(ptype) if isinstance(ptype, str) else None
    if entry is None:
        # Outside the closed vocabulary. Same posture as the planner's domain
        # validator: reject the TYPE, never invent a verdict for it.
        return UNEVALUABLE, f"unknown predicate type {ptype!r}"
    try:
        return entry[0](pred, facts or {})
    except Exception as e:  # noqa: BLE001 -- a broken evaluator costs a verdict, never the answer
        return UNEVALUABLE, f"evaluator raised {type(e).__name__}: {e}"


def evaluate_claim(preconditions: Any, facts: dict | None) -> dict:
    """Roll per-predicate verdicts up to ONE claim verdict.

    THE ROLL-UP RULE, and it is the whole safety argument:
      - ANY predicate CONTRADICTED  -> CONTRADICTED. This is the only thing in
        the system permitted to drop a claim.
      - ALL predicates SATISFIED (and at least one) -> SATISFIED. Lead with these.
      - anything else -> UNEVALUABLE. SHIPS, hedged, and is recorded.

    A claim stating NO preconditions is UNEVALUABLE, never SATISFIED: silence
    about a precondition is not evidence that one holds.
    """
    rows: list[dict] = []
    for p in (preconditions or []):
        verdict, reason = evaluate(p, facts)
        rows.append({
            "predicate": p,
            "type": (p or {}).get("type") if isinstance(p, dict) else None,
            "verdict": verdict,
            "reason": reason,
        })

    if any(r["verdict"] == CONTRADICTED for r in rows):
        overall = CONTRADICTED
    elif rows and all(r["verdict"] == SATISFIED for r in rows):
        overall = SATISFIED
    else:
        overall = UNEVALUABLE

    return {
        "verdict": overall,
        "predicates": rows,
        "n_predicates": len(rows),
        "n_satisfied": sum(1 for r in rows if r["verdict"] == SATISFIED),
        "n_contradicted": sum(1 for r in rows if r["verdict"] == CONTRADICTED),
        "n_unevaluable": sum(1 for r in rows if r["verdict"] == UNEVALUABLE),
        "predicate_version": PREDICATE_VERSION,
    }


def coverage(claim_results: list[dict]) -> dict:
    """The metric the design is judged on: how much of what we say can we
    actually check? Reported per fact class so a future widening's verifying
    power is VISIBLE rather than assumed."""
    by_class: dict[str, dict[str, int]] = {}
    totals = {SATISFIED: 0, CONTRADICTED: 0, UNEVALUABLE: 0}
    for res in claim_results or []:
        for row in res.get("predicates", []):
            cls = PREDICATE_FACT_CLASS.get(row.get("type"), "<unknown>")
            slot = by_class.setdefault(cls, {SATISFIED: 0, CONTRADICTED: 0,
                                             UNEVALUABLE: 0})
            slot[row["verdict"]] = slot.get(row["verdict"], 0) + 1
            totals[row["verdict"]] = totals.get(row["verdict"], 0) + 1
    n = len(claim_results or [])
    claim_verdicts = {v: sum(1 for r in claim_results or []
                             if r.get("verdict") == v)
                      for v in (SATISFIED, CONTRADICTED, UNEVALUABLE)}
    decided = totals[SATISFIED] + totals[CONTRADICTED]
    return {
        "claims": n,
        "claim_verdicts": claim_verdicts,
        "predicate_verdicts": totals,
        "by_fact_class": by_class,
        "typed_coverage": (decided / (decided + totals[UNEVALUABLE]))
        if (decided + totals[UNEVALUABLE]) else 0.0,
    }


# ---------------------------------------------------- the emission contract
# Phase 1 (S137): the INTERPRETER declares a claim's preconditions itself, in
# this vocabulary, with the verse in front of it. Nothing is authored offline
# and there is no claim-text -> predicate lookup anywhere in the system; the
# verse states its own condition and the model transcribes it into a shape
# Python can check. Argument names live HERE, beside the evaluators that read
# them, so the prompt and the validator cannot drift from the registry -- the
# S136 lesson (prompt glosses drawn from `_FALLBACK_GLOSS`) applied again.

PREDICATE_ARGS: dict[str, tuple[str, ...]] = {
    "lord_in_house": ("lord_of", "house"),
    "house_lord_is": ("house", "graha"),
    "planet_in_house": ("graha", "house"),
    "planet_in_sign": ("graha", "sign"),
    "planet_dignity": ("graha", "dignity"),
    "conjunction": ("grahas",),
    "aspects_house": ("graha", "house"),
    "aspected_by": ("graha", "by"),
    "mutual_aspect": ("grahas",),
    "navamsa_sign": ("graha", "sign"),
    "navamsa_dignity": ("graha", "dignity"),
    "ascendant_is": ("sign",),
    "yoga_fired": ("yoga_id",),
    "yoga_ruled_out": ("yoga_id",),
    "unfittable": ("note",),
    "any_of": ("any_of",),
}


def validate_precondition(p: Any) -> tuple[bool, str]:
    """SHAPE validation only -- is this a legal sentence in the vocabulary?

    Deliberately NOT value validation: whether `house: 13` or `graha: "Pluto"`
    is right is the EVALUATOR's business, and it answers UNEVALUABLE rather
    than rejecting. Splitting the two keeps one rule in one place.

    Rejecting an unknown TYPE is the same posture as the planner's closed-domain
    validator (S136): an emission outside the vocabulary is refused for free,
    which is belt-and-braces against a stale or jailbroken interpreter.
    """
    if not isinstance(p, dict):
        return False, "precondition is not an object"
    ptype = p.get("type")
    if not isinstance(ptype, str) or ptype not in PREDICATES:
        return False, f"unknown predicate type {ptype!r}"
    required = PREDICATE_ARGS.get(ptype, ())
    missing = [a for a in required if a not in p]
    if missing:
        return False, f"{ptype} is missing {', '.join(missing)}"
    extra = [k for k in p if k != "type" and k not in required]
    if extra:
        # Closed contract: an invented argument usually means an invented
        # reading of the verse, so it is refused rather than ignored.
        return False, f"{ptype} carries unknown argument(s) {', '.join(sorted(extra))}"
    if ptype == "any_of":
        subs = p.get("any_of")
        if not isinstance(subs, list) or not subs:
            return False, "any_of needs a non-empty list of sub-conditions"
        for sub in subs:
            ok, why = validate_precondition(sub)
            if not ok:
                return False, f"any_of arm invalid: {why}"
    return True, "ok"


def yoga_catalogue(facts: dict | None) -> list[str]:
    """Every yoga id the detector computes for this chart, fired or not.

    `fired` + `ruled_out` together ARE the catalogue: the detector emits a row
    for every rule it evaluates, so the union is exhaustive and needs no second
    list to drift from (P-030 in its other form -- a value space restated
    somewhere it is not computed).
    """
    y = (facts or {}).get("yogas") or {}
    ids: list[str] = []
    for key in ("fired", "ruled_out"):
        for row in (y.get(key) or []):
            if isinstance(row, dict) and row.get("id"):
                rid = str(row["id"])
                if rid not in ids:
                    ids.append(rid)
    return sorted(ids)


def vocabulary_prompt(facts: dict | None = None) -> str:
    """The predicate vocabulary as the interpreter is shown it.

    GENERATED FROM THE REGISTRY, never hand-maintained: a second copy of a
    closed vocabulary is KNOWN_PATTERNS P-030, and every term carries its gloss
    and its scope guard per Working Style #35 -- bare token names plus a mandate
    is exactly the defect that shipped `technique_method`.

    `facts` SUPPLIES THE YOGA CATALOGUE, and leaving it out is the S137 live
    defect this parameter exists to stop repeating. `yoga_fired` takes an id
    from a closed set the model cannot guess (`adhi`, `nipuna`,
    `kendra_trikona_1_5` ...). The first live Phase-1 run
    (20260919T072700Z) used `yoga_fired` ZERO times on a yoga question and
    reached for `unfittable` nine times instead -- a closed value space handed
    to an LLM without enumerating it, which is P-030 exactly.
    """
    lines = [
        "PRECONDITIONS -- the machine-checkable half of every claim.",
        "",
        "Each verse states the chart condition under which it applies. Write that "
        "condition out in the closed vocabulary below, as `preconditions` on the "
        "claim. Take it from THE VERSE, never from what you expect to be true, and "
        "never from the chart facts alone. These are checked against the computed "
        "chart: a condition this chart fails means the claim is dropped, so state "
        "the condition the verse actually sets and nothing more.",
        "",
        "A CONDITION WITH SEVERAL PARTS IS SEVERAL PREDICATES. They are ANDed: the "
        "claim is confirmed only when every one holds. Write them all out. For "
        "\"Saturn and Mars both in the 7th while the 10th lord is exalted\" give "
        "three: planet_in_house Saturn 7, planet_in_house Mars 7, planet_dignity on "
        "the 10th lord's graha. Do not collapse a multi-part condition into "
        "`unfittable` because it has several parts.",
        "",
        "A CONDITION THE VERSE JOINS WITH \"OR\" IS ONE any_of, NOT several "
        "predicates. \"the 5th lord in its own sign OR exalted\" is a single "
        "{\"type\": \"any_of\", \"any_of\": [{\"type\": \"planet_dignity\", ..., "
        "\"dignity\": \"Own Sign\"}, {\"type\": \"planet_dignity\", ..., "
        "\"dignity\": \"Exalted\"}]}. Separate plain predicates are ANDed and "
        "WRONGLY fail when only one arm is missing, so an OR verse written as "
        "separate predicates loses a true reading. Use any_of only where the "
        "verse actually says or.",
        "",
        "DO NOT ASSERT IN THE SENTENCE WHAT YOU HAVE NOT DECLARED. Every house, "
        "graha, sign or dignity your statement names must be covered by one of your "
        "preconditions. If you cannot declare a part of the verse's condition, do not "
        "state it as though it holds -- drop that clause, or declare the whole "
        "condition and let it be checked. A statement that says \"the 11th lord is in "
        "the 10th\" while declaring only WHICH graha rules the 11th is the failure "
        "this rule exists to stop: the declared part is true, the asserted part is "
        "never tested, and the claim ships looking verified.",
        "",
        "JUDGE EXPRESSIBILITY AGAINST THIS VOCABULARY, NOT AGAINST THE CHART FACTS. "
        "\"The chart facts do not state this\" is NOT a reason to use `unfittable` -- "
        "whether the condition HOLDS is decided downstream by evaluating it, and a "
        "condition this chart fails is exactly what should be written out so it can "
        "be caught. Your job is to state the verse's condition, not to check it.",
        "",
        "So if the condition concerns a house lord\u2019s placement, which graha rules "
        "a house, a planet\u2019s house, sign or dignity, an aspect, a D9 position, the "
        "ascendant sign, or a named yoga in the list below, it IS expressible -- write "
        "it out.",
        "",
        "`unfittable` is ONLY for a concept with no predicate type at all: Karakamsa, "
        "Arudha, combustion, planetary war, shadbala, avasthas, special lagnas, "
        "degrees or orbs. Give the note: {\"type\": \"unfittable\", \"note\": \"<the "
        "concept that has no type>\"} and still make the claim. That is honest and it "
        "is counted; inventing a near-miss predicate is not.",
        "",
        "A claim with no precondition is kept but can never be confirmed, so it "
        "reaches the reader hedged. Prefer stating the real condition.",
        "",
        "THE VOCABULARY -- these types and no others:",
    ]
    for name, (_fn, _cls, gloss, guard) in PREDICATES.items():
        args = PREDICATE_ARGS.get(name, ())
        sig = ", ".join(f'"{a}": ...' for a in args)
        lines.append(f'- {{"type": "{name}"{", " + sig if sig else ""}}}')
        lines.append(f"    {gloss}. {guard}")
    lines += [
        "",
        "Houses are numbers 1-12. Grahas are Sun, Moon, Mars, Mercury, Jupiter, "
        "Venus, Saturn, Rahu, Ketu. Signs are the twelve English names. Dignity is "
        "Exalted, Debilitated or Own Sign -- sign level only, never a degree.",
        "`grahas` takes exactly two graha names.",
    ]
    cat = yoga_catalogue(facts)
    if cat:
        lines += [
            "",
            "`yoga_id` MUST be one of these ids, exactly as written -- this list is "
            "COMPLETE and is every yoga the calculator evaluates for this chart. An "
            "id not in this list is not computed, so use `unfittable` for it rather "
            "than inventing an id:",
            ", ".join(cat),
        ]
    else:
        lines += [
            "",
            "No yoga catalogue was supplied for this chart, so do not emit "
            "`yoga_fired` or `yoga_ruled_out`; use `unfittable` for a named yoga.",
        ]
    return "\n".join(lines)


# ================= STATEMENT COVERAGE (ADVISORY, S137 amendment) =============
# THE DEFECT THIS MEASURES, from the controlled 072700Z/080136Z diff:
# a precondition that is TRUE but is not the STATEMENT's condition. Four of
# eight shipped claims carried a chart assertion the declared preconditions
# never tested -- e.g. "With the 11th lord in the 10th ..." declared only
# `house_lord_is(11, Venus)`, which is true and says nothing about where the
# 11th lord sits (it is in the 6th). Run A had typed that same segment as
# `lord_in_house(11,10)`, got CONTRADICTED and correctly DROPPED it; Run B
# re-typed it weaker and shipped it with a verified badge.
#
# `ANSWER_VERIFICATION_ARCHITECTURE` §7.1 named "a fabricated precondition that
# happens to be SATISFIED". This is its neighbour and is far more frequent:
# A TRUE PRECONDITION THAT IS NOT THE STATEMENT'S CONDITION. Nothing binds the
# declared condition to the sentence it licenses, and a predicate evaluator
# cannot see it by construction -- it only ever judges what it was handed.
#
# IT IS A COUNTER, NOT A JUDGE, AND IT HAS NO DROP AUTHORITY.
# Extracting tokens from prose is the very thing the typed path removed, so
# this is deliberately the WEAKEST possible form: closed vocabulary, set
# containment, no clause reading, no threshold. Its errors point toward
# hedging, the safe direction S125 permits for a permissive matcher. Promotion
# to enforcing is gated on a measured rate, exactly as the S129b planet reader
# was -- never in one step, never on intuition.

_ORDINAL_RE = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)\b", re.I)
_TOKEN_WORD_RE = re.compile(
    r"\b(" + "|".join(_GRAHAS + _SIGNS + ("Exalted", "Debilitated")) + r")\b", re.I)
_OWN_SIGN_RE = re.compile(r"\bown sign\b", re.I)
# The ascendant is house 1 under any name. Without this the commonest
# under-coverage in the live data ("... and aspecting the ascendant", declared
# as an aspect to house 10) is invisible.
_ASCENDANT_RE = re.compile(r"\b(ascendant|lagna|rising sign)\b", re.I)


def chart_tokens(text: str) -> set[str]:
    """Chart facts named in `text`, normalised. Houses as 'h<N>'.

    SINGLE OWNER of this extraction. `composer.chart_tokens` is an alias of
    this function: two copies of a closed vocabulary drift (P-030), and the
    composer's ENFORCING no-new-chart-facts check and this advisory counter
    must agree on what a chart token IS or their numbers cannot be compared.
    """
    if not text:
        return set()
    out = {f"h{int(m.group(1))}" for m in _ORDINAL_RE.finditer(text)}
    out |= {m.group(1).title() for m in _TOKEN_WORD_RE.finditer(text)}
    if _OWN_SIGN_RE.search(text):
        out.add("Own Sign")
    if _ASCENDANT_RE.search(text):
        out.add("h1")
    return out


def predicate_tokens(preconditions: Any) -> set[str]:
    """The chart tokens a precondition SET actually puts under test.

    Derived from each predicate's declared arguments, so it stays honest as the
    vocabulary grows. A yoga predicate contributes NOTHING here: `yoga_fired`
    tests a named combination, not the grahas and houses a sentence may name
    around it -- which is precisely how a true yoga predicate let an untested
    "Jupiter and Mars mutually aspect" ride along in the live data.
    """
    out: set[str] = set()
    for p in (preconditions or []):
        if not isinstance(p, dict):
            continue
        t = p.get("type")
        if t not in PREDICATES:
            continue
        if t == "any_of":
            out |= predicate_tokens(p.get("any_of") or [])
            continue
        for arg in PREDICATE_ARGS.get(t, ()):
            v = p.get(arg)
            if arg in ("house", "lord_of"):
                h = _house(v)
                if h:
                    out.add(f"h{h}")
            elif arg in ("graha", "by"):
                g = _graha(v)
                if g:
                    out.add(g)
            elif arg == "grahas" and isinstance(v, (list, tuple)):
                out |= {g for g in (_graha(x) for x in v) if g}
            elif arg == "sign":
                sg = _sign(v)
                if sg:
                    out.add(sg)
            elif arg == "dignity":
                d = _dignity(v)
                if d:
                    out.add(d)
    return out


def statement_coverage(statement: str, preconditions: Any) -> dict:
    """ADVISORY: which chart tokens the statement asserts and the preconditions
    never test. NEVER drops, NEVER demotes, NEVER changes a verdict."""
    asserted = chart_tokens(statement)
    declared = predicate_tokens(preconditions)
    uncovered = sorted(asserted - declared)
    return {
        "asserted": sorted(asserted),
        "declared": sorted(declared),
        "uncovered": uncovered,
        "covered": not uncovered,
        # Denominator is what the SENTENCE claims, not what was declared: the
        # question is "did you test what you said", not "did you declare a lot".
        "coverage_ratio": (1.0 if not asserted
                           else (len(asserted) - len(uncovered)) / len(asserted)),
    }
