# Read-Only Dasha System Integration Recon Report

**Report type:** Read-only code reconnaissance (no files edited)  
**HEAD commit:** 88e526cc4376a304f1df36965dda9412db4f280d  
**Working tree status:** 3 files modified (CLAUDE.md, diagnostics/latest_run.md, frontend/app.py), 1 untracked file (scripts/probe_neutral_chunk_valence.py) — none of these affected by this recon.

---

## 1. EXISTING DASHA INFRASTRUCTURE

### Vimshottari Dasha

**File:** `agent/chart_calculator.py` (NOT in `agent/calculations/dashas/vimshottari.py`)

**Implementation details:**
- Function `_calc_dasha(moon_lon: float, birth_local: datetime) -> dict` at line 474
- Also uses constants defined in chart_calculator.py:
  - `DASHA_ORDER = ("Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury")` at line 31
  - `DASHA_YEARS` dict mapping each lord to years (9 entries, 120 years total cycle) at lines 32-34
  - `_NAK_LORDS` tuple of 27 nakshatra lords (9 lords repeated 3 times) at line 38-39
  - `NAKSHATRAS` tuple of 27 nakshatra names at lines 11-35
  - Helper `_nakshatra(lon: float) -> tuple[str, int, str]` at line 140 — returns (nakshatra_name, pada: int 1-4, lord)

**MD/AD/PD depth:**  MD, AD, and PD (all 3 levels) — Pratyantar computed but NOT surfaced to users (line 559-560 comment: "±37-day drift causes wrong lord at Pratyantar granularity")

**Input signature:** `moon_lon: float` (sidereal longitude of Moon in degrees, 0-360), `birth_local: datetime` (local timezone datetime at birth)

**Output schema (dict keys):**
```python
{
    "current_mahadasha": {
        "lord": str,           # "Ketu", "Venus", ..., "Saturn", "Mercury"
        "start": str,          # "D Mon YYYY" format, e.g., "1 Aug 2025"
        "end": str,            # "D Mon YYYY" format
        "start_jd": float,     # Julian Day (UT), added Session 55
        "end_jd": float,       # Julian Day (UT), added Session 55
    },
    "current_antardasha": {
        "lord": str,
        "start": str,
        "end": str,
        "start_jd": float,
        "end_jd": float,
    } or None if not in an antardasha,
    "next_5_antardashas": [
        {same schema as current_antardasha}, ...
    ],
    "next_3_mahadashas": [
        {same schema as current_mahadasha}, ...
    ],
    "current_pratyantar": {
        "lord": str,
        "start": str,
        "end": str,
        "start_jd": float,
        "end_jd": float,
    } or None,
    "next_5_pratyantars": [
        {same schema as current_pratyantar}, ...
    ],
}
```

**Call site:** Only called from `calculate_chart()` at line 722 in the same file.

---

### Yogini Dasha

**File:** `agent/calculations/dashas/yogini.py`

**Status:** Empty stub file with only docstring:  
```python
"""Yogini dasha system — 36-year cycle with 8 lords."""
```

**MD/AD/PD depth:** None — not implemented  
**Input signature:** Not defined  
**Output schema:** Not defined  
**Call sites:** None (module is not imported anywhere)

---

### Ashtottari Dasha

**File:** `agent/calculations/dashas/ashtottari.py`

**Status:** Empty stub file with only docstring:  
```python
"""Ashtottari dasha system — 108-year cycle."""
```

**MD/AD/PD depth:** None — not implemented  
**Input signature:** Not defined  
**Output schema:** Not defined  
**Call sites:** None (module is not imported anywhere)

---

### Chara Dasha

**File:** `agent/calculations/dashas/chara.py`

**Status:** Empty stub file with only docstring:  
```python
"""Chara (movable) dasha system — Jaimini rasi-based periods."""
```

**MD/AD/PD depth:** None — not implemented  
**Input signature:** Not defined  
**Output schema:** Not defined  
**Call sites:** None (module is not imported anywhere)

---

### Mudda Dasha

**File:** `agent/calculations/dashas/mudda.py`

**Status:** Empty stub file with only docstring

