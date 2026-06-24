"""Ashtakoot (8-koota) marriage-compatibility lookup tables -- P2.4.0. Data only -- no calculation logic, no functions, no classes.

P2.4.0 constants module -- data only, no calculation logic. AstroSage is
the locked validation oracle for variant resolution; classical sources
cited where they agree, AstroSage chosen where they diverge.

Conventions (module-wide):
- Sign keys: 0-11 (0=Aries..11=Pisces), matching chandrabala.py / muhurta_scorer.py.
- Nakshatra keys: 0-26 (0=Ashwini..26=Revati), matching tarabala.py.
- Vashya is the SOLE exception requiring sub-sign resolution (see its own
  section below) -- a deliberate classical-accuracy choice for JHora/
  AstroSage parity, not a break of the 0-11 sign convention; every other
  sign-keyed table in this module is flat 0-11.

Source priority used while building this module: PVR Narasimha Rao's
"Vedic Astrology: An Integrated Approach" (515-page PDF, full-text scanned
for "ashtakoot"/"koota"/"vashya"/"yoni"/"gana"/"nadi"/"bhakoot"/"guna
milan" and variants -- ZERO hits outside of unrelated Naabhasa-yoga and
longevity/matchmaking-timing passages; PVR's Muhurta chapter, Ch.36, never
names an 8-koota system). The project's RAG corpus (data/all_chunks.json)
was checked next and found comprehensive, single-source coverage of all 8
kootas in Muhurtha-Chinthamani pp.155-180 ("Marriage Sanskaras" chapter) --
BPHS, Saravali and Phaladeepika were also checked and have no Ashtakoot
content (confirmed by direct corpus search; these are natal-analysis texts,
not muhurta/marriage-matching texts). Web research (AstroSage, PyJHora
source code) was used only where Muhurtha-Chinthamani's OCR was too
degraded to transcribe a precise table, or where a classical source gives
no number at all -- never as a primary classical source.

Total score-weight citation: Muhurtha-Chinthamani p.160 names the 8 kootas
(Varna, Vashya, Tara, Yoni, Graha Maitri, Gana, Bhakoot, Nadi) with point
values 1..8 respectively, and gives the closed-form sum "(8+1)*8/2 = 36"
explicitly in the source text.
"""

from agent.calculations.core._friendship_tables import NATURAL_FRIENDSHIP  # noqa: F401  (Graha Maitri reuses this directly -- see its section below)

# ============================================================================
# SCORE WEIGHTS -- max points per koota. Source: Muhurtha-Chinthamani p.160.
# ============================================================================

KOOTA_SCORE_WEIGHTS: dict[str, int] = {
    "Varna": 1,
    "Vashya": 2,
    "Tara": 3,
    "Yoni": 4,
    "GrahaMaitri": 5,
    "Gana": 6,
    "Bhakoot": 7,
    "Nadi": 8,
}
TOTAL_KOOTA_SCORE = 36  # sum of KOOTA_SCORE_WEIGHTS.values(); Muhurtha-Chinthamani p.160's own arithmetic check


# ============================================================================
# 1. VARNA KOOTA (max 1 point)
# Source: Muhurtha-Chinthamani p.161 "THE CONSIDERATION REGARDING THE KOOTA
# NAMED VARNA" -- "The signs of Pisces, Scorpio and Cancer are Brahmins;
# Aries, Leo and Sagittarius are Kshatriyas; Taurus, Virgo and Capricorn are
# Vaishyas; and Gemini, Aquarius and Libra are Shudras." Matches the
# universal water/fire/earth/air elemental convention exactly.
# Scoring (p.161-162): "if the Varna of the bridegroom is higher than that
# of the bride or [the same], 1 guna; otherwise 0" -- directional, keyed
# (groom_varna, bride_varna). A further classical exception (p.162: a
# lower-Varna groom's defect is removed if his Rashi LORD outranks the
# bride's Rashi lord's Varna) is cited for completeness but NOT implemented
# here -- it is a calculator-layer refinement, out of scope for a
# constants-only phase.
# ============================================================================

VARNA_GROUPS = ("Brahmin", "Kshatriya", "Vaishya", "Shudra")  # descending hierarchy order

