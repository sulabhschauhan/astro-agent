"""
sun_chesta_characterization_20260704.py
Session 47, post-K24 baseline (K24 = kala_bala.py _ayana_bala() Kranti fix:
Sayana-longitude Kranti, fixed 24deg obliquity, Raman Art. 72-73).
READ-ONLY characterization -- no project files modified, no parameters tuned.

Question: chesta_bala.py's Sun Chesta = Ayana Bala directly (BPHS 27.18,
doubled per the Sun *2.0 rule). Does the UNDOUBLED variant (ayana / 2, the
pre-doubling base) clear +/-1.0 Virupa vs AstroSage on all 4 reference charts?

Verdict: NO -- 0/4 charts clear +/-1.0. Best case +1.95 (surbhi), worst case
-5.72 (david). Residual sign flips with declination hemisphere (positive/
overshoot for sulabh, surbhi, sheridan; negative/undershoot for david) and
magnitude grows toward the +/-24deg Kranti extremes (sheridan's undoubled
value sits near the 60 ceiling -- Sun near summer solstice, 27 May; david's
sits near the 0 floor -- Sun near winter solstice, 19 Jan). Conclusion:
AstroSage is using a distinct Sun-Chesta formula, not a simple Ayana/2
halving -- this is a formula-shape gap, not a K24 data-quality artifact.

Undoubling would clear all 3 currently-xfailed Ishta/Kashta Sun cases
(sulabh, surbhi, sheridan -- all drop below the chesta_bala > 60 xfail
trigger) but introduces fresh deltas vs the JHora v8 Ishta/Kashta oracle
up to ~6 Virupa (worst: david ishta -5.85, sheridan kashta -4.00). Net:
not a clean win, trades one gap for another.

V1.1 status: OPEN. Pointer: CLAUDE.md Known Source Divergences section,
"Sun Ayana Bala doubling" entry.

Birth data below is transcribed verbatim from tests/fixtures/shadbala_fixtures.py
(AstroSage source) and tests/fixtures/jhora_shadbala_fixtures.py (JHora v8
source, sulabh/surbhi only -- sheridan/david have no JHora Sun-chesta fixture).

Runnable standalone: python diagnostics/sun_chesta_characterization_20260704.py
No pytest fixtures; not pytest-collected (no test_ prefix in filename or functions).
"""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from agent.chart_calculator import calculate_chart
from agent.calculations.strength.kala_bala import compute_kala_bala
from agent.calculations.strength.chesta_bala import compute_chesta_bala
from agent.calculations.strength.ishta_kashta import compute_ishta_kashta

CHARTS = {
    "sulabh":   ("Sulabh",   "6 Apr 1988", "00:30", "Calcutta, India"),
    "surbhi":   ("Surbhi",   "11 Sep 1992", "10:30", "Patna, India"),
    "sheridan": ("Sheridan", "27 May 1984", "08:00", "Durban, South Africa"),
    "david":    ("David",    "19 Jan 1976", "22:00", "London, UK"),
}

# AstroSage Sun chesta/ayana, verbatim from tests/fixtures/shadbala_fixtures.py
AS_SUN = {
    "sulabh":   {"chesta": 35.40, "ayana": 76.23},
    "surbhi":   {"chesta": 33.76, "ayana": 71.35},
    "sheridan": {"chesta": 52.05, "ayana": 114.14},
    "david":    {"chesta": 9.66,  "ayana": 7.99},
}

# JHora v8 Sun chesta/ayana, verbatim from tests/fixtures/jhora_shadbala_fixtures.py
# (sulabh/surbhi only)
JHORA_SUN = {
    "sulabh": {"chesta": 35.18, "ayana": 75.59},
    "surbhi": {"chesta": 34.01, "ayana": 72.09},
}

# JHora v8 Strengths-tab Ishta/Kashta oracle, Sun row only, verbatim from
# tests/fixtures/... via tests/calculations/strength/test_ishta_kashta.py
# JHORA_ISHTA_KASHTA dict.
JHORA_ISHTA_KASHTA_SUN = {
    "sulabh":   (43.66, 12.02),
    "surbhi":   (22.59, 34.20),
    "sheridan": (50.48, 9.41),
    "david":    (16.44, 39.90),
}

