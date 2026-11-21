"""Diagnostic (S162): does varsha_pravesh reproduce JHora's 2024 annual D-1 chart?

The saham formulas are proven exact on JHora's OWN 2024 annual longitudes
(test_sahams.py layer 1). The four-year integration fails, which points at the
INPUT -- varsha_pravesh's computed annual chart vs what JHora casts. This prints
the engine's 2024 annual Lagna + planets next to JHora's published 2024 annual
chart so the gap is visible in one run:

    pytest tests/calculations/annual/test_varsha_annual_diag.py -s -q
"""
import pytest

_B = {'Ar':0,'Ta':30,'Ge':60,'Cn':90,'Le':120,'Vi':150,'Li':180,'Sc':210,
      'Sg':240,'Cp':270,'Aq':300,'Pi':330}
def _dms(s,d,m,sec): return _B[s]+d+m/60.0+sec/3600.0

# JHora "Find Tajaka Chart" 2024 annual D-1 (your first screenshot)
JHORA_2024 = {
    'La': _dms('Ar',4,9,56.95), 'Sun': _dms('Pi',22,30,56.53),
    'Moon': _dms('Aq',14,2,48.83), 'Mars': _dms('Aq',16,44,5.69),
    'Mercury': _dms('Ar',2,5,32.47), 'Jupiter': _dms('Ar',24,15,18.27),
    'Venus': _dms('Pi',6,52,35.06), 'Saturn': _dms('Aq',19,58,11.19),
    'Rahu': _dms('Pi',21,35,51.30), 'Ketu': _dms('Vi',21,35,51.30),
}
def _d2dms(x):
    x%=360; s=int(x//30); r=x-30*s; d=int(r); m=int((r-d)*60); sec=((r-d)*60-m)*60
    names=['Ar','Ta','Ge','Cn','Le','Vi','Li','Sc','Sg','Cp','Aq','Pi']
    return f"{d:2d} {names[s]} {m:02d}'{sec:05.2f}\""


def test_engine_annual_2024_vs_jhora():
    pytest.importorskip("swisseph")
    from agent.chart_calculator import calculate_chart
    from agent.calculations.annual.varsha_pravesh import compute_varsha_pravesh
    chart = calculate_chart("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")
    jd = chart["meta"]["jd_ut"]; bd = chart["birth_details"]
    vp = compute_varsha_pravesh(jd, bd["lat"], bd["lon"], 2024)
    eng = dict(vp["planets_sid"]); eng['La'] = vp["ascendant_sid"]
    print("\n--- varsha_pravesh 2024 vs JHora annual D-1 ---")
    print(f"pravesh_jd_ut={vp['pravesh_jd_ut']:.6f}  cast={vp.get('cast_place')}")
    print(f"{'body':8} {'engine':>18} {'JHora':>18} {'delta(deg)':>11}")
    worst = 0.0
    for k in ['La','Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu']:
        e = eng.get(k); j = JHORA_2024[k]
        if e is None:
            print(f"{k:8} {'MISSING':>18}"); continue
        dl = abs((e - j + 180) % 360 - 180)
        worst = max(worst, dl)
        print(f"{k:8} {_d2dms(e):>18} {_d2dms(j):>18} {dl:11.4f}")
    print(f"worst delta = {worst:.4f} deg")
    # Not an assertion gate -- this is a diagnostic. It fails loudly only if the
    # engine chart is grossly off, to flag an input problem vs a formula one.
    assert worst < 1.0, (
        f"varsha_pravesh 2024 annual chart differs from JHora by up to "
        f"{worst:.3f} deg -- the saham integration failures are an INPUT problem "
        f"(annual chart), not a formula problem. See printed table.")
