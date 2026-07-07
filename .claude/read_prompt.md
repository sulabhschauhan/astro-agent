# Read Prompt

#Paste your instructions here. Then tell Claude: "Read .claude/read_prompt.md and execute"

MODEL: Sonnet 4.6

TASK: Create tests/calculations/test_jaimini_rasi_aspects.py. ONE
FILE. Read CLAUDE.md first. Do not modify rasi_aspects.py — any
failure means STOP and report, no fix-forward.

ORACLE SOURCES:
(a) PVR's 3 printed worked rows (Ch.10 §10.3, design-chat derived
    from the ratified rule + adjacency, and quoted verbatim in
    rasi_aspects.py's CITATION block):
    Aries   -> {Leo, Scorpio, Aquarius}
    Taurus  -> {Cancer, Libra, Capricorn}
    Gemini  -> {Virgo, Sagittarius, Pisces}
(b) PVR Exercise 15 answer key — transcribe ALL 9 rows EXACTLY as
    quoted in rasi_aspects.py's CITATION block into test fixtures.
    If any CITATION row disagrees with the module's computed table,
    that is a genuine falsification — STOP and report, do not
    reconcile silently.

TESTS (in order):
1. Three worked-row oracle tests: signs_rasi_aspected_by(sign) ==
   frozenset from (a), one test each, hard-coded sets from (a) —
   do NOT recompute them from the rule inside the test.
2. Exercise 15 oracle tests: one parametrized test over the 9
   transcribed rows from (b), asserting the module's answer matches
   PVR's answer key exactly (including the Ketu row — ordinary
   zodiacal counting; comment: the anti-zodiacal rule is
   argala-scoped, per CITATION).
3. Exhaustive symmetry sweep: all 144 ordered sign pairs,
   rasi_aspects_between(a, b) == rasi_aspects_between(b, a).
4. Structural locks, full 12-sign sweeps:
   - every aspect set has exactly 3 members
   - movable signs aspect only fixed signs; fixed only movable;
     dual sets == the other three duals exactly
   - no sign aspects an adjacent sign
   - no sign aspects itself (rasi_aspects_between(x, x) is False
     for all 12 — contract lock, comment it as such)
5. Return-type lock: signs_rasi_aspected_by returns a frozenset
   for all 12 signs.
6. Error paths, message-content asserts: unknown sign ("Atlantis")
   in each public function -> ValueError naming it; case
   sensitivity ("ARIES" rejected) consistent with aspects.py's
   existing contract.
7. Cross-system guard test: import signs_aspected_by from
   calculations.aspects and assert that for at least Aries the
   graha-drishti result of a planet placed there differs from the
   rasi-drishti set (e.g. Sun in Aries aspects only Libra under
   graha drishti — disjoint from {Le, Sc, Aq}). Comment: tripwire
   against future accidental unification of the two systems.

VERIFY: full suite. Baseline 2972 passed / 3 skipped / 0 failed
must lose nothing; REPORT measured new totals. Overwrite
diagnostics/latest_run.md. Commit "P6 Jaimini: rasi drishti
oracle tests (PVR Ch.10 §10.3 + Exercise 15)". Push.