VARNA_BY_SIGN: dict[int, str] = {
    0: "Kshatriya",   # Aries
    1: "Vaishya",     # Taurus
    2: "Shudra",      # Gemini
    3: "Brahmin",     # Cancer
    4: "Kshatriya",   # Leo
    5: "Vaishya",     # Virgo
    6: "Shudra",      # Libra
    7: "Brahmin",     # Scorpio
    8: "Kshatriya",   # Sagittarius
    9: "Vaishya",     # Capricorn
    10: "Shudra",     # Aquarius
    11: "Brahmin",    # Pisces
}

VARNA_SCORE: dict[tuple[str, str], int] = {
    ("Brahmin", "Brahmin"): 1, ("Brahmin", "Kshatriya"): 1, ("Brahmin", "Vaishya"): 1, ("Brahmin", "Shudra"): 1,
    ("Kshatriya", "Brahmin"): 0, ("Kshatriya", "Kshatriya"): 1, ("Kshatriya", "Vaishya"): 1, ("Kshatriya", "Shudra"): 1,
    ("Vaishya", "Brahmin"): 0, ("Vaishya", "Kshatriya"): 0, ("Vaishya", "Vaishya"): 1, ("Vaishya", "Shudra"): 1,
    ("Shudra", "Brahmin"): 0, ("Shudra", "Kshatriya"): 0, ("Shudra", "Vaishya"): 0, ("Shudra", "Shudra"): 1,
}  # keyed (groom_varna, bride_varna)


# ============================================================================
# 2. VASHYA KOOTA (max 2 points)
# Sub-sign exception (module-wide convention note): Sagittarius and
# Capricorn are classically split at the sign's own half (0-15deg = half 0,
# 15-30deg = half 1), unlike every other koota's flat 0-11 sign keying.
# Source: naturalstupid/PyJHora (PVR/JHora reimplementation),
# src/jhora/horoscope/match/compatibility.py, vasiya_porutham() --
#   chatushpada = signs{Aries,Taurus} or (Sagittarius and pada in [3,4]) or (Capricorn and pada in [1,2])
#   manava      = signs{Gemini,Virgo,Libra,Aquarius} or (Sagittarius and pada in [1,2])
#   jalachara   = signs{Cancer,Pisces} or (Capricorn and pada in [3,4])
#   vanachara   = Leo
#   keeta       = Scorpio
# (PyJHora's "pada in [1,2]" == degrees 0-15 in-sign == half 0 here;
# "pada in [3,4]" == degrees 15-30 == half 1 -- the "obvious" half-sign
# split, not a finer nakshatra-pada resolution.)
# AstroSage's own public matchmaking page (astrosage.com/freechart/
# matchmaking.asp, fetched directly) names the 5 groups but does not expose
# the degree-level split anywhere publicly findable; PyJHora is used as the
# concrete numeric source per this project's general "JHora primary where
# AstroSage doesn't expose the calculation" convention (CLAUDE.md). Cross-
# corroborated qualitatively by Muhurtha-Chinthamani p.164-165's "another
# book... 5 Vashyas" passage (OCR too table-garbled for an exact mapping)
# and by 2 independent web sources (freehoroscopesonline.in, AstroSight)
# describing the identical group/half assignment.
# ============================================================================

VASHYA_GROUPS = ("Chatushpada", "Manava", "Jalachara", "Vanachara", "Keeta")

VASHYA_BY_SIGN: dict[int, str] = {
    0: "Chatushpada",  # Aries
    1: "Chatushpada",  # Taurus
    2: "Manava",       # Gemini
    3: "Jalachara",    # Cancer
    4: "Vanachara",    # Leo
    5: "Manava",       # Virgo
    6: "Manava",       # Libra
    7: "Keeta",        # Scorpio
    # 8 (Sagittarius) and 9 (Capricorn) deliberately absent -- see VASHYA_BY_SIGN_HALF
    10: "Manava",      # Aquarius
    11: "Jalachara",   # Pisces
}

VASHYA_BY_SIGN_HALF: dict[tuple[int, int], str] = {
    (8, 0): "Manava",        # Sagittarius, 0-15deg
    (8, 1): "Chatushpada",   # Sagittarius, 15-30deg
    (9, 0): "Chatushpada",   # Capricorn, 0-15deg
    (9, 1): "Jalachara",     # Capricorn, 15-30deg
}

