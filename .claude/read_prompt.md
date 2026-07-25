# Read Prompt

#Paste your instructions here. Then tell Claude: "Read .claude/read_prompt.md and execute"

Model: Sonnet 4.6
Task: S74 Prompt 4 — pyjhora source read. Explain the row-0 fixed-
   offset spread in Vimshottari (Sulabh +4.25d, Surbhi +11.15d,
   Sheridan +3.80d, David +1.47d — §7-§8 of diagnostics/
   vimshottari_year_length_S74.md, verdict (c) unresolved) by reading
   the actual pyjhora implementation. Diagnostic markdown, no
   production code touched.

## 1. Locate pyjhora

Grep the repo for pyjhora — likely at astroagent/pyjhora/ or vendored
under a third_party/ or references/ path. Report the path and confirm
it is a Python port/source of JHora v8's dasha calculations (as
opposed to a stub, README-only folder, or unrelated package).

If pyjhora is NOT present, STOP and report — do not fall back to
web sources without design-chat approval.

## 2. Read balance-at-birth logic in pyjhora

Locate pyjhora's Vimshottari Mahadasha calculation. Identify:

- Which Moon longitude value it uses (which ayanamsa, which
  ephemeris precision, whether it applies a mean-vs-true correction).
- How it computes fraction_traversed within the natal nakshatra.
- How it converts fraction_traversed to balance_years / balance_days.
- Which year-length constant it uses (365.25 / 365.2422 / 365.256363
  / other).
- Whether the balance-at-birth calculation differs between the
  Vimshottari and Yogini panels within pyjhora itself (§4 of our
  diagnostic hypothesized independence; pyjhora will either confirm
  or refute).

Cite file:line for every claim.

## 3. Compare against our _calc_dasha

For each of the 4 mechanism-level questions in §2 above, produce a
side-by-side table:

    | Aspect          | Our code (file:line) | pyjhora (file:line) | Match? |
    | Moon longitude  |                      |                     |        |
    | Ayanamsa flag   |                      |                     |        |
    | fraction calc   |                      |                     |        |
    | year constant   |                      |                     |        |
    | Yogini shares?  |                      |                     |        |

## 4. Apply pyjhora's logic to Sulabh row-0 by hand

Using pyjhora's exact formulae, compute Sulabh's Vimshottari MD1
end_jd. Compare to:
- Our code's output: 2447740.008403 (Julian) / 2447740.016817 (sidereal)
- JHora GUI fixture: 2447735.756910

If pyjhora's computed value matches the JHora GUI to within seconds,
we've located the mechanism — report which specific difference from
our _calc_dasha accounts for the +4.25d gap.

If pyjhora's computed value matches OUR code (not the GUI), then the
JHora GUI's Vimshottari panel is using a different engine than
pyjhora — report that as a finding (surprising, and would explain
the "two black boxes" §4 hypothesis).

## 5. Diagnostic markdown extension

File: diagnostics/vimshottari_year_length_S74.md

Append §11 — "pyjhora source audit":
- Path to pyjhora, confirmation it is the JHora reference source.
- Mechanism side-by-side table from §3.
- Sulabh row-0 hand-computation result from §4.
- Verdict: mechanism located / partially located / not located.
- If located: recommended fix for _calc_dasha (do NOT implement here).
  Include estimated blast radius (files touched, golden fixtures
  affected, envelope tightening candidate).

## 6. What NOT to touch

- agent/chart_calculator.py — read-only.
- agent/calculations/dashas/*.py — read-only.
- pyjhora source — read-only (do not modify vendored code).
- Any test file — read-only.
- Any production module — read-only.

## 7. Commit

Single commit:
   diagnostic: S74 pyjhora source audit — Vimshottari balance-at-birth
               mechanism

Files staged: diagnostics/vimshottari_year_length_S74.md only.

No RATIFIED token — diagnostic append.

## 8. Report back

1. pyjhora path + confirmation
2. Mechanism side-by-side table verbatim
3. Sulabh row-0 hand-computation result
4. Verdict (located / partial / not located)
5. If located: proposed fix summary + blast radius
6. git status + git log origin/main..HEAD --oneline