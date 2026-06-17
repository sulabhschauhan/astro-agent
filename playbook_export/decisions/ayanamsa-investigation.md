# Ayanamsa / Cross-Ephemeris Discrepancy Investigation

Session 17.

## Question
calculate_solar_return showed ~10.6 min epoch drift vs AstroSage for
Sulabh's 2026 Varshaphal — root cause?

## Method
Compared AstroSage's stated Lahiri ayanamsa + degree-level Sun/Moon
positions against pyswisseph across 4 reference charts (see
reference_charts.md), spanning 1976-2026, 3 timezones (IST+5.5, Durban+2,
London+0), both hemispheres.

## Findings
- Ayanamsa: pyswisseph SIDM_LAHIRI vs AstroSage = constant ~2.2-2.7" across
  all 4 charts/epochs. SIDM_LAHIRI_ICRC slightly tighter (~1.1-1.6"), also
  flat. Ayanamsa-variant is NOT the source of the drift.
- Sun/Moon tropical longitude residuals (NOABERR/NONUT/TRUEPOS flag combos
  tested): 5-48", inconsistent in sign/magnitude across charts and between
  Sun/Moon. No flag combination resolves all cases.
- Consistent with display rounding + birth-time-to-the-second precision in
  source PDFs — irreducible noise, same class as the documented ±37-day
  Vimshottari drift.

## Decision
- Did not change global ayanamsa mode (risk to validated 9/9 D1 +
  Vimshottari, and ~1" gain from LAHIRI_ICRC is noise-level anyway).
- Added is_boundary_sensitive(degree_in_sign, threshold_deg=5.0) helper —
  flags sign-boundary-dependent results (Lagna, Muntha, etc.) within 5° of
  a boundary, based on observed worst-case ~48" residual ≈ ~5° ascendant
  motion. Reusable across Varshaphal, Muntha, and future sign-dependent
  calculations.

## Second-pass investigation (Session 17 continued)

Tested additional hypotheses against the same 4 charts before extending
is_boundary_sensitive to Muntha:

- Topocentric vs geocentric: AstroSage's published Moon positions match
  geocentric to ~30"; topocentric is off by 800-3000" (0.5-1°). Ruled out —
  AstroSage publishes geocentric.
- Local Sidereal Time: AstroSage's stated LST vs pyswisseph's differs by
  ~1.5-3 seconds (~22-44" of RA) — two orders of magnitude too small to
  explain the 5-48" Sun/Moon residuals. Ruled out.
- Reverse-engineered implied ayanamsa from each chart's published Sun/Moon:
  deltas range 17-48" and are inconsistent in sign between Sun and Moon and
  across charts (no single offset fits). Confirms: no corrective
  transformation exists for all 4 cases — irreducibility is demonstrated,
  not assumed.

## Muntha design implication

is_boundary_sensitive on Varshaphal Lagna is necessary but not sufficient
for Muntha. Muntha = (natal Lagna sign + age) mod 12, mapped to a bhav
relative to Varshaphal Lagna. When Varshaphal Lagna is boundary-sensitive,
Muntha's bhav shifts by a full house (categorical interpretive change, e.g.
6th vs 5th bhav — different life domains), not a degree variation.

Worked example (Sulabh 2026): Muntha seed = Aquarius. If Varshaphal Lagna =
Virgo (AstroSage): Muntha = 6th bhav. If Lagna = Libra (our boundary-
sensitive result): Muntha = 5th bhav.

Decision for Muntha implementation: when lagna_boundary_sensitive=True,
Muntha's return shape must surface both candidate bhavs (e.g.
{bhav_primary, bhav_alternate, ambiguous: True}), not a single int — a
single value would assert false confidence on a categorical interpretive
difference.

## Outstanding multi-location scope (discovered during B2)

calculate_chart()'s birth_ist (natal Vimshottari dasha timeline display)
still uses hardcoded _IST — same bug class as B1/B2, not yet fixed. Should
be addressed (Task B3) before Mudda Dasha is built, since Mudda Dasha will
likely reuse this date-display pattern.

**RESOLVED (Task B3, this session)**: calculate_chart() now derives its
dasha-timeline anchor via _local_datetime() (the same resolve_timezone_offset
pattern as B1/B2), renamed birth_ist -> birth_local. _IST is fully retired
except for its annotated, now-unused definition.

## Forward note for Mudda Dasha (Varshaphal sub-periods)

B3's validation observed 3-36 day drift on natal Antardasha boundaries vs
AstroSage (documented separately as the ±37-day Vimshottari drift, confirmed
pre-existing and unrelated to B3 — Sulabh's Case 1 output was byte-identical
before/after B3).

Mudda Dasha periods (Varshaphal's annual sub-periods) are shorter than
natal Antardashas — the same class of drift could represent a larger
fraction of a Mudda Dasha period's length. When scoping Mudda Dasha,
consider whether period-transition dates need a similar "disclose
uncertainty rather than assert precision" treatment, analogous to
is_boundary_sensitive for Lagna/Muntha — but on the time axis instead of
the degree axis. Not yet investigated; flag for that session.

## pyswisseph vs JHora ayanamsa (Session 19, P1.2d — Panchanga)

### Question
Wiring real SIDM_LAHIRI ayanamsa into Panchanga's return value (replacing a
0.0 placeholder). Added 4 tests comparing computed ayanamsa against each
fixture's `expected_ayanamsa_dms` (sourced from JHora) at 1" tolerance.
Hardest case first (Sheridan, per working-style rule): failed by 57.77".
All 4 fixtures failed by the same ~57.77", not noise — a constant
cross-implementation offset, independent of date/location.

### Sweep
Tested every `SIDM_*` mode pyswisseph exposes (~50 modes: Lahiri variants,
True Citra/Pushya/Revati/Mula, Krishnamurti, Fagan-Bradley, Babylonian
variants, etc.) against Sulabh's fixture (expected 24°12'38.22" =
24.210617°). None land within 1". Closest five:

