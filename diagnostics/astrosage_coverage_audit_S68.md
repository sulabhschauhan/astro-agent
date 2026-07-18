# AstroSage-PDF dependency coverage audit (S68)

Diagnostics-only, read-only. No product code changed. Classification only
— the keep/replace decision on any section below is a design-chat ruling,
not this audit's call.

**Source PDF**: `data/pdfs/VedicReport5-24-202610-01-26PM.pdf` (56 pages,
842454 bytes). Generated via `scripts/probe_astrosage_coverage.py`
(throwaway, read-only): Pass 1 runs the existing
`agent.astrosage_parser.parse_astrosage_pdf()` / `_extract_sections()`
unmodified against this PDF; Pass 2 independently walks the full raw
text via `pdfplumber` directly (same library the parser uses) to detect
heading-like lines page by page, since the current parser only ever
targets 7 fixed keywords and silently drops everything else — a genuine
full-taxonomy audit has to look past that narrow window. Full probe
output archived in this session's `diagnostics/latest_run.md` delta.

**Quoting discipline**: no AstroSage paragraph text is reproduced beyond
section titles and, where useful, the first ~5 words of a section's
opening line (copyrighted content) — this is a classification audit, not
a content transcription.

## Pass 1 — existing 7-keyword splitter, ground truth on this PDF

`parse_astrosage_pdf()` returned 40,929 chars. 6 of 7 target keywords
matched:

| Parser section name | Chars captured | Opening words |
|---|---|---|
| Varshaphal | 5,934 | "\|\| Varshaphal (Annual Predictions) Details" |
| Pratyantar | 7,238 | "\|\| Vimshottari Dasha - Pratyantar" |
| Muntha | 2,876 | "Muntha:6 Bhav It would be" |
| Sade Sati | 7,484 | "\|\| Sadesati Report \|\| Name" |
| Favourable Points | 6,701 | "Favourable Points Ghatak (Malefics) Lucky" |
| Lal Kitab | 10,587 | "Remedies (based on Lal Kitab," |

**Not matched**: `Transit Today` — the keyword is defined in the
parser's target list but this specific PDF has no page containing
"transit today"; not classifiable against this document. If present in
a different AstroSage export, its content would most likely map to the
`av_transit` routed domain (COVERED-CALC).

Note: the parser's "Lal Kitab" keyword match starts at a "Remedies
(based on Lal Kitab...)" line — meaning its captured block bundles the
PDF's general Remedial-Measures/Remedies content together with the
later Lal-Kitab-specific planet-by-planet material, because the keyword
"lal kitab" first appears inside that general remedies text. The full
raw-taxonomy pass below (Pass 2) reports these as separate logical
sections since they have different content types, even though the
current code captures them as one blob.

## Pass 2 — full raw-text section taxonomy (all 56 pages)

31 logical sections identified from page-by-page heading detection,
consolidating the page-level scan into content-coherent groups (a
"section" here is a page range sharing one topic/heading, not
necessarily a single physical page).

### Classification key
- **COVERED-CALC** — a live routed domain (`marriage_compatibility` /
  `career_strength` / `current_dasha` / `sade_sati` / `av_transit` /
  `arudha_lagna` / `upapada_lagna` / `muhurta_window`) computes
  equivalent content.
- **COVERED-PARTIAL** — calculable (a calculation module exists) but not
  exposed as a direct Q&A answer by any routed domain, and/or the
  underlying numbers exist but the layman interpretive text does not.
