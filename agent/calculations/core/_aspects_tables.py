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
# ── 2. LOCKED DECISION ───────────────────────────────────────────────────────
# Rahu=(5,7,9), Ketu=(5,7,9) -- Jupiter-pattern graha drishti for BOTH nodes.
# This is a RE-AFFIRMATION, not a new decision: the tuple values are
# UNCHANGED from the prior lock (commit de9debe). What changed is the
# evidence base below -- PyJHora's own source surfaced new conflicting
# evidence after the original lock, it was investigated on its merits, and
# it did not change the outcome.
#
# ── 3. SOURCE LANDSCAPE (8 sources, genuinely fragmented) ───────────────────
# | Source                                                | Rahu     | Ketu     |
# |--------------------------------------------------------|----------|----------|
# | PyJHora const.py L508 (PVR's own Python port)         | (7,)     | (7,)     |
# | JHora UI highlight (right-click -> highlight rasis)   | 2,5,7,9  | none     |
# | AstroSage (4 ref PDFs: Sulabh/Surbhi/Sheridan/David)  | 5,7,9    | 5,7,9    |
# | Modern Indian web consensus (astrosutras.in,          | 5,7,9    | 5,7,9    |
# |   astrosight.ai, jagatsevak.com, drikpanchang,        |          |          |
# |   prokerala)                                          |          |          |
# | Sanjay Rath commentary (srath.com)                    | 5,7,9    | 5,7,9    |
# | PVR book Exercise 14 (strict text reading)            | omitted  | omitted  |
# | Vedic-Planetary-Aspectarium (3rd-party)               | omitted  | omitted  |
# | lightonvedicastrology forum                           | 2,5,7,9  | none     |
#
# ── 4. DECISION RATIONALE ────────────────────────────────────────────────────
# No clean classical majority exists across the 8 sources above -- the field
# is genuinely fragmented, not a simple head-count. Per the project's
# tiebreaker principle for genuinely confused classical sources: prefer
# USER-PERCEIVED CORRECTNESS over single-source-code purity. This app is
# user-facing -- if a user cross-checks our output against AstroSage,
# Prokerala, or Drik Panchang and finds a disagreement, credibility is lost
# regardless of how defensible our internal citation chain is.
#
# 5,7,9 for both nodes has the highest cross-check convergence of any
# candidate value above: it matches all 4 AstroSage validation PDFs (Sulabh,
# Surbhi, Sheridan, David), the modern Indian web consensus (astrosutras.in,
# astrosight.ai, jagatsevak.com, drikpanchang, prokerala), AND Sanjay Rath's
# classical commentary -- three independent source families, not one.
#
# Explicitly rejected, with reasons:
#   - PyJHora (7,)-only -- outlier; a single author's Python port; contradicts
#     even JHora's own UI behavior (which shows Rahu=2,5,7,9, not bare 7).
#   - JHora-UI's asymmetric 2,5,7,9 (Rahu) / none (Ketu) -- no major
#     third-party site matches this pattern, and the Rahu/Ketu asymmetry is
#     unexplained and would be confusing to surface to users.
#   - PVR Exercise 14's strict-text omission -- would make this app uniquely
#     silent on node aspects against every popular consumer-facing source.
#
# ── 5. TRADE-OFF, ACKNOWLEDGED ───────────────────────────────────────────────
# We are choosing user-perceived correctness over single-source purity
# because the source landscape is genuinely confused, not because we dismiss
# PyJHora. PyJHora is PVR's own Python port and would normally carry real
# weight -- but here it is a single, isolated outlier that even disagrees
# with JHora's own UI. If a future authoritative consensus emerges (e.g. a
# revised PVR publication, or a cross-source convergence on a different
# value), this lock should be revisited.
#
# ── 6. SENSITIVITY TAG FOR DOWNSTREAM CONSUMERS ──────────────────────────────
# SENSITIVE_TO: rahu_ketu_drishti_lock -- yoga/dosha/transit modules that key
# off Rahu/Ketu aspects should reference this lock by name in their own
# docstrings, so that a future change here triggers a targeted regression
# sweep rather than a silent semantics shift.
#
# ── 7. AUDIT ANCHOR (rejected alternative, cited for traceability) ──────────
# PyJHora source: github.com/naturalstupid/PyJHora, const.py L508
# (graha_drishti dict), retrieved 2026-06-20 (this session). This is the
# rejected (7,)-only alternative from Sections 3-4 above, not the locked
# value -- cited here so a future reviewer can verify the claim directly
# against source rather than trusting this comment.
#
# ── 8. V2 CONFIGURABILITY NOTE ───────────────────────────────────────────────
# If a future v2 needs to support alternative aspect traditions (e.g. KP
# astrology's own aspect conventions, the strict-PVR-text no-node-aspect
# reading, or another school entirely), that should be parametrized via a
# constructor/config layer ABOVE this table -- e.g. selecting between
# multiple named tables at a higher layer. Do NOT add competing dicts to
# this file. This module remains the single canonical source for v1.
#
# ── 9. SCOPE NOTE FOR DOWNSTREAM CALLERS ─────────────────────────────────────
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
