"""
solar_return_check.py
Standalone (non-pytest) manual check for calculate_solar_return().

Computes the Varshaphal (solar return) epoch for target_year=2026 using
the D1-validation natal fixture (Sulabh, 6 April 1988, 00:30 IST,
Calcutta, India) and prints both UTC and local datetimes for manual
comparison against an external Varshaphal reference (e.g. AstroSage).

Run from the repo root:
    python tests/manual/solar_return_check.py
"""

import sys
from datetime import datetime
from pathlib import Path

import pytz
import swisseph as swe

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.chart_calculator import (
    SIGN_LORDS,
    SIGNS,
    _calc_planets,
    build_varshaphal_chart,
    calculate_chart,
    calculate_solar_return,
)

TARGET_YEAR = 2026

# AstroSage's published Varshaphal 2026 epoch, for the diagnostic check below.
ASTROSAGE_EPOCH_UTC = datetime(2026, 4, 6, 12, 48, 20, tzinfo=pytz.utc)

if __name__ == "__main__":
    try:
        natal = calculate_chart("Sulabh", "6 April 1988", "00:30:00", "Calcutta, India")
        result = calculate_solar_return(natal, TARGET_YEAR)
        varshaphal = build_varshaphal_chart(natal, TARGET_YEAR)
    except (RuntimeError, ValueError) as exc:
        print(f"FAILED: {exc}")
        sys.exit(1)

    print(f"Solar return epoch for target_year={TARGET_YEAR}")
    print(f"  Natal Sun longitude (sidereal): {result['natal_sun_longitude']}")
    print(f"  Return Sun longitude (sidereal): {result['sun_longitude']}")
    print(f"  UTC datetime:   {result['utc_datetime']}")
    print(f"  Local datetime: {result['local_datetime']} (Asia/Kolkata)")
    print(f"  jd_ut: {result['jd_ut']}")

    print(f"\nVarshaphal chart for target_year={TARGET_YEAR}")
    print(f"  Lagna: {varshaphal['lagna']} ({varshaphal['lagna_degree_in_sign']} deg in sign) (lord {varshaphal['lagna_lord']})")
    print(f"  Lagna boundary-sensitive: {varshaphal['lagna_boundary_sensitive']}")
    print(f"  Rasi:  {varshaphal['rasi']} (lord {varshaphal['rasi_lord']})")

    # --- DIAGNOSTIC (temporary, manual script only) -----------------------
    # Isolates epoch-finding (calculate_solar_return) from chart-construction
    # (build_varshaphal_chart's Lagna/planet block): re-run ONLY the
    # chart-construction logic at AstroSage's published fixed epoch
    # (2026-04-06 12:48:20 UTC = 18:18:20 IST), using the same natal
    # birth-location lat/lon. No call to calculate_solar_return here.
    try:
        delta = result["utc_datetime"] - ASTROSAGE_EPOCH_UTC
        print(f"\nDIAGNOSTIC: chart construction at AstroSage's fixed epoch")
        print(f"  AstroSage epoch UTC: {ASTROSAGE_EPOCH_UTC} (= 18:18:20 IST)")
        print(f"  Epoch delta (ours - AstroSage): {delta}")

        lat = natal["birth_details"]["lat"]
        lon_geo = natal["birth_details"]["lon"]

        swe.set_sid_mode(swe.SIDM_LAHIRI)
        utc = ASTROSAGE_EPOCH_UTC
        fixed_jd = swe.julday(
            utc.year, utc.month, utc.day,
            utc.hour + utc.minute / 60.0 + utc.second / 3600.0,
        )
        _, ascmc = swe.houses(fixed_jd, lat, lon_geo, b"P")
        ayanamsha = swe.get_ayanamsa_ut(fixed_jd)
        asc_lon = (ascmc[0] - ayanamsha) % 360
        asc_sign = SIGNS[int(asc_lon / 30) % 12]
        planets = _calc_planets(fixed_jd, asc_lon)
        moon_sign = planets["Moon"]["sign"]

        print(f"  jd_ut: {round(fixed_jd, 6)}")
        print(f"  Lagna: {asc_sign} ({asc_lon % 30:.4f} deg in sign) (lord {SIGN_LORDS[asc_sign]})")
        print(f"  Rasi:  {moon_sign} (lord {SIGN_LORDS[moon_sign]})")
    except (RuntimeError, ValueError) as exc:
        print(f"DIAGNOSTIC FAILED: {exc}")
        sys.exit(1)
