"""Classical name table for the lunar months (masa). Name data only -- no logic.

Mirrors the role of `_panchanga_tables.py`: a label table, not doctrine. The RULE
that selects an index lives in `masa.py`; this file only says what index 0 is
called.

ORDER: the twelve lunar months in their canonical sequence beginning with
Chaitra. Index i is the month in which the Sun enters the rashi of index i
counted from Mesha -- i.e. the month containing Mesha sankranti is index 0,
Chaitra. VERIFIED BY MEASUREMENT (S148, Lahiri nirayana, Moshier backend): the
amanta month [2026-03-19 01:23 UT .. 2026-04-17 11:52 UT] contains exactly the
Mesha ingress (2026-04-14 04:02 UT) and is Chaitra. An earlier draft of this
layer used index = rashi + 1 and would have named every month after its
successor; the measurement is what caught it, not a recollection.
"""

# 12 entries. Index = rashi index (0 = Mesha .. 11 = Meena) of the solar ingress
# contained in the lunar month. See masa.py for the selection rule and its limits.
MASA_NAMES: tuple[str, ...] = (
    "Chaitra",      # 0  -- contains Mesha sankranti
    "Vaishakha",    # 1  -- Vrishabha
    "Jyeshtha",     # 2  -- Mithuna
    "Ashadha",      # 3  -- Karka
    "Shravana",     # 4  -- Simha
    "Bhadrapada",   # 5  -- Kanya
    "Ashwina",      # 6  -- Tula
    "Kartika",      # 7  -- Vrischika
    "Margashirsha",  # 8  -- Dhanu
    "Pausha",       # 9  -- Makara
    "Magha",        # 10 -- Kumbha
    "Phalguna",     # 11 -- Meena
)

# Sidereal rashi names, 0-indexed from Mesha. Present so a consumer never has to
# re-derive the mapping from a number; same data-only status as MASA_NAMES.
RASHI_NAMES: tuple[str, ...] = (
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena",
)
