# Read Prompt

#Paste your instructions here. Then tell Claude: "Read .claude/read_prompt.md and execute"


CONTEXT:
Refactor migration paused (chart_calculator.py decomposition deferred 
to strangler-fig pattern after package grows). Now building NEW code 
in the calculations/ package. This is P1.2a — Panchanga module 
foundation: dataclasses + sunrise/sunset + skeleton function 
signature. No Panchanga element calculations in this prompt.

Tests must end 41/41 + new sunrise/sunset tests passing.

OBJECTIVE:
Implement the foundation layer of agent/calculations/core/panchanga.py:
1. Frozen dataclasses for PanchangaElement, ChoghadiyaWindow, Panchanga
2. calculate_sunrise() and calculate_sunset() pure functions
3. calculate_panchanga() function signature with NotImplementedError body
4. Test infrastructure with the 4 validation fixtures

EXACT FILES TO CREATE OR MODIFY:

1. agent/calculations/core/panchanga.py — populate the placeholder
2. tests/calculations/__init__.py — empty file if doesn't exist  
3. tests/calculations/fixtures/__init__.py — empty file
4. tests/calculations/fixtures/panchanga_fixtures.py — fixture data
5. tests/calculations/test_panchanga.py — sunrise/sunset tests only

DETAILED SPECIFICATION:

=== agent/calculations/core/panchanga.py ===

Module docstring: "Panchanga: tithi, vara, nakshatra, yoga, karana, 
hora, choghadiya, and muhurta-avoidance windows. Drik (ephemeris-based) 
calculation using Lahiri ayanamsa."

Imports needed:
- from dataclasses import dataclass
- from datetime import datetime, timedelta, timezone
- from typing import Optional
- import swisseph as swe

Module constants:
- AYANAMSA_FLAG = swe.SIDM_LAHIRI (set via swe.set_sid_mode at module 
  load — wrap in a helper to avoid global side effects on import; 
  apply per-call instead)
- BOUNDARY_THRESHOLD_PERCENT = 5.0  # for nakshatra/tithi boundary flag
- REFRACTION_ARCMIN = 34.0          # standard atmospheric refraction
- SUNRISE_FLAGS = swe.CALC_RISE | swe.BIT_DISC_CENTER  # NO — actually 
  use upper limb: swe.CALC_RISE (default upper limb, with refraction)
  
  Use this exact flag set:
      rise_flags = swe.CALC_RISE
      set_flags = swe.CALC_SET
  Both default to upper limb + atmospheric refraction in pyswisseph.

Dataclasses (ALL frozen, ALL with type hints):

    @dataclass(frozen=True)
    class PanchangaElement:
        name: str
        index: int
        percent_left: float
        next_name: str
        is_boundary: bool
        transition_time: datetime

    @dataclass(frozen=True)
    class ChoghadiyaWindow:
        name: str
        quality: str  # "auspicious" | "neutral" | "inauspicious"
        start: datetime
        end: datetime

    @dataclass(frozen=True)
    class Panchanga:
        moment: datetime
        location: tuple[float, float]  # (lat, lon)
        sunrise: datetime
        sunset: datetime
        tithi: PanchangaElement
        vara: PanchangaElement
        nakshatra: PanchangaElement
        nakshatra_pada: int
        yoga: PanchangaElement
        karana: PanchangaElement
        hora_lord: str
        choghadiya_day: list[ChoghadiyaWindow]
        choghadiya_night: list[ChoghadiyaWindow]
        rahu_kalam: tuple[datetime, datetime]
        yamaganda: tuple[datetime, datetime]
        gulika_kalam: tuple[datetime, datetime]
        abhijit_muhurta: Optional[tuple[datetime, datetime]]
        ayanamsa: float

