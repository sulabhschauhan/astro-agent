Goal: Answer "everything like the best astrologer"
STACK & CONVENTIONS (LOCKED)
Python 3.11, pyswisseph, SIDM_LAHIRI, Whole Sign houses, Mean Node
Sign convention: 0-11 (0=Aries). Nakshatra: 0-26 (0=Ashwini)
Validation: JHora v8 = primary oracle, AstroSage = secondary parity
Source hierarchy: AstroSage parity → JHora/PVR → Classical anchor (BPHS/MC)
Read PVR book FIRST before coding any scoring table; AstroSage = validation only
Every module: frozen dataclasses, try/except with meaningful errors, no full-file rewrites
Tests: 4 reference charts (Sulabh, Surbhi, Sheridan, David), hardest-case first
Ayanamsa = 23-40-39.08 for Sulabh; 60" tolerance vs JHora
REFERENCE CHARTS
Sulabh: 6 Apr 1988, 00:30 IST, Calcutta — Moon=2Sc14'52", Lagna=22Sg42'54"
Surbhi: 11 Sep 1992, 10:30 IST, Patna
Sheridan: 15 Mar 1995, 06:00 IST, Boston
David: 12 Dec 1990, 14:30 IST, New Delhi
CURRENT STATE — WHAT EXISTS (1011 tests passing)
COMPLETE MODULES (shipped + tested)
core/panchanga.py (407 lines) — Tithi, Vara, Nakshatra, Yoga, Karana, Hora, Choghadiya, Rahu Kalam, Yamaganda, Gulika Kalam, Abhijit Muhurta
core/dignity.py (63 lines) — Exalted, Debilitated, Moolatrikona, Own sign (static dignity only)
core/friendship.py (116 lines) — Natural, Tatkalika, Pancha-dha Maitri (7 classical planets)
core/aspects.py (158 lines) — Graha Drishti: 7th all planets, Mars 4/8, Jupiter 5/9, Saturn 3/10, Rahu/Ketu 5/7/9
vargas/navamsa.py (195 lines) — D9 complete with NavamsaChart frozen dataclass
transits/gochara.py (141 lines) — Transit snapshot, house_from_lagna + house_from_moon, 9 bodies
transits/sade_sati.py (301 lines) — 3-phase detection + date-range scan
transits/chandrabala.py (236 lines) — Instant + range-scan via discrete_scan
transits/tarabala.py (319 lines) — Instant + range-scan via discrete_scan
transits/panchaka.py (234 lines) — Binary IS_PANCHAK (Moon 300-360°)
transits/muhurta_scorer.py (273 lines) — Composite 3-limb scorer (TIER_1/2/3 + Panchaka veto) + range-scan
transits/transit_aspects.py (63 lines) — Transit-to-natal aspect detection
compatibility/ (FULL subpackage, ~1500 lines) — All 8 Ashtakoot kootas, Mangal Dosha with 7 cancellation rules
helpers/discrete_scan.py (175 lines) — Shared bisection range-scan helper
helpers/house_counting.py (61 lines) — Varshaphal bhav resolution
chart_calculator.py (1262 lines) — D1 chart, Vimshottari Dasha (basic), Varshaphal Lagna, Muntha, Mudda Dasha, aspects (legacy), yogas (legacy placeholder), solar return
STUB FILES (1-line docstring only, NEED full implementation)
core/chart_d1.py — D1 extraction from chart_calculator.py
vargas/divisional.py — D2-D60 divisional chart engine
vargas/vimshopaka.py — Vimshopaka Bala (varga strength scoring)
strength/shadbala.py — 6-component planetary strength
strength/bhava_bala.py — House strength calculation
strength/ishta_kashta.py — Ishta/Kashta Phala
dashas/vimshottari.py — Full Vimshottari (extract + enhance from chart_calculator.py)
dashas/chara.py — Chara Dasha (sign-based)
dashas/yogini.py — Yogini Dasha
dashas/ashtottari.py — Ashtottari Dasha
dashas/mudda.py — Mudda Dasha (extract from chart_calculator.py)
yogas/detector.py — Yoga detection orchestrator
yogas/catalog/raja_yogas.py — Raja Yoga detection
yogas/catalog/dhana_yogas.py — Dhana (wealth) Yoga detection
yogas/catalog/pancha_mahapurusha.py — Pancha Mahapurusha Yoga
yogas/catalog/neecha_bhanga.py — Neecha Bhanga Rajayoga
yogas/catalog/special.py — Gaja Kesari, Amala, Voshi, etc.
ashtakavarga/bav.py — Bhinnashtakavarga (per-planet point table)
ashtakavarga/sav.py — Sarvashtakavarga (aggregate point table)
jaimini/karakas.py — Jaimini 7 Karakas
jaimini/arudha.py — Arudha Lagna
jaimini/padas.py — Jaimini Padas
annual/muntha.py — Muntha (extract from chart_calculator.py)
annual/varshaphal.py — Varshaphal (extract from chart_calculator.py)
annual/sahams.py — Annual Sahams (sensitive points)
helpers/ephemeris.py — Shared pyswisseph wrapper
NOT YET CREATED (missing entirely)
infra/chart_profile.py — Pre-computation orchestrator (builds chart_profile.json)
infra/calc_router.py — Hybrid rule-based + LLM fallback question → module mapper
infra/result_formatter.py — Computation results → LLM-consumable context blocks
RAG pipeline wiring (prompt_builder.py currently receives NO computed data)
Sign-convention normalization (gochara uses 1-12, others use 0-11)
QUESTION DOMAINS A TOP ASTROLOGER MUST ANSWER
#	Domain	Key Houses	Key Planets	Required Modules	Status
1	General Life Overview	All	All	D1, Panchanga, Dignity, Aspects	DONE
2	Career & Profession	10, 6, 2	Sat, Merc, Sun	D10, Shadbala, Raja Yogas, AV	MISSING
3	Marriage & Compatibility	7, 8	Ven, Jup	D9, D7, Ashtakoot, Mangal Dosha	PARTIAL (D9+Koota done, D7 missing)
4	Health & Disease	6, 8, 1	Sat, Mars	D6, Shadbala, Bhava Bala	MISSING
5	Wealth & Finance	2, 11, 9	Jup, Ven, Mer	D2, Dhana Yogas, AV, Shadbala	MISSING
6	Education	4, 5, 2	Mer, Jup	D4, Shadbala, 2nd/4th/5th lords	MISSING
7	Children	5, 9	Jup	D7, 5th house analysis	MISSING
8	Timing (When?)	All	All	Vimshottari (full), Gochara, Transits	PARTIAL (Gochara done, Dasha not extracted)
9	Travel & Foreign	9, 12, 7	Rahu, Ketu	9th/12th house, Rahu/Ketu placement	PARTIAL (placement done, no depth)
10	Mental Health & Peace	4, 5, 1	Moon, Mer	Moon dignity, Nakshatra, 4th/5th lords	PARTIAL
11	Litigation & Enemies	6, 7, 12	Sat, Mars, Rahu	6th/8th/12th, Shadbala	MISSING
12	Property & Vehicles	4, 11	Mars, Ven, Sat	D4, 4th house, Mars strength	MISSING
13	Spiritual Life	9, 12	Jup, Ketu	D20, Jaimini Karakas, 9th/12th	MISSING
14	Longevity	8, 3, 1	Sat, 8th lord	Shadbala, 8th house, Maraka lords	MISSING
15	Remedies	—	—	RAG (Lal Kitab, BPHS) + dignity for gem rec	PARTIAL (RAG done, gem logic missing)
16	Annual Predictions	All	All	Varshaphal, Muntha, Mudda, Sahams	PARTIAL (in chart_calculator, not extracted)
17	Muhurta (Auspicious Time)	—	—	Muhurta Scorer, Panchanga	DONE
18	Psychological Traits	1, 4, 5	Moon, Mer	Nakshatra, Moon sign, Mercury strength	PARTIAL
SESSION-WISE BUILD PLAN
PHASE 0 — INFRASTRUCTURE (Sessions 30-32)
Prerequisite for everything. Build the skeleton that all later sessions plug into.
Session 30: helpers/ephemeris.py — Shared Ephemeris Wrapper
Priority: CRITICAL (blocks multiple sessions)File: agent/calculations/helpers/ephemeris.pyTask: Extract duplicated swe.calc_ut calls from gochara.py, navamsa.py, chart_calculator.py into one shared wrapper.Functions:

