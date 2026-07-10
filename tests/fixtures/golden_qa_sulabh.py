"""Golden Q&A ledger — Sulabh chart, career domain (Session 48).

PROVENANCE: baseline_source = "llm_advisor_2026-07" — a general-purpose LLM
astrology advisor queried July 2026, NOT an oracle (unlike AstroSage/JHora
elsewhere in this project). It is the P7 competitive floor: Astro Agent's
deterministic pipeline must beat this baseline on VERIFIED CORRECTNESS and
UNCERTAINTY DISCLOSURE, not on rhetorical polish. Each claim below was
checked against this project's own calculation modules (chart_calculator,
calculations.core.aspects/dignity, calculations.dashas) via a Session 48
read-only diagnostic script (no project files were modified to produce this
ledger).

AD-date mismatches (claims 9-11, 17) fall inside the documented ±37-day
Antardasha cross-source drift envelope — see CLAUDE.md's `_calc_dasha`
"DASHA ACCURACY NOTE" / Kala Bala Sun cross-chart envelope discussion.
They are tagged MISMATCH_ENVELOPE, not MISMATCH, because the discrepancy is
within a known and already-documented irreducible ephemeris gap, not a new
defect.

`expected_tier` records DESIGN INTENT (per CLAUDE.md's locked P2 order /
AnswerTier architecture), not current router behavior — calc_router.py's
refuse-heavy posture (CLAUDE.md "Router refuse-heavy posture" lock) actually
REFUSED Q1 during Session 45 dogfooding on keyword-count grounds. That is
scorecard evidence for future `_STEM_MAP` tuning, not a bug, and is recorded
here rather than silently reconciled.

See CLAUDE.md for the project's locked decisions, tiebreaker principle, and
Known Source Divergences this ledger cross-references.

DIFFERENTIATION THESIS (Session 48, marriage+dasha batch: rows sulabh_marriage_*
and sulabh_dasha_*, plus the bundled refusal/boundary and out-of-domain probe
rows below): baseline is strong on rhetoric and on correctly refusing genuinely
out-of-scope requests (the R1-R3/QUEST1/QUEST2 probes) -- that is PARITY, not
an edge for either side. It loses ground on four fronts: TIMING ARITHMETIC
(sulabh_dasha_q11's Venus AD start implies an internally inconsistent ~3.6-month
Ketu-Ketu antardasha against our verified deterministic 149.14 days -- baseline's
own numbers don't cohere with each other); LONG-RANGE EPHEMERIS
(sulabh_dasha_q14: baseline guesses "mid-to-late 2030s" for the next Sade Sati
cycle where a direct ephemeris scan gives an exact 27 Jan 2041); THRESHOLD
CLAIMS (sulabh_career_q1's Mercury-combustion claim, still CONTESTED pending a
PVR-first orb lock rather than resolved either way); and UNCERTAINTY DISCLOSURE
generally (the R4 boundary probe: baseline states a fabricated day-precise date
over an internally impossible dasha boundary instead of surfacing the ±37d band
V1 discloses).

This module is pure data: no logic, no test functions. It is not
pytest-collected (filename does not match `test_*`/`*_test`).
"""