# Directional score matrix (row=bride's group, col=groom's group) -- Vashya
# measures mutual control/dominance, not a symmetric compatibility, so the
# matrix is NOT required to be (and per this source, is not) symmetric.
# Source: freehoroscopesonline.in's Vashyakoota speculum table (AstroSage-
# consistent description); same-group always scores the 2-point max.
VASHYA_SCORE: dict[tuple[str, str], float] = {
    ("Chatushpada", "Chatushpada"): 2, ("Chatushpada", "Manava"): 1, ("Chatushpada", "Jalachara"): 1, ("Chatushpada", "Vanachara"): 1.5, ("Chatushpada", "Keeta"): 1,
    ("Manava", "Chatushpada"): 1, ("Manava", "Manava"): 2, ("Manava", "Jalachara"): 1.5, ("Manava", "Vanachara"): 0, ("Manava", "Keeta"): 1,
    ("Jalachara", "Chatushpada"): 1, ("Jalachara", "Manava"): 1.5, ("Jalachara", "Jalachara"): 2, ("Jalachara", "Vanachara"): 1, ("Jalachara", "Keeta"): 1,
    ("Vanachara", "Chatushpada"): 0, ("Vanachara", "Manava"): 0, ("Vanachara", "Jalachara"): 0, ("Vanachara", "Vanachara"): 2, ("Vanachara", "Keeta"): 0,
    ("Keeta", "Chatushpada"): 1, ("Keeta", "Manava"): 1, ("Keeta", "Jalachara"): 1, ("Keeta", "Vanachara"): 0, ("Keeta", "Keeta"): 2,
}  # keyed (bride_group, groom_group)


# ============================================================================
# 3. TARA KOOTA (max 3 points)
# Source: Muhurtha-Chinthamani p.166 "THE CONSIDERATION OF TARA KOOTA" --
# count nakshatra-distance both directions (girl->boy, boy->girl), divide
# each by 9; remainder in {3,5,7} = inauspicious, else (0,1,2,4,6,8) =
# auspicious. Score: 3 if both directions auspicious, 0 if both
# inauspicious, partial credit between (source's OCR gives "14 marks" for
# the mixed case -- almost certainly a garbled "1 1/2"/1.5, the only value
# consistent with "3 max points, symmetric partial credit" and the
# universal modern convention; corrected here, not transcribed literally).
# ============================================================================

TARA_REMAINDER_CATEGORY: dict[int, str] = {
    0: "AUSPICIOUS", 1: "AUSPICIOUS", 2: "AUSPICIOUS",
    3: "INAUSPICIOUS",
    4: "AUSPICIOUS",
    5: "INAUSPICIOUS",
    6: "AUSPICIOUS",
    7: "INAUSPICIOUS",
    8: "AUSPICIOUS",
}  # key: (nakshatra_count - 1) % 9, i.e. ((other - self) % 27) % 9 in the 0-26 convention

TARA_SCORE: dict[tuple[str, str], float] = {
    ("AUSPICIOUS", "AUSPICIOUS"): 3.0,
    ("AUSPICIOUS", "INAUSPICIOUS"): 1.5,
    ("INAUSPICIOUS", "AUSPICIOUS"): 1.5,
    ("INAUSPICIOUS", "INAUSPICIOUS"): 0.0,
}  # keyed (girl_to_boy_category, boy_to_girl_category)