sidereal_lon(jd_ut, planet) -> float — returns sidereal longitude 0-360
sidereal_lon_with_retro(jd_ut, planet) -> tuple[float, bool] — longitude + retrograde flag
tropical_to_sidereal(tropical_lon, jd_ut) -> float — apply Lahiri ayanamsa
moon_sign(jd_ut) -> int — Moon's rasi (0-11)
moon_nakshatra(jd_ut) -> tuple[int, int, float] — (nakshatra_index 0-26, pada 0-3, longitude_in_nakshatra)
all_planet_positions(jd_ut) -> dict[str, dict] — all 9 bodies with sign, degree, nakshatra, retrogradeTests: 20+ (4 reference charts × 5 planets minimum, boundary cases)Unlocks: Clean code for every subsequent session that needs ephemeris data
Session 31: sign_convention.py — Normalize 0-11 Everywhere
Priority: HIGHFile: agent/calculations/helpers/sign_convention.pyTask: gochara.py uses 1-12, everything else uses 0-11. Create conversion helpers and audit all modules.Functions:

to_zero_indexed(sign_1based: int) -> int
to_one_indexed(sign_0based: int) -> int
normalize_sign(value: int, convention: str) -> intAlso: Fix gochara.py to use 0-11 internally, output 0-11. This is a find-and-replace audit, not complex logic.Tests: 15+ (boundary: 0↔1, 11↔12, round-trip, all callers tested)Unlocks: Eliminates a class of cross-module bugs
Session 32: chart_profile.py — Pre-computation Schema + Orchestrator
Priority: CRITICAL (blocks answer pipeline)Files:

agent/calculations/infra/__init__.py
agent/calculations/infra/chart_profile.py
agent/calculations/infra/profile_schema.pyTask: Design the chart_profile.json schema and build the orchestrator that runs ALL natal calculations once and caches results.Schema (chart_profile.json):
@dataclass(frozen=True)class ChartProfile:    # Identity    name: str    dob: str    tob: str    place: str    ayanamsa: float    # D1 Basics    lagna: str  # sign name    lagna_longitude: float    moon_sign: int  # 0-11    moon_nakshatra: int  # 0-26    planetary_positions: dict  # {planet: {sign, degree, nakshatra, pada, retrograde, dignity, ishta_kashta}}    # Dignity    dignities: dict  # {planet: "Exalted"|"Debilitated"|"Own"|"Moolatrikona"|None}    # Friendship    pancha_dha_maitri: dict  # {(planet_a, planet_b): "Adhimitra"|...}    # Aspects    aspect_table: dict  # {planet: [list of aspected signs 0-11]}    # Navamsa    navamsa_chart: dict  # {planet: {sign, degree, pada}}    # Strength    shadbala: dict | None  # filled in Session 33    bhava_bala: dict | None  # filled in Session 34    ishta_kashta: dict | None  # filled in Session 35    # Yogas    yogas: list[dict] | None  # filled in Sessions 40-44    # Dashas    vimshottari: list[dict] | None  # filled in Session 45    # Ashtakavarga    bav: dict | None  # filled in Session 47    sav: list[int] | None  # filled in Session 48    # Jaimini    jaimini_karakas: dict | None  # filled in Session 50    arudha_lagna: int | None  # filled in Session 51    # Vargas    varga_charts: dict | None  # {D2: {...}, D7: {...}, D10: {...}, ...} filled in Sessions 36-39
Orchestrator function: build_chart_profile(chart_data: dict) -> ChartProfile

