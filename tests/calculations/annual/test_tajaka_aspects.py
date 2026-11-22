"""Tajika annual aspect yogas -- Ithasala / Ishrafa (S169).

VALIDATION MODEL (ruled with Sulabh): Ithasala is deterministic geometry
(annual longitudes + fixed deeptamsa table + fixed speed order), not a
contested formula, so there is no JHora desktop oracle to grade against --
and none is needed. Two independent checks instead:

HAND-VERIFIED anchors on Sulabh's 2027 annual chart, each worked out from the
definition by hand (see the per-assert comments). PyJHora is a FORMULA LOOKUP
only (never a runtime dependency, ruled by Sulabh S169), so the engine is NOT
cross-checked by executing PyJHora -- the hand-verified anchors are the whole
validation, exactly as the sahams were graded against the book, not a library.

Positions are Sulabh's 2027 Varsha Pravesh D-1 longitudes, read from the JHora
desktop "Longitude (in D-1)" column (Jupiter is retrograde -> its direction is
flagged provisional, as the engine documents).
"""
import pytest

from agent.calculations.annual.tajaka_aspects import compute_tajaka_aspects


def _dms(sign_base, d, mi, s):
    return sign_base * 30 + d + mi / 60 + s / 3600


# Sulabh 2027 annual D-1 (sign index 0=Aries .. 11=Pisces)
PTS_2027 = {
    "Su": _dms(11, 22, 30, 56.53),   # 22 Pi 30'
    "Mo": _dms(11, 20, 0, 7.68),     # 20 Pi 00'
    "Ma": _dms(3, 26, 50, 54.84),    # 26 Cn 50'
    "Me": _dms(11, 2, 9, 59.52),     # 2 Pi 09'
    "Ju": _dms(3, 22, 49, 1.30),     # 22 Cn 49' (R)
    "Ve": _dms(10, 19, 34, 47.56),   # 19 Aq 34'
    "Sa": _dms(11, 23, 18, 59.91),   # 23 Pi 18'
    "La": _dms(8, 21, 55, 51.25),    # 21 Sg 55'
    "Ra": _dms(9, 23, 31, 50.82),    # 23 Cp 31'
    "Ke": _dms(3, 23, 31, 50.82),    # 23 Cn 31'
}
RETRO_2027 = frozenset({"Ju"})


@pytest.fixture(scope="module")
def res():
    return compute_tajaka_aspects(PTS_2027, retrograde=RETRO_2027)


def _pair(group, a, b):
    for p in group:
        if {p.a, p.b} == {a, b}:
            return p
    return None


# --------------------------------------------------------------------------- #
# (A) HAND-VERIFIED anchors                                                     #
# --------------------------------------------------------------------------- #

def test_mars_saturn_is_ishrafa(res):
    # Ma Cn 26.85, Sa Pi 23.32: Cancer->Pisces offset 8 = 9th = trinal benefic.
    # deeptamsa: Ma orb8 range(18.85,34.85) contains Sa23.32; Sa orb9 range
    # (14.32,32.32) contains Ma26.85 -> within deeptamsa. Faster Ma is MORE
    # advanced (26.85>23.32) -> SEPARATING -> Ishrafa.
    p = _pair(res.ishrafa, "Ma", "Sa")
    assert p is not None and p.valence == "benefic"
    assert _pair(res.ithasala, "Ma", "Sa") is None


def test_sun_venus_is_ithasala(res):
    # Su Pi 22.52, Ve Aq 19.58: Pisces->Aquarius offset 11 = 12th = semisextile
    # neutral. Both within deeptamsa. Faster Ve is LESS advanced (19.58<22.52)
    # -> APPLYING -> Ithasala.
    p = _pair(res.ithasala, "Su", "Ve")
    assert p is not None and p.valence == "neutral"


def test_sun_mars_is_ithasala_benefic(res):
    # Su Pi 22.52, Ma Cn 26.85: trinal (benefic). Within deeptamsa. Faster Su
    # less advanced than Ma -> applying.
    p = _pair(res.ithasala, "Su", "Ma")
    assert p is not None and p.valence == "benefic"


def test_venus_saturn_is_ithasala_neutral(res):
    # Ve Aq 19.58, Sa Pi 23.32: semisextile neutral. Within deeptamsa. Faster
    # Ve less advanced -> applying.
    p = _pair(res.ithasala, "Ve", "Sa")
    assert p is not None and p.valence == "neutral"