# ============================================================================
# 4. YONI KOOTA (max 4 points)
# Nakshatra->animal source: Muhurtha-Chinthamani p.167 ("YONI KOOTA: ...").
# The source explicitly uses 28 nakshatras (Abhijit included, paired with
# Uttarashada -> Nakula/Mongoose). This project's locked nakshatra
# convention is 27 (0-26, no Abhijit -- matches tarabala.py and PVR's own
# statement elsewhere in this corpus that "we consider 27 nakshatras for
# all other purposes", _pvr_spec_reference.json's "nakshatra" entry). Folding
# Abhijit back into Uttarashada (its classical parent nakshatra) is a clean,
# risk-accepted reduction: every OTHER pairing in the source is already a
# standard 27-nakshatra pairing, so this is the only cell affected.
# 14-animal canonical order and the 7 Mahabair (extreme-enmity, 0-point)
# pairs are directly cited from Muhurtha-Chinthamani p.167-168; same order
# independently corroborated by anytimeastro.com's Yoni Koota guide.
# Score scale (Mahabair=0, Bair=1, neutral=2, Mitra=3, Ati-mitra/same=4):
# Muhurtha-Chinthamani p.168.
# Full 14x14 matrix (the ~70 non-enemy, non-same pairs the classical source
# does not enumerate numerically): AstroSage's own matrix is not published
# anywhere publicly findable (confirmed via 5 distinct web search/fetch
# attempts, including a direct fetch of astrosage.com's own matchmaking
# page). Locked to naturalstupid/PyJHora's YoniArray instead, per explicit
# user sign-off this session -- 100% cross-validated against the classical
# anchor above (all 7 Mahabair pairs score exactly 0, all 14 same-yoni
# pairs score exactly 4, zero divergence). Cited as PyJHora, not AstroSage --
# no provenance overclaim.
# ============================================================================

YONI_ANIMALS = (
    "Ashwa", "Gaja", "Mesha", "Sarpa", "Shwana", "Marjara", "Mushaka",
    "Gow", "Mahisha", "Vyaghra", "Mriga", "Vanara", "Nakula", "Simha",
)  # Horse, Elephant, Ram, Serpent, Dog, Cat, Rat, Cow, Buffalo, Tiger, Deer, Monkey, Mongoose, Lion

YONI_BY_NAKSHATRA: dict[int, str] = {
    0: "Ashwa",      # Ashwini
    1: "Gaja",       # Bharani
    2: "Mesha",      # Krittika
    3: "Sarpa",      # Rohini
    4: "Sarpa",      # Mrigashira
    5: "Shwana",     # Ardra
    6: "Marjara",    # Punarvasu
    7: "Mesha",      # Pushya
    8: "Marjara",    # Ashlesha
    9: "Mushaka",    # Magha
    10: "Mushaka",   # Purva Phalguni
    11: "Gow",       # Uttara Phalguni
    12: "Mahisha",   # Hasta
    13: "Vyaghra",   # Chitra
    14: "Mahisha",   # Swati
    15: "Vyaghra",   # Vishakha
    16: "Mriga",     # Anuradha
    17: "Mriga",     # Jyeshtha
    18: "Shwana",    # Mula
    19: "Vanara",    # Purva Ashadha
    20: "Nakula",    # Uttara Ashadha (Abhijit folded in here -- see citation above)
    21: "Vanara",    # Shravana
    22: "Simha",     # Dhanishtha
    23: "Ashwa",     # Shatabhisha
    24: "Simha",     # Purva Bhadrapada
    25: "Gow",       # Uttara Bhadrapada
    26: "Gaja",      # Revati
}

# The 7 Mahabair (extreme-enmity, 0-point) pairs -- explicit classical
# citation, Muhurtha-Chinthamani p.167-168.
YONI_MAHABAIR_PAIRS = frozenset({
    frozenset({"Ashwa", "Mahisha"}),
    frozenset({"Gaja", "Simha"}),
    frozenset({"Mesha", "Vanara"}),
    frozenset({"Nakula", "Sarpa"}),
    frozenset({"Mriga", "Shwana"}),
    frozenset({"Marjara", "Mushaka"}),
    frozenset({"Vyaghra", "Gow"}),
})

