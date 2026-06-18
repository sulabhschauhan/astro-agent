"""Natural (sthira/naisargika) friendship + compound-relationship tables per PVR §3.4.1 Table 7 and §3.4.3 Table 8. Data only — no logic."""

# Source: PVR Narasimha Rao, "Vedic Astrology: An Integrated Approach", §3.4.1
# Table 7 (Natural Relationships) and §3.4.3 Table 8 (Compound Relationships).
# Cross-validated against the "Permanent Friendship" table in all 4 AstroSage
# reference PDFs (Sulabh, Surbhi, Sheridan, David) — identical in every case.
#
# Scope: the 7 classical planets only (Sun, Moon, Mars, Mercury, Jupiter,
# Venus, Saturn). Rahu/Ketu are deliberately excluded — neither PVR's Table 7
# nor any of the 4 AstroSage friendship tables extend this table to the
# nodes. This is a scope match to both locked sources, not an oversight.
#
# ASYMMETRY WARNING — read before editing: natural friendship is NOT a
# symmetric matrix. Planet A counting planet B as a friend does NOT imply
# planet B counts planet A as a friend (e.g. Moon -> Mercury is "friend",
# but Mercury -> Moon is "enemy"). 11 of the 21 planet-pairs are asymmetric;
# only 10 happen to be symmetric. Each planet's row below is transcribed
# independently from PVR's table — do NOT derive or "fix" one planet's row
# from another's; an apparent asymmetry here is correct classical content,
# not a transcription error.
#
# Temporary (tatkalika) friendship is NOT a table and is intentionally absent
# from this module — per PVR §3.4.2 it is a chart-dependent rule (computed
# via house-counting from the sign occupied by one planet to the sign
# occupied by another), not fixed data. It will be implemented as logic in
# a later module, not added here. Pancha-dha-maitri (the 5-fold compound
# scheme combining natural + temporary) is likewise out of scope here.

NATURAL_FRIENDSHIP: dict[str, dict[str, list[str]]] = {
    "Sun":     {"friends": ["Moon", "Mars", "Jupiter"], "neutral": ["Mercury"], "enemies": ["Venus", "Saturn"]},
    "Moon":    {"friends": ["Sun", "Mercury"], "neutral": ["Mars", "Jupiter", "Venus", "Saturn"], "enemies": []},
    "Mars":    {"friends": ["Sun", "Moon", "Jupiter"], "neutral": ["Venus", "Saturn"], "enemies": ["Mercury"]},
    "Mercury": {"friends": ["Sun", "Venus"], "neutral": ["Mars", "Jupiter", "Saturn"], "enemies": ["Moon"]},
    "Jupiter": {"friends": ["Sun", "Moon", "Mars"], "neutral": ["Saturn"], "enemies": ["Mercury", "Venus"]},
    "Venus":   {"friends": ["Mercury", "Saturn"], "neutral": ["Mars", "Jupiter"], "enemies": ["Sun", "Moon"]},
    "Saturn":  {"friends": ["Mercury", "Venus"], "neutral": ["Jupiter"], "enemies": ["Sun", "Moon", "Mars"]},
}

# PVR §3.4.3 Table 8. Key is (natural_relation, temporal_relation); temporal
# relation has no neutral state (PVR §3.4.2), so only "Friend"/"Enemy" appear
# in that slot. Values use PVR's own English glosses (his parenthetical
# translations of the Sanskrit terms, given in the comments below) rather
# than AstroSage's alternate wording for the two extreme categories —
# AstroSage's report uses "Intimate"/"Bitter" where PVR uses "Good
# Friend"/"Bad Enemy" for the same compound categories. PVR's wording is the
# locked value since his book is the primary source.
COMPOUND_RELATIONSHIP_MAP: dict[tuple[str, str], str] = {
    ("Friend", "Friend"):  "Good Friend",  # PVR: Adhimitra
    ("Friend", "Enemy"):   "Neutral",      # PVR: Sama
    ("Neutral", "Friend"): "Friend",       # PVR: Mitra
    ("Neutral", "Enemy"):  "Enemy",        # PVR: Satru
    ("Enemy", "Friend"):   "Neutral",      # PVR: Sama
    ("Enemy", "Enemy"):    "Bad Enemy",    # PVR: Adhisatru
}
