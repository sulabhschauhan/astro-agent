# First-job sample check (hand-trace) — can grading improve the timing ranker?

Offline, $0, no model call. Purpose: the SAMPLE-before-SCALE check — does a
correctly-weighted model surface the true first-job window, or is the signal set
blind to it? If blind, grading cannot help and we stop.

## Correction to the baseline
`20261114T180718Z_timing_backtest_baseline.md` scored first job on **2011-02-01
(Mercury-Ketu)**. Sulabh corrected the date to **Feb 2012**, which falls in
**Mercury MD / Venus AD** (26 Dec 2011 → 26 Oct 2014) — a different window.
Ketu signifies only {3,8} (no career house), so the baseline row was doomed by a
wrong date, not by the model. **Re-baseline first job on Feb 2012 before/after any
change.**

## The window under test
Feb 2012 = **Mercury MD / Venus AD**. Career house set = {2 income, 6 service/job,
10 profession, 11 gains}. Chart: Sagittarius lagna (kundali_summary.txt).

## Hand-trace — is the true window strong on CORRECT doctrine?

**Venus (AD lord) — a textbook-strong career significator:**
- **Occupies the 6th house** (Taurus) — the service/employment house. In KP this is
  a **Level-1 (occupant) significator**, the STRONGEST tier.
- **Own sign** (Taurus) — dignified; will meet the Shadbala minimum (Stage-2 gate).
- **Lords the 6th AND the 11th** — both career houses.
- Engine flat significators: Venus → {3,5,6,10}; hits career 6 and 10.

**Mercury (MD lord):** 10th lord (profession), but **debilitated** in the 4th and a
functional malefic here; signifies 2 (income). Weak support — correct that it should
NOT carry the window; Venus should.

## Why the flat model buries it
Current score ≈ 2.5 (Venus sig 6,10 = +2.0; Mercury MD = +0.5), tied with ~14 other
windows. The flat model collapses Venus's **occupancy of the 6th** and its **own-sign
dignity** into the same flat "+1 per signified house" every weak lord gets. It throws
away exactly the two facts that make Venus stand out.

## Verdict: IMPROVEMENT IS ACHIEVABLE [Likely]
The signal is present AND gradeable. A model that (a) weights significators by the KP
hierarchy (occupant/star-lord > lord) and (b) gates by dignity/Shadbala would lift
Venus-Feb2012 clear of its flat tie, because Venus is strong on precisely those axes
and most tie-mates are not.

**Highest-leverage fix = the KP significator-HIERARCHY weighting** — which is NOT in
the staged plan. The staged SAV transit grading (Stage 1) is real but SECONDARY here:
the dominant discriminator for this event is natal significator STRENGTH, not transit
strength. Recommend re-ordering: hierarchy weighting first, then Shadbala gate, then
SAV.

## Caveats (honesty)
- Hand-trace INDICATION, not a measured result. No SAV table or exact Feb-2012 transit
  pulled; the weighted model was not run. Proof = build the hierarchy-weighted ranker
  and re-score.
- Still N=1. This shows the signal is THERE and GRADEABLE for first-job — a green light
  to build, NOT evidence it generalises. Multi-chart corpus (Astro-Databank AA) remains
  the only real accuracy test.
- Freeze weights from citation BEFORE re-scoring events (events are a check, never a
  tuning target).
