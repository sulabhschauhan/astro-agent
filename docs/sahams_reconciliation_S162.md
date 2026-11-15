# Tajaka Sahams — formula reconciliation (S162)

**Spec source (P-028):** B.V. Raman, *Varshaphal* Ch.VII (`data/pdfs/2015...djvu.txt`,
pp.34–36) for the core; Tajika Nilakanthi (`data/tajika_nilakanthi_hindi_djvu.txt`,
Saham adhyaya) for the general rule and the wider set. JHora v8
(`tests/fixtures/jhora_sulabh.md` §9) **grades only** — four Sulabh annual charts
(2024/25 day, 2026/27 night).

## Rules (validated across all four charts — not fitted)
- **Two-point** Saham = `(A − B)`; if Lagna NOT in forward arc B→A, add 30°; + Lagna.
- **Three-point**: same `(A−B)` + 30° rule, but the **third point** closes it instead of Lagna.
- **Night** (pravesh Sun below horizon): A,B swap for **every** saham. This is JHora's
  measured convention (reverse-all: 16 night mismatches vs 26 for Raman's "some don't");
  since we grade against JHora, reverse-all wins. Confirmed concretely — JHora night
  Bhratru = its Jeeva, the exact swap.

## Method correction (S162)
The first engine brute-forced `A−B` pairs to fit **2024 alone**, then cited the book
post-hoc — the exact thing the Validation Source agent warns against. The 4-chart run
caught it: several pairs were only *coincidentally* right on 2024 (Samartha≡Kali,
Roga≡Sraddha, Vyapara≡Satru). The table below is now split by what actually validates
on all four charts.

## CONFIRMED — 21 (reproduce JHora on 2024/25 day + 2026/27 night, <0.5°)
Punya, Vidya, Yasas, Mitra, Pitru, Rajya, Putra, Jeeva, Karma, Vivaha, Satru,
Mahatmya, Asha, Matru, Sraddha, Kali, Bandhu, Paradara, Vanik, Bandhana, Jadya.

Raman-cited core (Punya, Vidya, Yasas, Mitra, Pitru/Rajya, Putra, Jeeva, Karma,
Vivaha, Satru) + Nilakantha-grounded additions, each now holding across both branches.

## PENDING — 11, held out (NOT emitted, NOT asserted)
Must be re-derived from Nilakantha's shloka and pass all four charts before promotion:

| Saham | Why pending |
|---|---|
| Samartha | 2024-coincident with Kali (Ju−Ma); wrong on 2025/26/27 |
| Roga | 2024-coincident with Sraddha (Ve−Ma); wrong elsewhere |
| Vyapara | diverges from Satru at night; own night form unknown |
| Gaurava, Bhratru | night form unverified |
| Sastra | +30° edge case unresolved on 2024 |
| Karyasiddhi, Artha, Labha | 3-term, night/term unverified |
| Santapa | Sa−Mo + bhava term (OCR 5th/7th) unverified |
| Preeti, Jalapatana | extra term unresolved from 2024 alone |

## Verification
`tests/calculations/annual/test_sahams.py` — deterministic, embeds the four annual
charts (engine `varsha_pravesh` output) + §9, asserts the 21 CONFIRMED across all four
years. `test_sahams_debug.py` dumps all 31 per year for the ongoing PENDING work.