Calls calculate_chart() from chart_calculator.py (DO NOT refactor chart_calculator.py — locked decision)
Extracts D1 data, calls navamsa, dignity, friendship, aspects modules
Leaves strength/yogas/dashas/AV/Jaimini as None initially (filled as modules are built)
Saves to chart_profiles/{session_id}.json
Tests: 10+ (schema validation, 4 reference charts produce valid profiles)
Unlocks: The entire "compute once, serve many questions" architecture
PHASE 1 — PLANETARY STRENGTH (Sessions 33-35)
Why first: Strength is referenced by yoga detection, ashtakavarga, varga assessment, and remedy recommendations. Everything downstream depends on knowing how strong a planet is.
Session 33: Shadbala — Six-fold Planetary Strength
Priority: HIGHEST (most referenced classical calculation)
File: agent/calculations/strength/shadbala.py
Reference: PVR Chapter 15 (full chapter, ~40 pages), JHora v8 as numeric oracle
Components (all 6 required):

Sthana Bala (Positional Strength) — 5 sub-components:
Uccha Bala (Exaltation strength): 0-60 virupas based on degree from exaltation point
Saptavargajya Bala (7-varga strength): strength in D1,D2,D3,D4,D9,D10,D12
Ojayugma Bala (Odd/even sign strength): Masculine signs = odd = favorable
Kendradi Bala (Angular strength): Angular=full, Succedent=3/4, Cadent=1/2
Drekkana Bala (Decanate strength): Based on Drekkana position
Dig Bala (Directional Strength) — 0-60 virupas
Each planet has a direction where it's strongest (Jupiter/Mercury=East/Ascendant, etc.)
Kala Bala (Temporal Strength) — 6 sub-components:
Natonnata Bala (day/night strength)
Paksha Bala (Moon phase strength)
Tribhaga Bala (one-third of day/night)
Varsha/Masa/Dina Bala (year/month/day lord strength)
Hora Bala (hour lord)
Ayana Bala (equinox strength)
Chesta Bala (Motional Strength) — 0-60 virupas
Based on retrograde, direct, stationary states
Sun and Moon always 0 (no retrograde)
Naisargika Bala (Natural Strength) — fixed values
Sun=60, Moon=50, Mars=40, Mercury=35, Jupiter=50, Venus=45, Saturn=45
Drik Bala (Aspectual Strength) — net benefic/malefic aspects received
Output: ShadbalaResult frozen dataclass per planet:

@dataclass(frozen=True)
class ShadbalaResult:
    planet: str
    sthana_bala: float  # 0-60
    dig_bala: float  # 0-60
    kala_bala: float  # 0-60
    chesta_bala: float  # 0-60
    naisargika_bala: float  # 0-60
    drik_bala: float  # can be negative
    total: float  # sum of 6
    is_above_threshold: bool  # total > minimum required (varies by planet)


Validation: JHora v8 Shadbala export for all 4 reference charts. Tolerance: ±0.5 virupas.
Tests: 80+ (6 components × ~10 tests each + 4 fixture charts × 7 planets = 28 integration tests)
Question domains unlocked: Career strength, health vulnerability, remedy intensity, yoga potency qualification

Session 34: Bhava Bala — House Strength
Priority: HIGH
File: agent/calculations/strength/bhava_bala.py
Reference: PVR Chapter 16
Task: Calculate the strength of each of the 12 houses.
Components:

