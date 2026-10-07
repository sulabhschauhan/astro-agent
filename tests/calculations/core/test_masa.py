"""core/masa.build_masa_intervals -- pure doctrine tests, zero ephemeris.

Instants are plain floats here. That is the point of the pure/driver split: the
calendar rule is checkable without an ephemeris, including the cases a real
one-year scan would never produce (a zero-sankranti month at the window edge, a
two-sankranti month).
"""
import pytest

from agent.calculations.core._masa_tables import MASA_NAMES
from agent.calculations.core.masa import MasaInterval, build_masa_intervals

# A tidy synthetic year: new moons 30 days apart, one sankranti mid-month.
NM = [0.0, 30.0, 60.0, 90.0, 120.0]
SPAN = (-10.0, 130.0)


def _sankranti(jd, rashi):
    return (jd, rashi)


def test_single_sankranti_names_the_month_by_its_rashi():
    """The month containing the Mesha (0) ingress is Chaitra (index 0) -- NOT the
    following month. Pinned because the first draft of this layer used rashi + 1,
    which would have named every month after its successor."""
    months = build_masa_intervals(
        NM, [_sankranti(15.0, 0), _sankranti(45.0, 1), _sankranti(75.0, 2),
             _sankranti(105.0, 3)], sankranti_span=SPAN)
    assert [m.masa_index for m in months] == [0, 1, 2, 3]
    assert [m.name_sa for m in months] == \
        ["Chaitra", "Vaishakha", "Jyeshtha", "Ashadha"]
    assert all(m.sankranti_count == 1 and m.complete for m in months)


def test_zero_sankranti_month_is_counted_but_not_named():
    """The intercalary case. The COUNT is a placement fact and is reported; the
    NAME is withheld because the naming rule is uncited in this project's corpus
    (see masa.py's docstring). No `adhika` flag is emitted."""
    months = build_masa_intervals(
        NM, [_sankranti(15.0, 0), _sankranti(75.0, 2), _sankranti(105.0, 3)],
        sankranti_span=SPAN)
    gap = months[1]
    assert gap.sankranti_count == 0
    assert gap.contained_sankranti_rashis == ()
    assert gap.masa_index is None and gap.name_sa is None
    assert gap.complete is True          # it IS fully covered; just unnamed
    assert not hasattr(gap, "adhika")


def test_two_sankranti_month_is_counted_but_not_named():
    months = build_masa_intervals(
        NM, [_sankranti(15.0, 0), _sankranti(29.0, 1), _sankranti(45.0, 2),
             _sankranti(75.0, 3), _sankranti(105.0, 4)], sankranti_span=SPAN)
    first = months[0]
    assert first.sankranti_count == 2
    assert first.contained_sankranti_rashis == (0, 1)
    assert first.masa_index is None and first.name_sa is None


def test_sankranti_exactly_at_a_new_moon_belongs_to_the_opening_month():
    """Half-open [start, end). Decides the near-coincidence case, which is the
    only case where the count is actually in doubt (a 4.5-hour gap was measured
    in 2026)."""
    months = build_masa_intervals(
        NM, [_sankranti(30.0, 1)], sankranti_span=SPAN)
    assert months[0].sankranti_count == 0      # month [0, 30)
    assert months[1].sankranti_count == 1      # month [30, 60)
    assert months[1].masa_index == 1


def test_month_outside_the_sankranti_span_is_incomplete_and_unnamed():
    """THE LIE THIS GUARD PREVENTS: a clipped month shows zero sankrantis for a
    scanning reason, which is indistinguishable from the real zero-sankranti
    month. It must be marked incomplete and must not be named."""
    months = build_masa_intervals(
        NM, [_sankranti(45.0, 1), _sankranti(75.0, 2)],
        sankranti_span=(25.0, 95.0))
    assert months[0].complete is False
    assert months[0].masa_index is None
    assert months[-1].complete is False
    assert months[1].complete is True and months[1].masa_index == 1


def test_intervals_are_contiguous_and_bounded_by_the_new_moons():
    months = build_masa_intervals(NM, [], sankranti_span=SPAN)
    assert len(months) == len(NM) - 1
    assert months[0].start_jd == NM[0] and months[-1].end_jd == NM[-1]
    for i in range(len(months) - 1):
        assert months[i].end_jd == months[i + 1].start_jd


@pytest.mark.parametrize("nm", [[], [10.0]])
def test_fewer_than_two_new_moons_yields_no_months(nm):
    assert build_masa_intervals(nm, [], sankranti_span=SPAN) == []


def test_unsorted_sankranti_input_is_tolerated():
    a = build_masa_intervals(NM, [_sankranti(75.0, 2), _sankranti(15.0, 0)],
                             sankranti_span=SPAN)
    b = build_masa_intervals(NM, [_sankranti(15.0, 0), _sankranti(75.0, 2)],
                             sankranti_span=SPAN)
    assert a == b


def test_non_ascending_new_moons_raise():
    with pytest.raises(ValueError, match="strictly ascending"):
        build_masa_intervals([0.0, 30.0, 30.0], [], sankranti_span=SPAN)
    with pytest.raises(ValueError, match="strictly ascending"):
        build_masa_intervals([0.0, 60.0, 30.0], [], sankranti_span=SPAN)


def test_inverted_sankranti_span_raises():
    with pytest.raises(ValueError, match="inverted"):
        build_masa_intervals(NM, [], sankranti_span=(100.0, 0.0))


def test_is_idempotent():
    args = (NM, [_sankranti(15.0, 0)])
    assert build_masa_intervals(*args, sankranti_span=SPAN) == \
           build_masa_intervals(*args, sankranti_span=SPAN)


def test_masa_names_table_is_twelve_unique_names():
    assert len(MASA_NAMES) == 12 == len(set(MASA_NAMES))


def test_masa_interval_is_frozen():
    m = MasaInterval(0.0, 1.0, None, None, 0, (), True)
    with pytest.raises(Exception):
        m.start_jd = 5.0  # type: ignore[misc]
