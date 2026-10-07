"""Lunar month (masa) intervals from lunation and solar-ingress instants.

PURE. Stdlib only, no swisseph, no ephemeris. It takes two already-computed lists
of instants and does interval arithmetic. The ephemeris driver is
`transits/masa_scan.py`; this split exists so the doctrine is unit-testable with
zero astronomy and so the rule can be read without reading a scanner.

WHAT THIS MODULE REPORTS, AND WHAT IT DELIBERATELY DOES NOT
-----------------------------------------------------------
It reports PLACEMENT FACTS: where each lunar month begins and ends, and which
solar sign-ingresses (sankrantis) fall inside it. Naming a month is a placement
fact too, when exactly one sankranti falls inside it -- the month that contains
the Mesha ingress is Chaitra, and that correspondence is the calendar's
definition, not an interpretation of it.

It does NOT emit `adhika` or `kshaya` flags. That is not an oversight and not
caution for its own sake -- it is the Validation Source law applied honestly:

  The rule "a lunar month containing no sankranti is intercalary (adhika) and
  takes the name of the FOLLOWING month; one containing two is kshaya" is
  siddhantic doctrine, and the project's corpus DOES NOT CONTAIN IT. The only
  masa material held is BPHS ch.27 on the Masa lord (Ahargana / 30 -- a mean
  30-day month with no sankranti and no intercalation at all). Shipping the rule
  here would mean sourcing it from a panchanga implementation and then grading it
  against a panchanga -- the exact failure that put four wrong yoga formulas in
  this repo (S131/S132, "the oracle graded its own homework").

  So the COUNT is reported and the NAME is withheld when the count is not 1.
  `sankranti_count == 0` is, in every living panchanga tradition, the condition
  the word adhika names; a consumer that has a cited source may apply the name.
  This module will not apply it on an uncited one. When a chapter-and-verse
  citation is in hand, naming belongs in a doctrine layer above this one -- not
  in this file, which reports separations and placements (P-029).

AMANTA ONLY. Months run new moon -> new moon. The purnimanta reckoning (full
moon -> full moon, same names shifted) is NOT implemented: it is a presentation
transform over these same intervals, it changes a month's NAME for roughly half
of every month, and shipping both schemes would be shipping two contradictory
answers to defer a decision. One scheme, stated.

Python 3.11.
"""
from __future__ import annotations

from dataclasses import dataclass

from ._masa_tables import MASA_NAMES

__all__ = ["MasaInterval", "build_masa_intervals", "SYNODIC_MONTH_DAYS"]

# Mean synodic month, days. Used ONLY as the over-scan margin a driver needs on
# each side of a requested window so that the first and last reported months are
# whole (see `build_masa_intervals`' completeness contract). It is never used to
# predict or place a lunation -- those come from the ephemeris.
SYNODIC_MONTH_DAYS = 29.530588853


@dataclass(frozen=True)
class MasaInterval:
    """One amanta lunar month, [start_jd, end_jd), both new-moon instants (UT).

    masa_index / name_sa are None when `sankranti_count != 1` -- see the module
    docstring. `name_sa` is a bare Sanskrit token and is NOT renderable prose: a
    user-facing layer must wrap it, never print it alone.

    `complete` is False when the month was not fully covered by the sankranti
    scan, so its count cannot be trusted. A partially covered month can show
    zero sankrantis purely because the scan stopped, which is indistinguishable
    from the real zero-sankranti month -- the single most likely way this engine
    could tell a confident lie. Consumers MUST drop or ignore `complete=False`
    intervals rather than reading their counts.
    """
    start_jd: float
    end_jd: float
    masa_index: int | None
    name_sa: str | None
    sankranti_count: int
    contained_sankranti_rashis: tuple[int, ...]
    complete: bool


def build_masa_intervals(
    new_moon_jds: list[float],
    sankrantis: list[tuple[float, int]],
    *,
    sankranti_span: tuple[float, float],
) -> list[MasaInterval]:
    """Amanta lunar months spanned by `new_moon_jds`, with their sankranti counts.

    Args:
        new_moon_jds: new-moon instants (UT), ascending. N instants bound N-1
            months; a list shorter than 2 yields no months, which is correct and
            not an error -- there is no such thing as a month with one end.
        sankrantis: (jd_ut, rashi_index) for each solar sign ingress, rashi 0 =
            Mesha. Order is not assumed. Only ingresses are meaningful here, so a
            retrograde re-crossing of a cusp by the Sun cannot occur and is not
            modelled (the Sun never retrogrades); a duplicate instant would be
            counted twice, so the caller must not pass one.
        sankranti_span: (from_jd, to_jd) actually covered by the sankranti scan.
            A month not wholly inside this span is marked `complete=False`.

    Returns:
        Months in time order, contiguous: intervals[i].end_jd == intervals[i+1].start_jd.

    Raises:
        ValueError: new_moon_jds is not strictly ascending, or sankranti_span is
            inverted. Both are caller bugs that would otherwise produce a
            plausible-looking calendar with a silently wrong month count.
    """
    span_from, span_to = sankranti_span
    if span_from > span_to:
        raise ValueError(
            f"sankranti_span is inverted: {span_from} > {span_to}")
    for i in range(len(new_moon_jds) - 1):
        if not new_moon_jds[i] < new_moon_jds[i + 1]:
            raise ValueError(
                "new_moon_jds must be strictly ascending; "
                f"index {i} ({new_moon_jds[i]}) >= {i + 1} ({new_moon_jds[i + 1]})"
            )

    out: list[MasaInterval] = []
    for i in range(len(new_moon_jds) - 1):
        start, end = new_moon_jds[i], new_moon_jds[i + 1]
        # Half-open [start, end): a sankranti exactly at a new moon belongs to the
        # month that is beginning, never to the one that just ended. Stated because
        # that choice decides the count in precisely the near-coincidence case
        # where the answer matters (S148 measured a 4.5-hour gap in 2026).
        inside = tuple(r for (jd, r) in sorted(sankrantis) if start <= jd < end)
        complete = span_from <= start and end <= span_to
        index = inside[0] if (complete and len(inside) == 1) else None
        out.append(MasaInterval(
            start_jd=start,
            end_jd=end,
            masa_index=index,
            name_sa=MASA_NAMES[index] if index is not None else None,
            sankranti_count=len(inside),
            contained_sankranti_rashis=inside,
            complete=complete,
        ))
    return out
