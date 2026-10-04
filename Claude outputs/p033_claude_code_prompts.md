# P-033 — Claude Code build prompts (S139)

Branch base: `wip/interpretive-pilot @ 11d4f91`. Detector 144 rows, suite 4480/7/0.

**Build design (locked, roster-passed):** silences become checkable. The interpreter
declares *why* it withheld each item in the closed predicate vocabulary; Python
evaluates that condition against the computed chart with the **inverted** mapping
(a silence asserts the condition *fails*, so `SATISFIED` = the reason is
chart-refuted = a caught miss). **Recording only** — no answer is changed, no turn
fails yet; promotion to enforcing is gated on the live mistyping/adoption rate.
Python does arithmetic only; the condition is always declared by the LLM, never
parsed from prose. `silent_on` keeps its `list[str]` type for `_render`/`composer`;
the typed structure is a parallel field.

**The gate logic below was unit-tested in the cloud against the real
`predicates.py`: 13/13, incl. compound, partial-unevaluable, navamsa fragility
guard, malformed fail-safe, and the live ch15_s003 defect.** Apply it verbatim.

**RATIFIED protocol (WS#14):** these prompts do NOT contain `RATIFIED: commit
authorized`. Each instructs Claude Code to STOP before committing and report the
diff + suite result for your review. Re-run with the token appended only when you
want the commit made. Do them in order.

---

## PROMPT 1 — `silence_gate.py`: `judge_silence` + recording wiring + tests

```
MODEL: Sonnet (routine two-file implementation of pre-designed, cloud-tested code — not Opus).
DECISION THIS SERVES: if judge_silence records a CAUGHT_MISS on the ch15_s003 fixture and the full suite stays green, then P-033's silence check is live in recording mode; else STOP and report.
TOKEN CEILING: 40k. If you approach it, STOP and report where you are.
Write your run output to diagnostics/latest_run.md (truncate first; runs/<ts>.md then cp per rule 26). Chat gets a <=10-line summary with test counts.

TASK — ONE FILE (agent/astro/silence_gate.py) + its test file. Do not touch interpreter.py, predicates.py, pipeline.py, composer.py.

This adds silence judging in RECORDING mode. It must not change kept_claims,
dropped_claims, silent_on, or any existing verdict. Additive only.

1. Add these three definitions to agent/astro/silence_gate.py (predicates is
   already imported there as PRED). Place them after the ClaimVerdict dataclass:

# --- P-033: silence judging (recording mode) --------------------------------
# A silence is a NEGATIVE claim: "I withheld this because condition C does not
# hold." So the PRED verdict maps OPPOSITE to judge_claim:
#   PRED.CONTRADICTED -> C genuinely fails      -> JUSTIFIED   (silence was right)
#   PRED.SATISFIED    -> C HOLDS                 -> CAUGHT_MISS (reason is chart-refuted)
#   PRED.UNEVALUABLE  -> cannot decide           -> UNCHECKABLE (keep silent; S124)
# Python does arithmetic only; the condition (withheld_because) is declared by
# the interpreter, never parsed from prose here.
JUSTIFIED = "justified"
CAUGHT_MISS = "caught_miss"
UNCHECKABLE = "uncheckable"

# A CAUGHT_MISS alarm may rest ONLY on resolution-stable predicates. navamsa_*
# partitions a sign into 3deg20' cells that flip on a ~1deg ayanamsa/birth-time
# error, so a would-be CAUGHT_MISS resting on one is held to UNCHECKABLE until
# item 2's per-planet boundary_flag exists (Ephemeris Auditor, S138 HIGH).
_FRAGILE_PRED_TYPES = frozenset({"navamsa_sign", "navamsa_dignity"})


@dataclass
class SilenceVerdict:
    topic: str
    segment_ids: list
    verdict: str
    note: str = ""
    decided_by: str = "prose"          # "typed" once withheld_because was evaluated
    predicate_detail: list = field(default_factory=list)
    uncovered_tokens: list = field(default_factory=list)  # advisory, silence-side P-032
    downgraded_fragile: bool = False   # SATISFIED held back on a fragile predicate


def _normalize_silence(s):
    """Accept a legacy bare string OR the new structured entry. Never raises."""
    if isinstance(s, str):
        return s, [], None, s
    if isinstance(s, dict):
        topic = str(s.get("topic") or s.get("note") or "")
        seg = [str(i) for i in (s.get("segment_ids") or [])]
        wb = s.get("withheld_because")
        note = str(s.get("note") or "")
        return topic, seg, (wb if isinstance(wb, list) else None), note
    return str(s), [], None, ""


def judge_silence(silence, chart_facts=None) -> SilenceVerdict:
    """Evaluate ONE withheld item against the chart. Never raises. Reuses
    PRED.evaluate_claim, then maps its verdict THROUGH THE INVERSION above."""
    topic, seg, wb, note = _normalize_silence(silence)
    if not wb:                          # legacy string or no declared condition
        return SilenceVerdict(topic, seg, UNCHECKABLE, note=note, decided_by="prose")
    res = PRED.evaluate_claim(wb, chart_facts or {})
    pred_rows = res.get("predicates", [])
    cov = PRED.statement_coverage(note, wb)
    v = res["verdict"]
    if v == PRED.CONTRADICTED:
        verdict, fragile = JUSTIFIED, False
    elif v == PRED.SATISFIED:
        if {r.get("type") for r in pred_rows} & _FRAGILE_PRED_TYPES:
            verdict, fragile = UNCHECKABLE, True
        else:
            verdict, fragile = CAUGHT_MISS, False
    else:
        verdict, fragile = UNCHECKABLE, False
    return SilenceVerdict(topic, seg, verdict, note=note, decided_by="typed",
                          predicate_detail=pred_rows, uncovered_tokens=cov["uncovered"],
                          downgraded_fragile=fragile)

2. Extend GateResult: add `silence_verdicts: list = field(default_factory=list)`
   and, in to_dict(), add `d["silence_verdicts"] = [asdict(s) for s in self.silence_verdicts]`.

3. In apply_silence_gate(), AFTER the existing claim verdict/kept/dropped block
   and BEFORE building `stats`, add (do not alter anything above it):

   # P-033 recording pass. Prefer the interpreter's structured `silences`; fall
   # back to the silent_on strings (each -> UNCHECKABLE). Judges nothing about
   # claims; records only.
   raw_silences = interpreter_output.get("silences")
   if not isinstance(raw_silences, list) or not raw_silences:
       raw_silences = list(interpreter_output.get("silent_on") or [])
   silence_verdicts = [judge_silence(s, chart_facts) for s in raw_silences]

   Then add these keys into the `stats` dict:
   "silences_in": len(silence_verdicts),
   "silences_typed": sum(1 for s in silence_verdicts if s.decided_by == "typed"),
   "silences_caught_miss": sum(1 for s in silence_verdicts if s.verdict == CAUGHT_MISS),
   "silences_justified": sum(1 for s in silence_verdicts if s.verdict == JUSTIFIED),
   "silences_uncheckable": sum(1 for s in silence_verdicts if s.verdict == UNCHECKABLE),
   "silences_fragile_downgraded": sum(1 for s in silence_verdicts if s.downgraded_fragile),
   "silence_detail": [{"topic": s.topic[:160], "verdict": s.verdict,
                       "decided_by": s.decided_by, "segment_ids": s.segment_ids,
                       "uncovered_tokens": s.uncovered_tokens,
                       "downgraded_fragile": s.downgraded_fragile}
                      for s in silence_verdicts],

   And pass silence_verdicts into the GateResult(...) constructor at the end of
   the try block (add `silence_verdicts=silence_verdicts`). The fail-open
   GateResult in the except stays as-is (empty silence_verdicts by default).

4. Create tests/astro/test_silence_judge.py with the matrix below (adjust the
   import to `from agent.astro.silence_gate import judge_silence, SilenceVerdict,
   JUSTIFIED, CAUGHT_MISS, UNCHECKABLE`). This exact matrix passed 13/13 against
   the real predicates.py in isolation:

<PASTE THE TEST BODY FROM SECTION "TEST MATRIX" BELOW>

5. Run: pytest tests/astro/test_silence_judge.py -q, THEN the full suite
   (pytest -q). Both must be green; the full suite must stay at its current
   count with the new tests added (it was 4480/7/0 before this file).
6. If green: STOP. Report the diff summary and both test counts to
   diagnostics/latest_run.md and a <=10-line chat summary. DO NOT COMMIT unless
   this prompt contains the line 'RATIFIED: commit authorized'.
```

---

## PROMPT 2 — `interpreter.py`: emit structured silences + fix stale banner

```
MODEL: Sonnet.
DECISION THIS SERVES: if the interpreter emits a parsable `silences` array whose withheld_because entries pass PRED.validate_precondition, and the full suite stays green, the emission contract is live; else STOP and report.
TOKEN CEILING: 40k. STOP if approached.
Write output to diagnostics/latest_run.md (truncate; runs/<ts>.md then cp). <=10-line chat summary.

TASK — ONE FILE (agent/astro/interpreter.py) + its test file (tests/astro/test_interpreter.py). Nothing else.

CONTEXT: silence_gate.judge_silence (Prompt 1, already landed) reads a structured
`silences` field. This prompt makes the interpreter emit it, while keeping
`silent_on` as the list[str] that pipeline._render and composer already consume.

1. Fix the STALE BANNER at the top of the module docstring. Replace the
   "PATH B / LAB TRACK -- NOT WIRED TO THE PRODUCT (S128 lock) ... Changing this
   file ships NOTHING to users" block with:

     PATH B IS THE PRODUCT (S129 cutover). THIS MODULE IS LIVE.
     agent/astro/pipeline.answer_question (frontend/app.py:40) calls interpret()
     at pipeline.py:332. A change here SHIPS TO USERS. Path A
     (agent/infra/orchestrator) is the retained revert target, wired to no UI.
     SUPERSEDES the S128 "not wired" banner, false since S129.

2. In _SYSTEM_HEAD, change the JSON shape line for silent_on from a string array
   to an object array, and replace the "INTERNAL DIAGNOSTICS" note with the
   silence contract. New shape line:
     '"silent_on": [{"topic": "<what you did not state>", "segment_ids": ["<id>"], "withheld_because": [<preconditions>], "note": "<terse verse id + missing precondition>"}], "refused": false}\n'
   New contract block (append after the preconditions instructions):
     "`silent_on` records each verse or point you did NOT turn into a claim because "
     "its chart condition looks unmet. For each, give `withheld_because`: the SAME "
     "closed-vocabulary preconditions you would have declared had you made the claim "
     "-- the exact condition whose failure is your reason for staying silent. These "
     "are checked against the computed chart; if a condition you call unmet actually "
     "HOLDS, that is a silent miss. State the real condition at full strength, and "
     "NEVER withhold a verse whose condition you have not checked against the facts. "
     "A condition not expressible in the vocabulary -> one `unfittable` with a note. "
     "Silent for a NON-chart reason (verses don't address the question, or need a "
     "fact we don't compute) -> give `note` only, no `withheld_because`.\n"

3. In interpret(), replace the `"silent_on": list(obj.get("silent_on") or [])`
   line with a parse loop that ghost-guards silence citations and validates
   withheld_because via PRED.validate_precondition (mirror the existing claims
   loop's use of PRED.validate_precondition and `ids`). Produce BOTH:
     - `silences`: [{topic, segment_ids (real ids only), withheld_because
       (validated), note}], tolerating a legacy bare string (-> {topic:s,
       segment_ids:[], withheld_because:[], note:s}).
     - `silent_on`: derived list[str], one per silence: `f"{topic}: {note}"`
       when note adds to topic, else topic or note. THIS KEEPS THE list[str]
       CONTRACT for _render and composer.
   Add to the return dict: `"silences": clean_silences`, keep `"silent_on":
   silent_on_strings`, and add `"silences_with_preconditions": sum(1 for s in
   clean_silences if s["withheld_because"])`. Route any rejected silence
   precondition into the existing `precondition_rejects` list with a
   `"where": "silence"` marker.

4. Update tests/astro/test_interpreter.py: add cases that a stubbed interpreter
   returning structured silent_on objects yields a `silences` array with
   validated withheld_because and a derived list[str] `silent_on`; that a legacy
   bare-string silent_on still parses; that an illegal withheld_because predicate
   is dropped (not raised) and recorded. Keep existing tests green.

5. Run pytest tests/astro/test_interpreter.py -q then full pytest -q. Both green.
6. STOP. Report to latest_run.md + <=10-line chat summary. DO NOT COMMIT unless
   this prompt contains 'RATIFIED: commit authorized'.
```

---

## PROMPT 3 — `CLAUDE.md` row-count fix (docs, no RATIFIED needed)

```
MODEL: Haiku (single-line docs edit).
TASK — docs only. In CLAUDE.md's "Current Session Focus" (S138) line, change
"detector 64 -> 128" to "detector 64 -> 128 -> 144 (two S138 batches; 144 is the
module total, 47 unsourced)" and remove the trailing "Uncommitted on
`wip/interpretive-pilot`" (it committed at 11d4f91). Surgical string replacement,
assert exactly one match. No pytest (docs-only, WS#15). Commit as a docs change
(exempt from the RATIFIED token).
```

---

## TEST MATRIX (paste into Prompt 1, step 4)

```python
import pytest
from agent.astro.silence_gate import (
    judge_silence, SilenceVerdict, JUSTIFIED, CAUGHT_MISS, UNCHECKABLE,
)

# Mars = 5th lord, Exalted (ch15_s003 case). 11th lord in the 6th (ch24_s108).
CHART = {
    "ascendant_sign": "Virgo",
    "lord_house_map": {11: 6, 5: 10, 8: 8},
    "house_lords": {5: {"lord": "Mars", "sign": "Capricorn"}},
    "planet_positions": {
        "Mars": {"house": 10, "sign": "Capricorn", "dignity": "Exalted"},
        "Saturn": {"house": 7, "sign": "Aries"},
        "Jupiter": {"house": 3, "sign": "Scorpio"},
    },
    "navamsa": {"placements": {"Mars": {"house": 1, "sign": "Aries", "dignity": "Exalted"}}},
    "yogas": {"fired": [{"id": "adhi"}], "ruled_out": [{"id": "gajakesari_yoga"}]},
}

def test_compound_all_hold_is_caught_miss():
    s = {"topic": "x", "note": "needs Saturn 7 and Mars 10", "withheld_because": [
        {"type": "planet_in_house", "graha": "Saturn", "house": 7},
        {"type": "planet_in_house", "graha": "Mars", "house": 10}]}
    assert judge_silence(s, CHART).verdict == CAUGHT_MISS

def test_compound_one_fails_is_justified():
    s = {"topic": "x", "note": "needs Saturn 7 and Mars 7", "withheld_because": [
        {"type": "planet_in_house", "graha": "Saturn", "house": 7},
        {"type": "planet_in_house", "graha": "Mars", "house": 7}]}
    assert judge_silence(s, CHART).verdict == JUSTIFIED

def test_partial_unevaluable_never_alarms():
    s = {"topic": "x", "note": "needs Saturn 7 and Venus exalted", "withheld_because": [
        {"type": "planet_in_house", "graha": "Saturn", "house": 7},
        {"type": "planet_dignity", "graha": "Venus", "dignity": "Exalted"}]}
    v = judge_silence(s, CHART)
    assert v.verdict == UNCHECKABLE and v.downgraded_fragile is False

def test_navamsa_satisfied_is_downgraded_not_alarmed():
    s = {"topic": "x", "note": "needs Mars exalted in navamsa", "withheld_because": [
        {"type": "navamsa_dignity", "graha": "Mars", "dignity": "Exalted"}]}
    v = judge_silence(s, CHART)
    assert v.verdict == UNCHECKABLE and v.downgraded_fragile is True

def test_ch15_s003_caught_miss():
    s = {"topic": "housing (ch15 v3)", "segment_ids": ["ch15_s003"],
         "note": "needs 5th lord own sign/navamsa or exalted; not met here",
         "withheld_because": [{"type": "planet_dignity", "graha": "Mars", "dignity": "Exalted"}]}
    v = judge_silence(s, CHART)
    assert v.verdict == CAUGHT_MISS and v.decided_by == "typed"

def test_ch24_s108_lord_in_house_justified():
    s = {"topic": "11th lord in 12th", "segment_ids": ["ch24_s108"],
         "note": "11th lord in the 12th; here it is in the 6th",
         "withheld_because": [{"type": "lord_in_house", "lord_of": 11, "house": 12}]}
    assert judge_silence(s, CHART).verdict == JUSTIFIED

def test_dasha_unfittable_is_uncheckable():
    s = {"topic": "maraka timing", "note": "requires dasha timing not provided",
         "withheld_because": [{"type": "unfittable", "note": "dasha timing"}]}
    assert judge_silence(s, CHART).verdict == UNCHECKABLE

def test_yoga_fired_silence_is_caught_miss():
    s = {"topic": "adhi", "note": "adhi not present",
         "withheld_because": [{"type": "yoga_fired", "yoga_id": "adhi"}]}
    assert judge_silence(s, CHART).verdict == CAUGHT_MISS

def test_legacy_bare_string_is_uncheckable_prose():
    v = judge_silence("ch15_s006: requires multiple placements not present", CHART)
    assert v.verdict == UNCHECKABLE and v.decided_by == "prose"

def test_empty_withheld_because_is_uncheckable():
    assert judge_silence({"topic": "off topic", "note": "off topic"}, CHART).verdict == UNCHECKABLE

def test_malformed_never_raises():
    for junk in (None, 42, [], {"withheld_because": "not a list"},
                 {"withheld_because": [{"type": "no_such_pred"}]},
                 {"withheld_because": [{"type": "planet_dignity"}]}):
        v = judge_silence(junk, CHART)
        assert v.verdict in (JUSTIFIED, CAUGHT_MISS, UNCHECKABLE)
        assert v.verdict != CAUGHT_MISS

def test_no_chart_facts_is_uncheckable():
    s = {"topic": "x", "withheld_because": [{"type": "planet_dignity", "graha": "Mars", "dignity": "Exalted"}]}
    assert judge_silence(s, {}).verdict == UNCHECKABLE

def test_advisory_uncovered_tokens_recorded_never_acted():
    s = {"topic": "x", "note": "the 5th lord and Jupiter both matter",
         "withheld_because": [{"type": "planet_dignity", "graha": "Mars", "dignity": "Exalted"}]}
    v = judge_silence(s, CHART)
    assert v.verdict == CAUGHT_MISS and "Jupiter" in v.uncovered_tokens
```

---

## After the two source prompts land: the live validation (your machine)

Run the Streamlit app on the reference chart, ask the ch15/property question that
produced capture 20260919T122618Z, and read `gate_stats` in the capture:

- **`silences_caught_miss` >= 1 and the ch15_s003 item shows `caught_miss`** — the
  defect is now caught.
- **`silences_typed / silences_in`** — the adoption rate. If it's low, the
  interpreter isn't declaring `withheld_because` and the check is near-inert; that's
  a prompt-iteration problem (same shape as the yoga_catalogue fix that lifted
  yoga_fired usage), not a code bug.
- **`silence_detail` uncovered_tokens / downgraded_fragile** — the mistyping and
  fragility signals.

**That rate is the gate for promoting to "fails the turn" (option F).** Recording
mode ships first; enforcement waits for a clean measured rate. This is the S129b
planet-reader discipline, and the reason I did not enforce in one step.