- **NOT-COVERED** — interpretive/remedy content with no V1 equivalent at
  all (per CLAUDE.md's V1 scope lock: "LLM-generated interpretive Q&A is
  OUT; AstroSage paragraph + palm are the interpretive surface;
  deterministic calculation-engine output is V1's only structured Q&A
  surface").
- **OUT-OF-SCOPE-LOCKED** — content V1 deliberately suppresses.
- **N/A** — cover/promo boilerplate, no calculation or interpretive
  content to classify.

### Matrix

| # | Section | Pages | Content type | Classification | Owning domain / lock |
|---|---|---|---|---|---|
| 1 | Cover page | p.1 | promo-noise | N/A | — |
| 2 | Avkahada Chakra / basic birth details (Paya, Gana, Vasya, Nadi, Rasi, Nakshatra, Ayanamsa, Tithi, Yoga, Karan) | p.2 | calculation table | COVERED-PARTIAL | Underlying panchanga values are computed (`core/panchanga.py`) and consumed internally by several domains, but no routed domain answers "what is my Gana/Nadi/Ayanamsa" directly. |
| 3 | Favourable Points (Lucky Numbers, Ghatak, lucky metal/stone/day/years) | p.2 | calculation table | NOT-COVERED | No V1 module computes lucky numbers/colors/stones/ghatak; numerology-adjacent, no scope equivalent. |
| 4 | Lagna Chart / Navamsa Chart + planet sign/latitude/Nakshatra/Pada table | p.3 | calculation table | COVERED-PARTIAL | D1/D9 positions computed by `chart_calculator`/`vargas/`; not exposed as a standalone chart-dump Q&A answer. |
| 5 | Vimshottari Dasha table (Mahadasha/Antardasha years) | p.3 | calculation table | COVERED-CALC | `current_dasha` domain (Vimshottari; Pratyantar granularity deliberately excluded, see #6 below). |
| 6 | Chalit Table / Bhav Sign table (house cusps) | p.3 | calculation table | COVERED-PARTIAL | House cusps computed internally (e.g. `compute_porphyry_house_cusps`, used by `career_strength`); no standalone Q&A surface for a raw cusp table. |
| 7 | "What is Ascendent?" + Ascendant-sign Health/Temperament/Physical-Appearance | p.4 | interpretive paragraph | NOT-COVERED | Generic sign-based personality prose; V1 scope excludes LLM-generated interpretive Q&A entirely. |
| 8 | "Your Nakshatra: VISHAKHA" trait paragraph | p.5 | interpretive paragraph | COVERED-PARTIAL | Nakshatra position itself is computed (`core/panchanga.py`, consumed by e.g. `upapada_lagna`); the trait-narrative text has no V1 equivalent. |
| 9 | Character / Happiness And Fulfillment / Life Style | p.6 | interpretive paragraph | NOT-COVERED | No V1 equivalent; V1 scope lock. |
| 10 | Career / Occupation / Health (Nakshatra/Ascendant-based prose) | p.7 | interpretive paragraph | NOT-COVERED | `career_strength` exists but computes a methodologically different structured Shadbala/Bhava-Bala/10th-lord strength score, not this narrative — noted as a near-miss by name only, not a content match. |
| 11 | Hobbies / Love Matters / Finance | p.8 | interpretive paragraph | NOT-COVERED | `marriage_compatibility` requires a partner chart and produces Ashtakoot/Mangal-Dosha scoring, not this natal-only "Love Matters" prose — not a content match. |
| 12 | Education | p.9 | interpretive paragraph | NOT-COVERED | No V1 equivalent. |
| 13 | Panoti / Sade Sati windows table (lifetime dates, Rising/Peak/Setting phases) | p.11-13 | calculation table | COVERED-CALC | `sade_sati` domain. |
| 14 | Shani Sade Sati: Rising/Peak/Setting Phase narrative | p.14 | interpretive paragraph | COVERED-PARTIAL | Phase timing/tier is calculable via `sade_sati`; the "what this phase means" narrative text is not reproduced by the deterministic domain output. |
| 15 | Kalsarpa Dosh/Yog check | p.15 | calculation / dosha-check | NOT-COVERED | No Kalsarpa detector exists in `yogas/catalog/` (dhana_yogas, neecha_bhanga, pancha_mahapurusha, raja_yogas, special — no Kalsarpa module). |
| 16 | Varshaphal Chart (Solar Return) header + natal-vs-Varsha comparison table | p.16 | calculation table | NOT-COVERED | A calculation module exists (`calculations/annual/varshaphal.py`) but is not exposed via any routed domain — no Varshaphal Q&A surface in V1. |
| 17 | Muntha | p.17 | calculation content | NOT-COVERED | Calculation module exists (`calculations/annual/muntha.py`), unrouted. |
| 18 | Varshaphal annual-predictions narrative | p.16-22 (approx., matches the keyword-captured 5,934-char block) | interpretive paragraph | NOT-COVERED | V1 scope lock (interpretive Q&A out) + Varshaphal itself unrouted. |
| 19 | Karakamsa Chart / Swamsa Chart / Karak Avastha table (Jaimini karakas + Jagrat/Baladi/Deeptadi avasthas) | p.23 | calculation table | COVERED-PARTIAL | `calculations/jaimini/karakas.py` computes karakas, consumed internally by `arudha_lagna`/`upapada_lagna`; this avastha-table presentation is not a direct Q&A answer. |
| 20 | Char Maha Dasha / Char Antardasha tables | p.24-25 | calculation table | COVERED-PARTIAL | `calculations/dashas/chara.py` exists; `current_dasha` uses Vimshottari only, not Chara Dasha. |
| 21 | Remedial Measures / Remedies (gemstones, mantras, charity, etc.) | p.29-33 | remedy | OUT-OF-SCOPE-LOCKED | CLAUDE.md T4 architecture: "Pratyantar + Lal Kitab sections extracted (parser UNCHANGED) but withheld at display layer" — this content is captured under the parser's "Lal Kitab" keyword match and thus withheld. Also independently excluded by the V1 remedy scope lock ("Post-V1 design gate: Lal Kitab remedy tier" carry-forward) — doubly excluded, not just unbuilt. |
| 22 | Lal Kitab Dasha + planet-by-planet "Consideration" paragraphs (Sun through Ketu) | p.34-39 | remedy / interpretive | OUT-OF-SCOPE-LOCKED | Same citation as #21. |
| 23 | Shodashvarga Bhav Table (16-varga position table) | p.40 | calculation table | COVERED-PARTIAL | `vargas/` package (D2-D60) computes divisional positions; no routed domain surfaces a full varga table as a Q&A answer. |
| 24 | Divisional-chart planet-grid diagrams | p.41-43 | calculation table (chart diagrams) | COVERED-PARTIAL | Same `vargas/` package, unrouted presentation. |
| 25 | KP astrology block: Ruling Planet, Cuspal Positions, Planetary Positions (RASH/NAK/SUB/SS sub-lord columns), KP dasha-bhukti tables | p.44-48 | calculation table | NOT-COVERED | Krishnamurti Paddhati is a separate calculation system; no KP submodule exists anywhere in the `calculations/` architecture (`core`/`vargas`/`strength`/`dashas`/`yogas`/`transits`/`ashtakavarga`/`jaimini`/`annual`/`helpers`). |
| 26 | Permanent / Temporal / Five-fold Planetary Friendship tables | p.49 | calculation table | COVERED-PARTIAL | Planetary friendship (Naisargika/Tatkalika/Panchadha Maitri) is used internally by `core/dignity.py`; no standalone Q&A surface presents these reference tables directly. |
| 27 | ShadBala Table / BhavBala Table | p.50 | calculation table | COVERED-CALC | `career_strength` domain (`compute_shadbala_totals` + `compute_bhava_bala_totals`, verified at `agent/infra/chart_profile.py`). |
| 28 | Aspects on Bhav Madhya / Aspects on KP Cusp (Western-style CONJ/OPPN/TRIN/SQUR/SEXT grids with orb/weight) | p.51-53 | calculation table | NOT-COVERED | Western tropical-aspect methodology on a KP cusp basis; no equivalent V1 module (V1's `core/aspects.py`, per its package naming, implements Vedic graha drishti — a different system). |
| 29 | Unlabeled numeric strength grid (planet rows, small integer columns) | p.54 | calculation table | NOT-COVERED | System could not be confidently identified from headings alone during this audit; no obviously-named V1 equivalent. Flagged as low-confidence, not force-classified. |
| 30 | Final planet-grouping page (Sun/Moon, Mars/Mercury, Jupiter/Venus, Saturn headings) | p.55 | remedy / interpretive (likely continuation) | OUT-OF-SCOPE-LOCKED | Low-confidence attribution — heading pattern matches the p.34-39 planet-Consideration remedial sequence; same citation as #21 if so. |
| 31 | Back cover | p.56 | promo-noise (no text extracted) | N/A | — |

## Summary counts

| Classification | Count | Sections |
|---|---|---|
| COVERED-CALC | 3 | #5 (Vimshottari Dasha), #13 (Sade Sati table), #27 (ShadBala/BhavBala) |
| COVERED-PARTIAL | 10 | #2, #4, #6, #8, #14, #19, #20, #23, #24, #26 |
| NOT-COVERED | 13 | #3, #7, #9, #10, #11, #12, #15, #16, #17, #18, #25, #28, #29 |
| OUT-OF-SCOPE-LOCKED | 3 | #21, #22, #30 |
| N/A (promo/cover) | 2 | #1, #31 |
| Not present in this PDF | 1 (noted, not counted in the 31-row matrix) | Transit Today (keyword defined in parser, absent from this document) |
| **Total matrix rows** | **31** | |

## Note on Pass 1 vs. Pass 2 divergence

The existing `parse_astrosage_pdf()` splitter — the one actually wired
into the live T4 pipeline today — only ever looks for 7 fixed keywords
and returns 6 matches (40,929 chars) for this PDF. Pass 2's full-
taxonomy walk surfaces 24 additional distinct sections (rows 2, 4, 6-12,
15, 19, 20, 23-29) that the current code never extracts or displays at
all — not withheld by any lock, simply never looked for. This is a
factual observation about the current extraction surface's narrowness,
not a recommendation; whether any of it should be added to the
splitter's target list is a design-chat call.