# Full 14x14 score matrix, row/column order == YONI_ANIMALS. Source: see
# module-section citation above (PyJHora YoniArray, cross-validated against
# YONI_MAHABAIR_PAIRS (all 0) and the same-yoni diagonal (all 4) with zero
# divergence).
YONI_SCORE_MATRIX: tuple[tuple[int, ...], ...] = (
    (4, 2, 2, 3, 2, 2, 2, 1, 0, 1, 1, 3, 2, 1),  # Ashwa
    (2, 4, 3, 3, 2, 2, 2, 2, 3, 1, 2, 3, 2, 0),  # Gaja
    (2, 3, 4, 2, 1, 2, 1, 3, 3, 1, 2, 0, 3, 1),  # Mesha
    (3, 3, 2, 4, 2, 1, 1, 1, 1, 2, 2, 2, 0, 2),  # Sarpa
    (2, 2, 1, 2, 4, 2, 1, 2, 2, 1, 0, 2, 1, 1),  # Shwana
    (2, 2, 2, 1, 2, 4, 0, 2, 2, 1, 3, 3, 2, 1),  # Marjara
    (2, 2, 1, 1, 1, 0, 4, 2, 2, 2, 2, 2, 1, 2),  # Mushaka
    (1, 2, 3, 1, 2, 2, 2, 4, 3, 0, 3, 2, 2, 1),  # Gow
    (0, 3, 3, 1, 2, 2, 2, 3, 4, 1, 2, 2, 2, 1),  # Mahisha
    (1, 1, 1, 2, 1, 1, 2, 0, 1, 4, 1, 1, 2, 1),  # Vyaghra
    (1, 2, 2, 2, 0, 3, 2, 3, 2, 1, 4, 2, 2, 1),  # Mriga
    (3, 3, 0, 2, 2, 3, 2, 2, 2, 1, 2, 4, 3, 2),  # Vanara
    (2, 2, 3, 0, 1, 2, 1, 2, 2, 2, 2, 3, 4, 2),  # Nakula
    (1, 0, 1, 2, 1, 1, 2, 1, 1, 1, 1, 2, 2, 4),  # Simha
)


# ============================================================================
# 5. GRAHA MAITRI KOOTA (max 5 points)
# Friendship matrix reused, NOT duplicated: see NATURAL_FRIENDSHIP import
# at the top of this file (agent/calculations/core/_friendship_tables.py,
# PVR Table 7, cross-validated against 4 AstroSage PDFs). That table is the
# single source of truth for "Friend"/"Neutral"/"Enemy" between the 7
# classical planets -- the only planets relevant here, since no rashi is
# classically lorded by Rahu/Ketu (see SIGN_LORD below).
#
# What's new here is the KOOTA SCORE RUBRIC (how many points a friendship-
# pair outcome is worth), which is a distinct concept from the friendship
# matrix itself:
# Source: Muhurtha-Chinthamani p.172 (immediately preceding the GANA-KOOTA
# heading -- this is the Graha Maitri score table, PVR's own chapter
# doesn't name it but the text is unambiguous): "If the Lord... is the same
# or if there is friendship between them, 5 gunas; if one is friend and the
# other neutral, 4 Gunas; if both are neutral, 3 Gunas; if one is friend
# and the other enemy, 2 Gunas; if one is neutral and the other enemy, zero
# Guna." The classical source gives no enemy-enemy value at all, and its
# friend-enemy(2)/neutral-enemy(0) values diverge from AstroSage/modern
# convention's friend-enemy(1)/neutral-enemy(0.5) -- per this module's
# locked AstroSage-on-divergence rule, the AstroSage-convention numbers are
# used for those two cells and for the unstated enemy-enemy(0) cell; the
# top 3 tiers (5/4/3) agree across both sources and are not in dispute.
# "Same lord" -> 5 is a same-lord check, not a friendship-relation pair;
# left to the future calculator (it already has SIGN_LORD below).
# ============================================================================

GRAHA_MAITRI_SCORE: dict[tuple[str, str], float] = {
    ("Friend", "Friend"): 5,
    ("Friend", "Neutral"): 4, ("Neutral", "Friend"): 4,
    ("Neutral", "Neutral"): 3,
    ("Friend", "Enemy"): 1, ("Enemy", "Friend"): 1,        # classical: 2 -- AstroSage chosen (divergence)
    ("Neutral", "Enemy"): 0.5, ("Enemy", "Neutral"): 0.5,  # classical: 0 -- AstroSage chosen (divergence)
    ("Enemy", "Enemy"): 0,                                  # not given by the classical source at all
}