**Implementation location:** Mudda is actually implemented in `agent/chart_calculator.py` as function `calculate_mudda_dasha(natal_data: dict, varshaphal_data: dict, target_year: int, astrosage_parsed_data: dict | None = None) -> list[dict]` at line 1157.

**Signature details (line 1157-1162):**  
- Input: natal_data (from calculate_chart()), varshaphal_data (from calculate_solar_return()), target_year (int), optional astrosage_parsed_data
- Returns: list of dicts representing 9 Mudda periods for the target year
- Uses Vimshottari order but within a single year's scope (Varshaphal annual chart context)

---

## 2. VIMSHOTTARI AS REFERENCE (THE WIRING TEMPLATE)

**Exact call path from question → dasha answer:**

1. **Entry point:** `app.py` (Streamlit frontend, not shown) → calls `orchestrator.answer_question(question, chart_data, ...)`

2. **Line `agent/infra/orchestrator.py:222`** — Route the question:
   ```python
   route_result: RouteResult = route_question(
       question,
       has_partner_data=partner_chart_data is not None,
       chart_data=chart_data,
       _stage2_client=_stage2_client,
   )
   ```

3. **Inside `agent/infra/calc_router.py:947` — `route_question()` function:**
   - **Line 1018-1024:** Tokenize question and score against keyword sets
   - **Line 138:** `_DOMAIN_KEYWORDS["current_dasha"]` maps to `_DASHA_KEYWORDS` (line 68-71)
   - **Line 1037-1039:** If keywords hit floor (0.4) and margin (0.15), call:
   ```python
   return _route_to_domain(
       best_domain, best_score, has_partner_data, chart_data, route="stage1"
   )
   ```
   - **Lines 824-848 in `_route_to_domain()`:** If `domain == "current_dasha"`:
     - Returns `RouteResult(domain="current_dasha", tier=AnswerTier.TIER_2_RANGE, ...)`

4. **Back in `agent/infra/orchestrator.py:250-259` — Build domain profile:**
   ```python
   is_marriage = route_result.domain == "marriage_compatibility"
   is_av_transit = route_result.domain == "av_transit"
   profile = build_domain_profile(
       route_result.domain,  # "current_dasha"
       chart_data,
       evaluated_at_jd,
       partner_chart_data=partner_chart_data if is_marriage else None,
       primary_role=primary_role if is_marriage else None,
       transit_planet=transit_planet if is_av_transit else "Saturn",
   )
   ```

5. **Inside `agent/infra/chart_profile.py:490-939` — `build_domain_profile()` function:**
   - **Line 794-825:** If `domain == "current_dasha"`:
   ```python
   dasha = chart_data["dasha"]  # Already computed by calculate_chart()
   payload = {
       "current_mahadasha": dasha.get("current_mahadasha"),
       "current_antardasha": dasha.get("current_antardasha"),
       "next_5_antardashas": dasha.get("next_5_antardashas"),
       "next_3_mahadashas": dasha.get("next_3_mahadashas"),
   }
   uncertainty_days = 37.0  # ±37-day drift envelope
   ```
   - Returns `DomainAnswer` with payload

6. **Line 261 in orchestrator.py — Format the answer:**
   ```python
   formatted = dataclasses.replace(format_answer(profile), route=route_result.route)
   ```

7. **Inside `agent/infra/result_formatter.py` — `format_answer(profile)` dispatches:**
   - Calls `_format_dasha()` for current_dasha domain (implementation not shown but follows the same pattern)

**Key observation:** The dasha data is pre-computed in `calculate_chart()` (line 722) and stored in `chart_data["dasha"]` — orchestrator and formatter never call `_calc_dasha()` themselves; they just pass the pre-computed dict through.

---

## 3. ROUTER INTEGRATION SURFACE

### `_VALID_DOMAINS` (orchestrator.py, line 61-70):
```python
_VALID_DOMAINS = {
    "marriage_compatibility",
    "career_strength",
    "current_dasha",
    "sade_sati",
    "av_transit",
    "arudha_lagna",
    "upapada_lagna",
    "muhurta_window",
}
```