rows = []
for key, (name, date, time, place) in CHARTS.items():
    chart = calculate_chart(name, date, time, place)

    kala = compute_kala_bala(chart)
    current_ayana = kala["sun"]["ayana"]  # doubled, post-K24
    undoubled = current_ayana / 2.0

    # current code Sun chesta = ayana (doubled), per chesta_bala.py's
    # "Sun: Chesta = Ayana Bala (BPHS 27.18)" rule
    current_chesta = current_ayana

    as_chesta = AS_SUN[key]["chesta"]
    as_ayana  = AS_SUN[key]["ayana"]

    jhora_chesta = JHORA_SUN.get(key, {}).get("chesta")
    jhora_ayana  = JHORA_SUN.get(key, {}).get("ayana")

    rows.append({
        "chart": key,
        "current_ayana_code": round(current_ayana, 2),
        "current_chesta_code": round(current_chesta, 2),
        "undoubled_code": round(undoubled, 2),
        "as_ayana_fixture": as_ayana,
        "as_chesta_fixture": as_chesta,
        "jhora_ayana_fixture": jhora_ayana,
        "jhora_chesta_fixture": jhora_chesta,
        "undoubled_vs_AS": round(undoubled - as_chesta, 2),
        "undoubled_vs_JHora": (round(undoubled - jhora_chesta, 2) if jhora_chesta is not None else None),
    })

print(f"{'Chart':10} {'Current':>8} {'Undoubled':>10} {'AS-Chesta':>10} {'JHora-Chesta':>13} {'Und-vs-AS':>10} {'Und-vs-JHora':>13}")
for r in rows:
    print(f"{r['chart']:10} {r['current_chesta_code']:8.2f} {r['undoubled_code']:10.2f} "
          f"{r['as_chesta_fixture']:10.2f} "
          f"{(r['jhora_chesta_fixture'] if r['jhora_chesta_fixture'] is not None else float('nan')):13.2f} "
          f"{r['undoubled_vs_AS']:10.2f} "
          f"{(r['undoubled_vs_JHora'] if r['undoubled_vs_JHora'] is not None else float('nan')):13.2f}")

print()
print("Raw ayana (code, post-K24, doubled) vs AstroSage fixture ayana vs JHora fixture ayana:")
for r in rows:
    print(f"  {r['chart']:10} code_ayana={r['current_ayana_code']:.2f}  AS_ayana={r['as_ayana_fixture']}  JHora_ayana={r['jhora_ayana_fixture']}")

print()
print("Clears +/-1.0 vs AstroSage on 4/4?", all(abs(r["undoubled_vs_AS"]) <= 1.0 for r in rows))
for r in rows:
    print(f"  {r['chart']:10} |delta|={abs(r['undoubled_vs_AS']):.2f}  {'PASS' if abs(r['undoubled_vs_AS'])<=1.0 else 'FAIL'}")

print()
print("=== Ishta/Kashta Sun xfail characterization (chesta_bala > 60 triggers xfail) ===")
for key, (name, date, time, place) in CHARTS.items():
    chart = calculate_chart(name, date, time, place)
    ik = compute_ishta_kashta(chart)
    cb_current = ik["sun"]["chesta_bala"]
    xfail_now = cb_current > 60.0
    kala = compute_kala_bala(chart)
    undoubled_chesta = kala["sun"]["ayana"] / 2.0
    would_xfail_undoubled = undoubled_chesta > 60.0

    uchcha = ik["sun"]["uchcha_bala"]
    ishta_sq  = max(0.0, uchcha * undoubled_chesta)
    kashta_sq = max(0.0, (60.0 - uchcha) * (60.0 - undoubled_chesta))
    undoubled_ishta  = round(math.sqrt(ishta_sq), 2)
    undoubled_kashta = round(math.sqrt(kashta_sq), 2)

    jhora_ishta, jhora_kashta = JHORA_ISHTA_KASHTA_SUN[key]

    print(f"{key:10} current_chesta={cb_current:.2f} xfail_now={xfail_now}  "
          f"undoubled_chesta={undoubled_chesta:.2f} would_still_xfail={would_xfail_undoubled}")
    print(f"           current: ishta={ik['sun']['ishta_phala']:.2f} kashta={ik['sun']['kashta_phala']:.2f}  "
          f"(JHora ishta={jhora_ishta} kashta={jhora_kashta})")
    print(f"           undoubled: ishta={undoubled_ishta:.2f} (delta={undoubled_ishta - jhora_ishta:+.2f})  "
          f"kashta={undoubled_kashta:.2f} (delta={undoubled_kashta - jhora_kashta:+.2f})")