# Sign-lord mapping, shared by Graha Maitri and Bhakoot. Derived by
# inversion from agent/calculations/core/_dignity_tables.py's OWN_SIGNS
# (PVR Section 3.3) -- not re-cited from a new source, just re-keyed
# sign->lord instead of lord->signs. Only the 7 classical planets ever
# appear as values: no rashi is classically lorded by Rahu/Ketu.
SIGN_LORD: dict[int, str] = {
    0: "Mars",      # Aries
    1: "Venus",     # Taurus
    2: "Mercury",   # Gemini
    3: "Moon",      # Cancer
    4: "Sun",       # Leo
    5: "Mercury",   # Virgo
    6: "Venus",     # Libra
    7: "Mars",      # Scorpio
    8: "Jupiter",   # Sagittarius
    9: "Saturn",    # Capricorn
    10: "Saturn",   # Aquarius
    11: "Jupiter",  # Pisces
}


# ============================================================================
# 6. GANA KOOTA (max 6 points)
# Nakshatra mapping source: Muhurtha-Chinthamani p.172-173 ("GANA-KOOTA").
# Score values: classical source is qualitative only ("excessive love" for
# same-gana, "average" for Deva-Manushya, "death" for Manushya-Rakshasa,
# "quarrel" for Deva-Rakshasa) and does not commit to numbers for the two
# cross-gana-with-Rakshasa cells; AstroSage/modern convention (cited
# consistently across anytimeastro.com, astroassured.com, et al.) gives an
# explicit, internally consistent numeric table -- used here per this
# module's AstroSage-on-divergence rule. The qualitative-vs-numeric
# severity tension (is "death" worse than "quarrel", and does that imply
# Manushya-Rakshasa should score lower than Deva-Rakshasa?) is flagged
# here, not silently resolved by re-deriving numbers from the prose.
# ============================================================================

GANA_GROUPS = ("Deva", "Manushya", "Rakshasa")

GANA_BY_NAKSHATRA: dict[int, str] = {
    0: "Deva",       # Ashwini
    1: "Manushya",   # Bharani
    2: "Rakshasa",   # Krittika
    3: "Manushya",   # Rohini
    4: "Deva",       # Mrigashira
    5: "Manushya",   # Ardra
    6: "Deva",       # Punarvasu
    7: "Deva",       # Pushya
    8: "Rakshasa",   # Ashlesha
    9: "Rakshasa",   # Magha
    10: "Manushya",  # Purva Phalguni
    11: "Manushya",  # Uttara Phalguni
    12: "Deva",      # Hasta
    13: "Rakshasa",  # Chitra
    14: "Deva",      # Swati
    15: "Rakshasa",  # Vishakha
    16: "Deva",      # Anuradha
    17: "Rakshasa",  # Jyeshtha
    18: "Rakshasa",  # Mula
    19: "Manushya",  # Purva Ashadha
    20: "Manushya",  # Uttara Ashadha
    21: "Deva",      # Shravana
    22: "Rakshasa",  # Dhanishtha
    23: "Rakshasa",  # Shatabhisha
    24: "Manushya",  # Purva Bhadrapada
    25: "Manushya",  # Uttara Bhadrapada
    26: "Deva",      # Revati
}

GANA_SCORE: dict[tuple[str, str], int] = {
    ("Deva", "Deva"): 6, ("Manushya", "Manushya"): 6, ("Rakshasa", "Rakshasa"): 6,
    ("Deva", "Manushya"): 5, ("Manushya", "Deva"): 5,
    ("Manushya", "Rakshasa"): 1, ("Rakshasa", "Manushya"): 1,
    ("Deva", "Rakshasa"): 0, ("Rakshasa", "Deva"): 0,
}


