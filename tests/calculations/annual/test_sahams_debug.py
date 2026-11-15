"""Saham debug dump to a file (S162) -- run once:
    pytest tests/calculations/annual/test_sahams_debug.py -s -q
Writes diagnostics/sahams_debug_S162.txt with full-precision annual charts +
every saham engine-vs-JHora delta, for offline formula repair.
"""
import pytest
from pathlib import Path
from agent.calculations.annual.sahams import compute_sahams
def _ang(a,b): return abs((a-b+180)%360-180)

ORACLE = {
    2024: ('DAY', {
        'Punya': 325.697014,
        'Vidya': 72.634622,
        'Yasas': 62.723881,
        'Mitra': 35.434469,
        'Mahatmya': 43.127917,
        'Asha': 37.400678,
        'Samartha': 71.685978,
        'Bhratru': 68.451119,
        'Gaurava': 62.723881,
        'Pitru': 331.619892,
        'Rajya': 331.619892,
        'Matru': 341.336311,
        'Putra': 74.373997,
        'Jeeva': 329.880517,
        'Karma': 318.808381,
        'Roga': 54.284739,
        'Kali': 71.685978,
        'Sastra': 66.377656,
        'Bandhu': 82.211272,
        'Paradara': 348.526522,
        'Vanik': 316.120364,
        'Karyasiddhi': 351.709147,
        'Vivaha': 51.07245,
        'Santapa': 190.088694,
        'Sraddha': 54.307308,
        'Jadya': 358.857494,
        'Vyapara': 0.930958,
        'Satru': 0.930958,
        'Bandhana': 39.893056,
        'Artha': 61.455231,
        'Labha': 348.361861,
    }),
    2025: ('DAY', {
        'Punya': 200.931139,
        'Vidya': 22.040225,
        'Yasas': 338.172272,
        'Mitra': 213.027811,
        'Mahatmya': 206.216033,
        'Asha': 336.199789,
        'Samartha': 120.725314,
        'Bhratru': 208.188517,
        'Gaurava': 338.172272,
        'Pitru': 74.884875,
        'Rajya': 74.884875,
        'Matru': 222.105619,
        'Putra': 82.142253,
        'Jeeva': 14.78285,
        'Karma': 245.006922,
        'Roga': 96.010206,
        'Kali': 57.902622,
        'Sastra': 84.382386,
        'Bandhu': 2.204075,
        'Paradara': 75.311203,
        'Vanik': 220.767292,
        'Karyasiddhi': 31.016922,
        'Vivaha': 126.912011,
        'Santapa': 150.439419,
        'Sraddha': 336.626117,
        'Jadya': 122.965444,
        'Vyapara': 246.771578,
        'Satru': 246.771578,
        'Bandhana': 326.501928,
        'Artha': 230.455664,
        'Labha': 191.630144,
    }),
    2026: ('NIGHT', {
        'Punya': 341.409389,
        'Vidya': 51.315186,
        'Yasas': 80.809481,
        'Mitra': 273.686428,
        'Mahatmya': 173.184206,
        'Asha': 172.576892,
        'Samartha': 252.370217,
        'Bhratru': 311.307781,
        'Gaurava': 133.022108,
        'Pitru': 221.861289,
        'Rajya': 221.861289,
        'Matru': 3.132919,
        'Putra': 321.868694,
        'Jeeva': 311.307781,
        'Karma': 173.047761,
        'Roga': 140.255975,
        'Kali': 72.631397,
        'Sastra': 224.971286,
        'Bandhu': 78.914111,
        'Paradara': 159.638756,
        'Vanik': 313.810464,
        'Karyasiddhi': 122.779406,
        'Vivaha': 149.139756,
        'Santapa': 211.814189,
        'Sraddha': 140.354358,
        'Jadya': 3.702175,
        'Vyapara': 172.576892,
        'Satru': 220.147683,
        'Bandhana': 211.9696,
        'Artha': 59.493269,
        'Labha': 340.208872,
    }),
    2027: ('NIGHT', {
        'Punya': 294.444472,
        'Vidya': 259.417333,
        'Yasas': 83.55835,
        'Mitra': 141.207322,
        'Mahatmya': 114.334997,
        'Asha': 55.462831,
        'Samartha': 257.899364,
        'Bhratru': 51.431292,
        'Gaurava': 229.700808,
        'Pitru': 261.129967,
        'Rajya': 261.129967,
        'Matru': 231.508647,
        'Putra': 139.116011,
        'Jeeva': 51.431292,
        'Karma': 117.248869,
        'Roga': 173.859675,
        'Kali': 295.962444,
        'Sastra': 212.666147,
        'Bandhu': 309.766503,
        'Paradara': 324.866728,
        'Vanik': 244.095306,
        'Karyasiddhi': 146.131536,
        'Vivaha': 325.667667,
        'Santapa': 48.616397,
        'Sraddha': 89.199594,
        'Jadya': 208.634608,
        'Vyapara': 55.462831,
        'Satru': 138.398978,
        'Bandhana': 350.803072,
        'Artha': 200.545167,
        'Labha': 174.281931,
    }),
}


def test_dump_all_years():
    pytest.importorskip("swisseph")
    from agent.chart_calculator import calculate_chart
    from agent.calculations.annual.varsha_pravesh import compute_varsha_pravesh
    from agent.astro.varshaphal_facts import _is_night
    chart=calculate_chart("Sulabh","6 Apr 1988","00:30","Calcutta, India")
    jd=chart["meta"]["jd_ut"]; bd=chart["birth_details"]; lat,lon=bd["lat"],bd["lon"]
    ab={'Sun':'Su','Moon':'Mo','Mars':'Ma','Mercury':'Me','Jupiter':'Ju',
        'Venus':'Ve','Saturn':'Sa','Rahu':'Ra','Ketu':'Ke'}
    out=[]
    for year,(branch,oracle) in sorted(ORACLE.items()):
        vp=compute_varsha_pravesh(jd,lat,lon,year)
        night=_is_night(vp["pravesh_jd_ut"],float(lat),float(lon))
        pts={ab[k]:v for k,v in vp["planets_sid"].items() if k in ab}
        pts['La']=vp["ascendant_sid"]
        out.append(f"YEAR {year} tag={branch} engine_is_night={night}")
        out.append("PTS "+" ".join(f"{k}={pts[k]:.5f}" for k in ['Su','Mo','Ma','Me','Ju','Ve','Sa','Ra','Ke','La']))
        got=compute_sahams(pts, night=night)
        for n,exp in sorted(oracle.items()):
            out.append(f"  {n:12} eng={got[n]:.4f} jhora={exp:.4f} d={_ang(got[n],exp):.3f}")
        out.append("")
    p=Path(__file__).resolve().parents[2]/"diagnostics"/"sahams_debug_S162.txt"
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text("\n".join(out),encoding="utf-8")
    print("wrote", p)
