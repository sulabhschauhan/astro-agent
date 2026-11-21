# Tajaka Sahams — pending-formula derivation (S163 → S164)

## S164 UPDATE — 8 of the 9 resolved (house-lord terms were the missing piece)

**All 9 resolved — 33 CONFIRMED, 0 SOURCE, 0 pending (S165).** House-lords and a
no-night-swap mode resolved 6 against the oracle; **Samartha** came from PyJHora's
source; **Preeti/Jalapatana** used PyJHora formulas, then were graded against the
JHora v8 **desktop Sahama tables** Sulabh exported (all 4 charts <0.5°). Final:

- **33 CONFIRMED** (oracle-validated, 4 charts): the 24 + **Artha** (Nilakantha
  Dhana #26, `(H2−L2)+La`), **Labha** (`(H11−L11)+La`), **Gaurava** (Nilakantha
  Guruta #45, `(Ju−Mo)+Su`), **Bhratru** (`Ju−Sa`, no reversal), **Vyapara**
  (`Ma−Sa`, no reversal — JHora's; ≠ Nilakantha व्यापार = Karma), **Roga**
  (`(H12−Mo)`, no reversal), **Samartha** (`(Mars − Lagna-lord)+La`, reverse-all
  night; if Mars owns lagna → Jupiter substitutes + day/night flips — from
  PyJHora `horoscope/transit/saham.py`, Δ<0.07 on 4 charts).
  including **Preeti** `(Sastra−Punya)+La`, reverse-all night (JHora uses Sastra,
  not Vidya as Nila #36 does), and **Jalapatana** `(105° − Saturn)+La`, reverse-all
  night (JHora uses the fixed point 15° Cancer, not Nila's Sa−Mo) — both now graded
  against the desktop Sahama tables.

ADDED S165 — the full 36-saham JHora set: **Mrityu** `(H8−Mo)+La` (no reversal),
**Paradesa** `(H9−L9)+La` (no reversal), **Apamrityu** `(H8−Ma)+La` (reverse-all
night) — all PyJHora formulas, desktop-oracle validated (<0.5°, 4 charts). The two
death-group sahams (Mrityu, Apamrityu) are suppressed at the answer layer by
prompt; they are computed as background strength context, never a mortality
forecast. **Engine total: 36 CONFIRMED, 0 pending.**

Two source leads cracked it: the Nilakantha saham index (l.3481–3496) names all 50
(confirming Dhana#26=Artha, Guruta#45=Gaurava), and **PyJHora's installed source**
gave Samartha's exact formula + its Mars-owns-lagna exception. Uttara Kalāmṛta was
read end-to-end and has no sahams at all. Everything below is the original S163
analysis, superseded where S164 resolves it.

---

Continues `sahams_reconciliation_S162.md`. Method unchanged: formula comes FROM the
source shloka; JHora §9 (`tests/fixtures/jhora_sulabh.md`, embedded in
`test_sahams.py`) **grades only**, across the four Sulabh annual charts
(2024/25 day, 2026/27 night). A promotion requires the SOURCE to state the
formula AND the formula to reproduce JHora on all four charts <0.5°. No pair was
fitted to one chart.

## Outcome: 3 promoted (21 → 24 confirmed)

| Saham | Formula (day) | Night | Source | 4-chart max Δ |
|---|---|---|---|---|
| **Karyasiddhi** | (Saturn − Sun) + lord-of-Sun-sign | **day/night-DISTINCT**: (Saturn − Moon) + lord-of-Moon-sign | Nilakantha #31, l.3530–31 + śloka l.3562–63 (`शनेर्दिवा…निशि चंद्रमा…राशिनाथयोगात्…कार्यसिद्धिः`) | 0.000 |
| **Sastra** (Śāstra) | (Jupiter − Saturn) + Mercury | reverse-all: (Saturn − Jupiter) + Mercury | Nilakantha #22, l.3527–28 (`दिनको बृहस्पतिमं शनि, रात्रिको शनिमं बृहस्पति घटायके शेषमें बुध जोडना शाख्सहम`) | 0.000 |
| **Santapa** | (Saturn − Moon) + 6th-bhava cusp | reverse-all | Nilakantha #34, l.3560–61 + śloka l.3575–76 (`…निशि…विशोध्य षष्ठं क्षिपेत्…संतापसद्म`); षष्ठं = 6th | 0.066 |

Karyasiddhi needed a mechanism the engine lacked: a saham whose **points differ by
day/night** (not a simple A,B swap). Added as `night=(a,b,third)` override on
`SahamDef`.

Santapa's 0.066° is the same ~4′ Lagna-cusp offset every Lagna-derived saham
carries (the close term is the 6th cusp); under tolerance, same class as the
confirmed Lagna-based sahams.

## Held — JHora reproduces, but name ABSENT from Nilakantha (your call)

These four reproduce the JHora oracle on all four charts, but the **name does not
exist anywhere in `tajika_nilakanthi_hindi_djvu.txt`** — so the formula cannot be
cited to Nilakantha. Shipping them means accepting *JHora-structure-match across 4
charts/2 branches* as sufficient when the book is silent on the name. That is a
methodology decision (JHora is charter-defined as grader-only), so it is yours.

| Saham | Formula that reproduces JHora | 4-chart max Δ | Note |
|---|---|---|---|
| Gaurava | (Jupiter − Moon) + Sun, reverse-all | 0.000 | not in Nilakantha |
| Bhratru | (Jupiter − Saturn), **no night reversal** | 0.066 | = Jeeva's night value held constant |
| Vyapara | (Mars − Saturn), **no night reversal** | 0.066 | Nilakantha's व्यापार (l.3544) is (Mars − Mercury) = Karma — a DIFFERENT formula. JHora's "Vyapara" ≠ book's व्यापार. |
| Roga | (12th-cusp − Moon), no reversal | 0.132 | Nilakantha has रोग only as phala ("five inauspicious sahams", l.3829), no formula śloka. |

The lead for sourcing these: JHora's wider saham list likely follows a 36-saham
tradition (Uttara Kalāmṛta / Kalidasa), not Nilakantha. `uttkalamrita-kalidas-ps-sastri.pdf`
is in `data/pdfs/` — a future pull could source Gaurava/Bhratru/Samartha/Artha/Labha.

## Blocked — cannot resolve here

| Saham | Blocker |
|---|---|
| Samartha, Artha, Labha | No 2/3-point combo reproduces JHora on all 4 charts (searched all planets + houses + Lsun/Lmoon + every confirmed saham as component), AND the names are absent from Nilakantha. Likely 4-term or Uttara-Kalāmṛta-specific. |
| Preeti | Nilakantha #36 (l.3539–40) = (Vidya − Punya) + Lagna, source-clear — but **not in JHora §9 oracle**, so ungradeable. |
| Jalapatana | Nilakantha पानीयपतन (l.3546) exists but **not in JHora §9 oracle**. |

To grade Preeti/Jalapatana or the four JHora-only sahams against a named source,
the next JHora pull must include §9 values for them (Preeti/Jalapatana) or the
Uttara-Kalāmṛta OCR must be added (the five proprietary names).