Functions to implement in P1.2a:

    def _datetime_to_julian_day_ut(moment: datetime) -> float:
        """Convert timezone-aware datetime to Julian Day in UT.
        
        Raises ValueError if moment is naive (no tzinfo).
        """
        # Implementation: convert to UTC, then use swe.julday
        # Inline comment: pyswisseph julday expects UT, fractional hours

    def _julian_day_ut_to_datetime(jd_ut: float, tz: timezone) -> datetime:
        """Convert Julian Day (UT) back to timezone-aware datetime in tz."""

    def calculate_sunrise(date_local: datetime, latitude: float, 
                          longitude: float) -> datetime:
        """Visible sunrise (upper limb at apparent horizon, standard 
        atmospheric refraction) for the calendar date of date_local at 
        the given location.
        
        Returns timezone-aware datetime in same tz as input.
        
        Raises ValueError if date_local is naive.
        Raises ValueError if no sunrise on this date (polar latitudes).
        """
        # Use swe.rise_trans with rsmi=swe.CALC_RISE, body=swe.SUN
        # Anchor search at local midnight of date_local converted to JD UT
        # Result is JD UT — convert back to date_local's tz

    def calculate_sunset(date_local: datetime, latitude: float, 
                         longitude: float) -> datetime:
        """Visible sunset, same conventions as calculate_sunrise."""

    def calculate_panchanga(moment: datetime, latitude: float, 
                            longitude: float) -> Panchanga:
        """Compute full Panchanga at given moment + location.
        
        Args:
            moment: Timezone-aware datetime. Naive datetime raises 
                ValueError.
            latitude: Decimal degrees, positive N, negative S. 
                Must be in [-66.5, 66.5] (excludes polar regions per 
                v1 scope guard).
            longitude: Decimal degrees, positive E, negative W.
        
        Raises ValueError on naive datetime or out-of-scope latitude.
        """
        raise NotImplementedError("P1.2b — core five + hora")