| Mode                  | Ayanamsa   | Diff vs JHora |
|-----------------------|------------|---------------|
| SIDM_LAHIRI_1940      | 24.211895° | 4.60"         |
| SIDM_TRUE_CITRA       | 24.213363° | 9.89"         |
| SIDM_LAHIRI_ICRC      | 24.226361° | 56.68"        |
| SIDM_LAHIRI (current) | 24.226664° | 57.77"        |
| SIDM_LAHIRI_VP285     | 24.233052° | 80.77"        |

Also ruled out an ephemeris-source effect: `get_ayanamsa_ex_ut` with
FLG_SWIEPH vs FLG_MOSEPH gives identical ayanamsa (expected — ayanamsa is a
precession-model quantity, independent of which planetary ephemeris is
loaded).

### Measured gap, per fixture (2026-06-16 12:30 local, 4 charts)

| Fixture   | pyswisseph SIDM_LAHIRI | JHora expected | Diff       |
|-----------|------------------------|-----------------|------------|
| Sulabh    | 24.226664°              | 24.210617°      | 57.77"     |
| Surbhi    | 24.226664°              | 24.210617°      | 57.77"     |
| Sheridan  | 24.226670°              | 24.210622°      | 57.77"     |
| David     | 24.226672°              | 24.210625°      | 57.77"     |

(Sub-second fixture-to-fixture variation is the expected ~0.026"
precession drift across the ~4.5h of UTC spread between timezones on the
same calendar date — negligible next to the 57.77" gap itself.)

### Decision
- Keep SIDM_LAHIRI. It's the mode every other Panchanga element (tithi,
  vara, nakshatra, yoga, karana, hora) was already validated against in
  P1.2a/P1.2b; switching modes to chase a 4.60" reduction (still not exact)
  would be a global behavior change for a single-field gain, and is out of
  scope for what was meant to be a surgical "wire up the real value" edit.
- Treat 60" (1 arcmin) as the working cross-implementation tolerance for
  ayanamsa specifically — enough headroom above the measured 57.77" to not
  flag on this known gap, tight enough to still catch a real regression
  (e.g. wrong jd_ut, wrong sidereal mode, or a flipped sign).
- This is the same class of finding as the pyswisseph-vs-AstroSage ~2.2-2.7"
  gap above, just against a different oracle (JHora) and ~20x larger in
  magnitude. Both are treated as irreducible cross-implementation noise
  rather than a defect to chase further, absent a third independent oracle
  to triangulate which side (if either) is "right."

### Internal consistency check
An ayanamsa offset of δ shifts every sidereal longitude by -δ. Tithi
(moon_lon - sun_lon) cancels the offset exactly — consistent with tithi
showing no corresponding drift. Nakshatra (function of moon_lon alone)
should shift by δ directly; yoga (moon_lon + sun_lon) should shift by 2δ
since both terms carry the offset. For δ=57.77", against the nakshatra/yoga
span of 13°20' (48000"):
- Predicted nakshatra percent_left shift: 57.77/48000 = 0.12%
- Predicted yoga percent_left shift: 2 x 0.12% = 0.24%

Observed deltas (computed vs each fixture's expected percent_left, already
absorbed under PERCENT_TOLERANCE=0.5 and so never previously surfaced):
nakshatra ~0.14-0.15%, yoga ~0.30-0.31%, ratio ~2.1x. Same order of
magnitude and the expected ~2x yoga:nakshatra ratio — confirms the gap is
concentrated in ayanamsa itself, not a downstream Moon/Sun longitude bug.
The ~20-25% relative gap between predicted (0.12%/0.24%) and observed
(0.14-0.15%/0.30-0.31%) is consistent with the independent few-arcsecond
Sun/Moon residual noise already documented above (the 5-48" inconsistent-
sign residuals) — i.e. ayanamsa is the dominant but not sole contributor.
