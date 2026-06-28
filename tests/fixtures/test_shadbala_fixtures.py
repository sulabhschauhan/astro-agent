"""Smoke tests for shadbala_fixtures.py — structural integrity + rupa/virupa consistency."""

import pytest
from tests.fixtures.shadbala_fixtures import SHADBALA_FIXTURES

CHARTS = ["sulabh", "surbhi", "sheridan", "david"]
PLANETS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
PLANET_KEYS = [
    "ochcha", "saptavargaja", "ojayugma", "kendra", "drekkana",
    "sthan_total", "dig", "nathonnatha", "paksha", "thribhaga",
    "abda", "masa", "vara", "hora", "ayana", "yuddha", "kala_total",
    "chesta", "naisargika", "drik",
    "shadbala_virupa", "shadbala_rupa", "min_required", "ratio", "rank",
]


def test_all_charts_present():
    assert set(SHADBALA_FIXTURES.keys()) == set(CHARTS)


def test_all_planets_present_per_chart():
    for chart in CHARTS:
        assert set(SHADBALA_FIXTURES[chart]["planets"].keys()) == set(PLANETS), (
            f"{chart}: missing or extra planet keys"
        )


def test_all_keys_present_sulabh():
    planets = SHADBALA_FIXTURES["sulabh"]["planets"]
    for planet in PLANETS:
        missing = [k for k in PLANET_KEYS if k not in planets[planet]]
        assert not missing, f"sulabh/{planet}: missing keys {missing}"


def test_meta_present_per_chart():
    for chart in CHARTS:
        assert "meta" in SHADBALA_FIXTURES[chart], f"{chart}: missing meta block"
        for field in ("birth_date", "birth_time", "place", "source"):
            assert field in SHADBALA_FIXTURES[chart]["meta"], (
                f"{chart}/meta: missing field '{field}'"
            )


@pytest.mark.parametrize("chart", CHARTS)
@pytest.mark.parametrize("planet", PLANETS)
def test_virupa_rupa_consistency(chart, planet):
    """shadbala_virupa / 60 must equal shadbala_rupa within ±0.01."""
    data = SHADBALA_FIXTURES[chart]["planets"][planet]
    virupa = data["shadbala_virupa"]
    rupa = data["shadbala_rupa"]
    computed = virupa / 60
    assert abs(computed - rupa) <= 0.01, (
        f"{chart}/{planet}: {virupa}/60 = {computed:.4f} but shadbala_rupa = {rupa} "
        f"(delta={abs(computed - rupa):.4f})"
    )
