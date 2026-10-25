"""Muntha (sub-engine B): natal sidereal Lagna advanced one whole sign per
completed year, degree-within-sign preserved.

VALIDATED exact vs JHora for 2025/26/27 (data/default_user/jhora_sulabh_varshaphal.md,
"Muntha rule"). Pure arithmetic; no ephemeris call.
"""

_SIGN_DEG = 30.0


def compute_muntha(natal_lagna_sidereal_lon: float, completed_years: int,
                   annual_lagna_sign: int) -> dict:
    """Return {muntha_lon, muntha_sign, muntha_house_from_annual_lagna}.

    Signs are 0..11 (Aries=0); house is the whole-sign count 1..12 from the
    annual Lagna sign.

    Raises:
        ValueError: longitude outside [0, 360), negative/non-int years, or a
            sign outside 0..11.
    """
    if not (0.0 <= natal_lagna_sidereal_lon < 360.0):
        raise ValueError(
            f"muntha: natal Lagna longitude must be in [0, 360), got {natal_lagna_sidereal_lon}")
    if not isinstance(completed_years, int) or completed_years < 0:
        raise ValueError(f"muntha: completed_years must be a non-negative int, got {completed_years!r}")
    if not (isinstance(annual_lagna_sign, int) and 0 <= annual_lagna_sign <= 11):
        raise ValueError(f"muntha: annual_lagna_sign must be int 0..11, got {annual_lagna_sign!r}")

    lon = (natal_lagna_sidereal_lon + completed_years * _SIGN_DEG) % 360.0
    sign = int(lon // _SIGN_DEG)
    return {
        "muntha_lon": lon,
        "muntha_sign": sign,
        "muntha_house_from_annual_lagna": (sign - annual_lagna_sign) % 12 + 1,
    }