### `_DOMAIN_KEYWORDS` (calc_router.py, line 135-143):
```python
_DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "marriage_compatibility": _MARRIAGE_KEYWORDS,
    "career_strength": _CAREER_KEYWORDS,
    "current_dasha": _DASHA_KEYWORDS,
    "av_transit": _AV_TRANSIT_KEYWORDS,
    "arudha_lagna": _ARUDHA_LAGNA_KEYWORDS,
    "upapada_lagna": _UPAPADA_LAGNA_KEYWORDS,
    "muhurta_window": _MUHURTA_WINDOW_KEYWORDS,
}
```

### `_DASHA_KEYWORDS` (calc_router.py, line 68-71):
```python
_DASHA_KEYWORDS: tuple[str, ...] = (
    "dasha", "period", "mahadasha", "antardasha", "current period",
    "running period", "timing", "when", "phase",
)
```

### `_UNBUILT_MODULE_KEYWORDS` (calc_router.py, line 163-176) — where Yogini/Ashtottari are listed:
```python
_UNBUILT_MODULE_KEYWORDS: dict[str, str] = {
    "yoga": "yoga detection",
    "transit": "transit engine (gochara)",
    "gochara": "gochara transit engine",
    "navamsa": "D9 (Navamsa) divisional chart",
    "divisional": "divisional charts (vargas)",
    "d10": "D10 divisional chart",
    "d9": "D9 (Navamsa) divisional chart",
    "varga": "divisional charts (vargas)",
    "chara": "Chara dasha",
    "yogini": "Yogini dasha",              # Line 173
    "ashtottari": "Ashtottari dasha",      # Line 174
    "varshaphal": "Varshaphal annual chart",
}
```

### `_STEM_MAP` (calc_router.py, line 468-476):
```python
_STEM_MAP: dict[str, str] = {
    "married": "marriage",
    "marry": "marriage",
    "compatible": "compatibility",
    "compat": "compatibility",
    "job": "career",
    "jobs": "career",
    "working": "career",
}
```
(No dasha-adjacent entries; dasha keywords are not in this map)

### Where a `yogini_dasha` or `ashtottari_dasha` domain would need to be added (if wired):

1. **calc_router.py `_DOMAIN_KEYWORDS` dict (line 135):**  
   Add entries like:
   ```python
   "yogini_dasha": _YOGINI_KEYWORDS,
   "ashtottari_dasha": _ASHTOTTARI_KEYWORDS,
   ```

2. **calc_router.py `_UNBUILT_MODULE_KEYWORDS` dict (line 163-176):**  
   REMOVE "yogini" and "ashtottari" entries (currently at lines 173-174) — they would no longer be unbuilt

3. **calc_router.py `_route_to_domain()` function (line 653-861):**  
   Add new branches for yogini_dasha and ashtottari_dasha (similar to current_dasha branch at lines 824-848)

4. **calc_router.py `_STAGE2_VALID_DOMAINS` frozenset (line 302-314):**  
   Add "yogini_dasha" and "ashtottari_dasha" to the set

5. **orchestrator.py `_VALID_DOMAINS` set (line 61-70):**  
   Add "yogini_dasha" and "ashtottari_dasha"

6. **chart_profile.py `build_domain_profile()` function (line 490-939):**  
   Add elif branches for yogini_dasha and ashtottari_dasha, calling builder functions `build_yogini_profile()` and `build_ashtottari_profile()`

7. **result_formatter.py `format_answer()` function:**  
   Add dispatch cases for yogini_dasha and ashtottari_dasha, calling formatter functions `_format_yogini_dasha()` and `_format_ashtottari_dasha()`

---

## 4. GOLDEN HARNESS SURFACE

### Test files covering current_dasha:

1. **`tests/fixtures/golden_qa_sulabh.py`** — Golden fixture rows:
   - Line 391: `sulabh_dasha_q11` — "When does my current Vimshottari Mahadasha/Antardasha end..."
   - Line 431: `sulabh_dasha_q12` — "How does my Moon's placement affect my current dasha experience..."
   - Line 453: `sulabh_dasha_q13` — (content not shown in excerpt)
   - Line 483: `sulabh_dasha_q14` — (Sade Sati question, dasha-adjacent)
   - Line 520: `sulabh_dasha_q15` — (content not shown in excerpt)
   - Line 546: `sulabh_dasha_r4_exact_date` — Router probe for boundary-date false-positive