INPUT VALIDATION (apply in calculate_sunrise, calculate_sunset, 
calculate_panchanga):
- if moment.tzinfo is None: raise ValueError("moment must be 
  timezone-aware")
- if not -66.5 <= latitude <= 66.5: raise ValueError(f"latitude 
  {latitude} outside v1 supported range [-66.5, 66.5]")
- if not -180 <= longitude <= 180: raise ValueError

DESIGN CONSTRAINTS:
- All datetime returns must be timezone-aware
- No mutable module state (set ayanamsa per-call inside functions, 
  not at module load)
- No print statements
- Every function has a docstring
- Inline comments only where the swisseph API is non-obvious

=== tests/calculations/fixtures/panchanga_fixtures.py ===

Module docstring describing the 8-fixture validation strategy.

Define fixtures as a list of dicts. Each fixture has:
- name: str  (e.g. "Sulabh_20260616_1230_IST")
- moment: datetime (timezone-aware)
- latitude: float
- longitude: float
- expected_sunrise: time (HH:MM:SS)
- expected_sunset: time
- expected_tithi_name, tithi_percent_left, etc.  (full Panchanga 
  expected values — populate even though tests don't yet assert 
  them; P1.2b will use them)

Hard-coded fixtures (8 total):

# Birth-moment fixtures — populated from existing AstroSage + JHora data
# (P1.2a only needs Sulabh, Surbhi, Sheridan, David at 2026-06-16 fixtures
# for sunrise/sunset testing; birth-moment fixtures added but unused in P1.2a)

# 12:30 local fixtures (these are what JHora generated):
FIXTURES = [
    {
        "name": "Sulabh_20260616_1230_IST",
        "moment": datetime(2026, 6, 16, 12, 30, 0, 
                           tzinfo=timezone(timedelta(hours=5, minutes=30))),
        "latitude": 22 + 34/60,         # 22°34'N (Calcutta — JHora)
        "longitude": 88 + 22/60,        # 88°22'E
        "expected_sunrise_hms": (4, 55, 52),
        "expected_sunset_hms": (18, 18, 38),
        "expected_tithi_name": "Sukla Dwitiya",
        "expected_tithi_percent_left": 60.66,
        "expected_nakshatra_name": "Ardra",
        "expected_nakshatra_pada": None,  # JHora doesn't print pada in Key Info
        "expected_nakshatra_percent_left": 17.37,
        "expected_yoga_name": "Vriddhi",
        "expected_yoga_percent_left": 60.16,
        "expected_karana_name": "Balava",
        "expected_karana_percent_left": 21.31,
        "expected_vara_name": "Tuesday",
        "expected_hora_lord": "Mars",
        "expected_ayanamsa_dms": (24, 12, 38.22),
    },
    {
        "name": "Surbhi_20260616_1230_IST",
        "moment": datetime(2026, 6, 16, 12, 30, 0,
                           tzinfo=timezone(timedelta(hours=5, minutes=30))),
        "latitude": 27 + 50/60,         # 27°50'N (Patna)
        "longitude": 81 + 46/60,        # 81°46'E
        "expected_sunrise_hms": (5, 10, 54),
        "expected_sunset_hms": (18, 56, 24),
        "expected_tithi_name": "Sukla Dwitiya",
        "expected_tithi_percent_left": 60.66,
        "expected_nakshatra_name": "Ardra",
        "expected_nakshatra_percent_left": 17.37,
        "expected_yoga_name": "Vriddhi",
        "expected_yoga_percent_left": 60.16,
        "expected_karana_name": "Balava",
        "expected_karana_percent_left": 21.31,
        "expected_vara_name": "Tuesday",
        "expected_hora_lord": "Mars",
        "expected_ayanamsa_dms": (24, 12, 38.22),
    },
    {
        "name": "Sheridan_20260616_1230_SAST",
        "moment": datetime(2026, 6, 16, 12, 30, 0,
                           tzinfo=timezone(timedelta(hours=2))),
        "latitude": -(29 + 51/60),      # 29°51'S (Durban)
        "longitude": 31 + 1/60,         # 31°01'E
        "expected_sunrise_hms": (6, 54, 0),
        "expected_sunset_hms": (16, 59, 17),
        "expected_tithi_name": "Sukla Dwitiya",
        "expected_tithi_percent_left": 43.45,
        "expected_nakshatra_name": "Ardra",
        "expected_nakshatra_percent_left": 0.85,
        "expected_yoga_name": "Vriddhi",
        "expected_yoga_percent_left": 42.59,
        "expected_karana_name": "Kaulava",
        "expected_karana_percent_left": 86.91,
        "expected_vara_name": "Tuesday",
        "expected_hora_lord": "Saturn",
        "expected_ayanamsa_dms": (24, 12, 38.24),
        "notes": "Hardest case — Nakshatra boundary at 0.85% left of Ardra",
    },
    {
        "name": "David_20260616_1230_BST",
        "moment": datetime(2026, 6, 16, 12, 30, 0,
                           tzinfo=timezone(timedelta(hours=1))),  # BST
        "latitude": 51 + 30/60,         # 51°30'N (London)
        "longitude": -(0 + 7/60),       # 0°07'W
        "expected_sunrise_hms": (4, 49, 43),
        "expected_sunset_hms": (21, 12, 52),
        "expected_tithi_name": "Sukla Dwitiya",
        "expected_tithi_percent_left": 38.55,
        "expected_nakshatra_name": "Punarvasu",
        "expected_nakshatra_percent_left": 96.13,
        "expected_yoga_name": "Vriddhi",
        "expected_yoga_percent_left": 37.57,
        "expected_karana_name": "Kaulava",
        "expected_karana_percent_left": 77.09,
        "expected_vara_name": "Tuesday",
        "expected_hora_lord": "Mars",
        "expected_ayanamsa_dms": (24, 12, 38.25),
        "notes": "DST handling — London BST is GMT+1",
    },
]

=== tests/calculations/test_panchanga.py ===

import pytest
from datetime import datetime, timedelta, timezone, time
from agent.calculations.core.panchanga import (
    calculate_sunrise, calculate_sunset, calculate_panchanga,
    PanchangaElement, ChoghadiyaWindow, Panchanga,
)
from tests.calculations.fixtures.panchanga_fixtures import FIXTURES

# Tolerance: JHora rounds to whole seconds; we allow ±2 minutes for 
# refraction model differences across Swiss Ephemeris versions.
SUNRISE_SUNSET_TOLERANCE = timedelta(minutes=2)

@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["name"])
def test_sunrise_matches_jhora(fixture):
    moment = fixture["moment"]
    expected_h, expected_m, expected_s = fixture["expected_sunrise_hms"]
    expected_sunrise = moment.replace(
        hour=expected_h, minute=expected_m, second=expected_s, microsecond=0
    )
    actual = calculate_sunrise(moment, fixture["latitude"], fixture["longitude"])
    delta = abs(actual - expected_sunrise)
    assert delta <= SUNRISE_SUNSET_TOLERANCE, (
        f"{fixture['name']}: sunrise off by {delta} "
        f"(expected {expected_sunrise}, got {actual})"
    )

@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["name"])
def test_sunset_matches_jhora(fixture):
    moment = fixture["moment"]
    expected_h, expected_m, expected_s = fixture["expected_sunset_hms"]
    expected_sunset = moment.replace(
        hour=expected_h, minute=expected_m, second=expected_s, microsecond=0
    )
    actual = calculate_sunset(moment, fixture["latitude"], fixture["longitude"])
    delta = abs(actual - expected_sunset)
    assert delta <= SUNRISE_SUNSET_TOLERANCE, (
        f"{fixture['name']}: sunset off by {delta} "
        f"(expected {expected_sunset}, got {actual})"
    )

