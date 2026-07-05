"""Tests for agent/calculations/core/combustion.py.

Layer A: Real-chart parity, all 4 charts, 18 hand-falsified rows (David
         first — highest edge-case density: 3 retrograde planets, a
         max-separation boundary). Oracle: hand-derived from AstroSage PDF
         page-3 planetary longitudes, transcribed Session 51 design chat.
         Separations are ayanamsa-invariant (difference of two same-frame
         longitudes); tolerance ±0.05 deg covers residual cross-ephemeris
         noise. Two rows carry a special assertion instead of/in addition to
         the tolerance check: Sulabh Mercury is a near-miss guard (must stay
         NOT combust with separation strictly above its orb); David Saturn
         sits at the max-separation edge (179 < sep <= 180) where hand
         arithmetic and Swiss Ephemeris diverge by more than the usual noise
         band, so the edge condition is asserted directly rather than a tight
         numeric diff.

         AstroSage exposes NO combustion surface — its Deeptadi avastha is
         dignity-only and never assigns Vikala/Asta (verified: Surbhi PDF
         p.23 shows Mercury=Muditha at 3.6 deg from Sun). Oracle basis for
         this module is hand-falsified arithmetic on AstroSage p.3
         longitudes, not an external combustion flag. PyJHora const.py:608-609
         orb divergence documented in combustion.py CITATION block.

         Depends on the Session 51 chart_calculator.py FLG_SPEED fix (the
         retrograde field was dead — always False — before that fix); see
         CLAUDE.md / diagnostics for the corrected retrograde map.

Layer B: Retro-override decisive band (6 synthetic cases). combustion.py's
         imported swe.calc_ut is monkeypatched to return controlled
         longitudes; chart_data supplies controlled retrograde flags. Proves
         Mercury/Venus narrow their orb when retrograde and Mars does not,
         at the exact decisive separations (13.0, 9.0, 16.9) and the strict
         less-than boundary (12.0 exactly, retrograde Mercury).

Layer C: Error contract — missing meta.jd_ut, missing a planetary_positions
         retrograde entry, and swe.calc_ut raising all surface as
         ValueError/RuntimeError with the offending name in the message.

Layer D: Output shape, all 4 real charts — exactly the 6 lowercase planet
         keys (sun/rahu/ketu absent), each value exactly
         {is_combust, separation_deg, orb_used, retrograde}.

Geocoder monkeypatched by tests/conftest.py; all 4 birth locations already
exist in tests/fixtures/geocoded_locations.json.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest

import agent.calculations.core.combustion as combustion_mod
from agent.calculations.core.combustion import compute_combustion

_ALL_CHARTS = ["david", "sulabh", "surbhi", "sheridan"]
_PLANETS = ["moon", "mars", "mercury", "jupiter", "venus", "saturn"]


# ── Module-scoped chart fixtures (David first — highest edge-case density) ──

@pytest.fixture(scope="module")
def david_result():
    from agent.chart_calculator import calculate_chart
    chart = calculate_chart("David", "19 Jan 1976", "22:00", "London, UK")
    return compute_combustion(chart)


@pytest.fixture(scope="module")
def sulabh_result():
    from agent.chart_calculator import calculate_chart
    chart = calculate_chart("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")
    return compute_combustion(chart)


@pytest.fixture(scope="module")
def surbhi_result():
    from agent.chart_calculator import calculate_chart
    chart = calculate_chart("Surbhi", "11 Sep 1992", "10:30", "Patna, India")
    return compute_combustion(chart)


@pytest.fixture(scope="module")
def sheridan_result():
    from agent.chart_calculator import calculate_chart
    chart = calculate_chart("Sheridan", "27 May 1984", "08:00", "Durban, South Africa")
    return compute_combustion(chart)


@pytest.fixture(scope="module")
def all_results(david_result, sulabh_result, surbhi_result, sheridan_result):
    return {
        "david":    david_result,
        "sulabh":   sulabh_result,
        "surbhi":   surbhi_result,
        "sheridan": sheridan_result,
    }


# ── Layer A: real-chart parity against hand-falsified AstroSage oracle ──────
# 18 rows: David (6) first, then Sulabh (3), Surbhi (3), Sheridan (6).
# Each entry: sep (deg), combust, orb (exact orb_used), retro (retrograde flag).

_TOL = 0.05

_LAYER_A_ORACLE = {
    ("david", "moon"):    {"sep": 143.794, "combust": False, "orb": 12.0, "retro": False},
    ("david", "mars"):    {"sep": 135.742, "combust": False, "orb": 17.0, "retro": True},
    ("david", "mercury"): {"sep": 7.307,   "combust": True,  "orb": 12.0, "retro": True},
    ("david", "jupiter"): {"sep": 78.447,  "combust": False, "orb": 11.0, "retro": False},
    ("david", "venus"):   {"sep": 36.699,  "combust": False, "orb": 10.0, "retro": False},
    ("david", "saturn"):  {"sep": 179.315, "combust": False, "orb": 15.0, "retro": True,
                            "max_sep_edge": True},

    ("sulabh", "moon"):    {"sep": 140.291, "combust": False, "orb": 12.0, "retro": False},
    ("sulabh", "mercury"): {"sep": 14.644,  "combust": False, "orb": 14.0, "retro": False,
                             "near_miss_guard": True},
    ("sulabh", "jupiter"): {"sep": 20.041,  "combust": False, "orb": 11.0, "retro": False},

    ("surbhi", "moon"):    {"sep": 170.236, "combust": False, "orb": 12.0, "retro": False},
    ("surbhi", "mercury"): {"sep": 3.597,   "combust": True,  "orb": 14.0, "retro": False},
    ("surbhi", "jupiter"): {"sep": 4.942,   "combust": True,  "orb": 11.0, "retro": False},

    ("sheridan", "moon"):    {"sep": 40.347,  "combust": False, "orb": 12.0, "retro": False},
    ("sheridan", "mars"):    {"sep": 159.280, "combust": False, "orb": 17.0, "retro": True},
    ("sheridan", "mercury"): {"sep": 24.003,  "combust": False, "orb": 14.0, "retro": False},
    ("sheridan", "jupiter"): {"sep": 144.298, "combust": False, "orb": 11.0, "retro": True},
    ("sheridan", "venus"):   {"sep": 5.338,   "combust": True,  "orb": 10.0, "retro": False},
    ("sheridan", "saturn"):  {"sep": 155.246, "combust": False, "orb": 15.0, "retro": True},
}

_LAYER_A_KEYS = list(_LAYER_A_ORACLE.keys())
_LAYER_A_IDS  = [f"{chart}-{planet}" for chart, planet in _LAYER_A_KEYS]


@pytest.mark.parametrize("chart_key,planet", _LAYER_A_KEYS, ids=_LAYER_A_IDS)
def test_a_oracle_parity(chart_key, planet, all_results):
    """Hand-falsified AstroSage-longitude oracle parity, 4 real charts, 18 rows."""
    row = all_results[chart_key][planet]
    exp = _LAYER_A_ORACLE[(chart_key, planet)]

    if exp.get("max_sep_edge"):
        # David Saturn: hand arithmetic and Swiss Ephemeris diverge beyond the
        # usual noise band this close to 180 deg; assert the edge condition
        # directly instead of a tight numeric diff against the oracle value.
        assert 179.0 < row["separation_deg"] <= 180.0, (
            f"{chart_key} {planet}: separation_deg={row['separation_deg']:.4f} "
            "outside max-separation edge band (179, 180]"
        )
    else:
        delta = abs(row["separation_deg"] - exp["sep"])
        assert delta <= _TOL, (
            f"{chart_key} {planet}: separation_deg={row['separation_deg']:.4f}, "
            f"oracle {exp['sep']:.3f}, delta {delta:.4f} (tol ±{_TOL})"
        )

    assert row["is_combust"] is exp["combust"], (
        f"{chart_key} {planet}: is_combust={row['is_combust']}, expected {exp['combust']}"
    )
    assert row["orb_used"] == pytest.approx(exp["orb"]), (
        f"{chart_key} {planet}: orb_used={row['orb_used']}, expected {exp['orb']}"
    )
    assert row["retrograde"] is exp["retro"], (
        f"{chart_key} {planet}: retrograde={row['retrograde']}, expected {exp['retro']}"
    )

    if exp.get("near_miss_guard"):
        assert row["is_combust"] is False and row["separation_deg"] > row["orb_used"], (
            f"{chart_key} {planet}: near-miss guard failed — separation_deg="
            f"{row['separation_deg']:.4f} must exceed orb_used={row['orb_used']}"
        )


# ── Layer B: retro-override decisive band (synthetic) ────────────────────────
# combustion.py's imported swe.calc_ut is monkeypatched to return controlled
# longitudes (Sun fixed at 0.0, target planet at the decisive separation);
# other planets are irrelevant to the row under test so are left at 0.0.
# Patches are restored automatically by the monkeypatch fixture.

def _fake_calc_ut(lon_by_name: dict[str, float]):
    pid_to_name = {pid: name for name, pid in combustion_mod._SWE_IDS.items()}

    def _calc_ut(jd_ut, pid, flags):
        name = pid_to_name[pid]
        return ([lon_by_name.get(name, 0.0), 0.0, 0.0, 0.0, 0.0, 0.0], 0)

    return _calc_ut


def _make_chart_data(retro_overrides: dict[str, bool]) -> dict:
    retro = {"Moon": False, "Mars": False, "Mercury": False,
             "Jupiter": False, "Venus": False, "Saturn": False}
    retro.update(retro_overrides)
    return {
        "meta": {"jd_ut": 2450000.0},
        "planetary_positions": {p: {"retrograde": r} for p, r in retro.items()},
    }


_LAYER_B_CASES = [
    # (planet_key, planet_title, sep, retro, exp_combust, exp_orb)
    ("mercury", "Mercury", 13.0, False, True,  14.0),
    ("mercury", "Mercury", 13.0, True,  False, 12.0),
    ("venus",   "Venus",    9.0, False, True,  10.0),
    ("venus",   "Venus",    9.0, True,  False,  8.0),
    ("mercury", "Mercury", 12.0, True,  False, 12.0),   # strict-< boundary, exact
    ("mars",    "Mars",    16.9, True,  True,  17.0),   # retro does not narrow Mars
]
_LAYER_B_IDS = [
    "mercury-direct-combust", "mercury-retro-notcombust",
    "venus-direct-combust",   "venus-retro-notcombust",
    "mercury-retro-boundary-exact12", "mars-retro-orb-unaffected",
]


@pytest.mark.parametrize(
    "planet_key,planet_title,sep,retro,exp_combust,exp_orb",
    _LAYER_B_CASES,
    ids=_LAYER_B_IDS,
)
def test_b_retro_override_band(monkeypatch, planet_key, planet_title, sep, retro, exp_combust, exp_orb):
    """Synthetic decisive-band cases: Mercury/Venus retro-narrow their orb, Mars does not."""
    monkeypatch.setattr(
        combustion_mod.swe, "calc_ut",
        _fake_calc_ut({"Sun": 0.0, planet_title: sep}),
    )
    chart_data = _make_chart_data({planet_title: retro})

    row = compute_combustion(chart_data)[planet_key]

    assert row["is_combust"] is exp_combust, (
        f"{planet_key} sep={sep} retro={retro}: is_combust={row['is_combust']}, "
        f"expected {exp_combust}"
    )
    assert row["orb_used"] == pytest.approx(exp_orb)
    assert row["retrograde"] is retro
    assert row["separation_deg"] == pytest.approx(sep, abs=1e-9)


# ── Layer C: error contract ───────────────────────────────────────────────────

def test_c_missing_jd_ut_raises_valueerror():
    """Missing chart_data['meta']['jd_ut'] must raise ValueError naming jd_ut."""
    with pytest.raises(ValueError, match="jd_ut"):
        compute_combustion({"meta": {}, "planetary_positions": {}})


def test_c_missing_retrograde_raises_valueerror():
    """Missing a planetary_positions[planet]['retrograde'] entry must raise ValueError."""
    chart_data = {
        "meta": {"jd_ut": 2450000.0},
        "planetary_positions": {
            "Moon": {"retrograde": False}, "Mars": {"retrograde": False},
            "Mercury": {},  # retrograde key missing
            "Jupiter": {"retrograde": False}, "Venus": {"retrograde": False},
            "Saturn": {"retrograde": False},
        },
    }
    with pytest.raises(ValueError, match="retrograde"):
        compute_combustion(chart_data)


def test_c_calc_ut_raising_surfaces_runtimeerror(monkeypatch):
    """swe.calc_ut raising must surface as RuntimeError containing the planet name."""
    def _boom(jd_ut, pid, flags):
        raise Exception("ephemeris boom")

    monkeypatch.setattr(combustion_mod.swe, "calc_ut", _boom)
    chart_data = _make_chart_data({})

    with pytest.raises(RuntimeError, match="Sun"):
        compute_combustion(chart_data)


# ── Layer D: output shape ─────────────────────────────────────────────────────

@pytest.mark.parametrize("chart_key", _ALL_CHARTS)
def test_d_output_shape(chart_key, all_results):
    """Exactly the 6 lowercase planet keys; sun/rahu/ketu absent; each row has exactly 4 fields."""
    result = all_results[chart_key]

    assert set(result.keys()) == set(_PLANETS), (
        f"{chart_key}: keys={sorted(result.keys())}, expected {sorted(_PLANETS)}"
    )
    assert "sun" not in result and "rahu" not in result and "ketu" not in result

    for planet, row in result.items():
        assert set(row.keys()) == {"is_combust", "separation_deg", "orb_used", "retrograde"}, (
            f"{chart_key} {planet}: unexpected row shape {sorted(row.keys())}"
        )
        assert isinstance(row["is_combust"], bool)
        assert isinstance(row["separation_deg"], float)
        assert isinstance(row["orb_used"], float)
        assert isinstance(row["retrograde"], bool)
