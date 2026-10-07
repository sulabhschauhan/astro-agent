"""Dated per-chart fact timeline + cache (V1.5, S147).

The SECOND store, SEPARATE from fact_store (the chart-fixed static store). Where
static facts never change, these facts are DATED -- transits (gochara), planetary
combustion, lunar-month (masa) shuddhi -- so the store carries a time window and
is RE-ANCHORED as the clock advances. Varshaphal is deliberately OUT of this
phase (no Tajika engine yet -- S147 decision).

THE RE-FRAME that makes a 1-year precompute survive the day turning over: the
store never holds a "now" value. It holds INTERVALS (Saturn ingresses sign X on
date D; Venus is combust [start, end]; masa M runs [start, end]) as ISO strings
over [as_of, as_of + WINDOW_DAYS]. "Now" is resolved by the runtime dispatcher
AGAINST those intervals at answer time -- so yesterday's file still answers
today's question, and only the WINDOW's forward reach can go stale.

RE-ANCHOR POLICY -- ONE threshold (9-agent decision, S147): rebuild when the
window's forward reach drops below REANCHOR_TAIL_DAYS. Because intervals are
stored exact, an aging `as_of` costs NO accuracy; the only failure mode is the
window no longer reaching far enough ahead of "now", which the tail check
catches. A requested date beyond horizon_end (even post-reanchor) is the
dispatcher's cue to compute live -- not this store's concern.

LEAF module (stdlib only): the swisseph-heavy sweep is INJECTED as `builder`,
exactly like fact_store, so the cache + anchor logic stays pure and testable and
this module never imports a calculator. The ~15-line atomic-write/fail-soft-read
core is COPIED from fact_store (not shared) by 9-agent decision: the two stores
have different semantics and sharing now would couple them prematurely.

Python 3.11.
"""
from __future__ import annotations

import datetime as _dt
import json
import logging
import os
from typing import Callable

logger = logging.getLogger(__name__)

__all__ = ["TIMELINE_SCHEMA_VERSION", "DEFAULT_TIMELINE_DIR", "WINDOW_DAYS",
           "REANCHOR_TAIL_DAYS", "needs_reanchor", "load_or_refresh"]

# Bump when build_timeline changes which dated fact classes it produces or their
# shape, so every pre-existing file is treated as stale and rebuilt on next use.
# INDEPENDENT of fact_store.SCHEMA_VERSION -- widening a timeline fact never forces
# a static rebuild, and vice versa.
TIMELINE_SCHEMA_VERSION = 1

# MUST be gitignored -- derived from real birth data.
DEFAULT_TIMELINE_DIR = os.path.join("data", "timeline_cache")

# Forward span precomputed at each (re)build. One year per Sulabh's directive
# ("pull only for 1 year; beyond that, real-time"). Scope guard: beyond this the
# dispatcher computes live -- the store is never asked to cover it.
WINDOW_DAYS = 365

# Re-anchor when the window reaches less than this far ahead of "now". The SINGLE
# re-anchor trigger (9-agent, S147): guarantees the store always extends >= this
# far forward before the dispatcher falls back to live compute. Scope guard:
# evaluated only on a question that reads a dated fact, never on idle. Tuning
# note: raise toward 180 if live-compute-beyond-horizon proves expensive; lower
# toward 45 to rebuild less often at the cost of a shorter guaranteed reach.
REANCHOR_TAIL_DAYS = 90


def _parse_iso_date(s) -> _dt.date | None:
    """ISO 'YYYY-MM-DD' -> date, tolerating a full timestamp; None if unparseable."""
    try:
        return _dt.date.fromisoformat(str(s)[:10])
    except (TypeError, ValueError):
        return None


def needs_reanchor(blob, today: _dt.date) -> bool:
    """True when `blob` must be rebuilt: absent, malformed, stale-schema, or its
    forward reach has dropped below REANCHOR_TAIL_DAYS of `today`.

    Pure and total -- never raises. A None/!dict blob (cache miss or corrupt
    read) is treated as needing a build.
    """
    if not isinstance(blob, dict):
        return True
    if blob.get("timeline_schema_version") != TIMELINE_SCHEMA_VERSION:
        return True
    end = _parse_iso_date(blob.get("horizon_end"))
    if end is None:
        return True  # malformed anchor -> rebuild rather than trust it
    return (end - today).days < REANCHOR_TAIL_DAYS


def load_or_refresh(
    key: str,
    builder: Callable[[_dt.date], dict],
    today: _dt.date | None = None,
    *,
    cache_dir: str = DEFAULT_TIMELINE_DIR,
    identity: dict | None = None,
) -> dict:
    """Return the dated fact set for `key`, rebuilding when the window is stale.

    Loads the cached file; if it is schema-current AND still reaches
    REANCHOR_TAIL_DAYS ahead of `today`, returns its facts. Otherwise calls
    `builder(as_of)` -- a callable taking the new anchor date (today) and
    returning the dated fact dict for [as_of, as_of + WINDOW_DAYS] -- then
    persists and returns it.

    NEVER raises for a cache I/O or schema problem: a bad or unreadable file
    falls back to building in memory, so a cache fault can never block an answer.
    The write is atomic (tmp + os.replace). An empty `key` builds in memory with
    no caching (identity unavailable upstream).

    Args:
        key: the chart identity key (SAME key fact_store uses for this chart).
        builder: (as_of: date) -> dated fact dict (JSON-serialisable).
        today: injected for testability; defaults to date.today().
        cache_dir: gitignored directory for the files.
        identity: browsable, non-PII marker stored in the file; never used for lookup.
    """
    today = today or _dt.date.today()
    if not key:
        return builder(today)  # no identity -> cannot cache; build in memory

    path = os.path.join(cache_dir, f"{key}.json")
    blob = None
    try:
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                blob = json.load(f)
    except Exception as exc:  # noqa: BLE001 -- a bad read must never block an answer
        logger.warning("timeline_store: cache read failed (%s) -> rebuilding", exc)
        blob = None

    if not needs_reanchor(blob, today):
        return blob.get("facts") or {}
    logger.info("timeline_store: (re)building window for %s (as_of=%s)", key, today)

    as_of = today
    horizon_end = as_of + _dt.timedelta(days=WINDOW_DAYS)
    facts = builder(as_of)
    out = {
        "timeline_schema_version": TIMELINE_SCHEMA_VERSION,
        "key": key,
        "identity": identity or {},
        "as_of": as_of.isoformat(),
        "horizon_end": horizon_end.isoformat(),
        "facts": facts,
    }
    try:
        os.makedirs(cache_dir, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False)
        os.replace(tmp, path)  # atomic publish
    except Exception as exc:  # noqa: BLE001 -- persistence is best-effort
        logger.warning("timeline_store: cache write failed (%s)", exc)
    return facts
