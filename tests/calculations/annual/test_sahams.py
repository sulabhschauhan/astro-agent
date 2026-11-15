"""Tajaka Sahams -- deterministic 4-chart validation (S162).

Each of the four Sulabh annual charts (2024/25 day, 2026/27 night) is fed as
literal longitudes; every CONFIRMED saham must reproduce JHora (jhora_sulabh.md
section 9) on ALL FOUR to <0.5 deg. Annual longitudes are the engine's own
varsha_pravesh output (== JHora annual chart to <0.07 deg; the ~0.05 deg
constant offset is the 4' Lagna gap, under tolerance). No swisseph needed here;
the four-year ORACLE is what guards the day AND night branches.

PENDING sahams are not emitted by default and not asserted; they await
per-saham re-derivation from Nilakantha (docs/sahams_reconciliation_S162.md).
"""
import pytest
from agent.calculations.annual.sahams import compute_sahams, TABLE

def _ang(a,b): return abs((a-b+180)%360-180)
_CONF = [d.name for d in TABLE if d.status=="CONFIRMED"]
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

CHARTS = {
  2024: (False, dict(Su=352.51566,Mo=314.04686,Ma=316.73488,Me=2.09232,Ju=24.25504,Ve=336.87637,Sa=319.96974,Ra=351.59754,Ke=171.59754,La=4.23204)),
  2025: (False, dict(Su=352.51566,Mo=96.96112,Ma=91.20075,Me=332.67951,Ju=52.61769,Ve=331.34118,Sa=330.91486,Ra=332.24186,Ke=152.24186,La=96.53802)),
  2026: (True,  dict(Su=352.51566,Mo=222.46856,Ma=333.23127,Me=324.91674,Ju=81.96216,Ve=14.23919,Sa=342.01666,Ra=312.88600,Ke=132.88600,La=181.41822)),
  2027: (True,  dict(Su=352.51566,Mo=350.00209,Ma=116.84853,Me=332.16650,Ju=112.81699,Ve=319.57984,Sa=353.31660,Ra=293.53075,Ke=113.53075,La=261.99569)),
}


@pytest.mark.parametrize("year", sorted(CHARTS))
def test_confirmed_sahams_all_four_charts(year):
    night, pts = CHARTS[year]
    got = compute_sahams(pts, night=night)
    oracle = ORACLE[year][1]
    bad = []
    for n in _CONF:
        if n in oracle and _ang(got[n], oracle[n]) >= 0.5:
            bad.append(f"{n}: {got[n]:.3f} vs JHora {oracle[n]:.3f}")
    assert not bad, f"{year} ({'night' if night else 'day'}): " + "; ".join(bad)


def test_pending_not_emitted_by_default():
    _, pts = CHARTS[2024]
    got = compute_sahams(pts, night=False)
    for d in TABLE:
        if d.status == "PENDING":
            assert d.name not in got, f"{d.name} is PENDING; must not emit by default"


def test_missing_longitude_raises():
    _, pts = CHARTS[2024]
    bad = dict(pts); del bad["La"]
    with pytest.raises(ValueError):
        compute_sahams(bad, night=False)
