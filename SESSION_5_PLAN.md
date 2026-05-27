## chart_calculator.py Design (locked before Session 5)

- **Location:** `agent/chart_calculator.py`
- **Input:** `name, dob, tob, place` (city, country string)
- **Output:** `kundali_context` dict matching `kundali_summary.txt` format
- **Engine:** pyswisseph with `SIDM_LAHIRI` ayanamsha
- **Timezone:** IST handling (critical — birth times are local Indian time)
- **Geocoding:** geopy for lat/lon from city name
- **Verification:** must match Sulabh's AstroSage chart exactly before use in prod
- **Dependencies:** `pyswisseph`, `geopy`