2. **`tests/infra/test_orchestrator_e2e.py`** — E2E orchestrator tests (references current_dasha)

3. **`tests/infra/test_chart_profile_arudha_lagna.py`** — Profile builder tests

4. **`tests/infra/test_result_formatter_av_transit.py`** — Formatter tests

### Representative dasha fixture structure (from golden_qa_sulabh.py, line 391-429):

```python
{
    "id": "sulabh_dasha_q11",
    "chart": "sulabh",
    "domain": "dasha",
    "question": "When does my current Vimshottari Mahadasha/Antardasha end, and what comes next?",
    "baseline_source": "llm_advisor_2026-07",
    "baseline_answer_summary": "Baseline times the current cycle as Ketu Mahadasha running 4 Aug 2025 to 4 Aug 2032...",
    "claims": [
        {
            "claim": "MD 4 Aug 2025 - 4 Aug 2032",
            "verdict": "MISMATCH_ENVELOPE",
            "note": "Ours 1 Aug, JHora 28 Jul -- ephemeris noise, within the documented +-37d envelope.",
        },
        ...
    ],
    "v1_answerable": True,
    "expected_tier": "TIER_2_RANGE",
    "expected_techniques": ["vimshottari"],
    "adjudication": "pending_jhora",
}
```

**Key field meanings:**
- `domain`: "dasha" (string, not "current_dasha")
- `expected_tier`: "TIER_2_RANGE" (all current_dasha rows expected at this tier due to ±37-day drift)
- `expected_techniques`: ["vimshottari"] — only Vimshottari is wired as of this report's date
- `claims`: list of assertion objects with verdict (PASS, MISMATCH, MISMATCH_ENVELOPE, etc.)

---

## 5. CLASSICAL SPEC SOURCES IN CORPUS

### Directory status:
`project_files/classical_references/` — **DOES NOT EXIST** (confirmed by CLAUDE.md Locked Decisions, Session 57)

### PDF sources in `data/pdfs/`:
The following PDFs exist and are candidates for Yogini/Ashtottari specs (no content extracted, filenames only):
- `Sarvartha-Chintamani.pdf` — classical Jyotish reference, likely contains dasha systems
- `Saravali of Kalyana Varma Santhanam R. (Astrology).pdf`
- `Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri.pdf`
- `Jataka Parijata with explanation...` — historical classical reference

### Primary reference noted in CLAUDE.md:
`data/pdfs/Vedic Astrology_ PVR Narashimha Rao.pdf` — documented in CLAUDE.md as primary reference for P1-P6 (path corrected Session 57); PVR authored both the book and JHora (book = formulas/justification, JHora = numerical ground truth). Likely contains Yogini/Ashtottari specs if any classical formula is to be implemented.

### Grep results:
No Yogini or Ashtottari mentions in any `.py` file except:
- `agent/calculations/dashas/yogini.py` — docstring only
- `agent/calculations/dashas/ashtottari.py` — docstring only
- `agent/infra/calc_router.py` — keyword registry (lines 173-174)
- `tests/infra/test_calc_router_stage2.py` — Stage 2 test for refusing Yogini

---

## 6. JHORA PARITY

### File: `tests/fixtures/jhora_sulabh.md`

**Status:** File exists and is PARKED (line 6: "PARKED. Not consumed by any test in the current codebase.")

**Yogini/Ashtottari data:** **NOT CAPTURED** — grep search returned zero results for "Yogini" or "Ashtottari" in the fixture file.

The fixture captures Vimshottari dasha in the chart_calculator.py output format (via `calculate_chart()`), but no Yogini or Ashtottari data is present.

**Implication:** External fetch needed before implementation. JHora's `Sulabh.jhd` file (noted at line 13) would need to be queried for Yogini/Ashtottari data via the JHora GUI or API if parity validation is desired.

---

## 7. NAKSHATRA DEPENDENCY

### Shared nakshatra helper (Vimshottari):

