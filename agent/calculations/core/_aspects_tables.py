"""Planetary aspect (graha drishti) house positions per PVR §10.2 plus locked classical-conflict resolution for Rahu/Ketu. Data only — no logic."""

# ── 1. PRIMARY SOURCE ────────────────────────────────────────────────────────
# PVR Narasimha Rao, "Vedic Astrology: An Integrated Approach", §10.2 plus
# Example 34. The literal rule: all planets aspect (graha drishti) the 7th
# house counted from their own position. Three planets carry additional
# special aspects on top of the universal 7th: Mars adds the 4th and 8th;
# Jupiter adds the 5th and 9th; Saturn adds the 3rd and 10th. PVR's worked
# examples ("Sun in Taurus aspects Scorpio"; "Jupiter in Gemini aspects
# Libra, Sagittarius, Aquarius") confirm the rule is SIGN-BASED, not
# degree-based -- the aspect lands on whole signs counted from the
# aspecting planet's own sign, not on a degree-precise point. This matches
# the project's Whole Sign house lock naturally; no degree-based
# refinement is needed or implemented here.
#
# ── 2. THE RAHU/KETU QUESTION IS A LOCKED CLASSICAL-CONFLICT RESOLUTION ─────
# This is a locked resolution of a genuine textual and classical conflict,
# not a simple majority vote. PVR himself is internally inconsistent on
# this point: §10.2 states "all planets aspect the 7th" with no scope
# qualifier that would exclude the nodes, yet Exercise 14 explicitly
# enumerates graha drishti only for the 7 classical planets, silently
# omitting Rahu/Ketu -- while Exercise 15, covering rasi drishti (sign
# aspects, a separate mechanism), explicitly includes both nodes. The
# strict-text reading of Exercise 14 (no graha drishti for nodes) is
# therefore textually defensible on its own, but it is contradicted by
# PVR's own software, JHora (see Section 3 below).
#
# The broader classical field is genuinely fragmented beyond PVR, with no
# clean majority position:
#   - "No aspects at all" for the nodes -- some BPHS readings, the
#     "headless Ketu" school (Ketu has no head to cast a directional gaze).
#   - "7th only" for the nodes -- a BPHS-inclusive reading treating Rahu
#     and Ketu as ordinary planets under the universal 7th-aspect rule
#     only, with no special aspects.
#   - "5th/7th/9th for both" -- the modern Indian classical majority,
#     treating both nodes as Jupiter-like aspect sources.
#   - Asymmetric variants -- e.g. Rahu treated as Saturn-like (3rd/7th/
#     10th) with Ketu treated as Mars-like (4th/7th/8th); or Rahu given
#     2nd/5th/7th/9th with Ketu given no special aspects at all.
#
# ── 3. TIEBREAKER ────────────────────────────────────────────────────────────
# Per the project's locked conflict-resolution protocol -- "classical
# majority + JHora implementation wins"; with the classical majority
# itself contested per Section 2, JHora's own behavior is decisive --
# four independent, convergent pieces of evidence support the 5th/7th/9th
# (Jupiter-like) lock for BOTH Rahu and Ketu:
#
#   (a) JHora's own "Aspect Table with Relationships" output includes Rahu
#       and Ketu as aspect-source rows with non-zero aspect values landing
#       across multiple target signs and houses. Verified directly by
#       screenshot inspection of JHora's output on 19-Jun-2026, the session
#       in which this decision was locked. JHora is PVR-authored and the
#       project's locked numerical-ground-truth oracle, so this is the
#       single heaviest-weighted piece of evidence.
#
#   (b) Sanjay Rath (srath.com), a recognized commentator working within
#       PVR's own tradition, analyzing PVR's own natal chart, writes:
#       "Rahu being in the 2nd house also aspects them in the 10th house."
#       The 10th house is the 9th position counted from the 2nd house
#       (2nd as position 1) -- this is a worked example directly confirming
#       a 9th-house aspect for Rahu, i.e. Jupiter-like behavior, from a
#       source explicitly situated inside PVR's own tradition.
#
#   (c) All 4 AstroSage reference PDFs in project_files (Sulabh, Surbhi,
#       Sheridan, David) independently state "Ketu aspects [house X, house
#       Y, house Z]" in their respective chart reports. Across all four
#       charts, the three stated houses consistently map back to the
#       5th/7th/9th positions counted from Ketu's own sign -- four
#       independent real-chart confirmations of the same pattern.
#
#   (d) Modern Indian classical web sources outside the AstroSage/JHora
#       ecosystem -- astrosutras.in, astrosight.ai, jagatsevak.com --
#       independently converge on Jupiter-like 5th/7th/9th aspects for
#       both nodes, consistent with (a)-(c) above.
#
# ── 4. EXPLICITLY REJECTED ALTERNATIVES ─────────────────────────────────────
# Documented here, not silently discarded, so a future reviewer can see
# what was considered and why it didn't win:
#
#   - PVR Exercise 14's strict reading (no graha drishti for Rahu/Ketu at
#     all): contradicts JHora, the locked numerical oracle (Section 3a).
#     Rejected.
#   - "7th only" for the nodes: contradicted by Sanjay Rath's worked
#     example, which shows a 9th-house aspect for Rahu, not merely a 7th
#     (Section 3b). Rejected.
#   - Asymmetric variants (Rahu Saturn-like / Ketu Mars-like; or Rahu with
#     2nd/5th/7th/9th and Ketu silent): no corroborating evidence found in
#     JHora's actual behavior or in AstroSage parity across the 4
#     reference charts. Rejected for lack of supporting evidence, not on
#     principle -- if such evidence surfaces later this should be
#     revisited.
#
# ── 5. V2 CONFIGURABILITY NOTE ───────────────────────────────────────────────
# If a future v2 needs to support alternative aspect traditions (e.g. KP
# astrology's own aspect conventions, the strict-PVR-text no-node-aspect
# reading, or another school entirely), that should be parametrized via a
# constructor/config layer ABOVE this table -- e.g. selecting between
# multiple named tables at a higher layer. Do NOT add competing dicts to
# this file. This module remains the single canonical source for v1.
#
# ── 6. SCOPE NOTE FOR DOWNSTREAM CALLERS ─────────────────────────────────────
# ASPECTED_HOUSES_BY_PLANET.keys() defines the full aspecting-planet set:
# all 9 chart points, nodes included. This is intentionally DIFFERENT from
# friendship.py's CLASSICAL_PLANETS (7 classical planets only, nodes
# excluded by classical design -- see _friendship_tables.py). Aspects and
# friendship have different semantic scopes by classical design, not by
# oversight: nodes cast aspects but do not participate in the natural-
# friendship table. Downstream code that needs to iterate "all aspecting
# planets" should pull from this dict's keys (eventually surfaced as a
# public constant in aspects.py during Prompt 3), not from
# friendship.CLASSICAL_PLANETS.

ASPECTED_HOUSES_BY_PLANET: dict[str, tuple[int, ...]] = {
    "Sun":     (7,),
    "Moon":    (7,),
    "Mars":    (4, 7, 8),
    "Mercury": (7,),
    "Jupiter": (5, 7, 9),
    "Venus":   (7,),
    "Saturn":  (3, 7, 10),
    "Rahu":    (5, 7, 9),
    "Ketu":    (5, 7, 9),
}
