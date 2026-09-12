# S127 -- calculate_chart() characterization capture: David

Captured at: 2026-09-12T09:26:14.568938+00:00

Archived here (not left in `diagnostics/latest_run.md`) because that
file is overwrite-only and this run's own STOP report needed to occupy
it per rule 26 — this is the exact raw dict the STOP report at
`diagnostics/runs/20260912T092700Z.md` refers to as "the fresh capture."

## Input (verbatim from tests/test_chart_calculator.py _MUNTHA_FIXTURES)

```json
{
  "name": "David",
  "dob": "19 Jan 1976",
  "tob": "22:00",
  "place": "London, UK"
}
```

## Shape check (informational only -- no assertions made)

- All 9 planet dicts share identical key set: True
- Per-planet keys observed: ['dignity', 'house', 'retrograde', 'sign']
- 'longitude' absent from every planet dict (public contract): True
- Number of planets returned: 9
- lagna_chart present: True

## Full calculate_chart() return value, verbatim

```python
{'birth_details': {'name': 'David', 'dob': '19 Jan 1976', 'tob': '22:00', 'place': 'London, UK', 'lat': 51.5074, 'lon': -0.1278}, 'lagna_chart': {'ascendant': 'Virgo', 'ascendant_lord': 'Mercury', 'rasi': 'Leo', 'rasi_lord': 'Sun', 'nakshatra': 'Magha', 'nakshatra_pada': 4, 'nakshatra_lord': 'Ketu'}, 'planetary_positions': {'Sun': {'house': 5, 'sign': 'Capricorn', 'dignity': 'Inimical', 'retrograde': False}, 'Moon': {'house': 12, 'sign': 'Leo', 'dignity': 'Friendly', 'retrograde': False}, 'Mars': {'house': 9, 'sign': 'Taurus', 'dignity': 'Neutral', 'retrograde': True}, 'Mercury': {'house': 5, 'sign': 'Capricorn', 'dignity': 'Neutral', 'retrograde': True}, 'Jupiter': {'house': 7, 'sign': 'Pisces', 'dignity': 'Own Sign', 'retrograde': False}, 'Venus': {'house': 3, 'sign': 'Scorpio', 'dignity': 'Neutral', 'retrograde': False}, 'Saturn': {'house': 11, 'sign': 'Cancer', 'dignity': 'Inimical', 'retrograde': True}, 'Rahu': {'house': 2, 'sign': 'Libra', 'dignity': 'Neutral', 'retrograde': True}, 'Ketu': {'house': 8, 'sign': 'Aries', 'dignity': 'Neutral', 'retrograde': True}}, 'conjunctions': ['Sun conjunct Mercury (5th house)'], 'house_lord_mapping': [{'house': 1, 'sign': 'Virgo', 'lord': 'Mercury', 'lord_in_house': 5}, {'house': 2, 'sign': 'Libra', 'lord': 'Venus', 'lord_in_house': 3}, {'house': 3, 'sign': 'Scorpio', 'lord': 'Mars', 'lord_in_house': 9}, {'house': 4, 'sign': 'Sagittarius', 'lord': 'Jupiter', 'lord_in_house': 7}, {'house': 5, 'sign': 'Capricorn', 'lord': 'Saturn', 'lord_in_house': 11}, {'house': 6, 'sign': 'Aquarius', 'lord': 'Saturn', 'lord_in_house': 11}, {'house': 7, 'sign': 'Pisces', 'lord': 'Jupiter', 'lord_in_house': 7}, {'house': 8, 'sign': 'Aries', 'lord': 'Mars', 'lord_in_house': 9}, {'house': 9, 'sign': 'Taurus', 'lord': 'Venus', 'lord_in_house': 3}, {'house': 10, 'sign': 'Gemini', 'lord': 'Mercury', 'lord_in_house': 5}, {'house': 11, 'sign': 'Cancer', 'lord': 'Moon', 'lord_in_house': 12}, {'house': 12, 'sign': 'Leo', 'lord': 'Sun', 'lord_in_house': 5}], 'yogas_doshas': {'mangal_dosha': False, 'kalsarpa_yoga': False}, 'aspects_by_planet': {'Sun': [11], 'Moon': [6], 'Mars': [12, 3, 4], 'Mercury': [11], 'Jupiter': [11, 1, 3], 'Venus': [9], 'Saturn': [1, 5, 8], 'Rahu': [6, 8, 10], 'Ketu': [12, 2, 4]}, 'aspected_by': {'Saturn': ['Sun', 'Mercury', 'Jupiter'], 'Moon': ['Mars', 'Ketu'], 'Venus': ['Mars', 'Jupiter'], 'Mars': ['Venus'], 'Sun': ['Saturn'], 'Mercury': ['Saturn'], 'Ketu': ['Saturn', 'Rahu'], 'Rahu': ['Ketu']}, 'dasha': {'current_mahadasha': {'lord': 'Rahu', 'start': '7 Dec 2019', 'end': '6 Dec 2037', 'start_jd': 2458824.720474537, 'end_jd': 2465399.335011574}, 'current_antardasha': {'lord': 'Saturn', 'start': '12 Jan 2025', 'end': '19 Nov 2027', 'start_jd': 2460687.5279282406, 'end_jd': 2461728.508564815}, 'next_5_antardashas': [{'lord': 'Mercury', 'start': '19 Nov 2027', 'end': '7 Jun 2030', 'start_jd': 2461728.508564815, 'end_jd': 2462659.9122916665}, {'lord': 'Ketu', 'start': '7 Jun 2030', 'end': '25 Jun 2031', 'start_jd': 2462659.9122916665, 'end_jd': 2463043.4314699075}, {'lord': 'Venus', 'start': '25 Jun 2031', 'end': '25 Jun 2034', 'start_jd': 2463043.4314699075, 'end_jd': 2464139.2005555555}, {'lord': 'Sun', 'start': '25 Jun 2034', 'end': '20 May 2035', 'start_jd': 2464139.2005555555, 'end_jd': 2464467.9312847224}, {'lord': 'Moon', 'start': '20 May 2035', 'end': '18 Nov 2036', 'start_jd': 2464467.9312847224, 'end_jd': 2465015.8158333334}], 'next_3_mahadashas': [{'lord': 'Jupiter', 'start': '6 Dec 2037', 'end': '6 Dec 2053', 'start_jd': 2465399.335011574, 'end_jd': 2471243.4368171296}, {'lord': 'Saturn', 'start': '6 Dec 2053', 'end': '6 Dec 2072', 'start_jd': 2471243.4368171296, 'end_jd': 2478183.3077199073}, {'lord': 'Mercury', 'start': '6 Dec 2072', 'end': '7 Dec 2089', 'start_jd': 2478183.3077199073, 'end_jd': 2484392.6658912036}], 'current_pratyantar': {'lord': 'Moon', 'start': '2 Sep 2026', 'end': '28 Nov 2026', 'start_jd': 2461286.0917939814, 'end_jd': 2461372.840185185}, 'next_5_pratyantars': [{'lord': 'Mars', 'start': '28 Nov 2026', 'end': '28 Jan 2027', 'start_jd': 2461372.840185185, 'end_jd': 2461433.564050926}, {'lord': 'Rahu', 'start': '28 Jan 2027', 'end': '3 Jul 2027', 'start_jd': 2461433.564050926, 'end_jd': 2461589.711145833}, {'lord': 'Jupiter', 'start': '3 Jul 2027', 'end': '19 Nov 2027', 'start_jd': 2461589.711145833, 'end_jd': 2461728.508564815}]}, 'meta': {'ayanamsha_lahiri': 23.5226, 'asc_lon_sidereal': 155.2812, 'jd_ut': 2442797.416667}}
```

---

AWAITING HUMAN REVIEW of golden values before locking regression test.
