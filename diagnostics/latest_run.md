# Session: av_transit_scorer.py -- Ashtakavarga transit scorer (Session 55)

**New file:** `agent/calculations/transits/av_transit_scorer.py` (only
file changed besides the benign `calc_router_stage2.log` growth from
running the suite; `git status` confirms it). No other file touched --
`agent/calculations/transits/__init__.py`'s stale "Ashtakavarga transit
strength -- deferred to P5" comment is intentionally left as-is per this
prompt's "no other file changes" constraint.

**Function:** `score_av_transit(transit_planet, transit_sign,
degrees_in_sign, natal_bav, natal_sav, natal_contributors) ->
AvTransitScore` (frozen dataclass). Pure function, no ephemeris calls --
takes precomputed transit position + precomputed natal Ashtakavarga
tables (compute_bav/compute_sav/compute_bav_contributors outputs).

**Planet scope (locked V1):**
- Saturn/Jupiter: full scoring incl. kakshya_index/kakshya_lord/
  kakshya_has_rekha (PVR Table 60).
- Sun/Mars: sign-level only, kakshya fields = None (too fast for kakshya-
  scale precision to mean anything).
- Moon/Mercury/Venus: ValueError, fail closed -- excluded from V1 transit
  scoring by design (too fast to constrain event windows; Moon belongs to
  the Muhurta layer).

**Thresholds, each with CITATION + scope guard + tuning note in the
module docstring:**
- bav_band (>=5 FAVORABLE / ==4 NEUTRAL / <=3 UNFAVORABLE) -- PVR ch.
  25.5 verbatim.
- bav_intensity (EXCELLENT for 6/7/8, VERY_POOR for 0/1, else None) -- PVR
  verbatim for 6/7/0/1; 8 folded into EXCELLENT by monotonicity, flagged
  as an interpolation not a direct citation.
- sav_band (>=30 FAVORABLE / 25-29 AVERAGE / <=24 UNFAVORABLE) -- PVR ch.
  25.5.1 prose leaves the value 30 ambiguous (">30"/"<25"); resolved to
  >=30 on PVR's own Vajpayee worked example (SAV=30 in Pisces classed
  "very strong").
- verdict (SAV-dominance rule) -- verdict = sav_band when sav_band !=
  AVERAGE, else verdict = bav_band (NEUTRAL mapped to AVERAGE). No
  numeric weighting/composite score invented -- PVR provides none.
- kakshya boundaries (3d45'=3.75 deg divisions, half-open [start, end)) --
  PVR Table 60 doesn't state boundary-tie-breaking in the prose
  consulted; documented as a chosen convention (exactly 3.75 degrees
  falls to the second kakshya, Jupiter), not a citation.

**USAGE CONSTRAINT documented verbatim in the docstring:** PVR states the
kakshya method "can only be used to fine-tune a prediction to a few days"
and is never used in a vacuum -- nesting this score inside a dasha
envelope is the future convergence layer's responsibility, not enforced
here (a pure per-instant function cannot enforce it).

**Manual verification (no test file this prompt, per instructions) --**
ran an inline smoke script against David's already-oracle-locked BAV/SAV/
contributor tables (Session 54/56): confirmed the SAV-dominance rule
(Saturn/Gemini: BAV=UNFAVORABLE, SAV=33=FAVORABLE, verdict correctly
dominates to FAVORABLE), the exact-3.75-degree kakshya boundary falling to
Jupiter as documented, Sun/Mars returning kakshya fields = None, all three
excluded planets and an unknown planet/sign/degrees-out-of-range all
raising ValueError, and the dataclass rejecting mutation
(FrozenInstanceError). Script was not committed.

## Test tallies
- Full suite: `2843 passed, 3 skipped, 1 warning` -- unchanged (pure
  addition, no test file this prompt; existing suite stays green).

No existing file's logic changed.
