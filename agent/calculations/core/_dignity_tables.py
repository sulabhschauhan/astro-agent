"""Planetary dignity tables per PVR §3.3 Table 6 + special-points list. Data only — no logic."""

# Source: PVR Narasimha Rao, "Vedic Astrology: An Integrated Approach", §3.3
# Table 6 (exaltation/debilitation rasi + deep-point degree) and the
# special-points list immediately below it (Moolatrikona + own-sign ranges).
#
# Rahu/Ketu follow PVR's Convention B (Rahu exalts Gemini, debilitates
# Sagittarius; Ketu the reverse) — differs from the popular Convention A
# (Taurus/Scorpio). PVR-authored JHora is the locked validation oracle, so
# PVR's own table prevails over the popular convention.
#
# PVR's Table 6 gives exaltation/debilitation rasi only for the nodes, no
# deep-point degree — Rahu/Ketu deep_degree is None.
#
# PVR's special-points list gives no Moolatrikona degree range for the
# nodes — Rahu/Ketu MT entries default to the full sign (0.0-30.0).
#
# Strangler-fig replacement: this module is the authoritative source going
# forward. chart_calculator.py's EXALTATION / DEBILITATION / _OWN_SIGNS
# legacy dicts are not migrated or touched here.

EXALTATION: dict[str, tuple[str, float | None]] = {
    "Sun":     ("Aries", 10.0),
    "Moon":    ("Taurus", 3.0),
    "Mars":    ("Capricorn", 28.0),
    "Mercury": ("Virgo", 15.0),
    "Jupiter": ("Cancer", 5.0),
    "Venus":   ("Pisces", 27.0),
    "Saturn":  ("Libra", 20.0),
    "Rahu":    ("Gemini", None),
    "Ketu":    ("Sagittarius", None),
}

DEBILITATION: dict[str, tuple[str, float | None]] = {
    "Sun":     ("Libra", 10.0),
    "Moon":    ("Scorpio", 3.0),
    "Mars":    ("Cancer", 28.0),
    "Mercury": ("Pisces", 15.0),
    "Jupiter": ("Capricorn", 5.0),
    "Venus":   ("Virgo", 27.0),
    "Saturn":  ("Aries", 20.0),
    "Rahu":    ("Sagittarius", None),
    "Ketu":    ("Gemini", None),
}

MOOLATRIKONA: dict[str, tuple[str, float, float]] = {
    "Sun":     ("Leo", 0.0, 20.0),
    "Moon":    ("Taurus", 3.0, 30.0),
    "Mars":    ("Aries", 0.0, 12.0),
    "Mercury": ("Virgo", 15.0, 20.0),
    "Jupiter": ("Sagittarius", 0.0, 10.0),
    "Venus":   ("Libra", 0.0, 15.0),
    "Saturn":  ("Aquarius", 0.0, 20.0),
    "Rahu":    ("Virgo", 0.0, 30.0),    # PVR silent on degree range for nodes
    "Ketu":    ("Pisces", 0.0, 30.0),   # same — defaults to full sign
}

OWN_SIGNS: dict[str, list[tuple[str, float, float]]] = {
    "Sun":     [("Leo", 20.0, 30.0)],
    "Moon":    [("Cancer", 0.0, 30.0)],
    "Mars":    [("Aries", 12.0, 30.0), ("Scorpio", 0.0, 30.0)],
    "Mercury": [("Gemini", 0.0, 30.0), ("Virgo", 20.0, 30.0)],
    "Jupiter": [("Pisces", 0.0, 30.0), ("Sagittarius", 10.0, 30.0)],
    "Venus":   [("Taurus", 0.0, 30.0), ("Libra", 15.0, 30.0)],
    "Saturn":  [("Capricorn", 0.0, 30.0), ("Aquarius", 20.0, 30.0)],
    "Rahu":    [("Aquarius", 0.0, 30.0)],
    "Ketu":    [("Scorpio", 0.0, 30.0)],
}