def test_moon_venus_is_ishrafa(res):
    # Mo Pi 20.00, Ve Aq 19.58: semisextile neutral, within deeptamsa, |diff|<1
    # -> poorna; faster Mo more advanced -> separating -> Ishrafa.
    p = _pair(res.ishrafa, "Mo", "Ve")
    assert p is not None and p.ithasala_type == "poorna"


# --------------------------------------------------------------------------- #
# structural invariants                                                         #
# --------------------------------------------------------------------------- #

def test_ithasala_and_ishrafa_disjoint(res):
    ith = {frozenset((p.a, p.b)) for p in res.ithasala}
    ish = {frozenset((p.a, p.b)) for p in res.ishrafa}
    assert ith.isdisjoint(ish)


def test_every_directional_pair_actually_aspects(res):
    for p in res.ithasala + res.ishrafa:
        assert p.valence in ("benefic", "malefic", "neutral")
        assert p.relation in ("ithasala", "ishrafa")


def test_nodes_never_in_a_pair(res):
    for p in res.pairs:
        assert "Ra" not in (p.a, p.b) and "Ke" not in (p.a, p.b)


def test_retrograde_jupiter_pairs_flagged_provisional(res):
    # Every directional pair involving (retrograde) Jupiter must be flagged.
    prov = {frozenset(pr) for pr in res.retro_provisional}
    for p in res.ithasala + res.ishrafa:
        if "Ju" in (p.a, p.b):
            assert frozenset((p.a, p.b)) in prov
            assert p.retro_provisional is True


def test_missing_longitude_raises():
    bad = dict(PTS_2027)
    del bad["Sa"]
    with pytest.raises(ValueError):
        compute_tajaka_aspects(bad)


# --------------------------------------------------------------------------- #
# signed-velocity direction (retrograde doctrine, S169)                         #
# speeds are SYNTHETIC here -- these test the direction LOGIC (does retrograde  #
# flip applying/separating), not real ephemeris values. Real signed speeds     #
# arrive from varsha_pravesh at wiring time.                                    #
# --------------------------------------------------------------------------- #

# realistic-magnitude synthetic speeds (deg/day), all DIRECT (> 0) except nodes,
# ORDER-CONSISTENT with the mean-speed order (Sa < Ju < Ma < Su < Ve < Me < Mo) so
# the direct case must reproduce the fallback exactly.
_DIRECT = {"Su": 0.99, "Mo": 13.2, "Ma": 0.52, "Me": 1.4, "Ju": 0.08,
           "Ve": 1.2, "Sa": 0.03, "La": 0.0, "Ra": -0.05, "Ke": -0.05}


def _rel(res, a, b):
    for p in res.ithasala:
        if {p.a, p.b} == {a, b}:
            return "ithasala"
    for p in res.ishrafa:
        if {p.a, p.b} == {a, b}:
            return "ishrafa"
    return "none"


def test_direct_speeds_match_the_fallback():
    # With every planet direct, the signed-velocity method must reproduce the
    # direct-motion fallback exactly, and flag NOTHING provisional.
    fb = compute_tajaka_aspects(PTS_2027, retrograde=RETRO_2027)
    sp = compute_tajaka_aspects(PTS_2027, speeds=_DIRECT)
    fb_dir = {frozenset((p.a, p.b)): p.relation for p in fb.ithasala + fb.ishrafa}
    sp_dir = {frozenset((p.a, p.b)): p.relation for p in sp.ithasala + sp.ishrafa}
    assert fb_dir == sp_dir
    assert sp.retro_provisional == ()          # direction computed, nothing provisional


def test_retrograde_faster_planet_flips_ithasala_to_ishrafa():
    # Sun-Venus is applying (ithasala) with both direct. Make Venus -- the faster,
    # less-advanced planet -- retrograde: it now moves AWAY before exactitude, so
    # the apparent Ithasala is false (Khalasara) and must compute as Ishrafa.
    direct = compute_tajaka_aspects(PTS_2027, speeds=_DIRECT)
    assert _rel(direct, "Su", "Ve") == "ithasala"
    retro = dict(_DIRECT, Ve=-1.2)
    flipped = compute_tajaka_aspects(PTS_2027, speeds=retro)
    assert _rel(flipped, "Su", "Ve") == "ishrafa"


def test_speeds_override_the_retrograde_flag():
    # When real speeds are supplied, the `retrograde` arg is ignored (the speed
    # sign carries it) and no pair is marked provisional.
    r = compute_tajaka_aspects(PTS_2027, speeds=_DIRECT, retrograde=RETRO_2027)
    assert r.retro_provisional == ()
