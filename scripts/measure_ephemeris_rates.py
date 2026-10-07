#!/usr/bin/env python3
"""Re-derive the rate bounds that ingress_scan's crossing prune depends on.

WHY THIS SCRIPT EXISTS. `scan_quantised_crossings` prunes a sub-interval only
when a crossing inside it is arithmetically impossible, and that proof needs a
TRUE upper bound on |d(angle)/dt|. So `ingress_scan.MAX_ABS_SPEED_DEG_PER_DAY`
and `masa_scan.ELONGATION_RATE_BOUND` are correctness constants, not tuning
knobs -- and a correctness constant that came from memory is a correctness
constant nobody can check. This script is how they were produced and how they
are re-produced.

An UNDER-estimate silently drops crossings; an OVER-estimate only costs time.
So the stored values are the measured maxima rounded UP. Never round down.

Usage:
    python scripts/measure_ephemeris_rates.py [--from 2010] [--to 2040]

LLM: none. Reads the ephemeris only; writes nothing.
"""
from __future__ import annotations

import argparse

import swisseph as swe

from agent.calculations.helpers import ephemeris
from agent.calculations.transits.ingress_scan import MAX_ABS_SPEED_DEG_PER_DAY

# Sampling stride per body, days. Fast bodies are sampled finely enough that a
# speed maximum between samples cannot be far off the sampled one; slow bodies
# do not need it. This is a MEASUREMENT stride, not a scan step -- it affects
# only how tight the measured maximum is, never the scanner's correctness.
STRIDE = {"sun": 0.25, "moon": 0.25, "mercury": 0.5, "venus": 0.5,
          "mars": 0.5, "jupiter": 1.0, "saturn": 1.0}

BODIES = {"sun": swe.SUN, "moon": swe.MOON, "mercury": swe.MERCURY,
          "venus": swe.VENUS, "mars": swe.MARS, "jupiter": swe.JUPITER,
          "saturn": swe.SATURN}


def measure(start_jd: float, end_jd: float) -> dict[str, float]:
    out: dict[str, float] = {}
    for name, pid in BODIES.items():
        step = STRIDE[name]
        peak = 0.0
        jd = start_jd
        while jd < end_jd:
            peak = max(peak, abs(ephemeris.sidereal_position(jd, pid).speed))
            jd += step
        out[name] = peak
    # The composed angle masa_scan scans. Its rate is |moon - sun|, NOT the
    # Moon's own, which is why it is measured here rather than inferred.
    peak = 0.0
    jd = start_jd
    while jd < end_jd:
        peak = max(peak, abs(ephemeris.sidereal_position(jd, swe.MOON).speed
                             - ephemeris.sidereal_position(jd, swe.SUN).speed))
        jd += 0.25
    out["elongation(moon-sun)"] = peak
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from", dest="y0", type=int, default=2010)
    ap.add_argument("--to", dest="y1", type=int, default=2040)
    args = ap.parse_args()

    start, end = swe.julday(args.y0, 1, 1, 0.0), swe.julday(args.y1, 1, 1, 0.0)
    measured = measure(start, end)

    print(f"max |deg/day| over {args.y0}-01-01 .. {args.y1}-01-01 UT")
    print(f"{'body':22s} {'measured':>10s} {'stored':>8s}  verdict")
    bad = 0
    for name, peak in measured.items():
        stored = MAX_ABS_SPEED_DEG_PER_DAY.get(name)
        if stored is None:
            print(f"{name:22s} {peak:10.4f} {'-':>8s}  (not a scanned body)")
            continue
        ok = stored >= peak
        bad += 0 if ok else 1
        print(f"{name:22s} {peak:10.4f} {stored:8.3f}  "
              f"{'ok' if ok else 'TOO LOW -- RAISE IT'}")
    if bad:
        print(f"\n{bad} stored bound(s) are below the measured maximum. The "
              "crossing prune is UNSOUND until they are raised.")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
