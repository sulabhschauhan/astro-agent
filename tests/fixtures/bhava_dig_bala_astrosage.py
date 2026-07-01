"""
Bhava Dig Bala reference values for 4 charts (Sulabh, Surbhi, Sheridan, David).

Source: AstroSage PDF per-chart BhavBala Table, transcribed via design-chat
during Session 42 (2026-07-01), cross-checked against CLAUDE.md Session 41
anomaly note (Sulabh house 4 = 0) for consistency. Not OCR'd or re-derived
by the assistant -- direct user transcription of each chart's AstroSage PDF
"Shadbala and Bhavabala" page, Bhavdig Bala row, into this file.

Values are Virupa (1 Rupa = 60 Virupa), integer-valued per house 1-12 --
compute_bhava_dig_bala's rasi-animal-group taper only ever produces clean
multiples of 10 (see agent/calculations/strength/bhava_bala.py), so exact
match (not tolerance-band) assertions are appropriate here, unlike the
Kala/Chesta Bala fixtures elsewhere in this suite.
"""

BHAVA_DIG_BALA_ASTROSAGE: dict[str, dict[int, float]] = {
    "sulabh": {
        1: 30.0, 2: 40.0, 3: 50.0, 4: 0.0, 5: 10.0, 6: 20.0,
        7: 0.0, 8: 20.0, 9: 20.0, 10: 30.0, 11: 20.0, 12: 10.0,
    },
    "surbhi": {
        1: 60.0, 2: 50.0, 3: 10.0, 4: 30.0, 5: 50.0, 6: 20.0,
        7: 30.0, 8: 10.0, 9: 10.0, 10: 60.0, 11: 40.0, 12: 50.0,
    },
    "sheridan": {
        1: 30.0, 2: 40.0, 3: 10.0, 4: 30.0, 5: 20.0, 6: 50.0,
        7: 60.0, 8: 40.0, 9: 20.0, 10: 0.0, 11: 50.0, 12: 40.0,
    },
    "david": {
        1: 60.0, 2: 50.0, 3: 20.0, 4: 30.0, 5: 10.0, 6: 10.0,
        7: 30.0, 8: 40.0, 9: 50.0, 10: 30.0, 11: 10.0, 12: 40.0,
    },
}
