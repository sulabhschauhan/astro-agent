"""tests/astro/test_longevity_render.py
Rendered-fact-block guard (no model) for the S167 longevity layer on the real
Sulabh chart: window kinds, maraka_strength, protective_factors, no-number rule.
"""
from __future__ import annotations

import pytest

from agent.chart_calculator import calculate_chart
from agent.astro import pipeline
from agent.astro.static_facts import build_static_facts

_SULABH = ("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")


@pytest.fixture(scope="module")
def block() -> str:
    return pipeline._fact_block(build_static_facts(calculate_chart(*_SULABH)))


def test_wholistic_no_number_instruction(block):
    assert "READ THIS WHOLISTICALLY" in block
    assert "NEVER a lifespan number" in block


def test_window_kind_tags(block):
    assert "[randhra]" in block and "[maraka]" in block
    moon = [l for l in block.splitlines() if l.strip().startswith("Moon sub-period") and "6 Jul 2027" in l
            and ("[randhra]" in l or "[maraka]" in l or "[ayushkaraka]" in l)]
    assert moon, "no Moon 2027 window line"
    assert all("[randhra]" in l and "[maraka]" not in l for l in moon), moon


def test_strength_section(block):
    assert "Strength of these planets" in block and "rupa" in block
    assert any("Mercury" in l and "below the classical minimum" in l
               for l in block.splitlines())


def test_protective_section(block):
    assert "Protective / arishta-bhanga factors" in block
    assert "Ayushkaraka Saturn in house 1" in block
    assert "Lagna Sagittarius" in block
