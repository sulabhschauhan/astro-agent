"""TIER A of the dated layer: the sky, precomputed once, SHARED BY EVERY CHART.

THE SPLIT THIS MODULE EXISTS TO MAKE. Every engine built for the dated timeline
-- combustion windows (S147), divisional ingress (S148), the masa calendar (S148)
-- depends ONLY on the ephemeris and the ayanamsa. Their intervals are
byte-identical for every chart that will ever be built, because combustion is a
Sun-planet separation, an ingress is a graha crossing a cusp, and a lunar month is
a new moon. NONE of them reads a natal chart.

So they are cached ONCE per (as_of, horizon, ayanamsa) and reused by every user,
rather than rescanned per chart. Two consequences, and the second is the one that
matters for the multi-user rollout that reversed the no-storage lock:

  * COST: one scan per window instead of one per chart. Measured S148: a full year
    of masa + a 7-body ingress table is 0.42 s, so the saving is not dramatic for
    one user and is linear in users.
  * PII: THIS FILE CONTAINS NO BIRTH DATA. Not a name, not a date of birth, not a
    place -- only sky events over a date range. Unlike `fact_store` and
    `timeline_store`, whose directories must be gitignored because they are
    derived from real birth details, `data/ephemeris_cache/` holds nothing
    personal and needs no such protection.

WHAT IS *NOT* HERE. Anything chart-relative -- which house an ingress falls in,
which combust graha matters, a sade-sati phase -- is TIER B, and lives in
`build_timeline.py` as a JOIN over this blob. That join costs no ephemeris calls.
The line is exactly "depends on the sky" vs "depends on your chart", and every
engine lands cleanly on one side of it.

RULE OF THREE, NOW MET -- AND DELIBERATELY NOT ACTED ON IN THIS COMMIT. The
~15-line atomic-write / fail-soft-read core below is the THIRD copy (after
`fact_store.py` and `timeline_store.py`). S147 declined to extract it at two
copies citing the rule of three; three is now reached, which is the same threshold
that triggered the `helpers/discrete_scan.py` extraction at S26. Extracting it
here would mean editing two committed, green modules inside a commit that also
adds a feature, against the surgical-edit rule -- and the three stores do differ
in their invalidation semantics (schema version / forward-reach re-anchor /
content-addressed key). RECORDED as its own task, not silently skipped and not
bundled.

Python 3.11.
"""
from __future__ import annotations

import dataclasses
import datetime as _dt
import json
import logging
import os
from typing import Callable

import swisseph as swe

from agent.calculations.transits import (
    combustion_scan, ingress_scan, masa_scan,
)

logger = logging.getLogger(__name__)

__all__ = ["SHARED_SCHEMA_VERSION", "DEFAULT_SHARED_DIR", "shared_window_key",
           "build_shared_ephemeris", "load_or_build_shared"]

# Bump when the SHAPE or the SET of sky facts below changes, so every pre-existing
# file is treated as stale. INDEPENDENT of fact_store.SCHEMA_VERSION and
# timeline_store.TIMELINE_SCHEMA_VERSION -- the three stores version separately so
# a change to one never forces a rebuild of the others.
SHARED_SCHEMA_VERSION = 1

# NOT gitignored, and that is deliberate -- see the module docstring. Keeping it
# out of the PII directories is what makes it shareable.
DEFAULT_SHARED_DIR = os.path.join("data", "ephemeris_cache")


def shared_window_key(as_of: _dt.date, horizon_days: int, ayanamsa: str) -> str:
    """Content-addressed key. Two charts asking for the same window on the same
    day get the same file, which is the whole point of this tier.

    Deliberately HUMAN-READABLE (`2026-10-07_365_LAHIRI`) rather than hashed: the
    key carries no personal data, so there is nothing to obscure, and a browsable
    cache directory is easier to reason about and to clear by hand.
    """
    return f"{as_of.isoformat()}_{int(horizon_days)}_{ayanamsa}"


def _jd_at_midnight_ut(d: _dt.date) -> float:
    """Julian Day (UT) at 00:00 of `d`. The window anchor is a DATE, so it is
    pinned to midnight UT explicitly rather than inherited from a clock."""
    return swe.julday(d.year, d.month, d.day, 0.0)


