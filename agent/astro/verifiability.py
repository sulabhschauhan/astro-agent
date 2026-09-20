"""Standing verifiability ledger (S140).

ONE canonical, versioned summary of how much of a turn's output the typed
predicate layer could actually VERIFY -- the first-class / second-class split
ruled at S140 (first-class = a typed predicate can decide it; second-class =
it rests on a condition the vocabulary cannot yet check).

This module is a LEAF: it imports nothing from `agent.astro` (pure stdlib), so
the capture writer, the silence gate and an offline roll-up script can all read
it without a cycle. It owns the ledger SCHEMA and its version; every producer
and consumer goes through `summarize()` / `rollup()` so the shape stays in one
place (the P-030 discipline: one fact, one home).

MEASUREMENT ONLY -- nothing here has drop authority and nothing branches on it.
`caught_miss_rate` is the P-033 promotion gate: a human reads it and the
per-case detail and decides whether to flip enforcing; the number never flips
anything itself.

Fail-safe by construction: every field defaults to 0 / absent, so a capture
from an earlier era that never emitted `predicate_coverage` yields a ledger with
`second_class = None` (UNKNOWN, not silently 0) rather than a crash or an
under-count -- the trap that makes free-form-prose roll-ups lie.
"""
from __future__ import annotations

LEDGER_VERSION = 1


def _int(d: dict, key: str, default: int = 0) -> int:
    v = d.get(key, default)
    return v if isinstance(v, int) and not isinstance(v, bool) else default


def _pct(num: int, den: int):
    """Percentage, or None when the denominator is 0 (never a fake 0.0)."""
    return round(100.0 * num / den, 1) if den else None


def summarize(stats: dict | None) -> dict:
    """Canonical per-turn ledger from a `GateResult.stats` dict (silence_gate).

    `stats` is the flat dict silence_gate.apply_silence_gate assembles. Any
    missing key degrades to a fail-safe default; a stats dict lacking
    `predicate_coverage` (pre-S137 era) reports `second_class = None`
    (unknown), so a roll-up can EXCLUDE it from the second-class rate instead
    of counting it as zero.
    """
    stats = stats or {}
    claims_total = _int(stats, "claims_in")
    typed_decided = _int(stats, "typed_decided")
    prose_decided = _int(stats, "prose_decided")

    pc = stats.get("predicate_coverage")
    cv = (pc or {}).get("claim_verdicts") if isinstance(pc, dict) else None
    if isinstance(cv, dict):
        sat = _int(cv, "satisfied")
        con = _int(cv, "contradicted")
        unev = _int(cv, "unevaluable")
        first_class = sat + con          # a predicate DECIDED it (either way)
        second_class = unev              # a predicate could not evaluate it
        claim_ledger_known = True
    else:
        sat = con = unev = 0
        first_class = second_class = None
        claim_ledger_known = False

    sil = {
        "in": _int(stats, "silences_in"),
        "typed": _int(stats, "silences_typed"),
        "caught_miss": _int(stats, "silences_caught_miss"),
        "justified": _int(stats, "silences_justified"),
        "uncheckable": _int(stats, "silences_uncheckable"),
        "fragile_downgraded": _int(stats, "silences_fragile_downgraded"),
    }

    # Second-class exposure = claims a predicate could not evaluate + silences
    # the gate could not check. Only defined when the claim ledger is known.
    if claim_ledger_known:
        unverifiable = second_class + sil["uncheckable"]
        verifiable_universe = claims_total + sil["in"]
        uncheckable_rate = _pct(unverifiable, verifiable_universe)
    else:
        uncheckable_rate = None

    return {
        "ledger_version": LEDGER_VERSION,
        "claims": {
            "total": claims_total,
            "typed_decided": typed_decided,
            "prose_decided": prose_decided,
            "first_class": first_class,      # None => unknown (old capture)
            "second_class": second_class,    # None => unknown (old capture)
            "verdicts": {"satisfied": sat, "contradicted": con, "unevaluable": unev},
            "known": claim_ledger_known,
        },
        "silences": sil,
        "rates": {
            "first_class_pct": _pct(first_class, first_class + second_class)
                               if claim_ledger_known else None,
            "typed_share_pct": _pct(typed_decided, typed_decided + prose_decided),
            "caught_miss_rate_pct": _pct(sil["caught_miss"], sil["typed"]),  # P-033 gate
            "uncheckable_rate_pct": uncheckable_rate,
        },
    }


def rollup(ledgers: list[dict]) -> dict:
    """Aggregate per-turn ledgers into the standing report. Fail-safe: a turn
    whose claim ledger is unknown contributes its SILENCE counts but is excluded
    from the claim first/second-class totals (and counted in `turns_claims_unknown`).
    """
    agg = {
        "turns": 0, "turns_claims_known": 0, "turns_claims_unknown": 0,
        "claims_total": 0, "typed_decided": 0, "prose_decided": 0,
        "first_class": 0, "second_class": 0,
        "sat": 0, "con": 0, "unev": 0,
        "sil_in": 0, "sil_typed": 0, "sil_caught_miss": 0,
        "sil_justified": 0, "sil_uncheckable": 0, "sil_fragile": 0,
    }
    for L in ledgers:
        agg["turns"] += 1
        c = L.get("claims", {})
        s = L.get("silences", {})
        agg["sil_in"] += _int(s, "in"); agg["sil_typed"] += _int(s, "typed")
        agg["sil_caught_miss"] += _int(s, "caught_miss")
        agg["sil_justified"] += _int(s, "justified")
        agg["sil_uncheckable"] += _int(s, "uncheckable")
        agg["sil_fragile"] += _int(s, "fragile_downgraded")
        if c.get("known"):
            agg["turns_claims_known"] += 1
            agg["claims_total"] += _int(c, "total")
            agg["typed_decided"] += _int(c, "typed_decided")
            agg["prose_decided"] += _int(c, "prose_decided")
            agg["first_class"] += _int(c, "first_class")
            agg["second_class"] += _int(c, "second_class")
            v = c.get("verdicts", {})
            agg["sat"] += _int(v, "satisfied"); agg["con"] += _int(v, "contradicted")
            agg["unev"] += _int(v, "unevaluable")
        else:
            agg["turns_claims_unknown"] += 1

    fc, sc = agg["first_class"], agg["second_class"]
    agg["rates"] = {
        "first_class_pct": _pct(fc, fc + sc),
        "typed_share_pct": _pct(agg["typed_decided"], agg["typed_decided"] + agg["prose_decided"]),
        "caught_miss_rate_pct": _pct(agg["sil_caught_miss"], agg["sil_typed"]),   # P-033 gate
        "uncheckable_rate_pct": _pct(sc + agg["sil_uncheckable"], agg["claims_total"] + agg["sil_in"]),
    }
    return agg