Bhava Madhya (Midpoint of each house in whole-sign system)
Bhava Shadbala: Uses dig_bala of house lord, aspects received, occupants' strength
Ishta and Kashta for each house (based on house lord's Shadbala)
Output: BhavaBalaResult frozen dataclass
Tests: 30+
Question domains unlocked: House-level analysis for any domain question
Session 35: Ishta Kashta Phala
Priority: HIGH
File: agent/calculations/strength/ishta_kashta.py
Reference: PVR Chapter 17
Task: Net benefic/malefic score per planet based on Shadbala + natural benefic/malefic classification.
Formula:

Ishta Phala = (Shadbala - minimum) / (maximum - minimum) × natural_benefic_weight
Kashta Phala = (maximum - Shadbala) / (maximum - minimum) × natural_malefic_weight
Net = Ishta - Kashta (positive = overall benefic)
Output: IshtaKashtaResult frozen dataclass per planet
Tests: 25+
Question domains unlocked: Gem recommendation, overall chart positivity, remedy prioritization
PHASE 2 — DIVISIONAL CHARTS (Sessions 36-39)
Why second: Vargas provide domain-specific depth. D10 for career, D7 for children, D9 already done.
Session 36: Varga Engine + D2, D3, D4
Priority: HIGH
File: agent/calculations/vargas/divisional.py
Reference: PVR Chapter 7, BPHS Chapter 6
Task: Generic varga computation engine that handles all 16 divisional charts.
Varga table (start-sign per odd sign, per PVR):

VARGA_TABLE = {
    "D2":  {1: 0, 4: 0, 7: 3, 10: 3},   # Hora
    "D3":  {1: 0, 4: 9, 7: 6, 10: 3},    # Drekkana
    "D4":  {1: 0, 4: 9, 7: 3, 10: 6},    # Chaturthamsa
    "D6":  {1: 0, 4: 6, 7: 9, 10: 3},    # Shashtamsa
    "D7":  {1: 0, 4: 9, 7: 3, 10: 6},    # Saptamsa
    "D8":  {1: 0, 4: 6, 7: 9, 10: 3},    # Ashtamsa
    "D9":  {1: 0, 4: 9, 7: 3, 10: 6},    # Navamsa (already exists, but include for completeness)
    "D10": {1: 0, 4: 9, 7: 3, 10: 6},    # Dasamsa
    "D11": {1: 0, 4: 9, 7: 3, 10: 6},    # Ekadashamsa
    "D12": {1: 0, 4: 9, 7: 3, 10: 6},    # Dwadashamsa
    "D16": {1: 0, 4: 9, 7: 3, 10: 6},    # Shodashamsa
    "D20": {1: 0, 4: 6, 7: 9, 10: 3},    # Vimshamsa
    "D24": {1: 0, 4: 9, 7: 3, 10: 6},    # Chaturvimshamsa
    "D30": {1: 0, 4: 3, 7: 6, 10: 9},    # Trimsamsa (DIFFERENT — 5-fold, not regular)
    "D40": {1: 0, 4: 9, 7: 3, 10: 6},    # Khavedamsa
    "D45": {1: 0, 4: 9, 7: 3, 10: 6},    # Akshavedamsa
    "D60": {1: 0, 4: 9, 7: 3, 10: 6},    # Shashtyamsa
}


Public function: compute_varga(jd_ut, asc_lon_sidereal, varga_name: str) -> VargaChart
This session: Implement engine + D2 (Hora/wealth), D3 (Drekkana/siblings), D4 (Chaturthamsa/property)
Tests: 40+ (engine: 15 structural, D2: 8, D3: 8, D4: 8, 4 fixture charts)
Question domains unlocked: Wealth analysis (D2), sibling analysis (D3), property/vehicles (D4)

Session 37: D7 Saptamsa + D10 Dasamsa
Priority: HIGHEST (most requested domains: children + career)
Files: Add to vargas/divisional.py
Task: Add D7 (children/progeny) and D10 (career/profession) to the varga engine.
D7 Saptamsa specifics: 7-fold division. Analyze 5th house, Jupiter, D7 Lagna, D7 5th house.
D10 Dasamsa specifics: 10-fold division. Analyze D10 Lagna, 10th house, Sun/Saturn/Mercury in D10.
Tests: 35+ (D7: 15, D10: 15, cross-validation: 5)
Question domains unlocked: Children prospects (D7), Career analysis (D10) — TOP 2 user questions

Session 38: D6 Shashtamsa + D12 Dwadashamsa + D16 Shodashamsa
Priority: MEDIUM
Task: Add D6 (health/disease), D12 (parents/ancestors), D16 (vehicles/pleasure).
Tests: 30+
Question domains unlocked: Health (D6), parental longevity (D12), vehicles (D16)

Session 39: D20 Vimshamsa + D24 Chaturvimshamsa + D30 Trimsamsa
Priority: MEDIUM
Task: Add D20 (spiritual), D24 (higher education), D30 (misfortune/evil).
D30 Trimsamsa is SPECIAL: Uses 5-fold division for odd signs, different rules for even signs. Requires separate code path.
Tests: 35+ (D30 needs extra tests due to asymmetric rules)
Question domains unlocked: Spiritual inclination (D20), higher education (D24), chronic issues (D30)

Session 39b: Vimshopaka Bala
Priority: MEDIUM
File: agent/calculations/vargas/vimshopaka.py
Reference: PVR Chapter 8
Task: Score each planet's strength across a group of vargas (e.g., D1+D9+D12 for one group). Weighted average.
Tests: 20+
Question domains unlocked: Cross-varga planet strength, refines yoga/dasha interpretation

PHASE 3 — YOGA DETECTION (Sessions 40-44)
Why third: Yogas combine dignity + house + varga data. Need Phases 1-2 complete.
Session 40: Pancha Mahapurusha Yogas
Priority: HIGH
File: yogas/catalog/pancha_mahapurusha.py
Task: Detect 5 great yogas based on planet in own/exalted sign in kendra.
Yogas:

Hamsa (Jupiter in kendra in own/exalted sign) — Pisces/Sagittarius/Cancer
Malavya (Venus in kendra in own/exalted sign) — Taurus/Libra/Pisces
Ruchaka (Mars in kendra in own/exalted sign) — Aries/Scorpio/Capricorn
Bhadra (Mercury in kendra in own/exalted sign) — Gemini/Virgo
Shasha (Saturn in kendra in own/exalted sign) — Aquarius/Capricorn/Libra
Output: PanchaMahapurushaResult — which yoga(s) detected, which planet, which house, strength notes
Tests: 30+ (5 yogas × structural + 4 fixtures + cancellation cases)
Unlocks: Major personality trait identification
Session 41: Raja Yogas
Priority: HIGHEST
File: yogas/catalog/raja_yogas.py
Task: Detect Raja Yoga combinations.
Classical definitions (BPHS/PVR):

Lord of kendra (1,4,7,10) + Lord of trikona (1,5,9) in mutual kendra/trikona
Lord of 9th + Lord of 10th conjunct or in mutual aspects
Exalted planet in kendra
Multiple variations — need minimum 8 patterns
Output: RajaYogaResult — list of detected yogas with involved planets/houses
Tests: 40+ (8+ patterns × structural + fixtures)
Question domains unlocked: Power, authority, political success, fame
Session 42: Dhana Yogas (Wealth)
Priority: HIGH
File: yogas/catalog/dhana_yogas.py
Task: Detect wealth-yielding combinations.
Patterns:

Lord of 2nd + Lord of 11th in kendra/trikona
Lord of 2nd + Lord of 9th conjunct
Jupiter + Venus in 2nd/11th
Mercury + Jupiter in 1st/2nd/11th
Minimum 8 patterns
Tests: 35+
Question domains unlocked: Wealth potential, financial success timing
Session 43: Neecha Bhanga Rajayoga
Priority: MEDIUM
File: yogas/catalog/neecha_bhanga.py
Task: Detect cancellation of debilitation producing Raja Yoga.
Cancellation conditions (minimum 6):

Debilitated planet in kendra from Moon or Lagna
Lord of debilitation sign aspects the debilitated planet
Debilitated planet is exalted in Navamsa
Lord of exaltation sign of the debilitated planet is in kendra
Debilitated planet exchanges signs with its debilitation lord
Debilitated planet conjunct exalted planet
Tests: 30+
Question domains unlocked: Hidden strength in debilitated planets, rise-from-ashes narratives
Session 44: Special Yogas + Yoga Detector Orchestrator
Priority: MEDIUM
Files: yogas/catalog/special.py, yogas/detector.py
Special yogas to detect:

Gaja Kesari (Jupiter-Moon in kendra from each other)
Amala Yoga (benefic in 10th from Moon/Lagna)
Voshi Yoga (benefics in 2nd from Sun)
Parijata Yoga (lord of sign occupied by Lagna lord in exaltation/kendra)
Sunapha, Anapha, Durudhura, Kemadruma (Moon-yoga series based on planets in adjacent houses to Moon)
Budha-Aditya (Sun-Mercury conjunction)
Minimum 10 special yogas
Detector orchestrator: detect_all_yogas(chart_profile: ChartProfile) -> list[YogaResult]
Calls all 5 catalog modules
Returns consolidated list with priority ranking
Tests: 50+ across all modules
Question domains unlocked: Complete yoga inventory for any chart
PHASE 4 — DASHA SYSTEMS (Sessions 45-46)
Why fourth: Timing questions require dasha periods mapped to houses/lords.
Session 45: Vimshottari Dasha (Full Extraction + Enhancement)
Priority: HIGHEST (most commonly asked timing question)
File: dashas/vimshottari.py
Task: Extract Vimshottari from chart_calculator.py and add Antardasha + Pratyantardasha.
Current state: chart_calculator.py has basic Mahadasha calculation. Needs:

Extract to dashas/vimshottari.py as pure function (chart_calculator.py must NOT be refactored — locked)
Add Antardasha (sub-periods within each Mahadasha)
Add Pratyantardarda (sub-sub-periods within each Antardasha)
Add current_dasha() function that returns the running period at any given date
Dasha lord house mapping (which house the dasha lord rules → what life area is activated)
Output:
python

@dataclass(frozen=True)
class DashaPeriod:
    planet: str
    start_date: str  # ISO format
    end_date: str
    level: str  # "maha" | "antara" | "pratyantara"
    parent_planet: str | None  # for antara/pratyantara
    ruling_houses: list[int]  # houses this planet rules
Tests: 60+ (lord sequence, date boundaries, 4 fixtures, antardara proportions)
Question domains unlocked: "When will I get married?", "When will I change job?", "When is my good time?"

Session 46: Yogini Dasha + Chara Dasha
Priority: MEDIUM
Files: dashas/yogini.py, dashas/chara.py
Yogini Dasha:

8-planet cycle (different from Vimshottari's 9)
Used in some regional traditions (Kerala, Tamil Nadu)
36-year cycle
Chara Dasha (Jaimini):
Sign-based dasha system (not planet-based)
Requires Jaimini Karakas (Session 50 dependency — can stub until then)
Counts signs from Lagna based on a specific order
Tests: 30+ per system
Question domains unlocked: Alternative timing systems, cross-validation of Vimshottari predictions
PHASE 5 — ASHTAKAVARGA (Sessions 47-48)
Why fifth: Transits use AV points to assess transit strength. Also directly answers "how strong is my wealth/health house."
Session 47: Bhinnashtakavarga (BAV)
Priority: HIGH
File: ashtakavarga/bav.py
Reference: PVR Chapter 13, BPHS Chapter 71
Task: Calculate point table for each planet's contribution to each sign.
For each of 7 planets (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn):

Create 12-sign table (0-8 points per sign per planet)
Sources: sign placement, house from itself, exaltation, own sign, aspects from other planets
Lagna point contribution (special case)
Output: BAVResult — {planet: {sign_0: points, sign_1: points, ..., sign_11: points}}
Validation: JHora BAV tables for 4 reference charts
Tests: 50+ (7 planets × 12 signs = 84 cells to validate, structural tests, fixtures)
Question domains unlocked: Per-house transit assessment, natal house strength quantification
Session 48: Sarvashtakavarga (SAV)
Priority: HIGH
File: ashtakavarga/sav.py
Task: Sum all 7 BAV tables + Lagna contribution into one 12-sign aggregate.
Output: SAVResult — list of 12 integers (total points per sign, range 0-56)
Interpretation thresholds:

< 25: Weak house
25-28: Average
28-32: Good
32+: Excellent
Also: Identify benefic vs malefic transit zones for each house
Tests: 25+ (structural + 4 fixture charts)
Question domains unlocked: "Is my career house strong?", transit prediction refinement
PHASE 6 — JAIMINI ASTROLOGY (Sessions 50-51)
Why sixth: Provides alternative perspective. Jaimini Karakas identify key life themes.
Session 50: Jaimini Karakas
Priority: MEDIUM
File: jaimini/karakas.py
Reference: PVR Chapter 32, Jaimini Sutras
Task: Calculate 7 Jaimini Karakas based on planetary degree ranking.
7 Karakas (highest degree to lowest):

Atmakaraka (AK) — Soul indicator
Amatyakaraka (AmK) — Career/minister
Bhratrikaraka (BK) — Siblings/courage
Matrikaraka (MK) — Mother/education
Putrakaraka (PK) — Children/creativity
Gnatikaraka (GK) — Enemies/obstacles
Darakaraka (DK) — Spouse/partner
Rahu exception: If Rahu is between two planets in degrees, use special interpolation rule.
Output: JaiminiKarakasResult — ordered dict of 7 karaka positions
Tests: 25+ (degree ranking, Rahu exception, 4 fixtures)
Question domains unlocked: Life purpose (AK), spouse nature (DK), career theme (AmK), children (PK)
Session 51: Arudha Lagna + Padas
Priority: MEDIUM
Files: jaimini/arudha.py, jaimini/padas.py
Arudha Lagna: How the world perceives the person. Calculated from Lagna lord's position.
Padas: Each house has a "pada" (reflection point). Key padas:

Arudha Pada of each house
Dara Pada (A7) — from 7th house pada, shows marriage/relationship manifestation
Upapada (UL) — from 12th house pada, shows actual spouse
Tests: 30+
Question domains unlocked: Public image, marriage manifestation, how life areas actually express
PHASE 7 — ANNUAL CHARTS (Sessions 52-53)
Why seventh: "What about this year?" questions.
Session 52: Varshaphal + Muntha Extraction
Priority: MEDIUM
Files: annual/varshaphal.py, annual/muntha.py
Task: Extract Varshaphal and Muntha from chart_calculator.py into proper modules.
Varshaphal (Solar Return):

compute_varshaphal(natal_data, target_year) -> VarshaphalChart
Includes: Varshaphal Lagna, planetary positions at solar return, Muntha position
Mudda Dasha (already in chart_calculator.py — extract to annual/mudda.py)
Muntha:
compute_muntha(natal_data, varshaphal_data, target_year) -> MunthaResult
Already implemented in chart_calculator.py — extract and enhance
Tests: 30+ (already partially tested via manual/ — formalize into unit tests)
Question domains unlocked: "How will this year be?", annual focus areas
Session 53: Sahams (Annual Sensitive Points)
Priority: LOW-MEDIUM
File: annual/sahams.py
Task: Calculate Sahams — sensitive points in the annual chart that get activated by transits.
Key Sahams:

Punya Saham (fortune point)
Karma Saham (career point)
Vivaha Saham (marriage point)
Ayur Saham (longevity point)
Rajya Saham (power/authority point)
Minimum 8 Sahams
Formula pattern: Saham = A's longitude + B's longitude - C's longitude (varies per Saham)
Tests: 20+
Question domains unlocked: Fine-grained annual predictions, transit trigger points
PHASE 8 — ADVANCED TRANSIT ANALYSIS (Sessions 54-55)
Session 54: Transit Dasha Overlap Analysis
Priority: HIGH
File: transits/dasha_transit_overlay.py (NEW)
Task: Compute where transit planets sit relative to natal positions AND current dasha lord's houses.
Function: analyze_transit_dasha(transit_snapshot, chart_profile, current_date) -> TransitDashaAnalysis
What it computes:

Current Vimshottari Mahadasha + Antardasha lords
Where those lords are placed natively (houses, signs, dignity)
Where Saturn/Jupiter/Rahu currently transit relative to dasha lord positions
Sade Sati phase relative to dasha (is the person in Sade Sati during this dasha?)
Jupiter transit through natal houses (especially 2nd, 5th, 7th, 9th, 11th — favorable)
Tests: 25+
Question domains unlocked: "I'm running Rahu Mahadasha and Saturn is transiting my 7th — what does this mean?"
Session 55: Ashtakavarga Transit Scoring
Priority: MEDIUM
File: transits/av_transit_scorer.py (NEW)
Task: Score transit planet's effect using Ashtakavarga points.
Logic: When Saturn transits a sign, check SAV total of that sign. Higher SAV = transit is less harmful. Lower SAV = transit is more difficult.
Also: Check transit planet's own BAV contribution to the natal sign it's transiting.
Tests: 20+
Question domains unlocked: Refined transit predictions, "how bad will my Sade Sati be?"

PHASE 9 — COMBUSTION & SPECIAL PHENOMENA (Sessions 56-57)
Session 56: Combustion, Retrograde Analysis, Planetary War
Priority: MEDIUM
File: core/special_phenomena.py (NEW)
Task: Detect special planetary states that modify interpretation.
Combustion:

Planet too close to Sun = combust (loses power)
Standard combustion degrees: Moon 12°, Mars 17°, Mercury 14°, Jupiter 11°, Venus 10°, Saturn 15°
Exact combustion (deep) vs. casual combustion (mild)
Retrograde Analysis:
Which planets are retrograde in natal chart
Retrograde planets give past-life karma results
Direct vs. retrograde station periods
Planetary War (Graha Yuddha):
When two true planets are within 1° of each other
The one with lower longitude "wins" (is stronger)
Tests: 30+
Question domains unlocked: "Is my Venus combust?", "What does retrograde Jupiter mean?", nuanced interpretation
Session 57: Maraka (Death-inflicting) Planet Analysis
Priority: MEDIUM
File: core/maraka.py (NEW)
Task: Identify Maraka planets (2nd and 7th lords, planets in 2nd/7th, associated planets).
Output: MarakaResult — list of Maraka planets ranked by potency
Uses: Longevity assessment, health vulnerability periods
Tests: 20+
Question domains unlocked: "Will I face health issues this year?", longevity context

PHASE 10 — ANSWER PIPELINE (Sessions 58-62)
THE CRITICAL WIRING. All calculations exist but are DISCONNECTED from the answer pipeline.
Session 58: Calc Router (Hybrid Rule-Based + LLM Fallback)
Priority: CRITICAL
File: agent/infra/calc_router.py (NEW)
Task: Map user question → required computation modules.
Design (AGREED):

Layer A (Rule-based, tried first): Keyword/pattern matching to select modules
"marriage" → compatibility, D9, D7, 7th house, Venus, Mangal Dosha
"career" → D10, Shadbala, Raja Yogas, 10th house, Saturn
"health" → D6, Shadbala, 6th/8th houses, Saturn, Mars
"wealth" → D2, D11, Dhana Yogas, AV, 2nd/11th houses
"when" / "timing" → Vimshottari, Gochara, Transit Dasha Overlay
"children" → D7, 5th house, Jupiter, Jaimini Putrakaraka
"travel" → 9th/12th houses, Rahu, Ketu
"remedy" → Dignity, Shadbala, Ishta/Kashta, RAG (Lal Kitab)
"spiritual" → D20, Jaimini, 9th/12th, Jupiter, Ketu
"education" → D4, Mercury, Jupiter, 4th/5th houses
"this year" → Varshaphal, Muntha, Mudda Dasha
"muhurta" → Muhurta Scorer (already wired)
Layer B (LLM fallback, when A confidence < threshold): Send question to GPT-4o-mini to classify which modules are needed
Only used when Layer A can't match or confidence is low
Returns list of module names + confidence scores
Output: CalcRouteResult — list of (module_name, relevance_score) pairs
Tests: 40+ (rule coverage for all 15+ domains, LLM fallback mock, edge cases)
Unlocks: The entire computation → answer bridge
Session 59: Result Formatter
Priority: CRITICAL
File: agent/infra/result_formatter.py (NEW)
Task: Convert raw computation results into LLM-consumable context blocks.
Design:

Each module has a formatter function that takes its result and produces plain-text context
Context blocks are designed for prompt injection (not for user display)
Example for Shadbala:
text

SHADBALA CONTEXT:
Jupiter: Total 6.2 virupas (strong). Sthana 5.1, Dig 4.8, Kala 5.5, Chesta 0 (no retrograde), Naisargika 5.0, Drik 3.8. Above threshold.
Saturn: Total 4.1 virupas (moderate). Below threshold in Kala Bala.
Venus: Total 7.8 virupas (very strong). Highest in chart.
Example for Yogas:
text

YOGA CONTEXT:
Hamsa Yoga detected: Jupiter in Pisces in 4th house (kendra). Indicates wisdom, spiritual inclination, teaching ability.
Raja Yoga #1: 4th lord Moon + 9th lord Mars conjunct in 7th house. Indicates power through partnerships.
Output: Formatted text blocks, one per relevant module, concatenated for prompt injection
Tests: 25+ (formatting for each module type, truncation for token limits, edge cases)
Unlocks: Clean data injection into GPT prompts

Session 60: Wire Calculations into prompt_builder.py
Priority: CRITICAL
Files: Modify agent/prompt_builder.py
Task: prompt_builder currently receives only RAG passages. Add computation context.
Changes:

build_prompts() now accepts computation_context: str | None parameter
If computation context exists, inject it AFTER the system prompt but BEFORE RAG passages
Add clear separator: === COMPUTED ASTROLOGICAL DATA === ... === CLASSICAL REFERENCE TEXT ===
GPT sees: system prompt + computed data + RAG passages + user question
Token budget: Computation context gets up to 2000 tokens, RAG gets remainder
Tests: 15+ (integration tests with mock computation data)
Unlocks: GPT now has BOTH computation AND classical text to synthesize answers
Session 61: Wire Calc Router into astrologer.py
Priority: CRITICAL
Files: Modify agent/astrologer.py
Task: The main ask() pipeline currently goes: classify → RAG → GPT. Add computation step.
New pipeline:

classify question (existing)
If chart exists in session → load chart_profile from cache
Calc Router: map question → required modules
Run required computations (or pull from cached chart_profile)
Format results via Result Formatter
RAG retrieval (existing)
Build prompt with computation + RAG (modified prompt_builder)
GPT synthesis (existing)
Backward compatibility: If no chart data exists (palmistry-only, general knowledge questions), skip steps 2-5 and use existing RAG-only path.
Tests: 20+ (end-to-end with mock data, backward compatibility, chart-missing fallback)
Unlocks: THE COMPLETE PIPELINE. This is the moment calculations become visible to users.
Session 62: Remove AstroSage Dependency + Move query_engine
Priority: HIGH
Task:

Remove all astrosage_parser.py imports from calculation modules
Varshaphal/Muntha no longer need AstroSage parsed data (JHora-validated computation replaces it)
Move ingestion/query_engine.py → retrieval/query_engine.py (per .cursorrules)
Update all imports
Tests: 10+ (regression, import verification)
Unlocks: Clean architecture, no external dependency on parsed PDFs
PHASE 11 — GEMSTONE & REMEDY LOGIC (Session 63)
Session 63: Gemstone Recommendation Engine
Priority: MEDIUM
File: agent/calculations/remedies/gemstone.py (NEW)
Task: Recommend gemstones based on planetary strength and life area.
Rules (classical):

Strengthen benefic planets that are well-placed but weak in Shadbala
NEVER recommend gemstone for a planet ruling 6th, 8th, or 12th house (Maraka/dusthana)
NEVER recommend gemstone for a combust or debilitated planet
Lagna lord gemstone is generally always beneficial (if not afflicted)
5th and 9th lords are always recommendable (trikona)
Gem-planet mapping:
Ruby = Sun, Pearl = Moon, Red Coral = Mars, Emerald = Mercury, Yellow Sapphire = Jupiter, Diamond = Venus, Blue Sapphire = Saturn, Hessonite = Rahu, Cat's Eye = Ketu
Output: GemRecommendation — gem name, planet, reason, weight suggestion, wearing finger, metal, mantra
Tests: 30+
Unlocks: Actionable remedy recommendations (currently RAG-only, now computation-backed)
PHASE 12 — INTEGRATION TESTING & QUALITY (Sessions 64-65)
Session 64: End-to-End Question Domain Tests
Priority: CRITICAL
File: tests/integration/test_question_domains.py (NEW)
Task: For each of the 18 question domains, write an end-to-end test that:

Creates a chart for a reference person
Asks a representative question from that domain
Verifies Calc Router selects correct modules
Verifies computation results are non-empty and reasonable
Verifies prompt_builder receives computation context
Verifies GPT response mentions relevant astrological factors
Minimum: 18 tests (one per domain)
Unlocks: Confidence that the system works end-to-end for every question type
Session 65: chart_profile.json Builder Update
Priority: HIGH
Task: Now that all modules are built, update build_chart_profile() to call ALL modules:

Shadbala, Bhava Bala, Ishta Kashta
All needed vargas (D2, D3, D4, D6, D7, D9, D10, D12, D16, D20, D24, D30)
All yogas (Pancha Mahapurusha, Raja, Dhana, Neecha Bhanga, Special)
Vimshottari Dasha
Ashtakavarga (BAV + SAV)
Jaimini Karakas + Arudha
Combustion, Maraka, Retrograde states
Estimated profile size: ~50-100KB JSON per chart
Performance target: <5 seconds to build complete profile
Tests: 10+ (4 reference charts build successfully, no None fields remain)
SUMMARY PRIORITY MATRIX
Priority
Sessions
Modules
Question Domains Unlocked
CRITICAL	30, 32, 58-61	Infrastructure + Answer Pipeline	Everything gets wired
HIGHEST	33, 36-37, 41-42, 45, 47-48	Shadbala, D7/D10, Raja/Dhana Yogas, Vimshottari, AV	Career, Children, Wealth, Timing
HIGH	34-35, 40, 54, 62-63, 64-65	Bhava Bala, Ishta/Kashta, PMP Yogas, Transit Overlay, Integration	Health, Remedies, Gemstones, E2E
MEDIUM	31, 38-39, 43-44, 46, 50-53, 55-57	Sign norms, D6/D12/D16/D20/D30, Neecha Bhanga, Jaimini, Annual, Combustion	Spiritual, Longevity, Annual, Parents
LOW	39b, 53	Vimshopaka, Sahams	Varga refinement, Annual fine-tuning

SESSION DEPENDENCY GRAPH
text

Session 30 (ephemeris) ──────────────────────────────────────────┐
Session 31 (sign convention) ────────────────────────────────────┤
                                                                   ↓
Session 32 (chart_profile schema) ──── Session 65 (full profile) ←┘
         ↓
Session 33 (Shadbala) ────→ Session 34 (Bhava Bala) ────→ Session 35 (Ishta/Kashta)
         ↓                              ↓
Session 36 (Varga Engine + D2/D3/D4) ──→ Session 37 (D7/D10)
         ↓                              ↓
Session 38 (D6/D12/D16) ────→ Session 39 (D20/D24/D30 + Vimshopaka)
         ↓
Session 40 (PMP Yogas) ────→ Session 41 (Raja Yogas) ────→ Session 42 (Dhana Yogas)
         ↓                              ↓
Session 43 (Neecha Bhanga) ──→ Session 44 (Special Yogas + Detector)
         ↓
Session 45 (Vimshottari) ───→ Session 46 (Yogini/Chara)
         ↓
Session 47 (BAV) ──────────→ Session 48 (SAV)
         ↓
Session 50 (Jaimini Karakas) → Session 51 (Arudha/Padas)
         ↓
Session 52 (Varshaphal/Muntha) → Session 53 (Sahams)
         ↓
Session 54 (Transit-Dasha Overlay) → Session 55 (AV Transit Scoring)
         ↓
Session 56 (Combustion/Retrograde) → Session 57 (Maraka)
         ↓
Session 58 (Calc Router) ──→ Session 59 (Result Formatter) ──→ Session 60 (Wire prompt_builder) ──→ Session 61 (Wire astrologer) ──→ Session 62 (Remove AstroSage)
         ↓
Session 63 (Gemstones)
         ↓
Session 64 (E2E Tests) ──→ Session 65 (Full chart_profile builder)
ESTIMATED TEST COUNT GROWTH
After Session
Cumulative Tests
Notes
Current	1011	Baseline
Phase 0 (30-32)	~1060	Infrastructure
Phase 1 (33-35)	~1200	Strength
Phase 2 (36-39)	~1340	Vargas
Phase 3 (40-44)	~1470	Yogas
Phase 4 (45-46)	~1560	Dashas
Phase 5 (47-48)	~1635	Ashtakavarga
Phase 6 (50-51)	~1690	Jaimini
Phase 7 (52-53)	~1740	Annual
Phase 8-9 (54-57)	~1840	Advanced Transit + Phenomena
Phase 10 (58-62)	~1930	Answer Pipeline
Phase 11-12 (63-65)	~2020	Remedies + Integration

WHAT EACH SESSION DELIVERS (USER-FACING IMPACT)
After Phase
New Questions the System Can Answer
NOW	General life, Muhurta, Compatibility (Ashtakoot + Mangal Dosha), basic transit positions
Phase 1	"How strong is my career planet?", "Which planet should I strengthen?", remedy intensity
Phase 2	"Will I have children?", "What career suits me?", "Should I buy property?", "Am I spiritual?"
Phase 3	"Do I have Raja Yoga?", "Am I destined for wealth?", "Will my debilitation cancel?"
Phase 4	"When will I get married?", "When is my lucky period?", "Which dasha am I in?"
Phase 5	"How strong is my 7th house?", "Will Saturn transit hurt my career house?"
Phase 6	"What is my life purpose (Atmakaraka)?", "What does my Arudha Lagna say?"
Phase 7	"How will 2027 be for me?", "What are my lucky periods this year?"
Phase 8-9	"I'm in Rahu Dasha and Saturn transit 7th — what next?", "Is my Venus combust?"
Phase 10	ALL OF THE ABOVE NOW PRODUCE REAL ANSWERS (not just RAG text)
Phase 11-12	"Which gemstone should I wear?", validated end-to-end for every question type

text


This is ~65 sessions. Each session is one focused task. Any AI (Claude, GPT, etc.) reading this + `CLAUDE.md` + `SESSION_LOG.md` will know exactly what to build, in what order, with what conventions, what tests, and what it unlocks.

Suggested next step: Start from **Session 30** (ephemeris wrapper) — it's the cleanest starting point, unblocks multiple later sessions, and follows the locked "hardest-case-first" principle.