def build_shared_ephemeris(as_of: _dt.date, horizon_days: int) -> dict:
    """Scan every chart-independent dated fact over [as_of, as_of + horizon_days].

    Each engine is called in a separate try/except so one failing scan costs its
    own fact class and not the whole window -- the same isolation
    `ingress_scan.scan_ingress_table` applies per body, applied here per engine.
    A caller can tell a partial build by the `errors` key; it is never silent.

    Returns a JSON-serialisable dict (MasaInterval dataclasses are flattened).
    """
    start_jd = _jd_at_midnight_ut(as_of)
    end_jd = start_jd + float(horizon_days)
    out: dict = {
        "shared_schema_version": SHARED_SCHEMA_VERSION,
        "as_of": as_of.isoformat(),
        "horizon_end": (as_of + _dt.timedelta(days=horizon_days)).isoformat(),
        "horizon_days": int(horizon_days),
        "start_jd": start_jd,
        "end_jd": end_jd,
        "ayanamsa": ingress_scan.AYANAMSA_NAME,
        "nirayana": True,
        "errors": {},
    }

    try:
        out["combustion"] = combustion_scan.scan_combustion_windows(start_jd, end_jd)
    except Exception as exc:  # noqa: BLE001 -- one fact class, not the window
        logger.warning("ephemeris_cache: combustion scan failed (%s)", exc)
        out["combustion"] = {"intervals": []}
        out["errors"]["combustion"] = f"{type(exc).__name__}: {exc}"

    try:
        out["ingress"] = ingress_scan.scan_ingress_table(start_jd, end_jd)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ephemeris_cache: ingress scan failed (%s)", exc)
        out["ingress"] = {"events": [], "errors": {}}
        out["errors"]["ingress"] = f"{type(exc).__name__}: {exc}"

    try:
        cal = masa_scan.scan_masa_calendar(start_jd, end_jd)
        out["masa"] = {
            "months": [dataclasses.asdict(m) for m in cal["months"]],
            "new_moons": cal["new_moons"],
            "full_moons": cal["full_moons"],
            "sankrantis": [list(s) for s in cal["sankrantis"]],
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("ephemeris_cache: masa scan failed (%s)", exc)
        out["masa"] = {"months": [], "new_moons": [], "full_moons": [],
                       "sankrantis": []}
        out["errors"]["masa"] = f"{type(exc).__name__}: {exc}"

    return out


def _is_usable(blob) -> bool:
    """A cached blob is usable only if it is a dict of the CURRENT schema. The
    window itself is not re-checked here: the key already encodes as_of, horizon
    and ayanamsa, so a file found under a key covers that key by construction."""
    return isinstance(blob, dict) and \
        blob.get("shared_schema_version") == SHARED_SCHEMA_VERSION


def load_or_build_shared(
    as_of: _dt.date,
    horizon_days: int,
    *,
    cache_dir: str = DEFAULT_SHARED_DIR,
    builder: Callable[[_dt.date, int], dict] | None = None,
    ayanamsa: str | None = None,
) -> dict:
    """The shared sky for this window, from cache when present.

    NEVER raises for a cache I/O or schema problem: a bad or unreadable file falls
    back to building in memory, so a cache fault can never block an answer. The
    write is atomic (tmp + os.replace).

    Args:
        builder: injected for tests; defaults to build_shared_ephemeris.
        ayanamsa: key component; defaults to the engine's own declared ayanamsa so
            a frame change cannot silently reuse a file built under the old one.
    """
    build = builder or build_shared_ephemeris
    ayan = ayanamsa or ingress_scan.AYANAMSA_NAME
    key = shared_window_key(as_of, horizon_days, ayan)
    path = os.path.join(cache_dir, f"{key}.json")

    blob = None
    try:
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                blob = json.load(f)
    except Exception as exc:  # noqa: BLE001 -- a bad read must never block an answer
        logger.warning("ephemeris_cache: read failed (%s) -> rebuilding", exc)
        blob = None

    if _is_usable(blob):
        return blob

    logger.info("ephemeris_cache: building shared window %s", key)
    out = build(as_of, horizon_days)
    try:
        os.makedirs(cache_dir, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False)
        os.replace(tmp, path)  # atomic publish
    except Exception as exc:  # noqa: BLE001 -- persistence is best-effort
        logger.warning("ephemeris_cache: write failed (%s)", exc)
    return out
