# Read Prompt

#Paste your instructions here. Then tell Claude: "Read .claude/read_prompt.md and execute"



Model: Sonnet 4.6
Task: Implement Yogini MD computation in agent/calculations/dashas/
yogini.py and its unit test in tests/test_yogini_dasha.py. Two-file
exception to the one-file rule: module + its unit test are tightly
coupled; splitting creates a broken red-suite intermediate state
that would violate the never-push-red rule if committed between.

## 1. Module contract — agent/calculations/dashas/yogini.py

Replace the current stub docstring. Implement:

    from dataclasses import dataclass
    from typing import Sequence

    @dataclass(frozen=True)
    class YoginiPeriod:
        lord: str          # "Jup" | "Mars" | "Merc" | "Sat" | "Ven"
                           # | "Rah" | "Moon" | "Sun" (match Vimshottari
                           # lord string convention — verify against
                           # chart_calculator.py:_calc_dasha() before
                           # coding; mirror exactly, don't invent)
        yogini_name: str   # "Dhanya" | "Bhramari" | "Bhadrika" | "Ulka"
                           # | "Siddha" | "Sankata" | "Mangala" | "Pingala"
        begin_jd: float    # Julian Day UT
        end_jd: float      # Julian Day UT
        years: int         # 1..8, integer years per Yogini rule

    def compute_yogini_dasha(
        natal_moon_lon_sidereal: float,  # degrees, 0..360
        birth_jd_ut: float,
        n_cycles: int = 3,               # 3 × 36 = 108 years coverage
    ) -> list[YoginiPeriod]:
        ...

    def current_yogini_md(
        periods: Sequence[YoginiPeriod],
        query_jd_ut: float,
    ) -> YoginiPeriod | None:
        ...

## 2. Locked constants

Yogini cycle in order (index 0..7):

    _YOGINIS = [
        ("Mangala",  "Moon",  1),
        ("Pingala",  "Sun",   2),
        ("Dhanya",   "Jup",   3),
        ("Bhramari", "Mars",  4),
        ("Bhadrika", "Merc",  5),
        ("Ulka",     "Sat",   6),
        ("Siddha",   "Ven",   7),
        ("Sankata",  "Rah",   8),
    ]
    # Sum of years = 36. Full cycle = 36y. Source: PVR
    # "Vedic Astrology: An Integrated Approach", Yogini Dasa section.

Year length: 365.25 days (Julian year). Match Vimshottari convention
in chart_calculator.py; do NOT introduce a new year-length constant.

## 3. Starting-lord formula (validated against ONE chart only)

    starting_index = (nakshatra_number + 2) % 8
    # nakshatra_number is 1-indexed from Ashwini (1) to Revati (27).
    # Sulabh's Vishakha (16) → (16 + 2) % 8 = 2 → Dhanya (Jupiter). ✓
    # Validated against jhora_sulabh.md Yogini MD sequence
    # (Session 72 fixture extension).

Docstring on the function MUST include this caveat verbatim:

    # CAVEAT: The (nakshatra_number + 2) % 8 formula is validated
    # against ONE reference chart (Sulabh, Vishakha → Dhanya).
    # Alternative formulations exist in classical sources (Saravali,
    # Muhurtha Chinthamani variants). Surbhi/Sheridan/David
    # validation pending external JHora fetch. If any of those
    # charts fails this formula, revisit before treating it as
    # locked.

## 4. Balance-at-birth

Use existing _nakshatra(lon) helper from agent/chart_calculator.py:140
(import it — do not duplicate). It returns nakshatra_number and pada.
For fraction traversed:

    nak_span_deg = 360.0 / 27.0            # 13°20'
    nak_start_deg = (nakshatra_number - 1) * nak_span_deg
    fraction_traversed = (
        (natal_moon_lon_sidereal - nak_start_deg) / nak_span_deg
    )
    balance_years = (1.0 - fraction_traversed) * starting_lord_years
    balance_days = balance_years * 365.25

## 5. Cycle emission

- Period 1: starting lord, begin = birth_jd_ut,
  end = birth_jd_ut + balance_days.
- Periods 2..N: next lord in cycle, duration = lord_years * 365.25.
- Emit until n_cycles × 8 = 24 periods (default).

## 6. Test file — tests/test_yogini_dasha.py

Use existing chart-fixture pattern from tests/. Import Sulabh birth
data from wherever it's canonically defined (grep for "1988-04-06"
or "Calcutta" in existing test files to find the canonical fixture;
do NOT re-transcribe birth data).

Tests:

  def test_starting_lord_sulabh_vishakha_to_dhanya():
      # Vishakha (16) must map to Dhanya (Jup).

  def test_first_md_balance_at_birth():
      # First MD end date within ±1 day of 1988-07-06 (JHora fixture).

  def test_md_sequence_matches_jhora_fixture():
      # Parse jhora_sulabh.md Yogini section. Compare all 24 MDs:
      # lord match exact; begin/end JDs within ±1 day.
      # Load fixture path: tests/fixtures/jhora_sulabh.md.
      # Simple markdown table parser (no new dependency).

  def test_cycle_order_repeats():
      # Assert period[i].lord == period[i+8].lord for i in range(16).

  def test_current_md_lookup_today():
      # As of 2026-07-24, current MD lord must be "Mars"
      # (2024-07-06 → 2028-07-06 per fixture).

  @pytest.mark.xfail(
      reason="Formula validated against Sulabh only; "
             "external Yogini fetch pending for other charts."
  )
  def test_starting_lord_surbhi(): ...
  @pytest.mark.xfail(reason="same")
  def test_starting_lord_sheridan(): ...
  @pytest.mark.xfail(reason="same")
  def test_starting_lord_david(): ...

## 7. What NOT to touch

- calc_router.py: leave _UNBUILT_MODULE_KEYWORDS untouched (Yogini
  stays refused at routing layer until Prompts 3 and 4 wire it).
- chart_profile.py, result_formatter.py: no changes.
- orchestrator.py: no changes.
- chart_calculator.py: no changes (Vimshottari stays where it is;
  migration is out of scope for V1.1).
- CLAUDE.md: no docs changes in this commit (documentation-drift
  note about dashas/ stubs deferred to a separate docs commit).

## 8. Verification

- pytest tests/test_yogini_dasha.py -x — must be 5 passed, 3 xfailed.
- pytest -x — full suite must be baseline + 5 = 3286 passed, 0 failed,
  7 skipped, 3 xfailed. Any deviation = STOP, report, no commit.
- Import check: python -c "from agent.calculations.dashas.yogini
  import compute_yogini_dasha, current_yogini_md, YoginiPeriod".

## 9. Commit

Two files touched: agent/calculations/dashas/yogini.py +
tests/test_yogini_dasha.py. Single commit.
Message: "S72: Yogini dasha module + unit tests (formula validated
against Sulabh only; xfail markers for other charts)"
Do NOT push. Report diff before committing. Ratification token
required: send "RATIFIED: commit authorized" after diff review.