**Primary function:** `_nakshatra(lon: float) -> tuple[str, int, str]`  
**File:** `agent/chart_calculator.py`  
**Line:** 140-144

**Signature:**
```python
def _nakshatra(lon: float) -> tuple[str, int, str]:
    s = 360.0 / 27
    idx = int(lon / s) % 27
    pada = int((lon % s) / (s / 4)) + 1
    return NAKSHATRAS[idx], pada, _NAK_LORDS[idx]
```

**Returns:** (nakshatra_name: str, pada: int 1-4, lord: str)  
**Input:** Sidereal longitude in degrees (0-360)

### Call sites:

1. **`agent/chart_calculator.py:673`** — Inside `calculate_chart()`:
   ```python
   moon_nak, moon_pada, moon_nak_lord = _nakshatra(moon_lon)
   ```

2. **`tests/manual/mudda_dasha_lagna_nakshatra_check.py:65`** — Manual test:
   ```python
   nak_name, _pada, nak_lord = _nakshatra(full_lon)
   ```

3. **`tests/manual/mudda_dasha_natal_moon_nakshatra_check.py:86`** — Manual test (referenced in line 18 comment)

4. **`tests/manual/mudda_dasha_varsha_moon_nakshatra_check.py:86`** — Manual test

### Alternative nakshatra helper (transits):

**Secondary function:** `_moon_nakshatra(jd_ut: float) -> int`  
**File:** `agent/calculations/transits/tarabala.py`  
**Line:** 168-174

**Signature:**
```python
def _moon_nakshatra(jd_ut: float) -> int:
    """Moon's sidereal nakshatra (0=Ashwini..26=Revati) at jd_ut.
    
    Delegates to helpers/ephemeris.py's sidereal_longitude() (Session 52
    migration) for the underlying swe.calc_ut convention.
    """
    return int(ephemeris.sidereal_longitude(jd_ut, swe.MOON) / _NAK_SPAN) % 27
```

**Returns:** Nakshatra index (0-26)  
**Input:** Julian Day (UT)  
**Note:** Different from `_nakshatra()` — takes JD, returns index only, uses ephemeris helper

### Call sites for `_moon_nakshatra()` (tarabala.py):

1. **`agent/calculations/transits/tarabala.py:203`** — Inside `compute_tarabala()`:
   ```python
   transit_nakshatra = _moon_nakshatra(transit_jd)
   ```

2. **`tests/calculations/compatibility/test_ashtakoot.py:76`** — Test:
   ```python
   nakshatra = tarabala_module._moon_nakshatra(jd_ut)
   ```

3. **`tests/calculations/compatibility/test_matrix.py:67`** — Test

4. **`tests/calculations/compatibility/test_sign_lord.py:63`** — Test

5. **`tests/calculations/transits/test_tarabala_windows.py:90`** — Test

6. **`tests/calculations/transits/test_tarabala_windows.py:112`** — Test (2 call sites)

**Total call sites for `_moon_nakshatra()`: 7 (1 in production, 6 in tests)**

### Stability assessment:

Both functions are low-level calculations with stable signatures (no changes documented in recent sessions). Neither has been imported into dasha modules, so **both Yogini and Ashtottari would need to declare their own nakshatra dependency** — likely calling either `_nakshatra(moon_lon)` (if pre-computed at chart-build time) or `_moon_nakshatra(jd_ut)` (if computing at query time, transits-style).

---

## Summary of Findings

1. **Vimshottari is fully wired** — implemented in chart_calculator.py, routed via calc_router, formatted via result_formatter, covered by 5+ golden fixture rows.

2. **Yogini and Ashtottari are empty stubs** — files exist but contain only docstrings; not implemented, not imported anywhere, marked as UNBUILT in router keywords.

3. **Router insertion points are clear** — 7 locations documented above would need changes if these modules were implemented.

4. **No Yogini/Ashtottari JHora parity data exists** — would need external fetch from JHora GUI.

5. **Nakshatra dependency is available** — two helper functions exist; Yogini/Ashtottari would need to decide which to use based on whether they compute at chart-time or query-time.

6. **No classical-references directory** — specs would come from `data/pdfs/` (PVR Narashimha Rao book strongly indicated as primary source).