# ============================================================================
# 7. BHAKOOT KOOTA (max 7 points)
# Source: Muhurtha-Chinthamani p.173-174 -- house-distance between the two
# Janma Rashis (Moon signs), counted 1-12. {2,12}="poverty", {5,9}="loss of
# progeny", {6,8}="giver of death" are inauspicious (0 points pre-
# cancellation); all other distances (1,3,4,7,10,11) are auspicious (7
# points, the max).
# Cancellation rules (locked decisions): Bhakoot has three classical dosha
# types -- Dwirdwadash {2,12}, Nav-Pancham {5,9}, Shadashtak {6,8} -- and
# all three share the same primary cancellation rule. Locked via a 9-agent
# silent deliberation cross-validated across 12 independent sources
# (PyJHora, astroyogi, astrologymag/Navneet Khanna, astrosight, truthstar,
# kundalimatches, ganeshmitra, vama, instaastro, pawankaushik, 108astro,
# astronidan), P2.4.1b design chat.
# - Same Rashi lord cancels (any of the three dosha types), OR
# - Mutual Naisargika friend Rashi lords cancels (any of the three),
#   reusing NATURAL_FRIENDSHIP + SIGN_LORD above.
# - "Mutual" = STRICT: both NATURAL_FRIENDSHIP[A][B] == "Friend" AND
#   NATURAL_FRIENDSHIP[B][A] == "Friend". Asymmetric Friend/Neutral pairs
#   (e.g. Moon-Jupiter) do NOT qualify. Deliberate conservative choice,
#   consistent with P2.4.0's existing "mutual" language -- this is the
#   contract the future calculator must follow.
# Source: Muhurtha-Chinthamani p.176 ("If there is no friendship between
# the Lords... Dusta Bhakoota ... 5 kinds of removal" -- lists same-lord
# and friend-lords first).
# {6,8} resolution history: P2.4.0 left {6,8} as an explicit TODO because
# the surrounding OCR (p.173-177) was heavily degraded and at one point
# cross-referenced "Dusta Gana" mid-Bhakoota-discussion, making fine-
# grained sub-rule attribution unreliable from the source PDF alone. That
# TODO is now resolved by the 12-source cross-validation above: cross-
# source unanimity confirms {6,8} uses the same rule as {5,9}. The original
# OCR-degradation concern is acknowledged as the original reason for
# deferral, now superseded by this cross-source agreement.
# A further nuance -- p.173-174 also documents that 6 specific otherwise-
# auspicious 4th/10th sign-pairs (Capricorn/Libra, Taurus/Leo, Aries/
# Cancer, Gemini/Pisces, Sagittarius/Virgo, Aquarius/Scorpio) are
# inauspicious anyway because their lords are mutual enemies -- cited for
# completeness, NOT implemented (a calculator-layer refinement, out of
# scope for a constants-only phase, same treatment as Varna's lord-
# override exception above).
# V1.1 KNOWN EXPANSIONS (deferred, not implemented here):
# - Navamsa-lord cancellation pathway: a parallel cancellation check
#   against the Navamsa (D9) Rashi lords, not just the Rashi (D1) lords
#   used above. Cited via BPHS and Phaladeepika (per astrosight), and
#   independently corroborated by truthstar, mysticgazer, foresightindia,
#   and astrologymag/Navneet Khanna -- including a contested severity
#   exception specifically for {6,8} (per ganeshmitra) that is NOT cross-
#   source-unanimous and needs its own resolution pass before
#   implementation. This is a V1 scoping choice supported by classical
#   sources, NOT a claim that V1's rule-set is classically exhaustive.
# - Meta-cancellation: "no other dosha present" cancels Bhakoot dosha
#   outright (cite truthstar). Deferred as a known classical refinement.
# - The 4/10 enemy-lords exception documented in the "further nuance"
#   paragraph above also remains V1.1 territory.
# ============================================================================

BHAKOOT_SCORE_BY_DISTANCE: dict[int, int] = {
    1: 7, 2: 0, 3: 7, 4: 7, 5: 0, 6: 0,
    7: 7, 8: 0, 9: 0, 10: 7, 11: 7, 12: 0,
}  # key: classical 1-12 house count from one Janma Rashi to the other

BHAKOOT_DISTANCE_EFFECT: dict[int, str] = {
    2: "poverty", 12: "poverty",
    5: "loss_of_progeny", 9: "loss_of_progeny",
    6: "death", 8: "death",
}  # qualitative effect name per inauspicious distance; citation flavor only

BHAKOOT_CANCELLATION_RULES: dict[tuple[int, int], str | None] = {
    (2, 12): "same_lord_or_friend_lords",  # Dwirdwadash -- source: 12-source cross-validation, P2.4.1b design chat lock
    (5, 9): "same_lord_or_friend_lords",   # Nav-Pancham -- source: 12-source cross-validation, P2.4.1b design chat lock
    (6, 8): "same_lord_or_friend_lords",   # Shadashtak -- source: 12-source cross-validation, P2.4.1b design chat lock
}


