"""TIER B of the dated layer: the shared sky, PROJECTED onto one chart.

This is the `builder` that `timeline_store.load_or_refresh` calls. It does NO
astronomy: Tier A (`ephemeris_cache`) has already scanned the sky for this window,
and everything here is a JOIN of those events against one natal chart. No
ephemeris call, no scan, milliseconds.

THE ONE PROJECTION RULE, APPLIED UNIFORMLY. Every dated event that involves a
graha is expressed in the two frames the project already uses everywhere else --
house from the natal Lagna and house from the natal Moon, whole-sign, exactly
`gochara.compute_gochara`'s rule (locked S20, dual-reference, both populated
unconditionally; the answer layer picks per question type). Nothing else is added
and no event is filtered: WHICH of these matters for a given question is the
planner's and the interpreter's business, not this module's. One rule, no
doctrine, no use-case logic.

WHAT IS DELIBERATELY NOT DERIVED HERE
  * SADE SATI. `transits/sade_sati.py` already owns it and is oracle-validated.
    Re-deriving the phase from Saturn's house-from-Moon would be a second source
    of truth for a doctrine that already has one. Saturn's ingress events carry
    `house_from_moon`, which is the INPUT that module needs; the verdict stays
    where it is.
  * TITHI / PANCHANGA LIMBS. `core/panchanga.py` is the sole source (S148 lock).
    The lunations here are month BOUNDARIES, not a tithi series.
  * ANY "now" VALUE. Per the S147 lock, this store holds INTERVALS and EVENTS with
    their own instants; "today" is resolved against them at answer time, so a
    stored window survives the day turning over.
  * ANY NAMING OF AN INTERCALARY MONTH. Carried through from `core/masa.py`
    unchanged: `sankranti_count` is a fact, the name is withheld when it is not 1.

FAIL-SOFT, like every other fact composer on this path (`transit_facts`,
`static_facts`): a chart that cannot support the projection costs the dated facts,
never the answer. This module does not raise.

Python 3.11.
"""
from __future__ import annotations

import datetime as _dt
import logging

from agent.astro import ephemeris_cache, timeline_store

logger = logging.getLogger(__name__)

__all__ = ["project_events", "build_timeline", "timeline_builder_for",
           "load_timeline_for_chart"]

# Which body each fact class is "about", for the house projection. Masa has no
# graha, so it is carried through unprojected -- a lunar month is not in a house.
_SIGN_SPAN = 30.0


def _house(sign_0: int, ref_sign_0: int) -> int:
    """Whole-sign house of `sign_0` counted from `ref_sign_0`, 1-12.

    Identical arithmetic to gochara.compute_gochara's
    `((sign - natal_sign) % 12) + 1`, kept here rather than imported because
    gochara's version is embedded in a snapshot builder that would pull swisseph
    into this leaf module for one modulo.
    """
    return ((sign_0 - ref_sign_0) % 12) + 1


def project_events(shared: dict, natal_asc_lon: float,
                   natal_moon_lon: float) -> dict:
    """Join a Tier-A shared blob onto one chart. Pure; no ephemeris, never raises
    on well-formed input.

    Args:
        shared: a `ephemeris_cache.build_shared_ephemeris` blob.
        natal_asc_lon / natal_moon_lon: sidereal degrees, [0, 360).

    Returns:
        {
          "ingress":    [ {body, jd, from_index, to_index, retrograde,
                           from_house_from_lagna, to_house_from_lagna,
                           from_house_from_moon,  to_house_from_moon} ],
          "combustion": [ {planet, start_jd, end_jd, retrograde_at_mid} ],
          "masa":       [ {start_jd, end_jd, masa_index, name_sa,
                           sankranti_count, ...} ],
        }
        `from_index`/`to_index` are RASHI indices (0 = Mesha); the house fields are
        the same crossing seen from the two natal reference points. A retrograde
        crossing has to_house < from_house, which is how a consumer can tell a
        graha LEAVING a house from one entering it without re-reading the sky.
    """
    asc_sign = int((natal_asc_lon % 360.0) / _SIGN_SPAN) % 12
    moon_sign = int((natal_moon_lon % 360.0) / _SIGN_SPAN) % 12

    ingress_out: list[dict] = []
    for e in (shared.get("ingress") or {}).get("events") or []:
        fi, ti = e.get("from_index"), e.get("to_index")
        if not isinstance(fi, int) or not isinstance(ti, int):
            continue  # a malformed event costs itself, not the window
        ingress_out.append({
            **e,
            "from_house_from_lagna": _house(fi, asc_sign),
            "to_house_from_lagna": _house(ti, asc_sign),
            "from_house_from_moon": _house(fi, moon_sign),
            "to_house_from_moon": _house(ti, moon_sign),
        })

    return {
        "ingress": ingress_out,
        "combustion": list((shared.get("combustion") or {}).get("intervals") or []),
        "masa": list((shared.get("masa") or {}).get("months") or []),
    }


