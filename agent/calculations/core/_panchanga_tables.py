"""Classical name tables for Panchanga elements. Name data only — no logic."""

TITHI_NAMES = [
    "Sukla Pratipada", "Sukla Dwitiya", "Sukla Tritiya", "Sukla Chaturthi",
    "Sukla Panchami", "Sukla Shashti", "Sukla Saptami", "Sukla Ashtami",
    "Sukla Navami", "Sukla Dashami", "Sukla Ekadashi", "Sukla Dwadashi",
    "Sukla Trayodashi", "Sukla Chaturdashi", "Purnima",
    "Krishna Pratipada", "Krishna Dwitiya", "Krishna Tritiya", "Krishna Chaturthi",
    "Krishna Panchami", "Krishna Shashti", "Krishna Saptami", "Krishna Ashtami",
    "Krishna Navami", "Krishna Dashami", "Krishna Ekadashi", "Krishna Dwadashi",
    "Krishna Trayodashi", "Krishna Chaturdashi", "Amavasya",
]  # 30 entries; index = floor((moon_sid − sun_sid) % 360 / 12)

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
    "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishtha", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati",
]  # 27 entries; index = floor(moon_sid_lon / (360/27))

YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva",
    "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan",
    "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla",
    "Brahma", "Indra", "Vaidhriti",
]  # 27 entries; index = floor((moon_sid + sun_sid) % 360 / (360/27))

# 7 movable karanas cycling through slots 1–56 (8 full cycles = 56 slots)
_MOVABLE_KARANAS = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti"]


def _build_karana_sequence() -> list[str]:
    seq = ["Kintughna"]          # slot 0  — fixed, Sukla Pratipada first half
    for i in range(1, 57):       # slots 1–56 — movable, cycling
        seq.append(_MOVABLE_KARANAS[(i - 1) % 7])
    seq.append("Sakuni")         # slot 57 — fixed, Krishna Chaturdashi second half
    seq.append("Chatushpada")    # slot 58 — fixed, Amavasya first half
    seq.append("Naga")           # slot 59 — fixed, Amavasya second half
    return seq


KARANA_SEQ = _build_karana_sequence()  # 60 entries; index = floor((moon_sid − sun_sid) % 360 / 6)

# Vara names indexed by Python's weekday() — Monday=0 … Sunday=6
VARA_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Hora ruler sequence (Chaldean descending from Sun).
# The vara lord rules hora 0; subsequent horas advance through this list cyclically.
# Sequence verified: Sun at index 0 → after 24 horas → (0+24)%7=3 → Moon (Monday) ✓
HORA_SEQ = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]

# Position of each day's lord in HORA_SEQ (used to seed hora 0 for that vara)
VARA_LORD_INDEX: dict[str, int] = {
    "Sunday":    0,   # Sun    = HORA_SEQ[0]
    "Monday":    3,   # Moon   = HORA_SEQ[3]
    "Tuesday":   6,   # Mars   = HORA_SEQ[6]
    "Wednesday": 2,   # Mercury= HORA_SEQ[2]
    "Thursday":  5,   # Jupiter= HORA_SEQ[5]
    "Friday":    1,   # Venus  = HORA_SEQ[1]
    "Saturday":  4,   # Saturn = HORA_SEQ[4]
}

# ── Choghadiya ─────────────────────────────────────────────────────────────────
# 7 names cycling over 8 day-arc and 8 night-arc equal segments.
# Same Chaldean planetary-hour order as HORA_SEQ; CHOGHADIYA_NAMES[i] is ruled
# by the same planet as HORA_SEQ[i].
# Source: traditional North Indian almanac / Drik Panchang.
# PVR's book does not cover Choghadiya (muhurta topics absent from that text).
CHOGHADIYA_NAMES = ["Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog"]
CHOGHADIYA_QUALITY = [
    "inauspicious",  # Udveg — Sun lord
    "neutral",       # Char  — Venus lord
    "auspicious",    # Labh  — Mercury lord
    "auspicious",    # Amrit — Moon lord
    "inauspicious",  # Kaal  — Saturn lord
    "auspicious",    # Shubh — Jupiter lord
    "inauspicious",  # Rog   — Mars lord
]

# Day choghadiya start index = VARA_LORD_INDEX[vara_name] (reuses existing dict).
# Night start is offset by +5 mod 7 from the day start; stored explicitly here.
CHOG_NIGHT_START: dict[str, int] = {
    "Sunday":    5,   # Shubh
    "Monday":    1,   # Char
    "Tuesday":   4,   # Kaal
    "Wednesday": 0,   # Udveg
    "Thursday":  3,   # Amrit
    "Friday":    6,   # Rog
    "Saturday":  2,   # Labh
}

# ── Kalam windows ──────────────────────────────────────────────────────────────
# Each window occupies exactly one day-arc segment (day_length / 8).
# Indices are 0-based slot numbers; slot n → [sunrise + n×seg, sunrise + (n+1)×seg).
# Source: Drik Panchang / classical tradition.
# PVR's book does not cover these topics.
# Night versions are deferred to v2; not applicable here (fixed day-arc only).
# is_boundary flag NOT applied: these are fixed-slot lookups with no longitudinal
# ambiguity, so boundary propagation from tithi/nakshatra logic is not relevant.
# Indexed by Python weekday() — Mon=0 … Sun=6
RAHU_KALAM_SLOT   = [1, 6, 4, 5, 3, 2, 7]  # mnemonic "Mother Saw Father Wearing The Turban Suddenly"
YAMAGANDA_SLOT    = [3, 2, 1, 6, 5, 7, 4]  # source: Drik Panchang; Thu/Sat entries vary by text
GULIKA_KALAM_SLOT = [5, 4, 3, 2, 1, 0, 6]  # equivalent formula: (5 - weekday) % 7
