"""Mechanism test for varshaphal_facts._is_night (the Tajika day/night flag fed
to lord_of_the_year).

This is the acceptance gate for the swe.azalt xin-length fix: EQU2HOR needs a
3-value [RA, dec, dist] input, not 2. With the 2-value form the call raised on
every invocation and the fail-soft returned DAY, so the year-lord ran on a
wrong (always-day) flag.

Deliberately NOT a year-lord assertion. The year-lord's "correct" value is a
separate, independently-sourced question; here we gate only the mechanism --
does a known-night instant read night, a known-day instant read day, with no
fail-soft warning. Instants are local midnight / noon at the birthplace, far
from twilight, so the horizon SIGN is unambiguous (not a borderline judgement).

The real _is_night uses FLG_SWIEPH; with no ephe path set it resolves the Sun
via the Moshier fallback (arcsecond-accurate -- the production path, since
compute_varsha_pravesh restores set_ephe_path(None) before _is_night runs), so
this needs no .se1 files. swisseph is already a hard test dependency (the suite
imports it suite-wide).
"""
import logging

import swisseph as swe

import agent.astro.varshaphal_facts as vf

# Birthplace from the varshaphal composer fixture (Kolkata; local civil = UT+5.5).
_LAT, _LON = 22.5667, 88.35


def test_is_night_true_at_local_midnight(caplog):
    # 2025-06-21 00:00 IST == 2025-06-20 18:30 UT. Sun far below the horizon.
    jd = swe.julday(2025, 6, 20, 18.5)
    with caplog.at_level(logging.WARNING):
        result = vf._is_night(jd, _LAT, _LON)
    assert result is True
    assert "day/night calc failed" not in caplog.text


def test_is_night_false_at_local_noon(caplog):
    # 2025-06-21 12:00 IST == 2025-06-21 06:30 UT. Near-solstice noon, Sun high.
    jd = swe.julday(2025, 6, 21, 6.5)
    with caplog.at_level(logging.WARNING):
        result = vf._is_night(jd, _LAT, _LON)
    assert result is False
    assert "day/night calc failed" not in caplog.text