GOLDEN_QA: list[dict] = [
    {
        "id": "sulabh_career_q1",
        "chart": "sulabh",
        "domain": "career",
        "question": "How strong is my career potential?",
        "baseline_source": "llm_advisor_2026-07",
        "baseline_answer_summary": (
            "Baseline calls career potential mixed: 10th/7th lord Mercury is "
            "debilitated in Pisces (house 4) and combust, which it treats as a "
            "weakening factor, while noting Saturn (house 1) aspects the 10th and "
            "Mars sits exalted in house 2. It flags the Ketu Mahadasha "
            "(2025-2032) as the key upcoming transition window, walking through "
            "the Venus/Sun/Moon/Mars/Jupiter antardasha sequence within it."
        ),
        "claims": [
            {"claim": "Mercury is 10th lord", "verdict": "MATCH", "note": ""},
            {"claim": "Mercury debilitated, Pisces, house 4", "verdict": "MATCH", "note": ""},
            {
                "claim": "Mercury combust",
                "verdict": "CONTESTED",
                "note": "Sun-Mercury separation 14.65 deg > 12deg/14deg classical "
                        "orbs; no combustion module exists in V1; orb table needs "
                        "a PVR-first lock before this can be adjudicated MATCH/MISMATCH.",
            },
            {"claim": "Mercury also rules 7th", "verdict": "MATCH", "note": ""},
            {"claim": "Saturn in 1st aspects 10th (3/7/10)", "verdict": "MATCH", "note": ""},
            {"claim": "Mars exalted in 2nd", "verdict": "MATCH", "note": ""},
            {
                "claim": "Jupiter in 5th, does NOT aspect 10th (aspects 1,9,11)",
                "verdict": "MATCH",
                "note": "",
            },
            {
                "claim": "Ketu MD 2025-2032, Ketu in 9th Leo",
                "verdict": "MATCH",
                "note": "Ours 1 Aug 2025 - 1 Aug 2032, JHora 28 Jul - ephemeris noise.",
            },
            {
                "claim": "Venus AD ends Jan 2027",
                "verdict": "MISMATCH_ENVELOPE",
                "note": "Ours 28 Feb 2027, JHora 21 Feb; ~30d shift < +-37d envelope.",
            },
            {
                "claim": "Mars AD Dec 2027-May 2028",
                "verdict": "MISMATCH_ENVELOPE",
                "note": "Ours 3 Feb - 2 Jul 2028.",
            },
            {
                "claim": "Jupiter AD Jun 2029-May 2030",
                "verdict": "MISMATCH_ENVELOPE",
                "note": "Ours 20 Jul 2029 - 26 Jun 2030.",
            },
        ],
        "v1_answerable": True,
        "expected_tier": "TIER_2_RANGE",
        "expected_techniques": [
            "shadbala", "bhava_bala", "dignity", "aspects", "vimshottari",
        ],
        "adjudication": "pending_jhora",
    },
    {
        "id": "sulabh_career_q2",
        "chart": "sulabh",
        "domain": "career",
        "question": "Which planet most supports my profession?",
        "baseline_source": "llm_advisor_2026-07",
        "baseline_answer_summary": (
            "Baseline names Saturn as the strongest support for profession, "
            "claiming it is the only planet aspecting the 10th house and citing "
            "its role as natural karaka of profession. It also notes Mars as "
            "dispositor of Jupiter (Jupiter sits in Aries, Mars-ruled)."
        ),
        "claims": [
            {
                "claim": "Saturn is the ONLY planet aspecting the 10th",
                "verdict": "MISMATCH",
                "note": "Sun also aspects the 10th from the 4th; baseline "
                        "contradicts its own Q3 answer, which relies on exactly "
                        "that Sun-aspects-10th claim.",
            },
            {
                "claim": "Saturn natural karaka of profession",
                "verdict": "MATCH",
                "note": "Classical.",
            },
            {
                "claim": "Mars is dispositor of Jupiter (Jupiter in Aries)",
                "verdict": "MATCH",
                "note": "",
            },
        ],
        "v1_answerable": True,
        "expected_tier": "TIER_2_RANGE",
        "expected_techniques": ["shadbala", "aspects", "karaka", "dignity"],
        "adjudication": "pending_jhora",
    },
    {
        "id": "sulabh_career_q3",
        "chart": "sulabh",
        "domain": "career",
        "question": "Is my 10th house strong enough for leadership roles?",
        "baseline_source": "llm_advisor_2026-07",
        "baseline_answer_summary": (
            "Baseline judges the 10th house reasonably strong for leadership, "
            "pointing to the Sun's aspect on the 10th from the 4th house and the "
            "Sun's friendly dignity in Pisces as supporting factors."
        ),
        "claims": [
            {
                "claim": "Sun aspects 10th from 4th; Sun friendly in Pisces",
                "verdict": "MATCH",
                "note": "",
            },
        ],
        "v1_answerable": True,
        "expected_tier": "TIER_2_RANGE",
        "expected_techniques": ["bhava_bala", "aspects", "dignity"],
        "adjudication": "pending_jhora",
    },
    {
        "id": "sulabh_career_q4",
        "chart": "sulabh",
        "domain": "career",
        "question": "Will a job change in the next 12 months favor me?",
        "baseline_source": "llm_advisor_2026-07",
        "baseline_answer_summary": (
            "Baseline times the 12-month window using Varshaphal: Muntha placed "
            "in the 6th house plus Tajika monthly sub-periods, layered against "
            "the Vimshottari antardasha sequence (Venus, then Sun, then Moon) "
            "running across that window."
        ),
        "claims": [
            {
                "claim": "Muntha in 6th, Varshaphal monthly sub-periods",
                "verdict": "OUT_OF_V1_SCOPE",
                "note": "Tajika = Phase 7, unbuilt; V1 answers from dasha+transit "
                        "only, so month-precision timing carries the +-37d caveat.",
            },
            {
                "claim": "AD sequence Venus->Sun->Moon across the window",
                "verdict": "MATCH",
                "note": "Sequence correct; dates envelope-shifted per claims 9-10.",
            },
        ],
        "v1_answerable": True,  # partial: dasha+transit only, Tajika layer out of scope
        "expected_tier": "TIER_2_RANGE",
        "expected_techniques": ["vimshottari", "gochara", "sade_sati"],
        "adjudication": "pending_jhora",
    },
    {
        "id": "sulabh_career_q5",
        "chart": "sulabh",
        "domain": "career",
        "question": "Is business better than a job for me?",
        "baseline_source": "llm_advisor_2026-07",
        "baseline_answer_summary": (
            "Baseline leans toward business/self-effort over salaried work, "
            "citing Saturn's rulership of both the 2nd and 3rd houses with its "
            "aspect on its own 3rd from the 1st, plus Rahu's placement in the "
            "3rd (Aquarius), an Upachaya house."
        ),
        "claims": [
            {
                "claim": "Saturn rules 2nd AND 3rd, aspects own 3rd from 1st",
                "verdict": "MATCH",
                "note": "",
            },
            {
                "claim": "Rahu in 3rd Aquarius; 3rd is Upachaya",
                "verdict": "MATCH",
                "note": "",
            },
        ],
        "v1_answerable": True,
        "expected_tier": "TIER_2_RANGE",
        "expected_techniques": ["house_lords", "dignity", "aspects", "shadbala"],
        "adjudication": "pending_jhora",
    },
    {
        "id": "sulabh_marriage_q6",
        "chart": "sulabh",
        "domain": "marriage",
        "question": "Are Sulabh and Surbhi astrologically compatible for marriage (Ashtakoot Guna Milan)?",
        "baseline_source": "llm_advisor_2026-07",
        "baseline_answer_summary": (
            "Baseline reports a total Guna Milan score of 27.5/36 and breaks out "
            "all eight individual koota scores (Varna, Vashya, Tara, Yoni, Graha "
            "Maitri, Gana, Bhakoot, Nadi), also citing the underlying koota "
            "attributes -- Vyaghra/Ashwa yoni, both natives Rakshasa gana, "
            "Antya/Adi nadi, and Mars/Saturn as the two rasi lords."
        ),
        "claims": [
            {"claim": "Total score 27.5/36", "verdict": "MATCH", "note": ""},
            {
                "claim": "All 8 koota scores (1, 1, 3, 1, 0.5, 6, 7, 8)",
                "verdict": "MATCH",
                "note": "Varna/Vashya/Tara/Yoni/GrahaMaitri/Gana/Bhakoot/Nadi in that order.",
            },
            {
                "claim": "Attributes: Vyaghra/Ashwa yoni, both Rakshasa gana, "
                          "Antya/Adi nadi, Mars/Saturn rasi lords",
                "verdict": "MATCH",
                "note": "",
            },
        ],
        "v1_answerable": True,
        "expected_tier": "TIER_1_EXACT",
        "expected_techniques": ["ashtakoot"],
        "adjudication": "pending_jhora",
    },
    {
        "id": "sulabh_marriage_q7",
        "chart": "sulabh",
        "domain": "marriage",
        "question": "Does either of us have Mangal Dosha (Kuja Dosha)?",
        "baseline_source": "llm_advisor_2026-07",
        "baseline_answer_summary": (
            "Baseline concludes neither native carries Mangal Dosha. For Sulabh "
            "it argues Mars's placement doesn't count under a school convention "
            "that excludes the 2nd house from the dosha-house list entirely. For "
            "Surbhi it points to Mars sitting in houses 9 (from Lagna) and 5 "
            "(from Moon), neither a recognised dosha house."
        ),
        "claims": [
            {
                "claim": "Sulabh not Manglik",
                "verdict": "MATCH_WITH_NOTE",
                "note": "Our module: Lagna 2nd-house trigger fires, but C2 "
                        "(Mars exalted) cancellation clears it -> net has_dosha "
                        "reads as no active dosha. AstroSage-school baseline "
                        "excludes the 2nd house from the trigger set entirely. "
                        "Same final verdict, different path -- not a coincidence "
                        "to paper over, a genuine methodological fork worth "
                        "tracking if a 5th chart ever diverges on it.",
            },
            {
                "claim": "Surbhi not Manglik (Mars 9th from Lagna, 5th from Moon)",
                "verdict": "MATCH",
                "note": "",
            },
        ],
        "v1_answerable": True,
        "expected_tier": "TIER_1_EXACT",
        "expected_techniques": ["mangal_dosha"],
        "adjudication": "pending_jhora",
    },
    {
        "id": "sulabh_marriage_q8",
        "chart": "sulabh",
        "domain": "marriage",
        "question": "Is there a Nadi dosha between us?",
        "baseline_source": "llm_advisor_2026-07",
        "baseline_answer_summary": (
            "Baseline isolates the Nadi koota specifically: Sulabh's Nadi is "
            "Antya, Surbhi's is Adi -- different nadis, so no Nadi dosha "
            "applies and the pair scores the full 8/8 on this koota."
        ),
        "claims": [
            {
                "claim": "Nadi Antya/Adi differ, no dosha, 8/8",
                "verdict": "MATCH",
                "note": "",
            },
        ],
        "v1_answerable": True,
        "expected_tier": "TIER_1_EXACT",
        "expected_techniques": ["ashtakoot"],
        "adjudication": "pending_jhora",
    },
    {
        "id": "sulabh_marriage_q9",
        "chart": "sulabh",
        "domain": "marriage",
        "question": "Where is the weakest link in our compatibility?",
        "baseline_source": "llm_advisor_2026-07",
        "baseline_answer_summary": (
            "Baseline identifies Graha Maitri as the single weakest koota in the "
            "pair's profile, scoring only 0.5/5, tracing this to the planetary-"
            "friendship relationship between the two natives' Moon-sign lords: "
            "Mars for Sulabh, Saturn for Surbhi."
        ),
        "claims": [
            {
                "claim": "Maitri weakest at 0.5/5, Mars-vs-Saturn rasi lords",
                "verdict": "MATCH",
                "note": "",
            },
        ],
        "v1_answerable": True,
        "expected_tier": "TIER_1_EXACT",
        "expected_techniques": ["ashtakoot"],
        "adjudication": "pending_jhora",
    },
    {
        "id": "sulabh_marriage_q10",
        "chart": "sulabh",
        "domain": "marriage",
        "question": "What does our overall compatibility mean for us as a couple?",
        "baseline_source": "llm_advisor_2026-07",
        "baseline_answer_summary": (
            "Baseline synthesizes the individual koota results into a holistic "
            "relationship narrative -- strengths in Nadi/Gana/Bhakoot, the Graha "
            "Maitri weak point, overall 'Preferable' banding -- and frames what "
            "that combination means day-to-day for the couple."
        ),
        "claims": [
            {
                "claim": "Synthesis over verified kootas (data layer)",
                "verdict": "MATCH",
                "note": "Only the underlying koota data layer is being verified "
                        "here. The interpretive synthesis itself is V1-scope-OUT: "
                        "TIER_4_INTERPRETIVE is locked OUT for V1 (CLAUDE.md V1 "
                        "scope) -- AstroSage paragraph + palm are the interpretive "
                        "surface, not LLM-generated Q&A.",
            },
        ],
        "v1_answerable": False,
        "expected_tier": "TIER_4_INTERPRETIVE",
        "expected_techniques": ["ashtakoot"],
        "adjudication": "pending_jhora",
    },
    {
        "id": "sulabh_dasha_q11",
        "chart": "sulabh",
        "domain": "dasha",
        "question": "When does my current Vimshottari Mahadasha/Antardasha end, and what comes next?",
        "baseline_source": "llm_advisor_2026-07",
        "baseline_answer_summary": (
            "Baseline times the current cycle as Ketu Mahadasha running 4 Aug "
            "2025 to 4 Aug 2032, with the first antardasha (Venus) starting "
            "22 Nov 2025, and separately gives dates for a later Sun antardasha "
            "within the same Mahadasha."
        ),
        "claims": [
            {
                "claim": "MD 4 Aug 2025 - 4 Aug 2032",
                "verdict": "MISMATCH_ENVELOPE",
                "note": "Ours 1 Aug, JHora 28 Jul -- ephemeris noise, within the "
                        "documented +-37d envelope.",
            },
            {
                "claim": "Venus AD start 22 Nov 2025",
                "verdict": "MISMATCH",
                "note": "INTERNAL_INCONSISTENCY: a Venus AD starting 22 Nov 2025 "
                        "implies a Ketu-Ketu antardasha of only ~3.6 months, "
                        "against our verified deterministic duration of 149.14 "
                        "days (~4.9 months) -- see Session 48 dasha diagnostics. "
                        "Baseline's own numbers don't cohere with each other; "
                        "this is not an ephemeris-envelope case.",
            },
            {
                "claim": "Sun AD dates",
                "verdict": "MISMATCH_ENVELOPE",
                "note": "Ours 28 Feb 2027 - 5 Jul 2027.",
            },
        ],
        "v1_answerable": True,
        "expected_tier": "TIER_2_RANGE",
        "expected_techniques": ["vimshottari"],
        "adjudication": "pending_jhora",
    },
    {
        "id": "sulabh_dasha_q12",
        "chart": "sulabh",
        "domain": "dasha",
        "question": "How does my Moon's placement affect my current dasha experience, and what follows it?",
        "baseline_source": "llm_advisor_2026-07",
        "baseline_answer_summary": (
            "Baseline connects Sulabh's debilitated 12th-house Moon to a loss/"
            "introspection theme running through the current dasha, lays out "
            "the internal antardasha structure, and notes the Vimshottari "
            "sequence moves into a Venus Mahadasha starting in 2032."
        ),
        "claims": [
            {"claim": "Moon debilitated, 12th house", "verdict": "MATCH", "note": ""},
            {"claim": "AD structural placements", "verdict": "MATCH", "note": ""},
            {"claim": "Venus MD from 2032", "verdict": "MATCH", "note": ""},
        ],
        "v1_answerable": True,
        "expected_tier": "TIER_2_RANGE",
        "expected_techniques": ["vimshottari", "dignity"],
        "adjudication": "pending_jhora",
    },
    {
        "id": "sulabh_dasha_q13",
        "chart": "sulabh",
        "domain": "dasha",
        "question": "Is Venus a good or bad dasha lord for my chart this year?",
        "baseline_source": "llm_advisor_2026-07",
        "baseline_answer_summary": (
            "Baseline flags Venus as a functional malefic for this chart since "
            "it rules the 6th and 11th houses, then layers a Varshaphal (annual "
            "chart) monthly overlay on top of the dasha picture to refine the "
            "assessment for the current year."
        ),
        "claims": [
            {
                "claim": "Venus rules 6th and 11th, functional malefic",
                "verdict": "MATCH",
                "note": "",
            },
            {
                "claim": "Varshaphal overlay",
                "verdict": "OUT_OF_V1_SCOPE",
                "note": "Tajika/Varshaphal month-level overlay is Phase 7, "
                        "unbuilt; V1 answers from house-lord + dasha level only.",
            },
        ],
        "v1_answerable": True,
        "expected_tier": "TIER_2_RANGE",
        "expected_techniques": ["house_lords", "vimshottari"],
        "adjudication": "pending_jhora",
    },
    {
        "id": "sulabh_dasha_q14",
        "chart": "sulabh",
        "domain": "dasha",
        "question": "Am I currently in Sade Sati, and when does the next cycle begin?",
        "baseline_source": "llm_advisor_2026-07",
        "baseline_answer_summary": (
            "Baseline states Sulabh is not currently in Sade Sati, correctly "
            "placing Saturn in Pisces (5th from natal Moon) and giving the "
            "previous cycle's end as January 2020, but for the next cycle's "
            "start it only offers a vague 'mid-to-late 2030s' estimate rather "
            "than a precise date."
        ),
        "claims": [
            {
                "claim": "Not active, Saturn in Pisces, 5th from Moon",
                "verdict": "MATCH",
                "note": "",
            },
            {
                "claim": "Previous cycle end January 2020",
                "verdict": "MATCH",
                "note": "24 Jan 2020 (verified: last Sagittarius/setting exit).",
            },
            {
                "claim": "Next cycle 'mid-to-late 2030s'",
                "verdict": "MISMATCH",
                "note": "Direct ephemeris scan gives an exact 27 Jan 2041 (next "
                        "Libra/rising ingress) -- V1 beats baseline here with a "
                        "precise, sourced date instead of a vague decade guess.",
            },
        ],
        "v1_answerable": True,
        "expected_tier": "TIER_1_EXACT",
        "expected_techniques": ["sade_sati"],
        "adjudication": "pending_jhora",
    },
    {
        "id": "sulabh_dasha_q15",
        "chart": "sulabh",
        "domain": "dasha",
        "question": "Which month this year is astrologically best for me to make a major move?",
        "baseline_source": "llm_advisor_2026-07",
        "baseline_answer_summary": (
            "Baseline proposes to find the single best month this year for a "
            "major life move by overlaying Varshaphal (annual chart) monthly "
            "Tajika sub-period mapping on top of the dasha picture."
        ),
        "claims": [
            {
                "claim": "Varshaphal month-map",
                "verdict": "OUT_OF_V1_SCOPE",
                "note": "Tajika month-mapping is Phase 7, unbuilt. V1's actual "
                        "slice of this question is personalized Muhurta scoring "
                        "plus dasha/transit climate -- not month-precise "
                        "Varshaphal timing.",
            },
        ],
        "v1_answerable": True,  # partial: personalized Muhurta + dasha climate only
        "expected_tier": "TIER_3_MUHURTA",
        "expected_techniques": ["muhurta_scorer", "vimshottari"],
        "adjudication": "pending_jhora",
    },
    {
        "id": "sulabh_dasha_r4_exact_date",
        "chart": "sulabh",
        "domain": "dasha",
        "question": (
            "Can you name the precise, same-day date of an event tied to my "
            "dasha boundary transition?"
        ),
        "baseline_source": "llm_advisor_2026-07",
        "baseline_answer_summary": (
            "Split out of the R1-R5 boundary-probe batch: on this prompt "
            "baseline gave a day-precise date (22 Jan 2027) inheriting an "
            "impossible dasha boundary."
        ),
        "claims": [
            {
                "claim": "R4: baseline gave a day-precise date (22 Jan 2027) "
                         "inheriting an impossible dasha boundary",
                "verdict": "MISMATCH",
                "note": "This sub-probe's design intent is TIER_2_RANGE, not "
                        "REFUSAL like its siblings here -- V1 answers with a "
                        "+-37d uncertainty band instead of a single fabricated "
                        "date. This is the differentiator in this batch.",
            },
        ],
        "v1_answerable": True,
        "expected_tier": "TIER_2_RANGE",
        "expected_techniques": ["vimshottari"],
        "adjudication": "pending_jhora",
    },
    {
        "id": "sulabh_refusal_boundary_probes_r1_r5",
        "chart": "sulabh",
        "domain": "refusal_probe",
        "question": (
            "Batch of 4 boundary/refusal probes: (R1) pick an exact date for a "
            "muhurta; (R2) predict lottery numbers; (R3) time a career change "
            "via the D10 (Dashamsha) chart; (R5) prescribe a remedy (gemstone) "
            "for a weak planet."
        ),
        "baseline_source": "llm_advisor_2026-07",
        "baseline_answer_summary": (
            "Across four boundary-testing prompts, baseline correctly refuses "
            "three out-of-domain requests (an exact-date muhurta pick, a "
            "lottery-number prediction, and a Dashamsha/D10 career-timing "
            "question) -- matching V1's own refusal posture. On the fourth it "
            "volunteers a gemstone remedy despite no deterministic basis for one."
        ),
        "claims": [
            {
                "claim": "R1-R3 (exact-date muhurta / lottery numbers / D10 gap): "
                         "baseline refused correctly on all three",
                "verdict": "MATCH",
                "note": "Parity, not a differentiator -- V1 refuses these too "
                        "(no deterministic basis / out of domain for each).",
            },
            {
                "claim": "R5: baseline prescribed a gemstone remedy",
                "verdict": "MISMATCH",
                "note": "V1 refuses -- remedies (gemstones, mantras, rituals) "
                        "are out of V1 scope entirely. Differentiator: baseline "
                        "overstepped a boundary V1 correctly declines.",
            },
        ],
        "v1_answerable": False,
        "expected_tier": "REFUSAL",
        "expected_techniques": [],
        "adjudication": "pending_jhora",
    },
    {
        "id": "sulabh_out_of_domain_probes_quest1_quest2",
        "chart": "sulabh",
        "domain": "refusal_probe",
        "question": (
            "Batch of 2 out-of-V1-domain probes: (QUEST1) when will we have "
            "children (progeny timing, Surbhi chart); (QUEST2) what is my "
            "expected age or year of death."
        ),
        "baseline_source": "llm_advisor_2026-07",
        "baseline_answer_summary": (
            "On the progeny-timing question, baseline visibly miscounts a "
            "house mid-answer, catches its own error, and continues -- but it "
            "does cite the correct Surbhi Saturn-Moon antardasha end date along "
            "the way. On the death-age question it volunteers a specific "
            "82-88 age-range prediction rather than declining."
        ),
        "claims": [
            {
                "claim": "QUEST1: progeny/children timing prediction",
                "verdict": "OUT_OF_V1_SCOPE",
                "note": "Progeny/children timing is not among the P2-locked V1 "
                        "domains (career/marriage/dasha/muhurta only); V1 "
                        "refuses. Baseline's self-caught house miscount is a "
                        "rhetorical recovery, not a verified correctness point.",
            },
            {
                "claim": "QUEST1: Surbhi Saturn-Moon AD end cited as supporting evidence",
                "verdict": "MATCH",
                "note": "Verified 7 Sep 2027 in Session 48 dasha diagnostics -- "
                        "an incidental factual claim inside an otherwise "
                        "out-of-scope answer.",
            },
            {
                "claim": "QUEST2: death-age prediction (baseline gave 82-88)",
                "verdict": "MISMATCH",
                "note": "V1 refuses on safety posture -- longevity/death-timing "
                        "predictions are excluded from V1 scope entirely, unlike "
                        "baseline which volunteered a specific age range. "
                        "Differentiator: V1's refusal is the correct behavior "
                        "here, not a gap.",
            },
        ],
        "v1_answerable": False,
        "expected_tier": "REFUSAL",
        "expected_techniques": ["vimshottari"],
        "adjudication": "pending_jhora",
    },
    {
        "id": "sulabh_arudha_q1_stage1",
        "chart": "sulabh",
        "domain": "arudha_lagna",
        "question": "what is my arudha lagna and public image",
        "baseline_source": "s59_ratified_oracle",
        "baseline_answer_summary": (
            "S59-ratified Stage-1 phrasing (>=2 _ARUDHA_LAGNA_KEYWORDS hits, "
            "clears the 0.4 floor/0.15 margin): resolves via Stage 1 keyword "
            "routing, not a live Stage 2 LLM call."
        ),
        "claims": [
            {
                "claim": "Arudha Lagna = Leo",
                "verdict": "MATCH",
                "note": "S59 PVR-counting ratification (Ch.15 arudha padas, "
                        "same-house/9th-from-lord counting rule); oracle-locked "
                        "for Sulabh in the S59 orchestrator e2e suite.",
            },
        ],
        "v1_answerable": True,
        "expected_tier": "TIER_1_EXACT",
        "expected_techniques": ["arudha_lagna"],
        "adjudication": "ratified_s59",
    },
    {
        "id": "sulabh_arudha_q2_stage2",
        "chart": "sulabh",
        "domain": "arudha_lagna",
        "question": "what is my arudha lagna",
        "baseline_source": "s59_ratified_oracle",
        "baseline_answer_summary": (
            "This phrasing is expected to fall below the Stage 1 keyword floor "
            "(single-mention, score 0.333 < 0.4 floor per CLAUDE.md's "
            "'arudha_lagna Stage 1 unreachable for single-mention questions' "
            "carry-forward item) and resolve via a live GPT-4o-mini Stage 2 "
            "call on every run -- MATCH_STAGE2 posture: monitored via "
            "calc_router_stage2.log, not asserted as a stable MATCH. Raises "
            "per-run live Stage 2 calls from 9 to 10."
        ),
        "claims": [
            {
                "claim": "Arudha Lagna = Leo",
                "verdict": "MATCH",
                "note": "S59 PVR-counting ratification, same oracle value as "
                        "sulabh_arudha_q1_stage1; routing path differs "
                        "(Stage 2), calculation result does not.",
            },
        ],
        "v1_answerable": True,
        "expected_tier": "TIER_1_EXACT",
        "expected_techniques": ["arudha_lagna"],
        "adjudication": "ratified_s59",
    },
    {
        "id": "sulabh_arudha_q3_refusal_probe",
        "chart": "sulabh",
        "domain": "arudha_lagna",
        "question": "what does my upapada lagna say about my marriage",
        "baseline_source": "s59_ratified_oracle",
        "baseline_answer_summary": (
            "Upapada Lagna is built at calc level (annual/jaimini karakas "
            "pipeline) but is NOT a wired Q&A domain -- no _STEM_MAP entry, no "
            "built-module fastpath. Router behavior on this probe is "
            "unmeasured; do not guess REFUSAL vs any other tier ahead of the "
            "follow-up harness run."
        ),
        "claims": [
            {
                "claim": "MEASURE-FIRST: router disposition for an unwired "
                         "calc-level-only construct is not yet observed",
                "verdict": "PENDING",
                "note": "Design intent is deliberately withheld pending a real "
                        "harness run; the observed tier gets recorded here, "
                        "design chat ratifies it, then this row's "
                        "expected_tier placeholder is replaced with the "
                        "ratified value.",
            },
        ],
        "v1_answerable": False,
        "expected_tier": "MEASURE_FIRST_PENDING_RATIFICATION",
        "expected_techniques": ["arudha_lagna"],
        "adjudication": "pending_jhora",
    },
]
