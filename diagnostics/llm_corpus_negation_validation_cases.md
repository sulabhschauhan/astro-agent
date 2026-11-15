# LLM corpus-application validation cases (negation / promise / nullifiers)

Pinned for the live-validation batch. Purpose: the deterministic ranker is a
SHORTLISTER + strength facts; the DOCTRINE (negation houses, promise, combustion,
delay) lives in the corpus and is applied by the interpreter. These cases check
whether the LLM actually applies that corpus doctrine to facts the block already
carries -- NOT whether the ranker scores them.

## Architecture decision (ratified by Sulabh, 15 Nov)
Do NOT code negation / promise / nullifier RULES into the ranker -- that is
per-scenario patchwork that will not generalise. The ranker stays a convergence
shortlister + universal strength facts (incl. KP-tier weighting, S161). The corpus
+ LLM applies the meaning. New doctrine in the corpus is then auto-applied to any
future life area with zero new code.

## Audit: the fact block already surfaces what the corpus rules need
No plumbing gap found (pipeline._fact_block):
- full per-planet significations incl. DENIAL houses (~l.727)
- cusp sub-lords, 7th + all 12 = the PROMISE (~l.799)
- combustion windows incl. "currently combust" (~l.665)
- dignity / DEBILITATION + dispositor (~l.112)
- malefic aspect on a house, incl. aspected-by (~l.76)
ONE friction (not a gap): the promise needs a two-step join -- "7th-cusp sub-lord
is planet X -> look up X's significations." Both facts are present but not
pre-joined. This is the ONLY candidate for a tiny plumbing aid, and ONLY if live
validation shows the LLM failing the join. No rule either way.

## Test cases (Sulabh's chart; facts from data/default_user/kundali_summary.txt)

### CASE 1 -- Marriage (strongest; three independent negations)
Facts in the block:
- Venus (natural marriage karaka) sits in the 6th (a DENIAL house) as a strong
  occupant, and reaches the supporting 11th only weakly (by lordship).
- The 7th lord (Mercury) is DEBILITATED in the 4th -- the marriage house's own
  ruler is weak.
- Saturn (malefic) ASPECTS the 7th -- restriction / delay on marriage.
- The event occurred in the Mercury-Rahu window; Rahu reaches 2 & 7 (support).
PASS if the LLM reads marriage as OBSTRUCTED / DELAYED and credits the enabling
lord (Rahu, reaching 2 & 7), NOT Venus. FAIL if it leads with "strong Venus
marriage period" or just reports the top-scored window with no negation.

### CASE 2 -- Career (milder)
- The 10th lord (Mercury) is also DEBILITATED.
PASS if the LLM notes the career lord is weak and routes career strength through
Venus (6th, own sign = service), matching the real path. FAIL if it asserts a
strong 10th-lord career with no mention of the debilitation.

### CASE 3 -- Promise gate (confirm live)
7th-cusp sub-lord's significations are not transcribed here. In the run, confirm
the LLM reads the 7th-cusp sub-lord and states "promised / not promised" for
marriage (the two-step join above). If it skips the sub-lord entirely, that is the
one place to consider surfacing the sub-lord's significations inline.

## How to run (live, costs OpenAI)
Ask the live model, on Sulabh's chart:
  Q1: "When was marriage most likely, and why?"   -> grade against CASE 1.
  Q2: "How are my career prospects, and through what?" -> grade against CASE 2.
  Q3: (implicit in Q1) does it mention the 7th-cusp sub-lord / promise? -> CASE 3.
Grade each PASS/FAIL on whether the NAMED negation/promise doctrine appears, not on
which window it picks. Target: corpus applied in all three.
