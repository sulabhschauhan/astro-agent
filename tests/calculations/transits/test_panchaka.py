"""Tests for agent/calculations/transits/panchaka.py -- P2.3.4 Panchaka
(instant primitive).

Panchaka is NOT natal-relative (see panchaka.py's module docstring) -- no
reference-chart fixtures here, unlike test_chandrabala.py / test_tarabala.py.
The Sulabh-anchor fixture below reuses the project-wide canonical transit
moment purely for JD continuity with the other transit test files, not
because Sulabh's natal chart matters to a Panchaka calculation.

Locked design decisions (Definition B sourcing, named-type / Panchaka-Rahita
deferral, no-natal-parameter rationale) live in
agent/calculations/transits/panchaka.py's module docstring -- not
duplicated here.

Imports go through the direct module path
(agent.calculations.transits.panchaka), not through
agent.calculations.transits -- that package's __init__.py is intentionally
empty (Session 21 locked convention).
"""

import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))  # project root

import pytest
import swisseph as swe

import agent.calculations.transits.panchaka as panchaka_module
from agent.calculations.transits.panchaka import (
    PanchakaCategory,
    compute_panchaka,
)

# Canonical transit fixture moment: 2026-06-20 18:30 UTC. Shared with
# test_chandrabala.py / test_tarabala.py / test_gochara.py / test_sade_sati.py
# -- see test_gochara.py's ANCHOR CONVENTION note. Redefined inline per this
# test family's self-containment convention, not imported.
_JD_UT_20260620_1830_UTC = swe.julday(2026, 6, 20, 18.5)

# Known mid-Panchak fixture: 2026-07-06 00:00 UTC. Locked from the P2.3.4
# design proposal's diagnostic scan -- not recomputed here.
_JD_UT_KNOWN_MID_PANCHAK = 2461227.5

# Known non-Panchak fixture: 2026-07-15 00:00 UTC. Locked from the P2.3.4
# design proposal's diagnostic scan -- not recomputed here.
_JD_UT_KNOWN_NON_PANCHAK = 2461236.5


# ─── Fixture 1: known mid-Panchak ──────────────────────────────────────────

def test_known_mid_panchak_is_panchak():
    status = compute_panchaka(_JD_UT_KNOWN_MID_PANCHAK)
    assert status.category == PanchakaCategory.PANCHAK
    assert 300.0 <= status.moon_longitude < 360.0


# ─── Fixture 2: known non-Panchak ──────────────────────────────────────────

def test_known_non_panchak_is_not_panchak():
    status = compute_panchaka(_JD_UT_KNOWN_NON_PANCHAK)
    assert status.category == PanchakaCategory.NOT_PANCHAK
    assert not (300.0 <= status.moon_longitude < 360.0)


# ─── Fixture 3: Sulabh canonical anchor (JD continuity, not chart) ─────────

def test_sulabh_canonical_anchor_not_panchak():
    # Sulabh anchor used purely for project-wide JD continuity, not because
    # the chart matters -- Panchak is universal at a given JD (see module
    # docstring's "No natal parameter" lock).
    status = compute_panchaka(_JD_UT_20260620_1830_UTC)
    assert status.category == PanchakaCategory.NOT_PANCHAK


# ─── Unit tests: mechanical correctness, no fixtures ───────────────────────

def test_panchaka_status_is_frozen():
    status = compute_panchaka(_JD_UT_20260620_1830_UTC)
    with pytest.raises(dataclasses.FrozenInstanceError):
        status.category = PanchakaCategory.PANCHAK


def test_moon_longitude_boundary_at_300_is_panchak(monkeypatch):
    # Mocks swe.calc_ut directly -- mirrors test_chandrabala.py's
    # test_moon_sign_boundary_just_below_sign_edge / just_above_sign_edge
    # pattern (existing precedent for boundary-mocking swe.calc_ut).
    def fake_calc_ut(jd_ut, planet, flags):
        return ([300.0, 0.0, 0.0, 0.0, 0.0, 0.0], 0)

    monkeypatch.setattr(panchaka_module.swe, "calc_ut", fake_calc_ut)
    status = compute_panchaka(0.0)
    assert status.category == PanchakaCategory.PANCHAK


def test_moon_longitude_boundary_at_360_wraps_to_not_panchak(monkeypatch):
    def fake_calc_ut(jd_ut, planet, flags):
        return ([360.0, 0.0, 0.0, 0.0, 0.0, 0.0], 0)

    monkeypatch.setattr(panchaka_module.swe, "calc_ut", fake_calc_ut)
    status = compute_panchaka(0.0)
    assert status.moon_longitude == 0.0
    assert status.category == PanchakaCategory.NOT_PANCHAK


def test_moon_longitude_just_below_300_is_not_panchak(monkeypatch):
    def fake_calc_ut(jd_ut, planet, flags):
        return ([299.9, 0.0, 0.0, 0.0, 0.0, 0.0], 0)

    monkeypatch.setattr(panchaka_module.swe, "calc_ut", fake_calc_ut)
    status = compute_panchaka(0.0)
    assert status.category == PanchakaCategory.NOT_PANCHAK
