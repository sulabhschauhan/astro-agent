# Read Prompt

#Paste your instructions here. Then tell Claude: "Read .claude/read_prompt.md and execute"

MODEL: Sonnet 4.6

TASK: Implement agent/calculations/jaimini/rasi_aspects.py — new file,
ONE FILE ONLY. No test file, no other module touched.

Read CLAUDE.md first. THEN read the CURRENT diagnostics/latest_run.md
(rasi drishti extraction) BEFORE anything else — you will transfer
its verbatim material into this module's docstring, because your own
run will overwrite that diagnostics file.

SPEC (PVR Ch.10 §10.3, printed p.102 — verbatim in current
diagnostics/latest_run.md):
- Movable signs (Ar, Cn, Li, Cp) aspect the three fixed signs
  EXCEPT the one adjacent to them.
- Fixed signs (Ta, Le, Sc, Aq) aspect the three movable signs
  EXCEPT the one adjacent to them.
- Dual signs (Ge, Vi, Sg, Pi) aspect the other three duals.
- Symmetry is explicit in PVR: quote it in the CITATION block.

DESIGN (locked):
1. Derive the aspect sets PROGRAMMATICALLY from sign-class +
   adjacency at module import (module-level frozen structure) — do
   NOT hand-type a 12-row literal table. Rationale comment: PVR
   prints the rule + 3 worked rows, not a full table; the rule is
   the source-verbatim artifact.
2. Public API:
   - signs_rasi_aspected_by(sign: str) -> frozenset[str]
   - rasi_aspects_between(sign_a: str, sign_b: str) -> bool
   Canonical Title-case sign names, same vocabulary as aspects.py.
   Unknown sign -> ValueError naming it. Case-sensitive, consistent
   with aspects.py's existing contract.
3. Module docstring:
   - LOUD warning: this is Jaimini RASI drishti (sign aspects),
     NOT graha drishti — never interchangeable with
     calculations/aspects.py; consumers: §15.5.1 stronger-co-lord
     step 2, arudha layer.
   - CITATION block: verbatim §10.3 rule text, the symmetry
     sentence, the planets-carry-the-sign's-aspect sentences, the
     three PVR worked sign-rows (Ar/Ta/Ge), AND the full Exercise
     15 answer key rows — all copied exactly from the current
     diagnostics/latest_run.md with printed+PDF page numbers.
     Include PVR's Ketu-anti-zodiacal note with its scope flag
     (Argala only, NOT rasi drishti — Exercise 15's Ketu row is
     the proof).
4. Pure functions, no ephemeris, no imports from aspects.py.

VERIFY: full suite — expect 2972 passed / 3 skipped / 0 failed,
zero delta (nothing imports this new module yet). THEN overwrite
diagnostics/latest_run.md with the run report. Commit
"P6 Jaimini: rasi drishti primitive (PVR Ch.10 §10.3)". Push.