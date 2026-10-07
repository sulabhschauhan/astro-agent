"""Static per-chart fact store + cache (V1.5, S147).

Compute-once-per-chart: on birth details (+ palm) the full STATIC fact set is
assembled and persisted, keyed by the chart's identity, so every later question
-- this session or a future one, this user or another with the same chart --
reads a ready store instead of recomputing.

The DYNAMIC, date-ranged facts (muhurta scans, transit-at-date) are NOT stored
here: they depend on dates the question supplies and are computed at question
time by the runtime dispatcher. The boundary is strict -- static if it is fixed
for the chart, runtime if it is parametrised by the question.

SUPERSEDES the S65 "no storage -- fresh upload every session" lock, reversed by
Sulabh (S147) for multi-user rollout. The cache is LOCAL and the directory is
gitignored -- real birth data is never committed.

KEY: a hash of (name, place, dob, tob, birth-time-exact) -> a short, filename-
safe id that leaks no PII in the path. The readable identity is kept INSIDE the
file for browsability. One file per distinct birth combination, as intended.

SCHEMA-VERSIONED: a file written under an older SCHEMA_VERSION is ignored and
rebuilt, so growing the static library never silently serves a stale, thin set.

This is a LEAF module (stdlib only) -- the swisseph-heavy assembly is INJECTED
as a `builder` callable, so the cache logic stays pure and testable and this
module never imports a calculator.

Python 3.11.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Callable

logger = logging.getLogger(__name__)

__all__ = ["SCHEMA_VERSION", "DEFAULT_CACHE_DIR", "chart_cache_key",
           "chart_identity_key", "load_or_build"]

# Bump whenever build_static_facts changes which fact classes it produces, so
# every pre-existing cached file is treated as stale and rebuilt on next use.
#   v1 -> v2 (S147): added "lucky_unlucky" fact class.
SCHEMA_VERSION = 2

# MUST be listed in .gitignore -- real birth data is never committed.
DEFAULT_CACHE_DIR = os.path.join("data", "fact_cache")


def chart_cache_key(name, place, dob, tob, *, exact: bool) -> str:
    """Filename-safe identity hash for a birth combination.

    Normalises name/place casing + whitespace and folds in the birth-time
    confidence (Exact vs Approximate changes the fact set -- KP inclusion,
    S145), so an Approximate and an Exact run of the same details never collide.
    """
    norm = "|".join([
        str(name or "").strip().lower(),
        str(place or "").strip().lower(),
        str(dob or "").strip(),
        str(tob or "").strip(),
        "exact" if exact else "approx",
    ])
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


def chart_identity_key(jd_ut, asc_lon_sidereal, *, exact: bool) -> str:
    """Filename-safe identity hash from the chart's OWN computed identity.

    Used at answer time, where the birth-entry form fields are no longer in
    scope (a fresh Streamlit rerun) but the chart is. jd_ut fixes the exact UTC
    moment and asc_lon_sidereal the ascendant (which depends on both time and
    place), so the pair is a sound chart identity -- equivalent to "date-time +
    place" without needing the name (astrologically irrelevant, and PII). Folds
    in the birth-time confidence so Exact and Approximate never collide.

    Returns "" when the identity is unavailable (missing meta) -- the caller
    then skips caching and builds in memory.
    """
    try:
        norm = "|".join([
            f"{float(jd_ut):.6f}",
            f"{float(asc_lon_sidereal):.4f}",
            "exact" if exact else "approx",
        ])
    except (TypeError, ValueError):
        return ""
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


def load_or_build(
    key: str,
    builder: Callable[[], dict],
    *,
    cache_dir: str = DEFAULT_CACHE_DIR,
    identity: dict | None = None,
) -> dict:
    """Return the static fact store for `key`.

    Loads a schema-current cached file if present; otherwise calls `builder()`
    (a no-arg callable returning the fact dict), persists it, and returns it.

    NEVER raises for a cache I/O or schema problem -- a bad or unreadable cache
    falls back to building in memory, so a cache fault can never block an answer.
    The write is atomic (tmp + os.replace) so a crash mid-write cannot leave a
    half-written file that later reads as valid.

    Args:
        key: chart_cache_key(...) output.
        builder: produces the static fact dict (JSON-serialisable). Called only
            on a miss or a schema mismatch.
        cache_dir: where files live (gitignored).
        identity: readable {name, place, dob, tob, exact} stored in the file for
            browsing; never used for lookup.
    """
    if not key:
        return builder()  # no identity -> cannot cache; build in memory
    path = os.path.join(cache_dir, f"{key}.json")
    try:
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                blob = json.load(f)
            if isinstance(blob, dict) and blob.get("schema_version") == SCHEMA_VERSION:
                return blob.get("facts") or {}
            logger.info("fact_store: schema/shape mismatch for %s -> rebuilding", key)
    except Exception as exc:  # noqa: BLE001 -- a bad cache read must never block an answer
        logger.warning("fact_store: cache read failed (%s) -> rebuilding", exc)

    facts = builder()
    blob = {
        "schema_version": SCHEMA_VERSION,
        "key": key,
        "identity": identity or {},
        "facts": facts,
    }
    try:
        os.makedirs(cache_dir, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(blob, f, ensure_ascii=False)
        os.replace(tmp, path)  # atomic publish
    except Exception as exc:  # noqa: BLE001 -- persistence is best-effort
        logger.warning("fact_store: cache write failed (%s)", exc)
    return facts
