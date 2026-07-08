# Read Prompt

#Paste your instructions here. Then tell Claude: "Read .claude/read_prompt.md and execute"




MODEL: Sonnet 4.6

TASK: New test file only — tests/calculations/test_jaimini_arudha.py.
Do NOT touch agent/calculations/jaimini/arudha.py or any other file.
Mirror tests/calculations/test_jaimini_strength.py's structure and provenance discipline.

TARGET UNDER TEST:
  agent.calculations.jaimini.arudha.compute_arudha_pada(house_sign, planet_longitudes) -> ArudhaPadaResult
  Fields: house_sign, lord, lord_sign, co_lord_deciding_step, count, raw_ending_sign, exception_applied, arudha_sign

Use the same _SIGN_BASES / _dms_to_abs helper as test_jaimini_strength.py.

--- LAYER A: PVR Example 29 (book oracle, printed p.87 / PDF p.99) ---
First: open data/pdfs/"Vedic Astrology_ PVR Narashimha Rao.pdf" via pymupdf,
read Example 29 (Chart 1) + Example 30 (same chart), reconstruct the full
9-planet placement dict for Chart 1. PRINT that reconstructed dict in the
run report so it can be ratified before commit.
Then assert, for each of the 12 houses below, ONLY that
compute_arudha_pada(house_sign, chart1).arudha_sign equals the book value:
  Virgo->Gemini, Libra->Leo, Scorpio->Virgo, Sagittarius->Leo,
  Capricorn->Aries, Aquarius->Gemini, Pisces->Taurus, Aries->Capricorn,
  Taurus->Capricorn, Gemini->Virgo, Cancer->Taurus, Leo->Libra
Do NOT assert count/raw_ending_sign/co_lord_deciding_step here — inputs are
reconstructed, only arudha_sign is book-printed. Add a comment saying so.

--- LAYER B: step-5 exception (synthetic, expected values derived in design chat) ---
If ANY assert in this layer fails, STOP and paste the observed
ArudhaPadaResult in the report — do NOT change the expected values.
  B1 (1st-house trigger, distance 0): house_sign="Aries", Mars at 10.0deg
     (Aries). Expect count=1, raw_ending_sign="Aries",
     exception_applied=True, arudha_sign="Capricorn", lord="Mars".
  B2 (7th-house trigger, distance 6): house_sign="Gemini", Mercury at
     165.0deg (Virgo). Expect count=4, raw_ending_sign="Sagittarius",
     exception_applied=True, arudha_sign="Virgo", lord="Mercury".
  B3 (no exception, PVR's own inline example Gemini->Aquarius=9->Libra):
     house_sign="Gemini", Mercury at 315.0deg (Aquarius). Expect count=9,
     raw_ending_sign="Libra", exception_applied=False, arudha_sign="Libra".
For B1/B2/B3 fill the remaining 8 planet keys with any in-range distinct
longitudes (non-co-lorded house signs don't consult them).

--- LAYER C: co-lord dependency + propagation ---
  C1 (basic_rule, Scorpio): use SHERIDAN longitudes (copy the SHERIDAN dict
     verbatim from test_jaimini_strength.py). Ketu resident in Scorpio ->
     basic_rule picks Mars. Assert lord=="Mars",
     co_lord_deciding_step=="basic_rule". Do NOT assert arudha_sign as
     oracle (self-derived) — comment it as a routing check only.
  C2 (basic_rule, Aquarius): use SULABH dict verbatim. Rahu resident in
     Aquarius -> basic_rule picks Saturn. Assert lord=="Saturn",
     co_lord_deciding_step=="basic_rule".
  C3 (D2 propagation): synthetic chart with BOTH Mars and Ketu resident in
     Scorpio (e.g. Mars 210.0, Ketu 220.0; Rahu 40.0; fill the rest
     in-range). compute_arudha_pada("Scorpio", chart) must raise ValueError
     (strength.py's D2 fail-closed, propagated UNMODIFIED). Use pytest.raises
     and assert the message mentions "D2" or "both". arudha must not swallow it.

--- LAYER D: input contract ---
  Missing planet key -> raises. Bad house_sign ("Xyz") -> raises.
  Out-of-range longitude (>=360 or <0) -> raises. Mirror strength.py's paths.

--- LAYER E: result-shape locks ---
  ArudhaPadaResult is frozen (setattr raises FrozenInstanceError) and
  hashable (hash(result) works).

VERIFY: run full suite. Expected 3074 + this file's test count, 3 skipped,
0 failed. Report the new total and the per-layer pass counts. Overwrite
diagnostics/latest_run.md. Do NOT commit yet — paste the report (including
the reconstructed Example 29 dict) for review first.