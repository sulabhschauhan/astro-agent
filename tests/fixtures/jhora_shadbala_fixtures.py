"""
JHora v8 Shadbala component fixtures for cross-validation.
Source: JHora v8 exports provided manually by Sulabh (Sessions 35-36).
Oracle role: SECONDARY — AstroSage is primary. Use JHora to diagnose
source divergences, not to override AstroSage fixture assertions.

Units: Virupa throughout (same as shadbala_fixtures.py).
Kala Bala column in JHora includes Ayana but NOT Chesta — Chesta is
reported separately. Total Shadbala = Sthana + Kala + Dig + Chesta +
Naisargika + Drik (6 components).
"""

JHORA_SHADBALA: dict[str, dict] = {
    "sulabh": {
        "meta": {
            "birth_date": "1988-04-06",
            "birth_time": "00:30 IST",
            "place": "Calcutta",
            "source": "JHora v8, Sulabh chart, Sessions 35-36",
        },
        "shadbala_components": {
            # columns: sthana, kala, dig, chesta, naisargika, drik, total_virupa, total_rupa
            "sun":     {"sthana": 211.68, "kala": 88.89,  "dig": 0.06,  "chesta": 35.18, "naisargika": 60.00, "drik": -17.22, "total_virupa": 343.41, "total_rupa": 5.72},
            "moon":    {"sthana": 157.75, "kala": 237.70, "dig": 13.18, "chesta": 46.76, "naisargika": 51.43, "drik":   5.84, "total_virupa": 465.89, "total_rupa": 7.76},
            "mars":    {"sthana": 240.03, "kala": 137.09, "dig": 25.71, "chesta": 30.34, "naisargika": 17.14, "drik":  16.39, "total_virupa": 466.70, "total_rupa": 7.78},
            "mercury": {"sthana": 219.87, "kala": 103.69, "dig": 34.94, "chesta":  3.19, "naisargika": 25.70, "drik":  -9.84, "total_virupa": 377.55, "total_rupa": 6.29},
            "jupiter": {"sthana": 197.52, "kala": 153.78, "dig": 23.38, "chesta":  7.81, "naisargika": 34.28, "drik": -15.24, "total_virupa": 401.53, "total_rupa": 6.69},
            "venus":   {"sthana": 213.09, "kala": 162.89, "dig": 44.79, "chesta": 20.85, "naisargika": 42.85, "drik":   1.46, "total_virupa": 485.94, "total_rupa": 8.10},
            "saturn":  {"sthana": 234.97, "kala": 193.04, "dig":  4.62, "chesta": 35.33, "naisargika":  8.57, "drik":  17.46, "total_virupa": 493.98, "total_rupa": 8.23},
        },
        "kala_bala_breakdown": {
            # JHora Kala Bala sub-components (Ayana included, Chesta separate above)
            "sun":     {"nathonnatha": 0.06,  "paksha": 13.24, "thribhaga": 0,  "abda": 0,  "masa": 0,  "vara": 0,  "hora": 0,  "ayana": 75.59, "yuddha": 0},
            "moon":    {"nathonnatha": 59.94, "paksha": 93.52, "thribhaga": 0,  "abda": 0,  "masa": 30, "vara": 0,  "hora": 0,  "ayana": 54.23, "yuddha": 0},
            "mars":    {"nathonnatha": 59.94, "paksha": 13.24, "thribhaga": 0,  "abda": 15, "masa": 0,  "vara": 45, "hora": 0,  "ayana": 3.91,  "yuddha": 0},
            "mercury": {"nathonnatha": 60.00, "paksha": 13.24, "thribhaga": 0,  "abda": 0,  "masa": 0,  "vara": 0,  "hora": 0,  "ayana": 30.45, "yuddha": 0},
            "jupiter": {"nathonnatha": 0.06,  "paksha": 46.76, "thribhaga": 60, "abda": 0,  "masa": 0,  "vara": 0,  "hora": 0,  "ayana": 46.96, "yuddha": 0},
            "venus":   {"nathonnatha": 0.06,  "paksha": 46.76, "thribhaga": 60, "abda": 0,  "masa": 0,  "vara": 0,  "hora": 0,  "ayana": 56.07, "yuddha": 0},
            "saturn":  {"nathonnatha": 59.94, "paksha": 13.24, "thribhaga": 0,  "abda": 0,  "masa": 0,  "vara": 0,  "hora": 60, "ayana": 59.87, "yuddha": 0},
        },
    },
    "surbhi": {
        "meta": {
            "birth_date": "1992-09-11",
            "birth_time": "10:30 IST",
            "place": "Patna",
            "source": "JHora v8, Surbhi chart, Session 36",
        },
        "shadbala_components": {
            "sun":     {"sthana": 150.01, "kala": 201.99, "dig": 51.64, "chesta": 34.01, "naisargika": 60.00, "drik":  -7.72, "total_virupa": 456.00, "total_rupa": 7.60},
            "moon":    {"sthana": 131.57, "kala": 162.61, "dig": 54.90, "chesta": 56.75, "naisargika": 51.43, "drik":   4.12, "total_virupa": 404.45, "total_rupa": 6.74},
            "mars":    {"sthana": 163.70, "kala":  71.51, "dig": 41.92, "chesta": 35.93, "naisargika": 17.14, "drik":  13.38, "total_virupa": 343.58, "total_rupa": 5.73},
            "mercury": {"sthana": 209.63, "kala": 154.58, "dig": 37.16, "chesta":  7.39, "naisargika": 25.70, "drik":  -6.37, "total_virupa": 427.95, "total_rupa": 7.13},
            "jupiter": {"sthana": 184.18, "kala": 291.94, "dig": 40.01, "chesta":  1.09, "naisargika": 34.28, "drik":  -9.59, "total_virupa": 541.91, "total_rupa": 9.03},
            "venus":   {"sthana": 124.48, "kala": 177.26, "dig": 16.43, "chesta": 16.17, "naisargika": 42.85, "drik":  -8.40, "total_virupa": 369.19, "total_rupa": 6.15},
            "saturn":  {"sthana": 180.32, "kala":  63.45, "dig": 26.38, "chesta": 48.36, "naisargika":  8.57, "drik":   0.42, "total_virupa": 327.50, "total_rupa": 5.46},
        },
        "kala_bala_breakdown": {
            "sun":     {"nathonnatha": 3.37,  "paksha": 51.64, "thribhaga": 3.25,  "abda": 60.00, "masa": 15.00, "vara": 0, "hora": 0, "ayana": 72.09, "yuddha": 0},
            "moon":    {"nathonnatha": 2.71,  "paksha": 8.36,  "thribhaga": 113.50,"abda": 0,     "masa": 0,     "vara": 0, "hora": 0, "ayana": 40.75, "yuddha": 0},
            "mars":    {"nathonnatha": 1.19,  "paksha": 8.36,  "thribhaga": 3.25,  "abda": 0,     "masa": 0,     "vara": 0, "hora": 0, "ayana": 59.90, "yuddha": 0},
            "mercury": {"nathonnatha": 2.58,  "paksha": 60.00, "thribhaga": 56.75, "abda": 0,     "masa": 0,     "vara": 0, "hora": 0, "ayana": 37.84, "yuddha": 0},
            "jupiter": {"nathonnatha": 4.87,  "paksha": 51.64, "thribhaga": 56.75, "abda": 60.00, "masa": 0,     "vara": 30,"hora": 60,"ayana": 33.55, "yuddha": 0},
            "venus":   {"nathonnatha": 2.95,  "paksha": 51.64, "thribhaga": 56.75, "abda": 0,     "masa": 0,     "vara": 0, "hora": 45,"ayana": 23.87, "yuddha": 0},
            "saturn":  {"nathonnatha": 1.06,  "paksha": 8.36,  "thribhaga": 3.25,  "abda": 0,     "masa": 0,     "vara": 0, "hora": 0, "ayana": 51.84, "yuddha": 0},
        },
    },
}
