"""Regression pin for Muntha (B): exact vs JHora 2025/26/27 (natal Lagna 22Sg40'59")."""
import pytest

from agent.calculations.annual.muntha import compute_muntha

NATAL_LAGNA = 240.0 + 22.0 + 40.0 / 60 + 59.06 / 3600   # 22 Sg 40'59.06" = 262.683
# year -> (completed years, expected muntha sign idx, annual Lagna sign idx)
CASES = {2025: (37, 9, 3), 2026: (38, 10, 6), 2027: (39, 11, 8)}   # Cp/Aq/Pi; Cn/Li/Sg lagna


@pytest.mark.parametrize("year", sorted(CASES))
def test_sign_and_degree(year):
    years, sign, lagna = CASES[year]
    r = compute_muntha(NATAL_LAGNA, years, lagna)
    assert r["muntha_sign"] == sign
    assert r["muntha_lon"] % 30 == pytest.approx(NATAL_LAGNA % 30, abs=1e-9)  # 22 40'59"


def test_house_from_annual_lagna():
    houses = {y: compute_muntha(NATAL_LAGNA, c, l)["muntha_house_from_annual_lagna"]
              for y, (c, _, l) in CASES.items()}
    assert houses == {2025: 7, 2026: 5, 2027: 4}   # Cp from Cn, Aq from Li, Pi from Sg


def test_one_sign_per_year_and_wrap():
    signs = [compute_muntha(NATAL_LAGNA, n, 0)["muntha_sign"] for n in range(37, 50)]
    assert all((b - a) % 12 == 1 for a, b in zip(signs, signs[1:]))
    assert compute_muntha(NATAL_LAGNA, 12, 0)["muntha_sign"] == 8   # 12 years = full cycle


@pytest.mark.parametrize("args", [(-1.0, 1, 0), (360.0, 1, 0), (10.0, -1, 0),
                                  (10.0, 1.5, 0), (10.0, 1, 12)])
def test_invalid_inputs_raise(args):
    with pytest.raises(ValueError):
        compute_muntha(*args)