def test_naive_datetime_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        calculate_panchanga(datetime(2026, 6, 16, 12, 30), 22.5, 88.0)

def test_polar_latitude_rejected():
    moment = datetime(2026, 6, 16, 12, 30, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="outside v1 supported range"):
        calculate_panchanga(moment, 70.0, 88.0)
    with pytest.raises(ValueError, match="outside v1 supported range"):
        calculate_panchanga(moment, -70.0, 88.0)

def test_panchanga_not_implemented_yet():
    """P1.2a only ships sunrise/sunset. Full Panchanga lands in P1.2b."""
    moment = datetime(2026, 6, 16, 12, 30, 
                      tzinfo=timezone(timedelta(hours=5, minutes=30)))
    with pytest.raises(NotImplementedError):
        calculate_panchanga(moment, 22.5666, 88.3666)

CONSTRAINTS:
- DO NOT implement tithi, nakshatra, yoga, karana, vara, hora, 
  choghadiya, rahu_kalam, yamaganda, gulika, abhijit. Those are P1.2b/c.
- DO NOT modify chart_calculator.py
- DO NOT modify any existing test file
- DO NOT add pyswisseph to requirements — it must already be there
- 41 existing tests must remain passing
- New tests: 4 sunrise + 4 sunset + 1 naive-rejection + 2 polar-rejection 
  + 1 not-implemented = 12 new tests

VERIFICATION CHECKLIST (paste output back for review):
1. `head -50 agent/calculations/core/panchanga.py` showing module 
   docstring, imports, constants, dataclasses
2. `grep -n "^def \|^    def " agent/calculations/core/panchanga.py` 
   showing all 4 function definitions (helpers + 3 publics)
3. `cat tests/calculations/fixtures/panchanga_fixtures.py | head -20` 
   showing fixture module docstring and start of FIXTURES list
4. `pytest -q tests/calculations/test_panchanga.py` — should show 
   12 tests passing
5. `pytest -q` — should show 53 tests passing (41 old + 12 new)
6. `git status` showing the 5 new/modified files
7. `python -c "from agent.calculations.core.panchanga import Panchanga, PanchangaElement, ChoghadiyaWindow; print('ok')"` — should print 'ok'

STOP after verification. Do not proceed to P1.2b (core five + hora). 
Report back results.

CRITICAL EDGE CASE NOTE:
The swisseph rise_trans API has specific behavior at high latitudes 
and near the date line. For this prompt, only need to handle the 4 
fixture locations (Calcutta, Patna, Durban, London — all standard). 
If rise_trans returns no rise on the search date, raise ValueError. 
Do not silently return None or the previous day's sunrise.