# ============================================================================
# 8. NADI KOOTA (max 8 points)
# Source: Muhurtha-Chinthamani p.177-178 ("NADI KOOTA"). Clean partition of
# all 27 nakshatras into Adi/Madhya/Antya, 9 each. Same Nadi = inauspicious
# (0 points); different Nadi = auspicious (8 points, the max).
# V1 calculator: pure binary lookup (same-Nadi=0, different-Nadi=8).
# No cancellation applied. AstroSage empirical lock, June 2026.
# Classical cancellation rule (MC p.180, same nakshatra different pada)
# preserved in NADI_CANCELLATION_RULE_CLASSICAL_V1_1 for V1.1.
# V1 calculator: pure binary lookup only (same-Nadi=0,
# different-Nadi=8). No cancellation path. AstroSage empirical lock,
# June 2026. See NADI_CANCELLATION_RULE_CLASSICAL_V1_1 for V1.1
# expansion.
# ============================================================================

NADI_GROUPS = ("Adi", "Madhya", "Antya")

NADI_BY_NAKSHATRA: dict[int, str] = {
    0: "Adi",       # Ashwini
    1: "Madhya",    # Bharani
    2: "Antya",     # Krittika
    3: "Antya",     # Rohini
    4: "Madhya",    # Mrigashira
    5: "Adi",       # Ardra
    6: "Adi",       # Punarvasu
    7: "Madhya",    # Pushya
    8: "Antya",     # Ashlesha
    9: "Antya",     # Magha
    10: "Madhya",   # Purva Phalguni
    11: "Adi",      # Uttara Phalguni
    12: "Adi",      # Hasta
    13: "Madhya",   # Chitra
    14: "Antya",    # Swati
    15: "Antya",    # Vishakha
    16: "Madhya",   # Anuradha
    17: "Adi",      # Jyeshtha
    18: "Adi",      # Mula
    19: "Madhya",   # Purva Ashadha
    20: "Antya",    # Uttara Ashadha
    21: "Antya",    # Shravana
    22: "Madhya",   # Dhanishtha
    23: "Adi",      # Shatabhisha
    24: "Adi",      # Purva Bhadrapada
    25: "Madhya",   # Uttara Bhadrapada
    26: "Antya",    # Revati
}

NADI_SCORE: dict[tuple[str, str], int] = {
    ("Adi", "Adi"): 0, ("Adi", "Madhya"): 8, ("Adi", "Antya"): 8,
    ("Madhya", "Adi"): 8, ("Madhya", "Madhya"): 0, ("Madhya", "Antya"): 8,
    ("Antya", "Adi"): 8, ("Antya", "Madhya"): 8, ("Antya", "Antya"): 0,
}

NADI_CANCELLATION_RULE_CLASSICAL_V1_1 = "same_nakshatra_different_pada"
# V1.1 EXPANSION -- NOT applied in V1 Nadi calculator.
# Classical source: Muhurtha-Chinthamani p.180 ("THE REMOVAL OF
# NADI DOSHA... if the Nakshatras are the same but the quarters
# [padas] of the Nakshatras are different, it is also regarded
# auspicious"). This is an explicit, clean classical citation.
#
# WHY NOT IN V1: AstroSage empirical testing (three synthetic pairs
# designed to isolate Rules #1 and #3 independently, June 2026,
# P2.4.1c design chat) showed AstroSage applies ZERO cancellation
# logic -- raw same-Nadi = 0, different-Nadi = 8, always. Per the
# locked three-tier source hierarchy (AstroSage parity > PyJHora >
# classical anchor when sources conflict on algorithm behavior),
# V1 matches AstroSage. Classical rule preserved here for V1.1.
#
# NOTE ON MISNOMER FIX: the prior constant was named
# "same_sign_different_pada" -- this was a misnomer ("sign" !=
# "nakshatra" in Vedic terminology). The classical citation above
# uses nakshatra-level granularity (same Nakshatra, different Pada),
# not sign-level. The rename corrects the terminology for V1.1
# implementation clarity.