def build_timeline(chart: dict, as_of: _dt.date, *,
                   horizon_days: int = timeline_store.WINDOW_DAYS,
                   shared_loader=None) -> dict:
    """The dated fact set for one chart over [as_of, as_of + horizon_days].

    This is the callable shape `timeline_store.load_or_refresh` expects, once
    bound to a chart by `timeline_builder_for`.

    Args:
        chart: `agent.chart_calculator.calculate_chart()` output. Read-only; the
            same two fields `transit_facts.build_transit_facts` reads --
            `planetary_positions['Moon']['longitude']` and
            `meta['asc_lon_sidereal']`.
        shared_loader: injected for tests; defaults to
            `ephemeris_cache.load_or_build_shared`, so the sky is scanned once and
            shared across charts rather than rescanned here.

    Returns:
        A JSON-serialisable dict. On an unusable chart: the Tier-A facts with
        `{"projected": False}` and a `chart_error`, NOT an exception and NOT an
        empty dict -- the sky is still true even when the chart cannot be read,
        and dropping it would lose a window that cost real work to build.
    """
    load = shared_loader or ephemeris_cache.load_or_build_shared
    try:
        shared = load(as_of, horizon_days)
    except Exception as exc:  # noqa: BLE001 -- dated facts, never the answer
        logger.warning("build_timeline: shared window unavailable (%s)", exc)
        return {"projected": False, "shared_error": f"{type(exc).__name__}: {exc}"}

    meta = {
        "as_of": shared.get("as_of"),
        "horizon_end": shared.get("horizon_end"),
        "ayanamsa": shared.get("ayanamsa"),
        "nirayana": shared.get("nirayana"),
        "shared_errors": shared.get("errors") or {},
    }

    try:
        pp = chart.get("planetary_positions") or {}
        moon_lon = (pp.get("Moon") or {}).get("longitude")
        asc_lon = (chart.get("meta") or {}).get("asc_lon_sidereal")
        if moon_lon is None or asc_lon is None:
            raise ValueError("chart lacks Moon longitude or asc_lon_sidereal")
        projected = project_events(shared, float(asc_lon) % 360.0,
                                   float(moon_lon) % 360.0)
    except Exception as exc:  # noqa: BLE001
        logger.warning("build_timeline: projection failed (%s)", exc)
        return {**meta, "projected": False,
                "chart_error": f"{type(exc).__name__}: {exc}",
                "ingress": [], "combustion": [], "masa": []}

    return {**meta, "projected": True, **projected}


def timeline_builder_for(chart: dict, *,
                         horizon_days: int = timeline_store.WINDOW_DAYS,
                         shared_loader=None):
    """Bind `chart` so the result matches `timeline_store`'s `builder(as_of)`
    contract. The store stays ignorant of charts and calculators, exactly as its
    leaf-module docstring requires."""
    def _builder(as_of: _dt.date) -> dict:
        return build_timeline(chart, as_of, horizon_days=horizon_days,
                              shared_loader=shared_loader)
    return _builder


def load_timeline_for_chart(key: str, chart: dict, *, today: _dt.date | None = None,
                            identity: dict | None = None, shared_loader=None,
                            **store_kwargs) -> dict:
    """Convenience seam for the app: cached dated facts for `key`, rebuilt only
    when `timeline_store`'s single re-anchor threshold fires.

    `key` is the SAME chart identity key `fact_store` uses, so the static and
    dated stores stay addressable together.
    """
    return timeline_store.load_or_refresh(
        key, timeline_builder_for(chart, shared_loader=shared_loader), today,
        identity=identity, **store_kwargs)
