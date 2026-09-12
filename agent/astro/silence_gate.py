"""

================================================================
PATH B / LAB TRACK -- NOT WIRED TO THE PRODUCT (S128 lock).

This module has NO non-test caller. The live answer path is
agent/infra/orchestrator.answer_question, imported by
frontend/app.py:31. Changing this file ships NOTHING to users.
Read docs/ANSWER_PATHS.md before editing or proposing work here.
================================================================

Astro Agent -- STAGE 5a: THE SILENCE GATE.

WHAT PROBLEM THIS SOLVES (measured 2026-09-05, S125 three-domain run).
The Interpreter fabricates nothing -- every citation resolves, zero ghosts
across every run on record. But it recites doctrine whose PRECONDITION is
false for this chart. Real examples from that run, all correctly cited:

    "if the 12th lord is in the ascendant..."   chart: 12th lord in the 6th
    "if the 5th lord is in the 5th..."          chart: 5th lord in the 2nd
    "if the 5th lord is in the 6th..."          chart: 5th lord in the 2nd

3 of 12 shipped claims. Grounded, honest, correctly attributed -- and not
about this person. This is precondition-mismatch, the SAME defect class
that reversed the T4 palm ratification at S71 (`p139_c0`), reappearing on
a different surface.

WHAT THIS IS NOT.
Not a fabrication detector -- fabrication was never the problem here.
Not an LLM. Working Style #9 (NO ANCHORED JUDGMENT) forbids handing a
model both an expectation and a request to judge against it; the model
observes, PYTHON compares. This module is that Python.

THE RULE, one line: drop a claim only when THE CLAIM ITSELF states a
lord-in-house condition that is readable, unambiguous, and POSITIVELY
FALSE for this chart. Anything unreadable, ambiguous, unconditioned, or
matching is kept.

That asymmetry is deliberate and mirrors the S123 palm ruling ("a DEFINITE
absence is stated, a can't-tell stays silent"): act only on a positive
determination, never on an absence of evidence. A gate that dropped
UNDETERMINED claims would silence most of the corpus, because most verses
are not lord-in-house shaped.

FAIL-OPEN, everywhere: any error inside this module returns the answer
unchanged with the failure recorded. A silence gate that eats a good
answer is worse than the defect it fixes.

Python 3.11.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Optional

from agent.astro import payload_builder as PB

GATE_VERSION = "silence-gate-1.0"

# Verdicts. Only NOT_APPLICABLE ever removes anything.
APPLICABLE = "applicable"
NOT_APPLICABLE = "not_applicable"
UNDETERMINED = "undetermined"
UNKNOWN_SOURCE = "unknown_source"


class SilenceGateError(Exception):
    """Raised only for a caller error (malformed arguments), never for a
    claim we could not judge -- that is UNDETERMINED, not an exception."""


@dataclass
class SourceVerdict:
    source_id: str
    verdict: str
    relations: list[tuple[int, int]] = field(default_factory=list)
    matched: list[tuple[int, int]] = field(default_factory=list)
    note: str = ""


@dataclass
class ClaimVerdict:
    statement: str
    segment_ids: list[str]
    verdict: str
    sources: list[SourceVerdict] = field(default_factory=list)
    reason: str = ""


@dataclass
class GateResult:
    kept_claims: list[dict]
    dropped_claims: list[dict]
    verdicts: list[ClaimVerdict]
    silent_on: list[str]
    stats: dict
    gate_version: str = GATE_VERSION
    error: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["verdicts"] = [asdict(v) for v in self.verdicts]
        return d


# ---------------------------------------------------------------------------
# Chart facts -> the map we compare against
# ---------------------------------------------------------------------------
def _lord_house_map(chart_facts: dict) -> dict[int, int]:
    """Normalise to {house_owned: house_occupied} with int keys.

    JSON round-trips turn int keys into strings; this is the single place
    that is reconciled, so no caller has to care.
    """
    if not isinstance(chart_facts, dict):
        raise SilenceGateError("chart_facts must be a dict")
    raw = chart_facts.get("lord_house_map")
    if not isinstance(raw, dict) or not raw:
        raise SilenceGateError("chart_facts has no usable 'lord_house_map'")
    out: dict[int, int] = {}
    for k, v in raw.items():
        try:
            out[int(k)] = int(v)
        except (TypeError, ValueError) as e:
            raise SilenceGateError(
                f"lord_house_map entry {k!r}->{v!r} is not integer-valued") from e
    return out


# ---------------------------------------------------------------------------
# Source-level judgement
# ---------------------------------------------------------------------------
def judge_source(source_id: str, text: Optional[str],
                 lord_house: dict[int, int]) -> SourceVerdict:
    """Judge ONE cited source against the chart.

    A source is NOT_APPLICABLE only when it states at least one readable
    lord-in-house condition AND none of them hold for this chart.
    """
    if text is None:
        return SourceVerdict(source_id, UNKNOWN_SOURCE, note=(
            "cited id is not in the shipped payload; the ghost check owns "
            "this case, the gate does not judge it"))

    try:
        relations = PB.extract_relations(text)
    except Exception as e:  # never let a regex problem eat an answer
        return SourceVerdict(source_id, UNDETERMINED, note=(
            f"relation extraction failed ({type(e).__name__}: {e}); "
            f"kept by fail-open"))

    if not relations:
        return SourceVerdict(source_id, UNDETERMINED, note=(
            "no lord-in-house condition readable in this source -- it may be "
            "dasha, conjunction or general doctrine. Not judged, kept."))

    matched = [(a, b) for a, b in relations if lord_house.get(a) == b]
    if matched:
        return SourceVerdict(source_id, APPLICABLE, relations, matched, note=(
            f"chart satisfies {matched}"))
    return SourceVerdict(source_id, NOT_APPLICABLE, relations, [], note=(
        f"states {relations}; chart has "
        f"{sorted((a, lord_house.get(a)) for a, _ in relations)}"))


# ---------------------------------------------------------------------------
# READING A CONDITION -- purpose-built, strict, refuses when unsure
# ---------------------------------------------------------------------------
# ROOT CAUSE THIS REPLACES (adversarial review, S125). The first version of
# this gate reused `payload_builder.extract_relations`. That was the wrong
# tool, and the reason is a doctrine mismatch rather than a bug:
# `extract_relations` is a RETRIEVAL filter, deliberately permissive because
# over-matching there merely keeps extra text (fail-safe). Here, an
# over-match SILENCES A TRUE CLAIM -- invisible in production, and the worst
# thing this module can do. A permissive matcher cannot be a precision judge.
#
# Reproduced wrong drops it caused, every one on ordinary interpreter prose:
#   "if the 5th lord is NOT in the 5th"            -> read as "in the 5th"
#   "The 5th lord governs children. Jupiter is
#    in the 9th house."                            -> invented (5,9) across
#                                                      two sentences (DOTALL)
#   "the 4th lord is in the 7th FROM THE MOON"     -> judged against the
#                                                      ascendant-based map
#   "the 5th lord is ASPECTED BY Jupiter in the 9th" -> the 9th belongs to
#                                                      Jupiter, not the lord
#   "in the 9th OR THE 2ND"                        -> read only the first
#
# THE REPLACEMENT'S POSTURE: read one sentence at a time, demand an
# unambiguous shape, and REFUSE TO JUDGE at the first sign of anything that
# changes the meaning. Every disqualifier below turns the claim
# UNDETERMINED, which keeps it. The gate is deliberately narrow: it judges
# only the plain "the Nth lord is in the Mth" sentence, which is the exact
# shape the observed defect takes.

# House tokens: ORDINALS ONLY, plus the ascendant's own names. Bare digits
# are excluded on purpose -- "in the 2 charts examined" was being read as
# the 2nd house, which both invented and suppressed judgements.
_ORDINALS = {
    "1st": 1, "first": 1, "ascendant": 1, "lagna": 1, "asc": 1,
    "2nd": 2, "second": 2, "3rd": 3, "third": 3, "4th": 4, "fourth": 4,
    "5th": 5, "fifth": 5, "6th": 6, "sixth": 6, "7th": 7, "seventh": 7,
    "8th": 8, "eighth": 8, "9th": 9, "ninth": 9, "10th": 10, "tenth": 10,
    "11th": 11, "eleventh": 11, "12th": 12, "twelfth": 12,
}
_ORD_ALT = "|".join(sorted((re.escape(k) for k in _ORDINALS), key=len, reverse=True))
# "from the ascendant" / "from lagna" is the SAME frame the chart map uses
# and must never be treated as a foreign reference point -- only OTHER
# houses ("from the Moon", "from the 7th") change the frame.
_ASC_NAMES = {"ascendant", "lagna", "asc", "1st", "first"}
_FRAME_ORD_ALT = "|".join(sorted(
    (re.escape(k) for k in _ORDINALS if k not in _ASC_NAMES),
    key=len, reverse=True))

# The ONE shape this gate judges. Note: no DOTALL, and a 40-character window
# instead of 200.
#   THRESHOLD -- 40 characters between "<ordinal> lord" and "in the <ordinal>".
#   JUSTIFICATION: the plain doctrinal sentence ("If the 5th lord is in the
#   2nd") spans ~12 characters there; 40 absorbs ordinary qualifiers
#   ("is placed in", "happens to be in") without reaching a second clause.
#   SCOPE GUARD: the window can never cross a sentence -- sentences are split
#   before matching -- so widening it cannot manufacture a cross-sentence
#   relation, only a cross-clause one, which the disqualifiers below catch.
#   TUNING NOTE: widening this trades wrong-keeps for wrong-drops, the wrong
#   direction. Only narrow it.
_CONDITION_RE = re.compile(
    rf"\b({_ORD_ALT})\b\s+lords?\b.{{0,40}}?\bin\s+the\s+\b({_ORD_ALT})\b",
    re.IGNORECASE,
)

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.;:!?])\s+|\n+")

# Every one of these makes the sentence mean something the chart map cannot
# adjudicate. Presence => UNDETERMINED, never a drop.
# Read ONLY in the antecedent span. "free from diseases" is consequent
# language and must not suppress a clean condition, so scope matters more
# than the word list here.
_NEGATION = re.compile(
    r"\b(not|never|neither|nor|without|unless|except|other than|"
    r"rather than|instead of|devoid of|bereft of)\b", re.IGNORECASE)

# A frame other than the natal ascendant: a different reference point, or a
# different chart entirely. "from the ascendant"/"from lagna" is the SAME
# frame as the map and is explicitly allowed.
_OTHER_FRAME = re.compile(
    rf"\bfrom\s+(?:the\s+)?(?:moon|sun|mars|mercury|jupiter|venus|saturn|"
    rf"rahu|ketu|arudha|karakamsa|upapada|atmakaraka|{_FRAME_ORD_ALT})\b|"
    r"\b(navamsa|d-?\d{1,2}|amsa|varga|drekkana|dasamsa|arudha|upapada|"
    r"transit(?:s|ing)?|gochara|annual|varshaphal|divisional)\b",
    re.IGNORECASE)

# The second house in these belongs to another body, not to the lord.
_INDIRECT = re.compile(
    r"\b(aspect(?:ed|s|ing)?|conjunct(?:ion|ed)?|associate[ds]?|joined|"
    r"combust|karaka|along with|together with|placed with|"
    r"dasa|dasha|antardasa|antardasha|bhukti|period|"
    r"benefic|benefics|malefic|malefics)\b", re.IGNORECASE)


def _disjunction_after(sentence: str, end_pos: int) -> bool:
    """Is the matched house one of a list of alternatives?

    Looks only at the tail of the SAME sentence, for a connector followed by
    another ordinal, tolerating filler words ("or the 2nd", ", in the 5th",
    "/9th"). This is the general form of the guard the review found was too
    literal.
    """
    tail = sentence[end_pos:]
    return bool(re.search(
        rf"^\s*(?:house|bhava|sign|rasi)?\s*(?:,|/|\bor\b|\band\b)"
        rf"[\w\s]{{0,20}}?\b({_ORD_ALT})\b",
        tail, re.IGNORECASE))


def read_condition(statement: str) -> tuple[Optional[tuple[int, int]], str]:
    """Return (relation, reason). relation is None whenever the gate must
    not judge. NEVER guesses: every ambiguity returns None."""
    if not statement:
        return None, "empty claim"

    found: list[tuple[int, int]] = []
    for sentence in _SENTENCE_SPLIT_RE.split(statement):
        if not sentence.strip():
            continue
        for m in _CONDITION_RE.finditer(sentence):
            # disqualifiers are judged on the SENTENCE, not the whole claim,
            # so an unrelated later sentence cannot suppress a clean one
            # antecedent span only -- the "if" clause, not the "then"
            antecedent = sentence[:m.end()]
            if _NEGATION.search(antecedent):
                return None, "condition is negated or exclusionary; not judged"
            if _OTHER_FRAME.search(sentence):
                return None, ("sentence uses a reference frame other than the "
                              "natal ascendant (another house, or a divisional "
                              "or transit chart); not judged")
            if _INDIRECT.search(antecedent):
                return None, ("the house named belongs to an aspecting or "
                              "conjunct body, not to the lord; not judged")
            if _disjunction_after(sentence, m.end()):
                return None, ("the claim lists alternative houses and only the "
                              "first is readable; not judged")
            found.append((_ORDINALS[m.group(1).lower()],
                          _ORDINALS[m.group(2).lower()]))

    if not found:
        return None, ("no plain lord-in-house condition stated (dasha, "
                      "conjunction, or general doctrine); not judged")
    if len({f for f in found}) > 1:
        return None, (f"claim states {len(set(found))} conditions {sorted(set(found))}; "
                      "a compound condition cannot be judged one part at a "
                      "time; not judged")
    return found[0], "plain lord-in-house condition"


# ---------------------------------------------------------------------------
# SECOND CONDITION SHAPE: "<graha> is in the <Nth>"  -- ADVISORY ONLY (S129)
# ---------------------------------------------------------------------------
# WHY IT EXISTS. The fact block now carries per-graha house+sign, so the
# Interpreter can make planet-placement claims it previously could not. The
# lord reader above cannot see them: they fall to UNDETERMINED and are kept
# unchecked. Corpus measurement (S129, whole 2-book corpus, 20,426 sentences):
# 344 sentences state a plain planet-in-house condition against 176 that state
# a lord-in-house one, and 94.5% of the planet ones survive the four
# disqualifiers above. So this is the LARGER doctrinal shape, not a corner.
#
# WHY ADVISORY AND NOT ENFORCING. The lord reader earned its authority to DROP
# a claim from six MEASURED classes of wrong drop (S125). No equivalent
# measurement exists for this shape, and it cannot exist until live runs
# produce planet claims -- which they could not do before the block carried
# planet facts. Granting drop authority on an unmeasured axis is the same
# mistake S125 names, pointed at a new target.
#
# So `judge_planet_claim` RECORDS a verdict and NEVER removes a claim.
# `apply_silence_gate` reports the advisory tallies in `stats`; the capture
# writes them down. After a live run yields a real distribution with zero
# observed wrong drops, this can be promoted to enforcing -- a one-line change
# at the call site, not a rewrite.
#
# TUNING NOTE: promote only on measured evidence, never on the tally looking
# healthy. Demote on the first observed wrong drop.
_GRAHAS: dict[str, str] = {
    "sun": "Sun", "moon": "Moon", "mars": "Mars", "mercury": "Mercury",
    "jupiter": "Jupiter", "venus": "Venus", "saturn": "Saturn",
    "rahu": "Rahu", "ketu": "Ketu",
}
_GRAHA_ALT = "|".join(sorted((re.escape(k) for k in _GRAHAS), key=len, reverse=True))

# Same 40-character window and the same justification as _CONDITION_RE: it
# absorbs "is placed in" / "happens to be in" without reaching a second clause,
# and sentences are split before matching so it can never cross one.
_PLANET_CONDITION_RE = re.compile(
    rf"\b({_GRAHA_ALT})\b.{{0,40}}?\bin\s+the\s+\b({_ORD_ALT})\b",
    re.IGNORECASE,
)


def read_planet_condition(statement: str):
    """(graha, house) for a plain planet-in-house claim, else (None, why).

    Mirrors `read_condition` exactly -- same sentence split, same four
    disqualifiers -- so the two readers cannot diverge in judgement style.

    AMBIGUITY RULE: a sentence matching BOTH shapes ("Mars, the lord of the
    3rd, is in the 7th") is refused outright rather than guessed at. Measured:
    5 such sentences in the whole corpus. Picking one reading would let a
    single sentence produce two different verdicts.
    """
    found: list[tuple[str, int]] = []
    for sentence in _SENTENCE_SPLIT_RE.split(statement or ""):
        if _CONDITION_RE.search(sentence) and _PLANET_CONDITION_RE.search(sentence):
            return None, ("sentence states both a lord-in-house and a "
                          "planet-in-house condition; ambiguous, not judged")
        for m in _PLANET_CONDITION_RE.finditer(sentence):
            antecedent = sentence[:m.end()]
            if _NEGATION.search(antecedent):
                return None, "condition is negated or exclusionary; not judged"
            if _OTHER_FRAME.search(sentence):
                return None, ("sentence uses a reference frame other than the "
                              "natal ascendant; not judged")
            if _INDIRECT.search(antecedent):
                return None, ("the house named belongs to an aspecting or "
                              "conjunct body, not to the graha; not judged")
            if _disjunction_after(sentence, m.end()):
                return None, ("the claim lists alternative houses and only the "
                              "first is readable; not judged")
            found.append((_GRAHAS[m.group(1).lower()],
                          _ORDINALS[m.group(2).lower()]))

    if not found:
        return None, "no plain planet-in-house condition stated; not judged"
    if len(set(found)) > 1:
        return None, (f"claim states {len(set(found))} planet conditions "
                      f"{sorted(set(found))}; compound, not judged")
    return found[0], "plain planet-in-house condition"


def judge_planet_claim(statement: str, planet_house: dict[str, int]) -> tuple[str, str]:
    """ADVISORY verdict on one claim. Returns (verdict, reason). Never drops."""
    if not planet_house:
        return UNDETERMINED, "no planet positions in the chart facts; not judged"
    try:
        relation, why = read_planet_condition(statement)
    except Exception as e:  # noqa: BLE001 -- advisory must never break the gate
        return UNDETERMINED, f"planet reader failed ({type(e).__name__}: {e})"
    if relation is None:
        return UNDETERMINED, why
    graha, house = relation
    actual = planet_house.get(graha)
    if actual is None:
        return UNDETERMINED, f"{graha} is not in the supplied positions; not judged"
    if actual == house:
        return APPLICABLE, f"chart satisfies: {graha} is in the {house}"
    return NOT_APPLICABLE, (f"claim requires {graha} in the {house}; "
                            f"this chart has it in the {actual}")


# ---------------------------------------------------------------------------
# Claim-level judgement -- the CLAIM's own words are the primary signal
# ---------------------------------------------------------------------------
# WHY THE CLAIM AND NOT THE CITED SOURCE. Measured on the S125 three-domain
# run: a cited SEGMENT often carries several verses, so a claim can inherit
# a coincidental match from a neighbouring verse it has nothing to do with.
# Real case -- `ch30_s001` was judged APPLICABLE for a claim about planets in
# the 9th, purely because some other verse in the same segment stated a
# 2nd-lord-in-2nd relation this chart satisfies. Judging the claim's own
# words removed every such false pass and changed no correct verdict. Cited
# sources are recorded as audit context only; they never decide.
def judge_claim(claim: dict, source_texts: dict[str, str],
                lord_house: dict[int, int]) -> ClaimVerdict:
    statement = str(claim.get("statement", ""))
    ids = claim.get("segment_ids") or []
    if not isinstance(ids, list):
        ids = [ids]
    ids = [str(i) for i in ids]
    sources = [judge_source(i, source_texts.get(i), lord_house) for i in ids]

    try:
        relation, why = read_condition(statement)
    except Exception as e:
        return ClaimVerdict(statement, ids, UNDETERMINED, sources, reason=(
            f"condition reader failed ({type(e).__name__}: {e}); "
            f"kept by fail-open"))

    if relation is None:
        return ClaimVerdict(statement, ids, UNDETERMINED, sources, reason=why)

    a, b = relation
    if lord_house.get(a) == b:
        return ClaimVerdict(statement, ids, APPLICABLE, sources, reason=(
            f"chart satisfies: lord of the {a} is in the {b}"))
    return ClaimVerdict(statement, ids, NOT_APPLICABLE, sources, reason=(
        f"claim requires the lord of the {a} in the {b}; "
        f"this chart has it in the {lord_house.get(a)}"))


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def _collect_source_texts(payload: dict) -> dict[str, str]:
    """segment_id / unit_id -> text, for everything actually SHIPPED.

    Whole-chapter units are included so a claim citing one resolves; in
    practice a whole chapter carries many conditions and will almost
    always come back APPLICABLE or UNDETERMINED, which is correct -- a
    chapter is context, not a single precondition.
    """
    texts: dict[str, str] = {}
    for u in payload.get("units", []) or []:
        if "unit_id" in u:
            texts[str(u["unit_id"])] = u.get("text", "") or ""
    for s in payload.get("segments", []) or []:
        if s.get("kept") and "segment_id" in s:
            texts[str(s["segment_id"])] = s.get("text", "") or ""
    return texts


def apply_silence_gate(interpreter_output: dict, payload: dict,
                       chart_facts: dict) -> GateResult:
    """Gate one interpreter answer. NEVER raises for a judgement problem.

    Returns a GateResult whose `kept_claims` is what should be shown and
    whose `silent_on` extends the interpreter's own list with the topics
    the gate removed.
    """
    try:
        lord_house = _lord_house_map(chart_facts)
        claims = interpreter_output.get("claims") or []
        if not isinstance(claims, list):
            raise SilenceGateError("interpreter_output['claims'] is not a list")
        source_texts = _collect_source_texts(payload)

        verdicts = [judge_claim(c, source_texts, lord_house)
                    for c in claims if isinstance(c, dict)]

        kept, dropped = [], []
        for claim, v in zip((c for c in claims if isinstance(c, dict)), verdicts):
            (dropped if v.verdict == NOT_APPLICABLE else kept).append(claim)

        silent = list(interpreter_output.get("silent_on") or [])
        if dropped:
            silent.append(
                "the classical text I have on some of these points describes "
                "placements this chart does not have, so I have left them out")

        # ADVISORY second pass (S129). Judges the planet-in-house shape and
        # RECORDS the result; it removes nothing. Its only job right now is to
        # produce the measured distribution that would justify promoting it to
        # enforcing -- including, critically, any claim it would have WRONGLY
        # dropped, which a human reads off the capture.
        planet_house = {p: v.get("house") for p, v in
                        (chart_facts.get("planet_positions") or {}).items()
                        if isinstance(v, dict)}
        advisory = []
        for claim, v in zip((c for c in claims if isinstance(c, dict)), verdicts):
            pv, why = judge_planet_claim(str(claim.get("statement", "")), planet_house)
            advisory.append({"statement": str(claim.get("statement", ""))[:160],
                             "advisory_verdict": pv, "reason": why,
                             "enforced_verdict": v.verdict})
        adv_counts = {f"advisory_{k}": sum(1 for a in advisory
                                           if a["advisory_verdict"] == k)
                      for k in (APPLICABLE, NOT_APPLICABLE, UNDETERMINED)}
        # The number that decides promotion: claims the enforcing gate KEPT
        # which the advisory reader would have dropped. Each one needs a human
        # to say whether the drop would have been right.
        adv_counts["advisory_would_drop_a_kept_claim"] = sum(
            1 for a, claim in zip(advisory, (c for c in claims if isinstance(c, dict)))
            if a["advisory_verdict"] == NOT_APPLICABLE and claim in kept)

        counts = {k: sum(1 for v in verdicts if v.verdict == k)
                  for k in (APPLICABLE, NOT_APPLICABLE, UNDETERMINED)}
        total = len(verdicts) or 1
        stats = {
            "claims_in": len(verdicts),
            "claims_kept": len(kept),
            "claims_dropped": len(dropped),
            **counts,
            **adv_counts,
            "planet_reader_mode": "advisory",
            "advisory_detail": advisory,
            # How much of the shipped answer this gate could not judge at
            # all. NOT a threshold -- a visibility metric. A high number
            # means the gate is mostly decorative for that question and the
            # human should know it, per Working Style #5.
            "ungated_pct": round(100 * counts[UNDETERMINED] / total, 1),
        }
        return GateResult(kept, dropped, verdicts, silent, stats)

    except Exception as e:
        # FAIL OPEN. The unmodified answer ships, the failure is on record.
        return GateResult(
            kept_claims=list(interpreter_output.get("claims") or []),
            dropped_claims=[],
            verdicts=[],
            silent_on=list(interpreter_output.get("silent_on") or []),
            stats={"claims_in": len(interpreter_output.get("claims") or []),
                   "gate_failed": True},
            error=f"{type(e).__name__}: {e}",
        )


def render_audit(result: GateResult) -> str:
    """Human-readable audit block for diagnostics/latest_run.md."""
    lines = [f"### Silence gate ({result.gate_version})", ""]
    if result.error:
        lines += [f"**GATE FAILED, answer shipped unmodified:** {result.error}", ""]
    s = result.stats
    lines += [
        f"claims in {s.get('claims_in')} -> kept {s.get('claims_kept')}, "
        f"dropped {s.get('claims_dropped')} "
        f"(applicable {s.get(APPLICABLE)}, not-applicable "
        f"{s.get(NOT_APPLICABLE)}, undetermined {s.get(UNDETERMINED)}; "
        f"{s.get('ungated_pct')}% of claims were unjudgeable)", "",
        "| verdict | claim | cites | why |", "|---|---|---|---|",
    ]
    for v in result.verdicts:
        # the CLAIM's reason, never a source note -- a source can
        # disagree with the verdict by design, and showing its note
        # here printed a "chart satisfies" rationale beside a DROP.
        why = v.reason
        lines.append(f"| {v.verdict} | {v.statement[:70]} | "
                     f"{','.join(v.segment_ids)} | {why[:90]} |")
    return "\n".join(lines)
